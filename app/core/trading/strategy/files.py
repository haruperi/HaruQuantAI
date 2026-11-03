"""Read and write donor SQX strategy packages without translating their contents.

Description:
    Preserve strategy XML, optional last settings, and other ZIP entries for
    document exchange. Validate package structure without interpreting strategy
    behavior or applying the donor's unavailable conversion and repair routines.
Purpose:
    FEAT-DONOR-STRATEGY-FILES: Shared donor-native document file boundary.
Key Capabilities:
    - FR-sqx-files-read: Bound package reads and log successful entry counts.
    - FR-sqx-files-write: Replace files atomically and log successful entry counts.
    - FR-sqx-files-validation: Reject malformed or unsupported input with logged
      domain errors; tests verify rejection and preservation of existing files.
Python API Usage:
    from app.core.trading.strategy.files import read_sqx, write_sqx
    document = read_sqx("example.sqx")
    write_sqx("copy.sqx", document)
CLI Usage:
    uv run pytest tests/core/trading/strategy/test_files.py --no-cov
"""

from __future__ import annotations

import zlib
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import NoReturn
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError

logger = get_logger(__name__)

_STRATEGY_ENTRY = "strategy_Portfolio.xml"
_SETTINGS_ENTRY = "lastSettings.xml"
_MAX_ENTRIES = 4096
_MAX_CONTENT_BYTES = 256 * 1024 * 1024
_MAX_ZIP_COMMENT_BYTES = 65535


@dataclass(frozen=True, slots=True)
class SqxEntry:
    """One named archive payload, with original ZIP metadata when available."""

    name: str
    data: bytes
    metadata: ZipInfo | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class SqxDocument:
    """Ordered archive entries; XML bytes remain the authoritative document."""

    entries: tuple[SqxEntry, ...]
    comment: bytes = b""

    @property
    def strategy_xml(self) -> bytes:
        """Return strategy bytes from a structurally valid package."""
        return next(e.data for e in self.entries if e.name == _STRATEGY_ENTRY)

    @property
    def last_settings_xml(self) -> bytes | None:
        """Distinguish absent settings (None) from an empty settings entry (b'')."""
        return next((e.data for e in self.entries if e.name == _SETTINGS_ENTRY), None)


def _reject(code: str, message: str) -> NoReturn:
    """Report failures without logging paths, XML, or other package contents."""
    logger.warning("FR-sqx-files-validation: code=%s", code)
    raise DomainError(code=code, message=message)


def _require_sqx(path: Path) -> None:
    """Limit this file boundary to SQX; legacy conversion is not implemented."""
    if path.suffix.lower() != ".sqx":
        _reject(
            "SQX_FORMAT_UNSUPPORTED",
            "Expected an .sqx package; legacy conversion is not supported.",
        )


def _validate_document(document: SqxDocument) -> None:
    """Validate container structure without rewriting or repairing XML."""
    names = [e.name for e in document.entries]
    if len(names) > _MAX_ENTRIES:
        _reject("SQX_LIMIT_EXCEEDED", "Too many entries in the strategy package.")
    if sum(len(e.data) for e in document.entries) > _MAX_CONTENT_BYTES:
        _reject("SQX_LIMIT_EXCEEDED", "Strategy package contents exceed the limit.")
    if len(document.comment) > _MAX_ZIP_COMMENT_BYTES:
        _reject("SQX_LIMIT_EXCEEDED", "Archive comment exceeds the ZIP format limit.")
    if len(set(names)) != len(names) or any(not name or "\0" in name for name in names):
        _reject(
            "SQX_PACKAGE_INVALID", "Archive entry names must be unique and nonempty."
        )
    if _STRATEGY_ENTRY not in names:
        _reject("SQX_PACKAGE_INVALID", "Package is missing strategy_Portfolio.xml.")
    try:
        root = ET.fromstring(document.strategy_xml)  # noqa: S314
        settings = document.last_settings_xml
        if settings:
            ET.fromstring(settings)  # noqa: S314
    except ET.ParseError, LookupError, ValueError:
        _reject("SQX_XML_INVALID", "Strategy or last-settings XML is malformed.")
    if root.tag != "StrategyFile" or root.find("Strategy") is None:
        _reject(
            "SQX_STRUCTURE_UNSUPPORTED",
            "Expected a StrategyFile document containing a Strategy element.",
        )


def read_sqx(path: str | Path) -> SqxDocument:
    """Read a donor strategy package without extracting files or converting XML.

    Args:
        path: Existing SQX package to read.

    Returns:
        Ordered entries containing their original uncompressed payloads.

    Raises:
        DomainError: For unavailable, malformed, oversized, or unsupported input.
    """
    source = Path(path)
    _require_sqx(source)
    try:
        with ZipFile(source) as archive:
            metadata = archive.infolist()
            if (
                len(metadata) > _MAX_ENTRIES
                or sum(e.file_size for e in metadata) > _MAX_CONTENT_BYTES
            ):
                _reject("SQX_LIMIT_EXCEEDED", "Strategy package exceeds read limits.")
            if any(e.flag_bits & 1 for e in metadata):
                _reject(
                    "SQX_FORMAT_UNSUPPORTED", "Encrypted ZIP entries are unsupported."
                )
            document = SqxDocument(
                entries=tuple(
                    SqxEntry(e.filename, archive.read(e), copy(e)) for e in metadata
                ),
                comment=archive.comment,
            )
    except OSError, BadZipFile, RuntimeError, NotImplementedError, EOFError, zlib.error:
        _reject("SQX_READ_FAILED", "Cannot read the strategy package.")
    _validate_document(document)
    logger.info("FR-sqx-files-read: entries=%d", len(document.entries))
    return document


def write_sqx(path: str | Path, document: SqxDocument) -> None:
    """Write validated entries, replacing the destination after ZIP completion.

    Args:
        path: Destination SQX file; an existing file is replaced on success.
        document: Complete ordered archive contents to preserve or edit explicitly.

    Raises:
        DomainError: For invalid documents, unsupported targets, or write failures.
    """
    destination = Path(path)
    _require_sqx(destination)
    _validate_document(document)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as archive:
            archive.comment = document.comment
            for entry in document.entries:
                info = copy(entry.metadata) if entry.metadata is not None else None
                original_attributes = info.external_attr if info is not None else 0
                if info is not None:
                    info.filename = entry.name
                archive.writestr(info if info is not None else entry.name, entry.data)
                if info is not None:
                    # ZipFile assigns default permissions when the original is zero.
                    archive.getinfo(entry.name).external_attr = original_attributes
        Path(temporary).replace(destination)
    except OSError, BadZipFile, RuntimeError, NotImplementedError, ValueError:
        _reject("SQX_WRITE_FAILED", "Cannot write the strategy package.")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    logger.info("FR-sqx-files-write: entries=%d", len(document.entries))

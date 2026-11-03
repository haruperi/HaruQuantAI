"""Qualify donor package exchange independently of HSL or execution services."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import replace
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.strategy import files
from app.core.trading.strategy.files import SqxDocument, SqxEntry, read_sqx, write_sqx

_STRATEGY = (
    b'<?xml version="1.0" encoding="UTF-8"?>\r\n'
    b'<StrategyFile Version="3.9.130"><!--keep me-->'
    b'<options custom="0.00"/><Strategy name="Example">'
    b'<Unknown xmlns="urn:donor:test" parameter="1.0E-4"/>'
    b"</Strategy></StrategyFile>"
)
_FIXTURES = Path(__file__).with_name("fixtures")


@pytest.mark.parametrize(
    ("name", "digest"),
    [
        (
            "EMACross.sqx",
            "98a7ccb03937e113cbaf6a50e883d0b14b4e33bb08cc851be6d3c3e36ebc3700",
        ),
        (
            "InsideBarBreakout.sqx",
            "1dfb87f46b1ff52b5bd524b7b217a6f3bb783c83ab8441df87a7ac4e2420ff17",
        ),
    ],
)
def test_actual_donor_examples(
    name: str, digest: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Preserve actual donor payloads and metadata, not just a local object model."""
    source = _FIXTURES / name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    target = tmp_path / name
    with caplog.at_level(logging.INFO):
        loaded = read_sqx(source)
        write_sqx(target, loaded)
    with ZipFile(source) as original, ZipFile(target) as saved:
        assert saved.namelist() == original.namelist()
        assert saved.comment == original.comment
        for entry in original.infolist():
            assert saved.read(entry.filename) == original.read(entry)
            actual = saved.getinfo(entry.filename)
            assert actual.date_time == entry.date_time
            assert actual.compress_type == entry.compress_type
            assert actual.external_attr == entry.external_attr
    assert read_sqx(target).entries == loaded.entries
    assert loaded.last_settings_xml is None
    assert "FR-sqx-files-read: entries=2" in caplog.text
    assert "FR-sqx-files-write: entries=2" in caplog.text
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("settings", [None, b"", b'<Settings value="0.00"/>'])
def test_preserve_settings_and_opaque_contents(
    settings: bytes | None, tmp_path: Path
) -> None:
    """Keep absence, empty settings, XML text, binary results, order, and metadata."""
    info = ZipInfo("Results/Main: TEST_H1/equity.bin", (2020, 4, 5, 6, 7, 8))
    info.compress_type = ZIP_STORED
    info.comment = b"entry comment"
    info.extra = b"\xfe\xca\x02\x00ok"
    info.external_attr = 0o100600 << 16
    entries = [
        SqxEntry("strategy_Portfolio.xml", _STRATEGY),
        SqxEntry("settings.xml", b"opaque settings from another owner"),
        SqxEntry(info.filename, b"\x00\xff\x01result", info),
        SqxEntry("orders.bin", b"\x00\x01\xff"),
        SqxEntry("resources/", b""),
        SqxEntry("resources/custom.xml", b'<Custom foreign="yes"/>'),
    ]
    if settings is not None:
        entries.insert(1, SqxEntry("lastSettings.xml", settings))
    document = SqxDocument(tuple(entries), comment=b"archive comment")
    path = tmp_path / "strategy.sqx"
    write_sqx(path, document)
    loaded = read_sqx(path)
    assert loaded.entries == document.entries
    assert loaded.comment == document.comment
    assert loaded.strategy_xml == _STRATEGY
    assert loaded.last_settings_xml == settings
    with ZipFile(path) as archive:
        metadata = archive.getinfo(info.filename)
        assert metadata.comment == info.comment
        assert metadata.extra == info.extra
        assert metadata.external_attr == info.external_attr
    # Replace only the strategy entry; binary results and unknown entries stay intact.
    modified = replace(
        loaded,
        entries=tuple(
            replace(e, data=e.data.replace(b'name="Example"', b'name="Edited"'))
            if e.name == "strategy_Portfolio.xml"
            else e
            for e in loaded.entries
        ),
    )
    write_sqx(path, modified)
    assert read_sqx(path).entries == modified.entries


@pytest.mark.parametrize(
    ("entries", "code"),
    [
        ((), "SQX_PACKAGE_INVALID"),
        ((SqxEntry("strategy.xml", _STRATEGY),), "SQX_PACKAGE_INVALID"),
        ((SqxEntry("strategy_Portfolio.xml", b"not xml"),), "SQX_XML_INVALID"),
        (
            (SqxEntry("strategy_Portfolio.xml", b"<Strategy/>"),),
            "SQX_STRUCTURE_UNSUPPORTED",
        ),
        (
            (SqxEntry("strategy_Portfolio.xml", b"<StrategyFile/>"),),
            "SQX_STRUCTURE_UNSUPPORTED",
        ),
        (
            (
                SqxEntry("strategy_Portfolio.xml", _STRATEGY),
                SqxEntry("lastSettings.xml", b"broken"),
            ),
            "SQX_XML_INVALID",
        ),
        ((SqxEntry("strategy_Portfolio.xml", _STRATEGY),) * 2, "SQX_PACKAGE_INVALID"),
        (
            (SqxEntry("strategy_Portfolio.xml", _STRATEGY), SqxEntry("", b"")),
            "SQX_PACKAGE_INVALID",
        ),
    ],
)
def test_reject_invalid_packages_without_replacing_existing_file(
    entries: tuple[SqxEntry, ...],
    code: str,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Reader and writer reject malformed input with observable, bounded errors."""
    path = tmp_path / "existing.sqx"
    path.write_bytes(b"original file")
    with caplog.at_level(logging.WARNING), pytest.raises(DomainError) as error:
        write_sqx(path, SqxDocument(entries))
    assert error.value.code == code
    assert path.read_bytes() == b"original file"
    assert code in caplog.text
    assert "<Strategy" not in caplog.text
    if (
        entries
        and all(e.name for e in entries)
        and len({e.name for e in entries}) == len(entries)
    ):
        with ZipFile(path, "w") as archive:
            for entry in entries:
                archive.writestr(entry.name, entry.data)
        with pytest.raises(DomainError) as error:
            read_sqx(path)
        assert error.value.code == code


def test_read_errors_and_unsupported_conversion(tmp_path: Path) -> None:
    """Do not guess legacy conversions, missing files, or non-ZIP contents."""
    for name, payload, code in [
        ("old.sqw", _STRATEGY, "SQX_FORMAT_UNSUPPORTED"),
        ("broken.sqx", b"not a zip", "SQX_READ_FAILED"),
    ]:
        path = tmp_path / name
        path.write_bytes(payload)
        with pytest.raises(DomainError) as error:
            read_sqx(path)
        assert error.value.code == code
    with pytest.raises(DomainError, match="Cannot read"):
        read_sqx(tmp_path / "missing.sqx")
    with pytest.raises(DomainError) as error:
        write_sqx(tmp_path / "old.sqw", SqxDocument(()))
    assert error.value.code == "SQX_FORMAT_UNSUPPORTED"


def test_limits_before_decompression_or_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Apply the same explicit host bounds to reads and constructed documents."""
    path = tmp_path / "bounded.sqx"
    document = SqxDocument((SqxEntry("strategy_Portfolio.xml", _STRATEGY),))
    write_sqx(path, document)
    for limit, value in [("_MAX_ENTRIES", 0), ("_MAX_CONTENT_BYTES", 1)]:
        with monkeypatch.context() as patch:
            patch.setattr(files, limit, value)
            for operation in [
                lambda: read_sqx(path),
                lambda: write_sqx(path, document),
            ]:
                with pytest.raises(DomainError) as error:
                    operation()
                assert error.value.code == "SQX_LIMIT_EXCEEDED"


def test_failed_write_preserves_destination_and_cleans_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed final replacement cannot destroy a previously saved package."""
    path = tmp_path / "existing.sqx"
    path.write_bytes(b"original file")

    def unavailable(*_args: object) -> None:
        raise OSError("controlled failure")

    monkeypatch.setattr(Path, "replace", unavailable)
    with caplog.at_level(logging.WARNING), pytest.raises(DomainError) as error:
        write_sqx(path, SqxDocument((SqxEntry("strategy_Portfolio.xml", _STRATEGY),)))
    assert error.value.code == "SQX_WRITE_FAILED"
    assert path.read_bytes() == b"original file"
    assert list(tmp_path.iterdir()) == [path]
    assert "SQX_WRITE_FAILED" in caplog.text
    assert "controlled failure" not in caplog.text


def test_ambiguous_encrypted_and_corrupted_archives(tmp_path: Path) -> None:
    """Reject duplicate members, password flags, and invalid CRC payloads."""
    path = tmp_path / "ambiguous.sqx"
    with ZipFile(path, "w") as archive:
        archive.writestr("strategy_Portfolio.xml", _STRATEGY)
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("strategy_Portfolio.xml", _STRATEGY)
    with pytest.raises(DomainError) as error:
        read_sqx(path)
    assert error.value.code == "SQX_PACKAGE_INVALID"
    with ZipFile(path, "w") as archive:
        archive.writestr("strategy_Portfolio.xml", _STRATEGY)
    original = path.read_bytes()
    encrypted = bytearray(original)
    central = encrypted.index(b"PK\x01\x02")
    encrypted[6] |= 1  # Local ZIP general-purpose bit flag.
    encrypted[central + 8] |= 1  # Central-directory copy of the same flag.
    path.write_bytes(encrypted)
    with pytest.raises(DomainError) as error:
        read_sqx(path)
    assert error.value.code == "SQX_FORMAT_UNSUPPORTED"
    corrupt = bytearray(original)
    offset = 30 + len(b"strategy_Portfolio.xml")
    corrupt[offset] ^= 1
    path.write_bytes(corrupt)
    with pytest.raises(DomainError) as error:
        read_sqx(path)
    assert error.value.code == "SQX_READ_FAILED"


def test_invalid_constructed_metadata_is_not_silently_truncated(tmp_path: Path) -> None:
    """Refuse names/comments that ZipFile otherwise changes silently."""
    path = tmp_path / "metadata.sqx"
    document = SqxDocument((SqxEntry("strategy_Portfolio.xml", _STRATEGY),))
    with pytest.raises(DomainError) as error:
        write_sqx(path, replace(document, comment=b"x" * 65536))
    assert error.value.code == "SQX_LIMIT_EXCEEDED"
    with pytest.raises(DomainError) as error:
        write_sqx(
            path, replace(document, entries=(*document.entries, SqxEntry("a\0b", b"")))
        )
    assert error.value.code == "SQX_PACKAGE_INVALID"
    assert not path.exists()


def test_unavailable_target_directory(tmp_path: Path) -> None:
    """Return a domain failure without creating missing directories implicitly."""
    with pytest.raises(DomainError) as error:
        write_sqx(
            tmp_path / "missing" / "strategy.sqx",
            SqxDocument((SqxEntry("strategy_Portfolio.xml", _STRATEGY),)),
        )
    assert error.value.code == "SQX_WRITE_FAILED"

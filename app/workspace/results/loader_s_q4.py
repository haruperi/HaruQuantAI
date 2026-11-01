"""SQ4 / SQX strategy (.sqx ZIP/XML) archive loader with Zip Slip protection.

Description:
    Implements LoaderSQ4Service safely unpacking and parsing SQ4/SQX
    strategy archives, guarding against Zip Slip traversal entries and
    extracting strategy metadata, configuration, and trade results.

Purpose:
    FEAT-RESULTS-LOADER-SQ4: Safe SQ4/SQX archive parsing and extraction.

Key Capabilities:
    - FR-results-loader-sq4: Validate archive security and extract SQ4 strategies.

Python API Usage:
    from app.workspace.results.loader_s_q4 import LoaderSQ4Service
    archive = LoaderSQ4Service.load_bytes("Strat.sqx", raw_bytes)

CLI Usage:
    python -m app.cli results load-sq4 --file Strat.sqx
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.results.app_results import to_float, to_int
from app.workspace.results.loader_s_q3 import LoadedStrategyArchive

logger = get_logger(__name__)


class LoaderSQ4Service:
    """Service safely loading SQ4/SQX strategy archive packages."""

    @classmethod
    def _extract_xml_text(cls, filename: str, payload: bytes) -> str:
        """Extract XML string checking for Zip Slip vulnerabilities."""
        if zipfile.is_zipfile(io.BytesIO(payload)):
            try:
                with zipfile.ZipFile(io.BytesIO(payload), "r") as zf:
                    # Enforce Zip Slip protection
                    for entry in zf.namelist():
                        if ".." in entry or entry.startswith(("/", "\\")):
                            raise DomainError(
                                code="RESULTS_SQ4_UNSAFE_ARCHIVE_ENTRY",
                                message=(
                                    f"Unsafe path traversal entry detected: '{entry}'"
                                ),
                                details={"entry": entry, "filename": filename},
                            )

                    xml_files = [n for n in zf.namelist() if n.lower().endswith(".xml")]
                    if not xml_files:
                        raise DomainError(
                            code="RESULTS_SQ4_MALFORMED_ARCHIVE",
                            message="ZIP archive contains no XML files",
                            details={"filename": filename},
                        )
                    return zf.read(xml_files[0]).decode("utf-8", errors="replace")
            except (zipfile.BadZipFile, KeyError) as err:
                raise DomainError(
                    code="RESULTS_SQ4_MALFORMED_ARCHIVE",
                    message="Failed to unpack SQ4 ZIP archive",
                    details={"filename": filename},
                ) from err

        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as err:
            raise DomainError(
                code="RESULTS_SQ4_MALFORMED_ARCHIVE",
                message="Payload is neither a valid ZIP nor UTF-8 XML",
                details={"filename": filename},
            ) from err

    @classmethod
    def load_bytes(cls, filename: str, payload: bytes) -> LoadedStrategyArchive:
        """Parse SQ4 archive bytes, rejecting unsafe Zip Slip path traversal."""
        logger.info(
            "FR-results-loader-sq4: loading %s (%d bytes)",
            filename,
            len(payload),
        )
        if not payload:
            raise DomainError(
                code="RESULTS_SQ4_MALFORMED_ARCHIVE",
                message="Archive payload cannot be empty",
                details={"filename": filename},
            )

        xml_text = cls._extract_xml_text(filename, payload)

        try:
            root = ET.fromstring(xml_text)  # noqa: S314
        except ET.ParseError as err:
            raise DomainError(
                code="RESULTS_SQ4_MALFORMED_ARCHIVE",
                message="Malformed XML content in SQ4 strategy archive",
                details={"filename": filename},
            ) from err

        strategy_name = root.attrib.get(
            "name", root.attrib.get("strategyName", filename.rsplit(".", 1)[0])
        )
        symbol = root.attrib.get("symbol", "EURUSD")
        timeframe = root.attrib.get("timeframe", "H1")

        # Extract parameters
        params: dict[str, Any] = {}
        for p in root.findall(".//Param"):
            k = p.attrib.get("name")
            v = p.attrib.get("value")
            if k is not None and v is not None:
                params[k] = v

        # Extract trades
        trades_list: list[dict[str, Any]] = []
        for t in root.findall(".//Trade"):
            ticket = to_int(t.attrib.get("ticket", len(trades_list) + 1))
            direction = t.attrib.get("direction", "BUY")
            pl = to_float(t.attrib.get("profit_loss", 0.0))
            trades_list.append(
                {
                    "ticket": ticket,
                    "direction": direction,
                    "profit_loss": pl,
                }
            )

        logger.info(
            "FR-results-loader-sq4: parsed %s name='%s' trades=%d",
            filename,
            strategy_name,
            len(trades_list),
        )

        return LoadedStrategyArchive(
            format_version="SQ4",
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            trade_count=len(trades_list),
            trades=tuple(trades_list),
            parameters=params,
            xml_content=xml_text,
        )

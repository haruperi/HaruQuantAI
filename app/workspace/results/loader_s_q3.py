"""SQ3 legacy strategy (.str XML/ZIP) archive loader.

Description:
    Implements LoaderSQ3Service parsing SQ3 XML or ZIP container payloads
    into LoadedStrategyArchive representations preserving strategy metadata,
    trading parameters, and executed trades.

Purpose:
    FEAT-RESULTS-LOADER-SQ3: SQ3 legacy strategy archive loader.

Key Capabilities:
    - FR-results-loader-sq3: Parse SQ3 XML and ZIP strategy files.

Python API Usage:
    from app.workspace.results.loader_s_q3 import LoaderSQ3Service
    archive = LoaderSQ3Service.load_bytes("Strat.str", raw_bytes)

CLI Usage:
    python -m app.cli results load-sq3 --file Strat.str
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.results.app_results import to_float, to_int

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class LoadedStrategyArchive:
    """Parsed strategy archive metadata, parameters, and trade records."""

    format_version: str
    strategy_name: str
    symbol: str
    timeframe: str
    trade_count: int
    trades: tuple[dict[str, Any], ...]
    parameters: dict[str, Any]
    xml_content: str

    def to_dict(self) -> dict[str, Any]:
        """Convert loaded archive to dictionary."""
        return {
            "format_version": self.format_version,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "trade_count": self.trade_count,
            "trades": [dict(t) for t in self.trades],
            "parameters": dict(self.parameters),
            "xml_content": self.xml_content,
        }


class LoaderSQ3Service:
    """Service loading SQ3 strategy XML and ZIP container files."""

    @classmethod
    def _extract_xml_text(cls, filename: str, payload: bytes) -> str:
        """Extract XML string from ZIP or direct UTF-8 payload."""
        if zipfile.is_zipfile(io.BytesIO(payload)):
            try:
                with zipfile.ZipFile(io.BytesIO(payload), "r") as zf:
                    xml_files = [n for n in zf.namelist() if n.lower().endswith(".xml")]
                    if not xml_files:
                        raise DomainError(
                            code="RESULTS_SQ3_MALFORMED_ARCHIVE",
                            message="ZIP archive contains no XML files",
                            details={"filename": filename},
                        )
                    return zf.read(xml_files[0]).decode("utf-8", errors="replace")
            except (zipfile.BadZipFile, KeyError) as err:
                raise DomainError(
                    code="RESULTS_SQ3_MALFORMED_ARCHIVE",
                    message="Failed to unpack ZIP archive",
                    details={"filename": filename},
                ) from err

        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as err:
            raise DomainError(
                code="RESULTS_SQ3_MALFORMED_ARCHIVE",
                message="Payload is neither a valid ZIP nor UTF-8 XML",
                details={"filename": filename},
            ) from err

    @classmethod
    def load_bytes(cls, filename: str, payload: bytes) -> LoadedStrategyArchive:
        """Parse raw SQ3 bytes from ZIP or plain XML."""
        logger.info(
            "FR-results-loader-sq3: loading %s (%d bytes)",
            filename,
            len(payload),
        )
        if not payload:
            raise DomainError(
                code="RESULTS_SQ3_MALFORMED_ARCHIVE",
                message="Archive payload cannot be empty",
                details={"filename": filename},
            )

        xml_text = cls._extract_xml_text(filename, payload)

        try:
            root = ET.fromstring(xml_text)  # noqa: S314
        except ET.ParseError as err:
            raise DomainError(
                code="RESULTS_SQ3_MALFORMED_ARCHIVE",
                message="Malformed XML content in strategy archive",
                details={"filename": filename},
            ) from err

        strategy_name = root.attrib.get("name", filename.rsplit(".", 1)[0])
        symbol = root.attrib.get("symbol", "EURUSD")
        timeframe = root.attrib.get("timeframe", "H1")

        # Extract parameters
        params: dict[str, Any] = {}
        params_node = root.find("Parameters")
        if params_node is not None:
            for p in params_node.findall("Param"):
                k = p.attrib.get("name")
                v = p.attrib.get("value")
                if k is not None and v is not None:
                    params[k] = v

        # Extract trades
        trades_list: list[dict[str, Any]] = []
        trades_node = root.find("Trades")
        if trades_node is not None:
            for t in trades_node.findall("Trade"):
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
            "FR-results-loader-sq3: parsed %s name='%s' trades=%d",
            filename,
            strategy_name,
            len(trades_list),
        )

        return LoadedStrategyArchive(
            format_version="SQ3",
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            trade_count=len(trades_list),
            trades=tuple(trades_list),
            parameters=params,
            xml_content=xml_text,
        )

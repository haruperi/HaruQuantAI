"""SQ3 legacy strategy (.str XML/ZIP) archive exporter service.

Description:
    Implements SaverSQ3Service packaging strategy parameters, settings,
    and closed trades into a compatible SQ3 .str ZIP archive readable
    by LoaderSQ3Service.

Purpose:
    FEAT-RESULTS-SAVER-SQ3: SQ3 legacy strategy archive exporter.

Key Capabilities:
    - FR-results-saver-sq3: Package strategy into .str container.

Python API Usage:
    from app.workspace.results.saver_s_q3 import SaverSQ3Service
    service = SaverSQ3Service()
    receipt = service.export_sq3("p1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results export-sq3 --strategy-id Strat_01
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ExportArtifactReceipt:
    """Receipt holding exported file metadata and byte stream."""

    filename: str
    mime_type: str
    size_bytes: int
    content_bytes: bytes

    def to_dict(self) -> dict[str, Any]:
        """Convert receipt to dictionary representation."""
        return {
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
        }


class SaverSQ3Service:
    """Service exporting strategies to SQ3 .str ZIP format."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}

    def register_in_memory_result(self, result: RunResult) -> None:
        """Register candidate result in memory."""
        self._in_memory_results[result.strategy_id] = result

    def _resolve_result(self, strategy_id: str) -> RunResult:
        if strategy_id in self._in_memory_results:
            return self._in_memory_results[strategy_id]
        if self.store is not None:
            try:
                return self.store.get_result(strategy_id)
            except DomainError:
                pass
        raise DomainError(
            code="RESULTS_STRATEGY_NOT_FOUND",
            message=f"Strategy '{strategy_id}' not found for SQ3 export",
            details={"strategy_id": strategy_id},
        )

    def export_sq3(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
    ) -> ExportArtifactReceipt:
        """Serialize strategy result to SQ3 .str ZIP container."""
        logger.info(
            "FR-results-saver-sq3: exporting proj=%s db=%s strat=%s",
            project_id,
            databank_name,
            strategy_id,
        )
        run_res = self._resolve_result(strategy_id)
        name = run_res.strategy_name or strategy_id
        symbol = str(
            run_res.strategy_payload.get(
                "symbol", run_res.metrics.get("symbol", "EURUSD")
            )
        )
        timeframe = str(
            run_res.strategy_payload.get(
                "timeframe", run_res.metrics.get("timeframe", "H1")
            )
        )

        root = ET.Element(
            "Strategy",
            {
                "formatVersion": "SQ3",
                "name": name,
                "symbol": symbol,
                "timeframe": timeframe,
            },
        )

        # Parameters
        params_node = ET.SubElement(root, "Parameters")
        for k, v in run_res.parameters.items():
            if isinstance(v, (str, int, float, bool)):
                ET.SubElement(params_node, "Param", {"name": str(k), "value": str(v)})

        # Trades
        trades_node = ET.SubElement(root, "Trades")
        for idx, t in enumerate(run_res.trades, start=1):
            ticket = str(t.get("ticket", idx))
            direction = str(t.get("type", t.get("direction", "BUY")))
            pl = str(t.get("profit_loss", t.get("pnl", 0.0)))
            ET.SubElement(
                trades_node,
                "Trade",
                {"ticket": ticket, "direction": direction, "profit_loss": pl},
            )

        xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        # Package into ZIP
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{name}.xml", xml_bytes)

        payload = zip_buf.getvalue()
        logger.info(
            "FR-results-saver-sq3: packaged %s.str (%d bytes)",
            name,
            len(payload),
        )

        return ExportArtifactReceipt(
            filename=f"{name}.str",
            mime_type="application/zip",
            size_bytes=len(payload),
            content_bytes=payload,
        )

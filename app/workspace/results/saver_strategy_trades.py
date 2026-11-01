"""Strategy executed trades CSV exporter service.

Description:
    Implements SaverStrategyTradesService exporting strategy trades to
    RFC 4180 CSV with configurable delimiter and column selections.

Purpose:
    FEAT-RESULTS-SAVER-TRADES: Executed trades CSV exporter service.

Key Capabilities:
    - FR-results-saver-trades: Export executed trades to RFC 4180 CSV.

Python API Usage:
    from app.workspace.results.saver_strategy_trades import (
        SaverStrategyTradesService,
    )
    service = SaverStrategyTradesService()
    receipt = service.export_trades_csv("p1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results export-trades --strategy-id Strat_01
"""

from __future__ import annotations

import csv
import io
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float
from app.workspace.results.saver_s_q3 import ExportArtifactReceipt

logger = get_logger(__name__)

DEFAULT_EXPORT_COLUMNS = (
    "NumberOfTrade",
    "Ticket",
    "Symbol",
    "Type",
    "OpenTime",
    "OpenPrice",
    "Size",
    "CloseTime",
    "ClosePrice",
    "ProfitLoss",
    "ProfitLossPips",
    "ProfitLossPct",
    "Balance",
    "Drawdown",
    "Comment",
)


class SaverStrategyTradesService:
    """Service exporting strategy trades to RFC 4180 CSV."""

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
            message=f"Strategy '{strategy_id}' not found for trades export",
            details={"strategy_id": strategy_id},
        )

    def export_trades_csv(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        delimiter: str = ",",
        column_ids: tuple[str, ...] | None = None,
    ) -> ExportArtifactReceipt:
        """Export strategy trades to formatted CSV artifact."""
        logger.info(
            "FR-results-saver-trades: exporting proj=%s db=%s strat=%s key=%s",
            project_id,
            databank_name,
            strategy_id,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        name = run_res.strategy_name or strategy_id
        active_cols = column_ids if column_ids is not None else DEFAULT_EXPORT_COLUMNS

        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=delimiter, lineterminator="\n")

        # Write header
        writer.writerow(list(active_cols))

        initial_cap = to_float(run_res.strategy_payload.get("initial_capital", 10000.0))
        balance = initial_cap
        peak = initial_cap

        for idx, t in enumerate(run_res.trades, start=1):
            pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
            balance += pl
            peak = max(peak, balance)
            dd = min(0.0, balance - peak)

            field_map: dict[str, Any] = {
                "NumberOfTrade": idx,
                "Ticket": t.get("ticket", idx),
                "Symbol": t.get("symbol", run_res.metrics.get("symbol", "EURUSD")),
                "Type": t.get("type", t.get("direction", "BUY")),
                "OpenTime": t.get("open_time", t.get("open_time_ms", "")),
                "OpenPrice": t.get("open_price", 0.0),
                "Size": t.get("size", 1.0),
                "CloseTime": t.get("close_time", t.get("close_time_ms", "")),
                "ClosePrice": t.get("close_price", 0.0),
                "ProfitLoss": round(pl, 2),
                "ProfitLossPips": round(to_float(t.get("profit_loss_pips", 0.0)), 1),
                "ProfitLossPct": round(
                    to_float(t.get("profit_loss_pct", (pl / initial_cap) * 100.0)),
                    2,
                ),
                "Balance": round(balance, 2),
                "Drawdown": round(dd, 2),
                "Comment": t.get("comment", ""),
            }

            row = [str(field_map.get(col, "")) for col in active_cols]
            writer.writerow(row)

        csv_text = buf.getvalue()
        csv_bytes = csv_text.encode("utf-8")
        filename = f"{name}_trades.csv"

        logger.info(
            "FR-results-saver-trades: emitted %s (%d bytes)",
            filename,
            len(csv_bytes),
        )

        return ExportArtifactReceipt(
            filename=filename,
            mime_type="text/csv; charset=utf-8",
            size_bytes=len(csv_bytes),
            content_bytes=csv_bytes,
        )

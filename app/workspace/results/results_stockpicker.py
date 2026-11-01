"""Stockpicker constituent symbol breakdown and performance history service.

Description:
    Implements ResultsStockpickerService displaying per-symbol trade counts,
    win percentages, net profits, profit factors, and average holding periods.

Purpose:
    FEAT-RESULTS-STOCKPICKER: Constituent symbol metrics breakdown.

Key Capabilities:
    - FR-results-stockpicker-rows: Aggregate trades into symbol performance rows.
    - FR-results-stockpicker-ordering: Order rows by net profit descending.

Python API Usage:
    from app.workspace.results.results_stockpicker import ResultsStockpickerService
    service = ResultsStockpickerService()
    res = service.get_symbol_rows("proj_1", "Results", "SP_01")

CLI Usage:
    python -m app.cli results stockpicker --strategy-id SP_01
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float, to_int, wrap_response

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class StockpickerSymbolRow:
    """Statistical summary for an individual constituent symbol."""

    symbol: str
    trade_count: int
    winning_pct: float
    net_profit: float
    profit_factor: float
    avg_bars_in_trade: float

    def to_dict(self) -> dict[str, Any]:
        """Convert row to dictionary representation."""
        return {
            "symbol": self.symbol,
            "trade_count": self.trade_count,
            "winning_pct": self.winning_pct,
            "net_profit": self.net_profit,
            "profit_factor": self.profit_factor,
            "avg_bars_in_trade": self.avg_bars_in_trade,
        }


@dataclass(frozen=True, slots=True)
class ResultsStockpickerPayload:
    """Stockpicker symbol table payload."""

    strategy_id: str
    result_key: str
    rows: tuple[StockpickerSymbolRow, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary representation."""
        return {
            "strategy_id": self.strategy_id,
            "result_key": self.result_key,
            "rows": [r.to_dict() for r in self.rows],
        }


class ResultsStockpickerService:
    """Stockpicker constituent symbol breakdown service."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}

    def register_in_memory_result(self, result: RunResult) -> None:
        """Register an in-memory test result candidate."""
        self._in_memory_results[result.strategy_id] = result

    def _resolve_result(self, strategy_id: str) -> RunResult:
        """Resolve RunResult candidate from memory or ResultStore."""
        if strategy_id in self._in_memory_results:
            return self._in_memory_results[strategy_id]
        if self.store is not None:
            try:
                return self.store.get_result(strategy_id)
            except DomainError:
                pass
        raise DomainError(
            code="RESULTS_STRATEGY_NOT_FOUND",
            message=f"Strategy '{strategy_id}' not found for Stockpicker table",
            details={"strategy_id": strategy_id},
        )

    def get_symbol_rows(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        result_key: str = "Main",
    ) -> StandardResponse[ResultsStockpickerPayload]:
        """Group closed trades by symbol and compute statistical rows."""
        logger.info(
            "FR-results-stockpicker-rows: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        trades = run_res.trades

        # Group trades by symbol
        grouped: dict[str, list[dict[str, Any]]] = {}
        for t in trades:
            sym = str(t.get("symbol", "UNKNOWN"))
            grouped.setdefault(sym, []).append(dict(t))

        rows: list[StockpickerSymbolRow] = []
        for sym, sym_trades in grouped.items():
            trade_count = len(sym_trades)
            net_profit = sum(
                to_float(t.get("profit_loss", t.get("pnl", 0.0))) for t in sym_trades
            )
            wins = [
                to_float(t.get("profit_loss", t.get("pnl", 0.0)))
                for t in sym_trades
                if to_float(t.get("profit_loss", t.get("pnl", 0.0))) > 0.0
            ]
            losses = [
                abs(to_float(t.get("profit_loss", t.get("pnl", 0.0))))
                for t in sym_trades
                if to_float(t.get("profit_loss", t.get("pnl", 0.0))) < 0.0
            ]

            gross_profit = sum(wins)
            gross_loss = sum(losses)
            winning_pct = (
                round((len(wins) / trade_count) * 100.0, 2) if trade_count > 0 else 0.0
            )

            if gross_loss > 0.0:
                profit_factor = round(gross_profit / gross_loss, 2)
            elif gross_profit > 0.0:
                profit_factor = round(gross_profit, 2)
            else:
                profit_factor = 0.0

            total_bars = sum(
                to_int(t.get("bars_in_trade", t.get("bars", 0))) for t in sym_trades
            )
            avg_bars = round(total_bars / trade_count, 2) if trade_count > 0 else 0.0

            rows.append(
                StockpickerSymbolRow(
                    symbol=sym,
                    trade_count=trade_count,
                    winning_pct=winning_pct,
                    net_profit=round(net_profit, 2),
                    profit_factor=profit_factor,
                    avg_bars_in_trade=avg_bars,
                )
            )

        # Sort rows by net_profit descending (tie-breaker: symbol ascending)
        rows.sort(key=lambda r: (-r.net_profit, r.symbol))

        payload = ResultsStockpickerPayload(
            strategy_id=strategy_id,
            result_key=result_key,
            rows=tuple(rows),
        )

        logger.info(
            "FR-results-stockpicker-rows: evaluated %d symbol rows for strategy=%s",
            len(rows),
            strategy_id,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_stockpicker",
            data=payload,
            json_payload=payload.to_dict(),
        )

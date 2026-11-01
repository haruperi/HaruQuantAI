"""Paginated strategy trade list projection and calculation service.

Description:
    Implements ResultsTradeListService generating paginated, sortable,
    filterable trade list rows with running balance, drawdown, and
    column formatting bound to ResultsTradelistViews.

Purpose:
    FEAT-RESULTS-TRADE-LIST: Paginated trade list projection.

Key Capabilities:
    - FR-results-tradelist-pagination: Paginate trades with running balance.
    - FR-results-tradelist-filtering: Filter trades by direction and sample.

Python API Usage:
    from app.workspace.results.results_trade_list import ResultsTradeListService
    service = ResultsTradeListService()
    page = service.get_trades("proj_1", "Results", "Strat_01", offset=0, limit=50)

CLI Usage:
    python -m app.cli results trade-list --strategy-id Strat_01 --limit 50
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float, to_int, wrap_response
from app.workspace.results.results_tradelist_views import (
    ResultsTradelistViewsService,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TradeListPage:
    """Paginated trade list result page."""

    strategy_id: str
    result_key: str
    view_id: str
    total_rows: int
    offset: int
    limit: int
    columns: tuple[str, ...]
    rows: tuple[dict[str, str | int | float | None], ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert page to dictionary representation."""
        return {
            "strategy_id": self.strategy_id,
            "result_key": self.result_key,
            "view_id": self.view_id,
            "total_rows": self.total_rows,
            "offset": self.offset,
            "limit": self.limit,
            "columns": list(self.columns),
            "rows": [dict(r) for r in self.rows],
        }


class ResultsTradeListService:
    """Strategy trade list pagination and evaluation service."""

    def __init__(
        self,
        store: ResultStore | None = None,
        views_service: ResultsTradelistViewsService | None = None,
    ) -> None:
        """Initialize service with optional ResultStore and views service."""
        self.store = store
        self.views_service = views_service or ResultsTradelistViewsService()
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
            message=f"Strategy '{strategy_id}' not found for trade list",
            details={"strategy_id": strategy_id},
        )

    def get_trades(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        view_id: str = "Default",
        sample_type: str = "FullSample",
        direction: Literal["BOTH", "LONG", "SHORT"] = "BOTH",
        sort_by: str = "NumberOfTrade",
        descending: bool = False,
        offset: int = 0,
        limit: int = 200,
    ) -> StandardResponse[TradeListPage]:
        """Query and paginate strategy closed trades with running balances."""
        logger.info(
            "FR-results-tradelist-pagination: project=%s databank=%s",
            project_id,
            databank_name,
        )
        run_res = self._resolve_result(strategy_id)
        raw_trades = [dict(t) for t in run_res.trades]

        # Apply sample_type filter
        if sample_type != "FullSample":
            raw_trades = [
                t
                for t in raw_trades
                if str(t.get("sample_type", "FullSample")).lower()
                == sample_type.lower()
            ]

        # Apply direction filter
        if direction != "BOTH":
            raw_trades = [
                t
                for t in raw_trades
                if str(t.get("type", t.get("direction", ""))).upper()
                in (("BUY", "LONG") if direction == "LONG" else ("SELL", "SHORT"))
            ]

        # Chronological sequence for running balance & drawdown computation
        initial_capital = to_float(
            run_res.strategy_payload.get("initial_capital", 10000.0)
        )
        running_balance = initial_capital
        peak_balance = initial_capital

        evaluated_rows: list[dict[str, str | int | float | None]] = []
        for idx, t in enumerate(raw_trades, start=1):
            pl = to_float(t.get("profit_loss", t.get("pnl", 0.0)))
            running_balance += pl
            peak_balance = max(peak_balance, running_balance)
            dd = min(0.0, running_balance - peak_balance)
            pct_dd = round((dd / peak_balance) * 100.0, 4) if peak_balance > 0 else 0.0

            row: dict[str, str | int | float | None] = {
                "NumberOfTrade": idx,
                "Ticket": to_int(t.get("ticket", idx)),
                "Symbol": str(t.get("symbol", "EURUSD")),
                "Type": str(t.get("type", t.get("direction", "BUY"))),
                "OpenTime": str(t.get("open_time", "")),
                "OpenPrice": to_float(t.get("open_price", 0.0)),
                "Size": to_float(t.get("size", 1.0)),
                "CloseTime": str(t.get("close_time", "")),
                "ClosePrice": to_float(t.get("close_price", 0.0)),
                "ProfitLoss": round(pl, 2),
                "ProfitLossPips": round(to_float(t.get("pips", 0.0)), 2),
                "ProfitLossPct": (
                    round((pl / initial_capital) * 100.0, 4)
                    if initial_capital > 0
                    else 0.0
                ),
                "Balance": round(running_balance, 2),
                "Drawdown": round(dd, 2),
                "PctDrawdown": pct_dd,
                "MAE": round(to_float(t.get("mae", 0.0)), 2),
                "MFE": round(to_float(t.get("mfe", 0.0)), 2),
                "Comment": str(t.get("comment", "")),
            }
            evaluated_rows.append(row)

        total_rows = len(evaluated_rows)

        # Sorting if requested
        if sort_by in (
            "NumberOfTrade",
            "ProfitLoss",
            "Balance",
            "OpenTime",
            "CloseTime",
        ):
            evaluated_rows.sort(
                key=lambda r: r.get(sort_by) if r.get(sort_by) is not None else 0,  # type: ignore[arg-type, return-value]
                reverse=descending,
            )

        # Slicing for pagination
        sliced = evaluated_rows[offset : offset + limit]

        view_def = self.views_service.get_view(view_id)
        columns = tuple(c.column_id for c in view_def.columns)

        page = TradeListPage(
            strategy_id=strategy_id,
            result_key=result_key,
            view_id=view_id,
            total_rows=total_rows,
            offset=offset,
            limit=limit,
            columns=columns,
            rows=tuple(sliced),
        )

        logger.info(
            "FR-results-tradelist-pagination: returned %d/%d trades (offset=%d)",
            len(sliced),
            total_rows,
            offset,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_trades",
            data=page,
            json_payload=page.to_dict(),
        )

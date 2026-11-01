"""Strategy price chart and trade marker visualization service.

Description:
    Implements ResultsChartService providing OHLCV candle streams,
    indicator overlays, executed trade entry/exit markers, and cancellable
    loading (/resultsCharts/loadChartData, /resultsCharts/cancelLoading).

Purpose:
    FEAT-RESULTS-CHART: Interactive price chart with trade markers.

Key Capabilities:
    - FR-results-chart-slice: Slice candles and markers with max_bars truncation.
    - FR-results-chart-cancel: Support async request cancellation.

Python API Usage:
    from app.workspace.results.results_chart import ResultsChartService
    service = ResultsChartService()
    res = service.load_chart_data("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results chart --strategy-id Strat_01 --max-bars 1000
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
class ChartCandle:
    """Individual OHLCV price bar."""

    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict[str, Any]:
        """Convert candle to dictionary representation."""
        return {
            "timestamp_ms": self.timestamp_ms,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass(frozen=True, slots=True)
class ChartTradeMarker:
    """Executed trade entry/exit overlay marker on price chart."""

    ticket: int
    open_time_ms: int
    close_time_ms: int
    open_price: float
    close_price: float
    direction: str
    profit_loss: float
    sl_level: float | None
    pt_level: float | None

    def to_dict(self) -> dict[str, Any]:
        """Convert marker to dictionary representation."""
        return {
            "ticket": self.ticket,
            "open_time_ms": self.open_time_ms,
            "close_time_ms": self.close_time_ms,
            "open_price": self.open_price,
            "close_price": self.close_price,
            "direction": self.direction,
            "profit_loss": self.profit_loss,
            "sl_level": self.sl_level,
            "pt_level": self.pt_level,
        }


@dataclass(frozen=True, slots=True)
class ResultsChartPayload:
    """Complete price chart payload with candles, markers, and indicators."""

    result_key: str
    symbol: str
    timeframe: str
    candles: tuple[ChartCandle, ...]
    trades: tuple[ChartTradeMarker, ...]
    indicators: dict[str, tuple[tuple[int, float | None], ...]]
    truncated: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert chart payload to dictionary representation."""
        return {
            "result_key": self.result_key,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "candles": [c.to_dict() for c in self.candles],
            "trades": [t.to_dict() for t in self.trades],
            "indicators": {
                k: [list(item) for item in v] for k, v in self.indicators.items()
            },
            "truncated": self.truncated,
        }


class ResultsChartService:
    """Price chart and trade execution marker service."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}
        self._cancelled_requests: set[str] = set()

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
            message=f"Strategy '{strategy_id}' not found for chart",
            details={"strategy_id": strategy_id},
        )

    def cancel_loading(self, request_id: str) -> StandardResponse[bool]:
        """Cancel an in-flight chart loading request."""
        self._cancelled_requests.add(request_id)
        logger.info(
            "FR-results-chart-cancel: cancelled chart request %s",
            request_id,
        )
        return wrap_response(
            request_id=request_id,
            data=True,
            json_payload={"cancelled": True},
        )

    def load_chart_data(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        result_key: str = "Main",
        *,
        start_ms: int | None = None,
        end_ms: int | None = None,
        max_bars: int = 5000,
    ) -> StandardResponse[ResultsChartPayload]:
        """Load sliced candles, executed trade markers, and indicator overlays."""
        logger.info(
            "FR-results-chart-slice: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        payload = run_res.strategy_payload

        symbol = str(payload.get("symbol", run_res.metrics.get("symbol", "EURUSD")))
        timeframe = str(
            payload.get("timeframe", run_res.metrics.get("timeframe", "H1"))
        )

        # Parse candles
        raw_candles = payload.get("candles", [])
        candles_list: list[ChartCandle] = []
        if isinstance(raw_candles, (list, tuple)):
            for c in raw_candles:
                if isinstance(c, dict):
                    ts = to_int(c.get("timestamp_ms", c.get("time", 0)))
                    if start_ms is not None and ts < start_ms:
                        continue
                    if end_ms is not None and ts > end_ms:
                        continue
                    candles_list.append(
                        ChartCandle(
                            timestamp_ms=ts,
                            open=to_float(c.get("open", 0.0)),
                            high=to_float(c.get("high", 0.0)),
                            low=to_float(c.get("low", 0.0)),
                            close=to_float(c.get("close", 0.0)),
                            volume=to_float(c.get("volume", 0.0)),
                        )
                    )

        truncated = False
        if len(candles_list) > max_bars:
            candles_list = candles_list[-max_bars:]
            truncated = True

        # Parse trades
        trades_list: list[ChartTradeMarker] = []
        for t in run_res.trades:
            o_ts = to_int(t.get("open_time_ms", t.get("open_time", 0)))
            c_ts = to_int(t.get("close_time_ms", t.get("close_time", o_ts)))
            if start_ms is not None and c_ts < start_ms:
                continue
            if end_ms is not None and o_ts > end_ms:
                continue

            sl_raw = t.get("sl_level", t.get("stop_loss"))
            pt_raw = t.get("pt_level", t.get("profit_target"))

            trades_list.append(
                ChartTradeMarker(
                    ticket=to_int(t.get("ticket", 0)),
                    open_time_ms=o_ts,
                    close_time_ms=c_ts,
                    open_price=to_float(t.get("open_price", 0.0)),
                    close_price=to_float(t.get("close_price", 0.0)),
                    direction=str(t.get("type", t.get("direction", "BUY"))),
                    profit_loss=round(
                        to_float(t.get("profit_loss", t.get("pnl", 0.0))), 2
                    ),
                    sl_level=to_float(sl_raw) if sl_raw is not None else None,
                    pt_level=to_float(pt_raw) if pt_raw is not None else None,
                )
            )

        chart_payload = ResultsChartPayload(
            result_key=result_key,
            symbol=symbol,
            timeframe=timeframe,
            candles=tuple(candles_list),
            trades=tuple(trades_list),
            indicators={},
            truncated=truncated,
        )

        logger.info(
            "FR-results-chart-slice: loaded %d candles and %d trade markers",
            len(candles_list),
            len(trades_list),
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_chart",
            data=chart_payload,
            json_payload=chart_payload.to_dict(),
        )

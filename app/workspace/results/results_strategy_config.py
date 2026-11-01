"""Strategy configuration and backtest execution settings inspector service.

Description:
    Implements ResultsStrategyConfigService extracting backtest data range,
    symbol, timeframe, trading options, money management parameters,
    and strategy parameters from stored strategy documents and results.

Purpose:
    FEAT-RESULTS-STRATEGY-CONFIG: Inspector for backtest configuration.

Key Capabilities:
    - FR-results-strategy-settings: Project complete backtest settings.

Python API Usage:
    from app.workspace.results.results_strategy_config import (
        ResultsStrategyConfigService,
    )
    service = ResultsStrategyConfigService()
    res = service.load_strategy_settings("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results strategy-config --strategy-id Strat_01
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import to_float, wrap_response

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class StrategySettingsProjection:
    """Complete strategy execution configuration projection."""

    strategy_id: str
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float
    precision: str
    spread_pips: float
    slippage_pips: float
    commission_description: str
    money_management: dict[str, Any]
    trading_options: dict[str, Any]
    parameters: dict[str, str | int | float | bool]

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "precision": self.precision,
            "spread_pips": self.spread_pips,
            "slippage_pips": self.slippage_pips,
            "commission_description": self.commission_description,
            "money_management": dict(self.money_management),
            "trading_options": dict(self.trading_options),
            "parameters": dict(self.parameters),
        }


class ResultsStrategyConfigService:
    """Strategy configuration inspector service."""

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
            message=f"Strategy '{strategy_id}' not found for config inspection",
            details={"strategy_id": strategy_id},
        )

    def load_strategy_settings(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        result_key: str = "Main",
    ) -> StandardResponse[StrategySettingsProjection]:
        """Load and normalize backtest settings and parameters."""
        logger.info(
            "FR-results-strategy-settings: project=%s databank=%s key=%s",
            project_id,
            databank_name,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        payload = run_res.strategy_payload

        # Extract parameters map
        params: dict[str, str | int | float | bool] = {}
        for k, v in run_res.parameters.items():
            if isinstance(v, (str, int, float, bool)):
                params[str(k)] = v

        symbol = str(payload.get("symbol", run_res.metrics.get("symbol", "EURUSD")))
        timeframe = str(
            payload.get("timeframe", run_res.metrics.get("timeframe", "H1"))
        )
        start_date = str(payload.get("start_date", "2020-01-01"))
        end_date = str(payload.get("end_date", "2025-12-31"))
        initial_cap = to_float(payload.get("initial_capital", 10000.0))
        precision = str(payload.get("precision", "MinuteDataExactTickSimulation"))
        spread = to_float(payload.get("spread_pips", 1.5))
        slippage = to_float(payload.get("slippage_pips", 0.0))
        commission = str(payload.get("commission_description", "$3.50 per lot"))

        mm_raw = payload.get("money_management", {"mode": "FixedSize", "size": 0.1})
        money_management = dict(mm_raw) if isinstance(mm_raw, dict) else {}

        opts_raw = payload.get("trading_options", {"max_open_trades": 1})
        trading_options = dict(opts_raw) if isinstance(opts_raw, dict) else {}

        projection = StrategySettingsProjection(
            strategy_id=strategy_id,
            strategy_name=run_res.strategy_name or strategy_id,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_cap,
            precision=precision,
            spread_pips=spread,
            slippage_pips=slippage,
            commission_description=commission,
            money_management=money_management,
            trading_options=trading_options,
            parameters=params,
        )

        logger.info(
            "FR-results-strategy-settings: loaded config for %s (%d params)",
            strategy_id,
            len(params),
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_strategy_config",
            data=projection,
            json_payload=projection.to_dict(),
        )

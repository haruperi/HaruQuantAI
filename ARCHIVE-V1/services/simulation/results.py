"""Standard simulation result objects.

Purpose:
    Standard simulation result objects.

Classes:
    SimulationRunResult: Public class defined by this module.

Functions:
    build_symbol_summary: Public function defined by this module.

Notes:
    External-facing exports are collected in app/services/simulation/__init__.py;
    private underscore helpers remain implementation details unless preserved for API compatibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.services.simulation.config import SimulationConfig

if TYPE_CHECKING:
    from app.services.execution.core import RunResult, TradeRecord
    from app.services.simulation.data_preparation import PreparedSimulationData


@dataclass(frozen=True)
class SimulationRunResult:
    """Standard result returned by ``Engine.run(config)``."""

    config: SimulationConfig
    metadata: Mapping[str, Any]
    prepared: PreparedSimulationData
    result: RunResult
    metrics: Mapping[str, Any]

    @classmethod
    def from_run_result(
        cls,
        config: SimulationConfig,
        prepared: PreparedSimulationData,
        run_result: RunResult,
        metadata: Mapping[str, Any] | None = None,
    ) -> SimulationRunResult:
        """Public function for results.from_run_result."""
        from dataclasses import asdict

        # Extract values from metadata if provided by SimulationRunner
        meta_dict = dict(metadata or {})
        processed_ticks = int(
            meta_dict.get("processed_ticks", getattr(run_result, "processed_ticks", 0))
        )
        final_balance = float(
            meta_dict.get(
                "final_balance",
                getattr(run_result, "final_balance", config.account.initial_balance),
            )
        )
        final_equity = float(
            meta_dict.get(
                "final_equity",
                getattr(run_result, "final_equity", final_balance),
            )
        )

        symbol_summary = _build_symbol_summary_impl(
            config.data.symbols, run_result.trades
        )

        # Merge metrics (Output/Results)
        metrics = {
            "processed_ticks": processed_ticks,
            "trade_count": len(run_result.trades),
            "equity_points": len(run_result.equity_curve),
            "initial_balance": float(config.account.initial_balance),
            "final_balance": final_balance,
            "final_equity": final_equity,
            "total_profit": float(final_balance - config.account.initial_balance),
            "total_return": (
                float(
                    (final_balance - config.account.initial_balance)
                    / config.account.initial_balance
                )
                if config.account.initial_balance > 0.0
                else 0.0
            ),
            "symbol_summary": symbol_summary,
        }

        # Merge metadata (Inputs/Environment)
        # We flatten the config attributes directly into metadata
        merged_metadata = dict(asdict(config))
        # Add preparation metadata and other extras
        if "prepared" in meta_dict:
            merged_metadata["prepared"] = meta_dict["prepared"]
        merged_metadata["warnings"] = meta_dict.get("warnings", ())
        merged_metadata.update(metrics)

        return cls(
            config=config,
            metadata=merged_metadata,
            prepared=prepared,
            result=run_result,
            metrics=metrics,
        )

    @property
    def processed_ticks(self) -> int:
        """Public function for results.processed_ticks."""
        return int(self.metrics.get("processed_ticks", 0))

    @property
    def final_balance(self) -> float:
        """Public function for results.final_balance."""
        return float(self.metrics.get("final_balance", 0.0))

    @property
    def final_equity(self) -> float:
        """Public function for results.final_equity."""
        return float(self.metrics.get("final_equity", self.final_balance))

    @property
    def total_profit(self) -> float:
        """Public function for results.total_profit."""
        return float(self.metrics.get("total_profit", 0.0))

    @property
    def total_return(self) -> float:
        """Public function for results.total_return."""
        return float(self.metrics.get("total_return", 0.0))

    @property
    def trade_count(self) -> int:
        """Public function for results.trade_count."""
        return int(self.metrics.get("trade_count", 0))

    @property
    def symbol_summary(self) -> Mapping[str, Mapping[str, float]]:
        """Public function for results.symbol_summary."""
        return self.metrics.get("symbol_summary", {})

    @property
    def warnings(self) -> tuple[Any, ...]:
        """Public function for results.warnings."""
        return tuple(self.metadata.get("warnings", ()))

    @property
    def trades(self) -> list[TradeRecord]:
        """Public function for results.trades."""
        return self.result.trades


def _build_symbol_summary_impl(
    symbols: tuple[str, ...],
    trades: list[TradeRecord],
) -> Mapping[str, Mapping[str, float]]:
    """Build a PnL summary for each symbol in the backtest."""
    summary = {s: {"trades": 0.0, "pnl": 0.0} for s in symbols}
    for trade in trades:
        symbol = str(getattr(trade, "symbol", "") or "")
        if symbol not in summary:
            summary[symbol] = {"trades": 0.0, "pnl": 0.0}
        summary[symbol]["trades"] += 1.0
        summary[symbol]["pnl"] += float(getattr(trade, "profit_loss", 0.0) or 0.0)
    return summary


# Backward-compatible name for Phase 5 tests/imports during migration.
SimulationRun = SimulationRunResult


def build_symbol_summary(
    symbols: tuple[str, ...],
    trades: list[TradeRecord],
) -> dict[str, Any]:
    """AI Tool wrapper for _build_symbol_summary_impl."""
    try:
        import pandas as pd

        from app.services.utils.logger import logger

        kwargs = {}

        kwargs["symbols"] = symbols

        kwargs["trades"] = trades

        res = _build_symbol_summary_impl(**kwargs)
        logger.info("Executed build_symbol_summary tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, dict):
            # serialize values if they are complex
            pass

        return {"status": "success", "data": data_payload}
    except Exception as error:
        from app.services.utils.logger import logger

        logger.error(f"Error in build_symbol_summary: {error!s}")
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}

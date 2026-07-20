"""High-level simulation run orchestration.

Purpose:
    High-level simulation run orchestration.

Classes:
    SimulationRunner: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in app/services/simulation/__init__.py;
    private underscore helpers remain implementation details unless preserved for API compatibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from app.services.simulation.config import SimulationConfig
from app.services.simulation.results import SimulationRunResult
from app.services.utils.logger import logger

if TYPE_CHECKING:
    from app.services.execution.core import RunResult
    from app.services.simulation.data_preparation import (
        PreparedSimulationData,
        SimulationDataPreparer,
    )


class SimulationRunner:
    """Parse config, prepare data, reset runtime, and execute simulation."""

    def __init__(
        self,
        engine: Any,
        data_preparer: SimulationDataPreparer | None = None,
    ) -> None:
        """Internal function for runner.__init__."""
        from app.services.simulation.data_preparation import SimulationDataPreparer

        self.engine = engine
        self.data_preparer = data_preparer or SimulationDataPreparer(engine)

    def run(self, config: SimulationConfig | Mapping[str, Any]) -> SimulationRunResult:
        """Public function for runner.run."""
        parsed = self._parse_config(config)
        self.engine.reset_runtime(parsed.account)
        prepared = self.data_preparer.prepare(parsed)
        processed_ticks = self._run_prepared(prepared, parsed)
        result = self.engine.get_run_result(processed_ticks=processed_ticks)
        metadata = self._metadata(
            parsed, prepared, result, processed_ticks=processed_ticks
        )
        self._report_if_requested(parsed, metadata)

        sim_result = SimulationRunResult.from_run_result(
            parsed,
            prepared,
            result,
            metadata=metadata,
        )

        # Automatic DB persistence if configured
        if parsed.reporting.save_to_db and parsed.reporting.user_id is not None:
            self._save_to_database(parsed, sim_result)

        return sim_result

    @staticmethod
    def _save_to_database(
        config: SimulationConfig, result: SimulationRunResult
    ) -> None:
        """Persist simulation run to database."""
        import pandas as pd
        from data.database.sqlite.database_operations import DatabaseManager

        from app.services.analytics.overview import (
            build_overview_payload,
            get_analytics_overview,
        )

        db = DatabaseManager()

        try:
            backtest_id = config.reporting.backtest_id

            if backtest_id is None:
                backtest_id = db.create_backtest_run(
                    strategy_name=config.strategy.name,
                    strategy_version="1.0.0",
                    start_date=pd.Timestamp(config.data.start).to_pydatetime(),
                    end_date=pd.Timestamp(config.data.end).to_pydatetime(),
                    engine_type=config.engine_type,
                    data_resolution=result.metadata.get(
                        "data_resolution", "trading_timeframe"
                    ),
                    config_hash=str(
                        hash(
                            str(config.to_dict() if hasattr(config, "to_dict") else {})
                        )
                    ),
                    symbols=list(config.data.symbols),
                    timeframes=[config.data.timeframe],
                    initial_balance=float(config.account.initial_balance),
                    alias=config.reporting.alias,
                    description=config.reporting.description,
                    user_id=config.reporting.user_id,
                )

            analytics = get_analytics_overview(
                trades=result.result.trades,
                initial_balance=float(
                    result.metrics.get(
                        "initial_balance", config.account.initial_balance
                    )
                ),
                start_time=result.metadata.get("data", {}).get("start"),
                end_time=result.metadata.get("data", {}).get("end"),
            )
            analytics["overview"] = build_overview_payload(
                result.result.trades,
                initial_balance=float(
                    result.metrics.get(
                        "initial_balance", config.account.initial_balance
                    )
                ),
                start_time=result.metadata.get("data", {}).get("start"),
                end_time=result.metadata.get("data", {}).get("end"),
                equity_curve_records=result.result.equity_curve,
                summary_overrides={
                    **analytics.get("summary", {}),
                    "processed_ticks": result.metrics.get("processed_ticks"),
                },
            )

            db.save_backtest_snapshot(
                backtest_id=backtest_id,
                metadata=dict(result.metadata),
                result=result.result.to_dict(),
                analytics=analytics,
                status="completed",
                final_balance=float(result.metrics.get("final_balance", 0.0)),
            )

            logger.info(
                f"Simulation {backtest_id} persisted to database for user {config.reporting.user_id}"
            )
        except Exception as exc:
            logger.error(f"Failed to persist simulation to database: {exc}")

    @staticmethod
    def _parse_config(config: SimulationConfig | Mapping[str, Any]) -> SimulationConfig:
        """Internal function for runner._parse_config."""
        if isinstance(config, SimulationConfig):
            return config
        return SimulationConfig.from_dict(config)

    def _run_prepared(
        self,
        prepared: PreparedSimulationData,
        config: SimulationConfig,
    ) -> int:
        """Internal function for runner._run_prepared."""
        processed_ticks = self.engine.run_prepared(prepared, config)
        return int(processed_ticks or 0)

    @staticmethod
    def _metadata(
        config: SimulationConfig,
        prepared: PreparedSimulationData,
        result: RunResult,
        processed_ticks: int = 0,
    ) -> dict[str, Any]:
        # These are used as transport to from_run_result to build metrics and metadata
        """Internal function for runner._metadata."""
        return {
            "processed_ticks": int(processed_ticks),
            "final_balance": float(
                result.equity_curve[-1].balance
                if result.equity_curve
                else config.account.initial_balance
            ),
            "final_equity": float(
                result.equity_curve[-1].equity
                if result.equity_curve
                else config.account.initial_balance
            ),
            "prepared": dict(prepared.metadata),
        }

    @staticmethod
    def _report_if_requested(
        config: SimulationConfig,
        metadata: Mapping[str, Any],
    ) -> None:
        """Internal function for runner._report_if_requested."""
        if not config.reporting.print_summary:
            return
        # Note: metadata here is from _metadata() above, not the final SimulationRunResult.metadata
        logger.info(
            "Simulation completed: "
            f"engine={config.engine_type} "
            f"symbols={config.data.symbols} "
            f"ticks={metadata['processed_ticks']} "
            f"final_equity={metadata['final_equity']:.2f}"
        )

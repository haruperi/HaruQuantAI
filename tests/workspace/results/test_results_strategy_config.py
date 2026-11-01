"""Unit tests for ResultsStrategyConfigService."""

from __future__ import annotations

from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_strategy_config import (
    ResultsStrategyConfigService,
)


class TestResultsStrategyConfigService:
    """Test suite for ResultsStrategyConfigService."""

    def test_load_strategy_settings_golden_fixture(self) -> None:
        """Verify loaded config for Strat_01 contains symbol, timeframe, params."""
        service = ResultsStrategyConfigService()
        sample = RunResult(
            result_id="res_strat_01",
            databank_id="Results",
            strategy_id="Strat_01",
            strategy_name="Strat_01",
            strategy_payload={
                "symbol": "EURUSD",
                "timeframe": "H1",
                "initial_capital": 10000.0,
                "spread_pips": 1.5,
                "slippage_pips": 0.5,
            },
            parameters={"Period": 14, "Multiplier": 2.0, "Enabled": True},
        )
        service.register_in_memory_result(sample)

        resp = service.load_strategy_settings("proj_1", "Results", "Strat_01")
        config = resp.data
        assert config.symbol == "EURUSD"
        assert config.timeframe == "H1"
        assert config.initial_capital == 10000.0
        assert config.spread_pips == 1.5
        assert config.slippage_pips == 0.5
        assert config.parameters == {"Period": 14, "Multiplier": 2.0, "Enabled": True}

        d = config.to_dict()
        assert d["strategy_id"] == "Strat_01"

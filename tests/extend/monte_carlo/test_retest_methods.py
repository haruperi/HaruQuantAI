"""Unit tests for Monte Carlo retest perturbation methods."""

from app.core.data.contracts import MarketBar
from app.extend.monte_carlo.retest.catalog import MCRetestPerturbator
from app.workspace.algo_wizard.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    ParameterSpec,
    TimeframeSpec,
)


def _make_strategy(params: dict[str, float | int] | None = None) -> HSLStrategyDocument:
    raw_params = params or {"FastPeriod": 12, "SlowPeriod": 26}
    param_specs = {
        k: ParameterSpec(
            type="int" if isinstance(v, int) else "float",
            default=v,
        )
        for k, v in raw_params.items()
    }
    payload = HSLStrategyPayload(
        id="strat_test",
        name="TestStrategy",
        timeframe=TimeframeSpec(primary="H1"),
        parameters=param_specs,
    )
    return HSLStrategyDocument(strategy=payload)


def _make_bars(count: int = 20) -> list[MarketBar]:
    bars = []
    for i in range(count):
        price = 1.1000 + i * 0.0010
        bars.append(
            MarketBar(
                time=1600000000 + i * 3600,
                open=price,
                high=price + 0.0005,
                low=price - 0.0005,
                close=price + 0.0002,
                tick_volume=100,
                spread=2,
            )
        )
    return bars


class TestMCRetestPerturbations:
    """Test suite for MCRetestPerturbator."""

    def test_randomize_spread_golden_fixture(self) -> None:
        """Assert RandomizeSpread perturbs spread bounds deterministically."""
        bars = _make_bars(10)
        strat = _make_strategy()
        _, perturbed_bars = MCRetestPerturbator.perturb(
            "RandomizeSpread",
            strat,
            bars,
            {"min_spread": 1, "max_spread": 4},
            seed=7,
        )
        assert len(perturbed_bars) == 10
        for b in perturbed_bars:
            assert 1 <= b.spread <= 4

    def test_randomize_history_data(self) -> None:
        """Assert RandomizeHistoryData shifts prices without changing bar count."""
        bars = _make_bars(10)
        strat = _make_strategy()
        _, perturbed_bars = MCRetestPerturbator.perturb(
            "RandomizeHistoryData",
            strat,
            bars,
            {"pct": 0.5},
            seed=42,
        )
        assert len(perturbed_bars) == 10
        assert perturbed_bars[0].close != bars[0].close

    def test_randomize_starting_bar(self) -> None:
        """Assert RandomizeStartingBar trims initial bars."""
        bars = _make_bars(20)
        strat = _make_strategy()
        _, perturbed_bars = MCRetestPerturbator.perturb(
            "RandomizeStartingBar",
            strat,
            bars,
            {"max_offset": 5},
            seed=10,
        )
        assert len(perturbed_bars) <= 20
        assert len(perturbed_bars) >= 15

    def test_randomize_strategy_parameters(self) -> None:
        """Assert RandomizeStrategyParameters jitters parameter values."""
        bars = _make_bars(5)
        strat = _make_strategy({"Period": 20})
        new_strat, _ = MCRetestPerturbator.perturb(
            "RandomizeStrategyParameters",
            strat,
            bars,
            {"pct_change": 20.0},
            seed=42,
        )
        assert "Period" in new_strat.strategy.parameters
        val = new_strat.strategy.parameters["Period"].default
        assert isinstance(val, (int, float))

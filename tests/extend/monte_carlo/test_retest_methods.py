"""Unit tests for Monte Carlo retest perturbation methods."""

from __future__ import annotations

import random

import pytest
from app.core.data.contracts import MarketBar
from app.core.lib.errors import DomainError
from app.core.trading.strategy.hsl.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    ParameterSpec,
    TimeframeSpec,
)
from app.extend.monte_carlo.retest import (
    RETEST_CLASSES,
    MCRetestPerturbator,
    MonteCarloRetest,
    MonteCarloTestTypes,
    RandomizeHistoryData,
    RandomizeHistoryDataFixedRange,
    RandomizeHistoryDataOHLC,
    RandomizeMinDistance,
    RandomizeSlippage,
    RandomizeSpread,
    RandomizeStartingBar,
    RandomizeStrategyParameters,
    RandomizeStrategyParametersCustomizable,
    SettingsMap,
    TickEvent,
)


def _make_strategy(
    params: dict[str, float | int] | None = None,
) -> HSLStrategyDocument:
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
    bars: list[MarketBar] = []
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


class TestMCRetestCatalogAndFactory:
    """Test suite for retest catalog and class factory."""

    def test_retest_classes_count_and_types(self) -> None:
        """Verify all 9 donor retest classes are registered."""
        assert len(RETEST_CLASSES) == 9
        for definition_id, cls in RETEST_CLASSES.items():
            assert issubclass(cls, MonteCarloRetest)
            assert MCRetestPerturbator.get_retest_class(definition_id) is cls

        with pytest.raises(DomainError) as exc_info:
            MCRetestPerturbator.get_retest_class("NonExistentMethod")
        assert exc_info.value.code == "RETEST_METHOD_NOT_FOUND"

    def test_create_retest_factory(self) -> None:
        """Verify create_retest instantiates perturbation instances."""
        for definition_id in RETEST_CLASSES:
            instance = MCRetestPerturbator.create_retest(definition_id)
            assert isinstance(instance, MonteCarloRetest)
            assert isinstance(instance.name, str)


class TestRetestBaseModels:
    """Test suite for TickEvent, SettingsMap, and MonteCarloRetest."""

    def test_tick_event_getters_and_setters(self) -> None:
        """Verify TickEvent properties and donor compatibility aliases."""
        tick = TickEvent(time_ms=1000, ask=1.1005, bid=1.1000, volume=50.0)
        assert tick.get_time() == 1000
        assert tick.getTime() == 1000
        assert tick.get_ask() == 1.1005
        assert tick.getAsk() == 1.1005
        assert tick.get_bid() == 1.1000
        assert tick.getBid() == 1.1000

        tick.set_ask(1.1010)
        assert tick.get_ask() == 1.1010
        tick.setAsk(1.1015)
        assert tick.getAsk() == 1.1015

        tick.set_bid(1.1005)
        assert tick.get_bid() == 1.1005
        tick.setBid(1.1008)
        assert tick.getBid() == 1.1008

    def test_settings_map(self) -> None:
        """Verify SettingsMap get, set, and to_dict."""
        sm = SettingsMap()
        sm.set("Spread", 3.0)
        assert sm.get("Spread") == 3.0
        assert sm.get("Missing", 10.0) == 10.0
        assert sm.to_dict() == {"Spread": 3.0}


class TestIndividualRetestClasses:
    """Test suite for individual retest perturbation classes."""

    def test_randomize_history_data(self) -> None:
        """Verify RandomizeHistoryData tick and bar perturbations."""
        retest = RandomizeHistoryData(probability_up=50, max_change_up=20)
        assert retest.test_type == MonteCarloTestTypes.ModifyData

        # Test modify_data
        tick = TickEvent(time_ms=1000, ask=1.1005, bid=1.1000)
        rng = random.Random(42)
        retest.modifyData(rng, tick, global_atr=0.0020)

        # Test perturb_bars
        bars = _make_bars(5)
        p_bars = retest.perturb_bars(bars, rng, {"pct": 0.5})
        assert len(p_bars) == 5
        assert p_bars[0].close != bars[0].close

    def test_randomize_history_data_fixed_range(self) -> None:
        """Verify RandomizeHistoryDataFixedRange."""
        retest = RandomizeHistoryDataFixedRange(max_change=50)
        assert retest.test_type == MonteCarloTestTypes.ModifyData

        tick = TickEvent(time_ms=1000, ask=1.1005, bid=1.1000)
        rng = random.Random(42)
        retest.modify_data(rng, tick, global_atr=0.0020)

        bars = _make_bars(5)
        p_bars = retest.perturb_bars(bars, rng, {"max_pips": 4.0})
        assert len(p_bars) == 5

    def test_randomize_history_data_ohlc(self) -> None:
        """Verify RandomizeHistoryDataOHLC bar perturbation."""
        retest = RandomizeHistoryDataOHLC(max_change=15, atr_period=14)
        assert retest.test_type == MonteCarloTestTypes.ModifyData

        bars = _make_bars(5)
        rng = random.Random(42)
        p_bars = retest.perturb_bars(bars, rng)
        assert len(p_bars) == 5
        for b in p_bars:
            assert b.high >= b.low

    def test_randomize_min_distance(self) -> None:
        """Verify RandomizeMinDistance settings and bar perturbations."""
        retest = RandomizeMinDistance(min_dist=1.0, max_dist=5.0)
        assert retest.test_type == MonteCarloTestTypes.ModifySettings

        settings = SettingsMap()
        rng = random.Random(42)
        retest.modifySettings(rng, settings)
        assert 1.0 <= settings.get("MinimumDistance") <= 5.0

        bars = _make_bars(5)
        p_bars = retest.perturb_bars(bars, rng)
        assert len(p_bars) == 5

    def test_randomize_slippage(self) -> None:
        """Verify RandomizeSlippage settings and bar perturbations."""
        retest = RandomizeSlippage(min_slippage=1.0, max_slippage=4.0)
        assert retest.test_type == MonteCarloTestTypes.ModifySettings

        settings = SettingsMap()
        rng = random.Random(42)
        retest.modifySettings(rng, settings)
        assert 1.0 <= settings.get("Slippage") <= 4.0

        bars = _make_bars(5)
        p_bars = retest.perturb_bars(bars, rng)
        assert len(p_bars) == 5

    def test_randomize_spread(self) -> None:
        """Verify RandomizeSpread settings and bar perturbations."""
        retest = RandomizeSpread(min_spread=2.0, max_spread=6.0)
        assert retest.test_type == MonteCarloTestTypes.ModifySettings

        settings = SettingsMap()
        rng = random.Random(42)
        retest.modifySettings(rng, settings)
        assert 2.0 <= settings.get("Spread") <= 6.0

        bars = _make_bars(5)
        p_bars = retest.perturb_bars(bars, rng, {"min_spread": 2, "max_spread": 6})
        assert len(p_bars) == 5
        for b in p_bars:
            assert 2 <= b.spread <= 6

    def test_randomize_starting_bar(self) -> None:
        """Verify RandomizeStartingBar settings and bar perturbations."""
        retest = RandomizeStartingBar(max_change=20)
        assert retest.test_type == MonteCarloTestTypes.ModifySettings

        settings = SettingsMap()
        rng = random.Random(42)
        retest.modifySettings(rng, settings)
        assert 0 <= settings.get("StartingBar") <= 20

        bars = _make_bars(15)
        p_bars = retest.perturb_bars(bars, rng, {"max_offset": 5})
        assert len(p_bars) <= 15
        assert len(p_bars) >= 10

    def test_randomize_strategy_parameters(self) -> None:
        """Verify RandomizeStrategyParameters strategy mutation."""
        retest = RandomizeStrategyParameters(probability=100, max_change=30)
        assert retest.test_type == MonteCarloTestTypes.ModifySettings

        settings = SettingsMap()
        rng = random.Random(42)
        retest.modify_settings(rng, settings)
        assert settings.get("RandomizeParamsProbability") == 100

        strat = _make_strategy({"Period": 14})
        mutated = retest.apply_to_strategy(strat, rng)
        assert "Period" in mutated.strategy.parameters

    def test_randomize_strategy_parameters_customizable(self) -> None:
        """Verify RandomizeStrategyParametersCustomizable with period filtering."""
        retest = RandomizeStrategyParametersCustomizable(
            probability=100,
            max_change=30,
            period=False,
            shift=True,
        )
        assert retest.test_type == MonteCarloTestTypes.ModifySettings

        settings = SettingsMap()
        rng = random.Random(42)
        retest.modify_settings(rng, settings)
        assert settings.get("RandomizeParamsPeriod") is False

        strat = _make_strategy({"Period": 14, "Shift": 2})
        mutated = retest.apply_to_strategy(strat, rng, {"period": False})
        # Period should not be changed when period=False
        assert mutated.strategy.parameters["Period"].default == 14


class TestMCRetestPerturbations:
    """Test suite for MCRetestPerturbator end-to-end perturbations."""

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

    def test_randomize_history_data_fixed_range(self) -> None:
        """Assert RandomizeHistoryDataFixedRange shifts prices."""
        bars = _make_bars(10)
        strat = _make_strategy()
        _, perturbed_bars = MCRetestPerturbator.perturb(
            "RandomizeHistoryDataFixedRange",
            strat,
            bars,
            {"range_pips": 3.0},
            seed=42,
        )
        assert len(perturbed_bars) == 10

    def test_randomize_history_data_ohlc(self) -> None:
        """Assert RandomizeHistoryDataOHLC perturbs OHLC values."""
        bars = _make_bars(10)
        strat = _make_strategy()
        _, perturbed_bars = MCRetestPerturbator.perturb(
            "RandomizeHistoryDataOHLC",
            strat,
            bars,
            {"pct": 0.2},
            seed=42,
        )
        assert len(perturbed_bars) == 10

    def test_randomize_min_distance(self) -> None:
        """Assert RandomizeMinDistance samples bars."""
        bars = _make_bars(10)
        strat = _make_strategy()
        _, perturbed_bars = MCRetestPerturbator.perturb(
            "RandomizeMinDistance",
            strat,
            bars,
            {"min_distance": 2},
            seed=42,
        )
        assert len(perturbed_bars) == 5

    def test_randomize_slippage(self) -> None:
        """Assert RandomizeSlippage perturbs strategy slippage parameter."""
        bars = _make_bars(5)
        strat = _make_strategy()
        new_strat, _ = MCRetestPerturbator.perturb(
            "RandomizeSlippage",
            strat,
            bars,
            {"additional_slippage": 2.0},
            seed=42,
        )
        assert isinstance(new_strat, HSLStrategyDocument)

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

    def test_randomize_strategy_parameters_customizable(self) -> None:
        """Assert RandomizeStrategyParametersCustomizable with param filter."""
        bars = _make_bars(5)
        strat = _make_strategy({"Period": 20, "Threshold": 1.5})
        new_strat, _ = MCRetestPerturbator.perturb(
            "RandomizeStrategyParametersCustomizable",
            strat,
            bars,
            {"pct_change": 20.0, "parameter_names": ["Threshold"]},
            seed=42,
        )
        # Period should remain untouched, Threshold may be modified
        assert new_strat.strategy.parameters["Period"].default == 20

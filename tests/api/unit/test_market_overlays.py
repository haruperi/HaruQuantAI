"""Unit tests for Markets-widget technical overlay composition."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.services.api.routes import market_overlays


class _Series:
    """Minimal pandas-like series used by indicator-result fixtures."""

    def __init__(self, values: tuple[float, ...]) -> None:
        self._values = values

    @property
    def iloc(self) -> _Series:
        """Return the positional-indexing facade."""
        return self

    def __getitem__(self, index: int) -> float:
        """Return one positional value."""
        return self._values[index]


def _indicator_response(values: tuple[float, ...]) -> object:
    """Build one successful Indicators-owned response fixture."""
    return SimpleNamespace(
        status="success",
        data=SimpleNamespace(
            output_columns=("value",), values={"value": _Series(values)}
        ),
    )


def _dataset() -> object:
    """Build a bounded D1 dataset fixture with a current bar."""
    records = (
        *(
            SimpleNamespace(open=1.10, high=1.106, low=1.101, close=1.104)
            for _ in range(11)
        ),
        SimpleNamespace(open=1.105, high=1.108, low=1.105, close=1.107),
    )
    return SimpleNamespace(records=records)


def test_pip_size_matches_fractional_pip_contract() -> None:
    """Three- and five-digit symbols use ten points per pip."""
    assert market_overlays._pip_size(5, 0.00001) == pytest.approx(0.0001)
    assert market_overlays._pip_size(3, 0.001) == pytest.approx(0.01)
    assert market_overlays._pip_size(2, 0.01) == pytest.approx(0.01)


def test_overlay_formulas_use_prior_settled_indicator_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Volatility, ADR, and current range match the usage-script formulas."""
    dataset = _dataset()

    def _rolling(*_args: object, **_kwargs: object) -> object:
        return _indicator_response((0.0,) * 10 + (0.125, 0.250))

    def _adr(*_args: object, **_kwargs: object) -> object:
        return _indicator_response((0.0,) * 10 + (0.005, 0.006))

    monkeypatch.setattr(
        market_overlays,
        "rolling_volatility",
        _rolling,
    )
    monkeypatch.setattr(market_overlays, "adr", _adr)

    volatility = market_overlays._compute_volatility_percent(dataset, "EURUSD")
    adr_pips, range_percent = market_overlays._compute_adr_and_range(
        dataset, 0.0001, "EURUSD"
    )

    assert volatility == pytest.approx(12.5)
    assert adr_pips == pytest.approx(50.0)
    assert range_percent == pytest.approx(60.0)


def test_build_overlay_projects_latest_daily_prices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The composed overlay carries the same latest D1 OHLC evidence."""
    dataset = _dataset()

    def _pip_size(*_args: object) -> float:
        return 0.0001

    def _daily_bars(*_args: object) -> object:
        return dataset

    def _volatility(*_args: object) -> float:
        return 12.5

    def _adr_and_range(*_args: object) -> tuple[float, float]:
        return 50.0, 60.0

    monkeypatch.setattr(market_overlays, "_resolve_pip_size", _pip_size)
    monkeypatch.setattr(market_overlays, "_fetch_daily_bars", _daily_bars)
    monkeypatch.setattr(market_overlays, "_compute_volatility_percent", _volatility)
    monkeypatch.setattr(market_overlays, "_compute_adr_and_range", _adr_and_range)

    overlay = market_overlays._build_overlay_raw("mt5", "EURUSD", "req-1")

    assert overlay.pip_size == pytest.approx(0.0001)
    assert overlay.open == pytest.approx(1.105)
    assert overlay.high == pytest.approx(1.108)
    assert overlay.low == pytest.approx(1.105)
    assert overlay.volatility_percent == pytest.approx(12.5)
    assert overlay.adr_pips == pytest.approx(50.0)
    assert overlay.range_percent_of_adr == pytest.approx(60.0)


def test_build_overlay_caches_one_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated reads reuse bounded D1 overlay evidence within the TTL."""
    market_overlays._reset_overlay_cache_for_tests()
    calls = 0

    def _build(*args: object) -> market_overlays.TechnicalOverlay:
        nonlocal calls
        calls += 1
        return market_overlays.TechnicalOverlay(volatility_percent=10.0)

    monkeypatch.setattr(market_overlays, "_build_overlay_raw", _build)

    first = market_overlays.build_technical_overlay("mt5", "EURUSD")
    second = market_overlays.build_technical_overlay("mt5", "EURUSD")

    assert first == second
    assert calls == 1


def test_build_overlay_does_not_cache_missing_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transient unavailable result is retried on the next request."""
    market_overlays._reset_overlay_cache_for_tests()
    calls = 0

    def _build(*_args: object) -> market_overlays.TechnicalOverlay:
        nonlocal calls
        calls += 1
        return market_overlays.TechnicalOverlay()

    monkeypatch.setattr(market_overlays, "_build_overlay_raw", _build)

    market_overlays.build_technical_overlay("mt5", "EURUSD")
    market_overlays.build_technical_overlay("mt5", "EURUSD")

    assert calls == 2

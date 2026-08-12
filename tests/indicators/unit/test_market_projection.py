"""Unit tests for Indicators-owned market projections."""

from types import SimpleNamespace

import pytest
from app.services.indicators.volatility import market_projection


class _Series:
    """Minimal positional series fixture."""

    def __init__(self, values: tuple[float, ...]) -> None:
        self._values = values

    @property
    def iloc(self) -> _Series:
        """Return the positional index facade."""
        return self

    def __getitem__(self, index: int) -> float:
        """Return one positional value."""
        return self._values[index]


def _response(values: tuple[float, ...]) -> object:
    """Return one successful indicator response fixture."""
    return SimpleNamespace(
        status="success",
        data=SimpleNamespace(
            output_columns=("value",),
            values={"value": _Series(values)},
        ),
    )


def _dataset() -> object:
    """Return a bounded D1 dataset fixture."""
    return SimpleNamespace(
        records=(
            *(SimpleNamespace(open=1.10, high=1.106, low=1.101) for _ in range(11)),
            SimpleNamespace(open=1.105, high=1.108, low=1.105),
        )
    )


def test_projection_owns_volatility_adr_pip_and_change_formulas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Projection uses prior settled values and broker quote precision."""
    monkeypatch.setattr(
        market_projection,
        "rolling_volatility",
        lambda *_args, **_kwargs: _response((0.0,) * 10 + (0.125, 0.25)),
    )
    monkeypatch.setattr(
        market_projection,
        "adr",
        lambda *_args, **_kwargs: _response((0.0,) * 10 + (0.005, 0.006)),
    )

    result = market_projection.project_market_overlay(
        _dataset(), digits=5, point=0.00001, last_price=1.107
    )

    assert result["volatility"] == pytest.approx(12.5)
    assert result["adr"] == pytest.approx(50.0)
    assert result["range_percent_of_adr"] == pytest.approx(60.0)
    assert result["change"] == pytest.approx(0.002)
    assert result["change_pips"] == pytest.approx(20.0)


def test_projection_rejects_invalid_point() -> None:
    """Non-positive quote precision fails explicitly."""
    with pytest.raises(ValueError, match="point must be positive"):
        market_projection.project_market_overlay(
            _dataset(), digits=5, point=0.0, last_price=None
        )

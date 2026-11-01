"""Tests for order formula evaluation, sizing selection, ATM multi-exit, and bar validity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.extend.blocks.order.atm import ATMBracket, ATMStrategy
from app.extend.blocks.order.formulas import (
    evaluate_price_level,
    price_offset_atr,
    price_offset_percent,
    price_offset_pips,
)
from app.extend.blocks.order.sizing import (
    evaluate_sizing,
    fixed_lots,
    margin_percent,
    normalize_lots,
    risk_cash,
    risk_percent,
    volatility_risk,
)
from app.extend.blocks.order.validity import (
    parse_timeframe_delta,
    schedule_bar_validity,
)
from app.include.contracts import SymbolInfo, SymbolPrice

# ---------------------------------------------------------------------------
# 1. Sizing Selection and Formulas
# ---------------------------------------------------------------------------


def test_normalize_lots_alignment_and_clamping():
    assert normalize_lots(0.014, lot_step=0.01) == 0.01
    assert normalize_lots(0.016, lot_step=0.01) == 0.02
    assert normalize_lots(0.005, min_lot=0.01) == 0.01  # Clamped to min
    assert normalize_lots(150.0, max_lot=100.0) == 100.0  # Clamped to max
    assert normalize_lots(0.0) == 0.0

    with pytest.raises(ValueError, match="nonnegative"):
        normalize_lots(-0.5)


def test_fixed_lots():
    assert fixed_lots(0.1234, lot_step=0.01) == 0.12


def test_risk_cash():
    # Risk $100 with 50 pips stop, $10/pip per standard lot -> 100 / (50 * 10) = 0.20 lots
    lots = risk_cash(100.0, 50.0, pip_value=10.0, lot_step=0.01)
    assert lots == 0.20


def test_risk_percent():
    # $10,000 equity, risk 2% = $200. Stop 40 pips, $10/pip -> 200 / (40 * 10) = 0.50 lots
    lots = risk_percent(10_000.0, 2.0, 40.0, pip_value=10.0, lot_step=0.01)
    assert lots == 0.50


def test_margin_percent():
    # $10,000 equity, 10% margin target = $1000. Price = 1.1000, 100,000 contract, 30x leverage
    # Margin/lot = (1.1000 * 100000) / 30 = 3666.67. Lots = 1000 / 3666.67 = 0.2727 -> 0.27 lots
    lots = margin_percent(10_000.0, 10.0, 1.1000, leverage=30.0, lot_step=0.01)
    assert lots == 0.27


def test_volatility_risk():
    # Cash risk $150, ATR = 15.0 points, multiplier = 2.0 (stop at 30 points), point value = $5/point
    # Risk per lot = 30 * 5 = 150. Lots = 150 / 150 = 1.00 lot
    lots = volatility_risk(150.0, 15.0, point_value=5.0, multiplier=2.0)
    assert lots == 1.00


def test_evaluate_sizing_dispatcher():
    assert evaluate_sizing("fixed", lots=0.5) == 0.5
    assert (
        evaluate_sizing(
            "cash_risk", cash_amount=100.0, stop_distance_pips=50.0, pip_value=10.0
        )
        == 0.20
    )
    assert (
        evaluate_sizing(
            "percent_equity",
            equity=10_000.0,
            risk_pct=1.0,
            stop_distance_pips=50.0,
            pip_value=10.0,
        )
        == 0.20
    )

    with pytest.raises(ValueError, match="Unknown sizing method"):
        evaluate_sizing("unsupported_method")


# ---------------------------------------------------------------------------
# 2. Price Formulas and Evaluation
# ---------------------------------------------------------------------------


def test_price_offset_pips():
    # Long Entry: 1.1000 + 20 pips (0.0001) = 1.1020
    assert price_offset_pips(
        1.1000, 1, 20.0, 0.0001, is_protective=False
    ) == pytest.approx(1.1020)
    # Long Stop: 1.1000 - 30 pips = 1.0970
    assert price_offset_pips(
        1.1000, 1, 30.0, 0.0001, is_protective=True
    ) == pytest.approx(1.0970)
    # Short Entry: 1.1000 - 20 pips = 1.0980
    assert price_offset_pips(
        1.1000, -1, 20.0, 0.0001, is_protective=False
    ) == pytest.approx(1.0980)
    # Short Stop: 1.1000 + 30 pips = 1.1030
    assert price_offset_pips(
        1.1000, -1, 30.0, 0.0001, is_protective=True
    ) == pytest.approx(1.1030)


def test_price_offset_atr():
    # Long Stop with ATR 0.0050 * 2.0 = 0.0100 -> 1.1000 - 0.0100 = 1.0900
    assert price_offset_atr(
        1.1000, 1, 0.0050, multiplier=2.0, is_protective=True
    ) == pytest.approx(1.0900)


def test_price_offset_percent():
    # Short Stop with 1% above 100.0 -> 101.0
    assert price_offset_percent(100.0, -1, 1.0, is_protective=True) == pytest.approx(
        101.0
    )


def test_evaluate_price_level_with_symbol_normalization():
    spec = SymbolInfo(name="EURUSD", price=SymbolPrice(tick_step=0.00001))
    level = evaluate_price_level(
        "pips",
        1.10000,
        1,
        pips=15.5,
        pip_size=0.0001,
        is_protective=True,
        spec=spec,
    )
    # 1.10000 - 0.00155 = 1.09845
    assert level == pytest.approx(1.09845)


# ---------------------------------------------------------------------------
# 3. Bar Validity Scheduling
# ---------------------------------------------------------------------------


def test_parse_timeframe_delta():
    assert parse_timeframe_delta("M1") == timedelta(minutes=1)
    assert parse_timeframe_delta("M5") == timedelta(minutes=5)
    assert parse_timeframe_delta("M15") == timedelta(minutes=15)
    assert parse_timeframe_delta("H1") == timedelta(hours=1)
    assert parse_timeframe_delta("H4") == timedelta(hours=4)
    assert parse_timeframe_delta("D1") == timedelta(days=1)
    assert parse_timeframe_delta("DAILY") == timedelta(days=1)
    assert parse_timeframe_delta("W1") == timedelta(weeks=1)

    with pytest.raises(ValueError, match="Unsupported timeframe"):
        parse_timeframe_delta("INVALID_TF")


def test_schedule_bar_validity():
    t0 = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
    # GTC (0 bars) returns None
    assert schedule_bar_validity(t0, "H1", 0) is None
    assert schedule_bar_validity(t0, "H1", -1) is None

    # Valid for 3 H1 bars -> 15:00 UTC
    exp = schedule_bar_validity(t0, "H1", 3)
    assert exp == datetime(2026, 10, 28, 15, 0, tzinfo=UTC)

    # Naive datetime raises
    naive_t = datetime(2026, 10, 28, 12, 0)  # noqa: DTZ001
    with pytest.raises(ValueError, match="timezone-aware"):
        schedule_bar_validity(naive_t, "H1", 2)


# ---------------------------------------------------------------------------
# 4. ATM Multi-Exit Strategy Orchestration
# ---------------------------------------------------------------------------


def test_atm_bracket_and_strategy_validation():
    b1 = ATMBracket(volume_fraction=0.6, profit_target_pips=20.0, stop_loss_pips=15.0)
    b2 = ATMBracket(
        volume_fraction=0.4,
        profit_target_pips=40.0,
        stop_loss_pips=15.0,
        trailing_distance_pips=10.0,
    )

    strategy = ATMStrategy(brackets=(b1, b2))
    assert len(strategy.brackets) == 2

    # Fractions not summing to 1.0
    with pytest.raises(ValueError, match=r"must sum to 1\.0"):
        ATMStrategy(brackets=(ATMBracket(volume_fraction=0.5),))


def test_atm_split_volume_conservation():
    b1 = ATMBracket(volume_fraction=0.5, profit_target_pips=20.0)
    b2 = ATMBracket(volume_fraction=0.5, profit_target_pips=40.0)
    strategy = ATMStrategy(brackets=(b1, b2))

    vols = strategy.split_volume(0.25, lot_step=0.01)
    assert vols == [0.12, 0.13]
    assert sum(vols) == pytest.approx(0.25)


def test_atm_build_bracket_exits():
    b1 = ATMBracket(
        volume_fraction=0.5,
        profit_target_pips=20.0,
        stop_loss_pips=10.0,
        move_sl_to_be_trigger_pips=15.0,
        move_sl_to_be_offset_pips=1.0,
    )
    b2 = ATMBracket(
        volume_fraction=0.5,
        profit_target_pips=50.0,
        stop_loss_pips=10.0,
        trailing_distance_pips=15.0,
        trailing_activation_pips=25.0,
        exit_after_bars=20,
    )
    strategy = ATMStrategy(brackets=(b1, b2))

    # Long order at 1.1000 with 0.10 lots, pip_size = 0.0001
    specs = strategy.build_bracket_exits(0.10, 1.1000, 1, pip_size=0.0001)
    assert len(specs) == 2

    # Bracket 1
    spec1 = specs[0]
    assert spec1["volume"] == 0.05
    assert spec1["profit_target"] == pytest.approx(1.1020)
    assert spec1["stop_loss"] == pytest.approx(1.0990)
    assert spec1["move_sl_to_be"]["activation"] == pytest.approx(0.0015)
    assert spec1["move_sl_to_be"]["offset"] == pytest.approx(0.0001)
    assert spec1["trailing_stop"] is None

    # Bracket 2
    spec2 = specs[1]
    assert spec2["volume"] == 0.05
    assert spec2["profit_target"] == pytest.approx(1.1050)
    assert spec2["stop_loss"] == pytest.approx(1.0990)
    assert spec2["trailing_stop"]["distance"] == pytest.approx(0.0015)
    assert spec2["trailing_stop"]["activation"] == pytest.approx(0.0025)
    assert spec2["exit_after_bars"] == 20

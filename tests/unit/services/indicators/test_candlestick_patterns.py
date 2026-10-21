"""Unit tests for CandlestickPatterns in app.services.indicators.price_action.candlestick_patterns."""

from __future__ import annotations

import pytest
from app.services.indicators.price_action.candlestick_patterns import (
    CandlestickPatterns,
)


def test_doji_tick_size_and_ratio_modes() -> None:
    """Verify Doji detection under default 0.6*tick_size and explicit doji_ratio modes."""
    # Bar 0: |O - C| = 0.00004 < 0.6 * 0.0001 (0.00006) -> True in tick_size mode
    # Bar 1: |O - C| = 0.00010 >= 0.00006, but range = 0.0020 (ratio 0.05 <= 0.10)
    # Bar 2: |O - C| = 0.00150, range = 0.0020 (ratio 0.75 -> False in both)
    o = [1.10000, 1.10000, 1.10000]
    h = [1.10100, 1.10100, 1.10200]
    low = [1.09900, 1.09900, 1.10000]
    c = [1.10004, 1.10010, 1.10150]

    res_tick = CandlestickPatterns.calculate(o, h, low, c, tick_size=0.0001, digits=5)
    assert CandlestickPatterns.is_doji(res_tick["doji"], shift=2) is True
    assert CandlestickPatterns.is_doji(res_tick, shift=1) is False
    assert CandlestickPatterns.is_doji(res_tick, shift=0) is False
    assert CandlestickPatterns.is_doji(res_tick, shift=99) is False

    res_ratio = CandlestickPatterns.calculate(
        o, h, low, c, doji_ratio=0.10, tick_size=0.0001, digits=5
    )
    assert CandlestickPatterns.is_doji(res_ratio["doji"], shift=2) is True
    assert CandlestickPatterns.is_doji(res_ratio["doji"], shift=1) is True
    assert CandlestickPatterns.is_doji(res_ratio["doji"], shift=0) is False


def test_bullish_and_bearish_engulfing_strict_body_inequality() -> None:
    """Verify BullishEngulfing and BearishEngulfing require strict body-size inequality."""
    # Bar 0 -> Bar 1: Equal bodies (O1=1.1020, C1=1.1010; O=1.1010, C=1.1020) -> False!
    # Bar 1 -> Bar 2: BearishEngulfing (O1=1.1010, C1=1.1020; O=1.1025, C=1.1005) -> True!
    # Bar 2 -> Bar 3: BullishEngulfing (O1=1.1025, C1=1.1005; O=1.1000, C=1.1030) -> True!
    o = [1.1020, 1.1010, 1.1025, 1.1000]
    h = [1.1025, 1.1025, 1.1030, 1.1035]
    low = [1.1005, 1.1005, 1.1000, 1.0995]
    c = [1.1010, 1.1020, 1.1005, 1.1030]

    res = CandlestickPatterns.calculate(o, h, low, c, tick_size=0.0001, digits=4)
    # Shift 2 is Bar 1 (equal body size -> must be False)
    assert CandlestickPatterns.is_bullish_engulfing(res, shift=2) is False
    assert CandlestickPatterns.is_bearish_engulfing(res, shift=2) is False

    # Shift 1 is Bar 2 (BearishEngulfing)
    assert CandlestickPatterns.is_bearish_engulfing(res, shift=1) is True
    assert CandlestickPatterns.is_bearish_engulfing(res["engulfing"], shift=1) is True
    assert (
        CandlestickPatterns.is_bearish_engulfing(res["bearish_engulfing"], shift=1)
        is True
    )
    assert CandlestickPatterns.is_bullish_engulfing(res, shift=1) is False

    # Shift 0 is Bar 3 (BullishEngulfing)
    assert CandlestickPatterns.is_bullish_engulfing(res, shift=0) is True
    assert CandlestickPatterns.is_bullish_engulfing(res["engulfing"], shift=0) is True
    assert CandlestickPatterns.is_bearish_engulfing(res, shift=0) is False


def test_hammer_and_shooting_star_four_bar_context() -> None:
    """Verify Hammer and ShootingStar 4-bar extrema, 12-tick range, and wick rules."""
    # Bars 0..2 set prior lows and highs:
    # L0=1.1050, L1=1.1040, L2=1.1030
    # Bar 3 (Hammer at index 3, shift=1):
    #   L=1.1000 (<= L2=1.1030, < L1=1.1040, < L0=1.1050)
    #   O=1.1025, C=1.1030 (body=0.0005, BL90_M2=0.0009)
    #   H=1.1032 (UW=0.0002, LW=0.0025 > 0.0009, LW_D4=0.000625 > UW=0.0002, CL=0.0032 >= 0.0012)
    # Bar 4 (ShootingStar at index 4, shift=0):
    #   H=1.1100 (>= H3=1.1032, > H2=1.1050, > H1=1.1060)
    #   O=1.1070, C=1.1065 (body=0.0005, BL90_M2=0.0009)
    #   L=1.1063 (LW=0.0002, UW=0.0030 > 0.0009, UW_D4=0.00075 > LW=0.0002, CL=0.0037 >= 0.0012)
    o = [1.1060, 1.1050, 1.1040, 1.1025, 1.1070]
    h = [1.1070, 1.1060, 1.1050, 1.1032, 1.1100]
    low = [1.1050, 1.1040, 1.1030, 1.1000, 1.1063]
    c = [1.1055, 1.1045, 1.1035, 1.1030, 1.1065]

    res = CandlestickPatterns.calculate(o, h, low, c, tick_size=0.0001, digits=4)
    # Shift 1 is Bar 3 (Hammer)
    assert CandlestickPatterns.is_hammer(res, shift=1) is True
    assert CandlestickPatterns.is_hammer(res["hammer"], shift=1) is True
    assert CandlestickPatterns.is_shooting_star(res, shift=1) is False
    assert CandlestickPatterns.is_bullish_pinbar(res["pinbar"], shift=1) is True

    # Shift 0 is Bar 4 (ShootingStar)
    assert CandlestickPatterns.is_shooting_star(res, shift=0) is True
    assert CandlestickPatterns.is_shooting_star(res["shooting_star"], shift=0) is True
    assert CandlestickPatterns.is_shooting_star(res["pinbar"], shift=0) is True
    assert CandlestickPatterns.is_bearish_pinbar(res["pinbar"], shift=0) is True
    assert CandlestickPatterns.is_hammer(res, shift=0) is False


def test_dark_cloud_and_piercing_line_with_min_candle_length() -> None:
    """Verify DarkCloud and PiercingLine midpoint penetration and 10-tick min length."""
    # Bar 0: Bullish candle O1=1.1000, C1=1.1040 (mid=1.1020)
    # Bar 1: DarkCloud O=1.1045, C=1.1010 (< mid 1.1020, > O1 1.1000), H=1.1050, L=1.1005
    #   HL=0.0045 >= 0.0010 (10*0.0001), OC=0.0035, OC/HL=0.777778 > 0.5 -> True!
    # Bar 2: Bearish candle O1=1.1040, C1=1.1000 (mid=1.1020)
    # Bar 3: PiercingLine O=1.0995, C=1.1030 (> mid 1.1020, < O1 1.1040), H=1.1035, L=1.0990
    #   HL=0.0045 >= 0.0010, CO=0.0035, CO/HL=0.777778 > 0.5 -> True!
    # Bar 4: Tiny candle (HL=0.0005 < 10*0.0001) -> False!
    o = [1.1000, 1.1045, 1.1040, 1.0995, 1.1032]
    h = [1.1045, 1.1050, 1.1045, 1.1035, 1.1033]
    low = [1.0995, 1.1005, 1.0995, 1.0990, 1.1028]
    c = [1.1040, 1.1010, 1.1000, 1.1030, 1.1029]

    res = CandlestickPatterns.calculate(o, h, low, c, tick_size=0.0001, digits=4)
    assert CandlestickPatterns.is_dark_cloud(res, shift=3) is True
    assert CandlestickPatterns.is_dark_cloud(res["dark_cloud"], shift=3) is True
    assert CandlestickPatterns.is_piercing_line(res, shift=1) is True
    assert CandlestickPatterns.is_piercing_line(res["piercing_line"], shift=1) is True
    assert CandlestickPatterns.is_dark_cloud(res, shift=0) is False
    assert CandlestickPatterns.is_piercing_line(res, shift=0) is False


def test_inside_bar_three_bar_and_validation() -> None:
    """Verify InsideBar, ThreeBarReversal, and parameter validation."""
    o = [1.1020, 1.1005, 1.1010, 1.1035]
    h = [1.1040, 1.1020, 1.1050, 1.1040]
    low = [1.1000, 1.0990, 1.1005, 1.0980]
    c = [1.1010, 1.1000, 1.1045, 1.0985]

    res = CandlestickPatterns.calculate(o, h, low, c)
    # Bar 2: L1 (1.0990) < L0 (1.1000) and C2 (1.1045) > H1 (1.1020) -> Bullish Three-Bar
    assert CandlestickPatterns.is_bullish_three_bar(res, shift=1) is True
    # Bar 3: H2 (1.1050) > H1 (1.1020) and C3 (1.0985) < L2 (1.1005) -> Bearish Three-Bar
    assert CandlestickPatterns.is_bearish_three_bar(res, shift=0) is True

    # Inside bar check
    o_in = [1.1000, 1.1010]
    h_in = [1.1050, 1.1030]
    l_in = [1.0950, 1.0970]
    c_in = [1.1020, 1.1015]
    res_in = CandlestickPatterns.calculate(o_in, h_in, l_in, c_in)
    assert CandlestickPatterns.is_inside_bar(res_in, shift=0) is True

    with pytest.raises(ValueError, match="empty"):
        CandlestickPatterns.calculate([], [], [], [])
    with pytest.raises(ValueError, match="doji_ratio"):
        CandlestickPatterns.calculate([1.0], [1.1], [0.9], [1.0], doji_ratio=1.5)
    with pytest.raises(ValueError, match="tick_size"):
        CandlestickPatterns.calculate([1.0], [1.1], [0.9], [1.0], tick_size=0.0)

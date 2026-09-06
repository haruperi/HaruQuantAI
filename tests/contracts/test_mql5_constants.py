"""Exact-value tests for high-risk MQL5-based constant families."""

from app.contracts.broker.trade_retcodes import (
    TRADE_RETCODE_HEDGE_PROHIBITED,
    TRADE_RETCODE_INVALID_ORDER,
    TRADE_RETCODE_POSITION_CLOSED,
)
from app.contracts.data.timeframes import (
    PERIOD_D1,
    PERIOD_H1,
    PERIOD_H12,
    PERIOD_M1,
    PERIOD_MN1,
    PERIOD_W1,
    parse_timeframe,
    timeframe_code,
)
from app.contracts.interfaces.io_constants import (
    CRYPT_ARCH_ZIP,
    CRYPT_HASH_SHA256,
)
from app.contracts.ui.chart_constants import (
    CHARTEVENT_CUSTOM,
    CHARTEVENT_CUSTOM_LAST,
)
from app.contracts.ui.color_constants import clrAliceBlue, clrBlue, clrRed
from app.contracts.ui.object_constants import OBJ_ALL_PERIODS
from app.contracts.ui.theme_constants import ENUM_THEME_COLOR, THEME_COLOR_WINDOW


def test_sparse_and_encoded_values_are_exact() -> None:
    """Encoded, sparse, rejected-gap, and bitmask values remain exact."""
    assert int(PERIOD_M1) == 1
    assert int(PERIOD_H1) == 16385
    assert int(PERIOD_H12) == 16396
    assert int(PERIOD_D1) == 16408
    assert int(PERIOD_W1) == 32769
    assert int(PERIOD_MN1) == 49153
    assert int(CHARTEVENT_CUSTOM) == 1000
    assert int(CHARTEVENT_CUSTOM_LAST) == 66534
    assert OBJ_ALL_PERIODS == 0x001FFFFF
    assert int(CRYPT_HASH_SHA256) == 5
    assert int(CRYPT_ARCH_ZIP) == 7
    assert TRADE_RETCODE_INVALID_ORDER == 10035
    assert TRADE_RETCODE_POSITION_CLOSED == 10036
    assert TRADE_RETCODE_HEDGE_PROHIBITED == 10046


def test_mql5_bgr_colors_and_theme_support_family() -> None:
    """Named colors use BGR integers and theme properties stay typed."""
    assert clrRed == 0x0000FF
    assert clrBlue == 0xFF0000
    assert clrAliceBlue == 0xFFF8F0
    assert isinstance(THEME_COLOR_WINDOW, ENUM_THEME_COLOR)
    assert int(THEME_COLOR_WINDOW) == 50


def test_standard_timeframe_boundary_helpers() -> None:
    """Canonical periods parse and encode only at explicit boundaries."""
    assert parse_timeframe("H1") is PERIOD_H1
    assert parse_timeframe("1H") is PERIOD_H1
    assert parse_timeframe(16385) is PERIOD_H1
    assert timeframe_code(PERIOD_MN1) == "MN1"

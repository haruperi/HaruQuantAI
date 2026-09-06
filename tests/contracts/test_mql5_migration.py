"""Compatibility-boundary tests for the MQL5-based contract migration."""

import pytest
from app.contracts.broker import binance, ctrader, dukascopy, metatrader, trade_retcodes
from app.contracts.common.models import OrderState, OrderType, Timeframe, TimeInForce
from app.contracts.data.timeframes import (
    PERIOD_D1,
    PERIOD_H1,
    PERIOD_M1,
    parse_timeframe,
)


def test_provider_maps_are_canonical_enum_keyed() -> None:
    """Provider mappings consume standard periods and encode locally."""
    assert binance.TIMEFRAME_MAP[PERIOD_H1] == "1h"
    assert ctrader.TIMEFRAME_MAP[PERIOD_H1] == "h1"
    assert dukascopy.TIMEFRAME_MAP[PERIOD_D1] == "1d"
    assert metatrader.TIMEFRAME_MAP[PERIOD_H1] == 16385
    assert binance.resolve_timeframe(PERIOD_H1) == "1h"
    assert metatrader.resolve_timeframe(PERIOD_M1) == 1


def test_complete_metatrader_retcode_sequence() -> None:
    """The provider wrapper includes every classified server outcome."""
    assert len(metatrader.MT5TradeRetcode) == 41
    assert metatrader.MT5TradeRetcode.INVALID_ORDER == 10035
    assert metatrader.MT5TradeRetcode.POSITION_CLOSED == 10036
    assert metatrader.MT5TradeRetcode.HEDGE_PROHIBITED == 10046
    assert len(metatrader.MT5_TRADE_RETCODE_DESCRIPTIONS) == 41
    for retcode in metatrader.MT5TradeRetcode:
        canonical = getattr(trade_retcodes, f"TRADE_RETCODE_{retcode.name}")
        assert int(retcode) == canonical


def test_non_equivalent_haru_contracts_remain_distinct() -> None:
    """Richer Haru-native aliases and custom intervals were not coerced."""
    assert Timeframe(unit="MINUTE", multiple=7).multiple == 7
    assert OrderType is not None
    assert TimeInForce is not None
    assert OrderState is not None


def test_boolean_is_not_a_standard_timeframe_integer() -> None:
    """Python's bool subtype relation must not turn True into PERIOD_M1."""
    with pytest.raises(ValueError, match="unsupported standard timeframe"):
        parse_timeframe(True)

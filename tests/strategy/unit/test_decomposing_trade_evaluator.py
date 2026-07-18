"""Decomposing Trade concrete signal tests."""

from app.services.strategy import DecomposingTradeEvaluator
from app.utils import logger

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_indicator,
    make_market,
    make_signal_config,
    make_signal_evidence,
)


def test_decomposing_trade_preserves_four_rsi_crossings() -> None:
    """Verify all four recovered RSI signal states are explicit and ordered."""
    logger.debug("Testing Decomposing Trade recovered RSI crossings")
    market = make_market(
        (("1", "2", "0", "1"), ("2", "3", "1", "2"), ("3", "4", "2", "3"))
    )
    rsi = make_indicator(
        market, indicator_id="rsi", output_column="rsi_14", values=(40, 20, 35)
    )
    config = make_signal_config(
        {"rsi_period": 14, "oversold": "30", "overbought": "70"}
    )
    evaluator = DecomposingTradeEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    signals = evaluator.evaluate_signals(
        make_signal_evidence(market), (rsi,), config, make_context()
    )
    assert tuple(signal.signal_name for signal in signals) == (
        "LONG_ENTRY",
        "SHORT_ENTRY",
        "OPPOSE_BUY",
        "OPPOSE_SELL",
    )
    assert tuple(signal.active for signal in signals) == (True, False, False, False)

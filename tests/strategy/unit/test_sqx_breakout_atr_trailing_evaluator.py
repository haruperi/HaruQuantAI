"""SQX breakout and ATR concrete signal tests."""

from app.services.strategy import SQXBreakoutAtrTrailingEvaluator
from app.utils import logger

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_indicator,
    make_market,
    make_signal_config,
    make_signal_evidence,
)


def test_sqx_preserves_prior_channel_breakout_and_atr_facts() -> None:
    """Verify a long opening breakout exposes non-executable ATR distances."""
    logger.debug("Testing recovered SQX breakout and ATR facts")
    market = make_market(
        (
            ("10", "11", "9", "10"),
            ("10", "11", "9", "10"),
            ("10", "11", "9", "10"),
            ("12", "13", "11", "12"),
        )
    )
    atr = make_indicator(
        market, indicator_id="atr", output_column="atr_2", values=(1, 1, 1, 2)
    )
    config = make_signal_config(
        {
            "breakout_lookback": 2,
            "atr_stop_period": 2,
            "stop_loss_atr_multiple": "2",
            "trailing_stop_atr_period": 2,
            "trailing_stop_atr_multiple": "3",
            "trailing_activation_atr_period": 2,
            "trailing_activation_atr_multiple": "4",
        }
    )
    evaluator = SQXBreakoutAtrTrailingEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    signals = evaluator.evaluate_signals(
        make_signal_evidence(market), (atr,), config, make_context()
    )
    assert tuple(signal.active for signal in signals) == (True, False)
    assert signals[0].facts["stop_distance"] == "4.0"
    assert signals[0].facts["trailing_distance"] == "6.0"
    assert signals[0].facts["trailing_activation_distance"] == "8.0"

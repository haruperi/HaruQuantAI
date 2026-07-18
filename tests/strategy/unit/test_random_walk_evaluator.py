"""RandomWalk concrete trigger tests."""

from app.services.strategy import RandomWalkEvaluator
from app.utils import logger

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_market,
    make_signal_config,
    make_signal_evidence,
)


def test_random_walk_emits_non_random_flat_state_triggers() -> None:
    """Verify owned magic tags deterministically suppress only active baskets."""
    logger.debug("Testing recovered non-random RandomWalk triggers")
    market = make_market((("1", "2", "0", "1"),))
    evaluator = RandomWalkEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    signals = evaluator.evaluate_signals(
        make_signal_evidence(market, active_position_tags=("magic:10:BUY",)),
        (),
        make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20}),
        make_context(),
    )
    assert tuple(signal.active for signal in signals) == (False, True)
    assert all(signal.facts["random_signal"] is False for signal in signals)

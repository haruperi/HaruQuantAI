"""Market Structure concrete signal tests."""

from decimal import Decimal

import pytest
from app.services.strategy import MarketStructureEvaluator, StrategySignalEvidence
from app.utils import logger
from pydantic import ValidationError

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_market,
    make_signal_config,
    make_signal_evidence,
)


def test_feature_evidence_must_be_provenance_complete() -> None:
    """Verify feature values cannot omit availability or provenance references."""
    logger.debug("Testing concrete Strategy feature evidence completeness")
    market = make_market((("100", "105", "95", "104"), ("104", "107", "103", "106")))
    with pytest.raises(ValidationError, match="feature evidence"):
        StrategySignalEvidence(
            evidence_id=HASH,
            primary_market=market,
            related_markets={},
            point_size=Decimal("0.00001"),
            feature_values={"zigzag_extremes": (Decimal(1),)},
            feature_available_at={},
            feature_refs={},
            active_position_tags=(),
        )


def test_market_structure_uses_exact_eight_zigzag_extremes() -> None:
    """Verify a recovered bullish break uses supplied immutable ZigZag evidence."""
    logger.debug("Testing recovered Market Structure bullish break")
    market = make_market((("100", "105", "95", "104"), ("104", "107", "103", "106")))
    values = tuple(
        Decimal(value) for value in ("110", "90", "105", "80", "100", "85", "110", "70")
    )
    evidence = make_signal_evidence(
        market,
        feature_values={"zigzag_extremes": values},
        feature_available_at={"zigzag_extremes": market.records[-1].timestamp},
        feature_refs={"zigzag_extremes": HASH},
    )
    evaluator = MarketStructureEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    signals = evaluator.evaluate_signals(
        evidence, (), make_signal_config({}), make_context()
    )
    assert tuple(signal.active for signal in signals) == (True, False)
    assert signals[0].lineage["zigzag_ref"] == HASH

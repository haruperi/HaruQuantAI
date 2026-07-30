"""Market Structure concrete signal tests."""

from decimal import Decimal

import pytest
from app.services.strategy.contracts import StrategySignalEvidence
from app.services.strategy.evaluators.market_structure import MarketStructureEvaluator
from app.utils import get_logger
from pydantic import ValidationError

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_indicator,
    make_market,
    make_signal_config,
    make_signal_evidence,
)

logger = get_logger(__name__)


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
    """Verify a bullish break uses official immutable ZigZag evidence."""
    logger.debug("Testing recovered Market Structure bullish break")
    market = make_market(
        (
            ("100", "111", "90", "100"),
            ("100", "110", "90", "100"),
            ("100", "106", "80", "100"),
            ("100", "105", "80", "100"),
            ("100", "101", "85", "100"),
            ("100", "111", "70", "100"),
            ("100", "105", "95", "104"),
            ("104", "107", "103", "106"),
        )
    )
    evidence = make_signal_evidence(market)
    zigzag = make_indicator(
        market,
        indicator_id="zigzag",
        output_column="zigzag_value_2",
        values=(110, 90, 105, 80, 100, 85, 110, 70),
    )
    evaluator = MarketStructureEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    response = evaluator.evaluate_signals(
        evidence, (zigzag,), make_signal_config({}), make_context()
    )
    assert response.data is not None
    signals = response.data
    assert tuple(signal.active for signal in signals) == (True, False)
    assert signals[0].lineage["zigzag_ref"] == HASH

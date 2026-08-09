"""Tests for the promotion contract consumer port (feature)."""

from collections.abc import Mapping

import pytest
from app.services.optimization import (
    evaluate_promotion_gate,
    get_promotion_contract_version,
)

_HASH = "a" * 64


def test_promotion_fails_closed_without_provider() -> None:
    """Missing provider yields NOT_PROMOTED, never an auto-promotion."""
    result = evaluate_promotion_gate(
        reproducibility_hash=_HASH,
        strategy_ref="strategy-v1",
        provider=None,
        final_decision="ready_for_risk_review",
    )
    assert result["promotion_status"] == "NOT_PROMOTED"
    assert result["advisory_final_decision"] == "ready_for_risk_review"
    assert result["deferred_to"] == "feature"


def test_promotion_passes_through_provider_evidence() -> None:
    """A present provider's evidence is passed through."""

    class FakeProvider:
        def evaluate_promotion(
            self, *, reproducibility_hash: str, strategy_ref: str
        ) -> Mapping[str, object]:
            del reproducibility_hash, strategy_ref
            return {"promotion_status": "APPROVED_FOR_ADOPTION"}

    result = evaluate_promotion_gate(
        reproducibility_hash=_HASH,
        strategy_ref="strategy-v1",
        provider=FakeProvider(),
        final_decision="ready_for_risk_review",
    )
    assert result["promotion_status"] == "APPROVED_FOR_ADOPTION"


def test_promotion_rejects_invalid_final_decision() -> None:
    """Unrecognized final decisions are rejected."""
    with pytest.raises(ValueError, match="recognized"):
        evaluate_promotion_gate(
            reproducibility_hash=_HASH,
            strategy_ref="strategy-v1",
            provider=None,
            final_decision="approved_for_live",
        )


def test_promotion_never_inferred() -> None:
    """Absent provider never returns APPROVED_FOR_ADOPTION."""
    result = evaluate_promotion_gate(
        reproducibility_hash=_HASH,
        strategy_ref="strategy-v1",
        provider=None,
        final_decision="ready_for_risk_review",
    )
    assert result["promotion_status"] != "APPROVED_FOR_ADOPTION"


def test_promotion_contract_version() -> None:
    """Consumer version is canonical."""
    assert get_promotion_contract_version() == "v1"

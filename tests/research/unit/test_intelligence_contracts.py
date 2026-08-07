"""Unit coverage for opaque Research intelligence contracts."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.research import create_research_value, project_research_value

_HASH = "e" * 64
_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _fundamental(**changes: object) -> object:
    """Build one opaque fundamental evidence value."""
    values: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "research.fundamental_source_evidence.v1",
        "asset_scope": ("EURUSD",),
        "issuer_scope": (),
        "document_references": ("doc-1",),
        "source_kinds": ("macro",),
        "observed_from": _NOW,
        "available_by": _NOW + timedelta(minutes=1),
        "coverage": {"macro": 1},
        "revisions": {"doc-1": 1},
        "currency_lineage": {"doc-1": "USD"},
        "unit_lineage": {"doc-1": None},
        "quality": {"trusted_records": 1},
        "canonical_hash": _HASH,
    }
    values.update(changes)
    return create_research_value("FundamentalSourceEvidence", **values)


def _sentiment(**changes: object) -> object:
    """Build one opaque sentiment evidence value."""
    values: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "research.sentiment_source_evidence.v1",
        "asset_scope": ("EURUSD",),
        "document_references": ("doc-1",),
        "event_references": (),
        "available_by": _NOW,
        "measurement_version": "lexicon-v1",
        "polarity": {"doc-1": 0.5},
        "source_coverage": {"source": 1},
        "disagreement": False,
        "missing_measurements": (),
        "revisions": {"doc-1": 1},
        "trust_evidence": {"doc-1": "trusted"},
        "manipulation_evidence": {"doc-1": "clear"},
        "injection_evidence": {"doc-1": "clear"},
        "canonical_hash": _HASH,
    }
    values.update(changes)
    return create_research_value("SentimentSourceEvidence", **values)


def test_intelligence_contracts_are_frozen_and_projectable() -> None:
    """Opaque contracts retain detached immutable mappings."""
    fundamental = project_research_value(_fundamental())
    sentiment = project_research_value(_sentiment())
    assert fundamental["coverage"] == {"macro": 1}
    assert sentiment["polarity"] == {"doc-1": 0.5}


@pytest.mark.parametrize(
    ("changes", "detail"),
    [
        ({"observed_from": _NOW.replace(tzinfo=None)}, "INTELLIGENCE_TIME_NOT_UTC"),
        ({"canonical_hash": "bad"}, "INTELLIGENCE_HASH_INVALID"),
        ({"document_references": ()}, "FUNDAMENTAL_EVIDENCE_INVALID"),
        (
            {"observed_from": _NOW + timedelta(days=1)},
            "FUNDAMENTAL_EVIDENCE_INVALID",
        ),
    ],
)
def test_fundamental_contract_rejects_invalid_evidence(
    changes: dict[str, object], detail: str
) -> None:
    """Fundamental evidence fails closed on invalid identity or chronology."""
    with pytest.raises(ValueError, match=detail):
        _fundamental(**changes)


@pytest.mark.parametrize(
    ("changes", "detail"),
    [
        ({"available_by": _NOW.replace(tzinfo=None)}, "INTELLIGENCE_TIME_NOT_UTC"),
        ({"canonical_hash": "bad"}, "INTELLIGENCE_HASH_INVALID"),
        ({"measurement_version": ""}, "SENTIMENT_EVIDENCE_INVALID"),
        ({"document_references": ()}, "SENTIMENT_EVIDENCE_INVALID"),
        ({"polarity": {"doc-1": 2.0}}, "SENTIMENT_EVIDENCE_INVALID"),
    ],
)
def test_sentiment_contract_rejects_invalid_evidence(
    changes: dict[str, object], detail: str
) -> None:
    """Sentiment evidence fails closed on invalid measurements or identity."""
    with pytest.raises(ValueError, match=detail):
        _sentiment(**changes)


def test_applicability_contract_requires_consistent_reasons() -> None:
    """Applicability status and refusal reasons cannot contradict."""
    with pytest.raises(ValueError, match="APPLICABILITY_INVALID"):
        create_research_value(
            "IntelligenceApplicability",
            status="applicable",
            asset_class="equity",
            model="issuer",
            reasons=("unexpected",),
        )

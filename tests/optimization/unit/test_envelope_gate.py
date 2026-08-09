"""Tests for the Strategy operating-envelope candidate gate (feature)."""

from decimal import Decimal

from app.services.optimization import (
    evaluate_candidate_envelope,
    filter_candidates_by_envelope,
    get_envelope_gate_contract_version,
)
from app.services.strategy import build_operating_envelope


def _envelope() -> dict[str, object]:
    """Build a valid operating envelope mapping for tests."""
    return build_operating_envelope(
        envelope_id="env-1",
        max_volatility=Decimal("0.03"),
        max_spread=Decimal("0.001"),
        min_liquidity=Decimal(100000),
        permitted_regimes=("trending",),
        permitted_sessions=("london",),
        max_holding_seconds=3600,
        blocked_event_types=("blackout_before",),
    )


_CANDIDATE: dict[str, object] = {"candidate_hash": "a" * 64}


def test_candidate_permitted_when_all_evidence_passes() -> None:
    """PERMITTED outcome when all evidence satisfies the envelope."""
    permitted, reason = evaluate_candidate_envelope(
        _CANDIDATE,
        operating_envelope=_envelope(),
        volatility=Decimal("0.01"),
        spread=Decimal("0.0005"),
        liquidity=Decimal(200000),
        regime="trending",
        session="london",
        active_event_types=(),
    )
    assert permitted is True
    assert reason is None


def test_candidate_restricted_when_regime_not_permitted() -> None:
    """RESTRICTED when regime is outside the permitted set."""
    permitted, reason = evaluate_candidate_envelope(
        _CANDIDATE,
        operating_envelope=_envelope(),
        volatility=Decimal("0.01"),
        spread=Decimal("0.0005"),
        liquidity=Decimal(200000),
        regime="choppy",
        session="london",
        active_event_types=(),
    )
    assert permitted is False
    assert reason == "operating_envelope_restricted"


def test_candidate_restricted_when_evidence_missing() -> None:
    """Missing evidence fails closed to rejection, never an inferred pass."""
    permitted, reason = evaluate_candidate_envelope(
        _CANDIDATE,
        operating_envelope=_envelope(),
        volatility=None,
        spread=Decimal("0.0005"),
        liquidity=Decimal(200000),
        regime="trending",
        session="london",
        active_event_types=(),
    )
    assert permitted is False
    assert reason == "operating_envelope_restricted"


def test_filter_candidates_partitions_correctly() -> None:
    """Filter partitions candidates into permitted and rejected without dropping."""
    candidates = {
        "a" * 64: {"candidate_hash": "a" * 64},
        "b" * 64: {"candidate_hash": "b" * 64},
    }
    evidence = {
        "volatility": Decimal("0.01"),
        "spread": Decimal("0.0005"),
        "liquidity": Decimal(200000),
        "regime": "trending",
        "session": "london",
        "active_event_types": (),
    }
    result = filter_candidates_by_envelope(
        candidates, operating_envelope=_envelope(), point_in_time_evidence=evidence
    )
    assert set(result["permitted"].keys()) == {"a" * 64, "b" * 64}
    assert result["rejected"] == {}


def test_filter_candidates_rejects_on_violation() -> None:
    """Candidates failing the envelope are rejected with a structured reason."""
    candidates = {"a" * 64: {"candidate_hash": "a" * 64}}
    evidence = {
        "volatility": Decimal("0.05"),
        "spread": Decimal("0.0005"),
        "liquidity": Decimal(200000),
        "regime": "trending",
        "session": "london",
        "active_event_types": (),
    }
    result = filter_candidates_by_envelope(
        candidates, operating_envelope=_envelope(), point_in_time_evidence=evidence
    )
    assert result["permitted"] == {}
    assert "a" * 64 in result["rejected"]
    assert (
        result["rejected"]["a" * 64]["reason_code"] == "operating_envelope_restricted"
    )


def test_envelope_gate_contract_version() -> None:
    """Consumer version is canonical."""
    assert get_envelope_gate_contract_version() == "v1"

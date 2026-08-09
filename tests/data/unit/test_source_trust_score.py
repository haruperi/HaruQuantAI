"""Unit tests for the deterministic source trust score (feature)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.data import compute_source_trust_score
from app.services.data.sources import policy
from app.utils import generate_id


@pytest.fixture
def isolated_attempts(monkeypatch: pytest.MonkeyPatch):
    """Return a setter for the fake recent-attempt history."""

    def _set(attempts: tuple[tuple[str, int], ...]) -> None:
        monkeypatch.setattr(policy, "_recent_attempts", lambda *_a, **_k: attempts)

    return _set


def test_trust_score_reflects_observed_success_ratio(isolated_attempts) -> None:
    """A 3-success/1-failure history scores exactly 75.00."""
    isolated_attempts((("SUCCESS", 1), ("SUCCESS", 2), ("SUCCESS", 3), ("FAILURE", 4)))
    response = compute_source_trust_score("mt5", request_id=generate_id("req"))
    assert response.status == "success"
    assert response.data == Decimal("75.00")


def test_trust_score_is_perfect_for_all_successes(isolated_attempts) -> None:
    """An unbroken success history scores exactly 100.00."""
    isolated_attempts((("SUCCESS", 1), ("SUCCESS", 2)))
    response = compute_source_trust_score("mt5", request_id=generate_id("req"))
    assert response.data == Decimal("100.00")


def test_trust_score_fails_closed_to_zero_with_no_evidence(isolated_attempts) -> None:
    """A source with no recorded attempts scores 0, never an assumed default."""
    isolated_attempts(())
    response = compute_source_trust_score("mt5", request_id=generate_id("req"))
    assert response.data == Decimal(0)


def test_trust_score_zero_for_all_failures(isolated_attempts) -> None:
    """An unbroken failure history scores exactly 0.00."""
    isolated_attempts((("FAILURE", 1), ("FAILURE", 2)))
    response = compute_source_trust_score("mt5", request_id=generate_id("req"))
    assert response.data == Decimal("0.00")

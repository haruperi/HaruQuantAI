"""Unit tests for market-context request and evidence contracts.

[CAP-DATA-026 Phase 7] Copy of the legacy test, re-pointed at the `evidence`
package. The legacy copy still guards its original module until Phase 11.
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts import DataError
from app.services.data.evidence.market_context_contracts import (
    MarketContextEvidence,
    MarketContextRequest,
)

from tests.data.helpers import END, START


def test_request_rejects_unknown_scope() -> None:
    """The evidence vocabulary is closed and duplicates are rejected."""
    with pytest.raises(DataError):
        MarketContextRequest(
            symbol="ABC",
            as_of=START,
            max_age_seconds=1,
            requested_evidence=("unknown",),
            timezone="UTC",
            request_id="req-165a766284f50a39de9f80e51b7c1910236bae61f97b7ba0b008c47470bbca81",
        )  # type: ignore[arg-type]


def test_missing_evidence_is_explicit() -> None:
    """Absent optional facts must be named in missing_fields."""
    with pytest.raises(DataError):
        MarketContextEvidence(
            symbol="ABC",
            correlations={},
            crisis_flags=(),
            timezone="UTC",
            as_of=START,
            expires_at=END,
            provenance={"source": "fixture"},
            missing_fields=(),
            request_id="req-920e2690aacb5670c1d16a27661943b27c995d93271a22d603075ce4e6f689cc",
        )


def test_get_market_context_evidence_raises_source_unavailable() -> None:
    """Provider failures map to stable SOURCE_UNAVAILABLE evidence."""
    from app.services.data.evidence.market_context import get_market_context_evidence

    request = MarketContextRequest(
        symbol="ABC",
        as_of=START,
        max_age_seconds=60,
        requested_evidence=("session",),
        timezone="UTC",
        request_id="req-b89bb415342811090c814e32b6f92350f6cb703de4ac8c068f751a194d49c34e",
    )
    provider = MagicMock()
    provider.get_market_context.side_effect = RuntimeError("provider secret")
    with pytest.raises(DataError) as captured:
        get_market_context_evidence(request, provider)
    assert captured.value.code == "SOURCE_UNAVAILABLE"
    assert captured.value.safe_details == {"operation": "market_context"}


def test_get_market_context_evidence_accepts_fresh_exact_evidence() -> None:
    """Acquisition returns exact fresh evidence without producing a Risk verdict."""
    from app.services.data.evidence.market_context import get_market_context_evidence

    request = MarketContextRequest(
        symbol="ABC",
        as_of=START,
        max_age_seconds=60,
        requested_evidence=("session",),
        timezone="UTC",
        request_id="req-b89bb415342811090c814e32b6f92350f6cb703de4ac8c068f751a194d49c34e",
    )
    evidence = MarketContextEvidence(
        symbol="ABC",
        session_state="open",
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=START,
        expires_at=END,
        provenance={"source": "fixture"},
        missing_fields=(
            "calendar",
            "spread",
            "liquidity",
            "volatility",
            "correlation",
            "crisis",
        ),
        request_id=request.request_id,
    )
    provider = MagicMock()
    provider.get_market_context.return_value = evidence
    assert get_market_context_evidence(request, provider) == evidence


def test_market_context_request_validation_failures() -> None:
    """Validate various validation rules of MarketContextRequest."""

    # 1. Reject non-UTC aware datetime
    with pytest.raises(DataError):
        MarketContextRequest(
            symbol="ABC",
            as_of=START.replace(tzinfo=None),  # naive datetime
            max_age_seconds=60,
            requested_evidence=("session",),
            timezone="UTC",
            request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
        )

    # 2. Reject negative/zero max_age_seconds
    with pytest.raises(DataError):
        MarketContextRequest(
            symbol="ABC",
            as_of=START,
            max_age_seconds=0,
            requested_evidence=("session",),
            timezone="UTC",
            request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
        )

    # 3. Reject duplicate requested_evidence
    with pytest.raises(DataError):
        MarketContextRequest(
            symbol="ABC",
            as_of=START,
            max_age_seconds=60,
            requested_evidence=("session", "session"),
            timezone="UTC",
            request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
        )


def test_market_context_evidence_validation_failures() -> None:
    """Validate various validation rules of MarketContextEvidence."""
    # 1. expires_at <= as_of
    with pytest.raises(DataError):
        MarketContextEvidence(
            symbol="ABC",
            timezone="UTC",
            as_of=START,
            expires_at=START,  # same, must follow
            provenance={"source": "fixture"},
            missing_fields=(),
            request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
        )

    # 2. spread present but spread_unit is None
    with pytest.raises(DataError):
        MarketContextEvidence(
            symbol="ABC",
            spread=Decimal("0.1"),
            spread_unit=None,  # missing unit
            timezone="UTC",
            as_of=START,
            expires_at=END,
            provenance={"source": "fixture"},
            missing_fields=(),
            request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
        )

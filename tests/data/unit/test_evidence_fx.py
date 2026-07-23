"""Unit tests for bounded FX path contracts.

[CAP-DATA-026 Phase 7] Copy of the legacy test, re-pointed at the `evidence`
package. The legacy copy still guards its original module until Phase 11.
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts import DataError
from app.services.data.evidence.fx_contracts import (
    FXConversionEvidence,
    FXConversionRequest,
    FXRateLeg,
)

from tests.data.helpers import END, START


def test_request_requires_explicit_policy_and_freshness() -> None:
    """The request rejects same-currency and unbounded path discovery."""
    with pytest.raises(DataError):
        FXConversionRequest(
            source_currency="USD",
            target_currency="USD",
            as_of=START,
            max_age_seconds=1,
            allowed_intermediates=(),
            max_legs=1,
            path_policy_id="fx",
            path_policy_version="v1",
            request_id="req-19bcbf5e9f7917def5093ece27886112b435d179d06778f368542bb32e69ee2b",
        )


def test_path_is_acyclic_exact_and_provenanced() -> None:
    """Composite rates must equal an ordered, acyclic leg product."""
    leg = FXRateLeg(
        source_currency="USD",
        target_currency="EUR",
        rate=Decimal("0.9"),
        source_id="fixture",
        provider_symbol="EURUSD",
        as_of=START,
        provenance={"revision": "one"},
    )
    with pytest.raises(DataError):
        FXConversionEvidence(
            source_currency="USD",
            target_currency="EUR",
            legs=(leg,),
            composite_rate=Decimal(1),
            as_of=START,
            expires_at=END,
            path_policy_id="fx",
            path_policy_version="v1",
            provenance={"selection": "one"},
            request_id="req-86a41bb55e8bda7b1bcc4f092055ac234ec568cb64dff3d0fc22d3bd702efdc8",
        )


def test_get_fx_conversion_evidence_raises_source_unavailable() -> None:
    """Provider failures map to a stable SOURCE_UNAVAILABLE boundary error."""
    from app.services.data.evidence.fx_conversion import get_fx_conversion_evidence

    request = FXConversionRequest(
        source_currency="USD",
        target_currency="JPY",
        as_of=START,
        max_age_seconds=60,
        allowed_intermediates=(),
        max_legs=1,
        path_policy_id="fx",
        path_policy_version="v1",
        request_id="req-0fa393edbb81d5a5a4a2876869c5ba3ee3a20b1477eb6ff43145b146188df532",
    )
    provider = MagicMock()
    provider.get_rate_leg.side_effect = RuntimeError("provider secret")
    with pytest.raises(DataError) as captured:
        get_fx_conversion_evidence(request, provider)
    assert captured.value.code == "SOURCE_UNAVAILABLE"
    assert captured.value.safe_details == {"operation": "fx_rate"}


def test_get_fx_conversion_evidence_uses_exact_direct_leg() -> None:
    """Acquisition preserves an exact fresh direct leg and its provenance."""
    from app.services.data.evidence.fx_conversion import get_fx_conversion_evidence

    request = FXConversionRequest(
        source_currency="USD",
        target_currency="EUR",
        as_of=START,
        max_age_seconds=60,
        allowed_intermediates=(),
        max_legs=1,
        path_policy_id="fx",
        path_policy_version="v1",
        request_id="req-0fa393edbb81d5a5a4a2876869c5ba3ee3a20b1477eb6ff43145b146188df532",
    )
    provider = MagicMock()
    provider.get_rate_leg.return_value = FXRateLeg(
        source_currency="USD",
        target_currency="EUR",
        rate=Decimal("0.9"),
        source_id="fixture",
        provider_symbol="EURUSD",
        as_of=START,
        provenance={"revision": "one"},
    )
    evidence = get_fx_conversion_evidence(request, provider)
    assert evidence.composite_rate == Decimal("0.9")
    assert evidence.legs[0].provenance == {"revision": "one"}

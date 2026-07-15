"""Unit tests for source policy and identity contracts."""

import pytest
from app.services.data.contracts import SourceIdentity, SourceLicensePolicy
from app.services.data.contracts.errors import DataError


def test_source_identity_requires_explicit_mapping_evidence() -> None:
    """Identity resolution cannot omit its mapping provenance."""
    with pytest.raises(DataError):
        SourceIdentity(
            source_id="fixture",
            canonical_symbol="ABC",
            friendly_name="ABC",
            provider_symbol="ABC.N",
            mapping_revision="map-1",
            provenance={},
            request_id="req-f0140e121439c0ae3756a0f2d773e56d9746935195678c2e936c9f592e4cf6af",
        )


def test_license_policy_fails_closed_for_validation() -> None:
    """Unknown licensing cannot permit a workflow or export."""
    with pytest.raises(DataError):
        SourceLicensePolicy(
            source_id="fixture",
            status="unknown",
            permitted_workflows=("research",),
            export_allowed=False,
            attribution_required=False,
        )

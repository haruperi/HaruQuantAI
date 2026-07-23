"""Unit tests for licence enforcement and attribution in the security module."""

from __future__ import annotations

import pytest
from app.services.data.contracts import DataError
from app.services.data.sources.contracts import SourceDescriptor, SourceLicensePolicy
from app.services.data.sources.licensing import enforce_license, get_attribution_text
from app.utils import generate_id


def _make_descriptor(
    *,
    permitted_workflows: tuple[str, ...] = ("research", "backtest"),
    status: str = "approved",
    attribution_required: bool = False,
    attribution_text: str | None = None,
) -> SourceDescriptor:
    """Construct a well-formed SourceDescriptor for unit testing."""
    return SourceDescriptor(
        source_id="test_source",
        readiness="staging",
        capabilities=("bars",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="1.0.0",
        timezone="UTC",
        revision="rev1",
        identity_mapping_revision="id_rev1",
        license_policy=SourceLicensePolicy(
            source_id="test_source",
            status=status,  # type: ignore[arg-type]
            permitted_workflows=permitted_workflows,  # type: ignore[arg-type]
            export_allowed=status == "approved",
            attribution_required=attribution_required,
            attribution_text=attribution_text,
        ),
    )


def test_permitted_workflow_passes() -> None:
    """Assert a permitted workflow passes licence enforcement without error."""
    descriptor = _make_descriptor(permitted_workflows=("research", "backtest"))
    req_id = generate_id("req")
    # Should not raise
    enforce_license(descriptor, "research", request_id=req_id)
    enforce_license(descriptor, "backtest", request_id=req_id)


def test_unpermitted_workflow_fails() -> None:
    """Assert an unpermitted workflow is rejected with LICENSE_RESTRICTION."""
    descriptor = _make_descriptor(permitted_workflows=("research",))
    req_id = generate_id("req")
    with pytest.raises(DataError) as exc_info:
        enforce_license(descriptor, "execution_bound", request_id=req_id)
    assert exc_info.value.code == "LICENSE_RESTRICTION"
    assert exc_info.value.safe_details == {"source_id": "test_source"}


def test_absent_permitted_workflows_fails_closed() -> None:
    """Assert empty permitted workflows rejects all contexts."""
    descriptor = _make_descriptor(permitted_workflows=(), status="restricted")
    req_id = generate_id("req")
    with pytest.raises(DataError) as exc_info:
        enforce_license(descriptor, "research", request_id=req_id)
    assert exc_info.value.code == "LICENSE_RESTRICTION"


def test_get_attribution_text_not_required() -> None:
    """Return empty attribution when the policy does not require one."""
    descriptor = _make_descriptor(attribution_required=False)
    req_id = generate_id("req")
    text = get_attribution_text(descriptor, request_id=req_id)
    assert text == ""


def test_get_attribution_text_required_and_declared() -> None:
    """Assert get_attribution_text returns declared text when required."""
    descriptor = _make_descriptor(
        attribution_required=True,
        attribution_text="Data provided by Test Vendor.",
    )
    req_id = generate_id("req")
    text = get_attribution_text(descriptor, request_id=req_id)
    assert text == "Data provided by Test Vendor."

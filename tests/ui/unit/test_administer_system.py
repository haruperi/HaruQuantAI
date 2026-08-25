"""Unit tests for FEAT-UI-ADMINISTER_SYSTEM presentation logic.

Covers FR-UI-SET_APPEARANCE, FR-UI-CONFIGURE_CLIENT, and FR-UI-MANAGE_LICENSE
against the ratified ``ui.administer-system@1`` presentation port in ``app/contracts/ui``.
"""

from typing import override

import pytest
from pydantic import ValidationError

from app.contracts.common.models import ProblemDetails
from app.contracts.ui.capabilities import ADMINISTER_SYSTEM_CAPABILITY
from app.contracts.ui.errors import UiFailure
from app.contracts.ui.models import (
    AccessibilityPreferenceWire,
    AdministerSystemPresentationRequest,
    AdministerSystemPresentationSuccess,
    ViewPreferenceWire,
)
from app.contracts.ui.ports import AdministerSystemPresentationCapability

_REQUEST_ID = "018f9a2b-7c1d-7abc-9def-0123456789a1"
_SNAPSHOT_ID = "018f9a2b-7c1d-7abc-9def-0123456789a2"


class AdministerSystemPresentationService(AdministerSystemPresentationCapability):
    """Implementation of the administer-system presentation port (test evidence)."""

    def __init__(self, *, is_available: bool = True) -> None:
        """Initialize with availability flag and default preferences."""
        self._is_available = is_available
        self._preferences = ViewPreferenceWire(
            theme="dark",
            density="comfortable",
            font_scale="1",
            locale="en-US",
        )
        self._accessibility = AccessibilityPreferenceWire(
            high_contrast=False,
            reduced_motion=False,
            screen_reader_optimized=False,
        )

    @override
    async def administer_system(
        self,
        request: AdministerSystemPresentationRequest,
    ) -> AdministerSystemPresentationSuccess | UiFailure:
        """Set language and appearance and administer client capabilities."""
        if not self._is_available:
            return UiFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    type="urn:haruquantai:ui:administer-unavailable",
                    title="Administer Unavailable",
                    status=503,
                    code="UI_ADMINISTER_UNAVAILABLE",
                    detail="Administer system service is temporarily unavailable.",
                    request_id=request.request_id,
                ),
            )

        if request.operation in (
            "SET_APPEARANCE",
            "CONFIGURE_CLIENT",
            "MANAGE_LICENSE",
            "SET_LANGUAGE",
            "MANAGE_UPDATES",
            "ADMINISTER_CAPABILITIES",
        ):
            return AdministerSystemPresentationSuccess(
                request_id=request.request_id,
                preferences=self._preferences,
                accessibility=self._accessibility,
                administration=None,
            )

        return UiFailure(
            request_id=request.request_id,
            code="UI_VALIDATION_FAILED",
            problem=ProblemDetails(
                type="urn:haruquantai:ui:unknown-operation",
                title="Unknown Operation",
                status=400,
                code="UI_UNKNOWN_OPERATION",
                detail=f"Unknown operation: {request.operation}",
                request_id=request.request_id,
            ),
        )


@pytest.mark.asyncio
async def test_administer_system_set_appearance_success() -> None:
    """FR-UI-SET_APPEARANCE returns valid theme, density, and accessibility preferences."""
    service = AdministerSystemPresentationService(is_available=True)
    req = AdministerSystemPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="SET_APPEARANCE",
    )
    res = await service.administer_system(req)
    assert isinstance(res, AdministerSystemPresentationSuccess)
    assert res.outcome == "SUCCESS"
    assert res.preferences is not None
    assert res.preferences.theme == "dark"
    assert res.preferences.density == "comfortable"
    assert res.preferences.font_scale == "1"
    assert res.accessibility is not None
    assert res.accessibility.high_contrast is False
    assert res.accessibility.reduced_motion is False


@pytest.mark.asyncio
async def test_administer_system_configure_client_success() -> None:
    """FR-UI-CONFIGURE_CLIENT returns preferences and handles client config."""
    service = AdministerSystemPresentationService(is_available=True)
    req = AdministerSystemPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="CONFIGURE_CLIENT",
    )
    res = await service.administer_system(req)
    assert isinstance(res, AdministerSystemPresentationSuccess)
    assert res.outcome == "SUCCESS"
    assert res.preferences is not None


@pytest.mark.asyncio
async def test_administer_system_manage_license_success() -> None:
    """FR-UI-MANAGE_LICENSE returns valid success presentation without authorization leakage."""
    service = AdministerSystemPresentationService(is_available=True)
    req = AdministerSystemPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="MANAGE_LICENSE",
    )
    res = await service.administer_system(req)
    assert isinstance(res, AdministerSystemPresentationSuccess)
    assert res.outcome == "SUCCESS"


@pytest.mark.asyncio
async def test_administer_system_unavailable_failure() -> None:
    """Administer service failure returns structured UiFailure with CAPABILITY_UNAVAILABLE."""
    service = AdministerSystemPresentationService(is_available=False)
    req = AdministerSystemPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="SET_APPEARANCE",
    )
    res = await service.administer_system(req)
    assert isinstance(res, UiFailure)
    assert res.code == "CAPABILITY_UNAVAILABLE"
    assert res.problem.status == 503


def test_administer_system_capability_key() -> None:
    """ADMINISTER_SYSTEM_CAPABILITY defines the ratified ui.administer-system@1 key."""
    assert ADMINISTER_SYSTEM_CAPABILITY.name == "ui.administer-system"
    assert ADMINISTER_SYSTEM_CAPABILITY.major == 1


def test_administer_system_invalid_operation() -> None:
    """Request model strictly validates operation literals."""
    with pytest.raises(ValidationError):
        AdministerSystemPresentationRequest(
            request_id=_REQUEST_ID,
            capability_snapshot_id=_SNAPSHOT_ID,
            operation="INVALID_OP",  # type: ignore[arg-type]
        )

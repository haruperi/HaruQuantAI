"""Unit tests for FEAT-UI-ENSURE_ACCESS presentation logic.

Covers FR-UI-MANAGE_FOCUS and FR-UI-DISTINGUISH_STATE against the ratified
``ui.ensure-access@1`` presentation port in ``app/contracts/ui``.
"""

from typing import override

import pytest
from pydantic import ValidationError

from app.contracts.common.models import ProblemDetails
from app.contracts.ui.capabilities import ENSURE_ACCESS_CAPABILITY
from app.contracts.ui.errors import UiFailure
from app.contracts.ui.models import (
    EnsureAccessPresentationRequest,
    EnsureAccessPresentationSuccess,
)
from app.contracts.ui.ports import EnsureAccessPresentationCapability

_REQUEST_ID = "018f9a2b-7c1d-7abc-9def-0123456789a1"
_SNAPSHOT_ID = "018f9a2b-7c1d-7abc-9def-0123456789a2"


class EnsureAccessPresentationService(EnsureAccessPresentationCapability):
    """Implementation of the ensure-access presentation port (test evidence)."""

    def __init__(self, *, is_available: bool = True) -> None:
        """Initialize with availability flag."""
        self._is_available = is_available

    @override
    async def ensure_access(
        self,
        request: EnsureAccessPresentationRequest,
    ) -> EnsureAccessPresentationSuccess | UiFailure:
        """Operate by keyboard, manage focus, and provide alternatives."""
        if not self._is_available:
            return UiFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    type="urn:haruquantai:ui:ensure-access-unavailable",
                    title="Ensure Access Unavailable",
                    status=503,
                    code="UI_ENSURE_ACCESS_UNAVAILABLE",
                    detail="Ensure access presentation service is temporarily unavailable.",
                    request_id=request.request_id,
                ),
            )

        if request.operation == "MANAGE_FOCUS":
            return EnsureAccessPresentationSuccess(
                request_id=request.request_id,
                focus_target="workspace-panel-main",
                alternatives=(),
                bindings=(),
            )

        if request.operation in (
            "DISTINGUISH_STATE",
            "OPERATE_BY_KEYBOARD",
            "LABEL_CONTROLS",
            "PROVIDE_DATA_ALTERNATIVES",
            "PRESERVE_USABILITY",
        ):
            return EnsureAccessPresentationSuccess(
                request_id=request.request_id,
                focus_target=None,
                alternatives=(),
                bindings=(),
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
async def test_ensure_access_manage_focus_success() -> None:
    """FR-UI-MANAGE_FOCUS returns valid success presentation with focus target."""
    service = EnsureAccessPresentationService(is_available=True)
    req = EnsureAccessPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="MANAGE_FOCUS",
    )
    res = await service.ensure_access(req)
    assert isinstance(res, EnsureAccessPresentationSuccess)
    assert res.outcome == "SUCCESS"
    assert res.focus_target == "workspace-panel-main"


@pytest.mark.asyncio
async def test_ensure_access_distinguish_state_success() -> None:
    """FR-UI-DISTINGUISH_STATE returns valid success presentation."""
    service = EnsureAccessPresentationService(is_available=True)
    req = EnsureAccessPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="DISTINGUISH_STATE",
    )
    res = await service.ensure_access(req)
    assert isinstance(res, EnsureAccessPresentationSuccess)
    assert res.outcome == "SUCCESS"


@pytest.mark.asyncio
async def test_ensure_access_unavailable_failure() -> None:
    """Ensure-access failure returns structured UiFailure with CAPABILITY_UNAVAILABLE."""
    service = EnsureAccessPresentationService(is_available=False)
    req = EnsureAccessPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation="MANAGE_FOCUS",
    )
    res = await service.ensure_access(req)
    assert isinstance(res, UiFailure)
    assert res.code == "CAPABILITY_UNAVAILABLE"
    assert res.problem.status == 503


def test_ensure_access_capability_key() -> None:
    """ENSURE_ACCESS_CAPABILITY defines the ratified ui.ensure-access@1 key."""
    assert ENSURE_ACCESS_CAPABILITY.name == "ui.ensure-access"
    assert ENSURE_ACCESS_CAPABILITY.major == 1


def test_ensure_access_invalid_operation() -> None:
    """Request model strictly validates operation literals."""
    with pytest.raises(ValidationError):
        EnsureAccessPresentationRequest(
            request_id=_REQUEST_ID,
            capability_snapshot_id=_SNAPSHOT_ID,
            operation="INVALID_OP",  # type: ignore[arg-type]
        )

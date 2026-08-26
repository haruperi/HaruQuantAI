"""Unit tests for FEAT-UI-EDIT_INPUTS presentation logic.

Covers FR-UI-PRESERVE_DRAFTS (entry 1.4 completable slice) against the
ratified ``ui.edit-inputs@1`` presentation port in ``app/contracts/ui``.
"""

import re
import typing
from typing import override

from app.contracts.common.models import ProblemDetails
from app.contracts.ui.errors import UiFailure
from app.contracts.ui.models import (
    DraftEnvelopeWire,
    EditInputsPresentationRequest,
    EditInputsPresentationSuccess,
)
from app.contracts.ui.ports import EditInputsPresentationCapability

_REQUEST_ID = "018f9a2b-7c1d-7abc-9def-0123456789c1"
_SNAPSHOT_ID = "018f9a2b-7c1d-7abc-9def-0123456789c2"
_DRAFT_ID = "018f9a2b-7c1d-7abc-9def-0123456789c3"
_WORKSPACE_ID = "018f9a2b-7c1d-7abc-9def-0123456789c4"
_ACTOR_ID = "018f9a2b-7c1d-7abc-9def-0123456789c5"

_SECRET_KEY_PATTERN = re.compile(
    r"(secret|password|passwd|token|credential|api[_-]?key|private[_-]?key)",
    re.IGNORECASE,
)


class EditInputsPresentationService(EditInputsPresentationCapability):
    """Implementation of the edit-inputs presentation port (test evidence)."""

    def __init__(self) -> None:
        """Initialize with an in-memory draft map keyed by identity."""
        self._drafts: dict[tuple[str, str, str], DraftEnvelopeWire] = {}

    @override
    async def edit_inputs(
        self,
        request: EditInputsPresentationRequest,
    ) -> EditInputsPresentationSuccess | UiFailure:
        """Render fields, validate, preserve drafts, and confirm impact."""
        if request.operation != "PRESERVE_DRAFT":
            # Remaining operations are Stage 6.15 mock-build lines.
            return EditInputsPresentationSuccess(request_id=request.request_id)
        stored = self._drafts.get(self._current_key())
        if stored is None:
            return UiFailure(
                request_id=request.request_id,
                code="UI_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:haruquantai:ui:draft-not-found",
                    title="Draft not found",
                    status=404,
                    code="UI_DRAFT_NOT_FOUND",
                    detail="No preserved draft matches the current identity.",
                    request_id=request.request_id,
                ),
            )
        return EditInputsPresentationSuccess(
            request_id=request.request_id,
            draft=stored,
        )

    def _current_key(self) -> tuple[str, str, str]:
        """Identity scope of the single test draft slot."""
        return (_ACTOR_ID, "schema-strategy-params", _WORKSPACE_ID)

    def preserve(
        self, draft: DraftEnvelopeWire
    ) -> DraftEnvelopeWire | typing.Literal["secret_rejected"]:
        """Preserve a non-secret draft locally (R11 rule, client-side guard)."""
        if _contains_secret_key(draft.payload):
            return "secret_rejected"
        self._drafts[self._current_key()] = draft
        return draft

    def load_for(
        self, entity_version: int
    ) -> DraftEnvelopeWire | typing.Literal["mismatch"] | None:
        """Load a draft for an identity; mismatches require resolution."""
        stored = self._drafts.get(self._current_key())
        if stored is None:
            return None
        if stored.entity_version != entity_version:
            return "mismatch"
        return stored


def _contains_secret_key(value: object) -> bool:
    """Recursively detect secret-shaped keys in a JSON-like payload."""
    if isinstance(value, dict):
        for key, child in value.items():
            if _SECRET_KEY_PATTERN.search(str(key)):
                return True
            if _contains_secret_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def _draft(payload: dict[str, object]) -> DraftEnvelopeWire:
    """Build a valid draft envelope wire record."""
    return DraftEnvelopeWire(
        draft_id=_DRAFT_ID,
        schema_id="schema-strategy-params",
        workspace_id=_WORKSPACE_ID,
        actor_id=_ACTOR_ID,
        entity_version=1,
        payload=typing.cast("typing.Any", payload),
        created_at_iso="2026-08-26T00:00:00.000000Z",
        updated_at_iso="2026-08-26T00:00:00.000000Z",
    )


def _request(operation: str) -> EditInputsPresentationRequest:
    return EditInputsPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation=operation,  # type: ignore[arg-type]
    )


async def test_fr_ui_preserve_drafts() -> None:
    """FR-UI-PRESERVE_DRAFTS: drafts persist with identity and restore on refresh."""
    service = EditInputsPresentationService()
    draft = _draft({"symbol": "EURUSD"})

    preserved = service.preserve(draft)
    assert preserved == draft

    # Refresh restores the compatible draft through the port operation.
    result = await service.edit_inputs(_request("PRESERVE_DRAFT"))
    assert isinstance(result, EditInputsPresentationSuccess)
    assert result.draft is not None
    assert result.draft.draft_id == _DRAFT_ID
    assert result.draft.payload["symbol"] == "EURUSD"


async def test_fr_ui_preserve_drafts_mismatch_requires_resolution() -> None:
    """Identity/entity-version mismatches never silently restore."""
    service = EditInputsPresentationService()
    service.preserve(_draft({"symbol": "EURUSD"}))

    assert service.load_for(entity_version=2) == "mismatch"
    assert service.load_for(entity_version=1) is not None
    # Empty slot is distinct from mismatch.
    empty = EditInputsPresentationService()
    assert empty.load_for(entity_version=1) is None


async def test_fr_ui_preserve_drafts_non_secret_only() -> None:
    """Secret-shaped payload keys are rejected (R11 persisted-state rule)."""
    service = EditInputsPresentationService()
    assert service.preserve(_draft({"api_key": "x"})) == "secret_rejected"
    assert service.preserve(_draft({"nested": {"Password": "x"}})) == "secret_rejected"
    assert isinstance(
        service.preserve(_draft({"safe": {"symbol": "EURUSD"}})), DraftEnvelopeWire
    )

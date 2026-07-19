"""Persistent authority-resolution and mutation retry-lock control."""

from collections.abc import Callable
from hashlib import sha256
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.trading.contracts import (
    ExecutionReceipt,
    TradingError,
    TradingRoute,
)
from app.services.trading.reconciliation.compare import (
    ReconciliationReport,
    compare_authority_state,
)
from app.services.trading.reconciliation.snapshots import AuthoritySnapshot
from app.services.trading.state import (
    TradingEvent,
    TradingProjection,
    TradingStateStore,
    apply_execution_event,
)
from app.utils import canonical_json, logger


class AuthorityResolution(BaseModel):
    """Immutable approved transition and retry decision evidence.

    Attributes:
        transition: Explicit authority transition applied to the retry lock.
        retry_allowed: Whether an approved transition permits exact retry.
        incident_reference: Persisted incident event identity.
        remaining_unresolved_scope: Ordered discrepancy identities still blocked.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.authority_resolution.v1"] = (
        "trading.authority_resolution.v1"
    )
    resolution_id: str
    receipt_id: str
    report_id: str
    transition: Literal["retry_locked", "resolved_no_retry", "approved_retry"]
    retry_allowed: bool
    incident_reference: str
    approved_transition_reference: str | None = None
    remaining_unresolved_scope: tuple[str, ...]

    @field_validator(
        "resolution_id",
        "receipt_id",
        "report_id",
        "incident_reference",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required authority-resolution identities.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.

        Raises:
            ValueError: If identity is blank or untrimmed.
        """
        logger.debug("Validating AuthorityResolution identity")
        if not value or value != value.strip():
            raise ValueError("resolution identity must be non-empty and trimmed")
        return value

    @field_validator("approved_transition_reference")
    @classmethod
    def _validate_approval(cls, value: str | None) -> str | None:
        """Validate optional approved transition reference.

        Args:
            value: Candidate approval reference.

        Returns:
            Validated reference or ``None``.

        Raises:
            ValueError: If supplied reference is blank or untrimmed.
        """
        logger.debug("Validating AuthorityResolution approval reference")
        if value is not None and (not value or value != value.strip()):
            raise ValueError("approval reference must be non-empty and trimmed")
        return value

    @field_validator("remaining_unresolved_scope")
    @classmethod
    def _validate_scope(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate ordered unresolved discrepancy scope.

        Args:
            value: Candidate unresolved identities.

        Returns:
            Validated ordered identities.

        Raises:
            ValueError: If identities are blank, duplicated, or unsorted.
        """
        logger.debug("Validating AuthorityResolution unresolved scope")
        if any(not item or item != item.strip() for item in value):
            raise ValueError("unresolved identities must be non-empty and trimmed")
        if value != tuple(sorted(set(value))):
            raise ValueError("unresolved identities must be unique and sorted")
        return value

    @model_validator(mode="after")
    def _validate_transition(self) -> Self:
        """Validate retry decision against explicit transition evidence.

        Returns:
            Validated authority resolution.

        Raises:
            ValueError: If retry or remaining scope conflicts with transition.
        """
        logger.debug("Validating AuthorityResolution transition")
        if self.transition == "approved_retry" and (
            not self.retry_allowed
            or self.approved_transition_reference is None
            or self.remaining_unresolved_scope
        ):
            raise ValueError("approved retry requires approval and resolved scope")
        if self.transition != "approved_retry" and self.retry_allowed:
            raise ValueError("retry requires an approved retry transition")
        if self.transition == "retry_locked" and not self.remaining_unresolved_scope:
            raise ValueError("retry lock requires unresolved scope")
        if self.transition == "resolved_no_retry" and self.remaining_unresolved_scope:
            raise ValueError("resolved transition cannot retain unresolved scope")
        return self


def _unresolved_scope(report: ReconciliationReport) -> tuple[str, ...]:
    """Collect all ordered unresolved report identities.

    Args:
        report: Deterministic reconciliation report.

    Returns:
        Sorted unique unresolved identities.
    """
    logger.debug("Collecting unresolved reconciliation scope")
    values = {
        *report.missing_internal_ids,
        *report.missing_authority_ids,
        *report.mismatched_ids,
    }
    if report.stale_authority:
        values.add("authority:stale")
    return tuple(sorted(values))


def _approved_retry_reference(
    receipt: ExecutionReceipt,
    projection: TradingProjection,
) -> str | None:
    """Read an exact approved retry transition from Trading state.

    Args:
        receipt: Unknown-outcome receipt being resolved.
        projection: Current Trading authority-state projection.

    Returns:
        Approval reference or ``None`` when no exact approval exists.
    """
    logger.debug("Reading approved retry transition from Trading state")
    for raw in projection.authority_state.values():
        if not isinstance(raw, dict):
            continue
        if (
            raw.get("receipt_id") == receipt.receipt_id
            and raw.get("transition") == "approved_retry"
        ):
            reference = raw.get("approved_transition_reference")
            if isinstance(reference, str) and reference:
                return reference
    return None


def _event_id(receipt: ExecutionReceipt, event_type: str) -> str:
    """Build a deterministic reconciliation event identity.

    Args:
        receipt: Receipt driving the reconciliation event.
        event_type: Finite reconciliation event category.

    Returns:
        Stable event identifier.
    """
    logger.debug("Building deterministic reconciliation event identity")
    digest = sha256(
        canonical_json(
            {"receipt_id": receipt.receipt_id, "event_type": event_type}
        ).encode()
    ).hexdigest()
    return f"trd-event-{digest}"


def _load_context(
    receipt: ExecutionReceipt,
    authority: AuthoritySnapshot,
    store: TradingStateStore,
) -> tuple[TradingProjection, str]:
    """Load exact projection and workflow context for persistence.

    Args:
        receipt: Unknown-outcome receipt.
        authority: Current route-authority snapshot.
        store: Injected Trading persistence port.

    Returns:
        Current projection and originating workflow identifier.

    Raises:
        TradingError: If persistence or originating attempt evidence is absent.
    """
    logger.debug("Loading unknown-outcome Trading persistence context")
    scope = (authority.route, authority.account_id, authority.authority_id)
    try:
        projection = store.load_projection(scope)
        attempts = store.load_unresolved_attempts(scope)
    except Exception as error:
        raise TradingError(
            "PERSISTENCE_FAILED",
            "Unknown-outcome context read failed",
        ) from error
    if projection is None:
        raise TradingError("PERSISTENCE_FAILED", "Trading projection is absent")
    attempt = next(
        (item for item in attempts if item.request_id == receipt.request_id),
        None,
    )
    if attempt is None:
        raise TradingError("PERSISTENCE_FAILED", "Originating send attempt is absent")
    return projection, attempt.workflow_id


def resolve_unknown_outcome(
    receipt: ExecutionReceipt,
    store: TradingStateStore,
    snapshot_source: Callable[[TradingRoute], AuthoritySnapshot],
) -> AuthorityResolution:
    """Persist evidence and resolve an unknown outcome without blind retry.

    Args:
        receipt: Unknown-outcome receipt requiring reconciliation.
        store: Injected Trading-owned persistence port.
        snapshot_source: Route-authority snapshot reader.

    Returns:
        Explicit retry-lock or approved transition evidence.

    Raises:
        TradingError: If receipt, authority, persistence, or transition evidence
            is absent or incompatible.
    """
    logger.info("Resolving unknown Trading outcome %s", receipt.receipt_id)
    if receipt.status != "unknown_outcome" or not receipt.reconciliation_required:
        raise TradingError("INVALID_REQUEST", "Receipt does not require reconciliation")
    try:
        authority = snapshot_source(receipt.route)
    except Exception as error:
        raise TradingError(
            "SERVICE_UNAVAILABLE",
            "Route authority snapshot is unavailable",
        ) from error
    if authority.route != receipt.route:
        raise TradingError("SCOPE_MISMATCH", "Authority route does not match receipt")
    projection, workflow_id = _load_context(receipt, authority, store)
    report = compare_authority_state(authority, projection)
    unresolved_scope = _unresolved_scope(report)
    approval_reference = _approved_retry_reference(receipt, projection)
    if unresolved_scope:
        transition = "retry_locked"
        retry_allowed = False
        approval_reference = None
    elif approval_reference is not None:
        transition = "approved_retry"
        retry_allowed = True
    else:
        transition = "resolved_no_retry"
        retry_allowed = False
    incident_id = _event_id(receipt, "incident_recorded")
    incident = TradingEvent(
        event_id=incident_id,
        event_type="incident_recorded",
        aggregate_version=projection.version,
        route=receipt.route,
        tenant_id=authority.account_id,
        authority_id=authority.authority_id,
        occurred_at=authority.observed_at,
        request_id=receipt.request_id,
        workflow_id=workflow_id,
        correlation_id=receipt.correlation_id,
        causation_id=receipt.receipt_id,
        payload={
            "receipt_id": receipt.receipt_id,
            "report_id": report.report_id,
            "retry_locked": True,
            "unresolved_scope": list(unresolved_scope),
        },
    )
    projected = apply_execution_event(incident, store)
    transition_event = TradingEvent(
        event_id=_event_id(receipt, "reconciliation_transitioned"),
        event_type="reconciliation_transitioned",
        aggregate_version=projected.version,
        route=receipt.route,
        tenant_id=authority.account_id,
        authority_id=authority.authority_id,
        occurred_at=authority.observed_at,
        request_id=receipt.request_id,
        workflow_id=workflow_id,
        correlation_id=receipt.correlation_id,
        causation_id=incident_id,
        payload={
            "receipt_id": receipt.receipt_id,
            "report_id": report.report_id,
            "transition": transition,
            "retry_allowed": retry_allowed,
            "approved_transition_reference": approval_reference,
            "remaining_unresolved_scope": list(unresolved_scope),
        },
    )
    apply_execution_event(transition_event, store)
    resolution_digest = sha256(
        canonical_json(
            {
                "receipt_id": receipt.receipt_id,
                "report_id": report.report_id,
                "transition": transition,
            }
        ).encode()
    ).hexdigest()
    return AuthorityResolution(
        resolution_id=f"trd-resolution-{resolution_digest}",
        receipt_id=receipt.receipt_id,
        report_id=report.report_id,
        transition=transition,  # type: ignore[arg-type]
        retry_allowed=retry_allowed,
        incident_reference=incident_id,
        approved_transition_reference=approval_reference,
        remaining_unresolved_scope=unresolved_scope,
    )


__all__ = ["AuthorityResolution", "resolve_unknown_outcome"]

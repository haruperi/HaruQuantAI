"""Persistence port interfaces for the live runtime service.

Defines the required persistence port contracts that the live runtime
depends on. Concrete implementations are provided by infrastructure
modules; the live service depends only on these ``Protocol`` types.

Public exports:
    LiveStateStore, AuditSink, IdempotencyStore.

Side effects:
    None. Importing this module does not open connections, start
    threads, or mutate any state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LiveStateStore(Protocol):
    """Persistence port for live runtime session state.

    Stores session state, reconciliation results, and recovery context
    required for live execution recovery and monitoring.

    Schema version: 1. Implementations must reject loads whose
    persisted schema_version does not match the requested version.
    """

    def save_session_state(
        self,
        *,
        session_id: str,
        state: dict[str, Any],
        schema_version: int = 1,
    ) -> None:
        """Persist live session state.

        Args:
            session_id: Unique session identifier.
            state: Serialisable session state dict (must be JSON-safe).
            schema_version: Schema version for compatibility checks.

        Raises:
            IOError: If the state cannot be persisted.
        """
        ...

    def load_session_state(
        self,
        *,
        session_id: str,
        schema_version: int = 1,
    ) -> dict[str, Any] | None:
        """Load persisted live session state.

        Args:
            session_id: Unique session identifier.
            schema_version: Expected schema version.

        Returns:
            Serialisable session state dict, or ``None`` if not found.

        Raises:
            IOError: If the state cannot be read.
            ValueError: If schema_version does not match the persisted
                version.
        """
        ...


@runtime_checkable
class AuditSink(Protocol):
    """Persistence port for live audit evidence.

    Audit evidence MUST be written BEFORE broker mutations. A
    write failure MUST block broker mutation; callers must treat
    every ``IOError`` from ``write_pre_event`` as a blocking error.

    Schema version: 1.
    """

    def write_pre_event(
        self,
        *,
        request_id: str,
        action: str,
        gate_results: list[dict[str, Any]],
        audit_metadata: dict[str, Any],
        recorded_at: datetime,
    ) -> str:
        """Record audit evidence before a broker mutation.

        Args:
            request_id: Trace identifier.
            action: Requested action name.
            gate_results: Serialised gate evaluation results.
            audit_metadata: Structured audit context (redacted).
            recorded_at: UTC timestamp of the pre-event.

        Returns:
            Audit reference string for correlation with the matching
            ``write_post_event`` call.

        Raises:
            IOError: If the audit record cannot be written. Callers
                MUST treat this as a hard blocking error and MUST NOT
                proceed to any broker mutation.
        """
        ...

    def write_post_event(
        self,
        *,
        audit_ref: str,
        side_effect_mode: str,
        outcome: str,
        broker_response_ref: str | None,
        recorded_at: datetime,
    ) -> None:
        """Record audit evidence after a broker mutation attempt.

        Args:
            audit_ref: Reference returned by ``write_pre_event``.
            side_effect_mode: Resulting side-effect classification.
            outcome: ``'confirmed'``, ``'rejected'``, ``'unknown'``,
                or ``'incident'``.
            broker_response_ref: Redacted broker response reference,
                or ``None`` when unavailable.
            recorded_at: UTC timestamp of the post-event.

        Raises:
            IOError: If the audit record cannot be written.
        """
        ...


@runtime_checkable
class IdempotencyStore(Protocol):
    """Persistence port for live idempotency records.

    Idempotency records MUST be persisted BEFORE any broker mutation
    attempt. If this write fails, the mutation MUST be blocked.

    Schema version: 1.
    """

    def record_intent(
        self,
        *,
        idempotency_key: str,
        action: str,
        request_hash: str,
        recorded_at: datetime,
    ) -> bool:
        """Record an idempotency intent before broker mutation.

        Args:
            idempotency_key: Stable key for this request.
            action: Requested action name.
            request_hash: Canonical hash of the request material.
            recorded_at: UTC timestamp.

        Returns:
            ``True`` when the intent is new and was recorded.
            ``False`` when the key already exists with the same
            ``request_hash`` (safe idempotent duplicate).

        Raises:
            ValueError: If the key already exists with a different
                ``request_hash`` (material conflict — must be treated
                as ``LIVE_IDEMPOTENCY_CONFLICT``).
            IOError: If the record cannot be written. Callers MUST
                treat this as a hard blocking error.
        """
        ...

    def resolve_intent(
        self,
        *,
        idempotency_key: str,
        outcome: str,
    ) -> None:
        """Update the outcome of a previously recorded intent.

        Args:
            idempotency_key: Key of the previously recorded intent.
            outcome: Final outcome string — one of ``'confirmed'``,
                ``'rejected'``, ``'unknown'``, or ``'incident'``.

        Raises:
            KeyError: If no intent exists for the key.
            IOError: If the update cannot be written.
        """
        ...

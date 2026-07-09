"""Live state reconciliation and mismatch incident handling.

Manages reconciliation of the live runtime's internal position/order
view against broker truth. Detects missing, extra, mismatched, and
stale records. Packages incidents when discrepancies exceed thresholds.

Reconciliation prefers broker truth when determining live authority
state. Startup reconciliation must complete successfully before any
live mutation is permitted.

Ownership:
    - Owns live reconciliation sequencing, mismatch detection,
      incident packaging, startup guard, and retry guard.
    - Does NOT own broker adapter calls (uses approved port interface).
    - Does NOT own shared order/position/validation contracts.

Public exports:
    ReconciliationMismatch, ReconciliationResult,
    ReconciliationStartupGuard, reconcile_state.

Side effects:
    None on import. Reconciliation occurs only when called explicitly.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.utils.errors import ValidationError
from app.utils.logger import logger

# Timestamp field names checked when looking for record age.
_TIMESTAMP_FIELDS = ("updated_at", "timestamp", "created_at", "snapshot_at")

# Severity ordering for determining overall status.
_SEVERITY_ORDER = {"critical": 3, "error": 2, "warning": 1, "info": 0}


@dataclass
class ReconciliationMismatch:
    """A single discrepancy record between internal state and broker truth.

    Attributes:
        mismatch_type: One of ``'missing_local'``, ``'extra_local'``,
            ``'field_mismatch'``, or ``'stale'``.
        entity_type: Entity kind (``'position'``, ``'order'``,
            ``'account'``).
        entity_id: Identifier of the mismatched entity.
        internal_value: Internal system value (redacted if sensitive).
        broker_value: Broker truth value (redacted if sensitive).
        severity: One of ``'info'``, ``'warning'``, ``'error'``,
            ``'critical'``.
        details: Additional structured diagnostic details.
    """

    mismatch_type: str
    entity_type: str
    entity_id: str
    internal_value: Any
    broker_value: Any
    severity: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconciliationResult:
    """Result envelope for a reconciliation run.

    Attributes:
        reconciliation_id: Unique identifier for this run.
        status: One of ``'clean'``, ``'mismatch'``, ``'unknown_outcome'``,
            ``'incident'``, or ``'error'``.
        matched_count: Records that matched between internal and broker.
        missing_count: Records present in broker but missing internally.
        extra_count: Records present internally but missing in broker.
        mismatched_count: Records present in both but with field diffs.
        stale_count: Records whose age exceeds the staleness threshold.
        mismatches: Individual mismatch records.
        incidents: Packaged incident dicts.
        started_at: UTC timestamp when reconciliation started.
        completed_at: UTC timestamp when reconciliation completed.
        request_id: Trace identifier propagated from the caller.
        correlation_id: Optional correlation identifier.
        approval_id: Optional approval ID for the requesting action.
        retry_safety: Retry classification for the caller.
        message: Human-readable summary.
    """

    reconciliation_id: str
    status: str
    matched_count: int
    missing_count: int
    extra_count: int
    mismatched_count: int
    stale_count: int
    mismatches: list[ReconciliationMismatch]
    incidents: list[dict[str, Any]]
    started_at: datetime
    completed_at: datetime
    request_id: str | None
    correlation_id: str | None
    approval_id: str | None
    retry_safety: str
    message: str


@dataclass
class ReconciliationStartupGuard:
    """Guard that blocks live mutation until startup reconciliation passes.

    A live session must call ``record_startup_reconciliation`` with a
    clean ``ReconciliationResult`` before any broker mutation is
    allowed. Querying ``is_startup_complete`` before doing so returns
    ``False``.

    Attributes:
        startup_complete: Whether startup reconciliation has completed
            successfully.
        startup_reconciliation_id: ID of the reconciliation run that
            cleared startup.
        startup_completed_at: UTC timestamp when startup was cleared.
    """

    startup_complete: bool = False
    startup_reconciliation_id: str | None = None
    startup_completed_at: datetime | None = None

    def record_startup_reconciliation(self, result: ReconciliationResult) -> bool:
        """Record the outcome of the startup reconciliation run.

        Marks startup as complete only when the result status is
        ``'clean'`` or the caller provides an operator-cleared recovery
        state. Mismatch or incident statuses do not clear the guard.

        Args:
            result: Completed ``ReconciliationResult`` from the startup
                reconciliation run.

        Returns:
            ``True`` when startup is now marked complete, ``False``
            when the result does not clear the guard (mismatch or
            incident present).
        """
        if result.status == "clean":
            self.startup_complete = True
            self.startup_reconciliation_id = result.reconciliation_id
            self.startup_completed_at = result.completed_at
            logger.info(
                "reconciliation.startup_guard.cleared reconciliation_id=%r",
                result.reconciliation_id,
            )
            return True

        logger.warning(
            "reconciliation.startup_guard.not_cleared "
            "reconciliation_id=%r status=%r "
            "missing=%r extra=%r mismatched=%r",
            result.reconciliation_id,
            result.status,
            result.missing_count,
            result.extra_count,
            result.mismatched_count,
        )
        return False

    @property
    def is_startup_complete(self) -> bool:
        """Return ``True`` when startup reconciliation has passed."""
        return self.startup_complete


def _extract_timestamp(record: dict[str, Any]) -> datetime | None:
    """Extract a UTC datetime from a record dict using known field names.

    Checks ``updated_at``, ``timestamp``, ``created_at``, and
    ``snapshot_at`` in order. Accepts ISO 8601 strings and
    ``datetime`` objects.

    Args:
        record: Position or order record dict.

    Returns:
        ``datetime`` with UTC timezone when a parseable timestamp is
        found, or ``None`` when none of the fields exist or parse.
    """
    for key in _TIMESTAMP_FIELDS:
        raw = record.get(key)
        if raw is None:
            continue
        if isinstance(raw, datetime):
            return raw if raw.tzinfo is not None else raw.replace(tzinfo=UTC)
        if isinstance(raw, str):
            try:
                dt = datetime.fromisoformat(raw)
                return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
            except (ValueError, TypeError):
                continue
    return None


def _check_stale(
    record: dict[str, Any],
    entity_id: str,
    entity_type: str,
    now: datetime,
    max_staleness_seconds: float,
) -> ReconciliationMismatch | None:
    """Return a stale mismatch if the record's timestamp is too old.

    Args:
        record: Position or order record dict.
        entity_id: Entity identifier string.
        entity_type: Entity type string (``'position'`` or ``'order'``).
        now: Current UTC datetime for age calculation.
        max_staleness_seconds: Maximum allowed record age in seconds.

    Returns:
        ``ReconciliationMismatch`` with type ``'stale'`` when the
        record is too old, or ``None`` when freshness is acceptable or
        no timestamp field is present.
    """
    ts = _extract_timestamp(record)
    if ts is None:
        return None
    age = (now - ts).total_seconds()
    if age > max_staleness_seconds:
        return ReconciliationMismatch(
            mismatch_type="stale",
            entity_type=entity_type,
            entity_id=entity_id,
            internal_value=None,
            broker_value=None,
            severity="warning",
            details={
                "age_seconds": round(age, 3),
                "max_staleness_seconds": max_staleness_seconds,
                "action_required": "refresh_from_broker",
            },
        )
    return None


def reconcile_state(  # noqa: PLR0912, PLR0915, C901
    *,
    internal_positions: list[dict[str, Any]] | None = None,
    internal_orders: list[dict[str, Any]] | None = None,
    broker_positions: list[dict[str, Any]] | None = None,
    broker_orders: list[dict[str, Any]] | None = None,
    max_staleness_seconds: float = 10.0,
    request_id: str | None = None,
    correlation_id: str | None = None,
    approval_id: str | None = None,
    reconciliation_id: str | None = None,
) -> ReconciliationResult:
    """Package reconciliation of internal state against broker truth.

    Compares internal position/order records with broker-sourced
    snapshots. Detects missing, extra, mismatched, and stale records.
    Returns a ``ReconciliationResult`` that classifies the outcome.

    Reconciliation prefers broker truth: when internal and broker
    records diverge, the broker value is authoritative.

    Stale detection uses the ``updated_at``, ``timestamp``,
    ``created_at``, or ``snapshot_at`` field of each record. Records
    without any of these fields are not classified as stale.

    This function does NOT mutate broker state and does NOT call broker
    adapters directly. Broker snapshots must be provided by the caller
    from an approved adapter port.

    Args:
        internal_positions: Internal runtime position records.
        internal_orders: Internal runtime order records.
        broker_positions: Broker-sourced position snapshot.
        broker_orders: Broker-sourced order snapshot.
        max_staleness_seconds: Maximum record age before stale
            classification. Must be positive.
        request_id: Trace identifier.
        correlation_id: Optional correlation identifier.
        approval_id: Optional approval ID of the requesting action.
        reconciliation_id: Optional stable reconciliation run ID.
            Auto-generated when not provided.

    Returns:
        ``ReconciliationResult`` with mismatch counts, incident list,
        status, and all trace identifiers propagated.

    Raises:
        ValidationError: If any input list argument is not a list when
            provided, or if ``max_staleness_seconds`` is not positive.
    """
    start = time.perf_counter()
    started_at = datetime.now(UTC)

    if max_staleness_seconds <= 0:
        raise ValidationError(
            "max_staleness_seconds must be positive.",
            code="INVALID_INPUT",
        )

    for name, val in [
        ("internal_positions", internal_positions),
        ("internal_orders", internal_orders),
        ("broker_positions", broker_positions),
        ("broker_orders", broker_orders),
    ]:
        if val is not None and not isinstance(val, list):
            raise ValidationError(
                f"{name} must be a list when provided.",
                code="INVALID_INPUT",
            )

    int_positions = internal_positions or []
    int_orders = internal_orders or []
    brk_positions = broker_positions or []
    brk_orders = broker_orders or []

    if reconciliation_id is None:
        digest = hashlib.sha256(
            f"{started_at.isoformat()}{request_id}".encode()
        ).hexdigest()[:12]
        reconciliation_id = f"recon_{digest}"

    logger.info(
        "live_reconciliation.started reconciliation_id=%r "
        "internal_positions=%r internal_orders=%r "
        "broker_positions=%r broker_orders=%r request_id=%r",
        reconciliation_id,
        len(int_positions),
        len(int_orders),
        len(brk_positions),
        len(brk_orders),
        request_id,
    )

    mismatches: list[ReconciliationMismatch] = []
    incidents: list[dict[str, Any]] = []
    now = datetime.now(UTC)

    matched_count = 0
    missing_count = 0
    extra_count = 0
    mismatched_count = 0
    stale_count = 0

    # ── Position reconciliation ───────────────────────────────────────
    int_pos_map = {str(p.get("position_id", i)): p for i, p in enumerate(int_positions)}
    brk_pos_map = {str(p.get("position_id", i)): p for i, p in enumerate(brk_positions)}

    for pid, brk_pos in brk_pos_map.items():
        if pid not in int_pos_map:
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type="missing_local",
                    entity_type="position",
                    entity_id=pid,
                    internal_value=None,
                    broker_value={"position_id": pid, "broker_truth": True},
                    severity="error",
                    details={"action_required": "reconcile_position"},
                )
            )
            missing_count += 1
        else:
            int_pos = int_pos_map[pid]
            mismatch_fields: list[str] = [
                key
                for key in ("volume", "symbol", "type")
                if (key in brk_pos and key in int_pos and brk_pos[key] != int_pos[key])
            ]
            if mismatch_fields:
                mismatches.append(
                    ReconciliationMismatch(
                        mismatch_type="field_mismatch",
                        entity_type="position",
                        entity_id=pid,
                        internal_value={k: int_pos.get(k) for k in mismatch_fields},
                        broker_value={k: brk_pos.get(k) for k in mismatch_fields},
                        severity="warning",
                        details={"mismatched_fields": mismatch_fields},
                    )
                )
                mismatched_count += 1
            else:
                matched_count += 1

            # Stale check on broker position record.
            stale = _check_stale(brk_pos, pid, "position", now, max_staleness_seconds)
            if stale is not None:
                mismatches.append(stale)
                stale_count += 1

    for pid, int_pos in int_pos_map.items():
        if pid not in brk_pos_map:
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type="extra_local",
                    entity_type="position",
                    entity_id=pid,
                    internal_value={"position_id": pid},
                    broker_value=None,
                    severity="warning",
                    details={"action_required": "verify_with_broker"},
                )
            )
            extra_count += 1

    # ── Order reconciliation ──────────────────────────────────────────
    int_ord_map = {str(o.get("order_id", i)): o for i, o in enumerate(int_orders)}
    brk_ord_map = {str(o.get("order_id", i)): o for i, o in enumerate(brk_orders)}

    for oid, brk_ord in brk_ord_map.items():
        if oid not in int_ord_map:
            missing_count += 1
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type="missing_local",
                    entity_type="order",
                    entity_id=oid,
                    internal_value=None,
                    broker_value={"order_id": oid, "broker_truth": True},
                    severity="error",
                    details={"action_required": "reconcile_order"},
                )
            )
        else:
            matched_count += 1
            # Stale check on broker order record.
            stale = _check_stale(brk_ord, oid, "order", now, max_staleness_seconds)
            if stale is not None:
                mismatches.append(stale)
                stale_count += 1

    for oid in int_ord_map:
        if oid not in brk_ord_map:
            extra_count += 1
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type="extra_local",
                    entity_type="order",
                    entity_id=oid,
                    internal_value={"order_id": oid},
                    broker_value=None,
                    severity="warning",
                    details={"action_required": "verify_with_broker"},
                )
            )

    # ── Determine status ──────────────────────────────────────────────
    critical_mismatches = [m for m in mismatches if m.severity == "critical"]
    error_mismatches = [m for m in mismatches if m.severity == "error"]

    if critical_mismatches:
        status = "incident"
        incidents.append(
            {
                "incident_type": "critical_reconciliation_mismatch",
                "severity": "critical",
                "mismatch_count": len(critical_mismatches),
                "action_required": "immediate_operator_review",
                "reconciliation_id": reconciliation_id,
            }
        )
    elif error_mismatches:
        status = "mismatch"
        incidents.append(
            {
                "incident_type": "reconciliation_mismatch",
                "severity": "error",
                "mismatch_count": len(error_mismatches),
                "action_required": "operator_review",
                "reconciliation_id": reconciliation_id,
            }
        )
    elif mismatches:
        status = "mismatch"
    else:
        status = "clean"

    completed_at = datetime.now(UTC)
    elapsed_ms = (time.perf_counter() - start) * 1000
    retry_safety = (
        "retry_after_reconciliation" if status != "clean" else "safe_to_retry"
    )

    logger.info(
        "live_reconciliation.completed reconciliation_id=%r "
        "status=%r matched=%r missing=%r extra=%r "
        "mismatched=%r stale=%r incidents=%r "
        "elapsed_ms=%r request_id=%r",
        reconciliation_id,
        status,
        matched_count,
        missing_count,
        extra_count,
        mismatched_count,
        stale_count,
        len(incidents),
        round(elapsed_ms, 3),
        request_id,
    )

    return ReconciliationResult(
        reconciliation_id=reconciliation_id,
        status=status,
        matched_count=matched_count,
        missing_count=missing_count,
        extra_count=extra_count,
        mismatched_count=mismatched_count,
        stale_count=stale_count,
        mismatches=mismatches,
        incidents=incidents,
        started_at=started_at,
        completed_at=completed_at,
        request_id=request_id,
        correlation_id=correlation_id,
        approval_id=approval_id,
        retry_safety=retry_safety,
        message=(
            f"Reconciliation {reconciliation_id}: status={status}, "
            f"matched={matched_count}, missing={missing_count}, "
            f"extra={extra_count}, mismatched={mismatched_count}, "
            f"stale={stale_count}."
        ),
    )

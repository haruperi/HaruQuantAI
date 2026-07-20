"""Trading idempotency keys and durable lease records.

This module computes canonical SHA-256 idempotency material hashes and provides
a local JSONL-backed store for in-progress and completed command records. Live
route records are durable across process restarts when callers reuse the same
store path.
"""
# ruff: noqa: TC001

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.trading.contracts import (
    JsonObject,
    TradingAction,
    TradingRoute,
)
from app.services.trading.state.ports import Clock
from app.utils.logger import logger
from app.utils.standard import canonical_json

IDEMPOTENCY_MATERIAL_FIELDS = (
    "account_id",
    "strategy_id",
    "route",
    "promotion_stage",
    "broker",
    "symbol",
    "action",
    "type",
    "side",
    "volume",
    "price",
    "stop_limit_price",
    "sl",
    "tp",
    "deviation",
    "tif",
    "expiration",
    "magic_number",
    "client_order_id",
    "risk_id",
    "approval_id",
    "allocation_vector",
)


class IdempotencyStatus(StrEnum):
    """Idempotency record lifecycle status."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class IdempotencyDecision(StrEnum):
    """Reservation decision returned to callers."""

    RESERVED = "reserved"
    DUPLICATE_IN_PROGRESS = "duplicate_in_progress"
    DUPLICATE_COMPLETED = "duplicate_completed"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class IdempotencyMaterial(BaseModel):
    """Canonical command material used to derive idempotency keys.

    Attributes:
        account_id: Broker account identifier.
        strategy_id: Strategy identifier.
        route: Trading route.
        promotion_stage: Promotion stage string.
        broker: Broker identifier.
        symbol: Symbol identifier.
        action: Trading action.
        type: Order type.
        side: Trade side.
        volume: Requested volume.
        price: Requested price.
        stop_limit_price: Stop-limit trigger price.
        sl: Stop loss.
        tp: Take profit.
        deviation: Max price deviation.
        tif: Time in force.
        expiration: Expiration timestamp.
        magic_number: Strategy magic number.
        client_order_id: Client order identifier.
        risk_id: Risk approval or decision identifier.
        approval_id: Human/operator approval identifier.
        allocation_vector: Allocation weights.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    account_id: str
    strategy_id: str
    route: TradingRoute
    promotion_stage: str
    broker: str
    symbol: str
    action: TradingAction
    type: str | None = None
    side: str | None = None
    volume: str | None = None
    price: str | None = None
    stop_limit_price: str | None = None
    sl: str | None = None
    tp: str | None = None
    deviation: str | None = None
    tif: str | None = None
    expiration: str | None = None
    magic_number: str | None = None
    client_order_id: str | None = None
    risk_id: str | None = None
    approval_id: str | None = None
    allocation_vector: JsonObject | None = None

    @model_validator(mode="after")
    def validate_material(self) -> Self:
        """Validate required idempotency material fields.

        Returns:
            IdempotencyMaterial: Validated material.

        Raises:
            ValueError: If required identifiers are blank.
        """
        logger.info("Validating idempotency material for {}.", self.symbol)
        for field_name in (
            "account_id",
            "strategy_id",
            "promotion_stage",
            "broker",
            "symbol",
        ):
            if not str(getattr(self, field_name)).strip():
                message = f"{field_name} must be non-empty."
                raise ValueError(message)
        return self

    def canonical_payload(self) -> JsonObject:
        """Return canonical JSON-safe idempotency material.

        Returns:
            JsonObject: Material restricted to approved hash fields.
        """
        logger.info("Building canonical idempotency payload.")
        dumped = self.model_dump(mode="json")
        return {field: dumped.get(field) for field in IDEMPOTENCY_MATERIAL_FIELDS}


class IdempotencyRecord(BaseModel):
    """Durable idempotency record.

    Attributes:
        route: Trading route.
        tenant_id: Tenant namespace.
        key: Idempotency key.
        material_hash: Canonical material hash.
        status: Record lifecycle status.
        expires_at: Lease expiration timestamp.
        created_at: Creation timestamp.
        completed_at: Completion timestamp.
        outcome: Cached completed execution envelope.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    route: TradingRoute
    tenant_id: str
    key: str
    material_hash: str
    status: IdempotencyStatus
    expires_at: str
    created_at: str
    completed_at: str | None = None
    outcome: JsonObject | None = None

    @model_validator(mode="after")
    def validate_record(self) -> Self:
        """Validate idempotency record identifiers.

        Returns:
            IdempotencyRecord: Validated record.

        Raises:
            ValueError: If identifiers are blank.
        """
        logger.info("Validating idempotency record {}.", self.key)
        if not self.tenant_id.strip():
            raise ValueError("tenant_id must be non-empty.")
        if not self.key.strip():
            raise ValueError("key must be non-empty.")
        if not self.material_hash.strip():
            raise ValueError("material_hash must be non-empty.")
        return self


class IdempotencyReservation(BaseModel):
    """Reservation outcome for a command idempotency key."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: IdempotencyDecision
    record: IdempotencyRecord
    cached_outcome: JsonObject | None = None

    @model_validator(mode="after")
    def validate_reservation(self) -> Self:
        """Validate cached outcome consistency.

        Returns:
            IdempotencyReservation: Validated reservation.
        """
        logger.info("Validating idempotency decision {}.", self.decision.value)
        return self


def compute_idempotency_key(material: IdempotencyMaterial) -> str:
    """Compute a SHA-256 idempotency key from canonical JSON material.

    Args:
        material: Idempotency material.

    Returns:
        str: SHA-256 hex digest.
    """
    logger.info("Computing idempotency key for {}.", material.symbol)
    return hashlib.sha256(
        canonical_json(material.canonical_payload()).encode("utf-8"),
    ).hexdigest()


def compute_material_hash(payload: JsonObject) -> str:
    """Compute a SHA-256 material hash from a canonical JSON payload.

    Args:
        payload: JSON-safe payload.

    Returns:
        str: SHA-256 hex digest.
    """
    logger.info("Computing idempotency material hash.")
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class JsonlIdempotencyStore:
    """JSONL-backed idempotency store with TTL lease handling.

    Args:
        path: Durable JSONL path.
        clock: Injected clock.
    """

    def __init__(self, *, path: Path, clock: Clock) -> None:
        """Initialize the idempotency store.

        Args:
            path: Durable JSONL path.
            clock: Injected clock.
        """
        logger.info("Initializing idempotency store at {}.", path)
        self._path = path
        self._clock = clock

    def reserve(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        material: IdempotencyMaterial,
        ttl: timedelta,
    ) -> IdempotencyReservation:
        """Reserve an idempotency key or return duplicate state.

        Args:
            route: Trading route.
            tenant_id: Tenant namespace.
            material: Canonical command material.
            ttl: In-progress lease TTL.

        Returns:
            IdempotencyReservation: Reservation decision.

        Raises:
            ValueError: If TTL is non-positive or tenant is blank.
        """
        logger.info("Reserving idempotency key for tenant {}.", tenant_id)
        if ttl.total_seconds() <= 0:
            raise ValueError("ttl must be positive.")
        if not tenant_id.strip():
            raise ValueError("tenant_id must be non-empty.")

        now = self._clock.now_utc()
        key = compute_idempotency_key(material)
        material_hash = compute_material_hash(material.canonical_payload())
        existing = self.resolve(route=route, tenant_id=tenant_id, key=key)
        if existing is not None:
            return self._decision_for_existing(record=existing, now=now)

        record = IdempotencyRecord(
            route=route,
            tenant_id=tenant_id,
            key=key,
            material_hash=material_hash,
            status=IdempotencyStatus.IN_PROGRESS,
            expires_at=(now + ttl).isoformat(),
            created_at=now.isoformat(),
        )
        self._upsert(record)
        return IdempotencyReservation(
            decision=IdempotencyDecision.RESERVED,
            record=record,
        )

    def resolve(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
    ) -> IdempotencyRecord | None:
        """Resolve a durable idempotency record.

        Args:
            route: Trading route.
            tenant_id: Tenant namespace.
            key: Idempotency key.

        Returns:
            IdempotencyRecord | None: Existing record when found.
        """
        logger.info("Resolving idempotency key {}.", key)
        for record in self._load_all():
            if (
                record.route is route
                and record.tenant_id == tenant_id
                and record.key == key
            ):
                return record
        return None

    def complete(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        outcome: JsonObject,
        completed_at: datetime | None = None,
    ) -> IdempotencyRecord:
        """Mark an in-progress idempotency record completed.

        Args:
            route: Trading route.
            tenant_id: Tenant namespace.
            key: Idempotency key.
            outcome: Cached execution envelope.
            completed_at: Completion timestamp from an injected Clock. Accepted
                so this store satisfies the ``IdempotencyStore`` port, which
                ``finalize_dispatch_outcome`` calls with an explicit timestamp.
                Falls back to this store's own clock when omitted.

        Returns:
            IdempotencyRecord: Completed record.

        Raises:
            KeyError: If the record does not exist.
        """
        logger.info("Completing idempotency key {}.", key)
        record = self.resolve(route=route, tenant_id=tenant_id, key=key)
        if record is None:
            raise KeyError("idempotency record not found.")
        resolved_at = completed_at or self._clock.now_utc()
        completed = record.model_copy(
            update={
                "status": IdempotencyStatus.COMPLETED,
                "completed_at": resolved_at.isoformat(),
                "outcome": outcome,
            },
        )
        self._upsert(completed)
        return completed

    def mark_expired_leases(self) -> tuple[IdempotencyRecord, ...]:
        """Transition expired in-progress leases to reconciliation-required.

        Returns:
            tuple[IdempotencyRecord, ...]: Records transitioned.
        """
        logger.info("Marking expired idempotency leases.")
        now = self._clock.now_utc()
        transitioned: list[IdempotencyRecord] = []
        retained: list[IdempotencyRecord] = []
        for record in self._load_all():
            if self._is_expired_in_progress(record=record, now=now):
                updated = record.model_copy(
                    update={"status": IdempotencyStatus.RECONCILIATION_REQUIRED},
                )
                transitioned.append(updated)
                retained.append(updated)
            else:
                retained.append(record)
        self._rewrite(retained)
        return tuple(transitioned)

    def _decision_for_existing(
        self,
        *,
        record: IdempotencyRecord,
        now: datetime,
    ) -> IdempotencyReservation:
        """Return the reservation decision for an existing record.

        Args:
            record: Existing record.
            now: Current timestamp from injected clock.

        Returns:
            IdempotencyReservation: Duplicate or recovery decision.
        """
        logger.info("Resolving duplicate idempotency status {}.", record.status.value)
        if record.status is IdempotencyStatus.COMPLETED:
            return IdempotencyReservation(
                decision=IdempotencyDecision.DUPLICATE_COMPLETED,
                record=record,
                cached_outcome=record.outcome,
            )
        if self._is_expired_in_progress(record=record, now=now):
            updated = record.model_copy(
                update={"status": IdempotencyStatus.RECONCILIATION_REQUIRED},
            )
            self._upsert(updated)
            return IdempotencyReservation(
                decision=IdempotencyDecision.RECONCILIATION_REQUIRED,
                record=updated,
            )
        if record.status is IdempotencyStatus.RECONCILIATION_REQUIRED:
            return IdempotencyReservation(
                decision=IdempotencyDecision.RECONCILIATION_REQUIRED,
                record=record,
            )
        return IdempotencyReservation(
            decision=IdempotencyDecision.DUPLICATE_IN_PROGRESS,
            record=record,
        )

    def _is_expired_in_progress(
        self,
        *,
        record: IdempotencyRecord,
        now: datetime,
    ) -> bool:
        """Return whether an in-progress record lease is expired.

        Args:
            record: Idempotency record.
            now: Current timestamp.

        Returns:
            bool: True when the record requires reconciliation.
        """
        logger.debug("Checking idempotency lease expiry for {}.", record.key)
        expires_at = datetime.fromisoformat(record.expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return record.status is IdempotencyStatus.IN_PROGRESS and expires_at <= now

    def _load_all(self) -> tuple[IdempotencyRecord, ...]:
        """Load all idempotency records from disk.

        Returns:
            tuple[IdempotencyRecord, ...]: Durable records.
        """
        logger.debug("Loading idempotency records.")
        if not self._path.exists():
            return ()
        records: list[IdempotencyRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(IdempotencyRecord.model_validate_json(line))
        return tuple(records)

    def _upsert(self, record: IdempotencyRecord) -> None:
        """Insert or replace a record.

        Args:
            record: Record to persist.
        """
        logger.debug("Upserting idempotency record {}.", record.key)
        retained = [
            item
            for item in self._load_all()
            if not (
                item.route is record.route
                and item.tenant_id == record.tenant_id
                and item.key == record.key
            )
        ]
        retained.append(record)
        self._rewrite(retained)

    def _rewrite(self, records: list[IdempotencyRecord]) -> None:
        """Rewrite the durable idempotency file atomically.

        Args:
            records: Records to persist.
        """
        logger.debug("Rewriting {} idempotency records.", len(records))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                )
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(self._path)

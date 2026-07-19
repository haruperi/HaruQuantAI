"""Caller-key reservation against canonical Trading request material."""

from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.trading.contracts import TradingError, TradingRequest
from app.services.trading.state.stores import TradingStateStore
from app.utils import canonical_json, logger

type ReservationStatus = Literal[
    "new",
    "duplicate_completed",
    "duplicate_active",
    "conflict",
    "reconciliation_required",
]
_SHA256_HEX_LENGTH = 64


class IdempotencyReservation(BaseModel):
    """Immutable atomic idempotency reservation result.

    Attributes:
        status: Finite atomic reservation decision.
        material_hash: Canonical SHA-256 request digest.
        receipt_id: Existing completed receipt when one is known.
        reserved_at: Injected UTC reservation creation time.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    material_hash: str
    material_version: str
    status: ReservationStatus
    reserved_at: datetime
    expires_at: datetime
    receipt_id: str | None = None

    @field_validator("key", "material_version")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required reservation text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating IdempotencyReservation text")
        if not value or value != value.strip():
            raise ValueError("reservation text must be non-empty and trimmed")
        return value

    @field_validator("material_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate canonical SHA-256 material digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated lowercase digest.

        Raises:
            ValueError: If digest shape is invalid.
        """
        logger.debug("Validating IdempotencyReservation material hash")
        if len(value) != _SHA256_HEX_LENGTH or any(
            item not in "0123456789abcdef" for item in value
        ):
            raise ValueError("material_hash must be lowercase SHA-256 hex")
        return value

    @field_validator("reserved_at", "expires_at")
    @classmethod
    def _validate_expiry(cls, value: datetime) -> datetime:
        """Validate reservation UTC expiry.

        Args:
            value: Candidate expiry.

        Returns:
            Validated UTC timestamp.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating IdempotencyReservation UTC time")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("reservation expiry must be timezone-aware UTC")
        return value

    @model_validator(mode="after")
    def _validate_state(self) -> Self:
        """Validate finite state-specific evidence.

        Returns:
            Validated reservation.

        Raises:
            ValueError: If completed state lacks receipt evidence.
        """
        logger.debug("Validating IdempotencyReservation state evidence")
        if self.status == "duplicate_completed" and self.receipt_id is None:
            raise ValueError("duplicate_completed requires receipt_id")
        if self.expires_at <= self.reserved_at:
            raise ValueError("reservation expiry must follow creation time")
        return self


def reserve_idempotency(
    request: TradingRequest,
    store: TradingStateStore,
    *,
    reservation_time: datetime,
    retention_seconds: int,
    concurrency_lock_timeout_seconds: Decimal,
) -> IdempotencyReservation:
    """Reserve caller key against versioned canonical request material.

    Args:
        request: Validated governed Trading request.
        store: Injected atomic Trading state store.
        reservation_time: Injected aware UTC reservation time.
        retention_seconds: Exact positive reservation lifetime.
        concurrency_lock_timeout_seconds: Exact positive active-lock age bound.

    Returns:
        New or same-material duplicate reservation.

    Raises:
        TradingError: If policy is invalid, material conflicts, an active lock is
            stale, or persistence fails.
    """
    logger.info("Reserving Trading request idempotency material")
    if (
        reservation_time.tzinfo is None
        or reservation_time.utcoffset() != timedelta(0)
        or isinstance(retention_seconds, bool)
        or not isinstance(retention_seconds, int)
        or retention_seconds <= 0
        or not isinstance(concurrency_lock_timeout_seconds, Decimal)
        or not concurrency_lock_timeout_seconds.is_finite()
        or concurrency_lock_timeout_seconds <= 0
    ):
        raise TradingError(
            "CONFIGURATION_INVALID", "Idempotency runtime policy is invalid"
        )
    material = request.model_dump(mode="python")
    digest = sha256(canonical_json(material).encode("utf-8")).hexdigest()
    expires_at = reservation_time + timedelta(seconds=retention_seconds)
    try:
        reservation = store.reserve_idempotency(
            request.idempotency_key,
            digest,
            request.canonical_material_version,
            reservation_time,
            expires_at,
        )
    except TradingError:
        logger.warning("Trading store rejected idempotency reservation")
        raise
    except Exception as error:
        logger.error("Trading idempotency persistence failed")
        raise TradingError(
            "PERSISTENCE_FAILED",
            "Idempotency reservation persistence failed",
            trace_context={"request_id": request.request_id},
        ) from error
    if reservation.material_hash != digest or reservation.status == "conflict":
        raise TradingError(
            "IDEMPOTENCY_CONFLICT",
            "Caller key was reused for different canonical material",
            trace_context={"request_id": request.request_id},
        )
    if reservation.material_version != request.canonical_material_version:
        raise TradingError(
            "VERSION_CONFLICT",
            "Idempotency material version does not match",
            trace_context={"request_id": request.request_id},
        )
    if (
        reservation.status == "duplicate_active"
        and Decimal(str((reservation_time - reservation.reserved_at).total_seconds()))
        > concurrency_lock_timeout_seconds
    ):
        raise TradingError(
            "TRADING_CONCURRENCY_CONFLICT",
            "Active idempotency reservation exceeded its lock bound",
            trace_context={"request_id": request.request_id},
        )
    return reservation


__all__ = ["IdempotencyReservation", "reserve_idempotency"]

"""Durable Risk concurrent-capacity reservation over relational records."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.services.risk.persistence import (
    create_capacity_reservation,
    read_active_capacity_reservations,
)

logger = get_logger(__name__)


class _DurableCapacityGuard:
    """Data-backed implementation of Risk's atomic capacity-reservation port."""

    def reserve_capacity(
        self,
        *,
        reservation_key: str,
        account_id: str,
        strategy_id: str,
        symbol: str,
        requested_notional: Decimal,
        expires_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> Literal["reserved", "already_reserved", "conflict", "unavailable"]:
        """Atomically reserve capacity for one exact proposed action.

        Two individually valid trades might become unsafe if approved
        simultaneously; only one active reservation may exist per exact
        (account, strategy, symbol) scope at a time. A retried call with the
        identical reservation key is treated as the same reservation, not a
        new one.

        Returns:
            Atomic receiver-owned capacity outcome.
        """
        del timeout_seconds
        now = datetime.now(UTC).isoformat()
        active = read_active_capacity_reservations(
            account_id, strategy_id, symbol, now=now
        )
        if any(row["reservation_key"] == reservation_key for row in active):
            logger.debug("Replaying an already-active Risk capacity reservation")
            return "already_reserved"
        if active:
            logger.info(
                "Risk capacity reservation conflict for account=%s strategy=%s "
                "symbol=%s",
                account_id,
                strategy_id,
                symbol,
            )
            return "conflict"
        try:
            create_capacity_reservation(
                reservation_key=reservation_key,
                account_id=account_id,
                strategy_id=strategy_id,
                symbol=symbol,
                requested_notional=str(requested_notional),
                expires_at=expires_at.isoformat(),
                request_id=generate_id("req"),
                correlation_id=generate_id("cor"),
                created_at=now,
            )
        except ValueError:
            logger.info("Risk capacity reservation raced to conflict on insert")
            return "conflict"
        return "reserved"


def build_risk_capacity_guard() -> object:
    """Build the durable Risk concurrent-capacity reservation adapter.

    Returns:
        Opaque capacity-guard handle satisfying Risk's ``_CapacityGuard`` port.
    """
    logger.info("Building durable Risk capacity-reservation guard")
    return _DurableCapacityGuard()


__all__ = ("build_risk_capacity_guard",)

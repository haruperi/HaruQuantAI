"""Minimal injected persistence port for Trading-owned state."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from app.services.trading.contracts.models import JsonValue, TradingRoute
from app.utils import logger

if TYPE_CHECKING:
    from app.services.trading.state.events import TradingEvent
    from app.services.trading.state.idempotency import IdempotencyReservation
    from app.services.trading.state.projections import TradingProjection

type TradingScope = tuple[TradingRoute, str, str]


class TradingStateStore(Protocol):  # pragma: no cover - structural port declarations.
    """Persistence operations required by Trading orchestration."""

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> IdempotencyReservation:
        """Atomically reserve or compare one caller key.

        Args:
            key: Caller-supplied idempotency key.
            material_hash: Canonical request material digest.
            material_version: Canonical material version.
            reserved_at: Injected UTC reservation creation time.
            expires_at: UTC reservation expiry.

        """
        del key, material_hash, material_version, reserved_at, expires_at
        logger.debug("Calling Trading store idempotency reservation port")
        raise NotImplementedError

    def append_event(self, event: TradingEvent) -> None:
        """Append one immutable versioned event.

        Args:
            event: Event to append without rewriting history.
        """
        del event
        logger.debug("Calling Trading store append-event port")
        raise NotImplementedError

    def load_projection(self, scope: TradingScope) -> TradingProjection | None:
        """Load the latest projection for one exact scope.

        Args:
            scope: Route, tenant, and authority identity.

        """
        del scope
        logger.debug("Calling Trading store projection-read port")
        raise NotImplementedError

    def save_projection(
        self,
        projection: TradingProjection,
        expected_version: int,
    ) -> None:
        """Save a projection using optimistic version matching.

        Args:
            projection: New immutable projection.
            expected_version: Version that must currently be stored.
        """
        del projection, expected_version
        logger.debug("Calling Trading store projection-write port")
        raise NotImplementedError

    def load_unresolved_attempts(
        self,
        scope: TradingScope,
    ) -> tuple[TradingEvent, ...]:
        """Load every unresolved attempt for one exact scope.

        Args:
            scope: Route, tenant, and authority conflict scope.

        """
        del scope
        logger.debug("Calling Trading store unresolved-attempt port")
        raise NotImplementedError

    def load_report_evidence(
        self,
        scope: TradingScope,
    ) -> Mapping[str, JsonValue]:
        """Load official reporting evidence for one exact scope.

        Args:
            scope: Route, tenant, and authority identity.

        """
        del scope
        logger.debug("Calling Trading store report-evidence port")
        raise NotImplementedError


__all__ = ["TradingStateStore"]

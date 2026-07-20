"""Track execution latency statistics and implement the lost-order recovery watchdog.

This module implements:
- Bounded latency history tracking (TRD-FR-171)
- Lost-order recovery watchdog with staleness transitions (TRD-FR-172)
"""

from collections import deque
from datetime import datetime
from typing import Any, Protocol

from app.services.trading.contracts import TradingRoute
from app.services.trading.state.ports import Clock
from loguru import logger


class ReconciliationService(Protocol):  # pragma: no cover
    """Protocol for reconciliation service to avoid circular dependencies."""

    def run_reconciliation(
        self,
        route: TradingRoute,
        tenant_id: str,
        account_id: str,
        run_type: str,
    ) -> object:
        """Run state synchronization and mismatch checks."""
        ...


class LatencyTracker:
    """Tracks broker execution latency using bounded rolling samples."""

    def __init__(self, max_samples: int = 100) -> None:
        """Initialize the tracker with a maximum number of samples.

        Args:
            max_samples: Bounded sample limit to prevent unbounded memory growth.
        """
        self._samples: deque[float] = deque(maxlen=max_samples)

    def record_latency(self, latency_ms: float) -> None:
        """Record a single latency observation in milliseconds.

        Args:
            latency_ms: Latency observation.
        """
        if latency_ms >= 0:
            self._samples.append(latency_ms)

    def get_p95_latency(self) -> float:
        """Calculate the 95th percentile execution latency.

        Returns:
            float: p95 latency in ms, or 0.0 if empty.
        """
        if not self._samples:
            return 0.0
        sorted_samples = sorted(self._samples)
        idx = int(len(sorted_samples) * 0.95)
        return float(sorted_samples[min(idx, len(sorted_samples) - 1)])

    @property
    def samples(self) -> list[float]:
        """Return the current sample list.

        Returns:
            list[float]: Latency samples.
        """
        return list(self._samples)


class LostOrderWatchdog:
    """Watchdog checking for stale pending or working orders."""

    def __init__(self, life_to_live_seconds: float, clock: Clock) -> None:
        """Initialize the lost-order recovery watchdog.

        Args:
            life_to_live_seconds: Life-to-live window in seconds.
            clock: Injected clock source.
        """
        self._life_to_live_seconds = life_to_live_seconds
        self._clock = clock

    def check_stale_orders(
        self,
        active_orders: list[dict[str, Any]],
        reconciliation_service: ReconciliationService,
        route: TradingRoute,
        tenant_id: str,
        account_id: str,
    ) -> list[str]:
        """Verify active orders and flag those exceeding life-to-live as stale.

        Triggers a state reconciliation under the STALE_ORDER run_type
        incident classification if any stale orders are found.

        Args:
            active_orders: Active orders representation list.
            reconciliation_service: ReconciliationService reference to trigger sync.
            route: Route context (e.g. live, paper).
            tenant_id: Tenant ID.
            account_id: Account ID.

        Returns:
            list[str]: Ticket IDs of flagged stale orders.
        """
        stale_tickets: list[str] = []
        now = self._clock.now_utc()

        for order in active_orders:
            # We target orders in non-terminal states
            state = str(order.get("state") or "").upper()
            if state in ("FILLED", "CANCELLED", "REJECTED", "EXPIRED", "STALE"):
                continue

            created_at_val = order.get("created_at") or order.get("timestamp")
            if not created_at_val:
                continue

            created_at: datetime
            if isinstance(created_at_val, datetime):
                created_at = created_at_val
            else:
                try:
                    created_at = datetime.fromisoformat(str(created_at_val))
                except ValueError:
                    logger.warning("Invalid timestamp in order: {}", created_at_val)
                    continue

            elapsed_seconds = (now - created_at).total_seconds()
            if elapsed_seconds > self._life_to_live_seconds:
                ticket = str(order.get("ticket") or order.get("order_id") or "")
                if ticket:
                    stale_tickets.append(ticket)
                    # Transition order state in-place to stale
                    order["state"] = "STALE"

        if stale_tickets:
            logger.warning(
                "Stale orders detected beyond TTL: {}. Forcing reconciliation.",
                stale_tickets,
            )
            try:
                # Force reconciliation with special incident type classification
                reconciliation_service.run_reconciliation(
                    route=route,
                    tenant_id=tenant_id,
                    account_id=account_id,
                    run_type="stale_order",
                )
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to run stale order reconciliation: {}", e)

        return stale_tickets

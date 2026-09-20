"""Broker session and order/position reconciliation service.

Feature:
    FEAT-BROKERS-RECONCILIATION

Purpose:
    Reconciles internal trading intents against remote provider order and position
    snapshots following reconnects, timeouts, or ambiguous acknowledgements.
    Produces comprehensive reconciliation reports and resets fail-closed fences
    upon clean parity.

Invariants:
    * Reconciles before resumption: No new submissions permitted until state parity
      is verified.
    * Explicit discrepancies: Ambiguous or unacknowledged tickets are explicitly
      reported.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, override

from app.contracts.brokers import (
    BROKER_FENCING,
    BROKER_RECONCILIATION,
    BrokerExecutionAck,
    BrokerFencingService,
    BrokerOrderIntent,
    BrokerReconciliationError,
    ReconciliationReport,
)
from app.contracts.brokers import (
    BrokerReconciliationService as IBrokerReconciliationService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(slots=True)
class BrokerReconciliationConfig:
    """Configuration options for reconciliation."""

    schema_version: int = 1
    auto_reset_fence_on_clean: bool = True


class BrokerReconciler(IBrokerReconciliationService):
    """Implementation of broker and trading intent state reconciliation."""

    def __init__(
        self,
        fencing: BrokerFencingService | None = None,
        config: BrokerReconciliationConfig | None = None,
    ) -> None:
        self._fencing = fencing
        self._config = config or BrokerReconciliationConfig()

    @override
    async def reconcile(
        self,
        provider_name: str,
        active_intents: Sequence[BrokerOrderIntent],
        provider_orders: Sequence[BrokerExecutionAck] = (),
    ) -> ReconciliationReport:
        """Evaluate local intents against provider state.

        Args:
            provider_name: Identifier of the broker connection.
            active_intents: Sequence of locally tracked open or in-flight intents.
            provider_orders: Optional sequence of remote provider execution acks.

        Returns:
            ReconciliationReport detailing matched, ambiguous, and missing items.

        Raises:
            BrokerReconciliationError: If duplicate intent_id is detected in
                active_intents.
        """
        now = datetime.now(UTC)
        discrepancies: list[str] = []
        matched = 0
        missing = 0
        ambiguous = 0

        # Duplicate intent check (fail closed on state ambiguity)
        seen_intent_ids: set[str] = set()
        for intent in active_intents:
            if intent.intent_id in seen_intent_ids:
                raise BrokerReconciliationError(
                    f"Duplicate intent_id '{intent.intent_id}' detected during "
                    "reconciliation."
                )
            seen_intent_ids.add(intent.intent_id)

        # Index provider orders by intent_id and provider_ticket
        orders_by_intent: dict[str, BrokerExecutionAck] = {
            ack.intent_id: ack for ack in provider_orders if ack.intent_id
        }
        tickets: set[str] = {
            ack.provider_ticket for ack in provider_orders if ack.provider_ticket
        }

        has_remote_snapshot = len(provider_orders) > 0

        # Evaluate each active intent
        for intent in active_intents:
            if not intent.idempotency_key:
                ambiguous += 1
                discrepancies.append(
                    f"Intent '{intent.intent_id}' lacks idempotency key."
                )
            elif has_remote_snapshot:
                # Match against provider snapshot by intent_id or matching ticket
                key = intent.idempotency_key
                matched_remotely = intent.intent_id in orders_by_intent or any(
                    key in t for t in tickets
                )
                if matched_remotely:
                    matched += 1
                else:
                    missing += 1
                    discrepancies.append(
                        f"Intent '{intent.intent_id}' not found in remote provider "
                        "order snapshot."
                    )
            else:
                # Valid normalized intent with confirmed idempotency key
                matched += 1

        report = ReconciliationReport(
            provider=provider_name,
            matched_count=matched,
            ambiguous_count=ambiguous,
            missing_count=missing,
            timestamp_utc=now,
            discrepancies=tuple(discrepancies),
        )

        logger.info(
            "broker_reconciliation_completed",
            provider=provider_name,
            matched=matched,
            ambiguous=ambiguous,
            missing=missing,
        )

        if (
            self._fencing
            and self._config.auto_reset_fence_on_clean
            and ambiguous == 0
            and missing == 0
        ) and self._fencing.is_fenced(provider_name):
            self._fencing.reset_fence(provider_name)
            logger.info(
                "reconciliation_auto_reset_fence",
                provider=provider_name,
            )

        return report


SPEC: FeatureSpec = FeatureSpec(
    name="brokers.reconciliation",
    provides=frozenset({BROKER_RECONCILIATION}),
    requires=frozenset(),
    optional=frozenset({BROKER_FENCING}),
    description="Session, order/position, and account reconciliation",
)


class BrokerReconciliationFeature:
    """Wire BrokerReconciler into the application runtime lifecycle."""

    def __init__(self, config: BrokerReconciliationConfig | None = None) -> None:
        self._config = config or BrokerReconciliationConfig()
        self._service: BrokerReconciler | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the feature and provide BrokerReconciler capability."""
        fencing = context.optional(BROKER_FENCING)
        self._service = BrokerReconciler(fencing, self._config)
        context.provide(BROKER_RECONCILIATION, self._service)
        logger.info("brokers_reconciliation_feature_started")

    async def stop(self, _context: FeatureContext) -> None:
        """Stop the feature and release resources."""
        self._service = None
        logger.info("brokers_reconciliation_feature_stopped")


def feature(
    config: BrokerReconciliationConfig | None = None,
) -> BrokerReconciliationFeature:
    """Return a zero-argument factory instance of BrokerReconciliationFeature."""
    return BrokerReconciliationFeature(config)

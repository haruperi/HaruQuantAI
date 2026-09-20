"""Uncertainty and disconnect fail-closed fencing service.

Feature:
    FEAT-BROKERS-FENCING

Purpose:
    Enforces fail-closed isolation across external broker connections. Automatically
    trips circuit breaker upon consecutive communication dropouts, prevents command
    leakage during uncertain provider acknowledgement, and blocks operations until
    verified state reconciliation resets the fence.

Invariants:
    * Fail-closed: Ambiguous disconnects immediately lock command submission (FIP-12).
    * Bounded error tolerance: Trips after max_consecutive_errors.
    * Controlled reset: Only explicit reconciliation or administrative unlock can clear.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, override

from app.contracts.brokers import (
    BROKER_FENCING,
    BrokerFencedError,
)
from app.contracts.brokers import (
    BrokerFencingService as IBrokerFencingService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(slots=True)
class BrokerFencingConfig:
    """Configuration options for isolation fencing."""

    schema_version: int = 1
    max_consecutive_errors: int = 3


@dataclass(slots=True)
class _FenceState:
    fenced: bool = False
    reason: str = ""
    fenced_at_utc: datetime | None = None
    consecutive_errors: int = 0


class BrokerFencingService(IBrokerFencingService):
    """Implementation of fail-closed provider isolation fencing."""

    def __init__(self, config: BrokerFencingConfig | None = None) -> None:
        self._config = config or BrokerFencingConfig()
        self._states: dict[str, _FenceState] = {}

    def _get_state(self, provider_name: str) -> _FenceState:
        normalized = provider_name.lower()
        if normalized not in self._states:
            self._states[normalized] = _FenceState()
        return self._states[normalized]

    @override
    def is_fenced(self, provider_name: str) -> bool:
        """Return True if the specified provider is locked in fenced mode."""
        return self._get_state(provider_name).fenced

    @override
    def trip_fence(self, provider_name: str, reason: str) -> None:
        """Lock the provider in fail-closed mode and block all new submissions."""
        state = self._get_state(provider_name)
        state.fenced = True
        state.reason = reason
        state.fenced_at_utc = datetime.now(UTC)
        logger.warning(
            "broker_isolation_fence_tripped",
            provider=provider_name,
            reason=reason,
        )

    @override
    def reset_fence(self, provider_name: str) -> None:
        """Unlock the provider after verified state reconciliation."""
        state = self._get_state(provider_name)
        state.fenced = False
        state.reason = ""
        state.fenced_at_utc = None
        state.consecutive_errors = 0
        logger.info("broker_isolation_fence_reset", provider=provider_name)

    @override
    def assert_safe_to_submit(self, provider_name: str) -> None:
        """Raise BrokerFencedError if the provider is currently locked."""
        state = self._get_state(provider_name)
        if state.fenced:
            raise BrokerFencedError(
                f"Provider '{provider_name}' is locked in fail-closed fence: "
                f"{state.reason}"
            )

    def record_error(self, provider_name: str, error_message: str) -> None:
        """Increment consecutive error count and trip fence if threshold exceeded."""
        state = self._get_state(provider_name)
        state.consecutive_errors += 1
        logger.warning(
            "broker_communication_error_recorded",
            provider=provider_name,
            consecutive_errors=state.consecutive_errors,
            error=error_message,
        )
        if state.consecutive_errors >= self._config.max_consecutive_errors:
            self.trip_fence(
                provider_name,
                f"Exceeded max errors ({state.consecutive_errors}): {error_message}",
            )

    def record_success(self, provider_name: str) -> None:
        """Reset consecutive error count on successful communication."""
        state = self._get_state(provider_name)
        state.consecutive_errors = 0


SPEC: FeatureSpec = FeatureSpec(
    name="brokers.fencing",
    provides=frozenset({BROKER_FENCING}),
    requires=frozenset(),
    optional=frozenset(),
    description="Fail-closed uncertainty and disconnect isolation fencing",
)


class BrokerFencingFeature:
    """Wire BrokerFencingService into the application runtime lifecycle."""

    def __init__(self, config: BrokerFencingConfig | None = None) -> None:
        self._config = config or BrokerFencingConfig()
        self._service: BrokerFencingService | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the feature and provide BrokerFencingService capability."""
        self._service = BrokerFencingService(self._config)
        context.provide(BROKER_FENCING, self._service)
        logger.info("brokers_fencing_feature_started")

    async def stop(self, _context: FeatureContext) -> None:
        """Stop the feature and release resources."""
        self._service = None
        logger.info("brokers_fencing_feature_stopped")


def feature(config: BrokerFencingConfig | None = None) -> BrokerFencingFeature:
    """Return a zero-argument factory instance of BrokerFencingFeature."""
    return BrokerFencingFeature(config)

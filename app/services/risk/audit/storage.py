"""Private persistence ports for Risk-owned durable state semantics."""

# Private protocols are intentionally implemented by receiver-owned adapters.
# ruff: noqa: PYI046

from abc import abstractmethod
from decimal import Decimal
from typing import Literal, Protocol

from app.composition.logging import get_logger
from app.services.risk.contracts import (
    AllocationRiskDecision,  # noqa: TC001
    KillSwitchState,  # noqa: TC001
    RiskAuditRecord,  # noqa: TC001
    StrategyOperationalEligibilityDecision,  # noqa: TC001
)

logger = get_logger(__name__)


class _RiskAuditStore(Protocol):  # pragma: no cover
    """Atomic durable store for sealed Risk audit records."""

    @abstractmethod
    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        """Return the latest sealed record.

        Args:
            timeout_seconds: Bounded store timeout.

        Returns:
            Current chain head or None.
        """
        logger.debug("Reading current Risk audit-chain head")
        raise NotImplementedError

    @abstractmethod
    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        """Atomically append a sealed record with idempotency checks.

        Args:
            record: Sealed record to append.
            expected_sequence: Required next sequence.
            expected_previous_hash: Required current head hash.
            timeout_seconds: Bounded store timeout.

        Returns:
            Atomic append outcome.
        """
        logger.debug("Atomically appending sealed Risk audit record")
        raise NotImplementedError

    @abstractmethod
    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        """Return all sealed records in ascending sequence order.

        Args:
            timeout_seconds: Bounded store timeout.

        Returns:
            Ordered sealed records.
        """
        logger.debug("Reading complete Risk audit chain")
        raise NotImplementedError


class _EligibilityDecisionStore(Protocol):  # pragma: no cover
    """Atomic store for strategy operational-eligibility decisions."""

    @abstractmethod
    def save_if_absent(
        self,
        decision: StrategyOperationalEligibilityDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Persist an exact decision if its identity is absent.

        Args:
            decision: Decision to persist.
            timeout_seconds: Bounded store timeout.

        Returns:
            Whether the exact idempotent save succeeded.
        """
        logger.debug("Persisting strategy eligibility decision if absent")
        raise NotImplementedError


class _AllocationDecisionStore(Protocol):  # pragma: no cover
    """Atomic store for allocation review and active Risk budget state."""

    @abstractmethod
    def save_review_if_absent(
        self,
        decision: AllocationRiskDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Persist one exact allocation review if absent.

        Args:
            decision: Allocation review decision.
            timeout_seconds: Bounded store timeout.

        Returns:
            Whether the exact idempotent save succeeded.
        """
        logger.debug("Persisting allocation review decision if absent")
        raise NotImplementedError

    @abstractmethod
    def get_active(
        self, portfolio_id: str, *, timeout_seconds: Decimal | None
    ) -> AllocationRiskDecision | None:
        """Return the active Risk budget for a portfolio.

        Args:
            portfolio_id: Portfolio identity.
            timeout_seconds: Bounded store timeout.

        Returns:
            Active allocation Risk decision or None.
        """
        logger.debug("Reading active allocation Risk budget")
        raise NotImplementedError

    @abstractmethod
    def activate_compare_and_swap(
        self,
        decision: AllocationRiskDecision,
        *,
        expected_predecessor_version: str | None,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Atomically activate an exact reviewed allocation version.

        Args:
            decision: Approved allocation decision to activate.
            expected_predecessor_version: Required active predecessor.
            timeout_seconds: Bounded store timeout.

        Returns:
            Whether compare-and-swap succeeded.
        """
        logger.debug("Activating allocation Risk budget by compare-and-swap")
        raise NotImplementedError


class _KillSwitchStateStore(_RiskAuditStore, Protocol):  # pragma: no cover
    """Atomic store for canonical scoped kill-switch state and its audit."""

    @abstractmethod
    def compare_and_swap_with_audit(
        self,
        state: KillSwitchState,
        record: RiskAuditRecord,
        *,
        expected_version: int,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["committed", "already_committed", "conflict"]:
        """Atomically persist a canonical state and its sealed audit record.

        Args:
            state: New canonical state.
            record: Sealed audit record for the exact state transition.
            expected_version: Required current version.
            expected_sequence: Required next audit sequence.
            expected_previous_hash: Required current audit head hash.
            timeout_seconds: Bounded store timeout.

        Returns:
            Exact atomic transition outcome.
        """
        logger.debug("Persisting atomic kill-switch state and audit transition")
        raise NotImplementedError


__all__: list[str] = []

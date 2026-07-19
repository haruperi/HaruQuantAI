"""Injected-store repository for immutable Portfolio state."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.services.portfolio.exceptions import PortfolioError
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.portfolio.contracts import (
        ActivePortfolioAllocation,
        PortfolioConstructionResult,
        PortfolioRebalancePlan,
    )

type AuditOutboxRecord = Mapping[str, str]


@runtime_checkable
class PortfolioStateStore(Protocol):
    """Atomic persistence operations required by Portfolio."""

    def save_construction(
        self,
        result: PortfolioConstructionResult,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioConstructionResult:
        """Atomically save a construction result and audit outbox record.

        Args:
            result: Immutable construction result.
            audit_record: Redacted audit outbox record.

        """
        del result, audit_record
        logger.debug("Calling Portfolio construction persistence port")
        raise NotImplementedError

    def activate_allocation(
        self,
        allocation: ActivePortfolioAllocation,
        expected_predecessor: str | None,
        expected_revision: int,
        material_hash: str,
        audit_record: AuditOutboxRecord,
    ) -> ActivePortfolioAllocation:
        """Atomically compare-and-swap one active allocation and audit record.

        Args:
            allocation: New immutable allocation version.
            expected_predecessor: Caller-observed predecessor version.
            expected_revision: Caller-observed active-scope revision.
            material_hash: Canonical idempotency material digest.
            audit_record: Redacted audit outbox record.

        """
        del (
            allocation,
            expected_predecessor,
            expected_revision,
            material_hash,
            audit_record,
        )
        logger.debug("Calling Portfolio atomic activation persistence port")
        raise NotImplementedError

    def save_plan(
        self,
        plan: PortfolioRebalancePlan,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioRebalancePlan:
        """Atomically save an immutable plan version and audit record.

        Args:
            plan: Immutable rebalance plan.
            audit_record: Redacted audit outbox record.

        """
        del plan, audit_record
        logger.debug("Calling Portfolio plan persistence port")
        raise NotImplementedError

    def load_active(
        self,
        portfolio_id: str,
        scope_key: str,
    ) -> tuple[ActivePortfolioAllocation, int] | None:
        """Load the active allocation and revision for an exact scope.

        Args:
            portfolio_id: Portfolio identity.
            scope_key: Canonical governed scope.

        """
        del portfolio_id, scope_key
        logger.debug("Calling Portfolio active allocation read port")
        raise NotImplementedError

    def load_allocation(
        self,
        portfolio_id: str,
        allocation_version: str,
    ) -> ActivePortfolioAllocation | None:
        """Load one immutable allocation version.

        Args:
            portfolio_id: Portfolio identity.
            allocation_version: Exact allocation version.

        """
        del portfolio_id, allocation_version
        logger.debug("Calling Portfolio allocation-version read port")
        raise NotImplementedError

    def load_history(self, portfolio_id: str) -> tuple[ActivePortfolioAllocation, ...]:
        """Load all immutable allocation versions in activation order.

        Args:
            portfolio_id: Portfolio identity.

        """
        del portfolio_id
        logger.debug("Calling Portfolio allocation history read port")
        raise NotImplementedError

    def load_plan(
        self,
        plan_id: str,
        plan_version: str | None,
    ) -> PortfolioRebalancePlan | None:
        """Load one exact or latest immutable rebalance plan.

        Args:
            plan_id: Plan identity.
            plan_version: Exact version or ``None`` for latest.

        """
        del plan_id, plan_version
        logger.debug("Calling Portfolio rebalance plan read port")
        raise NotImplementedError


def scope_key(scope: Mapping[str, str]) -> str:
    """Return canonical text for one exact governed scope.

    Args:
        scope: Governed scope mapping.

    Returns:
        Canonical scope JSON.

    Raises:
        PortfolioError: If the scope is empty.
    """
    logger.debug("Canonicalizing Portfolio scope key")
    if not scope:
        raise PortfolioError("PORT_INVALID_INPUT", "SCOPE")
    return canonical_json(dict(scope))


class PortfolioRepository:
    """Portfolio-owned repository over a caller-injected atomic store."""

    def __init__(self, store: PortfolioStateStore) -> None:
        """Initialize the repository with its only persistence dependency.

        Args:
            store: Data-adapted Portfolio atomic state store.

        Raises:
            PortfolioError: If the injected object does not satisfy the port.
        """
        logger.info("Initializing injected Portfolio repository")
        if not isinstance(store, PortfolioStateStore):
            raise PortfolioError("PORT_UNSAFE_OBJECT", "STATE_STORE")
        self._store = store

    def save_construction(
        self,
        result: PortfolioConstructionResult,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioConstructionResult:
        """Atomically persist complete construction lineage and audit evidence.

        Args:
            result: Complete construction result.
            audit_record: Redacted audit outbox record.

        Returns:
            Persisted result.

        Raises:
            PortfolioError: If persistence fails or conflicts.
        """
        logger.info("Persisting Portfolio construction result")
        try:
            return self._store.save_construction(result, audit_record)
        except PortfolioError:
            raise
        except Exception as error:
            raise PortfolioError("PORT_PERSISTENCE_FAILED", "CONSTRUCTION") from error

    def activate(
        self,
        allocation: ActivePortfolioAllocation,
        *,
        expected_predecessor: str | None,
        expected_revision: int,
        audit_record: AuditOutboxRecord,
    ) -> ActivePortfolioAllocation:
        """Atomically activate one immutable allocation using optimistic CAS.

        Args:
            allocation: Complete immutable allocation version.
            expected_predecessor: Caller-observed predecessor version.
            expected_revision: Caller-observed active-scope revision.
            audit_record: Redacted audit outbox record.

        Returns:
            Stored or identical idempotent allocation.

        Raises:
            PortfolioError: If CAS, idempotency, or persistence fails.
        """
        logger.info("Atomically activating Portfolio allocation version")
        if expected_revision < 0:
            raise PortfolioError("PORT_INVALID_INPUT", "EXPECTED_REVISION")
        material_hash = allocation.canonical_hash
        try:
            return self._store.activate_allocation(
                allocation,
                expected_predecessor,
                expected_revision,
                material_hash,
                audit_record,
            )
        except PortfolioError:
            raise
        except Exception as error:
            raise PortfolioError("PORT_PERSISTENCE_FAILED", "ACTIVATION") from error

    def save_plan(
        self,
        plan: PortfolioRebalancePlan,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioRebalancePlan:
        """Atomically persist an immutable plan and audit evidence.

        Args:
            plan: Complete immutable rebalance plan.
            audit_record: Redacted audit outbox record.

        Returns:
            Persisted plan.

        Raises:
            PortfolioError: If persistence fails or conflicts.
        """
        logger.info("Persisting Portfolio rebalance plan")
        try:
            return self._store.save_plan(plan, audit_record)
        except PortfolioError:
            raise
        except Exception as error:
            raise PortfolioError("PORT_PERSISTENCE_FAILED", "PLAN") from error

    def active(
        self,
        portfolio_id: str,
        scope: Mapping[str, str],
    ) -> tuple[ActivePortfolioAllocation, int] | None:
        """Return the active allocation and revision for an exact scope.

        Args:
            portfolio_id: Portfolio identity.
            scope: Exact governed scope.

        Returns:
            Active allocation and revision, or ``None``.
        """
        logger.debug("Loading active Portfolio allocation")
        return self._store.load_active(portfolio_id, scope_key(scope))

    def allocation(
        self,
        portfolio_id: str,
        allocation_version: str,
    ) -> ActivePortfolioAllocation:
        """Return one immutable allocation version or fail closed.

        Args:
            portfolio_id: Portfolio identity.
            allocation_version: Exact allocation version.

        Returns:
            Stored immutable allocation.

        Raises:
            PortfolioError: If the allocation is unknown.
        """
        logger.debug("Loading exact Portfolio allocation version")
        value = self._store.load_allocation(portfolio_id, allocation_version)
        if value is None:
            raise PortfolioError("PORT_NOT_FOUND", "ALLOCATION")
        return value

    def history(self, portfolio_id: str) -> tuple[ActivePortfolioAllocation, ...]:
        """Return complete immutable allocation history.

        Args:
            portfolio_id: Portfolio identity.

        Returns:
            Ordered immutable allocation history.
        """
        logger.debug("Loading complete Portfolio allocation history")
        return self._store.load_history(portfolio_id)

    def plan(
        self,
        plan_id: str,
        plan_version: str | None = None,
    ) -> PortfolioRebalancePlan:
        """Return one exact or latest immutable rebalance plan.

        Args:
            plan_id: Plan identity.
            plan_version: Exact version or ``None`` for latest.

        Returns:
            Stored immutable plan.

        Raises:
            PortfolioError: If the plan is unknown.
        """
        logger.debug("Loading Portfolio rebalance plan")
        value = self._store.load_plan(plan_id, plan_version)
        if value is None:
            raise PortfolioError("PORT_NOT_FOUND", "PLAN")
        return value


__all__: tuple[str, ...] = (
    "AuditOutboxRecord",
    "PortfolioRepository",
    "PortfolioStateStore",
    "scope_key",
)

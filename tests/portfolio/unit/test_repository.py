"""Unit tests for Portfolio injected-store persistence semantics."""

# ruff: noqa: INP001

from __future__ import annotations

import inspect
from collections.abc import Mapping

import pytest
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioConstructionResult,
    PortfolioRebalancePlan,
)
from app.services.portfolio.exceptions import PortfolioError
from app.services.portfolio.state import (
    PORTFOLIO_MIGRATIONS,
    AuditOutboxRecord,
    PortfolioRepository,
    scope_key,
)
from app.services.portfolio.state import repository as repository_module
from app.utils import logger


class FakePortfolioStore:
    """Deterministic in-memory fake implementing the atomic store port."""

    def __init__(self) -> None:
        """Initialize empty immutable-history test state."""
        logger.debug("Initializing fake Portfolio atomic store")
        self.constructions: dict[str, PortfolioConstructionResult] = {}
        self.allocations: dict[tuple[str, str], ActivePortfolioAllocation] = {}
        self.histories: dict[str, list[ActivePortfolioAllocation]] = {}
        self.active_scopes: dict[str, tuple[ActivePortfolioAllocation, int]] = {}
        self.plans: dict[tuple[str, str], PortfolioRebalancePlan] = {}
        self.idempotency: dict[str, tuple[str, ActivePortfolioAllocation]] = {}
        self.audit_records: list[AuditOutboxRecord] = []

    def save_construction(
        self,
        result: PortfolioConstructionResult,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioConstructionResult:
        """Store a construction result and audit record atomically.

        Args:
            result: Immutable construction result.
            audit_record: Redacted audit record.

        Returns:
            Stored construction result.
        """
        logger.debug("Saving construction in fake Portfolio store")
        existing = self.constructions.get(result.result_id)
        if existing is not None and existing.canonical_hash != result.canonical_hash:
            raise PortfolioError("PORT_IDEMPOTENCY_CONFLICT", "CONSTRUCTION")
        self.constructions[result.result_id] = result
        self.audit_records.append(audit_record)
        return existing or result

    def activate_allocation(
        self,
        allocation: ActivePortfolioAllocation,
        expected_predecessor: str | None,
        expected_revision: int,
        material_hash: str,
        audit_record: AuditOutboxRecord,
    ) -> ActivePortfolioAllocation:
        """Apply idempotency and compare-and-swap activation atomically.

        Args:
            allocation: New allocation version.
            expected_predecessor: Expected predecessor version.
            expected_revision: Expected active revision.
            material_hash: Canonical idempotency material.
            audit_record: Redacted audit record.

        Returns:
            Stored or identical allocation.
        """
        logger.debug("Activating allocation in fake Portfolio store")
        existing_idempotency = self.idempotency.get(allocation.idempotency_key)
        if existing_idempotency is not None:
            if existing_idempotency[0] != material_hash:
                raise PortfolioError("PORT_IDEMPOTENCY_CONFLICT", "ACTIVATION")
            return existing_idempotency[1]
        key = scope_key(allocation.scope)
        active = self.active_scopes.get(key)
        current_version = None if active is None else active[0].allocation_version
        current_revision = 0 if active is None else active[1]
        if (
            current_version != expected_predecessor
            or current_revision != expected_revision
        ):
            raise PortfolioError("PORT_VERSION_CONFLICT", "ACTIVE_SCOPE")
        new_revision = current_revision + 1
        self.allocations[(allocation.portfolio_id, allocation.allocation_version)] = (
            allocation
        )
        self.histories.setdefault(allocation.portfolio_id, []).append(allocation)
        self.active_scopes[key] = (allocation, new_revision)
        self.idempotency[allocation.idempotency_key] = (material_hash, allocation)
        self.audit_records.append(audit_record)
        return allocation

    def save_plan(
        self,
        plan: PortfolioRebalancePlan,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioRebalancePlan:
        """Store an immutable plan version and audit record.

        Args:
            plan: Immutable plan.
            audit_record: Redacted audit record.

        Returns:
            Stored plan.
        """
        logger.debug("Saving plan in fake Portfolio store")
        self.plans[(plan.plan_id, plan.plan_version)] = plan
        self.audit_records.append(audit_record)
        return plan

    def load_active(
        self,
        portfolio_id: str,
        scope_key_value: str,
    ) -> tuple[ActivePortfolioAllocation, int] | None:
        """Load an active allocation by canonical scope.

        Args:
            portfolio_id: Portfolio identity.
            scope_key_value: Canonical governed scope.

        Returns:
            Active allocation and revision, or ``None``.
        """
        logger.debug("Loading active allocation from fake Portfolio store")
        value = self.active_scopes.get(scope_key_value)
        if value is None or value[0].portfolio_id != portfolio_id:
            return None
        return value

    def load_allocation(
        self,
        portfolio_id: str,
        allocation_version: str,
    ) -> ActivePortfolioAllocation | None:
        """Load one immutable allocation version.

        Args:
            portfolio_id: Portfolio identity.
            allocation_version: Exact allocation version.

        Returns:
            Stored allocation or ``None``.
        """
        logger.debug("Loading allocation version from fake Portfolio store")
        return self.allocations.get((portfolio_id, allocation_version))

    def load_history(self, portfolio_id: str) -> tuple[ActivePortfolioAllocation, ...]:
        """Load complete allocation history.

        Args:
            portfolio_id: Portfolio identity.

        Returns:
            Ordered immutable allocation history.
        """
        logger.debug("Loading history from fake Portfolio store")
        return tuple(self.histories.get(portfolio_id, ()))

    def load_plan(
        self,
        plan_id: str,
        plan_version: str | None,
    ) -> PortfolioRebalancePlan | None:
        """Load exact or latest plan from the fake store.

        Args:
            plan_id: Plan identity.
            plan_version: Exact version or ``None``.

        Returns:
            Stored plan or ``None``.
        """
        logger.debug("Loading plan from fake Portfolio store")
        candidates = [
            value for (identity, _), value in self.plans.items() if identity == plan_id
        ]
        if plan_version is not None:
            return self.plans.get((plan_id, plan_version))
        return (
            None
            if not candidates
            else sorted(candidates, key=lambda item: item.plan_version)[-1]
        )


def _audit() -> Mapping[str, str]:
    """Return one redacted audit outbox record.

    Returns:
        Safe symbolic audit mapping.
    """
    logger.debug("Building Portfolio repository audit test record")
    return {
        "event_id": "audit-1",
        "event_type": "portfolio.activation",
        "aggregate_id": "portfolio-alpha",
        "request_id": "req-portfolio-0001",
        "correlation_id": "corr-portfolio-0001",
    }


def test_repository_activation_is_atomic_idempotent_and_versioned(
    active_allocation: ActivePortfolioAllocation,
) -> None:
    """Verify activation CAS, idempotency, and one active scope.

    Args:
        active_allocation: Complete governed allocation.
    """
    logger.info("Testing Portfolio repository atomic activation semantics")
    store = FakePortfolioStore()
    repository = PortfolioRepository(store)

    first = repository.activate(
        active_allocation,
        expected_predecessor=None,
        expected_revision=0,
        audit_record=_audit(),
    )
    replay = repository.activate(
        active_allocation,
        expected_predecessor=None,
        expected_revision=0,
        audit_record=_audit(),
    )

    assert replay is first
    assert repository.active(
        active_allocation.portfolio_id, active_allocation.scope
    ) == (
        active_allocation,
        1,
    )
    assert repository.history(active_allocation.portfolio_id) == (active_allocation,)


def test_repository_preserves_superseded_and_rollback_versions(
    active_allocation: ActivePortfolioAllocation,
) -> None:
    """Verify every successor and rollback remains immutable history.

    Args:
        active_allocation: Initial complete allocation.
    """
    logger.info("Testing immutable Portfolio allocation history")
    repository = PortfolioRepository(FakePortfolioStore())
    repository.activate(
        active_allocation,
        expected_predecessor=None,
        expected_revision=0,
        audit_record=_audit(),
    )
    rollback = active_allocation.model_copy(
        update={
            "allocation_id": "allocation-2",
            "allocation_version": "allocation-version-2",
            "predecessor_version": active_allocation.allocation_version,
            "rollback_of_version": active_allocation.allocation_version,
            "idempotency_key": "activation-idempotency-2",
            "canonical_hash": "9" * 64,
        }
    )
    repository.activate(
        rollback,
        expected_predecessor=active_allocation.allocation_version,
        expected_revision=1,
        audit_record=_audit(),
    )

    assert repository.history(active_allocation.portfolio_id) == (
        active_allocation,
        rollback,
    )
    assert (
        repository.allocation(
            active_allocation.portfolio_id,
            active_allocation.allocation_version,
        )
        is active_allocation
    )


def test_repository_detects_cas_and_idempotency_conflicts(
    active_allocation: ActivePortfolioAllocation,
) -> None:
    """Verify different material and stale revisions fail closed.

    Args:
        active_allocation: Initial complete allocation.
    """
    logger.info("Testing Portfolio repository conflict detection")
    repository = PortfolioRepository(FakePortfolioStore())
    repository.activate(
        active_allocation,
        expected_predecessor=None,
        expected_revision=0,
        audit_record=_audit(),
    )
    conflicting = active_allocation.model_copy(update={"canonical_hash": "8" * 64})
    with pytest.raises(PortfolioError, match="PORT_IDEMPOTENCY_CONFLICT"):
        repository.activate(
            conflicting,
            expected_predecessor=active_allocation.allocation_version,
            expected_revision=1,
            audit_record=_audit(),
        )
    successor = active_allocation.model_copy(
        update={
            "allocation_id": "allocation-2",
            "allocation_version": "allocation-version-2",
            "predecessor_version": active_allocation.allocation_version,
            "idempotency_key": "activation-idempotency-2",
            "canonical_hash": "7" * 64,
        }
    )
    with pytest.raises(PortfolioError, match="PORT_VERSION_CONFLICT"):
        repository.activate(
            successor,
            expected_predecessor=None,
            expected_revision=0,
            audit_record=_audit(),
        )


def test_state_declares_data_executed_migrations_without_storage_access() -> None:
    """Verify schema coverage and Portfolio-owned persistence boundary."""
    logger.info("Testing Portfolio state migration and ownership boundary")
    statements = "\n".join(PORTFOLIO_MIGRATIONS[0].statements)
    source = inspect.getsource(repository_module)

    for table in (
        "portfolio_definitions",
        "portfolio_construction_results",
        "portfolio_allocation_versions",
        "portfolio_active_scopes",
        "portfolio_rebalance_plans",
        "portfolio_idempotency",
        "portfolio_audit_outbox",
    ):
        assert table in statements
    assert "sqlite" not in source.lower()
    assert "app.services.data.persistence" not in source

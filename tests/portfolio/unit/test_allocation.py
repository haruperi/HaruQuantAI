"""Unit tests for governed Portfolio activation and rollback semantics."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.portfolio._settings import PortfolioSettings
from app.services.portfolio.allocation import AllocationService
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioConstructionResult,
)
from app.services.portfolio.contracts.errors import PortfolioError
from app.services.risk import (
    create_allocation_risk_decision,
    create_kill_switch_state,
    get_decision_state,
)
from app.utils import get_logger

logger = get_logger(__name__)

# Private type-only aliases; Risk exposes functions, not contract classes.
AllocationBudgetActivationRequest = object
AllocationRiskDecision = object
KillSwitchState = object
PortfolioSimulationResult = object


class RecordingRepository:
    """Record the one allocation passed through repository activation."""

    def __init__(self) -> None:
        """Initialize without a recorded allocation."""
        logger.debug("Initializing recording Portfolio repository")
        self.value: ActivePortfolioAllocation | None = None

    def activate(
        self,
        allocation: ActivePortfolioAllocation,
        *,
        expected_predecessor: str | None,
        expected_revision: int,
        audit_record: object,
    ) -> ActivePortfolioAllocation:
        """Record and return one allocation.

        Args:
            allocation: New governed allocation.
            expected_predecessor: Expected predecessor version.
            expected_revision: Expected repository revision.
            audit_record: Redacted audit record.

        Returns:
            Supplied allocation.
        """
        logger.debug("Recording Portfolio allocation activation")
        del expected_predecessor, expected_revision, audit_record
        self.value = allocation
        return allocation


def _simulation(
    result: PortfolioConstructionResult,
    now: datetime,
) -> PortfolioSimulationResult:
    """Build a completed exact Simulation result binding.

    Args:
        result: Construction result under validation.
        now: Stable UTC time.

    Returns:
        Minimal public Simulation result instance.
    """
    logger.debug("Building Portfolio Simulation gate fixture")
    return SimpleNamespace(
        status="completed",
        portfolio_id=result.portfolio_id,
        construction_result_id=result.result_id,
        construction_version=result.portfolio_version,
        result_id="simulation-result-1",
        result_hash="e" * 64,
        measurement_end=now,
    )


def _risk_decision(
    result: PortfolioConstructionResult,
    now: datetime,
) -> AllocationRiskDecision:
    """Build a current approving Risk allocation decision.

    Args:
        result: Construction result under validation.
        now: Stable UTC time.

    Returns:
        Current inactive Risk decision.
    """
    logger.debug("Building Portfolio Risk decision gate fixture")
    return create_allocation_risk_decision(
        decision_id="risk-decision-1",
        portfolio_id=result.portfolio_id,
        reviewed_version=result.portfolio_version,
        state=get_decision_state("APPROVE"),
        capped_weights={
            item.component_id: item.capital_weight for item in result.component_weights
        },
        risk_budget_projection={
            item.component_id: Decimal("0.5") for item in result.component_weights
        },
        conditions=(),
        policy_version="risk-policy-1",
        evidence_refs={"construction": result.canonical_hash},
        issued_at=now,
        expires_at=now + timedelta(minutes=10),
        active=False,
        predecessor_version=None,
        audit_ref="risk-audit-1",
    )


def _inactive_kill_switch(now: datetime) -> KillSwitchState:
    """Build canonical inactive Risk kill-switch evidence.

    Args:
        now: Stable UTC time.

    Returns:
        Inactive global kill-switch state.
    """
    logger.debug("Building inactive Portfolio kill-switch fixture")
    return create_kill_switch_state(
        state_id="kill-switch-1",
        scope_level="global",
        scope={},
        state="inactive",
        reason="policy-clear",
        version=1,
        updated_at=now,
    )


def _activator(
    request: AllocationBudgetActivationRequest,
    decision: AllocationRiskDecision,
) -> AllocationRiskDecision:
    """Return the exact Risk decision marked active.

    Args:
        request: Receiver-owned Risk activation request.
        decision: Reviewed Risk decision.

    Returns:
        Active authoritative Risk decision.
    """
    logger.info("Executing deterministic fake Risk budget activation")
    assert request.schema_id == "risk.allocation_budget_activation_request.v1"
    assert request.decision_id == decision.decision_id
    return decision.model_copy(update={"active": True})


def test_simulation_activation_requires_all_external_gates(
    construction_result: PortfolioConstructionResult,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Verify Simulation policy activates only after Risk and kill-switch gates.

    Args:
        construction_result: Complete construction result.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
    """
    logger.info("Testing governed simulation Portfolio activation")
    repository = RecordingRepository()
    service = AllocationService(
        portfolio_settings,
        repository,  # type: ignore[arg-type]
        _activator,
    )
    allocation = service.activate(
        construction_result,
        simulation=_simulation(construction_result, portfolio_now),
        risk_decision=_risk_decision(construction_result, portfolio_now),
        kill_switches=(_inactive_kill_switch(portfolio_now),),
        approval_attestation=None,
        approval_validation=None,
        runtime_profile="simulation",
        activated_at=portfolio_now,
        expires_at=portfolio_now + timedelta(days=1),
        idempotency_key="activation-key-1",
        expected_predecessor=None,
        expected_revision=0,
        audit_ref="portfolio-audit-1",
        audit_record={"event_type": "portfolio.activation"},
    )

    assert repository.value is allocation
    assert allocation.risk_decision_id == "risk-decision-1"
    assert allocation.risk_budget_projection_ref == "risk-decision-1"


def test_activation_blocks_kill_switch_and_missing_human_approval(
    construction_result: PortfolioConstructionResult,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Verify kill switches and demo/live approval policy fail closed.

    Args:
        construction_result: Complete construction result.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
    """
    logger.info("Testing Portfolio activation kill-switch and approval gates")
    service = AllocationService(
        portfolio_settings,
        RecordingRepository(),  # type: ignore[arg-type]
        _activator,
    )
    arguments = {
        "simulation": _simulation(construction_result, portfolio_now),
        "risk_decision": _risk_decision(construction_result, portfolio_now),
        "approval_attestation": None,
        "approval_validation": None,
        "activated_at": portfolio_now,
        "expires_at": portfolio_now + timedelta(days=1),
        "idempotency_key": "activation-key-1",
        "expected_predecessor": None,
        "expected_revision": 0,
        "audit_ref": "portfolio-audit-1",
        "audit_record": {"event_type": "portfolio.activation"},
    }
    active_switch = _inactive_kill_switch(portfolio_now).model_copy(
        update={"state": "active"}
    )
    with pytest.raises(PortfolioError, match="PORT_KILL_SWITCH_ACTIVE"):
        service.activate(
            construction_result,
            kill_switches=(active_switch,),
            runtime_profile="simulation",
            **arguments,
        )
    with pytest.raises(PortfolioError, match="PORT_APPROVAL_REQUIRED"):
        service.activate(
            construction_result,
            kill_switches=(_inactive_kill_switch(portfolio_now),),
            runtime_profile="demo",
            **arguments,
        )


def test_activation_rejects_each_invalid_external_gate(
    construction_result: PortfolioConstructionResult,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Exercise fail-closed activation branches for malformed owner evidence."""
    base = {
        "simulation": _simulation(construction_result, portfolio_now),
        "risk_decision": _risk_decision(construction_result, portfolio_now),
        "kill_switches": (_inactive_kill_switch(portfolio_now),),
        "approval_attestation": None,
        "approval_validation": None,
        "runtime_profile": "simulation",
        "activated_at": portfolio_now,
        "expires_at": portfolio_now + timedelta(days=1),
        "idempotency_key": "activation-key-negative",
        "expected_predecessor": None,
        "expected_revision": 0,
        "audit_ref": "portfolio-audit-negative",
        "audit_record": {"event_type": "portfolio.activation"},
    }
    service = AllocationService(
        portfolio_settings,
        RecordingRepository(),  # type: ignore[arg-type]
        _activator,
    )

    variants = (
        (
            {"activated_at": portfolio_now.replace(tzinfo=None)},
            "ACTIVATED_AT_NOT_UTC",
        ),
        (
            {
                "simulation": SimpleNamespace(
                    **{
                        **vars(base["simulation"]),
                        "construction_result_id": "different",
                    }
                )
            },
            "PORT_SIMULATION_INVALID",
        ),
        (
            {
                "risk_decision": base["risk_decision"].model_copy(
                    update={"expires_at": portfolio_now}
                )
            },
            "PORT_RISK_AUTHORIZATION_INVALID",
        ),
        ({"kill_switches": ()}, "PORT_KILL_SWITCH_ACTIVE"),
        ({"expires_at": portfolio_now}, "ALLOCATION_EXPIRY"),
    )
    for overrides, expected in variants:
        with pytest.raises(PortfolioError, match=expected):
            service.activate(construction_result, **{**base, **overrides})

    invalid_policy = portfolio_settings.model_copy(
        update={
            "portfolio_activation_approval_policy": {
                **portfolio_settings.portfolio_activation_approval_policy,
                "simulation": "explicit_human",
            }
        },
    )
    with pytest.raises(PortfolioError, match="SIMULATION_APPROVAL"):
        AllocationService(
            invalid_policy,
            RecordingRepository(),  # type: ignore[arg-type]
            _activator,
        ).activate(construction_result, **base)

    def failing_activator(
        _request: object,
        _decision: object,
    ) -> object:
        """Raise one receiver failure for dependency mapping coverage."""
        raise RuntimeError("risk receiver unavailable")

    with pytest.raises(PortfolioError, match="PORT_DEPENDENCY_FAILED"):
        AllocationService(
            portfolio_settings,
            RecordingRepository(),  # type: ignore[arg-type]
            failing_activator,  # type: ignore[arg-type]
        ).activate(construction_result, **base)


def test_rollback_is_recorded_only_as_new_governed_version(
    construction_result: PortfolioConstructionResult,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Verify rollback metadata is carried on a newly activated version.

    Args:
        construction_result: Complete construction result.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
    """
    logger.info("Testing governed Portfolio rollback version creation")
    candidate = construction_result.model_copy(
        update={"portfolio_version": "version-2", "canonical_hash": "8" * 64}
    )
    allocation = AllocationService(
        portfolio_settings,
        RecordingRepository(),  # type: ignore[arg-type]
        _activator,
    ).activate(
        candidate,
        simulation=_simulation(candidate, portfolio_now),
        risk_decision=_risk_decision(candidate, portfolio_now),
        kill_switches=(_inactive_kill_switch(portfolio_now),),
        approval_attestation=None,
        approval_validation=None,
        runtime_profile="simulation",
        activated_at=portfolio_now,
        expires_at=portfolio_now + timedelta(days=1),
        idempotency_key="rollback-key-1",
        expected_predecessor="version-1",
        expected_revision=1,
        audit_ref="portfolio-audit-2",
        audit_record={"event_type": "portfolio.rollback"},
        rollback_of_version="version-1",
    )

    assert allocation.allocation_version == "version-2"
    assert allocation.predecessor_version == "version-1"
    assert allocation.rollback_of_version == "version-1"

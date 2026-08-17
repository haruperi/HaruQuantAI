"""Portfolio gateway request schemas."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from app.services.api.contracts.models import _BaseApiContract
from app.services.api.workstation.simulation.schemas import (
    PortfolioSimulationRunRequest,  # noqa: TC001 - Pydantic resolves this model.
)


class PortfolioStrategyAllocationRef(_BaseApiContract):
    """Exact API projection of one Portfolio component reference.

    Attributes:
        component_id: Portfolio-local stable component identity.
        strategy_id: Strategy-owned immutable identity.
        strategy_version: Exact Strategy version.
        registry_record_hash: Strategy registry record digest.
        eligibility_decision_id: Risk eligibility decision reference.
    """

    component_id: str
    strategy_id: str
    strategy_version: str
    registry_record_hash: str
    eligibility_decision_id: str


class PortfolioFixedWeightInput(_BaseApiContract):
    """Exact API projection of one fixed-weight component.

    Attributes:
        component_id: Referenced component identity.
        capital_weight: Target capital metadata weight.
        proposed_risk_budget_weight: Non-authoritative proposed Risk budget.
    """

    component_id: str
    capital_weight: Decimal
    proposed_risk_budget_weight: Decimal


class PortfolioEvidenceReferenceSet(_BaseApiContract):
    """Exact API projection of one Portfolio construction evidence lineage.

    Attributes:
        account_snapshot_id: Data account snapshot reference.
        account_snapshot_hash: Account snapshot digest.
        account_snapshot_as_of: Account snapshot observation time.
        market_dataset_id: Data market dataset reference.
        market_dataset_hash: Market dataset digest.
        market_dataset_as_of: Market evidence observation time.
        analytics_evidence_id: Analytics evidence reference.
        analytics_evidence_hash: Analytics evidence digest.
        analytics_evidence_as_of: Analytics evidence observation time.
        fx_evidence_ids: Ordered Data FX evidence references.
        fx_evidence_hashes: Ordered digests aligned to each FX reference.
    """

    account_snapshot_id: str
    account_snapshot_hash: str
    account_snapshot_as_of: datetime
    market_dataset_id: str
    market_dataset_hash: str
    market_dataset_as_of: datetime
    analytics_evidence_id: str
    analytics_evidence_hash: str
    analytics_evidence_as_of: datetime
    fx_evidence_ids: tuple[str, ...]
    fx_evidence_hashes: tuple[str, ...]


class PortfolioConstructRequest(_BaseApiContract):
    """Exact API projection of ``PortfolioConstructionRequest``.

    The bridge converts this boundary model into the strict Portfolio-owned
    construction request through Portfolio's package-root value factory.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.construction_request.v1"] = (
        "portfolio.construction_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    portfolio_id: str
    portfolio_version: str
    scope: Mapping[str, str]
    components: tuple[PortfolioStrategyAllocationRef, ...]
    method: Literal["fixed", "equal", "inverse_volatility"]
    fixed_weights: tuple[PortfolioFixedWeightInput, ...]
    evidence: PortfolioEvidenceReferenceSet
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    runtime_profile: Literal["simulation", "demo", "live"]
    execution_route: Literal["sim", "demo", "live"]
    simulation_policy_version: str
    requested_at: datetime


class PortfolioDefinitionRequest(_BaseApiContract):
    """Exact API projection of an immutable Portfolio definition."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.definition.v1"] = "portfolio.definition.v1"
    portfolio_id: str
    portfolio_version: str
    scope: Mapping[str, str]
    definition: Mapping[str, Any]
    canonical_hash: str


class PortfolioActivationRequest(_BaseApiContract):
    """Governed Portfolio activation command.

    Activation runs the complete owner workflow chain WF-PORT-001 through
    WF-PORT-004 as one governed write: the composed Portfolio workflow handle
    constructs the candidate and its validated evidence, coordinates the
    Simulation and Risk review, and only then activates. The gateway supplies
    no evidence of its own and never decides approval.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_activation_request.v1"] = (
        "api.portfolio_activation_request.v1"
    )
    construction: PortfolioConstructRequest
    simulation: PortfolioSimulationRunRequest
    approval_refs: tuple[str, ...] = ()
    approval_attestation: Mapping[str, Any] | None = None
    approval_validation: Mapping[str, Any] | None = None
    expires_at: datetime
    expected_predecessor: str | None = None
    expected_revision: int


class PortfolioRollbackRequest(_BaseApiContract):
    """Governed Portfolio rollback command.

    Rollback shares activation's evidence chain and additionally names the
    immutable prior version being rolled back to. Portfolio creates a new
    forward version; no historical version is mutated or deleted.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_rollback_request.v1"] = (
        "api.portfolio_rollback_request.v1"
    )
    construction: PortfolioConstructRequest
    simulation: PortfolioSimulationRunRequest
    rollback_of_version: str
    approval_refs: tuple[str, ...] = ()
    approval_attestation: Mapping[str, Any] | None = None
    approval_validation: Mapping[str, Any] | None = None
    expires_at: datetime
    expected_predecessor: str | None = None
    expected_revision: int


class PortfolioDriftRequest(_BaseApiContract):
    """Portfolio drift-assessment request over one active allocation.

    The gateway reads the active allocation through the Portfolio public status
    operation and forwards caller-supplied observed exposures. Drift thresholds
    and the resulting judgement remain entirely Portfolio-owned.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_drift_request.v1"] = (
        "api.portfolio_drift_request.v1"
    )
    scope: Mapping[str, str]
    actual_exposures: Mapping[str, Decimal]
    evidence_as_of: datetime
    risk_decision: Mapping[str, Any]
    eligibility_decisions: Mapping[str, Mapping[str, Any]]


class PortfolioRebalanceRequest(_BaseApiContract):
    """Governed Portfolio rebalance submission.

    Every evidence reference is opaque and owner-resolved. The runtime profile
    and execution route must match the operator-selected account mode; the
    composition layer enforces that before Portfolio is reached. No separate
    live-enablement flag applies - Risk decides whether the change proceeds.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_rebalance_request.v1"] = (
        "api.portfolio_rebalance_request.v1"
    )
    plan: Mapping[str, Any]
    account_evidence_ref: str
    market_evidence_ref: str
    fx_evidence_refs: tuple[str, ...]
    runtime_profile: Literal["simulation", "demo", "live"]
    execution_route: Literal["sim", "demo", "live"]
    approval_refs: tuple[str, ...]
    approval_token_ref: str
    trading_request_id: str
    valid_until: datetime


class PortfolioMeasurementRequest(_BaseApiContract):
    """Recompute one Portfolio measurement from immutable Trading evidence."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_measurement_request.v1"] = (
        "api.portfolio_measurement_request.v1"
    )
    plan_id: str
    trading_request_id: str


__all__ = (
    "PortfolioActivationRequest",
    "PortfolioConstructRequest",
    "PortfolioDefinitionRequest",
    "PortfolioDriftRequest",
    "PortfolioEvidenceReferenceSet",
    "PortfolioFixedWeightInput",
    "PortfolioMeasurementRequest",
    "PortfolioRebalanceRequest",
    "PortfolioRollbackRequest",
    "PortfolioStrategyAllocationRef",
)

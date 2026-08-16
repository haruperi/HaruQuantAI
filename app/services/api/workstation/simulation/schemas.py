"""Simulation gateway request schemas."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import Field, field_validator

from app.services.api.contracts.models import _BaseApiContract, _validate_non_empty


class SimulationSessionCreateRequest(_BaseApiContract):
    """Request to open playback over one completed Simulation run."""

    run_id: str = Field(min_length=1, max_length=200)

    @field_validator("run_id")
    @classmethod
    def _validate_run_id(cls, value: str) -> str:
        """Validate one trimmed completed-run identity.

        Returns:
            Validated run identity.
        """
        return _validate_non_empty(value, "run_id")


class SimulationRunRequest(_BaseApiContract):
    """Exact API projection of ``SimulationBacktestRequest``."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["simulation.backtest_request.v1"] = (
        "simulation.backtest_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    strategy_id: str
    strategy_version: str
    strategy_config_ref: str
    strategy_config_hash: str
    data_ref: str
    data_version: str
    data_hash: str
    tick_generation_ref: str
    tick_generation_version: str
    tick_generation_hash: str
    execution_profile_ref: str
    execution_profile_version: str
    execution_profile_hash: str
    risk_policy_ref: str
    risk_policy_version: str
    risk_policy_hash: str
    symbol: str
    timeframe: str
    start: datetime
    end: datetime
    parameters: Mapping[str, object]
    initial_balance: Decimal
    account_currency: str
    asset_class: Literal["FX"]
    seed: int
    runtime_profile: Literal["simulation", "fast_research"]
    execution_route: Literal["sim"]
    canonical: bool
    config_hash: str


class PortfolioComponentRunRequest(_BaseApiContract):
    """One exact portfolio component and its canonical backtest request."""

    component_id: str
    capital_weight: Decimal
    risk_budget: Decimal
    risk_decision_id: str
    metrics_ref: str
    backtest_request: SimulationRunRequest


class PortfolioSimulationRunRequest(_BaseApiContract):
    """Exact API projection of ``PortfolioBacktestRequest``."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["simulation.portfolio_backtest_request.v1"] = (
        "simulation.portfolio_backtest_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    portfolio_id: str
    construction_result_id: str
    construction_version: str
    components: tuple[PortfolioComponentRunRequest, ...]
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    fx_evidence_ids: tuple[str, ...]
    fx_evidence_versions: tuple[str, ...]
    fx_evidence_hashes: tuple[str, ...]
    execution_profile_version: str
    risk_policy_version: str
    seed: int
    initial_balance: Decimal
    runtime_profile: Literal["simulation"]
    execution_route: Literal["sim"]
    config_hash: str


class SimulationBranchRequest(_BaseApiContract):
    """Live what-if branch command.

    The overrides are Simulator-owned request fields. The gateway forwards them
    unchanged; the Simulator validates them and refuses any override that
    cannot produce a valid request, so no branch opens on bad input.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.simulation_branch_request.v1"] = (
        "api.simulation_branch_request.v1"
    )
    overrides: Mapping[str, Any]


__all__ = (
    "PortfolioComponentRunRequest",
    "PortfolioSimulationRunRequest",
    "SimulationBranchRequest",
    "SimulationRunRequest",
    "SimulationSessionCreateRequest",
)

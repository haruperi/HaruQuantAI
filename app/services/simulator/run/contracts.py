"""Versioned receiver-owned requests and run dependency protocol."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, Protocol

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.utils import canonical_digest, canonical_json, logger

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset
    from app.services.data.evidence.fx_contracts import FXConversionEvidence
    from app.services.indicators import IndicatorResult
    from app.services.risk import RiskDecisionPackage
    from app.services.simulator.accounting import (
        ExecutionCostModel,
        SymbolSpecification,
    )
    from app.services.simulator.execution import ExecutionProfile
    from app.services.simulator.state import SimulationStateStore
    from app.services.strategy import TradeIntent
    from app.services.trading import OrderIntent

type JsonParameter = (
    None
    | bool
    | int
    | str
    | Decimal
    | tuple["JsonParameter", ...]
    | Mapping[str, "JsonParameter"]
)


def _hash_material(payload: Mapping[str, object]) -> str:
    """Hash execution-affecting request material.

    Args:
        payload: Complete request projection.

    Returns:
        Lowercase SHA-256 digest excluding trace IDs and config hash.
    """
    logger.debug("Hashing Simulation request configuration material")
    excluded = {"request_id", "workflow_id", "correlation_id", "config_hash"}
    material = {key: value for key, value in payload.items() if key not in excluded}
    return canonical_digest(material)


class SimulationBacktestRequestV1(BaseModel):
    """Exact reference-based synchronous FX backtest request version 1."""

    model_config = ConfigDict(extra="forbid", frozen=True)

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
    parameters: Mapping[str, JsonParameter]
    initial_balance: Decimal
    account_currency: str
    asset_class: Literal["FX"]
    seed: int
    runtime_profile: Literal["simulation", "fast_research"]
    execution_route: Literal["sim"]
    canonical: bool
    config_hash: str

    @classmethod
    def calculate_config_hash(cls, payload: Mapping[str, object]) -> str:
        """Calculate the required configuration hash for request construction.

        Args:
            payload: Full request field projection.

        Returns:
            Lowercase SHA-256 configuration digest.
        """
        logger.debug("Calculating SimulationBacktestRequestV1 config hash")
        material = dict(payload)
        material.setdefault("contract_version", "v1")
        material.setdefault("schema_id", "simulation.backtest_request.v1")
        return _hash_material(material)

    @field_validator("start", "end")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate request aware UTC time.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated timestamp.

        Raises:
            ValueError: If not UTC.
        """
        logger.debug("Validating Simulation request UTC time")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("Simulation request times must be aware UTC")
        return value

    @field_validator("initial_balance")
    @classmethod
    def _validate_balance(cls, value: Decimal) -> Decimal:
        """Validate finite positive initial balance.

        Args:
            value: Candidate balance.

        Returns:
            Validated balance.

        Raises:
            ValueError: If invalid.
        """
        logger.debug("Validating Simulation request initial balance")
        if not value.is_finite() or value <= 0:
            raise ValueError("Initial balance must be finite and positive")
        return value

    @field_validator("parameters", mode="after")
    @classmethod
    def _freeze_parameters(
        cls, value: Mapping[str, JsonParameter]
    ) -> Mapping[str, JsonParameter]:
        """Canonicalize and freeze bounded request parameters.

        Args:
            value: Candidate parameter mapping.

        Returns:
            Immutable parameter mapping.
        """
        logger.debug("Freezing Simulation request parameters")
        canonical_json(value)
        return MappingProxyType(dict(value))

    @field_serializer("parameters", when_used="json")
    def _serialize_parameters(
        self, value: Mapping[str, JsonParameter]
    ) -> dict[str, JsonParameter]:
        """Serialize immutable request parameters.

        Args:
            value: Frozen parameter mapping.

        Returns:
            Ordinary mapping.
        """
        logger.debug("Serializing Simulation request parameters")
        return dict(value)

    @model_validator(mode="after")
    def _validate_request(self) -> SimulationBacktestRequestV1:
        """Validate range, profile, and configuration identity.

        Returns:
            Validated request.

        Raises:
            ValueError: If request relationships conflict.
        """
        logger.debug("Validating Simulation backtest request relationships")
        if self.end < self.start:
            raise ValueError("Backtest end must not precede start")
        if self.runtime_profile == "simulation" and not self.canonical:
            raise ValueError("Official simulation request must be canonical")
        if self.runtime_profile == "fast_research" and self.canonical:
            raise ValueError("Fast research request cannot be canonical")
        payload = self.model_dump(mode="python", warnings=False)
        if self.config_hash != type(self).calculate_config_hash(payload):
            raise ValueError("config_hash does not match request material")
        return self


class PortfolioComponentRequest(BaseModel):
    """One ordered Simulation-owned portfolio component projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    component_id: str
    capital_weight: Decimal
    risk_budget: Decimal
    risk_decision_id: str
    metrics_ref: str
    backtest_request: SimulationBacktestRequestV1


class PortfolioBacktestRequestV1(BaseModel):
    """Self-contained receiver-owned portfolio candidate request version 1."""

    model_config = ConfigDict(extra="forbid", frozen=True)

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
    components: tuple[PortfolioComponentRequest, ...]
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    fx_evidence_ids: tuple[str, ...]
    execution_profile_version: str
    risk_policy_version: str
    seed: int
    initial_balance: Decimal
    runtime_profile: Literal["simulation"]
    execution_route: Literal["sim"]
    config_hash: str

    @classmethod
    def calculate_config_hash(cls, payload: Mapping[str, object]) -> str:
        """Calculate portfolio request configuration identity.

        Args:
            payload: Full portfolio request projection.

        Returns:
            Lowercase SHA-256 digest.
        """
        logger.debug("Calculating PortfolioBacktestRequestV1 config hash")
        material = dict(payload)
        material.setdefault("contract_version", "v1")
        material.setdefault("schema_id", "simulation.portfolio_backtest_request.v1")
        return _hash_material(material)

    @model_validator(mode="after")
    def _validate_portfolio(self) -> PortfolioBacktestRequestV1:
        """Validate component completeness and portfolio config hash.

        Returns:
            Validated portfolio request.

        Raises:
            ValueError: If component or identity evidence is invalid.
        """
        logger.debug("Validating Simulation portfolio request relationships")
        if not self.components or self.measurement_end < self.measurement_start:
            raise ValueError("Portfolio components and ordered window are required")
        if sum((row.capital_weight for row in self.components), Decimal(0)) != 1:
            raise ValueError("Portfolio component weights must sum exactly to one")
        identifiers = tuple(row.component_id for row in self.components)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Portfolio component IDs must be unique")
        if not self.initial_balance.is_finite() or self.initial_balance <= 0:
            raise ValueError("Portfolio initial balance must be positive")
        payload = self.model_dump(mode="python", warnings=False)
        if self.config_hash != type(self).calculate_config_hash(payload):
            raise ValueError("config_hash does not match portfolio material")
        return self


class SimulationRunDependencies(Protocol):
    """Typed receiver-owned composition seam for one Simulation run."""

    state_store: SimulationStateStore
    artifact_root: Path
    fast_research_enabled: bool

    def load_market_data(self, request: SimulationBacktestRequestV1) -> MarketDataset:
        """Load the immutable referenced Data dataset."""
        logger.debug("Declaring Simulation load_market_data dependency")
        del request
        raise NotImplementedError

    def generate_tick_series(
        self, dataset: MarketDataset, request: SimulationBacktestRequestV1
    ) -> MarketDataset:
        """Invoke Data's official real-evidence tick generator."""
        logger.debug("Declaring Simulation generate_tick_series dependency")
        del dataset, request
        raise NotImplementedError

    def calculate_indicators(
        self, dataset: MarketDataset, request: SimulationBacktestRequestV1
    ) -> tuple[IndicatorResult, ...]:
        """Calculate point-in-time Indicator evidence."""
        logger.debug("Declaring Simulation calculate_indicators dependency")
        del dataset, request
        raise NotImplementedError

    def evaluate_strategy(
        self,
        dataset: MarketDataset,
        indicators: tuple[IndicatorResult, ...],
        request: SimulationBacktestRequestV1,
    ) -> tuple[TradeIntent, ...]:
        """Evaluate a registered Strategy against supplied evidence."""
        logger.debug("Declaring Simulation evaluate_strategy dependency")
        del dataset, indicators, request
        raise NotImplementedError

    def review_risk(
        self,
        intents: tuple[TradeIntent, ...],
        request: SimulationBacktestRequestV1,
    ) -> tuple[RiskDecisionPackage, ...]:
        """Review Strategy proposals under the referenced sim policy."""
        logger.debug("Declaring Simulation review_risk dependency")
        del intents, request
        raise NotImplementedError

    def build_order_intents(
        self,
        decisions: tuple[RiskDecisionPackage, ...],
        request: SimulationBacktestRequestV1,
    ) -> tuple[OrderIntent, ...]:
        """Pack approved Risk decisions through Trading's public boundary."""
        logger.debug("Declaring Simulation build_order_intents dependency")
        del decisions, request
        raise NotImplementedError

    def resolve_execution_profile(
        self, request: SimulationBacktestRequestV1
    ) -> ExecutionProfile:
        """Resolve the exact referenced execution profile."""
        logger.debug("Declaring Simulation execution profile dependency")
        del request
        raise NotImplementedError

    def resolve_symbol_specification(
        self, request: SimulationBacktestRequestV1
    ) -> SymbolSpecification:
        """Resolve approved symbol constraints."""
        logger.debug("Declaring Simulation symbol specification dependency")
        del request
        raise NotImplementedError

    def resolve_cost_model(
        self, request: SimulationBacktestRequestV1
    ) -> ExecutionCostModel:
        """Resolve the exact referenced cost model."""
        logger.debug("Declaring Simulation cost-model dependency")
        del request
        raise NotImplementedError

    def resolve_fx_evidence(
        self, evidence_ids: tuple[str, ...]
    ) -> Mapping[str, FXConversionEvidence]:
        """Resolve one Data-owned FXConversionEvidence v1 per identifier.

        Simulation validates freshness through `validate_fx_evidence()` and
        never selects, refreshes, or synthesizes a rate. An identifier the
        caller cannot resolve fails the run closed.
        """
        logger.debug("Declaring Simulation FX evidence dependency")
        del evidence_ids
        raise NotImplementedError


__all__ = [
    "PortfolioBacktestRequestV1",
    "PortfolioComponentRequest",
    "SimulationBacktestRequestV1",
    "SimulationRunDependencies",
]

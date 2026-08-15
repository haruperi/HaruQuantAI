"""Versioned receiver-owned requests and run dependency protocol."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Protocol, Self, override

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.simulator.errors import guard_operation
from app.utils import (
    canonical_digest,
    canonical_json,
    get_logger,
)

type StandardResponse[T] = Any

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)
_SHA256_HEX_LENGTH = 64

if TYPE_CHECKING:
    FXConversionEvidence = Any
    MarketDataset = Any
    RiskDecisionPackage = Any
    create_trade_intent_value = Any
    from app.services.simulator.accounting import (
        ExecutionCostModel,
        SymbolSpecification,
    )
    from app.services.simulator.execution import ExecutionProfile
    from app.services.simulator.state import SimulationStateStore

    OrderIntent = Any

    AuditEvent = Any

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
    def calculate_config_hash(
        cls, payload: Mapping[str, object]
    ) -> StandardResponse[str]:
        """Calculate the required configuration hash for request construction.

        Args:
            payload: Full request field projection.

        Returns:
            Lowercase SHA-256 configuration digest.
        """
        logger.debug("Calculating SimulationBacktestRequestV1 config hash")

        def calculate(value: Mapping[str, object]) -> str:
            material = dict(value)
            material.setdefault("contract_version", "v1")
            material.setdefault("schema_id", "simulation.backtest_request.v1")
            return _hash_material(material)

        return guard_operation(
            calculate,
            operation="simulation.run.simulation_backtest_request_v1.calculate_config_hash",
            risk_level="low",
            read_only=True,
        )(payload)

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
        if self.config_hash != _hash_material(payload):
            raise ValueError("config_hash does not match request material")
        return self


class ProviderSpecificationRevisionBinding(BaseModel):
    """Immutable provider-revision identity bound into a V2 request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    revision_id: str
    checksum: str
    provider: str
    server: str
    environment: Literal["demo", "live"]
    account_digest: str
    symbol: str
    observed_at: datetime
    effective_from: datetime
    effective_to: datetime | None = None
    historical_provenance: Mapping[str, JsonParameter] | None = None

    @field_validator("checksum", "account_digest")
    @classmethod
    def _validate_digest(cls, value: str) -> str:
        """Validate a lowercase SHA-256 digest.

        Returns:
            Validated digest.

        Raises:
            ValueError: If the digest is malformed.
        """
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("provider revision digests must be lowercase SHA-256")
        return value

    @field_validator("observed_at", "effective_from", "effective_to")
    @classmethod
    def _validate_utc(cls, value: datetime | None) -> datetime | None:
        """Require aware UTC provider-revision bounds.

        Returns:
            Validated timestamp or ``None``.

        Raises:
            ValueError: If a timestamp is not aware UTC.
        """
        if value is not None and (
            value.tzinfo is None or value.utcoffset() != timedelta(0)
        ):
            raise ValueError("provider revision times must be aware UTC")
        return value

    @model_validator(mode="after")
    def _validate_interval(self) -> Self:
        """Validate interval order and provenance-backed history.

        Returns:
            Validated binding.

        Raises:
            ValueError: If bounds or provenance are invalid.
        """
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("provider revision interval must be positive")
        if self.effective_from < self.observed_at and not self.historical_provenance:
            raise ValueError("historical provider revision requires provenance")
        if self.historical_provenance is not None:
            canonical_json(self.historical_provenance)
        return self


class SimulationBacktestRequestV2(SimulationBacktestRequestV1):
    """Parity-eligible backtest request with complete execution identity."""

    contract_version: Literal["v2"] = "v2"  # type: ignore[assignment]
    schema_id: Literal["simulation.backtest_request.v2"] = (
        "simulation.backtest_request.v2"  # type: ignore[assignment]
    )
    execution_model_ref: str
    execution_model_hash: str
    calculation_model_hash: str
    calculation_artifact_checksum: str
    source_lineage_hash: str
    tick_lineage_hash: str
    market_evidence_class: Literal[
        "genuine_bid_ask_ticks", "depth_supported_ticks", "derived_bar_model"
    ]
    decision_instant_policy: Literal["point_in_time_available_at"]
    market_evidence_eligible: bool = False
    required_clock_edges: tuple[str, ...] = ()
    evidenced_clock_edges: tuple[str, ...] = ()
    provider_specification_revisions: tuple[ProviderSpecificationRevisionBinding, ...]
    initial_authority_state_hash: str
    certification_target: Literal["demo", "live"]
    close_open_positions_at_end: bool

    @classmethod
    @override
    def calculate_config_hash(
        cls, payload: Mapping[str, object]
    ) -> StandardResponse[str]:
        """Calculate the complete V2 execution configuration hash.

        Returns:
            Standard response containing the lowercase SHA-256 digest.
        """

        def calculate(value: Mapping[str, object]) -> str:
            material = dict(value)
            material.setdefault("contract_version", "v2")
            material.setdefault("schema_id", "simulation.backtest_request.v2")
            material.setdefault("market_evidence_eligible", False)
            material.setdefault("required_clock_edges", ())
            material.setdefault("evidenced_clock_edges", ())
            return _hash_material(material)

        return guard_operation(
            calculate,
            operation="simulation.run.simulation_backtest_request_v2.calculate_config_hash",
            risk_level="low",
            read_only=True,
        )(payload)

    @field_validator(
        "calculation_artifact_checksum",
        "calculation_model_hash",
        "execution_model_hash",
        "source_lineage_hash",
        "tick_lineage_hash",
        "initial_authority_state_hash",
    )
    @classmethod
    def _validate_identity_digest(cls, value: str) -> str:
        """Validate one lowercase SHA-256 execution-identity digest.

        Returns:
            Validated digest.

        Raises:
            ValueError: If the digest is malformed.
        """
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("execution identity hashes must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def _validate_execution_identity(self) -> Self:  # noqa: C901, PLR0912
        """Require ordered continuous matching provider revision coverage.

        Returns:
            Validated V2 request.

        Raises:
            ValueError: If execution identity or coverage is invalid.
        """
        if self.required_clock_edges != tuple(sorted(set(self.required_clock_edges))):
            raise ValueError("required clock edges must be ordered and unique")
        if self.evidenced_clock_edges != tuple(
            sorted(set(self.evidenced_clock_edges))
        ) or not set(self.evidenced_clock_edges).issubset(
            set(self.required_clock_edges)
        ):
            raise ValueError("evidenced clock edges must be an ordered required subset")
        if self.market_evidence_eligible and (
            self.market_evidence_class == "derived_bar_model"
            or self.evidenced_clock_edges != self.required_clock_edges
        ):
            raise ValueError("market evidence eligibility is not proven")
        revisions = self.provider_specification_revisions
        if not revisions:
            raise ValueError("provider specification revisions are required")
        identities = tuple(revision.revision_id for revision in revisions)
        if len(set(identities)) != len(identities):
            raise ValueError("provider specification revisions must be unique")
        ordered = tuple(
            sorted(
                revisions,
                key=lambda revision: (
                    revision.provider,
                    revision.server,
                    revision.environment,
                    revision.account_digest,
                    revision.symbol,
                    revision.effective_from,
                ),
            )
        )
        if revisions != ordered:
            raise ValueError("provider specification revisions must be canonical")
        for index, revision in enumerate(revisions):
            if revision.symbol != self.symbol:
                raise ValueError("provider revision symbol does not match request")
            if revision.environment != self.certification_target:
                raise ValueError(
                    "provider revision cannot be relabelled across targets"
                )
            if index and revisions[index - 1].effective_to != revision.effective_from:
                raise ValueError("provider revision coverage contains a gap or overlap")
        if revisions[0].effective_from > self.start:
            raise ValueError("provider revision coverage starts after the request")
        final_bound = revisions[-1].effective_to
        if final_bound is not None and final_bound < self.end:
            raise ValueError("provider revision coverage ends before the request")
        payload = self.model_dump(mode="python", warnings=False)
        if self.config_hash != _hash_material(payload):
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
    fx_evidence_versions: tuple[str, ...]
    fx_evidence_hashes: tuple[str, ...]
    execution_profile_version: str
    risk_policy_version: str
    seed: int
    initial_balance: Decimal
    runtime_profile: Literal["simulation"]
    execution_route: Literal["sim"]
    config_hash: str

    @classmethod
    def calculate_config_hash(
        cls, payload: Mapping[str, object]
    ) -> StandardResponse[str]:
        """Calculate portfolio request configuration identity.

        Args:
            payload: Full portfolio request projection.

        Returns:
            Lowercase SHA-256 digest.
        """
        logger.debug("Calculating PortfolioBacktestRequestV1 config hash")

        def calculate(value: Mapping[str, object]) -> str:
            material = dict(value)
            material.setdefault("contract_version", "v1")
            material.setdefault("schema_id", "simulation.portfolio_backtest_request.v1")
            return _hash_material(material)

        return guard_operation(
            calculate,
            operation="simulation.run.portfolio_backtest_request_v1.calculate_config_hash",
            risk_level="low",
            read_only=True,
        )(payload)

    def _validate_fx_bindings(self) -> None:
        """Validate ordered immutable FX evidence identities.

        Raises:
            ValueError: If FX bindings are incomplete or malformed.
        """
        sha256_hex_length = 64
        if not (
            len(self.fx_evidence_ids)
            == len(self.fx_evidence_versions)
            == len(self.fx_evidence_hashes)
        ):
            raise ValueError("Portfolio FX evidence bindings must align")
        if len(set(self.fx_evidence_ids)) != len(self.fx_evidence_ids):
            raise ValueError("Portfolio FX evidence IDs must be unique")
        if any(version != "v1" for version in self.fx_evidence_versions):
            raise ValueError("Portfolio FX evidence versions must be v1")
        if any(
            len(digest) != sha256_hex_length
            or digest != digest.lower()
            or any(character not in "0123456789abcdef" for character in digest)
            for digest in self.fx_evidence_hashes
        ):
            raise ValueError("Portfolio FX evidence hashes must be lowercase SHA-256")

    def _validate_component_allocations(self) -> None:
        """Validate component capital and currency allocations.

        Raises:
            ValueError: If a child request disagrees with its allocation.
        """
        for component in self.components:
            expected_balance = self.initial_balance * component.capital_weight
            child = component.backtest_request
            if (
                child.initial_balance != expected_balance
                or child.account_currency != self.base_currency
            ):
                raise ValueError(
                    "Portfolio component capital and currency must match allocation"
                )

    @model_validator(mode="after")
    def _validate_portfolio(self) -> PortfolioBacktestRequestV1:
        """Validate portfolio relationships and configuration identity.

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
        self._validate_fx_bindings()
        self._validate_component_allocations()
        payload = self.model_dump(mode="python", warnings=False)
        if self.config_hash != _hash_material(payload):
            raise ValueError("config_hash does not match portfolio material")
        return self


class SimulationRunDependencies(Protocol):
    """Typed receiver-owned composition seam for one Simulation run."""

    state_store: SimulationStateStore
    artifact_root: Path
    fast_research_enabled: bool

    def persist_audit_event(self, event: AuditEvent) -> StandardResponse[None]:
        """Persist one governed Simulation audit event through Data.

        Args:
            event: Bounded Utils-owned audit envelope.

        Raises:
            SimulationError: If durable persistence fails.
        """
        ...

    def load_market_data(
        self, request: SimulationBacktestRequestV1
    ) -> StandardResponse[MarketDataset]:
        """Load the immutable referenced Data dataset."""
        ...

    def generate_tick_series(
        self, dataset: MarketDataset, request: SimulationBacktestRequestV1
    ) -> StandardResponse[MarketDataset]:
        """Invoke Data's official real-evidence tick generator."""
        ...

    def calculate_indicators(
        self, dataset: MarketDataset, request: SimulationBacktestRequestV1
    ) -> StandardResponse[tuple[Any, ...]]:
        """Calculate point-in-time Indicator evidence."""
        ...

    def evaluate_strategy(
        self,
        dataset: MarketDataset,
        indicators: tuple[Any, ...],
        request: SimulationBacktestRequestV1,
    ) -> StandardResponse[tuple[create_trade_intent_value, ...]]:
        """Evaluate a registered Strategy against supplied evidence."""
        ...

    def review_risk(
        self,
        intents: tuple[create_trade_intent_value, ...],
        request: SimulationBacktestRequestV1,
    ) -> StandardResponse[tuple[RiskDecisionPackage, ...]]:
        """Review Strategy proposals under the referenced sim policy."""
        ...

    def build_order_intents(
        self,
        decisions: tuple[RiskDecisionPackage, ...],
        request: SimulationBacktestRequestV1,
    ) -> StandardResponse[tuple[OrderIntent, ...]]:
        """Pack approved Risk decisions through Trading's public boundary."""
        ...

    def build_approved_requests(
        self,
        intents: tuple[create_trade_intent_value, ...],
        decisions: tuple[RiskDecisionPackage, ...],
        request: SimulationBacktestRequestV2,
    ) -> StandardResponse[tuple[object, ...]]:
        """Invoke Trading's public approved-request builder for canonical v2 runs."""
        ...

    async def execute_trading_action(
        self,
        approved_request: object,
        engine: object,
        request: SimulationBacktestRequestV2,
    ) -> StandardResponse[object]:
        """Execute one approved request through a public Trading action."""
        ...

    async def execute_terminal_action(
        self,
        position: Mapping[str, object],
        engine: object,
        request: SimulationBacktestRequestV2,
    ) -> StandardResponse[object]:
        """Execute one Risk-authorized terminal close through Trading."""
        ...

    def load_initial_authority_state(
        self, request: SimulationBacktestRequestV2
    ) -> StandardResponse[Mapping[str, object]]:
        """Load one complete initial authority snapshot for both projections."""
        ...

    def load_account_activity(
        self, request: SimulationBacktestRequestV2
    ) -> StandardResponse[tuple[Mapping[str, object], ...]]:
        """Load complete ordered foreign/manual activity evidence."""
        ...

    def load_provider_specification_revisions(
        self, request: SimulationBacktestRequestV2
    ) -> StandardResponse[Mapping[str, object]]:
        """Load complete Data-owned effective provider revisions for the run."""
        ...

    async def evaluate_point_in_time_cycle(
        self,
        dataset: MarketDataset,
        decision_at: datetime,
        engine: object,
        request: SimulationBacktestRequestV2,
    ) -> StandardResponse[object]:
        """Invoke Trading's shared evaluation cycle at scheduler time."""
        ...

    def resolve_execution_profile(
        self, request: SimulationBacktestRequestV1
    ) -> StandardResponse[ExecutionProfile]:
        """Resolve the exact referenced execution profile."""
        ...

    def resolve_symbol_specification(
        self, request: SimulationBacktestRequestV1
    ) -> StandardResponse[SymbolSpecification]:
        """Resolve approved symbol constraints."""
        ...

    def resolve_cost_model(
        self, request: SimulationBacktestRequestV1
    ) -> StandardResponse[ExecutionCostModel]:
        """Resolve the exact referenced cost model."""
        ...

    def resolve_fx_evidence(
        self, evidence_ids: tuple[str, ...]
    ) -> StandardResponse[Mapping[str, FXConversionEvidence]]:
        """Resolve one Data-owned FXConversionEvidence v1 per identifier.

        Simulation validates freshness through `validate_fx_evidence()` and
        never selects, refreshes, or synthesizes a rate. An identifier the
        caller cannot resolve fails the run closed.
        """
        ...


__all__ = [
    "PortfolioBacktestRequestV1",
    "PortfolioComponentRequest",
    "SimulationBacktestRequestV1",
    "SimulationBacktestRequestV2",
    "SimulationRunDependencies",
]

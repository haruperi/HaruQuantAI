"""Versioned contracts for the Optimization execution boundary."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.analytics import PerformanceReport  # noqa: TC001
from app.services.optimization.parameters import ParameterValue  # noqa: TC001
from app.utils import logger

_SHA256_HEX_LENGTH = 64


class BacktestExecutionContext(BaseModel):
    """Invariant provenance required to package a Simulation request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

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
    initial_balance: Decimal
    account_currency: str
    runtime_profile: str
    canonical: bool
    cost_model_hash: str
    realism_hash: str
    objective_hash: str
    engine_type: str
    engine_version: str
    module_version: str

    @model_validator(mode="after")
    def _validate_context(self) -> BacktestExecutionContext:
        """Validate complete immutable execution provenance.

        Returns:
            Validated execution context.

        Raises:
            ValueError: If provenance, time, or runtime policy is invalid.
        """
        logger.debug("Validating Optimization backtest execution context")
        text_fields = (
            self.strategy_id,
            self.strategy_version,
            self.strategy_config_ref,
            self.data_ref,
            self.data_version,
            self.tick_generation_ref,
            self.tick_generation_version,
            self.execution_profile_ref,
            self.execution_profile_version,
            self.risk_policy_ref,
            self.risk_policy_version,
            self.symbol,
            self.timeframe,
            self.account_currency,
            self.engine_type,
            self.engine_version,
            self.module_version,
        )
        if any(not value or value != value.strip() for value in text_fields):
            raise ValueError("execution context text fields must be non-empty")
        hashes = (
            self.strategy_config_hash,
            self.data_hash,
            self.tick_generation_hash,
            self.execution_profile_hash,
            self.risk_policy_hash,
            self.cost_model_hash,
            self.realism_hash,
            self.objective_hash,
        )
        if any(
            len(value) != _SHA256_HEX_LENGTH
            or any(character not in "0123456789abcdef" for character in value)
            for value in hashes
        ):
            raise ValueError("execution context hashes must be SHA-256 digests")
        start_offset = self.start.utcoffset()
        end_offset = self.end.utcoffset()
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("execution times must be timezone-aware")
        if start_offset != end_offset or start_offset is None:
            raise ValueError("execution times must use one UTC offset")
        if start_offset.total_seconds() != 0 or self.end <= self.start:
            raise ValueError("execution window must be ordered UTC")
        if not self.initial_balance.is_finite() or self.initial_balance <= 0:
            raise ValueError("initial balance must be finite and positive")
        if self.runtime_profile not in {"simulation", "fast_research"}:
            raise ValueError("runtime profile is unsupported")
        if self.canonical != (self.runtime_profile == "simulation"):
            raise ValueError("canonical policy conflicts with runtime profile")
        return self


class BacktestExecutionRequest(BaseModel):
    """One candidate request for the Optimization-owned adapter."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: str = "v1"
    candidate_hash: str
    executable_parameters: Mapping[str, ParameterValue]
    seed: int
    request_id: str
    workflow_id: str
    correlation_id: str
    context: BacktestExecutionContext

    @field_validator("candidate_hash")
    @classmethod
    def _validate_candidate_hash(cls, value: str) -> str:
        """Validate candidate identity.

        Args:
            value: Candidate digest.

        Returns:
            Validated SHA-256 digest.

        Raises:
            ValueError: If the digest is malformed.
        """
        logger.debug("Validating Optimization execution candidate hash")
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("candidate_hash must be a SHA-256 digest")
        return value


class EngineOptimizationResult(BaseModel):
    """Optimization-facing completed Simulation and Analytics evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    candidate_hash: str
    simulation_run_id: str
    simulation_request_hash: str
    analytics_report: PerformanceReport
    runtime_ms: float
    engine_type: str
    engine_version: str

    @model_validator(mode="after")
    def _validate_result(self) -> EngineOptimizationResult:
        """Validate result identity and runtime evidence.

        Returns:
            Validated engine result.

        Raises:
            ValueError: If identity or runtime evidence is invalid.
        """
        logger.debug("Validating Optimization engine result")
        if (
            len(self.candidate_hash) != _SHA256_HEX_LENGTH
            or len(self.simulation_request_hash) != _SHA256_HEX_LENGTH
        ):
            raise ValueError("engine result hashes are malformed")
        if (
            not self.simulation_run_id
            or not self.engine_type
            or not self.engine_version
        ):
            raise ValueError("engine result identity is incomplete")
        if not math.isfinite(self.runtime_ms) or self.runtime_ms < 0:
            raise ValueError("engine result runtime must be finite and non-negative")
        return self


class BacktestExecutionAdapter(Protocol):
    """Receiver-owned synchronous candidate execution port."""

    contract_version: str
    engine_type: str
    engine_version: str
    deterministic: bool

    def execute(
        self,
        request: BacktestExecutionRequest,  # noqa: ARG002
    ) -> EngineOptimizationResult:
        """Execute one candidate and return measured evidence.

        Args:
            request: Complete candidate execution request.

        Raises:
            NotImplementedError: Protocol declarations are not executable.
        """
        logger.debug("Declaring Optimization backtest adapter execution")
        raise NotImplementedError


__all__ = [
    "BacktestExecutionAdapter",
    "BacktestExecutionContext",
    "BacktestExecutionRequest",
    "EngineOptimizationResult",
]

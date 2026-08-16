"""Immutable execution-realism contracts."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LatencyProfile(BaseModel):
    """Explicit non-negative latency for each simulation time domain."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    market_ms: Decimal = Decimal(0)
    client_ms: Decimal = Decimal(0)
    network_ms: Decimal = Decimal(0)
    broker_ms: Decimal = Decimal(0)
    venue_ms: Decimal = Decimal(0)
    report_ms: Decimal = Decimal(0)
    processing_ms: Decimal = Decimal(0)

    @field_validator("*")
    @classmethod
    def _validate_latency(cls, value: Decimal) -> Decimal:
        """Require finite non-negative millisecond latency."""
        if not value.is_finite() or value < 0:
            raise ValueError("latency must be finite and non-negative")
        return value


class QueueModel(BaseModel):
    """Price-level queue state used to determine bounded fills."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    price: Decimal
    order_quantity: Decimal = Field(gt=0)
    quantity_ahead: Decimal = Field(ge=0)
    cancellation_rate: Decimal = Field(ge=0, le=1)
    maximum_fill_probability: Decimal = Field(gt=0, le=1)

    @field_validator("price", "order_quantity", "quantity_ahead")
    @classmethod
    def _validate_decimal(cls, value: Decimal) -> Decimal:
        """Require finite queue quantities and price."""
        if not value.is_finite():
            raise ValueError("queue values must be finite")
        return value


class QueueFillResult(BaseModel):
    """Deterministic queue fill projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    filled_quantity: Decimal = Field(ge=0)
    remaining_quantity: Decimal = Field(ge=0)
    remaining_ahead: Decimal = Field(ge=0)
    fill_probability: Decimal = Field(ge=0, le=1)


class RealisticExecutionResult(BaseModel):
    """Price result after explicit slippage and market impact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_price: Decimal
    slippage_points: Decimal = Field(ge=0)
    impact_points: Decimal = Field(ge=0)
    total_latency_ms: Decimal = Field(ge=0)


@dataclass(frozen=True, slots=True, kw_only=True)
class _CalibratedRealism:
    """Private admitted calibration and applicability projection."""

    artifact_checksum: str
    component: str
    environment: str
    symbol: str
    parameters: Mapping[str, str]
    exclusions: tuple[str, ...]
    canonical: bool


def build_latency_profile(**fields: object) -> LatencyProfile:
    """Build one validated latency profile."""
    return LatencyProfile.model_validate(fields)


def build_queue_model(**fields: object) -> QueueModel:
    """Build one validated queue model."""
    return QueueModel.model_validate(fields)


__all__ = [
    "LatencyProfile",
    "QueueFillResult",
    "QueueModel",
    "RealisticExecutionResult",
    "build_latency_profile",
    "build_queue_model",
]

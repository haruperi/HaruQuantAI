"""Private immutable contracts for governed calibration evidence."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from app.utils import canonical_digest

_COMPONENTS = frozenset(
    {"latency", "slippage", "queue_position", "partial_fill", "requote", "fault"}
)
_SHA256_LENGTH = 64
_MAX_TEXT_LENGTH = 256


def _utc(value: datetime, name: str) -> datetime:
    """Require an aware UTC timestamp."""
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{name} must be aware UTC"
        raise ValueError(message)
    return value


def _digest(value: str, name: str) -> str:
    """Require a lowercase SHA-256 digest."""
    if len(value) != _SHA256_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        message = f"{name} must be a lowercase SHA-256 digest"
        raise ValueError(message)
    return value


def _text(value: str, name: str) -> str:
    """Require bounded non-empty trimmed text."""
    if not value or value != value.strip() or len(value) > _MAX_TEXT_LENGTH:
        message = f"{name} must be bounded trimmed text"
        raise ValueError(message)
    return value


@dataclass(frozen=True, slots=True, kw_only=True)
class _EvidenceRecord:
    """One sanitized point-in-time calibration observation."""

    evidence_id: str
    component: str
    value: Decimal
    unit: str
    economic_at: datetime
    available_at: datetime
    ingested_at: datetime
    source_checksum: str
    broker: str
    server: str
    account_digest: str
    environment: Literal["demo", "live"]
    symbol: str
    regime: Literal["scheduled_event", "ordinary"]

    def __post_init__(self) -> None:
        """Validate identity, value, and temporal provenance."""
        _text(self.evidence_id, "evidence_id")
        if self.component != "spread" and self.component not in _COMPONENTS:
            raise ValueError("component is unsupported")
        if not self.value.is_finite() or self.value < 0:
            raise ValueError("evidence value must be finite and non-negative")
        _text(self.unit, "unit")
        _digest(self.source_checksum, "source_checksum")
        _text(self.broker, "broker")
        _text(self.server, "server")
        _digest(self.account_digest, "account_digest")
        _text(self.symbol, "symbol")
        _utc(self.economic_at, "economic_at")
        _utc(self.available_at, "available_at")
        _utc(self.ingested_at, "ingested_at")
        if self.economic_at > self.available_at or self.available_at > self.ingested_at:
            raise ValueError("evidence temporal order is invalid")


@dataclass(frozen=True, slots=True, kw_only=True)
class _Partition:
    """Immutable evidence partition with a canonical content hash."""

    name: Literal["calibration", "validation", "certification"]
    records: tuple[_EvidenceRecord, ...]
    checksum: str


@dataclass(frozen=True, slots=True, kw_only=True)
class _PartitionBundle:
    """Disjoint pre-fit partition bundle."""

    selection_rule: str
    retrospective: bool
    calibration: _Partition
    validation: _Partition
    certification: _Partition


@dataclass(frozen=True, slots=True, kw_only=True)
class _CalibrationArtifact:
    """Versioned immutable empirical calibration artifact."""

    schema_id: Literal["simulator.calibration.v1"]
    artifact_id: str
    broker: str
    server: str
    account_digest: str
    environment: Literal["demo", "live"]
    symbol: str
    source_identity: str
    source_available_at: datetime
    ingested_at: datetime
    calibrated_at: datetime
    training_start: datetime
    training_end: datetime
    effective_from: datetime
    effective_to: datetime
    retrospective: bool
    partition_hashes: Mapping[str, str]
    selection_rule: str
    component: str
    regime: str
    sample_count: int
    minimum_samples: int
    minimum_coverage: Decimal
    observed_coverage: Decimal
    parameters: Mapping[str, str]
    applicability: Mapping[str, str]
    exclusions: tuple[str, ...]
    threshold_metric: str
    threshold_unit: str
    threshold_test: str
    threshold_tolerance: Decimal
    confidence: Decimal
    economic_error_budget: Decimal
    valid_until: datetime
    estimator_version: str
    checksum: str


def record_material(record: _EvidenceRecord) -> Mapping[str, object]:
    """Return canonical material for one evidence record."""
    return {
        "evidence_id": record.evidence_id,
        "component": record.component,
        "value": str(record.value),
        "unit": record.unit,
        "economic_at": record.economic_at.isoformat(),
        "available_at": record.available_at.isoformat(),
        "ingested_at": record.ingested_at.isoformat(),
        "source_checksum": record.source_checksum,
        "broker": record.broker,
        "server": record.server,
        "account_digest": record.account_digest,
        "environment": record.environment,
        "symbol": record.symbol,
        "regime": record.regime,
    }


def partition_hash(name: str, records: tuple[_EvidenceRecord, ...]) -> str:
    """Return the canonical content hash for one named partition."""
    return canonical_digest(
        {"name": name, "records": tuple(map(record_material, records))}
    )


def freeze_mapping(value: Mapping[str, str]) -> Mapping[str, str]:
    """Return a sorted immutable defensive mapping copy."""
    return MappingProxyType(dict(sorted(value.items())))


__all__ = []

"""Configuration model for Economic Calendar and News Evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EconomicNewsEvidenceConfig:
    """Configuration for economic news observation, revision, and query governance."""

    database_path: Path | str = ":memory:"
    max_query_results: int = 10_000
    default_rate_limit_per_minute: int = 60
    max_payload_size_bytes: int = 5_000_000
    default_freshness_limit_seconds: int = 86_400
    allowed_sources: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"FOREX_FACTORY", "FAIR_ECONOMY", "TEST_SOURCE", "REUTERS", "BLOOMBERG"}
        )
    )

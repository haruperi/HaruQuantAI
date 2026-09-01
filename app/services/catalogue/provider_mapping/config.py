"""Configuration dataclass for Provider and Broker Mapping."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProviderMappingConfig:
    """Configuration options for Provider and Broker Mapping."""

    database_path: str | Path | None = None
    auto_migrate: bool = True

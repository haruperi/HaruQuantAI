"""Configuration dataclass for Instrument Catalogue."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class InstrumentCatalogueConfig:
    """Configuration options for Instrument Catalogue."""

    database_path: str | Path | None = None
    auto_migrate: bool = True

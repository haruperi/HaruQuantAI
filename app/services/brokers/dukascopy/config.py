"""Configuration dataclass for Dukascopy broker connection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DukascopyConfig:
    """Dukascopy feature configuration options."""

    database_path: Path | str = "data/database/haruquantai.db"
    username: str | None = None
    password: str | None = None
    account_id: str | None = None
    live: bool = False
    timeout: int = 30

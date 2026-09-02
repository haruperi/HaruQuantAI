"""Configuration dataclass for cTrader broker connection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CTraderConfig:
    """cTrader feature configuration options."""

    database_path: Path | str = "data/database/haruquantai.db"
    client_id: str | None = None
    client_secret: str | None = None
    access_token: str | None = None
    account_id: str | None = None
    live: bool = False
    timeout: int = 30

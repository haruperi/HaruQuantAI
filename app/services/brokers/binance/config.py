"""Configuration dataclass for Binance broker connection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BinanceConfig:
    """Binance feature configuration options."""

    database_path: Path | str = "data/database/haruquantai.db"
    api_key: str | None = None
    api_secret: str | None = None
    testnet: bool = False
    timeout: int = 30

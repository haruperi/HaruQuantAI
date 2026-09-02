"""Configuration dataclass for Yahoo Finance provider."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class YahooConfig:
    """Yahoo Finance feature configuration options."""

    database_path: Path | str = "data/database/haruquantai.db"
    timeout: int = 30

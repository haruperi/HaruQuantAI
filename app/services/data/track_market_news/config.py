"""Strict configuration for point-in-time market-news tracking."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_DEFAULT_DATABASE_PATH = Path(".haruquant") / "data-market-news.sqlite3"
_ALLOWED_KEYS = frozenset({"database_path"})


@dataclass(frozen=True, slots=True)
class TrackMarketNewsConfig:
    """Trusted configuration for market-news evidence persistence."""

    database_path: Path = _DEFAULT_DATABASE_PATH

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> TrackMarketNewsConfig:
        """Validate and normalize raw feature configuration."""
        unknown = set(values) - _ALLOWED_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        raw = values.get("database_path", str(_DEFAULT_DATABASE_PATH))
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("database_path must be a non-empty string")
        return cls(database_path=Path(raw).expanduser())

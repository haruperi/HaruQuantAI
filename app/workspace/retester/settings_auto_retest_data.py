"""Auto Retest Data settings and source override resolution.

Description:
    Provides AutoRetestDataSettings and SettingsAutoRetestDataService to configure
    whether retesting uses strategy-embedded market parameters or custom overrides,
    normalizing legacy boolean string flags via RetestValueSource.

Purpose:
    FEAT-RETESTER-DATA-SETTINGS: Market and symbol resolution for retest runs.

Key Capabilities:
    - FR-retest-auto-data-settings: Configure symbol, timeframe, date range,
      spread, precision, and capital sources.
    - FR-retest-auto-data-normalize: Normalize legacy flags and validate bounds.

Python API Usage:
    from app.workspace.retester.settings_auto_retest_data import (
        AutoRetestDataSettings,
        SettingsAutoRetestDataService,
    )
    settings = SettingsAutoRetestDataService.from_raw(
        {"symbol_source": "false", "symbol": "GBPUSD"}
    )

CLI Usage:
    python -m app.cli retest auto-data-settings --symbol EURUSD --timeframe H1
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.retester.value_source import RetestValueSource

logger = get_logger(__name__)

SourceType = Literal["strategy", "custom"]


@dataclass(frozen=True, slots=True)
class AutoRetestDataSettings:
    """Controls whether retesting uses strategy properties or custom overrides."""

    symbol_source: SourceType = "strategy"
    symbol: str = "EURUSD"
    timeframe_source: SourceType = "strategy"
    timeframe: str = "H1"
    date_range_source: SourceType = "strategy"
    start_date: str = "2010-01-01"
    end_date: str = "2025-01-01"
    spread_source: SourceType = "strategy"
    spread_pips: float = 1.0
    precision_source: SourceType = "strategy"
    precision: str = "SelectedTimeframeOnly"
    initial_capital: float = 10000.0

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary representation."""
        return {
            "symbol_source": self.symbol_source,
            "symbol": self.symbol,
            "timeframe_source": self.timeframe_source,
            "timeframe": self.timeframe,
            "date_range_source": self.date_range_source,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "spread_source": self.spread_source,
            "spread_pips": self.spread_pips,
            "precision_source": self.precision_source,
            "precision": self.precision,
            "initial_capital": self.initial_capital,
        }


class SettingsAutoRetestDataService:
    """Service to parse, normalize, and resolve retest data settings."""

    @staticmethod
    def _normalize_source(raw_val: Any, default: SourceType = "strategy") -> SourceType:
        if raw_val is None:
            return default
        normalized = RetestValueSource.normalize(
            str(raw_val).lower() if isinstance(raw_val, bool) else str(raw_val)
        )
        if normalized in ("strategy", "custom"):
            return normalized  # type: ignore[return-value]
        return default

    @classmethod
    def from_raw(cls, payload: Mapping[str, Any]) -> AutoRetestDataSettings:
        """Construct AutoRetestDataSettings from raw payload with legacy normalization.

        Args:
            payload: Mapping containing configuration keys.

        Returns:
            Validated AutoRetestDataSettings instance.

        Raises:
            DomainError: If spread_pips < 0.0 or initial_capital <= 0.0.
        """
        symbol_src = cls._normalize_source(payload.get("symbol_source"), "strategy")
        timeframe_src = cls._normalize_source(
            payload.get("timeframe_source"), "strategy"
        )
        date_src = cls._normalize_source(payload.get("date_range_source"), "strategy")
        spread_src = cls._normalize_source(payload.get("spread_source"), "strategy")
        precision_src = cls._normalize_source(
            payload.get("precision_source"), "strategy"
        )

        spread_pips = float(payload.get("spread_pips", 1.0))
        initial_capital = float(payload.get("initial_capital", 10000.0))

        if spread_pips < 0.0 or initial_capital <= 0.0:
            logger.error(
                "FR-retest-auto-data-normalize: invalid data bounds: "
                "spread=%.2f, capital=%.2f",
                spread_pips,
                initial_capital,
            )
            raise DomainError(
                code="RETESTER_INVALID_DATA_SETTINGS",
                message=(
                    f"Invalid data bounds: spread_pips={spread_pips}, "
                    f"initial_capital={initial_capital}"
                ),
            )

        logger.info(
            "FR-retest-auto-data-normalize: created data settings: "
            "symbol=%s (%s), timeframe=%s (%s)",
            payload.get("symbol", "EURUSD"),
            symbol_src,
            payload.get("timeframe", "H1"),
            timeframe_src,
        )

        return AutoRetestDataSettings(
            symbol_source=symbol_src,
            symbol=str(payload.get("symbol", "EURUSD")),
            timeframe_source=timeframe_src,
            timeframe=str(payload.get("timeframe", "H1")),
            date_range_source=date_src,
            start_date=str(payload.get("start_date", "2010-01-01")),
            end_date=str(payload.get("end_date", "2025-01-01")),
            spread_source=spread_src,
            spread_pips=spread_pips,
            precision_source=precision_src,
            precision=str(payload.get("precision", "SelectedTimeframeOnly")),
            initial_capital=initial_capital,
        )

"""Monte Carlo Retest base classes, contracts, and data structures.

Description:
    Provides the foundational MonteCarloRetest abstract base class, test types,
    tick event abstractions, settings mapping, and perturbation contracts
    matching StrategyQuant donor snippets.

Purpose:
    FEAT-RETESTER-MC-RETEST: Monte Carlo retest base contracts.

Key Capabilities:
    - FR-mc-retest-core: Core retest perturbation abstractions and models.

Python API Usage:
    from app.extend.monte_carlo.retest.base import (
        MonteCarloRetest,
        MonteCarloTestTypes,
        SettingsMap,
        TickEvent,
    )

CLI Usage:
    python -m app.cli retest mc-perturb --list
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.core.trading.strategy.hsl.models import HSLStrategyDocument

logger = get_logger(__name__)


class MonteCarloTestTypes:
    """Retest perturbation target categories matching donor types."""

    ModifyData: int = 1
    ModifySettings: int = 2


@dataclass
class TickEvent:
    """Individual price tick event with Bid/Ask and timestamp."""

    time_ms: int = 0
    ask: float = 0.0
    bid: float = 0.0
    volume: float = 0.0

    def get_time(self) -> int:
        """Return tick timestamp in milliseconds."""
        return self.time_ms

    def getTime(self) -> int:  # noqa: N802
        """Donor compatibility alias for get_time."""
        return self.get_time()

    def get_ask(self) -> float:
        """Return tick ask price."""
        return self.ask

    def getAsk(self) -> float:  # noqa: N802
        """Donor compatibility alias for get_ask."""
        return self.get_ask()

    def get_bid(self) -> float:
        """Return tick bid price."""
        return self.bid

    def getBid(self) -> float:  # noqa: N802
        """Donor compatibility alias for get_bid."""
        return self.get_bid()

    def set_ask(self, val: float) -> None:
        """Set tick ask price."""
        self.ask = val

    def setAsk(self, val: float) -> None:  # noqa: N802
        """Donor compatibility alias for set_ask."""
        self.set_ask(val)

    def set_bid(self, val: float) -> None:
        """Set tick bid price."""
        self.bid = val

    def setBid(self, val: float) -> None:  # noqa: N802
        """Donor compatibility alias for set_bid."""
        self.set_bid(val)


@dataclass
class SettingsMap:
    """Key-value settings mapping container matching donor SettingsMap."""

    _values: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value for key."""
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store configuration value under key."""
        self._values[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert settings map to standard dictionary."""
        return dict(self._values)


class MonteCarloRetest:
    """Abstract base class for all Monte Carlo retest perturbations."""

    def __init__(self, test_type: int, name: str = "MonteCarloRetest") -> None:
        self.test_type: int = test_type
        self.name: str = name
        logger.info(
            "FR-mc-retest-core: initialized %s (type=%d)", self.name, self.test_type
        )

    def modify_data(
        self, rng: random.Random, tick_event: TickEvent, global_atr: float
    ) -> None:
        """Modify tick price event data in-place."""

    def modifyData(  # noqa: N802
        self, rng: random.Random, tick_event: TickEvent, global_atr: float
    ) -> None:
        """Donor compatibility alias for modify_data."""
        self.modify_data(rng, tick_event, global_atr)

    def modify_ohlc_bars(
        self, rng: random.Random, bars: tuple[MarketBar, ...], global_atr: float
    ) -> tuple[MarketBar, ...]:
        """Modify OHLC bars sequence and return perturbed bars."""
        del rng, global_atr
        return bars

    def modify_settings(self, rng: random.Random, settings: SettingsMap) -> None:
        """Modify backtest simulation settings map in-place."""

    def modifySettings(  # noqa: N802
        self, rng: random.Random, settings: SettingsMap
    ) -> None:
        """Donor compatibility alias for modify_settings."""
        self.modify_settings(rng, settings)

    def apply_to_strategy(
        self,
        strategy: HSLStrategyDocument,
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> HSLStrategyDocument:
        """Perturb strategy parameters and return modified HSLStrategyDocument."""
        del rng, params
        return strategy

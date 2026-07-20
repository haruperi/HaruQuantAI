"""Canonical portfolio state for risk processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.risk.domain.account import AccountState
from app.services.risk.domain.market import MarketState
from app.services.risk.domain.position import PositionState
from app.services.risk.domain.symbol import SymbolState
from app.services.risk.limits import RiskLimits
from app.services.risk.validators.common import ValidationSummary


@dataclass(frozen=True)
class PortfolioState:
    """Validated point-in-time portfolio snapshot used by risk modules."""

    account: AccountState
    positions: list[PositionState]
    symbols: dict[str, SymbolState]
    markets: dict[str, MarketState]
    limits: RiskLimits | None = None
    symbol_to_cluster: dict[str, str] = field(default_factory=dict)
    symbol_to_clusters: dict[str, list[str]] = field(default_factory=dict)
    validation_summary: ValidationSummary = field(default_factory=ValidationSummary)
    exposures: dict[str, float] = field(default_factory=dict)
    as_of: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def active_symbols(self) -> list[str]:
        return [position.symbol for position in self.positions]

    @property
    def position_map(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for position in self.positions:
            symbol = str(position.symbol)
            totals[symbol] = float(totals.get(symbol, 0.0) + float(position.lots))
        return totals

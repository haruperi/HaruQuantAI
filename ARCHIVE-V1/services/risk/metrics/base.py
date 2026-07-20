"""Base contracts for normalized risk metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.services.risk.limits import GovernanceState, LimitEvent
from app.services.risk.models import PortfolioState
from app.services.risk.regimes.models import RegimeReport, RegimeState


@dataclass(frozen=True)
class MetricRow:
    """One normalized metric row suitable for later persistence."""

    family: str
    metric_key: str
    scope: str
    scope_key: str | None = None
    numeric_value: float | None = None
    text_value: str | None = None
    unit: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricContext:
    """Execution context for one metric registry run."""

    state: PortfolioState
    shared: dict[str, Any] = field(default_factory=dict)


class MetricFamily(Protocol):
    """Family-level metric calculator contract."""

    family_name: str

    def compute(self, context: MetricContext) -> list[MetricRow]:
        """Compute normalized metric rows for this family."""


@dataclass(frozen=True)
class RiskSnapshot:
    """Current-state risk snapshot built from normalized metric rows."""

    state: PortfolioState
    metric_rows: list[MetricRow]
    summary: dict[str, Any] = field(default_factory=dict)
    governance_state: GovernanceState | None = None
    policy_events: list[LimitEvent] = field(default_factory=list)
    regime_state: RegimeState | None = None
    regime_report: RegimeReport | None = None

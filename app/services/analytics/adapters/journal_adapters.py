"""Simulation-journal and live-journal analytics adapters (ANL-NFR-449).

Converts execution journals containing Phase 1.5 event contracts into the canonical
TradingResult. Prohibits reading raw broker SDK DTOs (ANL-NFR-450).
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.services.analytics.contracts.models import Lineage, TradingResult
from app.services.trading.contracts import ExecutionReport, Fill, TradeResult
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.analytics.contracts.audit import AuditEvent
    from app.services.analytics.contracts.portfolio import PortfolioSnapshot
    from app.services.risk.contracts import RiskDecision
    from app.services.simulator.contracts import BacktestResult


@dataclass(frozen=True, slots=True)
class SimulationJournal:
    """Simulation execution journal container structure (ANL-NFR-449)."""

    run_id: str
    config_hash: str
    journal_ref: str
    events: tuple[
        TradeResult
        | ExecutionReport
        | Fill
        | PortfolioSnapshot
        | BacktestResult
        | RiskDecision
        | AuditEvent
        | dict[str, Any],
        ...,
    ] = ()
    equity_curve: tuple[dict[str, Any], ...] = ()
    strategy_id: str = "unknown"
    dataset_hash: str = "unknown"
    cost_model: str = "unknown"
    fill_model: str = "unknown"
    risk_policy_version: str = "unknown"


@dataclass(frozen=True, slots=True)
class LiveTradeJournal:
    """Live execution journal container structure (ANL-NFR-449)."""

    session_id: str
    events: tuple[
        TradeResult
        | ExecutionReport
        | Fill
        | PortfolioSnapshot
        | RiskDecision
        | AuditEvent
        | dict[str, Any],
        ...,
    ] = ()
    equity_curve: tuple[dict[str, Any], ...] = ()
    strategy_id: str = "unknown"
    dataset_hash: str = "unknown"
    cost_model: str = "unknown"
    fill_model: str = "unknown"
    risk_policy_version: str = "unknown"


def _extract_trades_from_events(events: tuple[Any, ...]) -> tuple[dict[str, Any], ...]:
    """Helper to extract closed trades from event stream.

    Args:
        events (tuple[Any, ...]): Input parameter `events`.

    Returns:
        Calculated tuple[dict[str, Any], ...] value.
    """
    logger.debug("_extract_trades_from_events: executed.")
    trades_list = []
    for event in events:
        if isinstance(event, TradeResult):
            trades_list.append(event.model_dump())
        elif isinstance(event, dict) and event.get("trade_id"):
            trades_list.append(event)
    return tuple(trades_list)


def from_simulation_journal(journal: SimulationJournal) -> TradingResult:
    """Convert a SimulationJournal into a canonical TradingResult (ANL-NFR-449).

    Args:
        journal (SimulationJournal): Input parameter `journal`.

    Returns:
        Calculated TradingResult value.
    """
    logger.debug("from_simulation_journal: executed.")
    trades = _extract_trades_from_events(journal.events)

    lineage = Lineage(
        run_id=journal.run_id,
        strategy_id=journal.strategy_id,
        dataset_hash=journal.dataset_hash,
        cost_model=journal.cost_model,
        fill_model=journal.fill_model,
        risk_policy_version=journal.risk_policy_version,
        journal_reference=journal.journal_ref,
    )

    return TradingResult(
        schema_version="1.3.1",
        result_id=journal.run_id,
        environment="simulation",
        account_base_currency="USD",
        trades=trades,
        equity_curve=journal.equity_curve,
        benchmark=None,
        lineage=lineage,
    )


def from_live_trade_journal(journal: LiveTradeJournal) -> TradingResult:
    """Convert a LiveTradeJournal into a canonical TradingResult (ANL-NFR-449).

    Args:
        journal (LiveTradeJournal): Input parameter `journal`.

    Returns:
        Calculated TradingResult value.
    """
    logger.debug("from_live_trade_journal: executed.")
    trades = _extract_trades_from_events(journal.events)

    lineage = Lineage(
        run_id=journal.session_id,
        strategy_id=journal.strategy_id,
        dataset_hash=journal.dataset_hash,
        cost_model=journal.cost_model,
        fill_model=journal.fill_model,
        risk_policy_version=journal.risk_policy_version,
        journal_reference=journal.session_id,
    )

    return TradingResult(
        schema_version="1.3.1",
        result_id=journal.session_id,
        environment="live",
        account_base_currency="USD",
        trades=trades,
        equity_curve=journal.equity_curve,
        benchmark=None,
        lineage=lineage,
    )

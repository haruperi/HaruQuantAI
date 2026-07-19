"""Unit tests for Simulation reporting contracts."""
# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.simulator.reporting import (
    AccountingSummary,
    ArtifactEntry,
    ClosedTradeRecord,
    PortfolioSimulationResult,
    RealismDisclosure,
    SimulationResult,
)
from pydantic import ValidationError


def _accounting() -> AccountingSummary:
    """Build exact completed accounting totals."""
    return AccountingSummary(
        final_balance=Decimal(10_010),
        final_equity=Decimal(10_010),
        used_margin=Decimal(0),
        free_margin=Decimal(10_010),
        gross_profit=Decimal(12),
        commission=Decimal(-2),
        swap=Decimal(0),
        net_profit=Decimal(10),
    )


def _realism() -> RealismDisclosure:
    """Build explicit execution realism disclosures."""
    return RealismDisclosure(
        tick_model="real",
        slippage_model="none",
        liquidity_model="unbounded",
        session_model="explicit_utc",
        data_quality="passed",
        assumptions=("Bid and ask are provider evidence.",),
        limitations=("No queue-position model.",),
    )


def _closed_trade() -> ClosedTradeRecord:
    """Build one completed closed-trade ledger record."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    return ClosedTradeRecord(
        ticket="ticket-1",
        symbol="EURUSD",
        type="BUY",
        volume=Decimal(1),
        entry_time=instant,
        entry_price=Decimal("1.1"),
        stop_loss=None,
        take_profit=None,
        exit_time=instant + timedelta(hours=1),
        exit_price=Decimal("1.2"),
        comment="simulated",
        commission=Decimal(-2),
        swap=Decimal(0),
        profit=Decimal(100),
        magic="strategy-v1",
        mae=Decimal(-10),
        mfe=Decimal(120),
    )


def _result() -> SimulationResult:
    """Build one completed canonical result."""
    return SimulationResult(
        run_id="run-result",
        request_hash="a" * 64,
        config_hash="b" * 64,
        data_hash="c" * 64,
        engine_version="v1",
        status="completed",
        journal_ref="journal.jsonl",
        artifact_manifest_ref="manifest.json",
        fills=(),
        closed_trades=(_closed_trade(),),
        initial_balance=Decimal(10_000),
        account_currency="USD",
        accounting=_accounting(),
        diagnostics=(),
        realism=_realism(),
    )


def test_result_rejects_incomplete_status() -> None:
    """Reject publication before canonical completion."""
    payload = _result().model_dump(mode="python") | {"status": "running"}
    with pytest.raises(ValidationError, match="completed"):
        SimulationResult.model_validate(payload)


def test_closed_trade_profit_is_gross() -> None:
    """Keep gross price profit separate from signed costs."""
    record = _closed_trade()
    assert record.profit == Decimal(100)
    assert record.commission == Decimal(-2)


def test_manifest_rejects_unsafe_path() -> None:
    """Reject traversal outside the canonical artifact set."""
    with pytest.raises(ValidationError, match="relative"):
        ArtifactEntry(
            relative_path="../result.json",
            media_type="application/json",
            size_bytes=1,
            sha256="a" * 64,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        )


def test_portfolio_result_requires_all_components() -> None:
    """Reject empty component and return evidence."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    with pytest.raises(ValidationError, match="component"):
        PortfolioSimulationResult(
            result_id="result",
            run_id="run",
            request_hash="a" * 64,
            config_hash="b" * 64,
            data_hash="c" * 64,
            result_hash="d" * 64,
            engine_version="v1",
            status="completed",
            portfolio_id="portfolio",
            construction_result_id="construction",
            construction_version="v1",
            measurement_start=instant,
            measurement_end=instant + timedelta(days=30),
            base_currency="USD",
            component_results=(),
            component_return_series=(),
            aggregate_journal_ref="journal.jsonl",
            aggregate_metrics_ref="metrics.json",
            risk_budget_history=(),
            fx_evidence_ids=("fx-1",),
            artifact_manifest_ref="manifest.json",
        )

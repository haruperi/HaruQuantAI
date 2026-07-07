"""Unit tests for the trading result adapters, canonicalization, and protocols."""

from __future__ import annotations

from typing import Any

import pytest
from app.services.analytics.adapters import (
    LiveTradeJournal,
    SimulationJournal,
    from_live_trade_journal,
    from_simulation_journal,
    to_canonical,
    to_trading_result,
    validate_adapter_contract,
)
from app.services.analytics.contracts.models import (
    BenchmarkData,
    Lineage,
    TradingResult,
)
from app.services.contracts.trading import TradeResult
from app.utils.errors import ValidationError


class CompliantAdapter:
    def to_canonical(self, source_payload: dict[str, Any]) -> dict[str, Any]:
        return source_payload


class NonCompliantAdapter:
    pass


def test_validate_adapter_contract() -> None:
    """Test validation of compliant and non-compliant adapters (ANL-NFR-095)."""
    # Compliant
    validate_adapter_contract(CompliantAdapter())

    # Non-compliant
    with pytest.raises(ValidationError) as exc_info:
        validate_adapter_contract(NonCompliantAdapter())
    assert "missing callable method 'to_canonical'" in str(exc_info.value)


def test_to_canonical_success() -> None:
    """Test standard dictionary canonicalization defaults and checks."""
    payload = {
        "schema_version": "1.3.1",
        "result_id": "RES-101",
        "phase": "backtest",
        "trades": [{"trade_id": "T1", "pnl": 50.0}],
        "equity_curve": [{"timestamp": "2026-07-07T12:00:00Z", "equity": 10000.0}],
    }
    result = to_canonical(payload)
    assert result["result_id"] == "RES-101"
    assert result["strategy_id"] == "default_strategy"
    assert result["strategy_version"] == "v1"
    assert result["account_base_currency"] == "USD"
    assert result["symbols"] == []
    assert result["timeframe"] == "H1"
    assert len(result["_adapter_warnings"]) == 1


def test_to_canonical_validation_errors() -> None:
    """Test errors raised on missing keys, bad phase, or wrong types."""
    # Missing required key
    with pytest.raises(ValidationError) as exc_info:
        to_canonical({"schema_version": "1.3.1"})
    assert "Missing required keys" in str(exc_info.value)

    # Bad phase
    payload = {
        "schema_version": "1.3.1",
        "result_id": "RES-101",
        "phase": "invalid_phase",
        "trades": [],
        "equity_curve": [],
    }
    with pytest.raises(ValidationError) as exc_info:
        to_canonical(payload)
    assert "phase must be one of" in str(exc_info.value)


def test_to_trading_result_conversions() -> None:
    """Test conversion of dicts and dataclasses to TradingResult (ANL-NFR-092)."""
    # 1. From dict source
    dict_payload = {
        "schema_version": "1.3.1",
        "result_id": "RES-DICT",
        "environment": "backtest",
        "account_base_currency": "EUR",
        "trades": [{"trade_id": "T1", "pnl": 10.0}],
        "equity_curve": [{"timestamp": "2026-07-07T12:00:00Z", "equity": 100.0}],
        "benchmark": {
            "symbol": "SPY",
            "prices": (100.0, 101.0),
            "returns": (0.0, 0.01),
            "timestamps": ("2026-07-07T12:00:00Z", "2026-07-07T12:01:00Z"),
        },
    }
    tr = to_trading_result(dict_payload)
    assert isinstance(tr, TradingResult)
    assert tr.schema_version == "1.3.1"
    assert tr.result_id == "RES-DICT"
    assert tr.account_base_currency == "EUR"
    assert tr.environment == "backtest"
    assert tr.trades == ({"trade_id": "T1", "pnl": 10.0},)
    assert isinstance(tr.benchmark, BenchmarkData)
    assert tr.benchmark.symbol == "SPY"
    assert tr.benchmark.prices == (100.0, 101.0)

    # 2. From TradingResult direct
    tr_direct = to_trading_result(tr)
    assert tr_direct is tr


def test_simulation_journal_adapter() -> None:
    """Test SimulationJournal conversion and provenance mapping (ANL-NFR-449)."""
    trade = TradeResult(
        trade_id="TRADE-1",
        execution_request_id="REQ-1",
        status="filled",
        fill_price=1.234,
        fill_volume=1.0,
    )

    journal = SimulationJournal(
        run_id="RUN-SIM-777",
        config_hash="abc123config",
        journal_ref="s3://simulation-bucket/RUN-SIM-777.json",
        events=(trade,),
        equity_curve=({"timestamp": "2026-07-07T12:00:00Z", "equity": 15000.0},),
        strategy_id="ma_crossover",
        dataset_hash="xyz789dataset",
        cost_model="standard_commission",
        fill_model="bar_close",
        risk_policy_version="risk-v2",
    )

    tr = from_simulation_journal(journal)
    assert tr.result_id == "RUN-SIM-777"
    assert tr.environment == "simulation"
    assert len(tr.trades) == 1
    assert tr.trades[0]["trade_id"] == "TRADE-1"
    assert tr.equity_curve == (
        {"timestamp": "2026-07-07T12:00:00Z", "equity": 15000.0},
    )

    assert isinstance(tr.lineage, Lineage)
    assert tr.lineage.run_id == "RUN-SIM-777"
    assert tr.lineage.strategy_id == "ma_crossover"
    assert tr.lineage.dataset_hash == "xyz789dataset"
    assert tr.lineage.cost_model == "standard_commission"
    assert tr.lineage.fill_model == "bar_close"
    assert tr.lineage.risk_policy_version == "risk-v2"
    assert tr.lineage.journal_reference == "s3://simulation-bucket/RUN-SIM-777.json"


def test_live_trade_journal_adapter() -> None:
    """Test LiveTradeJournal conversion and provenance mapping (ANL-NFR-449)."""
    trade = TradeResult(
        trade_id="TRADE-LIVE",
        execution_request_id="REQ-LIVE",
        status="filled",
        fill_price=10.5,
        fill_volume=0.5,
    )

    journal = LiveTradeJournal(
        session_id="SESS-LIVE-888",
        events=(trade,),
        equity_curve=({"timestamp": "2026-07-07T12:00:00Z", "equity": 25000.0},),
        strategy_id="live_scalper",
        dataset_hash="live_feed_hash",
        cost_model="raw_spread",
        fill_model="market_instant",
        risk_policy_version="risk-v4",
    )

    tr = from_live_trade_journal(journal)
    assert tr.result_id == "SESS-LIVE-888"
    assert tr.environment == "live"
    assert len(tr.trades) == 1
    assert tr.trades[0]["trade_id"] == "TRADE-LIVE"

    assert tr.lineage.run_id == "SESS-LIVE-888"
    assert tr.lineage.strategy_id == "live_scalper"
    assert tr.lineage.dataset_hash == "live_feed_hash"
    assert tr.lineage.cost_model == "raw_spread"
    assert tr.lineage.fill_model == "market_instant"
    assert tr.lineage.risk_policy_version == "risk-v4"

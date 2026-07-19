"""Unit tests for producer-neutral Analytics result adaptation."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.analytics.adapters.results import (
    adapt_trading_result,
    build_closed_trade_equity_curve,
)
from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    AnalyticsValidationError,
    ClosedTrade,
    StatisticalValidationConfig,
)
from app.utils import logger

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _config(**overrides: int) -> AnalyticsRunConfig:
    """Build bounded adapter configuration."""
    logger.debug("Building Analytics adapter test configuration")
    values = {
        "max_warning_detail_bytes": 1024,
        "max_trades": 100,
        "max_equity_points": 100,
        "max_benchmark_points": 100,
        "max_statistical_observations": 100,
        "max_bootstrap_iterations": 100,
        "max_permutation_iterations": 100,
        "max_portfolio_components": 10,
        "max_response_bytes": 100_000,
    }
    values.update(overrides)
    return AnalyticsRunConfig(
        **values,
        risk_free_rate=None,
        statistics=StatisticalValidationConfig(
            seed=1,
            bootstrap_iterations=10,
            permutation_iterations=10,
            confidence=0.95,
            alpha=0.05,
        ),
    )


def _trade(ticket: str, exit_offset: int) -> ClosedTrade:
    """Build one canonical adapter trade."""
    logger.debug("Building Analytics adapter test trade")
    return ClosedTrade(
        ticket=ticket,
        symbol="EURUSD",
        type="BUY",
        volume=Decimal(1),
        entry_time=NOW,
        entry_price=Decimal("1.10"),
        stop_loss=Decimal("1.09"),
        take_profit=Decimal("1.12"),
        exit_time=NOW + timedelta(hours=exit_offset),
        exit_price=Decimal("1.11"),
        comment="closed",
        commission=Decimal(-1),
        swap=Decimal(0),
        profit=Decimal(10),
        magic="strategy-1",
        mae=Decimal(-2),
        mfe=Decimal(12),
    )


def _source() -> dict[str, object]:
    """Build one exact producer-neutral source mapping."""
    logger.debug("Building Analytics adapter source mapping")
    trade = _trade("ticket-1", 1)
    return {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "run-1",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW + timedelta(days=1),
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (dict(trade.__dict__),),
        "quality_metadata": {"canonical": True},
        "source_metadata": {"engine_version": "v1"},
    }


def test_adapt_trading_result_preserves_required_lineage() -> None:
    """Adaptation preserves source identity and every closed-trade field."""
    logger.debug("Testing Analytics adapter lineage")
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    assert result.lineage.source_ids == ("run-1",)
    assert result.trades[0].ticket == "ticket-1"
    assert result.source_metadata["engine_version"] == "v1"


def test_equity_curve_ordering_is_deterministic_and_daily_resampled() -> None:
    """Curve ordering uses exit time then ticket and daily last equity."""
    logger.debug("Testing Analytics equity-curve ordering")
    later = _trade("ticket-2", 2)
    earlier = _trade("ticket-1", 1)
    curve, daily = build_closed_trade_equity_curve(
        (later, earlier), initial_balance=Decimal(1000), config=_config()
    )
    assert [point["ticket"] for point in curve] == ["ticket-1", "ticket-2"]
    assert daily[-1]["equity"] == Decimal(1018)


def test_adapter_requires_configured_point_bounds() -> None:
    """Oversized ledgers fail before curve allocation."""
    logger.debug("Testing Analytics adapter point bounds")
    source = _source()
    second = _trade("ticket-2", 2)
    source["closed_trades"] = (*source["closed_trades"], dict(second.__dict__))
    with pytest.raises(AnalyticsValidationError, match="exceeds configured"):
        adapt_trading_result(
            source,
            source_contract="simulation.result",
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=_config(max_trades=2, max_equity_points=1),
        )


def test_adapter_rejects_unknown_source_fields() -> None:
    """Producer-specific or placeholder fields cannot leak through adaptation."""
    logger.debug("Testing Analytics adapter exact source fields")
    source = _source() | {"provider_object": object()}
    with pytest.raises(AnalyticsValidationError, match="fields mismatch"):
        adapt_trading_result(
            source,
            source_contract="simulation.result",
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=_config(),
        )


def test_adapter_redacts_sensitive_source_metadata() -> None:
    """Producer source metadata is redacted before it reaches the contract."""
    logger.debug("Testing Analytics adapter source-metadata redaction")
    source = _source()
    source["source_metadata"] = {
        "api_key": "abcd1234abcd1234abcd1234",  # pragma: allowlist secret
        "engine_version": "v1",
    }
    result = adapt_trading_result(
        source,
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    assert result.source_metadata["engine_version"] == "v1"
    assert (
        result.source_metadata["api_key"]
        != "abcd1234abcd1234abcd1234"  # pragma: allowlist secret
    )


def test_adapter_redacts_sensitive_quality_metadata() -> None:
    """Producer quality metadata is redacted before it reaches the contract."""
    logger.debug("Testing Analytics adapter quality-metadata redaction")
    source = _source()
    source["quality_metadata"] = {
        "password": "hunter2hunter2hunter2",  # pragma: allowlist secret
        "canonical": True,
    }
    result = adapt_trading_result(
        source,
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    assert result.quality_metadata["canonical"] is True
    assert (
        result.quality_metadata["password"]
        != "hunter2hunter2hunter2"  # pragma: allowlist secret
    )

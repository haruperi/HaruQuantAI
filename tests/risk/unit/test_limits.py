"""Unit tests for deterministic portfolio and market Policy limits."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.evidence.market_context_contracts import (
    MarketContextEvidence,
)
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    LimitStatus,
    PortfolioRiskSnapshot,
    RiskDomainError,
)
from app.services.risk.limits import (
    evaluate_market_context,
    evaluate_portfolio_limits,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _config(*, live: bool = False) -> RiskConfig:
    """Build one complete deterministic Policy configuration.

    Args:
        live: Whether to build the fail-closed live profile.

    Returns:
        Validated Risk configuration.
    """
    values: dict[str, object] = {
        "profile": "live" if live else "simulation",
        "execution_route": "live" if live else "sim",
        "policy_version": "policy-1",
        "base_currency": "USD",
        "pending_order_exposure_policy": "include_full_remaining_exposure",
        "evidence_max_age_seconds": {"portfolio": 60, "market": 30},
        "clock_skew_tolerance_seconds": Decimal(0),
        "var_min_observations": 3,
        "var_lookback": 3,
        "regime_assessment_enabled": False,
        "approval_token_ttl_seconds": Decimal(60),
        "approval_signing_key_ref": "secrets/risk-key",
        "decision_ttl_seconds": Decimal(30),
        "kill_switch_activation_permissions": ("risk.kill.activate",),
        "kill_switch_clearance_permissions": ("risk.kill.clear",),
        "report_timeout_seconds": Decimal(5),
        "session_timezone": "UTC",
        "missing_calendar_mode": "block",
        "max_spread": {"EURUSD@points": Decimal(2)},
    }
    if live:
        values.update(
            audit_timeout_seconds=Decimal(2),
            token_state_timeout_seconds=Decimal(2),
            double_spend_owner="risk_store",
        )
    return RiskConfig.model_validate(values)


def _snapshot(config: RiskConfig) -> PortfolioRiskSnapshot:
    """Build a complete snapshot with several simultaneous breaches."""
    return PortfolioRiskSnapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(1000),
        daily_loss=Decimal(60),
        total_loss=Decimal(120),
        gross_exposure=Decimal(1000),
        net_exposure=Decimal(700),
        drawdown=Decimal("0.11"),
        margin_utilization=Decimal("0.60"),
        effective_leverage=Decimal(11),
        historical_var=Decimal(30),
        historical_cvar=Decimal(40),
        volatility=Decimal("0.02"),
        portfolio_correlation=Decimal("0.80"),
        exposure_by_dimension={
            "symbol:EURUSD": Decimal(600),
            "currency:USD": Decimal(1000),
        },
        contributions={"EURUSD": Decimal(1)},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=NOW,
        config_hash=compute_config_hash(config),
        evidence_refs={"account": "account-evidence-1"},
        request_id="request-1",
        workflow_id="workflow-1",
    )


def _market(*, timezone: str = "UTC") -> MarketContextEvidence:
    """Build complete normalized market-context evidence.

    Args:
        timezone: Evidence timezone text.

    Returns:
        Immutable Data-owned market context.
    """
    return MarketContextEvidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state="clear",
        spread=Decimal(1),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone=timezone,
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={
            "source": "fixture",
            "blackout_before_minutes": "10",
            "blackout_after_minutes": "10",
        },
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def test_limit_order_and_composite_failures() -> None:
    """Return exact precedence with every simultaneous breach preserved."""
    config = _config()
    results = evaluate_portfolio_limits(_snapshot(config), config, now=NOW)
    assert [item.precedence for item in results] == list(range(len(results)))
    assert [item.limit_id for item in results[:5]] == [
        "freshness",
        "consistency",
        "daily_loss",
        "total_loss",
        "drawdown",
    ]
    failures = [item.limit_id for item in results if item.status is LimitStatus.FAIL]
    assert failures[0] == "daily_loss"
    assert {
        "daily_loss",
        "total_loss",
        "drawdown",
        "margin_utilization",
        "effective_leverage",
        "historical_var",
        "historical_cvar",
        "correlation",
    }.issubset(failures)


def test_timezone_failure_blocks_live() -> None:
    """Block a live review when supplied timezone conversion is impossible."""
    results = evaluate_market_context(
        _market(timezone="Mars/Nowhere"),
        _config(live=True),
        now=NOW,
    )
    assert results[1].limit_id == "session"
    assert results[1].status is LimitStatus.BLOCKED


def test_market_context_applies_missing_modes_units_and_availability() -> None:
    """Apply missing calendar policy, exact spread units, and liquidity evidence."""
    config = _config(live=True)
    missing = _market().model_copy(
        update={
            "session_state": "unknown",
            "calendar_state": "unknown",
            "spread": Decimal(3),
            "liquidity": None,
        }
    )
    results = evaluate_market_context(missing, config, now=NOW)
    assert results[1].status is LimitStatus.NEEDS_MORE_EVIDENCE
    assert results[2].status is LimitStatus.BLOCKED
    assert results[3].status is LimitStatus.FAIL
    assert results[4].status is LimitStatus.NEEDS_MORE_EVIDENCE

    blocked = _market().model_copy(
        update={"session_state": "closed", "calendar_state": "event"}
    )
    blocked_results = evaluate_market_context(blocked, config, now=NOW)
    assert blocked_results[1].status is LimitStatus.BLOCKED
    assert blocked_results[2].status is LimitStatus.BLOCKED


def test_portfolio_limits_require_freshness_configuration() -> None:
    """Fail closed when the canonical portfolio freshness key is absent."""
    config = _config().model_copy(update={"evidence_max_age_seconds": {"market": 30}})
    with pytest.raises(RiskDomainError):
        evaluate_portfolio_limits(_snapshot(_config()), config, now=NOW)

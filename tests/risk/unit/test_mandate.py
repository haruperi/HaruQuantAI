"""Unit tests for Risk firm mandates."""

import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
import yaml
from app.services.risk import (
    compute_config_hash,
    create_firm_mandate,
    create_portfolio_risk_snapshot,
    create_risk_config,
    evaluate_portfolio_limits,
    load_firm_mandate,
)
from pydantic import ValidationError

from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 28, tzinfo=UTC)


def _mandate(*, verified: bool = True, terms_hash: str = "a" * 64) -> Any:
    """Build a small valid mandate fixture."""
    return create_firm_mandate(
        account_id="account-1",
        mandate_version="2026.07.28-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="funded",
        initial_balance=Decimal(1000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash=terms_hash,
        verified=verified,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.1")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.05"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.1"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
        consistency_rule={
            "type": "max_single_day_share_of_profit",
            "value": Decimal("0.4"),
            "evaluated": "retrospective",
            "applies_in_phase": ("funded",),
        },
    )


def _config() -> Any:
    """Build a valid simulation configuration."""
    return create_risk_config(
        profile="simulation",
        execution_route="sim",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


def _snapshot(config: Any) -> Any:
    """Build a complete account snapshot for mandate gating."""
    return create_portfolio_risk_snapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(1000),
        initial_balance=Decimal(1000),
        daily_loss=Decimal(0),
        total_loss=Decimal(0),
        gross_exposure=Decimal(0),
        net_exposure=Decimal(0),
        drawdown=Decimal(0),
        peak_equity=Decimal(1000),
        highest_eod_balance=Decimal(1000),
        margin_utilization=Decimal(0),
        effective_leverage=Decimal(0),
        historical_var=None,
        historical_cvar=None,
        volatility=None,
        portfolio_correlation=Decimal(0),
        exposure_by_dimension={},
        contributions={},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=NOW,
        config_hash=unwrap_risk_response(
            compute_config_hash(config), operation="compute_config_hash"
        ),
        evidence_refs={"account": "account-evidence-1"},
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )


def test_mandate_requires_terms_hash() -> None:
    """Reject a mandate without archived terms provenance."""
    values = _mandate().model_dump()
    values.pop("terms_source_hash")
    with pytest.raises(ValidationError):
        create_firm_mandate(**values)


def test_unverified_mandate_blocks_evaluation(tmp_path) -> None:
    """Block limit evaluation before any profile fallback is considered."""
    mandate = _mandate(verified=False)
    config = _config()
    results = unwrap_risk_response(
        evaluate_portfolio_limits(_snapshot(config), config, now=NOW, mandate=mandate),
        operation="evaluate_portfolio_limits",
    )
    assert results[0].limit_id == "mandate"
    assert results[0].reason_code.value == "INVALID_RISK_CONFIG"

    terms = b"archived terms"
    digest = hashlib.sha256(terms).hexdigest()
    loaded = mandate.model_copy(update={"terms_source_hash": digest})
    (tmp_path / "account-1.terms").write_bytes(terms)
    (tmp_path / "account-1.yaml").write_text(
        yaml.safe_dump(loaded.model_dump(warnings=False, mode="json")), encoding="utf-8"
    )
    response = load_firm_mandate("account-1", tmp_path)
    assert response.status == "error"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("account_id", ""),
        ("mandate_version", ""),
        ("firm", ""),
        ("currency", "usd"),
        ("terms_url", ""),
        ("initial_balance", Decimal(0)),
        ("terms_source_hash", "invalid"),
    ],
)
def test_mandate_rejects_invalid_identity(
    field: str,
    value: object,
) -> None:
    """Reject invalid mandate identity and provenance values."""
    values = _mandate().model_dump(warnings=False, mode="python")
    values[field] = value
    with pytest.raises(ValidationError):
        create_firm_mandate(**values)


@pytest.mark.parametrize(
    ("rule", "updates"),
    [
        ("profit_target", {"value": None, "value_absolute": None}),
        ("profit_target", {"value": Decimal("0.1"), "value_absolute": Decimal(10)}),
        ("daily_loss", {"value": None, "value_absolute": None}),
        ("daily_loss", {"reset_time": ""}),
        ("daily_loss", {"reset_tz": "Mars/Nowhere"}),
        ("max_drawdown", {"value": None, "value_absolute": None}),
        (
            "max_drawdown",
            {
                "mode": "trailing_eod",
                "eod_snapshot_time": None,
                "eod_snapshot_tz": None,
            },
        ),
        (
            "max_drawdown",
            {"mode": "static", "eod_snapshot_time": "23:59", "eod_snapshot_tz": "UTC"},
        ),
    ],
)
def test_mandate_rejects_invalid_nested_rules(
    rule: str,
    updates: dict[str, object],
) -> None:
    """Reject ambiguous or incompatible firm-rule representations."""
    values = _mandate().model_dump(warnings=False, mode="python")
    values[rule] = {**values[rule], **updates}
    with pytest.raises(ValidationError):
        create_firm_mandate(**values)

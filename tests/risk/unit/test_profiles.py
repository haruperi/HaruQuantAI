"""Unit tests for strict Risk configuration profiles."""

from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from app.services.risk.config import (
    DrawdownMode,
    RiskConfig,
    compute_config_hash,
    load_risk_config,
)
from app.services.risk.contracts import RiskErrorCode
from app.services.risk.contracts.responses import unwrap_risk_response
from pydantic import ValidationError


def _config_values() -> dict[str, object]:
    """Return the minimum valid non-live Risk configuration values."""
    return {
        "profile": "research",
        "execution_route": "none",
        "policy_version": "policy-1",
        "base_currency": "USD",
        "pending_order_exposure_policy": "block",
        "evidence_max_age_seconds": {"portfolio": 60, "market": 30},
        "regime_assessment_enabled": False,
        "approval_token_ttl_seconds": Decimal(60),
        "approval_signing_key_ref": "secrets/risk-approval-key",
        "decision_ttl_seconds": Decimal(30),
        "kill_switch_activation_permissions": ("risk.kill.activate",),
        "kill_switch_clearance_permissions": ("risk.kill.clear",),
        "report_timeout_seconds": Decimal(5),
    }


def _yaml_values() -> dict[str, object]:
    """Return a YAML-safe form of the minimum configuration."""
    values = _config_values()
    values["approval_token_ttl_seconds"] = "60"
    values["decision_ttl_seconds"] = "30"
    values["report_timeout_seconds"] = "5"
    values["kill_switch_activation_permissions"] = ["risk.kill.activate"]
    values["kill_switch_clearance_permissions"] = ["risk.kill.clear"]
    return values


def test_live_profile_requires_all_safety_values() -> None:
    """Fail closed when a live profile omits mandatory safety settings."""
    values = _config_values()
    values.update({"profile": "live", "execution_route": "live"})
    with pytest.raises(ValidationError):
        RiskConfig.model_validate(values)


def test_missing_live_profile_fails_closed(tmp_path: Path) -> None:
    """Map a missing selected profile to the canonical configuration error."""
    response = load_risk_config("live", tmp_path)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.INVALID_RISK_CONFIG.value


def test_selected_profile_loads_from_bounded_root(tmp_path: Path) -> None:
    """Load only the matching selected YAML document."""
    profile_path = tmp_path / "research.yaml"
    profile_path.write_text(yaml.safe_dump(_yaml_values()), encoding="utf-8")
    config = unwrap_risk_response(
        load_risk_config("research", tmp_path), operation="load_risk_config"
    )
    assert config.profile == "research"
    assert config.approval_token_ttl_seconds == Decimal(60)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("decision_ttl_seconds", True),
        ("decision_ttl_seconds", "not-a-number"),
        ("max_spread", []),
    ],
)
def test_yaml_loader_rejects_invalid_declared_types(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    """Fail closed when YAML values violate declared numeric contracts."""
    values = _yaml_values()
    values[field] = value
    (tmp_path / "research.yaml").write_text(
        yaml.safe_dump(values),
        encoding="utf-8",
    )
    response = load_risk_config("research", tmp_path)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.INVALID_RISK_CONFIG.value


def test_config_hash_is_stable_and_sensitive() -> None:
    """Keep identical hashes stable and change them for material policy changes."""
    config = RiskConfig.model_validate(_config_values())
    same = RiskConfig.model_validate(_config_values())
    changed_values = _config_values()
    changed_values["max_daily_loss"] = Decimal("0.04")
    changed = RiskConfig.model_validate(changed_values)
    first = unwrap_risk_response(
        compute_config_hash(config), operation="compute_config_hash"
    )
    second = unwrap_risk_response(
        compute_config_hash(same), operation="compute_config_hash"
    )
    third = unwrap_risk_response(
        compute_config_hash(changed), operation="compute_config_hash"
    )
    assert first == second
    assert first != third


def test_trailing_eod_requires_snapshot_time() -> None:
    """Require time and timezone evidence for end-of-day trailing mode."""
    values = _config_values()
    values["drawdown_mode"] = DrawdownMode.TRAILING_EOD
    with pytest.raises(ValidationError):
        RiskConfig.model_validate(values)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile", "paper"),
        ("evidence_max_age_seconds", {}),
        ("kill_switch_activation_permissions", ()),
        ("var_confidence", Decimal(1)),
        ("max_correlation", Decimal("-0.1")),
        ("max_daily_loss", Decimal(0)),
        ("max_historical_var_ratio", Decimal(0)),
        ("max_historical_cvar_ratio", Decimal("0.01")),
        ("allocation_caps", {"strategy": Decimal(0)}),
        ("max_spread", {"EURUSD": Decimal(-1)}),
        ("dependency_timeouts_seconds", {"data": Decimal(0)}),
        ("clock_skew_tolerance_seconds", Decimal(-1)),
        ("var_min_observations", 0),
        ("var_lookback", 0),
        ("min_kelly_trades", 0),
        ("news_blackout_before_minutes", -1),
        ("audit_retry_attempts", -1),
        ("max_scenarios_per_run", 0),
        ("max_positions_per_scenario_run", 501),
        ("audit_genesis_hash", "A" * 64),
        ("policy_version", " policy-1"),
        ("report_timezone", "Not/AZone"),
        ("compatible_config_hashes", {"bad": ("a" * 64,)}),
        ("crisis_windows_utc", {"event": ("bad", "values")}),
        ("kelly_insufficient_evidence_mode", "block"),
        ("stressed_lookback_days", 0),
    ],
)
def test_config_rejects_invalid_policy_values(
    field: str,
    value: object,
) -> None:
    """Reject invalid strict policy values at the public construction boundary."""
    values = _config_values()
    values[field] = value
    with pytest.raises(ValidationError):
        RiskConfig.model_validate(values)

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

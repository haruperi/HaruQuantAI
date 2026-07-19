"""Runnable usage examples for the public Risk configuration API."""

from decimal import Decimal
from pathlib import Path

import yaml
from app.services.risk.config import RiskConfig, compute_config_hash, load_risk_config


def _values() -> dict[str, object]:
    """Return one bounded research-profile policy mapping."""
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


def test_usage_profiles_config() -> None:
    """Construct one strict immutable Risk configuration."""
    config = RiskConfig.model_validate(_values())
    assert config.policy_version == "policy-1"


def test_usage_profiles_load(tmp_path: Path) -> None:
    """Load one explicitly selected profile from a bounded root."""
    values = _values()
    for field_name in (
        "approval_token_ttl_seconds",
        "decision_ttl_seconds",
        "report_timeout_seconds",
    ):
        values[field_name] = str(values[field_name])
    values["kill_switch_activation_permissions"] = ["risk.kill.activate"]
    values["kill_switch_clearance_permissions"] = ["risk.kill.clear"]
    (tmp_path / "research.yaml").write_text(
        yaml.safe_dump(values),
        encoding="utf-8",
    )
    assert load_risk_config("research", tmp_path).profile == "research"


def test_usage_profiles_hash() -> None:
    """Compute the stable canonical configuration hash."""
    digest = compute_config_hash(RiskConfig.model_validate(_values()))
    assert len(digest) == 64

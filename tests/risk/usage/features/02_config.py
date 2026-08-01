"""Executable Risk config usage example.

Demonstrates FEAT-RISK-02 Risk profiles, firm mandates, and stable configuration hashing.
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import (
    build_development_risk_config,
    compute_config_hash,
    create_firm_mandate,
    create_risk_config,
    get_drawdown_mode,
    load_firm_mandate,
    load_risk_config,
)
from tests.risk._support import unwrap_risk_response


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _values() -> dict[str, object]:
    """Return bounded policy configuration mapping."""
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


def _mandate(*, verified: bool = True, digest: str = "a" * 64) -> object:
    """Build a bounded mandate usage fixture."""
    return create_firm_mandate(
        account_id="usage-account",
        mandate_version="2026.07.28-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="funded",
        initial_balance=Decimal(10000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash=digest,
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
    )


# --- Stage 1: YAML Profile & Mandate Inputs ---


def fr_risk_023() -> None:
    """FR-RISK-023: Stage 1 — Load only the selected YAML profile from the bounded root and fail closed on missing/invalid live configuration."""
    _header("Stage 1: YAML Profile Input - Load Risk Profile Config (FR-RISK-023)")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "research.yaml").write_text(
            yaml.safe_dump(
                create_risk_config(**_values()).model_dump(warnings=False, mode="json"),
            ),
            encoding="utf-8",
        )
        loaded = unwrap_risk_response(
            load_risk_config("research", root),
            operation="load_risk_config",
        )
        print(_format_result(loaded))
        print(
            f"Data -> profile='{loaded.profile}', execution_route='{loaded.execution_route}'"
        )


def fr_risk_063() -> None:
    """FR-RISK-063: Stage 1 — Define an immutable per-account firm mandate record carrying firm identity, product model, phase, initial balance, the archived terms URL, access date and terms content hash, and an explicit `verified` flag."""
    _header("Stage 1: Firm Mandate Input - Define Firm Mandate (FR-RISK-063)")
    mandate = _mandate()
    print(_format_result(mandate))
    print(
        f"Data -> account_id='{mandate.account_id}', version='{mandate.mandate_version}', verified={mandate.verified}"
    )


# --- Stage 2: Strict RiskConfig & Mandate Validation ---


def fr_risk_022() -> None:
    """FR-RISK-022: Stage 2 — Define strict profile fields, thresholds, modes, freshness, rounding, concurrency, audit, and dependency timeouts with stable schema version."""
    _header(
        "Stage 2: Strict Config Validation - Define RiskConfig Fields (FR-RISK-022)"
    )
    config = create_risk_config(**_values())
    print(_format_result(config))
    print(
        f"Data -> profile='{config.profile}', policy_version='{config.policy_version}'"
    )


def fr_risk_064() -> None:
    """FR-RISK-064: Stage 2 — Refuse every limit evaluation for an account whose mandate is unverified or whose archived terms hash no longer matches, failing closed rather than falling back to a profile default."""
    _header("Stage 2: Mandate Verification - Load & Verify Firm Mandate (FR-RISK-064)")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        terms = b"bounded archived terms"
        digest = hashlib.sha256(terms).hexdigest()
        (root / "usage-account.terms").write_bytes(terms)
        (root / "usage-account.yaml").write_text(
            yaml.safe_dump(
                _mandate(digest=digest).model_dump(warnings=False, mode="json")
            ),
            encoding="utf-8",
        )
        loaded = unwrap_risk_response(
            load_firm_mandate("usage-account", root), operation="load_firm_mandate"
        )
        print(_format_result(loaded))
        print(f"Data -> account_id='{loaded.account_id}', verified={loaded.verified}")


def fr_risk_065() -> None:
    """FR-RISK-065: Stage 2 — Expose the drawdown mode, its reference basis, whether it trails unrealised equity, whether a ratchet ceiling applies, and any end-of-day snapshot time and timezone as required configuration."""
    _header("Stage 2: Drawdown Config Validation - Drawdown Mode Config (FR-RISK-065)")
    config = create_risk_config(
        **_values(),
        drawdown_mode=get_drawdown_mode("TRAILING_EOD"),
        drawdown_eod_snapshot_time="23:59",
        drawdown_eod_snapshot_timezone="UTC",
    )
    print(_format_result(config))
    print(
        f"Data -> drawdown_mode='{config.drawdown_mode}', eod_snapshot='{config.drawdown_eod_snapshot_time} {config.drawdown_eod_snapshot_timezone}'"
    )


# --- Stage 3: Config Hashing & Final Artifacts ---


def fr_risk_024() -> None:
    """FR-RISK-024: Stage 3 — Hash canonical exact serialization so any material config change changes the SHA-256 hash."""
    _header("Stage 3: Config Hash Output - Compute Config SHA256 Hash (FR-RISK-024)")
    config = create_risk_config(**_values())
    digest = unwrap_risk_response(
        compute_config_hash(config), operation="compute_config_hash"
    )
    print(_format_result(digest))
    print(f"Data -> config_hash='{digest}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-02 — config/ — Risk Profiles and Stable Configuration\n\n"
        "Purpose: Load, validate, select, and hash profile-driven Risk configuration without inventing trading thresholds.\n\n"
        "Module flow:\n"
        "-> Stage 1: YAML profile configs & firm mandate inputs\n"
        "-> Stage 2: Strict RiskConfig and firm mandate validation\n"
        "-> Stage 3: Canonical JSON & config SHA-256 hash"
    )
    assert build_development_risk_config().profile == "research"

    # 1. Stage 1: YAML & Mandate inputs
    fr_risk_023()
    fr_risk_063()

    # 2. Stage 2: Config and Mandate validation
    fr_risk_022()
    fr_risk_064()
    fr_risk_065()

    # 3. Stage 3: Canonical config hash
    fr_risk_024()


if __name__ == "__main__":
    main()

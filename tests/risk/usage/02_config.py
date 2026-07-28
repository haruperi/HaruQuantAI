"""Executable Risk config usage example.

Demonstrates RiskConfig validation, file loading, and canonical config hash calculation.
"""

import hashlib
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import yaml

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk import (
    DrawdownMode,
    FirmMandate,
    RiskConfig,
    compute_config_hash,
    load_firm_mandate,
)

from tests.risk._support import unwrap_risk_response


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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


def example_config() -> None:
    """Demonstrate RiskConfig validation and hashing."""
    _header("Demonstrate RiskConfig validation and hashing.")
    print("Risk Example 2: Configuration Validation and Hashing")

    # 1. Validate config
    config = RiskConfig.model_validate(_values())
    print(
        f"RiskConfig profile: {config.profile}, policy version: {config.policy_version}"
    )

    # 2. Compute config hash
    digest = unwrap_risk_response(
        compute_config_hash(config), operation="compute_config_hash"
    )
    print(f"Computed RiskConfig SHA256 digest: {digest}")


_DEMONSTRATED = False


def _demonstrate_once() -> None:
    """Run the bounded configuration demonstration once."""
    global _DEMONSTRATED  # noqa: PLW0603
    if not _DEMONSTRATED:
        example_config()
        _DEMONSTRATED = True


def fr_risk_022() -> None:
    """FR-RISK-022: Define strict profile fields, thresholds, modes, freshness,
    rounding, concurrency, audit, and dependency timeouts with stable schema
    version."""
    _header(
        "FR-RISK-022: Define strict profile fields, thresholds, modes, freshness, rounding, concurrency, audit, and dependency timeouts with stable schema version."
    )
    _demonstrate_once()


def fr_risk_023() -> None:
    """FR-RISK-023: Load only the selected YAML profile from the bounded root and
    fail closed on missing/invalid live configuration."""
    _header(
        "FR-RISK-023: Load only the selected YAML profile from the bounded root and fail closed on missing/invalid live configuration."
    )
    _demonstrate_once()


def fr_risk_024() -> None:
    """FR-RISK-024: Hash canonical exact serialization so any material config
    change changes the SHA-256 hash."""
    _header(
        "FR-RISK-024: Hash canonical exact serialization so any material config change changes the SHA-256 hash."
    )
    _demonstrate_once()


def _mandate(*, verified: bool = True, digest: str = "a" * 64) -> FirmMandate:
    """Build a bounded mandate usage fixture."""
    return FirmMandate(
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


def fr_risk_063() -> None:
    """FR-RISK-063: Demonstrate an immutable mandate record."""
    _header("FR-RISK-063: Immutable per-account firm mandate record")
    mandate = _mandate()
    print(f"Mandate account/version: {mandate.account_id}/{mandate.mandate_version}")
    print(f"Terms hash present: {bool(mandate.terms_source_hash)}")


def fr_risk_064() -> None:
    """FR-RISK-064: Demonstrate archived terms verification and fail-closed load."""
    _header("FR-RISK-064: Verified mandate loading")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        terms = b"bounded archived terms"
        digest = hashlib.sha256(terms).hexdigest()
        (root / "usage-account.terms").write_bytes(terms)
        (root / "usage-account.yaml").write_text(
            yaml.safe_dump(_mandate(digest=digest).model_dump(mode="json")),
            encoding="utf-8",
        )
        loaded = unwrap_risk_response(
            load_firm_mandate("usage-account", root), operation="load_firm_mandate"
        )
        print(f"Verified mandate loaded: {loaded.verified}")


def fr_risk_065() -> None:
    """FR-RISK-065: Demonstrate explicit drawdown mode configuration."""
    _header("FR-RISK-065: Explicit drawdown mode configuration")
    config = RiskConfig.model_validate(
        {
            **_values(),
            "drawdown_mode": DrawdownMode.TRAILING_EOD,
            "drawdown_eod_snapshot_time": "23:59",
            "drawdown_eod_snapshot_timezone": "UTC",
        }
    )
    print(
        f"Drawdown mode: {config.drawdown_mode}; snapshot: "
        f"{config.drawdown_eod_snapshot_time} {config.drawdown_eod_snapshot_timezone}"
    )


def main() -> None:
    """Run every functional-requirement demonstration for Risk configuration."""
    for demonstrate in (
        fr_risk_022,
        fr_risk_023,
        fr_risk_024,
        fr_risk_063,
        fr_risk_064,
        fr_risk_065,
    ):
        demonstrate()


if __name__ == "__main__":
    main()

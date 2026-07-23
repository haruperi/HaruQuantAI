"""Executable Risk config usage example.

Demonstrates RiskConfig validation, file loading, and canonical config hash calculation.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk.config import RiskConfig, compute_config_hash


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
    print("=" * 80)
    print("Risk Example 2: Configuration Validation and Hashing")
    print("=" * 80)

    # 1. Validate config
    config = RiskConfig.model_validate(_values())
    print(
        f"RiskConfig profile: {config.profile}, policy version: {config.policy_version}"
    )

    # 2. Compute config hash
    digest = compute_config_hash(config)
    print(f"Computed RiskConfig SHA256 digest: {digest}")


def main() -> None:
    """Run Risk config usage example."""
    example_config()


if __name__ == "__main__":
    main()

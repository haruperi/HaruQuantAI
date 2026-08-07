"""Executable Risk strategy operational-eligibility usage example.

Demonstrates FEAT-RISK-08 reviewing an exact registered Strategy version for operational use without mutating Strategy registration state.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import build_market_context_evidence
from app.services.risk import (
    create_risk_audit_chain,
    create_risk_audit_record,
    create_risk_config,
    create_strategy_operational_eligibility_request,
    review_strategy_admission,
)
from app.services.strategy import (
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)
from app.utils import canonical_json
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"
HASH_A = "a" * 64
HASH_B = "b" * 64


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


class _ExampleAuditStore:
    """Minimal append-only audit store for this example."""

    def __init__(self) -> None:
        self.records: list[create_risk_audit_record] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> Any | None:
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: Any,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(self, *, timeout_seconds: Decimal | None) -> tuple[Any, ...]:
        del timeout_seconds
        return tuple(self.records)


class _ExampleEligibilityStore:
    """Minimal idempotent eligibility decision store for this example."""

    def __init__(self) -> None:
        self.decision: Any | None = None

    def save_if_absent(
        self,
        decision: Any,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        del timeout_seconds
        if self.decision is not None:
            return False
        self.decision = decision
        return True


def _config() -> create_risk_config:
    """Build a complete simulation-profile Risk configuration."""
    return create_risk_config(
        profile="simulation",
        execution_route="sim",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=3,
        var_lookback=3,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


def _market() -> build_market_context_evidence:
    """Build fresh complete Data-owned market-context evidence."""
    return build_market_context_evidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state="clear",
        spread=Decimal(1),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "example"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def _registration() -> create_validated_strategy_ref:
    """Build an approved simulation Strategy registration reference."""
    validation = create_strategy_validation_policy(
        policy_version="strategy-policy-1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4096,
        max_config_nesting_depth=8,
        max_config_string_length=256,
        max_config_collection_items=128,
    )
    manifest = create_strategy_manifest(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        owner_ref="team-alpha",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("bars",),
        required_indicators=(),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        permitted_environments=(get_strategy_environment("SIMULATION"),),
        source_hash=HASH_A,
        artifact_hash=HASH_A,
        dependency_hash=HASH_A,
        provenance_refs=("build-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=100,
        max_diagnostic_bytes=8192,
        max_checkpoint_bytes=8192,
        max_local_state_bytes=4096,
        decision_timeout_seconds=5,
    )
    return create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("SIMULATION"),
        policy_version=validation.policy_version,
        validation_policy=validation,
        registry_record_hash=HASH_B,
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _request() -> create_strategy_operational_eligibility_request:
    """Build an eligibility request bound to one exact registered version."""
    return create_strategy_operational_eligibility_request(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        runtime_profile="simulation",
        execution_route="sim",
        policy_version="policy-1",
        registration_ref=HASH_B,
        evidence_refs={"market": MARKET_REQUEST_ID},
        approval_refs=(),
        requested_scope={"symbol": "EURUSD"},
        requested_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def fr_risk_029() -> None:
    """FR-RISK-029: Stage 3 — Validate a public Strategy `create_validated_strategy_ref` against the exact request, produce and atomically persist `StrategyOperationalEligibilityDecision v1` with scope, conditions, evidence/policy lineage, issue/expiry, and suspension semantics, then append its Risk audit record; never mutate Strategy state."""
    _header(
        "Stage 3: Strategy Admission Review - Review Strategy Admission (FR-RISK-029)"
    )
    print("SUCCESS: FR-RISK-029")

    config = _config()
    store = _ExampleEligibilityStore()
    audit = create_risk_audit_chain(
        config, _ExampleAuditStore(), lambda: NOW, canonical_json
    )

    decision = unwrap_risk_response(
        review_strategy_admission(
            _request(),
            _registration(),
            _market(),
            config,
            store,
            audit,
            now=NOW,
        ),
        operation="review_strategy_admission",
    )
    print(_format_result(decision))
    print(
        f"Data -> decision_id='{decision.decision_id}', state='{decision.state}', suspended={decision.suspended}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-08 — admission/ — Strategy Operational Eligibility Review\n\n"
        "Purpose: Review an exact registered Strategy version for operational use without mutating Strategy registration state.\n\n"
        "Module flow:\n"
        "-> Stage 1: Build untrusted eligibility request, strategy registration ref, and market evidence\n"
        "-> Stage 2: Validate strategy registration match, policy, and market context\n"
        "-> Stage 3: Return StrategyOperationalEligibilityDecision and persist sealed audit record"
    )
    fr_risk_029()


if __name__ == "__main__":
    main()

"""Executable Risk strategy operational-eligibility usage example.

Demonstrates reviewing an exact registered Strategy version for operational use
without mutating Strategy registration state.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.evidence.market_context_contracts import MarketContextEvidence
from app.services.risk.admission import review_strategy_admission
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import (
    RiskAuditRecord,
    StrategyOperationalEligibilityDecision,
    StrategyOperationalEligibilityRequest,
)
from app.services.strategy import (
    StrategyEnvironment,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyRef,
)
from app.utils import canonical_json

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"
HASH_A = "a" * 64
HASH_B = "b" * 64


class _ExampleAuditStore:
    """Minimal append-only audit store for this example."""

    def __init__(self) -> None:
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        del timeout_seconds
        return tuple(self.records)


class _ExampleEligibilityStore:
    """Minimal idempotent eligibility decision store for this example."""

    def __init__(self) -> None:
        self.decision: StrategyOperationalEligibilityDecision | None = None

    def save_if_absent(
        self,
        decision: StrategyOperationalEligibilityDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        del timeout_seconds
        if self.decision is not None:
            return False
        self.decision = decision
        return True


def _config() -> RiskConfig:
    """Build a complete simulation-profile Risk configuration."""
    return RiskConfig(
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


def _market() -> MarketContextEvidence:
    """Build fresh complete Data-owned market-context evidence."""
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
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "example"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def _registration() -> ValidatedStrategyRef:
    """Build an approved simulation Strategy registration reference."""
    validation = StrategyValidationPolicy(
        policy_version="strategy-policy-1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4096,
        max_config_nesting_depth=8,
        max_config_string_length=256,
        max_config_collection_items=128,
    )
    manifest = StrategyManifest(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        owner_ref="team-alpha",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("bars",),
        required_indicators=(),
        timing_policy=StrategyTimingPolicy.EVENT_DRIVEN,
        permitted_environments=(StrategyEnvironment.SIMULATION,),
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
    return ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=StrategyEnvironment.SIMULATION,
        policy_version=validation.policy_version,
        validation_policy=validation,
        registry_record_hash=HASH_B,
        request_id="strategy-request-1",
        correlation_id="correlation-1",
    )


def _request() -> StrategyOperationalEligibilityRequest:
    """Build an eligibility request bound to one exact registered version."""
    return StrategyOperationalEligibilityRequest(
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
        request_id="admission-request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )


def example_admission() -> None:
    """Demonstrate reviewing strategy operational eligibility."""
    print("=" * 80)
    print("Risk Example 8: Strategy Operational Eligibility")
    print("=" * 80)

    config = _config()
    store = _ExampleEligibilityStore()
    audit = RiskAuditChain(config, _ExampleAuditStore(), lambda: NOW, canonical_json)

    decision = review_strategy_admission(
        _request(),
        _registration(),
        _market(),
        config,
        store,
        audit,
        now=NOW,
    )
    print(f"Eligibility verdict: {decision.state}, suspended: {decision.suspended}")
    print(
        f"Decision ID: {decision.decision_id}, "
        f"strategy: {decision.strategy_id}@{decision.strategy_version}"
    )
    print(f"Durably persisted: {store.decision is not None}")


def main() -> None:
    """Run the Risk strategy operational-eligibility usage example."""
    example_admission()


if __name__ == "__main__":
    main()

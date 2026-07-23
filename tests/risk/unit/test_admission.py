"""Unit tests for Strategy operational-admission Risk policy."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.evidence.market_context_contracts import (
    MarketContextEvidence,
)
from app.services.risk.admission import review_strategy_admission
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import (
    DecisionState,
    RiskAuditRecord,
    RiskDomainError,
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

NOW = datetime(2026, 7, 19, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


class _EligibilityStore:
    """Atomic in-memory eligibility store for admission tests."""

    def __init__(self) -> None:
        """Initialize without a decision."""
        self.decision: StrategyOperationalEligibilityDecision | None = None

    def save_if_absent(
        self,
        decision: StrategyOperationalEligibilityDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Persist the first exact decision.

        Args:
            decision: Decision to persist.
            timeout_seconds: Configured store timeout.

        Returns:
            Whether the store was empty.
        """
        del timeout_seconds
        if self.decision is not None:
            return False
        self.decision = decision
        return True


class _Audit:
    """Capturing audit coordinator for focused admission tests."""

    def __init__(self) -> None:
        """Initialize an empty event list."""
        self.records: list[RiskAuditRecord] = []

    def append(self, record: RiskAuditRecord) -> RiskAuditRecord:
        """Capture one admission event.

        Args:
            record: Unsealed event.

        Returns:
            Captured event.
        """
        self.records.append(record)
        return record


def _config() -> RiskConfig:
    """Build a complete simulation Policy configuration."""
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


def _registration() -> ValidatedStrategyRef:
    """Build one exact approved public Strategy reference."""
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


def _market() -> MarketContextEvidence:
    """Build complete fresh Data-owned market evidence."""
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
        provenance={"source": "fixture"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def _request() -> StrategyOperationalEligibilityRequest:
    """Build one exact simulation admission request."""
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


def test_admission_never_mutates_strategy_state() -> None:
    """Persist and audit eligibility without changing the Strategy reference."""
    registration = _registration()
    before = registration.model_dump(mode="json")
    store = _EligibilityStore()
    audit = _Audit()
    decision = review_strategy_admission(
        _request(),
        registration,
        _market(),
        _config(),
        store,
        audit,  # type: ignore[arg-type]
        now=NOW,
    )
    assert decision.state is DecisionState.APPROVE
    assert decision.suspended is False
    assert store.decision == decision
    assert len(audit.records) == 1
    assert registration.model_dump(mode="json") == before


def test_admission_fails_closed_on_evidence_or_identity_conflict() -> None:
    """Reject unbound market evidence and duplicate durable decision identity."""
    request = _request().model_copy(update={"evidence_refs": {"market": "wrong"}})
    with pytest.raises(RiskDomainError):
        review_strategy_admission(
            request,
            _registration(),
            _market(),
            _config(),
            _EligibilityStore(),
            _Audit(),  # type: ignore[arg-type]
            now=NOW,
        )

    store = _EligibilityStore()
    audit = _Audit()
    review_strategy_admission(
        _request(),
        _registration(),
        _market(),
        _config(),
        store,
        audit,  # type: ignore[arg-type]
        now=NOW,
    )
    with pytest.raises(RiskDomainError):
        review_strategy_admission(
            _request(),
            _registration(),
            _market(),
            _config(),
            store,
            audit,  # type: ignore[arg-type]
            now=NOW,
        )

"""Unit tests for source evaluation policy and promotion transitions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts import MarketDataRequest
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.sources import (
    SourceDescriptor,
    SourceLicensePolicy,
    SourcePromotionRequest,
)
from app.services.data.sources.policy import (
    SourcePolicyConfig,
    _record_failure,
    _reset_policy_registry,
    evaluate_source_policy,
    promote_source,
    record_source_attempt,
    register_source_policy,
)
from app.services.data.sources.protocol import MarketDataSource
from app.services.data.sources.registry import (
    _reset_registry,
    register_source,
)
from app.utils import generate_id
from app.utils.contracts.auth import AuthContext

# Base timestamps
START = datetime.now(UTC)
END = START + timedelta(hours=1)


def _configure_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test_policy.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    from app.services.data.storage.migrations import run_data_migrations

    run_data_migrations(generate_id("req"))


@pytest.fixture(autouse=True)
def _cleanup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _reset_registry()
    _reset_policy_registry()
    _configure_database(monkeypatch, tmp_path)


def _register_descriptor(descriptor: SourceDescriptor) -> None:
    """Register one source with explicit bounded policy configuration."""
    register_source(descriptor, lambda: MagicMock(spec=MarketDataSource))
    register_source_policy(
        SourcePolicyConfig(
            source_id=descriptor.source_id,
            rate_limit=100,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=60,
        )
    )


def _make_descriptor(
    source_id: str,
    readiness: str = "production",
    capabilities: tuple[str, ...] = ("bars",),
    workflows: tuple[str, ...] = ("research",),
    evidence: tuple[str, ...] = ("staging_check",),
) -> SourceDescriptor:
    policy = SourceLicensePolicy(
        source_id=source_id,
        status="approved",
        permitted_workflows=workflows,  # type: ignore[arg-type]
        export_allowed=True,
        attribution_required=False,
    )
    return SourceDescriptor(
        source_id=source_id,
        readiness=readiness,  # type: ignore[arg-type]
        capabilities=capabilities,
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="1.0",
        timezone="UTC",
        revision="v1",
        license_policy=policy,
        identity_mapping_revision="v1",
        promotion_evidence=evidence,
    )


def _make_auth_context(roles: tuple[str, ...] = ()) -> AuthContext:
    uid = "12b2174e-8e24-47ec-b2f1-feb0a9f75142"
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="user-1",
        principal_type="USER",
        roles=roles,
        permissions=(),
        scopes=(),
        tenant_or_environment="dev",
        request_id=f"req-{uid}",
        workflow_id=f"wf-{uid}",
        correlation_id=f"cor-{uid}",
        issued_at=datetime.now(UTC),
    )


def test_evaluate_source_policy_success() -> None:
    """Verify that a valid requested source evaluates successfully."""
    desc = _make_descriptor("src-1", readiness="production", capabilities=("bars",))
    _register_descriptor(desc)

    req = MarketDataRequest(
        source_id="src-1",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1m",
        start=START,
        end=END,
        limit=100,
        use_cache=False,
        quality_failure_behavior="fail",
        workflow_context="research",
        precision_policy="float_research_only",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    plan = evaluate_source_policy(req)
    assert plan.requested_source == "src-1"
    assert plan.ordered_sources == ("src-1",)


def test_evaluate_source_policy_unregistered() -> None:
    """Verify evaluate_source_policy raises SOURCE_UNAVAILABLE when missing."""
    req = MarketDataRequest(
        source_id="missing-source",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1m",
        start=START,
        end=END,
        limit=100,
        use_cache=False,
        quality_failure_behavior="fail",
        workflow_context="research",
        precision_policy="float_research_only",
        request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
    )

    with pytest.raises(DataError) as captured:
        evaluate_source_policy(req)
    assert captured.value.code == "SOURCE_UNAVAILABLE"


def test_evaluate_source_policy_capability_mismatch() -> None:
    """Verify SOURCE_UNAVAILABLE on capability mismatch."""
    desc = _make_descriptor("src-1", capabilities=("ticks",))
    _register_descriptor(desc)

    req = MarketDataRequest(
        source_id="src-1",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1m",
        start=START,
        end=END,
        limit=100,
        use_cache=False,
        quality_failure_behavior="fail",
        workflow_context="research",
        precision_policy="float_research_only",
        request_id="req-bc0e142195cb27a6127a29283e0ccdfb3a51449da848f04abee1c1526184084e",
    )

    with pytest.raises(DataError) as captured:
        evaluate_source_policy(req)
    assert captured.value.code == "SOURCE_UNAVAILABLE"


def test_evaluate_source_policy_license_restriction() -> None:
    """Verify LICENSE_RESTRICTION on workflow mismatch."""
    desc = _make_descriptor("src-1", workflows=("research",))
    _register_descriptor(desc)

    req = MarketDataRequest(
        source_id="src-1",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1m",
        start=START,
        end=END,
        limit=100,
        use_cache=False,
        quality_failure_behavior="fail",
        workflow_context="backtest",  # Not permitted
        precision_policy="decimal_string",  # Valid for backtest context
        request_id="req-d9c2b1bc8ab6d4617766f0c4dbee6bbbc164c63262325a31ed7b8c8bb2d90bca",
    )

    with pytest.raises(DataError) as captured:
        evaluate_source_policy(req)
    assert captured.value.code == "LICENSE_RESTRICTION"


def test_evaluate_source_policy_circuit_breaking() -> None:
    """Verify circuit breaker opens after consecutive failures."""
    desc = _make_descriptor("src-1")
    _register_descriptor(desc)

    # Record 3 failures
    _record_failure(
        "src-1", "req-7e0497538e5eb537ef157d96ac7f4711d11d3bf0b7150a2e9fc17dfd3379d2be"
    )
    _record_failure(
        "src-1", "req-a4f8331219e27b8ea303add61466df9c5db1cc849c368e401041e35c80549764"
    )
    _record_failure(
        "src-1", "req-4b7355ff9b565ae827dd671a6db82a3055875839e23fb50dbbf013f5edc03a38"
    )

    req = MarketDataRequest(
        source_id="src-1",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1m",
        start=START,
        end=END,
        limit=100,
        use_cache=False,
        quality_failure_behavior="fail",
        workflow_context="research",
        precision_policy="float_research_only",
        request_id="req-749e7e1c63a152e701f9ae4d52d9dc8fe7b50df12c9f54b06e7a9f8ff3550414",
    )

    with pytest.raises(DataError) as captured:
        evaluate_source_policy(req)
    assert captured.value.code == "CIRCUIT_BREAKER_OPEN"


def test_evaluate_source_policy_rate_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that evaluate_source_policy rejects source if rate limit is exceeded."""
    desc = _make_descriptor("src-1")
    _register_descriptor(desc)

    # Trigger rate limit (simulate 100 recent attempts)
    for _ in range(100):
        record_source_attempt("src-1", generate_id("req"), "SUCCESS")

    req = MarketDataRequest(
        source_id="src-1",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1m",
        start=START,
        end=END,
        limit=100,
        use_cache=False,
        quality_failure_behavior="fail",
        workflow_context="research",
        precision_policy="float_research_only",
        request_id="req-eb1bae3d11ff7b713a6bcf6bc16a5bf7fb51efa405d42d0caa8bf5dcda7c090b",
    )

    plan = evaluate_source_policy(req)
    assert plan.source_id == "src-1"


def test_promote_source_unauthorized() -> None:
    """Verify that promote_source checks permissions."""
    desc = _make_descriptor("src-1", readiness="disabled")
    _register_descriptor(desc)

    auth = _make_auth_context(roles=())

    promo_req = SourcePromotionRequest(
        source_id="src-1",
        target_readiness="staging",
        evidence=("staging_check",),
        request_id="req-cffae068a5c52b2bfc23b7bbd83d773ae5d705b427ad8341299d256dfcf06ffe",
    )

    with pytest.raises(DataError) as captured:
        promote_source(promo_req, auth)
    assert captured.value.code == "PERMISSION_DENIED"


def test_promote_source_production_missing_evidence() -> None:
    """Verify that promotion to production validates evidence checklist."""
    desc = _make_descriptor(
        "src-1",
        readiness="disabled",
        evidence=("staging_check", "audit_complete"),
    )
    _register_descriptor(desc)

    auth = _make_auth_context(roles=("admin",))

    promo_req = SourcePromotionRequest(
        source_id="src-1",
        target_readiness="production",
        evidence=("staging_check",),  # Missing 'audit_complete'
        request_id="req-cffae068a5c52b2bfc23b7bbd83d773ae5d705b427ad8341299d256dfcf06ffe",
    )

    with pytest.raises(DataError) as captured:
        promote_source(promo_req, auth)
    assert captured.value.code == "VALIDATION_FAILED"


def test_promote_source_success_and_demotion() -> None:
    """Verify that authorized promotion and reversible demotion work correctly."""
    desc = _make_descriptor(
        "src-1",
        readiness="disabled",
        evidence=("staging_check", "audit_complete"),
    )
    _register_descriptor(desc)

    auth = _make_auth_context(roles=("admin",))

    uid = "12b2174e-8e24-47ec-b2f1-feb0a9f75142"
    # 1. Promote to production with valid evidence
    promo_req = SourcePromotionRequest(
        source_id="src-1",
        target_readiness="production",
        evidence=("staging_check", "audit_complete"),
        request_id=f"req-{uid}",
    )
    res_promo = promote_source(promo_req, auth)
    assert res_promo.readiness == "production"

    # 2. Demote back to staging (should not require evidence checklist)
    demote_req = SourcePromotionRequest(
        source_id="src-1",
        target_readiness="staging",
        evidence=("staging_check",),
        request_id=f"req-{uid}",
    )
    res_demote = promote_source(demote_req, auth)
    assert res_demote.readiness == "staging"


def test_promoted_readiness_survives_registry_restart() -> None:
    """Use durable promotion evidence after volatile registries are rebuilt."""
    descriptor = _make_descriptor(
        "src-restart",
        readiness="disabled",
        evidence=("staging_check",),
    )
    _register_descriptor(descriptor)
    auth = _make_auth_context(roles=("admin",))
    promote_source(
        SourcePromotionRequest(
            source_id="src-restart",
            target_readiness="staging",
            evidence=("staging_check",),
            request_id=generate_id("req"),
        ),
        auth,
    )

    _reset_registry()
    _reset_policy_registry()
    _register_descriptor(descriptor)
    plan = evaluate_source_policy(
        MarketDataRequest(
            source_id="src-restart",
            symbol="AAPL",
            data_kind="bars",
            timeframe="1m",
            start=START,
            end=END,
            limit=10,
            use_cache=False,
            quality_failure_behavior="fail",
            workflow_context="research",
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
    )
    assert plan.ordered_sources == ("src-restart",)

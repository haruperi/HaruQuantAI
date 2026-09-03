"""Unit, contract, and scenario tests for Connector Synchronization."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.data.capabilities import SYNC_CONNECTORS_CAPABILITY
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    ConnectorSyncReceipt,
    SyncConnectorsRequest,
    SyncConnectorsSuccess,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.connector_synchronization.config import ConnectorSyncConfig
from app.services.data.connector_synchronization.connector_synchronization import (
    SyncConnectorsService,
    _compute_hash,
    _generate_uuid7,
    data_connect_data_providers,
    data_implement_connector_lifecycle,
    data_plan_incremental_sync,
    data_protect_connector_secrets,
    data_version_data_transforms,
    main,
)
from app.services.data.connector_synchronization.feature import (
    ConnectorSynchronizationFeature,
    feature,
)
from app.services.data.connector_synchronization.manifest import SPEC


def _context(
    feature_instance: ConnectorSynchronizationFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
    """Build a scoped context for testing feature mounting."""
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feature_instance.spec.feature_id)

    def register(
        capability: Any,
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature_instance.spec.feature_id,
            scope=owner_scope,
        )

    return (
        DefaultFeatureContext(
            spec=feature_instance.spec,
            scope=scope,
            resolver=registry.resolve,
            provider_registrar=register,
            event_bus=EventBus(),
        ),
        registry,
        scope,
    )


def test_data_plan_incremental_sync() -> None:
    """Verify FR-DATA-PLAN_INCREMENTAL_SYNC: range, overlap, dedup, and idempotency."""
    profile_id = _generate_uuid7()
    t_start = "2026-01-01T00:00:00.000000Z"
    t_end = "2026-01-02T00:00:00.000000Z"

    plan = data_plan_incremental_sync(
        profile_id=profile_id,
        connector_version="v1.0.0",
        requested_from=t_start,
        requested_to=t_end,
        max_records=5000,
        overlap_window_seconds=120,
        deduplication="KEEP_FIRST",
        revision_policy="COMPARE_OVERLAP",
    )

    assert plan.profile_id == profile_id
    assert plan.connector_version == "v1.0.0"
    assert plan.requested_from == t_start
    assert plan.requested_to == t_end
    assert plan.max_records == 5000
    assert plan.overlap_window_seconds == 120
    assert plan.deduplication == "KEEP_FIRST"
    assert plan.revision_policy == "COMPARE_OVERLAP"
    assert plan.schema_version == 1

    # Invalid timestamp range (requested_to <= requested_from) raises ValueError
    with pytest.raises(ValueError, match="requested_to"):
        data_plan_incremental_sync(
            profile_id=profile_id,
            connector_version="v1.0.0",
            requested_from=t_end,
            requested_to=t_start,
            max_records=100,
        )

    # Invalid profile_id UUID raises ValueError
    with pytest.raises(ValueError, match="Invalid profile_id UUID"):
        data_plan_incremental_sync(
            profile_id="invalid-uuid",
            connector_version="v1.0.0",
            requested_from=t_start,
            requested_to=t_end,
            max_records=100,
        )


def test_data_implement_connector_lifecycle() -> None:
    """Verify FR-DATA-IMPLEMENT_CONNECTOR_LIFECYCLE: fetch, checkpoint, normalize, and resume."""
    profile_id = _generate_uuid7()
    plan = data_plan_incremental_sync(
        profile_id=profile_id,
        connector_version="v1.0.0",
        requested_from="2026-01-01T00:00:00.000000Z",
        requested_to="2026-01-02T00:00:00.000000Z",
        max_records=100,
        deduplication="KEEP_FIRST",
    )

    pages = [
        [
            {"id": "rec_1", "timestamp": "2026-01-01T00:00:00.000000Z", "close": 1.10},
            {"id": "rec_2", "timestamp": "2026-01-01T00:01:00.000000Z", "close": 1.11},
        ],
        [
            {"id": "rec_2", "timestamp": "2026-01-01T00:01:00.000000Z", "close": 1.11},
            {"id": "rec_3", "timestamp": "2026-01-01T00:02:00.000000Z", "close": 1.12},
        ],
    ]

    receipt, normalized = data_implement_connector_lifecycle(plan, pages=pages)

    assert receipt.records == 3
    assert len(normalized) == 3
    assert receipt.is_complete is True
    assert len(receipt.content_hash) == 64
    assert receipt.committed_version_id is not None
    assert receipt.schema_version == 1

    # Test REJECT policy
    fail_plan = data_plan_incremental_sync(
        profile_id=profile_id,
        connector_version="v1.0.0",
        requested_from="2026-01-01T00:00:00.000000Z",
        requested_to="2026-01-02T00:00:00.000000Z",
        max_records=100,
        deduplication="REJECT",
    )
    with pytest.raises(ValueError, match="Duplicate record detected"):
        data_implement_connector_lifecycle(fail_plan, pages=pages)


def test_data_version_data_transforms() -> None:
    """Verify FR-DATA-VERSION_DATA_TRANSFORMS: traceable separate version transformations."""
    raw_series_id = _generate_uuid7()
    raw_recs = [
        {
            "id": "s1",
            "timestamp": "2026-01-01T00:00:00.000000Z",
            "open": 2.0,
            "close": 2.0,
        },
        {
            "id": "s2",
            "timestamp": "2026-01-01T00:01:00.000000Z",
            "open": 4.0,
            "close": 4.0,
        },
    ]

    t_id, t_hash, t_recs, manifest = data_version_data_transforms(
        raw_series_id=raw_series_id,
        transform_kind="SPLIT_ADJUSTMENT",
        transformation_params={"factor": 0.5},
        raw_records=raw_recs,
    )

    assert t_id != raw_series_id
    assert len(t_hash) == 64
    assert t_recs[0]["close"] == 1.0
    assert t_recs[1]["close"] == 2.0
    assert t_recs[0]["_transform_kind"] == "SPLIT_ADJUSTMENT"
    assert manifest["raw_series_id"] == raw_series_id
    assert manifest["transformed_version_id"] == t_id
    assert manifest["parameters"] == {"factor": 0.5}

    # Verify invalid raw_series_id raises ValueError
    with pytest.raises(ValueError, match="Invalid raw_series_id UUID"):
        data_version_data_transforms(
            raw_series_id="not-a-uuid",
            transform_kind="CORPORATE_ACTION",
            transformation_params={"factor": 1.0},
            raw_records=raw_recs,
        )


def test_data_connect_data_providers() -> None:
    """Verify FR-DATA-CONNECT_DATA_PROVIDERS: provider throttling, cursor pagination, and outage handling."""
    res = data_connect_data_providers(
        provider_id="mt5",
        symbol="EURUSD",
        requested_range=("2026-01-01T00:00:00.000000Z", "2026-01-02T00:00:00.000000Z"),
        rate_limit=50,
        rate_window_seconds=60,
        simulated_pages=3,
        records_per_page=5,
    )

    assert res["provider_id"] == "mt5"
    assert res["symbol"] == "EURUSD"
    assert res["pages_count"] == 3
    assert res["total_records"] == 15
    assert res["is_complete"] is True
    assert res["rate_governance"]["rate_limit"] == 50

    # Test simulated provider outage
    with pytest.raises(RuntimeError, match="outage encountered at page 2"):
        data_connect_data_providers(
            provider_id="mt5",
            symbol="EURUSD",
            requested_range=(
                "2026-01-01T00:00:00.000000Z",
                "2026-01-02T00:00:00.000000Z",
            ),
            simulated_pages=3,
            simulate_outage_at_page=2,
        )


def test_data_protect_connector_secrets() -> None:
    """Verify FR-DATA-PROTECT_CONNECTOR_SECRETS: opaque secret ID isolation without leak."""
    cred_ref = _generate_uuid7()
    secret_store = {
        cred_ref: {
            "token": "SECRET_VAL",  # pragma: allowlist secret
            "secret_key": "HIDDEN_PASSWORD",  # pragma: allowlist secret
        }
    }

    is_valid, log_msg, meta = data_protect_connector_secrets(
        "mt5", cred_ref, secret_store
    )
    assert is_valid is True
    assert cred_ref in log_msg
    assert "SECRET_VAL" not in log_msg
    assert "HIDDEN_PASSWORD" not in log_msg
    assert meta["credential_ref"] == cred_ref
    assert meta["is_isolated"] is True
    assert "token" not in meta

    # Missing secret in store raises KeyError
    other_ref = _generate_uuid7()
    with pytest.raises(KeyError, match="not found in workspace secret store"):
        data_protect_connector_secrets("mt5", other_ref, secret_store)

    # Invalid UUID format raises ValueError
    with pytest.raises(ValueError, match="Invalid opaque credential_ref UUID"):
        data_protect_connector_secrets("mt5", "invalid-cred", secret_store)


@pytest.mark.asyncio
async def test_sync_connectors_service_plan_fetch_commit() -> None:
    """Verify SyncConnectorsService executing PLAN, FETCH, and COMMIT."""
    service = SyncConnectorsService()
    profile_id = _generate_uuid7()
    req_id = _generate_uuid7()
    cap_id = _generate_uuid7()

    # 1. PLAN operation
    plan_req = SyncConnectorsRequest(
        request_id=req_id,
        capability_snapshot_id=cap_id,
        operation="PLAN",
        profile_id=profile_id,
        requested_from="2026-01-01T00:00:00.000000Z",
        requested_to="2026-01-02T00:00:00.000000Z",
        max_records=1000,
        overlap_window_seconds=120,
    )
    plan_res = await service.sync_connectors(plan_req)
    assert isinstance(plan_res, SyncConnectorsSuccess)
    assert plan_res.plan is not None
    plan = plan_res.plan

    # 2. FETCH operation
    fetch_req = SyncConnectorsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=cap_id,
        operation="FETCH",
        plan=plan,
    )
    fetch_res = await service.sync_connectors(fetch_req)
    assert isinstance(fetch_res, SyncConnectorsSuccess)
    assert fetch_res.receipt is not None
    receipt = fetch_res.receipt

    # 3. COMMIT operation
    commit_req = SyncConnectorsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=cap_id,
        operation="COMMIT",
        plan=plan,
        receipt=receipt,
    )
    commit_res = await service.sync_connectors(commit_req)
    assert isinstance(commit_res, SyncConnectorsSuccess)
    assert commit_res.outcome == "SUCCESS"


@pytest.mark.asyncio
async def test_sync_connectors_service_error_handling() -> None:
    """Verify SyncConnectorsService error handling returns DataFailure."""
    service = SyncConnectorsService()
    cap_id = _generate_uuid7()

    # Incomplete receipt commit returns DataFailure
    incomplete_receipt = ConnectorSyncReceipt(
        receipt_id=_generate_uuid7(),
        records=5,
        is_complete=False,
        content_hash=_compute_hash("test"),
    )
    plan = data_plan_incremental_sync(
        profile_id=_generate_uuid7(),
        connector_version="v1.0.0",
        requested_from="2026-01-01T00:00:00.000000Z",
        requested_to="2026-01-02T00:00:00.000000Z",
        max_records=50,
    )
    commit_req = SyncConnectorsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=cap_id,
        operation="COMMIT",
        plan=plan,
        receipt=incomplete_receipt,
    )
    res = await service.sync_connectors(commit_req)
    assert isinstance(res, DataFailure)
    assert res.problem.status == 409
    assert res.code == "DATA_VERSION_CONFLICT"
    assert "Incomplete" in res.problem.title


@pytest.mark.asyncio
async def test_feature_lifecycle_mount() -> None:
    """Verify ConnectorSynchronizationFeature mount lifecycle and provider registration."""
    feat = feature()
    assert isinstance(feat, ConnectorSynchronizationFeature)
    assert feat.spec == SPEC
    assert feat.spec.feature_id == "FEAT-DATA-SYNC_CONNECTORS"
    assert SYNC_CONNECTORS_CAPABILITY in feat.spec.provides

    ctx, registry, _ = _context(feat)
    config = {
        "default_overlap_window_seconds": 600,
        "default_deduplication_policy": "KEEP_LAST",
        "default_revision_policy": "FULL_RESCAN",
        "max_records_per_page": 20000,
        "max_rate_limit_per_window": 50,
        "rate_limit_window_seconds": 30,
        "strict_secret_isolation": True,
    }

    await feat.mount(ctx, config)
    provided = registry.resolve(SYNC_CONNECTORS_CAPABILITY)
    assert provided is feat.service
    assert feat.service is not None
    assert feat.service.config.default_overlap_window_seconds == 600
    assert feat.service.config.default_deduplication_policy == "KEEP_LAST"
    assert feat.service.config.default_revision_policy == "FULL_RESCAN"


def test_config_validation() -> None:
    """Verify ConnectorSyncConfig bounds and literal validation."""
    # Valid config
    cfg = ConnectorSyncConfig(default_overlap_window_seconds=100)
    assert cfg.default_overlap_window_seconds == 100

    # Negative overlap window
    with pytest.raises(
        ValueError, match="default_overlap_window_seconds must be non-negative"
    ):
        ConnectorSyncConfig(default_overlap_window_seconds=-1)

    # Invalid max_records_per_page
    with pytest.raises(ValueError, match="max_records_per_page must be at least 1"):
        ConnectorSyncConfig(max_records_per_page=0)

    # Invalid deduplication policy
    with pytest.raises(ValueError, match="Invalid default_deduplication_policy"):
        ConnectorSyncConfig(default_deduplication_policy="INVALID_POLICY")  # type: ignore[arg-type]

    # Invalid revision policy
    with pytest.raises(ValueError, match="Invalid default_revision_policy"):
        ConnectorSyncConfig(default_revision_policy="INVALID_REV")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_feature_lifecycle_mount_with_config_object() -> None:
    """Verify feature mount with ConnectorSyncConfig object."""
    feat = ConnectorSynchronizationFeature()
    ctx, registry, _ = _context(feat)
    cfg = ConnectorSyncConfig(default_overlap_window_seconds=120)
    await feat.mount(ctx, cfg)
    provided = registry.resolve(SYNC_CONNECTORS_CAPABILITY)
    assert provided is feat.service
    assert feat.service is not None
    assert feat.service.config.default_overlap_window_seconds == 120


@pytest.mark.asyncio
async def test_feature_lifecycle_mount_type_errors() -> None:
    """Verify TypeError raised when mount receives invalid configuration types."""
    feat = feature()
    ctx, _, _ = _context(feat)

    type_error_cases = [
        (
            {"default_overlap_window_seconds": "invalid"},
            "default_overlap_window_seconds must be an integer",
        ),
        (
            {"default_deduplication_policy": 123},
            "default_deduplication_policy must be a string",
        ),
        ({"default_revision_policy": 456}, "default_revision_policy must be a string"),
        ({"max_records_per_page": "ten"}, "max_records_per_page must be an integer"),
        (
            {"max_rate_limit_per_window": 1.5},
            "max_rate_limit_per_window must be an integer",
        ),
        (
            {"rate_limit_window_seconds": "60"},
            "rate_limit_window_seconds must be an integer",
        ),
        (
            {"strict_secret_isolation": "yes"},  # pragma: allowlist secret
            "strict_secret_isolation must be a boolean",
        ),
    ]
    for bad_cfg, expected_msg in type_error_cases:
        with pytest.raises(TypeError, match=expected_msg):
            await feat.mount(ctx, bad_cfg)


@pytest.mark.asyncio
async def test_sync_connectors_exception_handling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify sync_connectors wraps unexpected exceptions into DataFailure."""
    service = SyncConnectorsService()

    def _broken_handle_plan(*args: Any, **kwargs: Any) -> Any:
        msg = "Simulated unexpected crash"
        raise RuntimeError(msg)

    monkeypatch.setattr(service, "_handle_plan", _broken_handle_plan)
    req = SyncConnectorsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="PLAN",
        profile_id=_generate_uuid7(),
        requested_from="2026-01-01T00:00:00.000000Z",
        requested_to="2026-01-02T00:00:00.000000Z",
        max_records=1000,
    )
    res = await service.sync_connectors(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_FEED_UNAVAILABLE"
    assert "Simulated unexpected crash" in res.problem.detail


@pytest.mark.asyncio
async def test_main_scenario_harness() -> None:
    """Verify execution of standalone main usage scenarios."""
    await main()


def test_connector_sync_persistence() -> None:
    """Verify ConnectorSyncPersistence methods."""
    from app.contracts.data.models import ConnectorSyncPlan, ConnectorSyncReceipt
    from app.services.data.connector_synchronization._persistence import (
        ConnectorSyncPersistence,
    )

    store = ConnectorSyncPersistence()
    plan_id = _generate_uuid7()
    plan = ConnectorSyncPlan(
        plan_id=plan_id,
        profile_id=_generate_uuid7(),
        connector_version="1.0.0",
        requested_from="2026-01-01T00:00:00.000000Z",
        requested_to="2026-01-02T00:00:00.000000Z",
        max_records=100,
        overlap_window_seconds=60,
        deduplication="KEEP_FIRST",
    )
    store.save_plan(plan)
    assert store.get_plan(plan_id) == plan
    assert len(store.get_all_plans()) == 1

    receipt_id = _generate_uuid7()
    receipt = ConnectorSyncReceipt(
        receipt_id=receipt_id,
        records=10,
        provider_revision_ids=(),
        next_cursor="c1",
        is_complete=True,
        content_hash="0" * 64,
        committed_version_id=None,
    )
    store.save_receipt(receipt)
    assert store.get_receipt(receipt_id) == receipt
    assert len(store.get_all_receipts()) == 1

    store.set_checkpoint("conn1", "cp1")
    assert store.get_checkpoint("conn1") == "cp1"
    assert store.get_checkpoint("unknown") is None

    store.clear()
    assert len(store.get_all_plans()) == 0

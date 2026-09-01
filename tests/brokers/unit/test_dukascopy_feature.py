"""Unit and lifecycle tests for FEAT-BRK-CONNECT_DUKASCOPY."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    PROVIDER_DUKASCOPY_CAPABILITY,
)
from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerOperationRequest,
    BrokerProviderProfile,
    BrokerSessionRef,
    BrokerSessionState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
    ReadProviderStateRequest,
    ReadProviderStateSuccess,
    TransportOrdersRequest,
)
from app.contracts.broker.ports import ProviderBackend
from app.contracts.catalogue.models import ProviderRef
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.brokers.dukascopy.candle_transport import _CandleBatch
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.dukascopy.dukascopy import DukascopyProviderService
from app.services.brokers.dukascopy.feature import DukascopyFeature, feature
from app.services.brokers.dukascopy.manifest import SPEC
from app.services.brokers.provider_gateway.feature import ProviderGatewayFeature
from app.services.brokers.provider_gateway.manifest import SPEC as GW_SPEC


def _gen_id() -> str:
    return str(uuid.uuid7())


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")


def _make_context(
    providers: dict[CapabilityKey[Any], Any] | None = None,
) -> tuple[DefaultFeatureContext, FeatureScope, dict[CapabilityKey[Any], Any]]:
    registry: dict[CapabilityKey[Any], Any] = dict(providers or {})
    scope = FeatureScope(owner_id="FEAT-BRK-CONNECT_DUKASCOPY")
    context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    return context, scope, registry


class _FakeCandleTransport:
    """Fake candle transport returning configurable batches or raising errors."""

    def __init__(
        self,
        batch: _CandleBatch | None = None,
        *,
        fails: bool = False,
    ) -> None:
        if batch is not None:
            self.batch = batch
        else:
            now = datetime.now(UTC)
            base_time_ms = int((now - timedelta(hours=6)).timestamp() * 1000)
            rows = tuple(
                (
                    base_time_ms + i * 3600000,
                    1.0850 + i * 0.001,
                    1.0890 + i * 0.001,
                    1.0840 + i * 0.001,
                    1.0880 + i * 0.001,
                    1000.0 + i * 10,
                )
                for i in range(5)
            )
            self.batch = _CandleBatch(
                rows=rows,
                provider_symbol="EUR/USD",
                provider_interval="1HOUR",
                page_count=1,
                truncated=False,
            )
        self.fails = fails
        self.calls: list[dict[str, Any]] = []

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> _CandleBatch:
        self.calls.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "start": start,
                "end": end,
                "limit": limit,
            }
        )
        if self.fails:
            raise ConnectionError("fake candle transport failure")
        return self.batch


def _make_session_ref(environment: str = "SANDBOX") -> BrokerSessionRef:
    return BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="dukascopy-research-account",
        environment=environment,  # type: ignore[arg-type]
        generation=1,
    )


def test_manifest_spec() -> None:
    """Manifest declares the exact feature ID and capability."""
    assert SPEC.feature_id == "FEAT-BRK-CONNECT_DUKASCOPY"
    assert SPEC.domain == "brokers"
    assert SPEC.provides == frozenset({PROVIDER_DUKASCOPY_CAPABILITY})
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset()
    assert "probe_symbol" in SPEC.config_keys


def test_config_defaults() -> None:
    """DukascopyConfig provides deterministic research defaults."""
    cfg = DukascopyConfig()
    assert cfg.probe_symbol == "EURUSD"
    assert cfg.request_timeout_sec == 30.0
    assert cfg.circuit_failure_threshold == 5
    assert cfg.environment == "SANDBOX"


@pytest.mark.asyncio
async def test_feature_lifecycle_mount_unmount() -> None:
    """Feature mounts into FeatureContext and unmounts cleanly."""
    feat = feature()
    assert isinstance(feat, DukascopyFeature)
    assert feat.service is None

    context, _scope, registry = _make_context()

    await feat.mount(context, DukascopyConfig(probe_symbol="EURUSD"))
    assert feat.service is not None
    assert registry[PROVIDER_DUKASCOPY_CAPABILITY] is feat.service

    await feat.unmount(context)
    assert feat.service is None


def test_provider_backend_protocol() -> None:
    """DukascopyProviderService conforms to the ProviderBackend protocol."""
    service = DukascopyProviderService()
    assert isinstance(service, ProviderBackend)


@pytest.mark.asyncio
async def test_manage_sessions_open_without_probe() -> None:
    """OPEN without probe symbol succeeds immediately."""
    fake_transport = _FakeCandleTransport()
    service = DukascopyProviderService(
        config=DukascopyConfig(probe_symbol="EURUSD"),
        candle_transport=fake_transport,  # type: ignore[arg-type]
    )
    session = _make_session_ref()
    request = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session,
    )
    result = await service.manage_sessions(request)
    assert isinstance(result, ManageSessionsSuccess)
    assert result.state is not None
    assert result.state.connection_state == "READY"
    assert result.readiness is not None
    assert result.readiness.transport == "READY"
    assert result.readiness.trading_permission == "NOT_READY"


@pytest.mark.asyncio
async def test_manage_sessions_open_with_successful_probe() -> None:
    """OPEN with valid probe symbol verifies connectivity."""
    fake_transport = _FakeCandleTransport()
    service = DukascopyProviderService(
        config=DukascopyConfig(probe_symbol="EURUSD"),
        candle_transport=fake_transport,  # type: ignore[arg-type]
    )
    session = _make_session_ref()
    request = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session,
    )
    result = await service.manage_sessions(request)
    assert isinstance(result, ManageSessionsSuccess)
    assert len(fake_transport.calls) == 1
    assert fake_transport.calls[0]["symbol"] == "EURUSD"


@pytest.mark.asyncio
async def test_manage_sessions_open_with_failing_probe() -> None:
    """OPEN with failing probe returns BROKER_SESSION_NOT_READY."""
    fake_transport = _FakeCandleTransport(fails=True)
    service = DukascopyProviderService(
        config=DukascopyConfig(probe_symbol="EURUSD"),
        candle_transport=fake_transport,  # type: ignore[arg-type]
    )
    session = _make_session_ref()
    request = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session,
    )
    result = await service.manage_sessions(request)
    assert isinstance(result, BrokerFailure)
    assert result.code == "BROKER_SESSION_NOT_READY"


@pytest.mark.asyncio
async def test_manage_sessions_rejects_non_sandbox_environment() -> None:
    """Manage sessions fails closed if environment is not SANDBOX."""
    service = DukascopyProviderService()
    session = _make_session_ref(environment="LIVE")
    request = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session,
    )
    result = await service.manage_sessions(request)
    assert isinstance(result, BrokerFailure)
    assert result.code == "BROKER_ENVIRONMENT_MISMATCH"


@pytest.mark.asyncio
async def test_manage_sessions_transition_reconnect_assess_close() -> None:
    """Exercise transition, reconnect, assess readiness, and close operations."""
    fake_transport = _FakeCandleTransport()
    service = DukascopyProviderService(
        config=DukascopyConfig(probe_symbol="EURUSD"),
        candle_transport=fake_transport,  # type: ignore[arg-type]
    )
    session = _make_session_ref()

    # TRANSITION
    state_to_set = BrokerSessionState(
        session_id=session.session_id,
        generation=session.generation,
        connection_state="DEGRADED",
        transitioned_at=_utc_now(),
    )
    trans_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="TRANSITION",
        session=session,
        state=state_to_set,
    )
    trans_res = await service.manage_sessions(trans_req)
    assert isinstance(trans_res, ManageSessionsSuccess)
    assert trans_res.state is not None
    assert trans_res.state.connection_state == "DEGRADED"

    # RECONNECT
    rec_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="RECONNECT",
        session=session,
    )
    rec_res = await service.manage_sessions(rec_req)
    assert isinstance(rec_res, ManageSessionsSuccess)
    assert rec_res.state is not None
    assert rec_res.state.connection_state == "READY"

    # ASSESS_READINESS
    ass_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="ASSESS_READINESS",
        session=session,
    )
    ass_res = await service.manage_sessions(ass_req)
    assert isinstance(ass_res, ManageSessionsSuccess)
    assert ass_res.readiness is not None
    assert ass_res.readiness.transport == "READY"

    # CLOSE
    cls_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="CLOSE",
        session=session,
    )
    cls_res = await service.manage_sessions(cls_req)
    assert isinstance(cls_res, ManageSessionsSuccess)
    assert cls_res.state is not None
    assert cls_res.state.connection_state == "DISCONNECTED"


@pytest.mark.asyncio
async def test_read_provider_state_page_history() -> None:
    """PAGE_HISTORY returns genuine historical candles mapped to BrokerHistoryPage."""
    fake_transport = _FakeCandleTransport()
    service = DukascopyProviderService(
        config=DukascopyConfig(probe_symbol="EURUSD"),
        candle_transport=fake_transport,  # type: ignore[arg-type]
    )
    session = _make_session_ref()
    request = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="PAGE_HISTORY",
        session=session,
        page_size=10,
    )
    result = await service.read_provider_state(request)
    assert isinstance(result, ReadProviderStateSuccess)
    assert result.page is not None
    assert result.page.requested_count == 10
    assert result.page.returned_count == 5
    assert len(result.page.records) == 5
    rec = result.page.records[0]
    assert rec.provider_id == "dukascopy"
    assert rec.record["symbol"] == "EURUSD"
    assert rec.record["provenance"]["provider"] == "dukascopy"
    assert rec.record["provenance"]["research_only"] is True


@pytest.mark.asyncio
async def test_read_provider_state_page_history_transport_failure() -> None:
    """PAGE_HISTORY maps transport failure into BROKER_VALIDATION_FAILED."""
    fake_transport = _FakeCandleTransport(fails=True)
    service = DukascopyProviderService(
        config=DukascopyConfig(probe_symbol="EURUSD"),
        candle_transport=fake_transport,  # type: ignore[arg-type]
    )
    session = _make_session_ref()
    request = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="PAGE_HISTORY",
        session=session,
        page_size=10,
    )
    result = await service.read_provider_state(request)
    assert isinstance(result, BrokerFailure)
    assert result.code == "BROKER_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_read_provider_state_rejects_non_sandbox() -> None:
    """Read provider state rejects non-sandbox environment."""
    service = DukascopyProviderService()
    session = _make_session_ref(environment="TESTNET")
    request = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="PAGE_HISTORY",
        session=session,
    )
    result = await service.read_provider_state(request)
    assert isinstance(result, BrokerFailure)
    assert result.code == "BROKER_ENVIRONMENT_MISMATCH"


@pytest.mark.asyncio
async def test_read_provider_state_unsupported_operations() -> None:
    """Non-history read operations are deterministically rejected."""
    service = DukascopyProviderService()
    session = _make_session_ref()

    for op in ("READ_ACCOUNT", "READ_TRADING_STATE"):
        req = ReadProviderStateRequest(
            request_id=_gen_id(),
            capability_snapshot_id=_gen_id(),
            operation=op,  # type: ignore[arg-type]
            session=session,
        )
        res = await service.read_provider_state(req)
        assert isinstance(res, BrokerFailure)
        assert res.code == "BROKER_PROFILE_UNSUPPORTED"


@pytest.mark.asyncio
async def test_transport_orders_unsupported() -> None:
    """All order transport operations are rejected with BROKER_PROFILE_UNSUPPORTED."""
    service = DukascopyProviderService()
    session = _make_session_ref()

    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=session,
        operation="SUBMIT_ORDER",
        provider_symbol="EURUSD",
        normalized_quantity="1",
        policy={"type": "MARKET"},
        risk_authorization_id=_gen_id(),
        idempotency_key=_gen_id(),
        attempt_no=1,
        request_hash="a" * 64,
    )
    req = TransportOrdersRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="SUBMIT",
        operation_request=op_req,
    )
    res = await service.transport_orders(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "BROKER_PROFILE_UNSUPPORTED"


@pytest.mark.asyncio
async def test_gateway_dispatch_to_dukascopy() -> None:
    """ProviderGateway dispatches directly to mounted DukascopyFeature."""
    registry: dict[CapabilityKey[Any], Any] = {}
    scope = FeatureScope(owner_id="test-scope")

    gw_context = DefaultFeatureContext(
        spec=GW_SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    dukascopy_context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )

    dukascopy_feat = feature()
    await dukascopy_feat.mount(
        dukascopy_context, DukascopyConfig(probe_symbol="EURUSD")
    )
    fake_transport = _FakeCandleTransport()
    assert dukascopy_feat._service is not None
    dukascopy_feat._service._candle_transport = fake_transport

    gateway_feat = ProviderGatewayFeature()
    await gateway_feat.mount(gw_context, {})

    gw_service = gateway_feat.service
    assert gw_service is not None

    profile = BrokerProviderProfile(
        profile_id=_gen_id(),
        version=1,
        provider=ProviderRef(
            provider_id=_gen_id(),
            provider_name="Dukascopy",
        ),
        kind="DUKASCOPY",
        account_ref="acc-dukascopy",
        environment="SANDBOX",
        api_version_range=">=1.0.0",
        content_hash="0" * 64,
    )
    gw_service.register_profile(profile)

    session_ref = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=profile.profile_id,
        profile_version=1,
        account_ref=profile.account_ref,
        environment=profile.environment,
        generation=1,
    )

    # Dispatch manage_sessions through gateway
    manage_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session_ref,
    )
    manage_res = await gw_service.manage_sessions(manage_req)
    assert isinstance(manage_res, ManageSessionsSuccess)
    assert manage_res.state is not None
    assert manage_res.state.connection_state == "READY"

    # Dispatch read_provider_state through gateway
    read_req = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="PAGE_HISTORY",
        session=session_ref,
        page_size=5,
    )
    read_res = await gw_service.read_provider_state(read_req)
    assert isinstance(read_res, ReadProviderStateSuccess)
    assert read_res.page is not None
    assert read_res.page.returned_count == 5
    assert read_res.page.records[0].provider_id == "dukascopy"

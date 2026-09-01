"""Unit and lifecycle tests for FEAT-BRK-CONNECT_METATRADER."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    PROVIDER_METATRADER_CAPABILITY,
)
from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerOperationRequest,
    BrokerSessionRef,
    BrokerSessionState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
    ReadProviderStateRequest,
    ReadProviderStateSuccess,
    TransportOrdersRequest,
    TransportOrdersSuccess,
)
from app.contracts.broker.ports import ProviderBackend
from app.contracts.catalogue.models import InstrumentRef
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.brokers.metatrader.config import MetaTraderConfig
from app.services.brokers.metatrader.feature import MetaTraderFeature, feature
from app.services.brokers.metatrader.manifest import SPEC
from app.services.brokers.metatrader.metatrader import MetaTraderProviderService
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
    scope = FeatureScope(owner_id="FEAT-BRK-CONNECT_METATRADER")
    context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    return context, scope, registry


class _FakeMT5Transport:
    """Fake transport returning configurable responses or raising errors."""

    def __init__(
        self,
        *,
        fails: bool = False,
        error: Exception | None = None,
    ) -> None:
        self.fails = fails
        self.error = error
        self.calls: list[dict[str, Any]] = []
        self._connected = False
        self._closed = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        if self.fails:
            raise (self.error or ConnectionError("MetaTrader connect failed"))
        self._connected = True
        return True

    async def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        self.calls.append({"name": name, "args": args, "kwargs": kwargs})
        if self.fails:
            raise (self.error or ConnectionError(f"MetaTrader {name} failed"))
        return {}

    async def close(self) -> None:
        self._closed = True
        self._connected = False


# ==============================================================================
# 1. Manifest & Config Specification Tests
# ==============================================================================


def test_manifest_spec() -> None:
    assert SPEC.feature_id == "FEAT-BRK-CONNECT_METATRADER"
    assert SPEC.domain == "brokers"
    assert PROVIDER_METATRADER_CAPABILITY in SPEC.provides
    assert len(SPEC.provides) == 1
    assert len(SPEC.requires) == 0
    assert SPEC.state is None
    assert "probe_symbol" in SPEC.config_keys
    assert "request_timeout_sec" in SPEC.config_keys
    assert "circuit_failure_threshold" in SPEC.config_keys
    assert "login" in SPEC.config_keys
    assert "password" in SPEC.config_keys
    assert "server" in SPEC.config_keys
    assert "terminal_path" in SPEC.config_keys


def test_config_defaults() -> None:
    cfg = MetaTraderConfig()
    assert cfg.environment == "DEMO"
    assert cfg.probe_symbol == "EURUSD"
    assert cfg.request_timeout_sec == 30.0
    assert cfg.connect_timeout_sec == 10.0
    assert cfg.circuit_failure_threshold == 5
    assert cfg.circuit_recovery_timeout_sec == 30.0
    assert cfg.circuit_half_open_max_calls == 1
    assert cfg.stream_buffer_size == 1000


# ==============================================================================
# 2. Feature Mount & Unmount Lifecycle Tests
# ==============================================================================


def test_feature_factory() -> None:
    feat = feature()
    assert isinstance(feat, MetaTraderFeature)
    assert feat.spec == SPEC
    assert feat.service is None


@pytest.mark.asyncio
async def test_feature_mount_and_unmount() -> None:
    context, _scope, registry = _make_context()
    feat = feature()

    await feat.mount(context, {"probe_symbol": "EURUSD", "environment": "DEMO"})
    assert feat.service is not None
    assert PROVIDER_METATRADER_CAPABILITY in registry
    assert isinstance(registry[PROVIDER_METATRADER_CAPABILITY], ProviderBackend)

    await feat.unmount(context)
    assert feat.service is None


# ==============================================================================
# 3. ProviderBackend Protocol Conformance Tests
# ==============================================================================


def test_provider_backend_conformance() -> None:
    svc = MetaTraderProviderService()
    assert isinstance(svc, ProviderBackend)


# ==============================================================================
# 4. Session Management Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_manage_sessions_open_success() -> None:
    svc = MetaTraderProviderService(config=MetaTraderConfig(probe_symbol=None))
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=sess,
    )
    res = await svc.manage_sessions(req)
    assert isinstance(res, ManageSessionsSuccess)
    assert res.request_id == req_id
    assert res.state is not None
    assert res.state.connection_state == "READY"
    assert res.readiness is not None
    assert res.readiness.transport == "READY"
    assert res.readiness.authentication == "READY"
    assert res.readiness.trading_permission == "READY"


@pytest.mark.asyncio
async def test_manage_sessions_environment_mismatch() -> None:
    svc = MetaTraderProviderService()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="SIMULATION",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=sess,
    )
    res = await svc.manage_sessions(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "BROKER_ENVIRONMENT_MISMATCH"


@pytest.mark.asyncio
async def test_manage_sessions_transition() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    target_state = BrokerSessionState(
        session_id=sess.session_id,
        generation=1,
        connection_state="DEGRADED",
        transitioned_at=_utc_now(),
    )
    req = ManageSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="TRANSITION",
        session=sess,
        state=target_state,
    )
    res = await svc.manage_sessions(req)
    assert isinstance(res, ManageSessionsSuccess)
    assert res.state == target_state


@pytest.mark.asyncio
async def test_manage_sessions_reconnect() -> None:
    svc = MetaTraderProviderService(config=MetaTraderConfig(probe_symbol=None))
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="RECONNECT",
        session=sess,
    )
    res = await svc.manage_sessions(req)
    assert isinstance(res, ManageSessionsSuccess)
    assert res.state is not None
    assert res.state.connection_state == "READY"


@pytest.mark.asyncio
async def test_manage_sessions_assess_readiness() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="ASSESS_READINESS",
        session=sess,
    )
    res = await svc.manage_sessions(req)
    assert isinstance(res, ManageSessionsSuccess)
    assert res.readiness is not None
    assert res.readiness.environment_verified is True


@pytest.mark.asyncio
async def test_manage_sessions_close() -> None:
    fake_transport = _FakeMT5Transport()
    fake_transport._connected = True
    svc = MetaTraderProviderService(transport=fake_transport)  # type: ignore[arg-type]
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="CLOSE",
        session=sess,
    )
    res = await svc.manage_sessions(req)
    assert isinstance(res, ManageSessionsSuccess)
    assert res.state is not None
    assert res.state.connection_state == "DISCONNECTED"
    assert fake_transport._closed is True


# ==============================================================================
# 5. Read Provider State Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_read_account_state() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ReadProviderStateRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="READ_ACCOUNT",
        session=sess,
    )
    res = await svc.read_provider_state(req)
    assert isinstance(res, ReadProviderStateSuccess)
    assert res.account is not None
    assert res.account.account_ref == "test_account"
    assert res.account.currency == "USD"
    assert res.account.equity.amount == "10000"


@pytest.mark.asyncio
async def test_read_trading_state() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ReadProviderStateRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="READ_TRADING_STATE",
        session=sess,
    )
    res = await svc.read_provider_state(req)
    assert isinstance(res, ReadProviderStateSuccess)
    assert res.trading_state is not None
    assert res.trading_state.session_id == sess.session_id


@pytest.mark.asyncio
async def test_read_market_state() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    inst = InstrumentRef(instrument_id=_gen_id())
    req = ReadProviderStateRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="READ_MARKET",
        session=sess,
        instrument=inst,
    )
    res = await svc.read_provider_state(req)
    assert isinstance(res, ReadProviderStateSuccess)
    assert res.market is not None
    assert res.market.provider_symbol == "EURUSD"
    assert res.market.bid is not None
    assert res.market.ask is not None


@pytest.mark.asyncio
async def test_page_history() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ReadProviderStateRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="PAGE_HISTORY",
        session=sess,
        page_size=50,
    )
    res = await svc.read_provider_state(req)
    assert isinstance(res, ReadProviderStateSuccess)
    assert res.page is not None
    assert res.page.requested_count == 50
    assert len(res.page.records) > 0


@pytest.mark.asyncio
async def test_normalize_event() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ReadProviderStateRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="NORMALIZE_EVENT",
        session=sess,
        raw_event={"symbol": "EURUSD", "bid": "1.08500", "ask": "1.08510"},
    )
    res = await svc.read_provider_state(req)
    assert isinstance(res, ReadProviderStateSuccess)
    assert res.market is not None
    assert res.market.provider_symbol == "EURUSD"
    assert res.market.bid == "1.085"
    assert res.market.ask == "1.0851"


# ==============================================================================
# 6. Order Transport Tests (DEMO mutations, LIVE denial, Unknown outcome)
# ==============================================================================


@pytest.mark.asyncio
async def test_transport_orders_check_success() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=sess,
        operation="SUBMIT_ORDER",
        provider_symbol="EURUSD",
        normalized_quantity="1",
        policy={},
        risk_authorization_id=_gen_id(),
        idempotency_key="idemp_1",
        attempt_no=1,
        request_hash="0" * 64,
    )
    req = TransportOrdersRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="VALIDATE_REQUEST",
        operation_request=op_req,
    )
    res = await svc.transport_orders(req)
    assert isinstance(res, TransportOrdersSuccess)
    assert res.receipt is not None
    assert res.receipt.outcome == "ACCEPTED"


@pytest.mark.asyncio
async def test_transport_orders_demo_submit_success() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=sess,
        operation="SUBMIT_ORDER",
        provider_symbol="EURUSD",
        normalized_quantity="1",
        policy={},
        risk_authorization_id=_gen_id(),
        idempotency_key="idemp_1",
        attempt_no=1,
        request_hash="0" * 64,
    )
    req = TransportOrdersRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="SUBMIT",
        operation_request=op_req,
    )
    res = await svc.transport_orders(req)
    assert isinstance(res, TransportOrdersSuccess)
    assert res.receipt is not None
    assert res.receipt.outcome == "ACCEPTED"


@pytest.mark.asyncio
async def test_transport_orders_live_denial() -> None:
    svc = MetaTraderProviderService()
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="LIVE",
        generation=1,
    )
    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=sess,
        operation="SUBMIT_ORDER",
        provider_symbol="EURUSD",
        normalized_quantity="1",
        policy={},
        risk_authorization_id=_gen_id(),
        idempotency_key="idemp_1",
        attempt_no=1,
        request_hash="0" * 64,
    )
    req = TransportOrdersRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="SUBMIT",
        operation_request=op_req,
    )
    res = await svc.transport_orders(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "BROKER_OPERATION_REJECTED"


@pytest.mark.asyncio
async def test_transport_orders_unknown_outcome() -> None:
    fake_transport = _FakeMT5Transport(
        fails=True, error=ConnectionError("Transport dropped")
    )
    svc = MetaTraderProviderService(transport=fake_transport)  # type: ignore[arg-type]
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=sess,
        operation="SUBMIT_ORDER",
        provider_symbol="EURUSD",
        normalized_quantity="1",
        policy={},
        risk_authorization_id=_gen_id(),
        idempotency_key="idemp_1",
        attempt_no=1,
        request_hash="0" * 64,
    )
    req = TransportOrdersRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="SUBMIT",
        operation_request=op_req,
    )
    res = await svc.transport_orders(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "BROKER_OUTCOME_UNKNOWN"


# ==============================================================================
# 7. Provider Gateway Integration Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_gateway_dispatch_to_metatrader() -> None:
    context, _scope, registry = _make_context()
    mt5_feat = feature()
    await mt5_feat.mount(context, {"probe_symbol": "EURUSD", "environment": "DEMO"})

    gw_scope = FeatureScope(owner_id="FEAT-BRK-DISPATCH_PROVIDERS")
    gw_context = DefaultFeatureContext(
        spec=GW_SPEC,
        scope=gw_scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    gw_feat = ProviderGatewayFeature()
    await gw_feat.mount(gw_context, {})

    from app.contracts.broker.capabilities import (
        MANAGE_SESSIONS_CAPABILITY,
        READ_PROVIDER_STATE_CAPABILITY,
    )

    manage_sessions_cap = registry[MANAGE_SESSIONS_CAPABILITY]
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    assert gw_feat.service is not None
    gw_feat.service.bind_profile(sess.profile_id, PROVIDER_METATRADER_CAPABILITY)
    req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="ASSESS_READINESS",
        session=sess,
    )
    res = await manage_sessions_cap.manage_sessions(req)
    assert isinstance(res, ManageSessionsSuccess)

    read_cap = registry[READ_PROVIDER_STATE_CAPABILITY]
    read_req = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="READ_ACCOUNT",
        session=sess,
    )
    read_res = await read_cap.read_provider_state(read_req)
    assert isinstance(read_res, ReadProviderStateSuccess)

    await mt5_feat.unmount(context)


# ==============================================================================
# 8. Error Handling & Probe Failures
# ==============================================================================


@pytest.mark.asyncio
async def test_open_probe_failure() -> None:
    fake_transport = _FakeMT5Transport(
        fails=True, error=ConnectionError("MT5 initialize failed")
    )
    svc = MetaTraderProviderService(
        config=MetaTraderConfig(probe_symbol="EURUSD"),
        transport=fake_transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="test_account",
        environment="DEMO",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=sess,
    )
    res = await svc.manage_sessions(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "BROKER_SESSION_NOT_READY"


# ==============================================================================
# 9. Resource Management & Cleanup
# ==============================================================================


@pytest.mark.asyncio
async def test_cleanup_and_remount_isolation() -> None:
    context, _scope, _registry = _make_context()
    feat1 = feature()
    await feat1.mount(context, {"probe_symbol": "EURUSD"})
    svc1 = feat1.service
    assert svc1 is not None

    await feat1.unmount(context)
    assert feat1.service is None

    feat2 = feature()
    await feat2.mount(context, {"probe_symbol": "EURUSD"})
    svc2 = feat2.service
    assert svc2 is not None
    assert svc2 is not svc1
    await feat2.unmount(context)

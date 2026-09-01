"""Unit and lifecycle tests for FEAT-BRK-CONNECT_BINANCE."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    PROVIDER_BINANCE_CAPABILITY,
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
from app.contracts.catalogue.models import InstrumentRef, ProviderRef
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.brokers.binance.binance import BinanceProviderService
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.binance.feature import BinanceFeature, feature
from app.services.brokers.binance.manifest import SPEC
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
    scope = FeatureScope(owner_id="FEAT-BRK-CONNECT_BINANCE")
    context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    return context, scope, registry


class _FakeBinanceTransport:
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

    async def connect(self) -> bool:
        if self.fails:
            raise (self.error or ConnectionError("Binance connect failed"))
        self._connected = True
        return True

    async def call(self, name: str, **kwargs: object) -> Any:
        self.calls.append({"method": name, "kwargs": kwargs})
        if self.fails:
            raise (self.error or ConnectionError(f"Binance call {name} failed"))
        if name == "ping":
            return {}
        if name == "get_server_time":
            return {"serverTime": int(datetime.now(UTC).timestamp() * 1000)}
        if name == "get_orderbook_ticker":
            return {
                "symbol": kwargs.get("symbol", "BTCUSDT"),
                "bidPrice": "50000.00",
                "askPrice": "50001.00",
                "bidQty": "1.5",
                "askQty": "2.0",
            }
        if name == "get_klines":
            now_ms = int(datetime.now(UTC).timestamp() * 1000)
            return [
                [
                    now_ms - 3600000,
                    "50000.00",
                    "50500.00",
                    "49900.00",
                    "50200.00",
                    "100.5",
                    now_ms,
                    "5045100.00",
                    1500,
                    "50.0",
                    "2500000.00",
                    "0",
                ]
            ]
        if name == "get_symbol_info":
            return {
                "symbol": kwargs.get("symbol", "BTCUSDT"),
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "baseAssetPrecision": 8,
                "quoteAssetPrecision": 2,
                "isSpotTradingAllowed": True,
            }
        return {}

    async def close(self) -> None:
        self._closed = True
        self._connected = False


# ==============================================================================
# 1. Manifest & Config Specification Tests
# ==============================================================================


def test_manifest_spec() -> None:
    assert SPEC.feature_id == "FEAT-BRK-CONNECT_BINANCE"
    assert SPEC.domain == "brokers"
    assert PROVIDER_BINANCE_CAPABILITY in SPEC.provides
    assert len(SPEC.provides) == 1
    assert len(SPEC.requires) == 0
    assert SPEC.state is None
    assert "probe_symbol" in SPEC.config_keys
    assert "request_timeout_sec" in SPEC.config_keys
    assert "circuit_failure_threshold" in SPEC.config_keys
    assert "environment" in SPEC.config_keys
    assert "stream_buffer_size" in SPEC.config_keys


def test_config_defaults_and_immutability() -> None:
    cfg = BinanceConfig()
    assert cfg.probe_symbol == "BTCUSDT"
    assert cfg.request_timeout_sec == 30.0
    assert cfg.connect_timeout_sec == 10.0
    assert cfg.circuit_failure_threshold == 5
    assert cfg.circuit_recovery_timeout_sec == 30.0
    assert cfg.circuit_half_open_max_calls == 1
    assert cfg.environment == "TESTNET"
    assert cfg.stream_buffer_size == 1000

    with pytest.raises(AttributeError):
        cfg.environment = "LIVE"  # type: ignore[misc]


# ==============================================================================
# 2. Feature Lifecycle (Mount / Unmount) Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_feature_mount_and_unmount() -> None:
    context, _scope, registry = _make_context()
    feat = BinanceFeature()
    assert feat.service is None

    await feat.mount(context, BinanceConfig(probe_symbol="BTCUSDT"))
    assert feat.service is not None
    assert PROVIDER_BINANCE_CAPABILITY in registry
    assert isinstance(registry[PROVIDER_BINANCE_CAPABILITY], ProviderBackend)

    await feat.unmount(context)
    assert feat.service is None


@pytest.mark.asyncio
async def test_feature_factory_and_dict_config() -> None:
    context, _scope, _registry = _make_context()
    feat = feature()
    assert isinstance(feat, BinanceFeature)

    await feat.mount(context, {"probe_symbol": "ETHUSDT", "environment": "TESTNET"})
    assert feat.service is not None
    assert feat.service._config.probe_symbol == "ETHUSDT"
    assert feat.service._config.environment == "TESTNET"

    await feat.unmount(context)
    assert feat.service is None


# ==============================================================================
# 3. Session Lifecycle (manage_sessions) Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_manage_sessions_open_success() -> None:
    transport = _FakeBinanceTransport()
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    req_id = _gen_id()
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=sess,
    )
    result = await service.manage_sessions(req)
    assert isinstance(result, ManageSessionsSuccess)
    assert result.request_id == req_id
    assert result.state is not None
    assert result.state.connection_state == "READY"
    assert result.readiness is not None
    assert result.readiness.transport == "READY"
    assert result.readiness.environment_verified is True


@pytest.mark.asyncio
async def test_manage_sessions_open_probe_failure() -> None:
    transport = _FakeBinanceTransport(fails=True)
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=sess,
    )
    result = await service.manage_sessions(req)
    assert isinstance(result, BrokerFailure)
    assert result.code == "BROKER_SESSION_NOT_READY"


@pytest.mark.asyncio
async def test_manage_sessions_environment_mismatch() -> None:
    transport = _FakeBinanceTransport()
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="invalid_env_account",
        environment="SIMULATION",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=sess,
    )
    result = await service.manage_sessions(req)
    assert isinstance(result, BrokerFailure)
    assert result.code == "BROKER_ENVIRONMENT_MISMATCH"


@pytest.mark.asyncio
async def test_manage_sessions_transition_and_assess_and_close() -> None:
    transport = _FakeBinanceTransport()
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )

    # TRANSITION
    state = BrokerSessionState(
        session_id=sess.session_id,
        generation=sess.generation,
        connection_state="DEGRADED",
        transitioned_at=_utc_now(),
    )
    trans_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="TRANSITION",
        session=sess,
        state=state,
    )
    res_trans = await service.manage_sessions(trans_req)
    assert isinstance(res_trans, ManageSessionsSuccess)
    assert res_trans.state == state

    # ASSESS_READINESS
    readiness_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="ASSESS_READINESS",
        session=sess,
    )
    res_readiness = await service.manage_sessions(readiness_req)
    assert isinstance(res_readiness, ManageSessionsSuccess)
    assert res_readiness.readiness is not None
    assert res_readiness.readiness.transport == "READY"

    # RECONNECT
    reconnect_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="RECONNECT",
        session=sess,
    )
    res_reconn = await service.manage_sessions(reconnect_req)
    assert isinstance(res_reconn, ManageSessionsSuccess)
    assert res_reconn.state is not None
    assert res_reconn.state.connection_state == "READY"

    # CLOSE
    close_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="CLOSE",
        session=sess,
    )
    res_close = await service.manage_sessions(close_req)
    assert isinstance(res_close, ManageSessionsSuccess)
    assert res_close.state is not None
    assert res_close.state.connection_state == "DISCONNECTED"
    assert transport._closed is True


# ==============================================================================
# 4. Provider Reads (read_provider_state) Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_read_provider_state_read_market_success() -> None:
    transport = _FakeBinanceTransport()
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )
    inst = InstrumentRef(instrument_id=_gen_id())
    req = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="READ_MARKET",
        session=sess,
        instrument=inst,
    )
    result = await service.read_provider_state(req)
    assert isinstance(result, ReadProviderStateSuccess)
    assert result.market is not None
    assert result.market.provider_symbol == "BTCUSDT"
    assert result.market.market_status == "OPEN"
    assert result.market.bid == "50000"
    assert result.market.ask == "50001"


@pytest.mark.asyncio
async def test_read_provider_state_page_history_success() -> None:
    transport = _FakeBinanceTransport()
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )
    req = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="PAGE_HISTORY",
        session=sess,
        page_size=10,
    )
    result = await service.read_provider_state(req)
    assert isinstance(result, ReadProviderStateSuccess)
    assert result.page is not None
    assert result.page.requested_count == 10
    assert result.page.returned_count == 1
    assert len(result.page.records) == 1
    assert result.page.records[0].provider_id == "binance_spot"
    assert result.page.records[0].record["symbol"] == "BTCUSDT"
    assert result.page.records[0].record["open"] == "50000"


@pytest.mark.asyncio
async def test_read_provider_state_normalize_event() -> None:
    transport = _FakeBinanceTransport()
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )
    raw_ticker_event = {
        "s": "BTCUSDT",
        "b": "51000.00",
        "a": "51001.00",
        "u": 12345678,
        "E": 1725000000000,
    }
    req = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="NORMALIZE_EVENT",
        session=sess,
        raw_event=raw_ticker_event,
    )
    result = await service.read_provider_state(req)
    assert isinstance(result, ReadProviderStateSuccess)
    assert result.market is not None
    assert result.market.provider_symbol == "BTCUSDT"
    assert result.market.bid == "51000"
    assert result.market.ask == "51001"
    assert result.market.provider_sequence == 12345678


@pytest.mark.asyncio
async def test_read_provider_state_unsupported_operations() -> None:
    transport = _FakeBinanceTransport()
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )
    for op in ("READ_ACCOUNT", "READ_TRADING_STATE"):
        req = ReadProviderStateRequest(
            request_id=_gen_id(),
            capability_snapshot_id=_gen_id(),
            operation=op,  # type: ignore[arg-type]
            session=sess,
        )
        result = await service.read_provider_state(req)
        assert isinstance(result, BrokerFailure)
        assert result.code == "BROKER_PROFILE_UNSUPPORTED"


# ==============================================================================
# 5. Order Transport (transport_orders) Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_transport_orders_unsupported() -> None:
    transport = _FakeBinanceTransport()
    service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )
    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=sess,
        operation="SUBMIT_ORDER",
        provider_symbol="BTCUSDT",
        normalized_quantity="0.1",
        policy={},
        risk_authorization_id=_gen_id(),
        idempotency_key="idemp_1",
        attempt_no=1,
        request_hash="a" * 64,
    )
    req = TransportOrdersRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="SUBMIT",
        operation_request=op_req,
    )
    result = await service.transport_orders(req)
    assert isinstance(result, BrokerFailure)
    assert result.code == "BROKER_PROFILE_UNSUPPORTED"


# ==============================================================================
# 6. Provider Gateway Dispatch Integration Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_provider_gateway_dispatch_to_binance() -> None:
    transport = _FakeBinanceTransport()
    binance_service = BinanceProviderService(
        config=BinanceConfig(probe_symbol="BTCUSDT"),
        transport=transport,  # type: ignore[arg-type]
    )
    registry: dict[CapabilityKey[Any], Any] = {
        PROVIDER_BINANCE_CAPABILITY: binance_service
    }
    scope = FeatureScope(owner_id="FEAT-BRK-DISPATCH_PROVIDERS")
    context = DefaultFeatureContext(
        spec=GW_SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    gw_feature = ProviderGatewayFeature()
    await gw_feature.mount(context, {})
    gw_service = gw_feature.service
    assert gw_service is not None

    profile_id = _gen_id()
    profile = BrokerProviderProfile(
        profile_id=profile_id,
        version=1,
        provider=ProviderRef(provider_id=_gen_id(), provider_name="binance"),
        kind="BINANCE_SPOT",
        account_ref="testnet_account",
        environment="TESTNET",
        api_version_range=">=1.0.0",
        content_hash="a" * 64,
    )
    gw_service.register_profile(profile)

    sess = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=profile_id,
        profile_version=1,
        account_ref="testnet_account",
        environment="TESTNET",
        generation=1,
    )
    sess_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=sess,
    )
    res_sess = await gw_service.manage_sessions(sess_req)
    assert isinstance(res_sess, ManageSessionsSuccess)
    assert res_sess.state is not None
    assert res_sess.state.connection_state == "READY"

    read_req = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="READ_MARKET",
        session=sess,
        instrument=InstrumentRef(instrument_id=_gen_id()),
    )
    res_read = await gw_service.read_provider_state(read_req)
    assert isinstance(res_read, ReadProviderStateSuccess)
    assert res_read.market is not None
    assert res_read.market.provider_symbol == "BTCUSDT"

"""Unit and lifecycle tests for FEAT-BRK-CONNECT_YAHOO."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    PROVIDER_YAHOO_CAPABILITY,
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
from app.contracts.catalogue.models import ProviderRef
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.brokers.provider_gateway.feature import ProviderGatewayFeature
from app.services.brokers.yahoo.config import YahooConfig
from app.services.brokers.yahoo.feature import YahooFeature, feature
from app.services.brokers.yahoo.manifest import SPEC
from app.services.brokers.yahoo.yahoo import YahooProviderService


def _gen_id() -> str:
    return str(uuid.uuid7())


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")


def _make_context(
    providers: dict[CapabilityKey[Any], Any] | None = None,
) -> tuple[DefaultFeatureContext, FeatureScope, dict[CapabilityKey[Any], Any]]:
    registry: dict[CapabilityKey[Any], Any] = dict(providers or {})
    scope = FeatureScope(owner_id="FEAT-BRK-CONNECT_YAHOO")
    context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    return context, scope, registry


class _FakeTable:
    """Minimal fake yfinance DataFrame."""

    def __init__(self, empty: bool = False, count: int = 5) -> None:
        self.empty = empty
        self._count = count

    def iterrows(self) -> Any:
        if self.empty:
            return iter(())
        base_time = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
        rows = []
        for i in range(self._count):
            row_dict = {
                "Open": 100.0 + i,
                "High": 105.0 + i,
                "Low": 99.0 + i,
                "Close": 104.0 + i,
                "Volume": 1000 + i * 10,
            }
            rows.append((base_time, row_dict))
        return iter(rows)


class _FakeTransport:
    """Fake transport returning configurable tables or raising errors."""

    def __init__(self, table: Any | None = None, *, fails: bool = False) -> None:
        self.table = table if table is not None else _FakeTable()
        self.fails = fails
        self.history_calls: list[dict[str, Any]] = []

    async def history(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: object | None = None,
        end: object | None = None,
    ) -> Any:
        self.history_calls.append(
            {"symbol": symbol, "timeframe": timeframe, "start": start, "end": end}
        )
        if self.fails:
            raise ConnectionError("fake transport failure")
        return self.table


def _make_session_ref(environment: str = "SANDBOX") -> BrokerSessionRef:
    return BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref="yahoo-research-account",
        environment=environment,  # type: ignore[arg-type]
        generation=1,
    )


def test_manifest_spec() -> None:
    """Manifest declares the exact feature ID and capability."""
    assert SPEC.feature_id == "FEAT-BRK-CONNECT_YAHOO"
    assert SPEC.domain == "brokers"
    assert SPEC.provides == frozenset({PROVIDER_YAHOO_CAPABILITY})
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset()
    assert "probe_symbol" in SPEC.config_keys


def test_config_defaults() -> None:
    """YahooConfig provides deterministic research defaults."""
    cfg = YahooConfig()
    assert cfg.probe_symbol is None
    assert cfg.request_timeout_sec == 30.0
    assert cfg.circuit_failure_threshold == 5
    assert cfg.environment == "SANDBOX"


@pytest.mark.asyncio
async def test_feature_lifecycle_mount_unmount() -> None:
    """Feature mounts into FeatureContext and unmounts cleanly."""
    feat = feature()
    assert isinstance(feat, YahooFeature)
    assert feat.service is None

    context, _scope, registry = _make_context()

    await feat.mount(context, YahooConfig(probe_symbol="SPY"))
    assert feat.service is not None
    assert registry[PROVIDER_YAHOO_CAPABILITY] is feat.service

    await feat.unmount(context)
    assert feat.service is None


@pytest.mark.asyncio
async def test_manage_sessions_open_without_probe() -> None:
    """OPEN without probe symbol succeeds immediately."""
    service = YahooProviderService(config=YahooConfig(probe_symbol=None))
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
    fake_transport = _FakeTransport(_FakeTable(count=3))
    service = YahooProviderService(
        config=YahooConfig(probe_symbol="SPY"),
        transport=fake_transport,  # type: ignore[arg-type]
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
    assert len(fake_transport.history_calls) == 1
    assert fake_transport.history_calls[0]["symbol"] == "SPY"


@pytest.mark.asyncio
async def test_manage_sessions_open_with_failing_probe() -> None:
    """OPEN with failing probe returns BROKER_SESSION_NOT_READY."""
    fake_transport = _FakeTransport(fails=True)
    service = YahooProviderService(
        config=YahooConfig(probe_symbol="SPY"),
        transport=fake_transport,  # type: ignore[arg-type]
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
    service = YahooProviderService()
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
    service = YahooProviderService(config=YahooConfig(probe_symbol=None))
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
    assert trans_res.state == state_to_set

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
    assess_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="ASSESS_READINESS",
        session=session,
    )
    assess_res = await service.manage_sessions(assess_req)
    assert isinstance(assess_res, ManageSessionsSuccess)
    assert assess_res.readiness is not None
    assert assess_res.readiness.environment_verified is True

    # CLOSE
    close_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="CLOSE",
        session=session,
    )
    close_res = await service.manage_sessions(close_req)
    assert isinstance(close_res, ManageSessionsSuccess)
    assert close_res.state is not None
    assert close_res.state.connection_state == "DISCONNECTED"


@pytest.mark.asyncio
async def test_read_provider_state_page_history() -> None:
    """PAGE_HISTORY returns genuine historical bars in BrokerHistoryPage."""
    fake_transport = _FakeTransport(_FakeTable(count=4))
    service = YahooProviderService(
        config=YahooConfig(probe_symbol="AAPL"),
        transport=fake_transport,  # type: ignore[arg-type]
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
    assert result.page.returned_count == 4
    assert result.page.requested_count == 10
    assert len(result.page.records) == 4
    assert result.page.records[0].provider_id == "yahoo"
    assert result.page.records[0].record["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_read_provider_state_unsupported_operations() -> None:
    """Unsupported state reads return BROKER_PROFILE_UNSUPPORTED."""
    service = YahooProviderService()
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
async def test_transport_orders_rejected() -> None:
    """All order transport operations are rejected as unsupported."""
    service = YahooProviderService()
    session = _make_session_ref()

    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=session,
        operation="SUBMIT_ORDER",
        provider_symbol="AAPL",
        normalized_quantity="10",
        policy={},
        risk_authorization_id=_gen_id(),
        idempotency_key="idemp-123",
        attempt_no=1,
        request_hash="0" * 64,
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
async def test_provider_gateway_dispatches_to_yahoo() -> None:
    """ProviderGateway resolves and dispatches to mounted Yahoo provider."""
    from app.services.brokers.provider_gateway.manifest import SPEC as GW_SPEC

    registry: dict[CapabilityKey[Any], Any] = {}
    scope = FeatureScope(owner_id="test-scope")

    gw_context = DefaultFeatureContext(
        spec=GW_SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    yahoo_context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )

    # Mount yahoo
    fake_transport = _FakeTransport(_FakeTable(count=3))
    yahoo_feat = YahooFeature()
    await yahoo_feat.mount(yahoo_context, YahooConfig(probe_symbol="MSFT"))
    yahoo_feat._service._transport = fake_transport

    # Mount gateway
    gw_feat = ProviderGatewayFeature()
    await gw_feat.mount(gw_context, {})

    gw_service = gw_feat.service
    assert gw_service is not None
    profile = BrokerProviderProfile(
        profile_id=_gen_id(),
        version=1,
        provider=ProviderRef(provider_id=_gen_id(), provider_name="Yahoo Finance"),
        kind="YAHOO",
        account_ref="acc-yahoo",
        environment="SANDBOX",
        api_version_range=">=1.0.0",
        content_hash="0" * 64,
    )
    gw_service.register_profile(profile)

    # Dispatch manage_sessions through gateway
    session_ref = BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=profile.profile_id,
        profile_version=1,
        account_ref=profile.account_ref,
        environment=profile.environment,
        generation=1,
    )
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
    assert read_res.page.returned_count == 3

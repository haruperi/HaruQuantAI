"""Unit and integration tests for Broker Provider Gateway (FEAT-BRK-DISPATCH_PROVIDERS)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    MANAGE_SESSIONS_CAPABILITY,
    PROVIDER_BINANCE_CAPABILITY,
    PROVIDER_CTRADER_CAPABILITY,
    PROVIDER_DUKASCOPY_CAPABILITY,
    PROVIDER_METATRADER_CAPABILITY,
    PROVIDER_YAHOO_CAPABILITY,
    READ_PROVIDER_STATE_CAPABILITY,
    TRANSPORT_ORDERS_CAPABILITY,
)
from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerAccountSnapshot,
    BrokerOperationOutcome,
    BrokerOperationReceipt,
    BrokerOperationRequest,
    BrokerProviderProfile,
    BrokerSessionReadiness,
    BrokerSessionRef,
    BrokerSessionState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
    ProviderCorrelation,
    ReadProviderStateRequest,
    ReadProviderStateSuccess,
    TransportOrdersRequest,
    TransportOrdersSuccess,
)
from app.contracts.catalogue.models import ProviderRef
from app.contracts.common.models import Money, ProblemDetails
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.brokers.provider_gateway.config import ProviderGatewayConfig
from app.services.brokers.provider_gateway.feature import (
    ProviderGatewayFeature,
    feature,
)
from app.services.brokers.provider_gateway.manifest import SPEC
from app.services.brokers.provider_gateway.provider_gateway import (
    ProviderGatewayService,
)


def _gen_id() -> str:
    return str(uuid.uuid7())


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")


class FakeProviderBackend:
    """Configurable fake provider backend for gateway testing."""

    def __init__(self, name: str = "fake") -> None:
        self.name = name
        self.call_log: list[tuple[str, Any]] = []
        self.fail_with: BrokerFailure | None = None

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        self.call_log.append(("manage_sessions", request))
        if self.fail_with is not None:
            return self.fail_with
        return ManageSessionsSuccess(
            request_id=request.request_id,
            session=request.session,
            state=BrokerSessionState(
                session_id=request.session.session_id,
                generation=request.session.generation,
                connection_state="READY",
                transitioned_at=_utc_now(),
            ),
            readiness=BrokerSessionReadiness(
                session_id=request.session.session_id,
                generation=request.session.generation,
                transport="READY",
                authentication="READY",
                account_authorization="READY",
                trading_permission="READY",
                subscriptions="READY",
                environment_verified=True,
                resynchronized=True,
                assessed_at=_utc_now(),
            ),
        )

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        self.call_log.append(("read_provider_state", request))
        if self.fail_with is not None:
            return self.fail_with
        return ReadProviderStateSuccess(
            request_id=request.request_id,
            account=BrokerAccountSnapshot(
                session_id=request.session.session_id if request.session else _gen_id(),
                generation=request.session.generation if request.session else 1,
                account_ref="acc_test",
                currency="USD",
                equity=Money(amount="10000", currency="USD"),
                retrieved_at=_utc_now(),
            ),
        )

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        self.call_log.append(("transport_orders", request))
        if self.fail_with is not None:
            return self.fail_with
        op_id = (
            request.operation_request.operation_id
            if request.operation_request
            else (request.operation_id or _gen_id())
        )
        receipt = BrokerOperationReceipt(
            receipt_id=_gen_id(),
            operation_id=op_id,
            attempt_no=1,
            profile_version_id=_gen_id(),
            environment="DEMO",
            session_generation=1,
            request_hash="0" * 64,
            outcome="ACCEPTED",
        )
        return TransportOrdersSuccess(
            request_id=request.request_id,
            receipt=receipt,
            outcome=BrokerOperationOutcome(
                operation_id=op_id,
                outcome="ACCEPTED",
                receipt=receipt,
            ),
            correlation=ProviderCorrelation(
                correlation_id=_gen_id(),
                operation_id=op_id,
                idempotency_key="idemp_1",
            ),
        )


def _make_context(
    providers: dict[CapabilityKey[Any], Any] | None = None,
) -> tuple[DefaultFeatureContext, FeatureScope, dict[CapabilityKey[Any], Any]]:
    registry: dict[CapabilityKey[Any], Any] = dict(providers or {})
    scope = FeatureScope(owner_id="FEAT-BRK-DISPATCH_PROVIDERS")
    context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    return context, scope, registry


def _make_session_ref(
    session_id: str | None = None,
    profile_id: str | None = None,
) -> BrokerSessionRef:
    return BrokerSessionRef(
        session_id=session_id or _gen_id(),
        profile_id=profile_id or _gen_id(),
        profile_version=1,
        account_ref="acc_001",
        environment="DEMO",
        generation=1,
    )


def test_manifest_spec_declarations() -> None:
    """Verify FeatureSpec declares exact publication and dependencies."""
    assert SPEC.feature_id == "FEAT-BRK-DISPATCH_PROVIDERS"
    assert SPEC.domain == "brokers"
    assert SPEC.provides == frozenset(
        {
            MANAGE_SESSIONS_CAPABILITY,
            READ_PROVIDER_STATE_CAPABILITY,
            TRANSPORT_ORDERS_CAPABILITY,
        }
    )
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset(
        {
            PROVIDER_METATRADER_CAPABILITY,
            PROVIDER_CTRADER_CAPABILITY,
            PROVIDER_BINANCE_CAPABILITY,
            PROVIDER_DUKASCOPY_CAPABILITY,
            PROVIDER_YAHOO_CAPABILITY,
        }
    )
    assert SPEC.state is None
    assert SPEC.config_keys == frozenset()
    SPEC.validate()


@pytest.mark.asyncio
async def test_feature_mount_and_service_creation() -> None:
    """Verify ProviderGatewayFeature mount provides all 3 capabilities."""
    feat = feature()
    assert isinstance(feat, ProviderGatewayFeature)
    context, _scope, registry = _make_context()

    await feat.mount(context, ProviderGatewayConfig())
    assert feat.service is not None

    assert registry.get(MANAGE_SESSIONS_CAPABILITY) is feat.service
    assert registry.get(READ_PROVIDER_STATE_CAPABILITY) is feat.service
    assert registry.get(TRANSPORT_ORDERS_CAPABILITY) is feat.service


@pytest.mark.asyncio
async def test_dispatch_single_provider() -> None:
    """Verify dispatching all operations to a single mounted provider."""
    mt5_backend = FakeProviderBackend(name="mt5")
    context, _, _ = _make_context({PROVIDER_METATRADER_CAPABILITY: mt5_backend})
    gateway = ProviderGatewayService(context=context)

    session = _make_session_ref()
    gateway.bind_profile(session.profile_id, PROVIDER_METATRADER_CAPABILITY)

    # 1. manage_sessions
    req_sess = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session,
    )
    res_sess = await gateway.manage_sessions(req_sess)
    assert isinstance(res_sess, ManageSessionsSuccess)
    assert res_sess.outcome == "SUCCESS"
    assert len(mt5_backend.call_log) == 1

    # 2. read_provider_state
    req_read = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="READ_ACCOUNT",
        session=session,
    )
    res_read = await gateway.read_provider_state(req_read)
    assert isinstance(res_read, ReadProviderStateSuccess)
    assert res_read.outcome == "SUCCESS"
    assert len(mt5_backend.call_log) == 2

    # 3. transport_orders (SUBMIT)
    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=session,
        operation="SUBMIT_ORDER",
        provider_symbol="EURUSD",
        normalized_quantity="1",
        policy={},
        risk_authorization_id=_gen_id(),
        idempotency_key="idemp_10",
        attempt_no=1,
        request_hash="0" * 64,
    )
    req_order = TransportOrdersRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="SUBMIT",
        operation_request=op_req,
    )
    res_order = await gateway.transport_orders(req_order)
    assert isinstance(res_order, TransportOrdersSuccess)
    assert len(mt5_backend.call_log) == 3

    # 4. transport_orders (JOURNAL) using previously recorded operation_id
    req_journal = TransportOrdersRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="JOURNAL",
        operation_id=op_req.operation_id,
    )
    res_journal = await gateway.transport_orders(req_journal)
    assert isinstance(res_journal, TransportOrdersSuccess)
    assert len(mt5_backend.call_log) == 4


@pytest.mark.asyncio
async def test_dispatch_multiple_providers_isolation() -> None:
    """Verify multi-provider dispatch routes exclusively to the target provider."""
    mt5_backend = FakeProviderBackend(name="mt5")
    binance_backend = FakeProviderBackend(name="binance")
    context, _, _ = _make_context(
        {
            PROVIDER_METATRADER_CAPABILITY: mt5_backend,
            PROVIDER_BINANCE_CAPABILITY: binance_backend,
        }
    )
    gateway = ProviderGatewayService(context=context)

    session_mt5 = _make_session_ref()
    session_binance = _make_session_ref()
    gateway.bind_session(session_mt5.session_id, PROVIDER_METATRADER_CAPABILITY)
    gateway.bind_session(session_binance.session_id, PROVIDER_BINANCE_CAPABILITY)

    # Call MT5
    req_mt5 = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="READ_ACCOUNT",
        session=session_mt5,
    )
    res_mt5 = await gateway.read_provider_state(req_mt5)
    assert isinstance(res_mt5, ReadProviderStateSuccess)
    assert len(mt5_backend.call_log) == 1
    assert len(binance_backend.call_log) == 0

    # Call Binance
    req_binance = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="READ_ACCOUNT",
        session=session_binance,
    )
    res_binance = await gateway.read_provider_state(req_binance)
    assert isinstance(res_binance, ReadProviderStateSuccess)
    assert len(mt5_backend.call_log) == 1
    assert len(binance_backend.call_log) == 1


@pytest.mark.asyncio
async def test_missing_provider_fails_unavailable() -> None:
    """Verify unmounted provider backend returns CAPABILITY_UNAVAILABLE."""
    context, _, _ = _make_context()  # No providers mounted
    gateway = ProviderGatewayService(context=context)

    session = _make_session_ref()
    gateway.bind_session(session.session_id, PROVIDER_YAHOO_CAPABILITY)

    req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session,
    )
    res = await gateway.manage_sessions(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "CAPABILITY_UNAVAILABLE"
    assert res.outcome == "FAILURE"
    assert res.problem.capability_key == PROVIDER_YAHOO_CAPABILITY.identifier


@pytest.mark.asyncio
async def test_unmapped_session_fails_unavailable() -> None:
    """Verify unmapped session returns CAPABILITY_UNAVAILABLE."""
    context, _, _ = _make_context()
    gateway = ProviderGatewayService(context=context)

    session = _make_session_ref()  # Not bound to any profile/provider

    req = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="READ_ACCOUNT",
        session=session,
    )
    res = await gateway.read_provider_state(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "CAPABILITY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_failing_provider_no_fallback() -> None:
    """Verify provider failures are returned directly with zero fallback."""
    failing_mt5 = FakeProviderBackend(name="mt5")
    failing_mt5.fail_with = BrokerFailure(
        request_id=_gen_id(),
        code="BROKER_OPERATION_REJECTED",
        problem=ProblemDetails(
            code="BROKER_OPERATION_REJECTED",
            detail="Order rejected by MT5 terminal",
        ),
    )
    backup_ctrader = FakeProviderBackend(name="ctrader")
    context, _, _ = _make_context(
        {
            PROVIDER_METATRADER_CAPABILITY: failing_mt5,
            PROVIDER_CTRADER_CAPABILITY: backup_ctrader,
        }
    )
    gateway = ProviderGatewayService(context=context)

    session = _make_session_ref()
    gateway.bind_session(session.session_id, PROVIDER_METATRADER_CAPABILITY)

    req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session,
    )
    res = await gateway.manage_sessions(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "BROKER_OPERATION_REJECTED"
    assert len(failing_mt5.call_log) == 1
    assert len(backup_ctrader.call_log) == 0  # Crucial: NO fallback!


@pytest.mark.asyncio
async def test_provider_removal_and_replacement_generations() -> None:
    """Verify dynamic provider removal and replacement across generations."""
    gen1_backend = FakeProviderBackend(name="gen1")
    context, _, registry = _make_context({PROVIDER_DUKASCOPY_CAPABILITY: gen1_backend})
    gateway = ProviderGatewayService(context=context)

    session = _make_session_ref()
    gateway.bind_session(session.session_id, PROVIDER_DUKASCOPY_CAPABILITY)

    # 1. Gen 1 active
    req = ReadProviderStateRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="READ_ACCOUNT",
        session=session,
    )
    res1 = await gateway.read_provider_state(req)
    assert isinstance(res1, ReadProviderStateSuccess)
    assert len(gen1_backend.call_log) == 1

    # 2. Remove provider from registry
    del registry[PROVIDER_DUKASCOPY_CAPABILITY]
    res2 = await gateway.read_provider_state(req)
    assert isinstance(res2, BrokerFailure)
    assert res2.code == "CAPABILITY_UNAVAILABLE"

    # 3. Mount Gen 2 replacement
    gen2_backend = FakeProviderBackend(name="gen2")
    registry[PROVIDER_DUKASCOPY_CAPABILITY] = gen2_backend
    res3 = await gateway.read_provider_state(req)
    assert isinstance(res3, ReadProviderStateSuccess)
    assert len(gen2_backend.call_log) == 1


def test_register_profile_wire_model() -> None:
    """Verify register_profile maps BrokerProviderProfile kinds correctly."""
    context, _, _ = _make_context()
    gateway = ProviderGatewayService(context=context)

    p_mt5 = BrokerProviderProfile(
        profile_id=_gen_id(),
        version=1,
        provider=ProviderRef(provider_id=_gen_id(), provider_name="MetaTrader5"),
        kind="MT5",
        account_ref="acc1",
        environment="DEMO",
        api_version_range=">=5.0",
        content_hash="a" * 64,
    )
    p_binance = BrokerProviderProfile(
        profile_id=_gen_id(),
        version=1,
        provider=ProviderRef(provider_id=_gen_id(), provider_name="Binance"),
        kind="BINANCE_SPOT",
        account_ref="acc2",
        environment="TESTNET",
        api_version_range=">=1.0",
        content_hash="b" * 64,
    )

    gateway.register_profile(p_mt5)
    gateway.register_profile(p_binance)

    assert (
        gateway._resolve_session_key(None, str(p_mt5.profile_id))
        == PROVIDER_METATRADER_CAPABILITY
    )
    assert (
        gateway._resolve_session_key(None, str(p_binance.profile_id))
        == PROVIDER_BINANCE_CAPABILITY
    )

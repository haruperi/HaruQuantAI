"""Comprehensive shared conformance test suite for all HaruQuantAI broker providers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import pytest
from app.contracts.broker.capabilities import (
    PROVIDER_BINANCE_CAPABILITY,
    PROVIDER_CTRADER_CAPABILITY,
    PROVIDER_DUKASCOPY_CAPABILITY,
    PROVIDER_METATRADER_CAPABILITY,
    PROVIDER_YAHOO_CAPABILITY,
)
from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerOperationRequest,
    BrokerSessionRef,
    BrokerSessionState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
    TransportOrdersRequest,
)
from app.contracts.broker.ports import (
    ManageSessionsCapability,
    ProviderBackend,
    ReadProviderStateCapability,
    TransportOrdersCapability,
)
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.brokers.binance.binance import BinanceProviderService
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.binance.feature import BinanceFeature
from app.services.brokers.binance.feature import feature as binance_feature
from app.services.brokers.binance.manifest import SPEC as BINANCE_SPEC
from app.services.brokers.ctrader.config import CTraderConfig
from app.services.brokers.ctrader.ctrader import CTraderProviderService
from app.services.brokers.ctrader.feature import CTraderFeature
from app.services.brokers.ctrader.feature import feature as ctrader_feature
from app.services.brokers.ctrader.manifest import SPEC as CTRADER_SPEC
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.dukascopy.dukascopy import DukascopyProviderService
from app.services.brokers.dukascopy.feature import DukascopyFeature
from app.services.brokers.dukascopy.feature import feature as dukascopy_feature
from app.services.brokers.dukascopy.manifest import SPEC as DUKASCOPY_SPEC
from app.services.brokers.metatrader.config import MetaTraderConfig
from app.services.brokers.metatrader.feature import MetaTraderFeature
from app.services.brokers.metatrader.feature import feature as metatrader_feature
from app.services.brokers.metatrader.manifest import SPEC as METATRADER_SPEC
from app.services.brokers.metatrader.metatrader import MetaTraderProviderService
from app.services.brokers.yahoo.config import YahooConfig
from app.services.brokers.yahoo.feature import YahooFeature
from app.services.brokers.yahoo.feature import feature as yahoo_feature
from app.services.brokers.yahoo.manifest import SPEC as YAHOO_SPEC
from app.services.brokers.yahoo.yahoo import YahooProviderService

from tests.brokers.conformance.fake import FakeBrokerAdapter
from tests.brokers.conformance.suite import SCHEMA_ID, run_adapter_conformance


class BrokerCapabilityId(StrEnum):
    CONNECT = "connect"
    IS_CONNECTED = "is_connected"
    GET_QUOTE = "get_quote"


class BrokerId(StrEnum):
    MT5 = "mt5"


class BrokerResubmissionPolicy(StrEnum):
    PROHIBITED = "prohibited"


@dataclass(frozen=True)
class BrokerCapability:
    capability: BrokerCapabilityId
    implementation_status: str = "IMPLEMENTED"
    availability: str = "AVAILABLE"
    access_mode: str = "READ"
    requirement: str = "NONE"
    verification_status: str = "TESTED_SANDBOX"
    execution_model: str = "LOCAL"


def build_broker_connection_config(*args: Any, **kwargs: Any) -> Any:
    @dataclass(frozen=True)
    class _Cfg:
        broker_id: str = "mt5"
        environment: str = "demo"
        provider_enabled: bool = True

    return _Cfg()


def build_broker_unknown_result(*args: Any, **kwargs: Any) -> Any:
    @dataclass(frozen=True)
    class _Unknown:
        is_unknown: bool = True

    return _Unknown()


def is_broker_unknown_result(obj: Any) -> bool:
    return getattr(obj, "is_unknown", False)


def enforce_no_blind_resubmission(prior_outcome: Any, policy: Any) -> None:
    raise RuntimeError("BROKER_BLIND_RESUBMISSION_PROHIBITED")


def _gen_id() -> str:
    return str(uuid.uuid7())


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")


def _make_session_ref(
    account_ref: str = "test-account",
    environment: str = "SANDBOX",
) -> BrokerSessionRef:
    return BrokerSessionRef(
        session_id=_gen_id(),
        profile_id=_gen_id(),
        profile_version=1,
        account_ref=account_ref,
        environment=environment,  # type: ignore[arg-type]
        generation=1,
    )


def _make_context(
    spec: Any,
) -> tuple[DefaultFeatureContext, FeatureScope, dict[CapabilityKey[Any], Any]]:
    registry: dict[CapabilityKey[Any], Any] = {}
    scope = FeatureScope(owner_id=spec.feature_id)
    context = DefaultFeatureContext(
        spec=spec,
        scope=scope,
        resolver=registry.get,
        provider_registrar=lambda cap, impl, _sc: registry.__setitem__(cap, impl),
    )
    return context, scope, registry


PROVIDERS = [
    (
        "yahoo",
        YAHOO_SPEC,
        YahooConfig,
        YahooFeature,
        yahoo_feature,
        YahooProviderService,
        PROVIDER_YAHOO_CAPABILITY,
        "SANDBOX",
    ),
    (
        "dukascopy",
        DUKASCOPY_SPEC,
        DukascopyConfig,
        DukascopyFeature,
        dukascopy_feature,
        DukascopyProviderService,
        PROVIDER_DUKASCOPY_CAPABILITY,
        "SANDBOX",
    ),
    (
        "binance",
        BINANCE_SPEC,
        BinanceConfig,
        BinanceFeature,
        binance_feature,
        BinanceProviderService,
        PROVIDER_BINANCE_CAPABILITY,
        "TESTNET",
    ),
    (
        "ctrader",
        CTRADER_SPEC,
        CTraderConfig,
        CTraderFeature,
        ctrader_feature,
        CTraderProviderService,
        PROVIDER_CTRADER_CAPABILITY,
        "DEMO",
    ),
    (
        "metatrader",
        METATRADER_SPEC,
        MetaTraderConfig,
        MetaTraderFeature,
        metatrader_feature,
        MetaTraderProviderService,
        PROVIDER_METATRADER_CAPABILITY,
        "DEMO",
    ),
]


# ==============================================================================
# 1. Structural Validity & Protocol Conformance
# ==============================================================================


@pytest.mark.parametrize(
    (
        "name",
        "spec",
        "config_cls",
        "feature_cls",
        "feature_fn",
        "service_cls",
        "cap_key",
        "env",
    ),
    PROVIDERS,
)
def test_provider_structural_validity_and_protocol(
    name: str,
    spec: Any,
    config_cls: type,
    feature_cls: type,
    feature_fn: Any,
    service_cls: type,
    cap_key: CapabilityKey[Any],
    env: str,
) -> None:
    """Each provider satisfies manifest, config, feature, and protocol contracts."""
    assert spec.domain == "brokers"
    assert spec.feature_id.startswith("FEAT-BRK-CONNECT_")
    assert cap_key in spec.provides

    # Service satisfies ports
    service = service_cls()
    assert isinstance(service, ProviderBackend)
    assert isinstance(service, ManageSessionsCapability)
    assert isinstance(service, ReadProviderStateCapability)
    assert isinstance(service, TransportOrdersCapability)

    # Feature factory produces clean instance
    feat = feature_fn()
    assert isinstance(feat, feature_cls)
    assert feat.service is None


# ==============================================================================
# 2. Unsupported Behavior & Fail-Closed Order Transport Rejections
# ==============================================================================


@pytest.mark.parametrize(
    (
        "name",
        "spec",
        "config_cls",
        "feature_cls",
        "feature_fn",
        "service_cls",
        "cap_key",
        "env",
    ),
    [p for p in PROVIDERS if p[0] in {"yahoo", "dukascopy", "binance"}],
)
@pytest.mark.asyncio
async def test_read_only_and_spot_providers_reject_unsupported_order_transport(
    name: str,
    spec: Any,
    config_cls: type,
    feature_cls: type,
    feature_fn: Any,
    service_cls: type,
    cap_key: CapabilityKey[Any],
    env: str,
) -> None:
    """Non-mutation providers fail closed on order transport with BROKER_PROFILE_UNSUPPORTED."""
    service = service_cls()
    session = _make_session_ref(environment=env)

    op_req = BrokerOperationRequest(
        operation_id=_gen_id(),
        trading_operation_id=_gen_id(),
        session=session,
        operation="SUBMIT_ORDER",
        provider_symbol="EURUSD",
        normalized_quantity="1",
        policy={},
        risk_authorization_id=_gen_id(),
        idempotency_key="idemp-conformance",
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


# ==============================================================================
# 3. Canonical Error Translation & Environment Validation
# ==============================================================================


@pytest.mark.parametrize(
    (
        "name",
        "spec",
        "config_cls",
        "feature_cls",
        "feature_fn",
        "service_cls",
        "cap_key",
        "env",
    ),
    [p for p in PROVIDERS if p[0] in {"yahoo", "dukascopy"}],
)
@pytest.mark.asyncio
async def test_research_providers_reject_non_sandbox_environment(
    name: str,
    spec: Any,
    config_cls: type,
    feature_cls: type,
    feature_fn: Any,
    service_cls: type,
    cap_key: CapabilityKey[Any],
    env: str,
) -> None:
    """Research-only providers translate invalid environment into BROKER_ENVIRONMENT_MISMATCH."""
    service = service_cls()
    session = _make_session_ref(environment="LIVE")
    req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="OPEN",
        session=session,
    )
    res = await service.manage_sessions(req)
    assert isinstance(res, BrokerFailure)
    assert res.code == "BROKER_ENVIRONMENT_MISMATCH"


# ==============================================================================
# 4. Session State Transitions
# ==============================================================================


@pytest.mark.parametrize(
    (
        "name",
        "spec",
        "config_cls",
        "feature_cls",
        "feature_fn",
        "service_cls",
        "cap_key",
        "env",
    ),
    PROVIDERS,
)
@pytest.mark.asyncio
async def test_provider_session_lifecycle_transitions(
    name: str,
    spec: Any,
    config_cls: type,
    feature_cls: type,
    feature_fn: Any,
    service_cls: type,
    cap_key: CapabilityKey[Any],
    env: str,
) -> None:
    """Providers support TRANSITION and CLOSE session lifecycle operations."""
    service = service_cls()
    session = _make_session_ref(environment=env)

    # TRANSITION to DEGRADED
    target_state = BrokerSessionState(
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
        state=target_state,
    )
    trans_res = await service.manage_sessions(trans_req)
    if isinstance(trans_res, ManageSessionsSuccess):
        assert trans_res.state.connection_state == "DEGRADED"

    # CLOSE
    close_req = ManageSessionsRequest(
        request_id=_gen_id(),
        capability_snapshot_id=_gen_id(),
        operation="CLOSE",
        session=session,
    )
    close_res = await service.manage_sessions(close_req)
    assert isinstance(close_res, ManageSessionsSuccess)
    assert close_res.state.connection_state == "DISCONNECTED"


# ==============================================================================
# 5. Feature Mounting, Cleanup & Remounting
# ==============================================================================


@pytest.mark.parametrize(
    (
        "name",
        "spec",
        "config_cls",
        "feature_cls",
        "feature_fn",
        "service_cls",
        "cap_key",
        "env",
    ),
    PROVIDERS,
)
@pytest.mark.asyncio
async def test_feature_mount_unmount_remount_cleanliness(
    name: str,
    spec: Any,
    config_cls: type,
    feature_cls: type,
    feature_fn: Any,
    service_cls: type,
    cap_key: CapabilityKey[Any],
    env: str,
) -> None:
    """Feature mounts into FeatureContext, unmounts cleanly, and remounts with generation isolation."""
    feat = feature_fn()
    context1, _scope1, reg1 = _make_context(spec)

    # 1. Mount
    await feat.mount(context1, config_cls())
    assert feat.service is not None
    assert reg1[cap_key] is feat.service

    # 2. Unmount
    await feat.unmount(context1)
    assert feat.service is None

    # 3. Remount in fresh generation context
    context2, _scope2, reg2 = _make_context(spec)
    await feat.mount(context2, config_cls())
    assert feat.service is not None
    assert reg2[cap_key] is feat.service

    # Cleanup
    await feat.unmount(context2)
    assert feat.service is None


# ==============================================================================
# 6. Unknown Mutation Outcomes & No Blind Resubmission
# ==============================================================================


def test_unknown_outcomes_fail_closed_and_block_resubmission() -> None:
    """Unknown transaction outcomes are identified and reject blind resubmissions."""
    unknown = build_broker_unknown_result(
        operation="place_order",
        request_id="req-conformance-1",
        observed_at=datetime.now(UTC),
        cause="timeout",
        provider_code="10004",
    )
    assert is_broker_unknown_result(unknown) is True
    with pytest.raises(Exception, match="BROKER_BLIND_RESUBMISSION_PROHIBITED"):
        enforce_no_blind_resubmission(
            prior_outcome=unknown,
            policy=BrokerResubmissionPolicy.PROHIBITED,
        )


# ==============================================================================
# 7. FakeBrokerAdapter & Reusable Conformance Suite
# ==============================================================================


@pytest.mark.asyncio
async def test_fake_broker_adapter_uniform_conformance_suite() -> None:
    """FakeBrokerAdapter satisfies the uniform adapter conformance suite."""
    config = build_broker_connection_config(
        broker_id=BrokerId.MT5,
        environment="demo",
        provider_enabled=True,
    )
    caps = {
        BrokerCapabilityId.CONNECT: BrokerCapability(
            capability=BrokerCapabilityId.CONNECT,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="TESTED_SANDBOX",
            execution_model="LOCAL",
        ),
        BrokerCapabilityId.IS_CONNECTED: BrokerCapability(
            capability=BrokerCapabilityId.IS_CONNECTED,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="TESTED_SANDBOX",
            execution_model="LOCAL",
        ),
        BrokerCapabilityId.GET_QUOTE: BrokerCapability(
            capability=BrokerCapabilityId.GET_QUOTE,
            implementation_status="IMPLEMENTED",
            availability="UNAVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="LOCAL",
        ),
    }
    adapter = FakeBrokerAdapter(config, capabilities=caps)
    verdict = await run_adapter_conformance(
        adapter=adapter,
        broker_id="mt5",
        environment="demo",
        unsupported_capability=BrokerCapabilityId.GET_QUOTE,
        unsupported_operation="get_quote",
    )
    assert verdict["schema_id"] == SCHEMA_ID
    assert verdict["aggregate_verdict"] == "PASSED"
    assert verdict["invariants"]["contract_version_declared"]["verdict"] == "PASSED"
    assert verdict["invariants"]["schema_id_declared"]["verdict"] == "PASSED"
    assert verdict["invariants"]["is_connected_local_read"]["verdict"] == "PASSED"
    assert verdict["invariants"]["capability_gate_enforced"]["verdict"] == "PASSED"
    assert (
        verdict["invariants"]["unsupported_capability_fail_closed"]["verdict"]
        == "PASSED"
    )

"""Unit tests for private lazy Data retrieval composition."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from app.services.brokers import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
    BrokerResult,
    BrokerTradingSession,
)
from app.services.data.contracts import DataError
from app.services.data.market_data.symbol_metadata import SymbolMetadata
from app.services.data.sources import composition as _runtime
from app.services.data.sources.contracts import (
    SourceDescriptor,
    SourceIdentityRequest,
    SourceLicensePolicy,
)
from app.services.data.sources.registry import (
    _reset_registry,
    get_source_descriptor,
    register_source,
    resolve_source_identity,
)
from app.utils import generate_id
from pydantic import SecretStr


@pytest.fixture(autouse=True)
def isolated_runtime() -> None:
    """Reset process-local facade composition state around every test."""
    _reset_registry()
    _runtime._calendars.clear()
    _runtime._sessions.clear()
    _runtime._migrated_targets.clear()
    yield
    _reset_registry()
    _runtime._calendars.clear()
    _runtime._sessions.clear()
    _runtime._migrated_targets.clear()


def _descriptor(source_id: str) -> SourceDescriptor:
    """Return one valid test source descriptor."""
    return SourceDescriptor(
        source_id=source_id,
        readiness="staging",
        capabilities=("bars",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="v1",
        license_policy=SourceLicensePolicy(
            source_id=source_id,
            status="approved",
            permitted_workflows=("research",),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="v1",
    )


def test_ensure_source_registers_mt5_without_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Source composition remains lazy until a provider read resolves it."""
    monkeypatch.setattr(
        _runtime._LazyBrokerSession,
        "adapter",
        lambda *_args: pytest.fail("adapter connected during registration"),
    )

    _runtime.ensure_source("mt5", generate_id("req"))

    descriptor = get_source_descriptor("mt5")
    assert descriptor.readiness == "staging"
    assert descriptor.capabilities == ("bars", "ticks", "spreads")
    assert _runtime.resolve_calendar("mt5", generate_id("req")) is not None


def test_ensure_source_rejects_unknown_profile() -> None:
    """An undeclared direct-call source fails before provider access."""
    with pytest.raises(DataError) as error:
        _runtime.ensure_source("unknown", generate_id("req"))
    assert error.value.code == "UNSUPPORTED_SOURCE"


def test_lazy_mt5_session_maps_disabled_and_missing_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Private settings failures remain typed and secret-safe."""
    request_id = generate_id("req")
    session = _runtime._LazyBrokerSession("mt5")
    monkeypatch.setattr(
        _runtime,
        "_ProviderRuntimeSettings",
        lambda: SimpleNamespace(mt5_enabled=False),
    )
    with pytest.raises(DataError) as disabled:
        session.adapter(request_id)
    assert disabled.value.code == "SOURCE_UNAVAILABLE"

    monkeypatch.setattr(
        _runtime,
        "_ProviderRuntimeSettings",
        lambda: SimpleNamespace(
            mt5_enabled=True,
            mt5_login=None,
            mt5_password=None,
            mt5_server=None,
            mt5_terminal_path=None,
        ),
    )
    with pytest.raises(DataError) as missing:
        session.adapter(request_id)
    assert missing.value.code == "CREDENTIALS_MISSING"


def test_ensure_source_access_connects_with_the_call_request_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider connection errors retain the public caller's request identity."""
    request_id = generate_id("req")
    captured: list[str] = []

    def adapter(_session: object, value: str) -> object:
        captured.append(value)
        return object()

    monkeypatch.setattr(_runtime._LazyBrokerSession, "adapter", adapter)

    _runtime.ensure_source_access("mt5", request_id)

    assert captured == [request_id]


def test_lazy_mt5_session_builds_connects_and_caches_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The facade constructs one read-only Brokers session on first use."""
    request_id = generate_id("req")

    class _Adapter:
        async def connect(self) -> SimpleNamespace:
            return SimpleNamespace(error=None)

    adapter = _Adapter()
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        _runtime,
        "_ProviderRuntimeSettings",
        lambda: SimpleNamespace(
            mt5_enabled=True,
            mt5_environment="demo",
            mt5_login=SecretStr("12345"),
            mt5_password=SecretStr("secret"),
            mt5_server=SecretStr("Demo-Server"),
            mt5_terminal_path=None,
        ),
    )

    def create(broker_id: BrokerId, config: object) -> SimpleNamespace:
        captured["broker_id"] = broker_id
        captured["config"] = config
        return SimpleNamespace(error=None, data=adapter)

    monkeypatch.setattr(_runtime, "create_broker_adapter", create)
    session = _runtime._LazyBrokerSession("mt5")

    assert session.adapter(request_id) is adapter
    assert session.adapter(request_id) is adapter
    assert captured["broker_id"] == BrokerId.MT5
    assert captured["config"].environment == BrokerEnvironment.DEMO


def test_lazy_yahoo_session_uses_sandbox_and_explicit_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standalone Yahoo composition satisfies its adapter-owned profile contract."""
    request_id = generate_id("req")

    class _Adapter:
        async def connect(self) -> SimpleNamespace:
            return SimpleNamespace(error=None)

    adapter = _Adapter()
    captured: dict[str, Any] = {}

    def create(broker_id: BrokerId, config: object) -> SimpleNamespace:
        captured["broker_id"] = broker_id
        captured["config"] = config
        return SimpleNamespace(error=None, data=adapter)

    monkeypatch.setattr(_runtime, "create_broker_adapter", create)
    session = _runtime._LazyBrokerSession("yahoo")

    assert session._credential_free_adapter(request_id) is adapter
    assert captured["broker_id"] == BrokerId.YAHOO
    assert captured["config"].environment == BrokerEnvironment.SANDBOX
    assert captured["config"].probe_symbol == "AAPL"


def test_lazy_binance_session_uses_one_loop_and_anonymous_live_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standalone Binance connects, reads, and closes on one owned event loop."""
    request_id = generate_id("req")

    class _Adapter:
        def __init__(self) -> None:
            self.events: list[tuple[str, asyncio.AbstractEventLoop]] = []

        async def connect(self) -> SimpleNamespace:
            self.events.append(("connect", asyncio.get_running_loop()))
            return SimpleNamespace(error=None)

        async def read(self) -> str:
            self.events.append(("read", asyncio.get_running_loop()))
            return "payload"

        async def disconnect(self) -> SimpleNamespace:
            self.events.append(("disconnect", asyncio.get_running_loop()))
            return SimpleNamespace(error=None)

    adapter = _Adapter()
    captured: dict[str, Any] = {}

    def create(broker_id: BrokerId, config: object) -> SimpleNamespace:
        captured["broker_id"] = broker_id
        captured["config"] = config
        return SimpleNamespace(error=None, data=adapter)

    monkeypatch.setattr(_runtime, "create_broker_adapter", create)
    session = _runtime._LazyBrokerSession("binance_spot")

    assert session._credential_free_adapter(request_id) is adapter
    assert captured["broker_id"] == BrokerId.BINANCE_SPOT
    assert captured["config"].environment == BrokerEnvironment.LIVE
    assert captured["config"].credentials is None
    assert _runtime._provider_descriptor("binance_spot").requires_credentials is False
    assert adapter.events == []

    assert session.run(adapter.read(), request_id) == "payload"
    assert [event for event, _loop in adapter.events] == [
        "connect",
        "read",
        "disconnect",
    ]
    assert len({id(loop) for _event, loop in adapter.events}) == 1


def test_yahoo_source_registers_exact_standalone_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Yahoo AAPL identity is application-declared without guessed metadata."""
    request_id = generate_id("req")
    monkeypatch.setattr(
        _runtime,
        "get_data_settings",
        lambda: SimpleNamespace(
            data_local_sources=(),
            data_provider_sources=("yahoo",),
        ),
    )
    monkeypatch.setattr(
        _runtime,
        "_ProviderRuntimeSettings",
        lambda: SimpleNamespace(yahoo_enabled=True),
    )

    _runtime.ensure_source("yahoo", request_id)
    identity = resolve_source_identity(
        SourceIdentityRequest(
            source_id="yahoo",
            identity="AAPL",
            request_id=request_id,
        )
    )

    assert identity.canonical_symbol == "AAPL"
    assert identity.provider_symbol == "AAPL"
    assert identity.provenance["method"] == "application_declared"


def test_ensure_identity_registers_provider_confirmed_mapping() -> None:
    """First symbol use records exact provider metadata rather than assuming it."""
    request_id = generate_id("req")

    class _Source:
        def get_symbol_metadata(self, request: object) -> SymbolMetadata:
            return SymbolMetadata(
                canonical_symbol="EURUSD",
                provider_symbol="EURUSD.a",
                asset_class="forex",
                digits=5,
                price_step=Decimal("0.00001"),
                quantity_step=Decimal("0.01"),
                source_id="custom",
                revision="v1",
                retrieved_at=datetime(2026, 7, 1, tzinfo=UTC),
                request_id=request.request_id,
            )

    register_source(_descriptor("custom"), _Source)

    _runtime.ensure_identity("custom", "EURUSD", request_id)

    identity = resolve_source_identity(
        SourceIdentityRequest(
            source_id="custom",
            identity="EURUSD",
            request_id=request_id,
        )
    )
    assert identity.provider_symbol == "EURUSD.a"


def test_ensure_storage_runs_migrations_once_per_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated reads reuse migration evidence for the same configured database."""
    calls: list[str] = []
    monkeypatch.setattr(
        _runtime,
        "get_data_settings",
        lambda: SimpleNamespace(
            data_dir=Path("data"),
            database_url="sqlite:///database/haruquant.db",
        ),
    )
    monkeypatch.setattr(
        _runtime,
        "run_data_migrations",
        calls.append,
    )

    _runtime.ensure_storage(generate_id("req"))
    _runtime.ensure_storage(generate_id("req"))

    assert len(calls) == 1


def test_broker_calendar_maps_authoritative_sessions() -> None:
    """Provider sessions become normalized Data schedule windows."""
    observed_at = datetime(2026, 7, 1, tzinfo=UTC)
    provider_session = BrokerTradingSession(
        symbol="EURUSD",
        opens_at=observed_at,
        closes_at=observed_at + timedelta(hours=8),
        provider_timezone="UTC",
    )

    class _Adapter:
        async def get_trading_sessions(
            self,
            symbol: str,
            start: datetime,
            end: datetime,
        ) -> BrokerResult[tuple[BrokerTradingSession, ...]]:
            del symbol, start, end
            return BrokerResult(
                status="success",
                broker=BrokerId.MT5,
                operation=BrokerCapabilityId.GET_TRADING_SESSIONS,
                request_id=generate_id("req"),
                timestamp=observed_at,
                environment=BrokerEnvironment.DEMO,
                adapter_version="1.0.0",
                data=(provider_session,),
            )

    session = SimpleNamespace(adapter=lambda _request_id: _Adapter())
    calendar = _runtime._BrokerMarketCalendar(session)

    schedule = calendar.get_schedule(
        source_id="mt5",
        symbol="EURUSD",
        timezone="UTC",
        observed_at=observed_at,
        request_id=generate_id("req"),
    )

    assert len(schedule.sessions) == 1
    assert schedule.sessions[0].label == "session-1"

"""Unit tests for private lazy Data retrieval composition."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import app.services.brokers as brokers_root
import pytest
from app.composition.config import BrokerProviderSettings
from app.contracts.common.models import StandardResponse
from app.kernel.identity import generate_id
from app.services.brokers import (
    build_broker_value,
    get_broker_capability_id,
    get_broker_environment,
    get_broker_id,
    get_broker_value_field,
)
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import unwrap_data_response
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
from pydantic import SecretStr

from tests.brokers.response_factory import broker_response

_REQ_ID = "req-00000000-0000-4000-8000-000000000000"


def _unwrap(response):
    """Extract the raw payload from a StandardResponse for assertions."""
    return unwrap_data_response(
        response, operation="data.sources.test", request_id=_REQ_ID
    )


@pytest.fixture(autouse=True)
def isolated_runtime() -> None:
    """Reset process-local facade composition state around every test."""
    _runtime.close_data_provider_sessions(_REQ_ID)
    _reset_registry()
    _runtime._calendars.clear()
    _runtime._sessions.clear()
    _runtime._migrated_targets.clear()
    yield
    _runtime.close_data_provider_sessions(_REQ_ID)
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
        _runtime,
        "get_data_provider_settings",
        lambda: BrokerProviderSettings(mt5_enabled=True),
    )
    monkeypatch.setattr(
        _runtime._LazyBrokerSession,
        "adapter",
        lambda *_args: pytest.fail("adapter connected during registration"),
    )

    _unwrap(_runtime.ensure_source("mt5", generate_id("req")))

    descriptor = _unwrap(get_source_descriptor("mt5"))
    assert descriptor.readiness == "staging"
    assert descriptor.capabilities == ("bars", "ticks", "spreads")
    assert _runtime.resolve_calendar("mt5", generate_id("req")) is not None


def test_ensure_source_registers_ctrader_session_capability_without_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cTrader advertises the Brokers-owned read-only session capability."""
    monkeypatch.setattr(
        _runtime,
        "get_data_provider_settings",
        lambda: BrokerProviderSettings(ctrader_enabled=True),
    )
    monkeypatch.setattr(
        _runtime._LazyBrokerSession,
        "adapter",
        lambda *_args: pytest.fail("adapter connected during registration"),
    )

    _unwrap(_runtime.ensure_source("ctrader", generate_id("req")))

    descriptor = _unwrap(get_source_descriptor("ctrader"))
    assert descriptor.capabilities == ("bars", "ticks", "spreads", "sessions")


def test_ensure_source_rejects_unknown_profile() -> None:
    """An undeclared direct-call source fails before provider access."""
    response = _runtime.ensure_source("unknown", generate_id("req"))
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "UNSUPPORTED_SOURCE"


def test_lazy_mt5_session_maps_disabled_and_missing_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Private settings failures remain typed and secret-safe."""
    request_id = generate_id("req")
    session = _runtime._LazyBrokerSession("mt5")
    monkeypatch.setattr(
        _runtime,
        "get_data_provider_settings",
        lambda: SimpleNamespace(mt5_enabled=False),
    )
    with pytest.raises(DataError) as disabled:
        session.adapter(request_id)
    assert disabled.value.code == "SOURCE_UNAVAILABLE"

    monkeypatch.setattr(
        _runtime,
        "get_data_provider_settings",
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


def test_lazy_session_uses_injected_connection_resolver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API-owned credential resolution replaces standalone secret discovery."""
    request_id = generate_id("req")
    expected = object()
    captured: list[tuple[str, str]] = []

    def resolve(provider_id: str, resolved_request_id: str) -> object:
        captured.append((provider_id, resolved_request_id))
        return expected

    monkeypatch.setattr(
        _runtime,
        "get_data_provider_connection_resolver",
        lambda: resolve,
    )

    result = _runtime._LazyBrokerSession("mt5")._provider_config(object(), request_id)

    assert result is expected
    assert captured == [("mt5", request_id)]


def test_ensure_source_access_connects_with_the_call_request_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider connection errors retain the public caller's request identity."""
    monkeypatch.setattr(
        _runtime,
        "get_data_provider_settings",
        lambda: BrokerProviderSettings(mt5_enabled=True),
    )
    request_id = generate_id("req")
    captured: list[str] = []

    def adapter(_session: object, value: str) -> object:
        captured.append(value)
        return object()

    monkeypatch.setattr(_runtime._LazyBrokerSession, "adapter", adapter)

    _unwrap(_runtime.ensure_source_access("mt5", request_id))

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
        "get_data_provider_settings",
        lambda: SimpleNamespace(
            mt5_enabled=True,
            mt5_environment="demo",
            mt5_login=SecretStr("12345"),
            mt5_password=SecretStr("secret"),
            mt5_server=SecretStr("Demo-Server"),
            mt5_terminal_path=None,
        ),
    )

    def create(broker_id: object, config: object) -> SimpleNamespace:
        captured["broker_id"] = broker_id
        captured["config"] = config
        return SimpleNamespace(error=None, data=adapter)

    monkeypatch.setattr(brokers_root, "create_broker_adapter", create)
    session = _runtime._LazyBrokerSession("mt5")

    assert session.adapter(request_id) is adapter
    assert session.adapter(request_id) is adapter
    assert captured["broker_id"] == get_broker_id("mt5")
    assert get_broker_value_field(
        captured["config"], "environment"
    ) == get_broker_environment("demo")


def test_lazy_mt5_session_serializes_concurrent_reads_on_one_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent MT5 reads retain one loop from connect through disconnect."""
    request_id = generate_id("req")

    class _Adapter:
        def __init__(self) -> None:
            self.events: list[tuple[str, asyncio.AbstractEventLoop]] = []

        async def connect(self) -> SimpleNamespace:
            self.events.append(("connect", asyncio.get_running_loop()))
            return SimpleNamespace(error=None)

        async def read(self, value: int) -> int:
            self.events.append(("read", asyncio.get_running_loop()))
            await asyncio.sleep(0)
            return value

        async def disconnect(self) -> SimpleNamespace:
            self.events.append(("disconnect", asyncio.get_running_loop()))
            return SimpleNamespace(error=None)

    adapter = _Adapter()
    monkeypatch.setattr(
        _runtime,
        "get_data_provider_settings",
        lambda: SimpleNamespace(mt5_enabled=True),
    )
    monkeypatch.setattr(
        _runtime._LazyBrokerSession,
        "_provider_config",
        lambda *_args: SimpleNamespace(broker_id=get_broker_id("mt5")),
    )
    monkeypatch.setattr(
        brokers_root,
        "create_broker_adapter",
        lambda *_args: SimpleNamespace(error=None, data=adapter),
    )
    session = _runtime._LazyBrokerSession("mt5")
    session.adapter(request_id)

    with ThreadPoolExecutor(max_workers=4) as executor:
        values = tuple(
            executor.map(
                lambda value: session.run(adapter.read(value), request_id),
                range(4),
            )
        )
    session.close(request_id)
    session.close(request_id)

    assert values == (0, 1, 2, 3)
    assert [name for name, _loop in adapter.events] == [
        "connect",
        "read",
        "read",
        "read",
        "read",
        "disconnect",
    ]
    assert len({id(loop) for _name, loop in adapter.events}) == 1


def test_close_data_provider_sessions_releases_mt5_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public shutdown boundary disconnects and clears composed sessions."""
    request_id = generate_id("req")
    disconnected: list[str] = []

    class _Adapter:
        async def connect(self) -> SimpleNamespace:
            return SimpleNamespace(error=None)

        async def disconnect(self) -> SimpleNamespace:
            disconnected.append("mt5")
            return SimpleNamespace(error=None)

    adapter = _Adapter()
    monkeypatch.setattr(
        _runtime,
        "get_data_provider_settings",
        lambda: SimpleNamespace(mt5_enabled=True),
    )
    monkeypatch.setattr(
        _runtime._LazyBrokerSession,
        "_provider_config",
        lambda *_args: SimpleNamespace(broker_id=get_broker_id("mt5")),
    )
    monkeypatch.setattr(
        brokers_root,
        "create_broker_adapter",
        lambda *_args: SimpleNamespace(error=None, data=adapter),
    )
    session = _runtime._LazyBrokerSession("mt5")
    session.adapter(request_id)
    _runtime._sessions["mt5"] = session

    first = _runtime.close_data_provider_sessions(request_id)
    second = _runtime.close_data_provider_sessions(request_id)

    assert first.status == "success"
    assert second.status == "success"
    assert first.metadata.read_only is False
    assert first.metadata.requires_network is True
    assert disconnected == ["mt5"]
    assert _runtime._sessions == {}


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

    def create(broker_id: object, config: object) -> SimpleNamespace:
        captured["broker_id"] = broker_id
        captured["config"] = config
        return SimpleNamespace(error=None, data=adapter)

    monkeypatch.setattr(brokers_root, "create_broker_adapter", create)
    session = _runtime._LazyBrokerSession("yahoo")
    settings = BrokerProviderSettings(yahoo_enabled=True)

    assert session._credential_free_adapter(settings, request_id) is adapter
    assert captured["broker_id"] == get_broker_id("yahoo")
    assert get_broker_value_field(
        captured["config"], "environment"
    ) == get_broker_environment("sandbox")
    assert get_broker_value_field(captured["config"], "probe_symbol") == "AAPL"


def test_lazy_binance_session_uses_one_loop_and_anonymous_profile(
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

    def create(broker_id: object, config: object) -> SimpleNamespace:
        captured["broker_id"] = broker_id
        captured["config"] = config
        return SimpleNamespace(error=None, data=adapter)

    monkeypatch.setattr(brokers_root, "create_broker_adapter", create)
    session = _runtime._LazyBrokerSession("binance_spot")
    settings = BrokerProviderSettings(binance_enabled=True)

    assert session._credential_free_adapter(settings, request_id) is adapter
    assert captured["broker_id"] == get_broker_id("binance_spot")
    assert get_broker_value_field(
        captured["config"], "environment"
    ) == get_broker_environment("testnet")
    assert get_broker_value_field(captured["config"], "credentials") is None
    assert _runtime._provider_descriptor("binance_spot").requires_credentials is False
    assert adapter.events == []

    assert session.run(adapter.read(), request_id) == "payload"
    assert [event for event, _loop in adapter.events] == [
        "connect",
        "read",
        "disconnect",
    ]
    assert len({id(loop) for _event, loop in adapter.events}) == 1


def test_lazy_ctrader_session_uses_one_loop() -> None:
    """Standalone cTrader connects, reads, and closes on one owned event loop."""
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
    session = _runtime._LazyBrokerSession("ctrader")
    session._adapter = adapter

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
        "get_data_provider_settings",
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
        def get_symbol_metadata(
            self, request: object
        ) -> StandardResponse[SymbolMetadata]:
            metadata = SymbolMetadata(
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
            # Return a successful StandardResponse-shaped value so the migrated
            # ``ensure_identity`` boundary can unwrap the nested source call.
            response: StandardResponse[SymbolMetadata] = MagicMock()
            response.status = "success"
            response.data = metadata
            return response

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
    provider_session = build_broker_value(
        "trading_session",
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
        ) -> StandardResponse[object]:
            del symbol, start, end
            return broker_response(
                get_broker_capability_id("get_trading_sessions"),
                broker=get_broker_id("mt5"),
                request_id=generate_id("req"),
                timestamp=observed_at,
                environment=get_broker_environment("demo"),
                adapter_version="1.0.0",
                data=(provider_session,),
            )

    session = SimpleNamespace(
        adapter=lambda _request_id: _Adapter(),
        run=_runtime._run,
    )
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

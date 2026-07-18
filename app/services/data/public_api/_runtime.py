"""Private lazy composition for standalone Data retrieval operations."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal

from pydantic import SecretStr

from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    BrokerResult,
    create_broker_adapter,
)
from app.services.data.config import get_data_settings
from app.services.data.contracts import (
    MarketSchedule,
    SessionWindow,
    SourceDescriptor,
    SourceIdentity,
    SourceIdentityRequest,
    SourceLicensePolicy,
    SymbolMetadataRequest,
)
from app.services.data.contracts.errors import DataError
from app.services.data.sources.external import ExternalMarketDataSource
from app.services.data.sources.registry import (
    get_source_descriptor,
    register_source,
    register_source_identity,
    resolve_source,
    resolve_source_identity,
)
from app.services.data.storage.migrations import run_data_migrations
from app.utils import AppSettings, generate_id, logger

if TYPE_CHECKING:
    from app.services.data.access.sessions import MarketCalendar

_lock = threading.RLock()
_calendars: dict[str, MarketCalendar] = {}
_sessions: dict[str, _LazyBrokerSession] = {}
_migrated_targets: set[tuple[str, str]] = set()


class _ProviderRuntimeSettings(AppSettings):
    """Private provider settings used only by the standalone Data facade."""

    mt5_enabled: bool = False
    mt5_environment: Literal["demo", "live"] = "demo"
    mt5_login: SecretStr | None = None
    mt5_password: SecretStr | None = None
    mt5_server: SecretStr | None = None
    mt5_terminal_path: SecretStr | None = None


def _run[T](operation: Coroutine[Any, Any, T], request_id: str) -> T:
    """Run one async Brokers operation behind the synchronous Data facade.

    Returns:
        The completed operation result.

    Raises:
        DataError: If the provider operation cannot complete.
    """
    try:
        return asyncio.run(operation)
    except DataError:
        raise
    except Exception as error:
        logger.error("Standalone Data provider operation failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "provider_runtime"},
            request_id=request_id,
        ) from error


def _require_broker_result[T](
    result: BrokerResult[T],
    *,
    operation: str,
    request_id: str,
) -> T:
    """Return a successful Brokers value or map the failure to Data.

    Raises:
        DataError: If Brokers returned an error or no result value.
    """
    if result.error is not None or result.data is None:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": operation},
            request_id=request_id,
        )
    return result.data


class _LazyBrokerSession:
    """Create and connect one read-only broker adapter on first provider read."""

    def __init__(self, source_id: str) -> None:
        self._source_id = source_id
        self._adapter: BrokerAdapter | None = None
        self._lock = threading.RLock()

    def adapter(self, request_id: str) -> BrokerAdapter:
        """Return the connected adapter for this source.

        Raises:
            DataError: If configuration, credentials, or connection fail.
        """
        with self._lock:
            if self._adapter is not None:
                return self._adapter
            if self._source_id != BrokerId.MT5.value:
                raise DataError(
                    "UNSUPPORTED_SOURCE",
                    safe_details={"source_id": self._source_id},
                    request_id=request_id,
                )
            try:
                settings = _ProviderRuntimeSettings()
            except ValueError as error:
                raise DataError(
                    "INVALID_INPUT",
                    safe_details={"field": "provider_settings"},
                    request_id=request_id,
                ) from error
            if not settings.mt5_enabled:
                raise DataError(
                    "SOURCE_UNAVAILABLE",
                    safe_details={"source_id": self._source_id},
                    request_id=request_id,
                )
            login = settings.mt5_login
            password = settings.mt5_password
            server = settings.mt5_server
            if login is None or password is None or server is None:
                raise DataError(
                    "CREDENTIALS_MISSING",
                    safe_details={"source_id": self._source_id},
                    request_id=request_id,
                )
            credentials = {
                "login": login,
                "password": password,
                "server": server,
            }
            if settings.mt5_terminal_path is not None:
                credentials["terminal_path"] = settings.mt5_terminal_path
            try:
                config = BrokerConnectionConfig(
                    broker_id=BrokerId.MT5,
                    environment=BrokerEnvironment(settings.mt5_environment),
                    provider_enabled=True,
                    connect_timeout_sec=10.0,
                    request_timeout_sec=30.0,
                    transport_reconnect_max_attempts=3,
                    stream_buffer_size=1_000,
                    circuit_failure_threshold=5,
                    circuit_recovery_timeout_sec=30.0,
                    circuit_half_open_max_calls=1,
                    account_reference=login.get_secret_value(),
                    credentials=credentials,
                )
            except ValueError as error:
                raise DataError(
                    "INVALID_INPUT",
                    safe_details={"field": "provider_settings"},
                    request_id=request_id,
                ) from error
            adapter = _require_broker_result(
                create_broker_adapter(BrokerId.MT5, config),
                operation="create_broker_adapter",
                request_id=request_id,
            )
            connect_result = _run(adapter.connect(), request_id)
            if connect_result.error is not None:
                raise DataError(
                    "SOURCE_UNAVAILABLE",
                    safe_details={"operation": "connect"},
                    request_id=request_id,
                )
            self._adapter = adapter
            return adapter

    def source(self) -> ExternalMarketDataSource:
        """Create the Data-owned source wrapper lazily.

        Returns:
            The connected provider-neutral source wrapper.
        """
        request_id = generate_id("req")
        return ExternalMarketDataSource(
            self._source_id,
            self.adapter(request_id),
        )


class _BrokerMarketCalendar:
    """Adapt provider-supplied sessions to the Data calendar contract."""

    def __init__(self, session: _LazyBrokerSession) -> None:
        self._session = session

    def get_schedule(
        self,
        *,
        source_id: str,
        symbol: str,
        timezone: str,
        observed_at: datetime,
        request_id: str,
    ) -> MarketSchedule:
        """Return current provider-supplied sessions as normalized UTC windows."""
        adapter = self._session.adapter(request_id)
        result = _run(
            adapter.get_trading_sessions(
                symbol=symbol,
                start=observed_at,
                end=observed_at + timedelta(days=7),
            ),
            request_id,
        )
        sessions = _require_broker_result(
            result,
            operation="trading_sessions",
            request_id=request_id,
        )
        windows = tuple(
            SessionWindow(
                label=f"session-{index}",
                opens_at=session.opens_at,
                closes_at=session.closes_at,
            )
            for index, session in enumerate(sessions, start=1)
        )
        return MarketSchedule(
            source_id=source_id,
            symbol=symbol,
            timezone=timezone,
            hours=windows,
            sessions=windows,
            observed_at=observed_at,
            request_id=request_id,
        )


def _mt5_descriptor() -> SourceDescriptor:
    """Return the Data-owned policy declaration for the Brokers MT5 profile."""
    source_id = BrokerId.MT5.value
    return SourceDescriptor(
        source_id=source_id,
        readiness="staging",
        capabilities=("bars", "ticks", "spreads"),
        requires_credentials=True,
        requires_network=True,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="brokers-adapter-v1",
        license_policy=SourceLicensePolicy(
            source_id=source_id,
            status="restricted",
            permitted_workflows=(
                "research",
                "backtest",
                "validation",
                "risk",
                "execution_bound",
            ),
            export_allowed=False,
            attribution_required=False,
        ),
        identity_mapping_revision="provider-confirmed-v1",
    )


def ensure_source(source_id: str, request_id: str) -> None:
    """Register one supported source and its private lazy dependencies.

    Raises:
        DataError: If the source is unsupported or registration fails.
    """
    try:
        get_source_descriptor(source_id)
        return
    except DataError as error:
        if error.code != "SOURCE_UNAVAILABLE":
            raise
    if source_id != BrokerId.MT5.value:
        raise DataError(
            "UNSUPPORTED_SOURCE",
            safe_details={"source_id": source_id},
            request_id=request_id,
        )
    with _lock:
        try:
            get_source_descriptor(source_id)
            return
        except DataError as error:
            if error.code != "SOURCE_UNAVAILABLE":
                raise
        session = _LazyBrokerSession(source_id)
        register_source(_mt5_descriptor(), session.source)
        _sessions[source_id] = session
        _calendars[source_id] = _BrokerMarketCalendar(session)


def ensure_source_access(source_id: str, request_id: str) -> None:
    """Connect a facade-composed source before its first provider read.

    Raises:
        DataError: If provider composition or connection fails.
    """
    ensure_source(source_id, request_id)
    with _lock:
        session = _sessions.get(source_id)
    if session is not None:
        session.adapter(request_id)


def ensure_identity(source_id: str, symbol: str, request_id: str) -> None:
    """Resolve or register one provider-confirmed identity mapping.

    Raises:
        DataError: If provider metadata cannot confirm the identity.
    """
    ensure_source_access(source_id, request_id)
    identity_request = SourceIdentityRequest(
        source_id=source_id,
        identity=symbol,
        request_id=request_id,
    )
    try:
        resolve_source_identity(identity_request)
        return
    except DataError as error:
        if error.code != "MISSING_ASSET_METADATA":
            raise
    metadata = resolve_source(source_id).get_symbol_metadata(
        SymbolMetadataRequest(
            source_id=source_id,
            symbol=symbol,
            request_id=request_id,
        )
    )
    register_source_identity(
        SourceIdentity(
            source_id=source_id,
            canonical_symbol=symbol,
            friendly_name=symbol,
            provider_symbol=metadata.provider_symbol,
            mapping_revision=get_source_descriptor(source_id).identity_mapping_revision,
            provenance={
                "method": "provider_metadata",
                "provider_symbol": metadata.provider_symbol,
            },
            request_id=request_id,
        )
    )


def ensure_storage(request_id: str) -> None:
    """Apply Data migrations once per configured storage target."""
    settings = get_data_settings()
    target = (str(settings.data_dir), str(settings.database_url))
    with _lock:
        if target in _migrated_targets:
            return
        run_data_migrations(request_id)
        _migrated_targets.add(target)


def resolve_calendar(source_id: str, request_id: str) -> MarketCalendar:
    """Return the private authoritative calendar for one source.

    Raises:
        DataError: If the source has no authoritative calendar.
    """
    ensure_source(source_id, request_id)
    with _lock:
        calendar = _calendars.get(source_id)
    if calendar is None:
        raise DataError(
            "UNSUPPORTED_OPERATION",
            safe_details={"operation": "market_calendar"},
            request_id=request_id,
        )
    return calendar


__all__ = [
    "ensure_identity",
    "ensure_source",
    "ensure_source_access",
    "ensure_storage",
    "resolve_calendar",
]

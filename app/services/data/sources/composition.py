"""Lazy composition and migrations execution trigger for standalone Data operations."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Coroutine, Mapping
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal

from pydantic import SecretStr, ValidationError

from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    BrokerResult,
    create_broker_adapter,
)
from app.services.data._settings import (
    LOCAL_SYMBOL_MANIFEST_NAME,
    get_data_settings,
)
from app.services.data.contracts import DataError
from app.services.data.market_data.symbol_metadata import (
    SymbolMetadata,
    SymbolMetadataRequest,
)
from app.services.data.persistence.migrations import run_data_migrations
from app.services.data.sources.broker_adapter import ExternalMarketDataSource
from app.services.data.sources.contracts import (
    SourceDescriptor,
    SourceIdentity,
    SourceIdentityRequest,
    SourceLicensePolicy,
)
from app.services.data.sources.local_adapter import LocalMarketDataSource
from app.services.data.sources.registry import (
    get_source_descriptor,
    register_source,
    register_source_identity,
    resolve_source,
    resolve_source_identity,
)
from app.services.data.time_sessions.contracts import MarketSchedule, SessionWindow
from app.utils import AppSettings, generate_id, logger

if TYPE_CHECKING:
    from app.services.data.time_sessions.schedule import MarketCalendar

_lock = threading.RLock()
_calendars: dict[str, MarketCalendar] = {}
_sessions: dict[str, _LazyBrokerSession] = {}
_migrated_targets: set[tuple[str, str]] = set()


class _ProviderRuntimeSettings(AppSettings):
    """Private provider settings used only by the standalone Data runtime."""

    mt5_enabled: bool = False
    mt5_environment: Literal["demo", "live"] = "demo"
    mt5_login: SecretStr | None = None
    mt5_password: SecretStr | None = None
    mt5_server: SecretStr | None = None
    mt5_terminal_path: SecretStr | None = None
    ctrader_enabled: bool = False
    binance_enabled: bool = False
    dukascopy_enabled: bool = False
    yahoo_enabled: bool = False


# Provider read capabilities mirror the Brokers capability catalogue exactly; Data
# never declares a capability the owning adapter does not implement.
_PROVIDER_CAPABILITIES: Final[Mapping[str, tuple[str, ...]]] = {
    BrokerId.MT5.value: ("bars", "ticks", "spreads"),
    BrokerId.CTRADER.value: ("bars", "ticks", "spreads"),
    BrokerId.BINANCE_SPOT.value: ("bars", "ticks", "spreads"),
    BrokerId.DUKASCOPY.value: ("bars", "ticks"),
    BrokerId.YAHOO.value: ("bars",),
}

# Providers whose public market data needs no credential material.
_CREDENTIAL_FREE_PROVIDERS: Final[frozenset[str]] = frozenset(
    {
        BrokerId.BINANCE_SPOT.value,
        BrokerId.DUKASCOPY.value,
        BrokerId.YAHOO.value,
    }
)

# Redistribution posture per provider, derived from each platform's published terms.
_PROVIDER_LICENSE_STATUS: Final[
    Mapping[str, Literal["approved", "restricted", "unknown"]]
] = {
    BrokerId.MT5.value: "restricted",
    BrokerId.CTRADER.value: "restricted",
    BrokerId.BINANCE_SPOT.value: "restricted",
    BrokerId.DUKASCOPY.value: "restricted",
    BrokerId.YAHOO.value: "restricted",
}

_PROVIDER_ENABLED_FIELDS: Final[Mapping[str, str]] = {
    BrokerId.MT5.value: "mt5_enabled",
    BrokerId.CTRADER.value: "ctrader_enabled",
    BrokerId.BINANCE_SPOT.value: "binance_enabled",
    BrokerId.DUKASCOPY.value: "dukascopy_enabled",
    BrokerId.YAHOO.value: "yahoo_enabled",
}

_YAHOO_PROBE_SYMBOL: Final = "AAPL"


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
    """Create one read-only broker adapter and govern its standalone lifecycle."""

    def __init__(self, source_id: str) -> None:
        self._source_id = source_id
        self._adapter: BrokerAdapter | None = None
        self._lock = threading.RLock()

    def adapter(self, request_id: str) -> BrokerAdapter:
        """Return the configured adapter for this source.

        Binance remains disconnected until ``run`` so its client is created and
        consumed on the same event loop. Other providers retain a connected adapter.

        Raises:
            DataError: If configuration, credentials, or connection fail.
        """
        with self._lock:
            if self._adapter is not None:
                return self._adapter
            if self._source_id not in _PROVIDER_CAPABILITIES:
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
            enabled_field = _PROVIDER_ENABLED_FIELDS[self._source_id]
            if not getattr(settings, enabled_field):
                raise DataError(
                    "SOURCE_UNAVAILABLE",
                    safe_details={"source_id": self._source_id},
                    request_id=request_id,
                )
            if self._source_id != BrokerId.MT5.value:
                return self._credential_free_adapter(request_id)
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

    def run[T](self, operation: Coroutine[Any, Any, T], request_id: str) -> T:
        """Execute one provider operation with the required loop ownership.

        Binance's asynchronous HTTP client is bound to the event loop where it is
        created. Standalone Data calls therefore connect, read, and disconnect on
        one loop instead of carrying the client across separate ``asyncio.run``
        calls. Other adapters retain their existing connected-session behavior.

        Args:
            operation: Broker coroutine to execute.
            request_id: Canonical request identifier for mapped failures.

        Returns:
            Completed broker operation result.

        Raises:
            DataError: If connection or operation execution fails.
        """
        if self._source_id != BrokerId.BINANCE_SPOT.value:
            return _run(operation, request_id)
        with self._lock:
            adapter = self.adapter(request_id)

            async def execute() -> T:
                connected = False
                try:
                    connect_result = await adapter.connect()
                    if connect_result.error is not None:
                        raise DataError(
                            "SOURCE_UNAVAILABLE",
                            safe_details={"operation": "connect"},
                            request_id=request_id,
                        )
                    connected = True
                    return await operation
                finally:
                    if not connected:
                        operation.close()
                    else:
                        disconnect_result = await adapter.disconnect()
                        if disconnect_result.error is not None:
                            logger.warning(
                                "Standalone Binance session disconnect failed"
                            )

            return _run(execute(), request_id)

    def _credential_free_adapter(self, request_id: str) -> BrokerAdapter:
        """Build one non-MT5 provider adapter and connect when loop-safe.

        Binance Spot, Dukascopy, and Yahoo serve public data and need no credential
        material. cTrader requires credentials that only an approved composition
        root resolves, so Data fails closed rather than constructing a partial
        configuration.

        Raises:
            DataError: If credentials are required, or construction or connection
                fails.
        """
        if self._source_id not in _CREDENTIAL_FREE_PROVIDERS:
            logger.info(
                "Provider %s requires composition-root credentials", self._source_id
            )
            raise DataError(
                "CREDENTIALS_MISSING",
                safe_details={"source_id": self._source_id},
                request_id=request_id,
            )
        try:
            env = (
                BrokerEnvironment.LIVE
                if self._source_id == BrokerId.BINANCE_SPOT.value
                else BrokerEnvironment.SANDBOX
            )
            config = BrokerConnectionConfig(
                broker_id=BrokerId(self._source_id),
                environment=env,
                provider_enabled=True,
                connect_timeout_sec=10.0,
                request_timeout_sec=30.0,
                transport_reconnect_max_attempts=3,
                stream_buffer_size=1_000,
                circuit_failure_threshold=5,
                circuit_recovery_timeout_sec=30.0,
                circuit_half_open_max_calls=1,
                probe_symbol=(
                    _YAHOO_PROBE_SYMBOL
                    if self._source_id == BrokerId.YAHOO.value
                    else None
                ),
            )
        except ValueError as error:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "provider_settings"},
                request_id=request_id,
            ) from error
        adapter = _require_broker_result(
            create_broker_adapter(BrokerId(self._source_id), config),
            operation="create_broker_adapter",
            request_id=request_id,
        )
        if self._source_id == BrokerId.BINANCE_SPOT.value:
            self._adapter = adapter
            return adapter
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
            The configured provider-neutral source wrapper.
        """
        request_id = generate_id("req")
        return ExternalMarketDataSource(
            self._source_id,
            self.adapter(request_id),
            runner=self.run,
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


def _provider_descriptor(source_id: str) -> SourceDescriptor:
    """Return the Data-owned policy declaration for one broker provider facade.

    Provider sources enter at `staging` readiness only. Reaching `production`
    requires the governed `WF-DATA-011` promotion, and separately requires the
    Brokers catalogue to record read-release evidence for that provider; until it
    does, reads fail closed with the Brokers capability reason rather than silently
    returning nothing.

    Raises:
        DataError: If the identifier is not a supported provider facade.
    """
    capabilities = _PROVIDER_CAPABILITIES.get(source_id)
    if capabilities is None:
        raise DataError("UNSUPPORTED_SOURCE", safe_details={"source_id": source_id})
    return SourceDescriptor(
        source_id=source_id,
        readiness="staging",
        capabilities=capabilities,
        requires_credentials=source_id not in _CREDENTIAL_FREE_PROVIDERS,
        requires_network=True,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="brokers-adapter-v1",
        license_policy=SourceLicensePolicy(
            source_id=source_id,
            status=_PROVIDER_LICENSE_STATUS[source_id],
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


def _local_descriptor(source_id: str) -> SourceDescriptor:
    """Return the Data-owned policy declaration for one local artifact source.

    Local sources reach `production` readiness without a `WF-DATA-011` promotion
    because their evidence is structural rather than operational: the read is
    offline, deterministic, and credential-free, and every claim below is
    verifiable against the descriptor's own `requires_credentials` and
    `requires_network` fields. No operational evidence is asserted.
    """
    return SourceDescriptor(
        source_id=source_id,
        readiness="production",
        capabilities=("bars", "ticks", "spreads"),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="local-artifact-v1",
        license_policy=SourceLicensePolicy(
            source_id=source_id,
            status="approved",
            permitted_workflows=(
                "research",
                "backtest",
                "validation",
                "risk",
                "execution_bound",
            ),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="local-declared-v1",
        promotion_evidence=(
            "offline_deterministic_artifact",
            "no_credentials_required",
            "no_network_required",
        ),
    )


def _resolve_raw_root(request_id: str) -> Path:
    """Resolve the configured absolute local artifact root.

    Raises:
        DataError: If `DATA_DIR` is unset or the raw root is not a directory.
    """
    settings = get_data_settings()
    data_dir = settings.data_dir
    if data_dir is None:
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"field": "DATA_DIR"},
            request_id=request_id,
        )
    return (data_dir.expanduser().resolve() / settings.data_raw_root).resolve()


def _require_manifest_object(declared: object) -> None:
    """Reject a local symbol manifest whose root is not a JSON object.

    Raises:
        TypeError: If the decoded manifest root is not a mapping.
    """
    if not isinstance(declared, dict):
        raise TypeError("local symbol manifest must be a JSON object")


def _load_local_symbol_metadata(
    source_id: str,
    raw_root: Path,
    request_id: str,
) -> Mapping[str, SymbolMetadata]:
    """Load operator-declared symbol metadata for one local source.

    Metadata is declared, never inferred: a local artifact cannot supply
    `asset_class`, so an absent manifest yields no symbols rather than a fabricated
    default. Discovery then returns an empty page and retrieval fails closed with
    `MISSING_ASSET_METADATA` for the requested symbol.

    Raises:
        DataError: If the manifest exists but is unreadable or malformed.
    """
    manifest_path = raw_root / LOCAL_SYMBOL_MANIFEST_NAME
    if not manifest_path.is_file():
        logger.info(
            "No local symbol manifest for source %s; composing with no symbols",
            source_id,
        )
        return {}
    try:
        with manifest_path.open(encoding="utf-8") as stream:
            declared = json.load(stream)
        _require_manifest_object(declared)
        metadata = {
            symbol: SymbolMetadata.model_validate(
                {
                    **entry,
                    "canonical_symbol": symbol,
                    "provider_symbol": entry.get("provider_symbol", symbol),
                    "source_id": source_id,
                    "request_id": request_id,
                }
            )
            for symbol, entry in declared.items()
        }
    except (OSError, TypeError, ValueError, ValidationError) as error:
        logger.error("Local symbol manifest for source %s is invalid", source_id)
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={"field": LOCAL_SYMBOL_MANIFEST_NAME},
            request_id=request_id,
        ) from error
    logger.info(
        "Loaded %d declared local symbols for source %s", len(metadata), source_id
    )
    return metadata


def _register_local_source(source_id: str, request_id: str) -> None:
    """Register one configured local artifact source and its declared identities."""
    raw_root = _resolve_raw_root(request_id)
    if not raw_root.is_dir():
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"field": "DATA_RAW_ROOT"},
            request_id=request_id,
        )
    descriptor = _local_descriptor(source_id)
    metadata = _load_local_symbol_metadata(source_id, raw_root, request_id)
    identities = tuple(
        SourceIdentity(
            source_id=source_id,
            canonical_symbol=item.canonical_symbol,
            friendly_name=item.canonical_symbol,
            provider_symbol=item.provider_symbol,
            mapping_revision=descriptor.identity_mapping_revision,
            provenance={"method": "operator_declared"},
            request_id=request_id,
        )
        for item in metadata.values()
    )
    artifact_format: Literal["csv", "parquet"] = (
        "parquet" if source_id == "parquet" else "csv"
    )
    register_source(
        descriptor,
        lambda: LocalMarketDataSource(
            source_id=source_id,
            raw_root=raw_root,
            metadata=metadata,
            format_preference=artifact_format,
        ),
        identities,
    )


def list_composable_sources() -> tuple[str, ...]:
    """Return every source identifier the current configuration can compose.

    Returns:
        Sorted local and provider identifiers, including already-registered ones,
        so a caller can discover valid `source_id` values without trial and error.
    """
    logger.debug("Listing composable DATA source identifiers")
    settings = get_data_settings()
    provider_settings = _ProviderRuntimeSettings()
    enabled_providers = {
        broker_id
        for broker_id, field in _PROVIDER_ENABLED_FIELDS.items()
        if getattr(provider_settings, field, False)
    }
    return tuple(
        sorted(
            {
                *settings.data_local_sources,
                *(
                    source
                    for source in settings.data_provider_sources
                    if source in _PROVIDER_CAPABILITIES
                ),
                *enabled_providers,
            }
        )
    )


def ensure_source(source_id: str, request_id: str) -> None:
    """Register one supported source and its private lazy dependencies.

    Composition dispatches on source kind. Local artifact sources need no
    credentials, network, or promotion evidence and register at `production`
    readiness; the MT5 broker profile composes a lazy read-only provider session.

    Raises:
        DataError: If the source is unsupported or registration fails.
    """
    try:
        get_source_descriptor(source_id)
        return
    except DataError as error:
        if error.code != "SOURCE_UNAVAILABLE":
            raise
    settings = get_data_settings()
    provider_settings = _ProviderRuntimeSettings()
    enabled_providers = {
        broker_id
        for broker_id, field in _PROVIDER_ENABLED_FIELDS.items()
        if getattr(provider_settings, field, False)
    }
    is_local = source_id in settings.data_local_sources
    is_provider = source_id in enabled_providers or (
        source_id in settings.data_provider_sources
        and source_id in _PROVIDER_CAPABILITIES
    )
    if not is_local and not is_provider:
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
        if is_local:
            _register_local_source(source_id, request_id)
            return
        session = _LazyBrokerSession(source_id)
        descriptor = (
            _mt5_descriptor()
            if source_id == BrokerId.MT5.value
            else _provider_descriptor(source_id)
        )
        identities = (
            (
                SourceIdentity(
                    source_id=source_id,
                    canonical_symbol=_YAHOO_PROBE_SYMBOL,
                    friendly_name=_YAHOO_PROBE_SYMBOL,
                    provider_symbol=_YAHOO_PROBE_SYMBOL,
                    mapping_revision=descriptor.identity_mapping_revision,
                    provenance={"method": "application_declared"},
                    request_id=request_id,
                ),
            )
            if source_id == BrokerId.YAHOO.value
            else ()
        )
        register_source(descriptor, session.source, identities)
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
    "list_composable_sources",
    "resolve_calendar",
]

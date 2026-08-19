"""Lazy composition and migrations execution trigger for standalone Data operations."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Coroutine, Mapping
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, cast

from pydantic import ValidationError

from app.services.data._settings import (
    LOCAL_SYMBOL_MANIFEST_NAME,
    get_data_provider_connection_resolver,
    get_data_provider_settings,
    get_data_settings,
)
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
    unwrap_data_response,
)
from app.services.data.market_data.symbol_metadata import (
    SymbolMetadata,
    SymbolMetadataRequest,
)
from app.services.data.persistence.migrations import run_data_migrations
from app.services.data.sources.async_runtime import _PersistentAsyncRunner
from app.services.data.sources.broker_adapter import ExternalMarketDataSource
from app.services.data.sources.contracts import (
    SourceDescriptor,
    SourceIdentity,
    SourceIdentityRequest,
    SourceLicensePolicy,
)
from app.services.data.sources.local_adapter import LocalMarketDataSource
from app.services.data.sources.registry import (
    _get_source_descriptor_raw,
    _register_source_raw,
    _resolve_source_raw,
    register_source_identity,
    resolve_source_identity,
)
from app.services.data.time_sessions.contracts import MarketSchedule, SessionWindow
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.time_sessions.schedule import MarketCalendar

_lock = threading.RLock()
_calendars: dict[str, MarketCalendar] = {}
_sessions: dict[str, _LazyBrokerSession] = {}
_migrated_targets: set[tuple[str, str]] = set()


# Provider read capabilities mirror the Brokers capability catalogue exactly; Data
# never declares a capability the owning adapter does not implement.
_MT5 = "mt5"
_CTRADER = "ctrader"
_BINANCE_SPOT = "binance_spot"
_DUKASCOPY = "dukascopy"
_YAHOO = "yahoo"

_PROVIDER_CAPABILITIES: Final[Mapping[str, tuple[str, ...]]] = {
    _MT5: ("bars", "ticks", "spreads"),
    _CTRADER: ("bars", "ticks", "spreads", "sessions"),
    _BINANCE_SPOT: ("bars", "ticks", "spreads"),
    _DUKASCOPY: ("bars", "ticks"),
    _YAHOO: ("bars",),
}

# Providers whose public market data needs no credential material.
_CREDENTIAL_FREE_PROVIDERS: Final[frozenset[str]] = frozenset(
    {
        _BINANCE_SPOT,
        _DUKASCOPY,
        _YAHOO,
    }
)

# Redistribution posture per provider, derived from each platform's published terms.
_PROVIDER_LICENSE_STATUS: Final[
    Mapping[str, Literal["approved", "restricted", "unknown"]]
] = {
    _MT5: "restricted",
    _CTRADER: "restricted",
    _BINANCE_SPOT: "restricted",
    _DUKASCOPY: "restricted",
    _YAHOO: "restricted",
}

_PROVIDER_ENABLED_FIELDS: Final[Mapping[str, str]] = {
    _MT5: "mt5_enabled",
    _CTRADER: "ctrader_enabled",
    _BINANCE_SPOT: "binance_enabled",
    _DUKASCOPY: "dukascopy_enabled",
    _YAHOO: "yahoo_enabled",
}
_LOOP_BOUND_PROVIDERS: Final[frozenset[str]] = frozenset({_BINANCE_SPOT, _CTRADER})

_YAHOO_PROBE_SYMBOL: Final = "AAPL"


def _run[T](operation: Coroutine[Any, Any, T], request_id: str) -> T:
    """Run one async Brokers operation behind the synchronous Data facade.

    Args:
        operation: The ``operation`` argument.
        request_id: The ``request_id`` argument.

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
        logger.exception("Standalone Data provider operation failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "provider_runtime"},
            request_id=request_id,
        ) from error


def _require_broker_result[T](
    result: StandardResponse[T],
    *,
    operation: str,
    request_id: str,
) -> T:
    """Return a successful Brokers value or map the failure to Data.

    Args:
        result: The ``result`` argument.
        operation: The ``operation`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If Brokers returned an error or no result value.
    """
    if result.error is not None or result.data is None:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": operation},
            request_id=request_id,
        )
    return cast("T", result.data)


class _LazyBrokerSession:
    """Create one read-only broker adapter and govern its standalone lifecycle."""

    def __init__(self, source_id: str) -> None:
        """Initialize one lazy session for a configured provider source.

        Args:
            source_id: Canonical provider source identifier.
        """
        self._source_id = source_id
        self._adapter: Any | None = None
        self._async_runner: _PersistentAsyncRunner | None = None
        self._lock = threading.RLock()

    def adapter(self, request_id: str) -> Any:  # noqa: ANN401
        """Return the configured adapter for this source.

        Loop-bound providers remain disconnected until ``run`` so their clients are
        created and consumed on the same event loop. Other providers retain a
        connected adapter.

        Args:
            request_id: The ``request_id`` argument.

        Returns:
            The result produced by the operation.

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
                settings = get_data_provider_settings()
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
            if self._source_id == _CTRADER:
                return self._ctrader_adapter(settings, request_id)
            if self._source_id != _MT5:
                return self._credential_free_adapter(settings, request_id)
            return self._mt5_adapter(settings, request_id)

    def _provider_config(
        self,
        settings: object,
        request_id: str,
    ) -> Any:  # noqa: ANN401
        """Resolve one governed provider connection configuration via Brokers.

        Credential resolution and environment enforcement are owned by the
        Brokers domain; Data selects a route only.

        Args:
            settings: Effective broker provider settings.
            request_id: Canonical request identity.

        Returns:
            Resolved broker connection configuration.

        Raises:
            DataError: If credentials are missing, the environment is live, or
                the broker identifier is unsupported.
        """
        from app.services.brokers import resolve_provider_connection_config

        resolver = get_data_provider_connection_resolver()
        if resolver is not None:
            return resolver(self._source_id, request_id)
        try:
            return resolve_provider_connection_config(
                self._source_id, settings=settings
            )
        except ValueError as error:
            message = str(error)
            if "credentials missing" in message:
                raise DataError(
                    "CREDENTIALS_MISSING",
                    safe_details={"source_id": self._source_id},
                    request_id=request_id,
                ) from error
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "provider_settings"},
                request_id=request_id,
            ) from error

    def _mt5_adapter(
        self,
        settings: object,
        request_id: str,
    ) -> object:
        """Build and connect the configured MT5 read adapter.

        Args:
            settings: Effective broker provider settings.
            request_id: Canonical request identity.

        Returns:
            Connected MT5 adapter.

        Raises:
            DataError: If credentials, configuration, or connection are invalid.
        """
        from app.services.brokers import create_broker_adapter

        config = self._provider_config(settings, request_id)
        adapter: Any = _require_broker_result(
            create_broker_adapter(config.broker_id, config),
            operation="create_broker_adapter",
            request_id=request_id,
        )
        runner = _PersistentAsyncRunner(thread_name="data-mt5-event-loop")
        try:
            connect_result = runner.run(adapter.connect())
        except Exception:
            runner.close()
            raise
        if connect_result.error is not None:
            try:
                runner.run(adapter.disconnect())
            finally:
                runner.close()
            raise DataError(
                "SOURCE_UNAVAILABLE",
                safe_details={"operation": "connect"},
                request_id=request_id,
            )
        self._adapter = adapter
        self._async_runner = runner
        return adapter

    def _ctrader_adapter(
        self,
        settings: object,
        request_id: str,
    ) -> object:
        """Build the configured cTrader read adapter.

        Args:
            settings: Effective broker provider settings.
            request_id: Canonical request identity.

        Returns:
            Disconnected cTrader adapter ready for one loop-owned operation.

        Raises:
            DataError: If credentials, configuration, or connection are invalid.
        """
        from app.services.brokers import create_broker_adapter

        config = self._provider_config(settings, request_id)
        adapter: Any = _require_broker_result(
            create_broker_adapter(config.broker_id, config),
            operation="create_broker_adapter",
            request_id=request_id,
        )
        self._adapter = adapter
        return adapter

    def run[T](self, operation: Coroutine[Any, Any, T], request_id: str) -> T:
        """Execute one provider operation with the required loop ownership.

        Binance and cTrader clients are bound to the event loop where they are
        created. Standalone Data calls therefore connect, read, and disconnect on
        one loop instead of carrying a client across separate ``asyncio.run`` calls.
        Other adapters retain their existing connected-session behavior.

        Args:
            operation: Broker coroutine to execute.
            request_id: Canonical request identifier for mapped failures.

        Returns:
            Completed broker operation result.

        Raises:
            DataError: If connection or operation execution fails.
        """
        if self._source_id == _MT5:
            with self._lock:
                self.adapter(request_id)
                runner = self._async_runner
                if runner is None:
                    operation.close()
                    raise DataError(
                        "SOURCE_UNAVAILABLE",
                        safe_details={"operation": "provider_runtime"},
                        request_id=request_id,
                    )
                return runner.run(operation)
        if self._source_id not in _LOOP_BOUND_PROVIDERS:
            return _run(operation, request_id)
        with self._lock:
            adapter = self.adapter(request_id)

            async def execute() -> T:
                """Connect, execute, and release one loop-bound read session.

                Returns:
                    The result produced by the operation.

                Raises:
                    DataError: If the operation cannot be completed safely.
                """
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
                            logger.warning("Standalone provider disconnect failed")

            return _run(execute(), request_id)

    def close(self, request_id: str) -> None:
        """Disconnect and release this session's owned runtime resources.

        Args:
            request_id: Canonical shutdown request identity.
        """
        with self._lock:
            adapter = self._adapter
            runner = self._async_runner
            self._adapter = None
            self._async_runner = None
            if adapter is None:
                if runner is not None:
                    runner.close()
                return
            if runner is not None:
                try:
                    result = runner.run(adapter.disconnect())
                    if result.error is not None:
                        logger.warning("MT5 provider disconnect returned an error")
                finally:
                    runner.close()
                return
            disconnect = getattr(adapter, "disconnect", None)
            if callable(disconnect):
                result = _run(disconnect(), request_id)
                if result.error is not None:
                    logger.warning("Provider disconnect returned an error")

    def _credential_free_adapter(
        self,
        settings: object,
        request_id: str,
    ) -> object:
        """Build one non-MT5 provider adapter and connect when loop-safe.

        Binance Spot, Dukascopy, and Yahoo serve public data and need no credential
        material. Credential resolution still flows through the Brokers resolver so
        the non-production environment guard is enforced uniformly.

        Args:
            settings: Effective broker provider settings.
            request_id: Canonical request identity.

        Returns:
            The result produced by the operation.

        Raises:
            DataError: If credentials are required, or construction or connection
                fails.
        """
        from app.services.brokers import create_broker_adapter

        if self._source_id not in _CREDENTIAL_FREE_PROVIDERS:
            logger.info(
                "Provider %s requires composition-root credentials", self._source_id
            )
            raise DataError(
                "CREDENTIALS_MISSING",
                safe_details={"source_id": self._source_id},
                request_id=request_id,
            )
        config = self._provider_config(settings, request_id)
        adapter: Any = _require_broker_result(
            create_broker_adapter(config.broker_id, config),
            operation="create_broker_adapter",
            request_id=request_id,
        )
        if self._source_id == _BINANCE_SPOT:
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
        """Initialize the calendar facade for one lazy read session.

        Args:
            session: Data-owned provider session used for schedule reads.
        """
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
        """Return current provider-supplied sessions as normalized UTC windows.

        Args:
            source_id: The ``source_id`` argument.
            symbol: The ``symbol`` argument.
            timezone: The ``timezone`` argument.
            observed_at: The ``observed_at`` argument.
            request_id: The ``request_id`` argument.

        Returns:
            The result produced by the operation.
        """
        adapter = self._session.adapter(request_id)

        async def read_sessions() -> StandardResponse[Any]:
            """Resolve and call the guarded operation after session connection.

            Returns:
                The result produced by the operation.
            """
            return await adapter.get_trading_sessions(
                symbol=symbol,
                start=observed_at,
                end=observed_at + timedelta(days=7),
            )

        result = self._session.run(
            read_sessions(),
            request_id,
        )
        sessions: Any = _require_broker_result(
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

    Args:
        source_id: The ``source_id`` argument.

    Returns:
        The result produced by the operation.

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
    """Return the Data-owned policy declaration for the Brokers MT5 profile.

    Returns:
        The result produced by the operation.
    """
    source_id = _MT5
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

    Args:
        source_id: The ``source_id`` argument.

    Returns:
        The result produced by the operation.
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

    Args:
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

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

    Args:
        declared: The ``declared`` argument.

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

    Args:
        source_id: The ``source_id`` argument.
        raw_root: The ``raw_root`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

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
        logger.exception("Local symbol manifest for source %s is invalid", source_id)
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
    """Register one configured local artifact source and its declared identities.

    Args:
        source_id: The ``source_id`` argument.
        request_id: The ``request_id`` argument.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
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
    _register_source_raw(
        descriptor,
        lambda: LocalMarketDataSource(
            source_id=source_id,
            raw_root=raw_root,
            metadata=metadata,
            format_preference=artifact_format,
        ),
        identities,
    )


def _list_composable_sources_raw() -> tuple[str, ...]:
    """Return every source identifier the current configuration can compose.

    Returns:
        Sorted local and provider identifiers, including already-registered ones,
        so a caller can discover valid `source_id` values without trial and error.
    """
    logger.debug("Listing composable DATA source identifiers")
    settings = get_data_settings()
    provider_settings = get_data_provider_settings()
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


def list_composable_sources() -> StandardResponse[tuple[str, ...]]:
    """Return every source identifier the current configuration can compose.

    Returns:
        Standard response carrying the sorted composable source identifiers.
    """
    return run_data_operation(
        operation="data.sources.list_composable_sources",
        request_id=None,
        start_time=data_start_time(),
        raw=_list_composable_sources_raw,
    )


def _ensure_source_raw(source_id: str, request_id: str) -> None:
    """Register one supported source and its private lazy dependencies.

    Composition dispatches on source kind. Local artifact sources need no
    credentials, network, or promotion evidence and register at `production`
    readiness; the MT5 broker profile composes a lazy read-only provider session.

    Args:
        source_id: The ``source_id`` argument.
        request_id: The ``request_id`` argument.

    Raises:
        DataError: If the source is unsupported or registration fails.
    """
    try:
        _get_source_descriptor_raw(source_id)
        return
    except DataError as error:
        if error.code != "SOURCE_UNAVAILABLE":
            raise
    settings = get_data_settings()
    provider_settings = get_data_provider_settings()
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
            _get_source_descriptor_raw(source_id)
            return
        except DataError as error:
            if error.code != "SOURCE_UNAVAILABLE":
                raise
        if is_local:
            _register_local_source(source_id, request_id)
            return
        session = _LazyBrokerSession(source_id)
        descriptor = (
            _mt5_descriptor() if source_id == _MT5 else _provider_descriptor(source_id)
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
            if source_id == _YAHOO
            else ()
        )
        _register_source_raw(descriptor, session.source, identities)
        _sessions[source_id] = session
        _calendars[source_id] = _BrokerMarketCalendar(session)


def ensure_source(source_id: str, request_id: str) -> StandardResponse[None]:
    """Register one supported source and its private lazy dependencies.

    Composition dispatches on source kind. Local artifact sources need no
    credentials, network, or promotion evidence and register at `production`
    readiness; the MT5 broker profile composes a lazy read-only provider session.

    Args:
        source_id: The ``source_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response confirming source composition.

    Raises:
        DataError: If the source is unsupported or registration fails.
    """
    return run_data_operation(
        operation="data.sources.ensure_source",
        request_id=request_id,
        start_time=data_start_time(),
        raw=lambda: _ensure_source_raw(source_id, request_id),
    )


def _ensure_source_access_raw(source_id: str, request_id: str) -> None:
    """Connect a facade-composed source before its first provider read.

    Args:
        source_id: The ``source_id`` argument.
        request_id: The ``request_id`` argument.

    Raises:
        DataError: If provider composition or connection fails.
    """
    _ensure_source_raw(source_id, request_id)
    with _lock:
        session = _sessions.get(source_id)
    if session is not None:
        session.adapter(request_id)


def ensure_source_access(source_id: str, request_id: str) -> StandardResponse[None]:
    """Connect a facade-composed source before its first provider read.

    Args:
        source_id: The ``source_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        Standard response confirming source access.

    Raises:
        DataError: If provider composition or connection fails.
    """
    return run_data_operation(
        operation="data.sources.ensure_source_access",
        request_id=request_id,
        start_time=data_start_time(),
        raw=lambda: _ensure_source_access_raw(source_id, request_id),
    )


def _close_data_provider_sessions_raw(request_id: str) -> None:
    """Close every composed provider session in reverse registration order.

    Args:
        request_id: Canonical shutdown request identity.
    """
    with _lock:
        sessions = tuple(reversed(tuple(_sessions.values())))
        _sessions.clear()
        _calendars.clear()
    for session in sessions:
        session.close(request_id)


def close_data_provider_sessions(
    request_id: str | None = None,
) -> StandardResponse[None]:
    """Disconnect and release all composed provider-session resources.

    Args:
        request_id: Optional canonical shutdown request identity.

    Returns:
        Standard response confirming provider-session shutdown.
    """
    resolved_request_id = request_id or generate_id("req")
    return run_data_operation(
        operation="data.sources.close_data_provider_sessions",
        request_id=resolved_request_id,
        start_time=data_start_time(),
        raw=lambda: _close_data_provider_sessions_raw(resolved_request_id),
    )


def _resolve_realtime_session_raw(
    source_id: str,
    request_id: str,
) -> _LazyBrokerSession:
    """Return Data's private lazy provider session for real-time reads.

    The session never crosses the Data package boundary. Real-time feature code uses
    it only to execute Brokers-owned read operations through the same credential,
    environment, circuit, and lifecycle controls as historical retrieval.

    Args:
        source_id: Configured provider source identifier.
        request_id: Canonical request identifier.

    Returns:
        Existing or newly composed private provider session.

    Raises:
        DataError: If the source cannot be composed or is not provider-backed.
    """
    _ensure_source_raw(source_id, request_id)
    with _lock:
        session = _sessions.get(source_id)
    if session is None:
        raise DataError(
            "UNSUPPORTED_SOURCE",
            safe_details={"source_id": source_id},
            request_id=request_id,
        )
    return session


def ensure_identity(source_id: str, symbol: str, request_id: str) -> None:
    """Resolve or register one provider-confirmed identity mapping.

    Args:
        source_id: The ``source_id`` argument.
        symbol: The ``symbol`` argument.
        request_id: The ``request_id`` argument.

    Raises:
        DataError: If provider metadata cannot confirm the identity.
    """
    _ensure_source_access_raw(source_id, request_id)
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
    source = _resolve_source_raw(source_id)
    metadata_response = source.get_symbol_metadata(
        SymbolMetadataRequest(
            source_id=source_id,
            symbol=symbol,
            request_id=request_id,
        )
    )
    metadata: Any = unwrap_data_response(
        metadata_response,
        operation="data.sources.ensure_identity",
        request_id=request_id,
    )
    register_source_identity(
        SourceIdentity(
            source_id=source_id,
            canonical_symbol=symbol,
            friendly_name=symbol,
            provider_symbol=metadata.provider_symbol,
            mapping_revision=_get_source_descriptor_raw(
                source_id
            ).identity_mapping_revision,
            provenance={
                "method": "provider_metadata",
                "provider_symbol": metadata.provider_symbol,
            },
            request_id=request_id,
        )
    )


def ensure_storage(request_id: str) -> None:
    """Apply Data migrations once per configured storage target.

    Args:
        request_id: The ``request_id`` argument.
    """
    settings = get_data_settings()
    target = (str(settings.data_dir), str(settings.database_url))
    with _lock:
        if target in _migrated_targets:
            return
        run_data_migrations(request_id)
        _migrated_targets.add(target)


def resolve_calendar(source_id: str, request_id: str) -> MarketCalendar:
    """Return the private authoritative calendar for one source.

    Args:
        source_id: The ``source_id`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the source has no authoritative calendar.
    """
    _ensure_source_raw(source_id, request_id)
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
    "close_data_provider_sessions",
    "ensure_identity",
    "ensure_source",
    "ensure_source_access",
    "ensure_storage",
    "list_composable_sources",
    "resolve_calendar",
]

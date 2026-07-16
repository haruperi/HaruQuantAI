"""Run practical DATA-domain recipes, including opt-in real provider reads.

Set ``DATA_USAGE_LIVE_PROVIDERS`` to a comma-separated list containing any of
``mt5``, ``ctrader``, ``dukascopy``, ``yahoo``, or ``binance`` (or ``all``) to
execute genuine network examples. Provider credentials come from typed settings;
only the shared Utils settings boundary reads the repository ``.env`` file.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import NoDecode

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services import data
from app.services.brokers import (
    BrokerAdapter,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
)
from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    clear_data_cache,
    create_data_update_job,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    get_data_update_job_status,
    get_market_data,
    get_tick_data,
    get_trading_sessions,
    list_symbols,
    load_local_dataset,
    resample_ohlcv,
    run_data_update_job_once,
    save_market_data,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.config import DataSettings, data_settings_context
from app.services.data.contracts import (
    CacheClearRequest,
    DataError,
    DataQualityReport,
    DatasetLoadRequest,
    DatasetSaveRequest,
    JobDefinition,
    JobStatusRequest,
    MarketDataRequest,
    MarketDataset,
    MarketSchedule,
    OHLCVRecord,
    ScheduleRequest,
    SessionWindow,
    SourceDescriptor,
    SourceIdentity,
    SourceLicensePolicy,
    SpreadRecord,
    SymbolListRequest,
    SymbolMetadata,
    SyntheticRequest,
    TickRecord,
)
from app.services.data.sources import register_source
from app.services.data.sources.external import ExternalMarketDataSource
from app.services.data.sources.local import LocalMarketDataSource
from app.services.data.sources.policy import SourcePolicyConfig, register_source_policy
from app.services.data.storage.migrations import run_data_migrations
from app.utils import (
    AppSettings,
    generate_id,
    logger,
    utc_now,
)

if TYPE_CHECKING:
    from typing import Literal

_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_END = _START + timedelta(minutes=4)
_REGISTERED_LOCAL_SOURCES: set[str] = set()
_REGISTERED_EXTERNAL_SOURCES: set[str] = set()


class _UsageSettings(AppSettings):
    """Typed opt-in and credential settings for real provider recipes."""

    data_usage_live_providers: Annotated[tuple[str, ...], NoDecode] = ()
    mt5_enabled: bool = False
    mt5_login: SecretStr | None = None
    mt5_password: SecretStr | None = None
    mt5_server: SecretStr | None = None
    mt5_terminal_path: SecretStr | None = None
    ctrader_enabled: bool = False
    ctrader_client_id: SecretStr | None = None
    ctrader_client_secret: SecretStr | None = None
    ctrader_access_token: SecretStr | None = None
    ctrader_account_id: SecretStr | None = None

    @field_validator("data_usage_live_providers", mode="before")
    @classmethod
    def _parse_live_providers(cls, value: object) -> object:
        """Parse the explicit comma-separated real-provider allowlist."""
        logger.debug("Parsing DATA usage live-provider settings")
        if not isinstance(value, str):
            return value
        return tuple(
            item.strip().casefold() for item in value.split(",") if item.strip()
        )


@dataclass
class _UsageState:
    """Mutable process-local resources owned by the standalone cookbook."""

    temporary_directory: TemporaryDirectory[str] | None = None
    demo_root: Path | None = None
    created_job: bool = False
    settings_context: AbstractContextManager[None] | None = None


_STATE = _UsageState()


def _live_enabled(provider: str) -> bool:
    """Return whether one real provider was explicitly enabled."""
    logger.info("Checking explicit live-read opt-in for %s", provider)
    configured = set(_UsageSettings().data_usage_live_providers)
    return "all" in configured or provider.casefold() in configured


def _demo_root() -> Path:
    """Create and migrate one isolated temporary DATA profile lazily."""
    logger.info("Resolving isolated storage for DATA usage recipes")
    if _STATE.demo_root is not None:
        return _STATE.demo_root
    _STATE.temporary_directory = TemporaryDirectory(prefix="haru-data-usecases-")
    _STATE.demo_root = Path(_STATE.temporary_directory.name)
    settings = DataSettings(
        database_url="sqlite:///usecases.sqlite3",
        data_dir=_STATE.demo_root,
        sqlite_busy_timeout_seconds=1.5,
        write_lock_lease_seconds=30,
    )
    _STATE.settings_context = data_settings_context(settings)
    _STATE.settings_context.__enter__()
    for relative in ("data/raw", "data/processed", "data/cache", "artifacts/data"):
        (_STATE.demo_root / relative).mkdir(parents=True, exist_ok=True)
    run_data_migrations(generate_id("req"))
    return _STATE.demo_root


def _cleanup_demo_environment() -> None:
    """Release only the isolated temporary files created by this cookbook."""
    logger.info("Cleaning the isolated DATA usage-example directory")
    if _STATE.temporary_directory is not None:
        _STATE.temporary_directory.cleanup()
    if _STATE.settings_context is not None:
        _STATE.settings_context.__exit__(None, None, None)
    _STATE.temporary_directory = None
    _STATE.demo_root = None
    _STATE.settings_context = None


def _quality(count: int, generated_at: datetime) -> DataQualityReport:
    """Build clean, bounded quality evidence for local recipes."""
    logger.info("Building quality evidence for %d recipe records", count)
    return DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        issues=(),
        warnings=(),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=100,
        schema_version="v1",
        generated_at=generated_at,
    )


def _bar_dataset(
    *,
    source_id: str,
    symbol: str,
    timeframe: str = "M1",
    count: int = 5,
    start: datetime = _START,
) -> MarketDataset:
    """Build a realistic normalized bar dataset for offline recipes."""
    logger.info("Building %d %s bars for %s", count, timeframe, symbol)
    step = timedelta(hours=1) if timeframe == "H1" else timedelta(minutes=1)
    records = tuple(
        OHLCVRecord(
            timestamp=start + (step * index),
            open=Decimal(100) + index,
            high=Decimal(101) + index,
            low=Decimal(99) + index,
            close=Decimal("100.5") + index,
            volume=Decimal(1000) + (index * 100),
            price_unit="USD",
            volume_unit="units",
            source=source_id,
            source_symbol=symbol,
            source_revision="usage-v1",
            available_at=start + (step * index) + timedelta(seconds=1),
        )
        for index in range(count)
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol=symbol,
        timeframe=timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=_quality(len(records), records[-1].available_at),
        source_metadata={"source_id": source_id, "revision": "usage-v1"},
        license_metadata={"status": "approved"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def _tick_dataset() -> MarketDataset:
    """Build sorted canonical ticks for aggregation recipes."""
    logger.info("Building sorted canonical ticks")
    records = tuple(
        TickRecord(
            timestamp=_START + timedelta(seconds=index * 10),
            bid=Decimal(100) + index,
            ask=Decimal("100.2") + index,
            last=Decimal("100.1") + index,
            volume=Decimal("0.5"),
            price_unit="USDT",
            volume_unit="BTC",
            source="usage-ticks",
            source_symbol="BTCUSDT",
            source_revision="usage-v1",
            available_at=_START + timedelta(seconds=index * 10, milliseconds=25),
        )
        for index in range(6)
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="BTCUSDT",
        timeframe=None,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=_quality(len(records), records[-1].available_at),
        source_metadata={"source_id": "usage-ticks", "revision": "usage-v1"},
        license_metadata={"status": "approved"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def _register_local_artifact_source(
    *,
    source_id: str,
    symbol: str,
    data_format: Literal["csv", "parquet"],
) -> None:
    """Persist a governed artifact and register its explicit local source."""
    logger.info("Registering %s local artifact source %s", data_format, source_id)
    if source_id in _REGISTERED_LOCAL_SOURCES:
        return
    root = _demo_root()
    dataset = _bar_dataset(source_id=source_id, symbol=symbol)
    relative_path = Path(f"data/raw/{symbol}.{data_format}")
    save_market_data(
        DatasetSaveRequest(
            dataset=dataset,
            relative_path=relative_path,
            format=data_format,
            overwrite=True,
            request_id=dataset.request_id,
        )
    )
    metadata = SymbolMetadata(
        canonical_symbol=symbol,
        provider_symbol=symbol,
        asset_class="equity",
        base_currency="USD",
        digits=2,
        price_step=Decimal("0.01"),
        quantity_step=Decimal(1),
        timezone="America/New_York",
        source_id=source_id,
        revision="usage-v1",
        retrieved_at=dataset.available_at,
        missing_fields=("quote_currency",),
        request_id=generate_id("req"),
    )
    descriptor = SourceDescriptor(
        source_id=source_id,
        readiness="production",
        capabilities=("bars", "symbol_discovery", "symbol_metadata"),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="America/New_York",
        revision="usage-v1",
        license_policy=SourceLicensePolicy(
            source_id=source_id,
            status="approved",
            permitted_workflows=("research", "backtest", "validation"),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("manifest-verified",),
    )
    identity = SourceIdentity(
        source_id=source_id,
        canonical_symbol=symbol,
        friendly_name=f"Local {symbol}",
        provider_symbol=symbol,
        mapping_revision="mapping-v1",
        provenance={"artifact": str(relative_path)},
        request_id=generate_id("req"),
    )
    register_source(
        descriptor,
        lambda: LocalMarketDataSource(
            source_id=source_id,
            raw_root=(root / "data" / "raw").resolve(),
            metadata={symbol: metadata},
            format_preference=data_format,
        ),
        identities=(identity,),
    )
    register_source_policy(
        SourcePolicyConfig(
            source_id=source_id,
            rate_limit=1000,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=30,
        )
    )
    _REGISTERED_LOCAL_SOURCES.add(source_id)


def _historical_request(
    source_id: str,
    symbol: str,
    *,
    data_kind: Literal["bars", "ticks"] = "bars",
    timeframe: str | None = "M1",
    use_cache: bool = False,
    start: datetime = _START,
    end: datetime = _END,
) -> MarketDataRequest:
    """Build one bounded historical request shared by recipes."""
    logger.info("Building historical request for %s through %s", symbol, source_id)
    return MarketDataRequest(
        source_id=source_id,
        symbol=symbol,
        data_kind=data_kind,
        timeframe=timeframe,
        start=start,
        end=end,
        limit=100,
        use_cache=use_cache,
        cache_ttl_seconds=3600 if use_cache else None,
        quality_failure_behavior="fail",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def _provider_config(provider: str, settings: _UsageSettings) -> BrokerConnectionConfig:
    """Build an explicitly enabled caller-owned broker/provider configuration."""
    logger.info("Building caller-owned configuration for %s", provider)
    common: dict[str, object] = {
        "provider_enabled": True,
        "connect_timeout_sec": 20,
        "request_timeout_sec": 20,
        "transport_reconnect_max_attempts": 0,
        "stream_buffer_size": 8,
        "circuit_failure_threshold": 3,
        "circuit_recovery_timeout_sec": 5,
        "circuit_half_open_max_calls": 1,
    }
    if provider == "mt5":
        if (
            settings.mt5_login is None
            or settings.mt5_password is None
            or settings.mt5_server is None
        ):
            raise ValueError("MT5 credentials are incomplete")
        credentials = {
            "login": settings.mt5_login,
            "password": settings.mt5_password,
            "server": settings.mt5_server,
        }
        if settings.mt5_terminal_path is not None:
            credentials["terminal_path"] = settings.mt5_terminal_path
        return BrokerConnectionConfig(
            broker_id=BrokerId.MT5,
            environment=BrokerEnvironment.DEMO,
            account_reference=settings.mt5_login.get_secret_value(),
            credentials=credentials,
            **common,  # type: ignore[arg-type]
        )
    if provider == "ctrader":
        if (
            settings.ctrader_client_id is None
            or settings.ctrader_client_secret is None
            or settings.ctrader_access_token is None
            or settings.ctrader_account_id is None
        ):
            raise ValueError("cTrader credentials are incomplete")
        credentials = {
            "client_id": settings.ctrader_client_id,
            "client_secret": settings.ctrader_client_secret,
            "access_token": settings.ctrader_access_token,
            "account_id": settings.ctrader_account_id,
        }
        return BrokerConnectionConfig(
            broker_id=BrokerId.CTRADER,
            environment=BrokerEnvironment.DEMO,
            account_reference=settings.ctrader_account_id.get_secret_value(),
            credentials=credentials,
            **common,  # type: ignore[arg-type]
        )
    identities = {
        "dukascopy": (BrokerId.DUKASCOPY, BrokerEnvironment.SANDBOX),
        "yahoo": (BrokerId.YAHOO, BrokerEnvironment.SANDBOX),
        "binance": (BrokerId.BINANCE_SPOT, BrokerEnvironment.TESTNET),
    }
    broker_id, environment = identities[provider]
    return BrokerConnectionConfig(
        broker_id=broker_id,
        environment=environment,
        probe_symbol="AAPL" if provider == "yahoo" else None,
        **common,  # type: ignore[arg-type]
    )


def _credentials_available(provider: str, settings: _UsageSettings) -> bool:
    """Check only presence and enablement, never log credential values."""
    logger.info("Checking configured credential references for %s", provider)
    if provider == "mt5":
        return settings.mt5_enabled and all(
            value is not None
            for value in (
                settings.mt5_login,
                settings.mt5_password,
                settings.mt5_server,
            )
        )
    if provider == "ctrader":
        return settings.ctrader_enabled and all(
            value is not None
            for value in (
                settings.ctrader_account_id,
                settings.ctrader_client_id,
                settings.ctrader_client_secret,
                settings.ctrader_access_token,
            )
        )
    return True


def _register_external_source(
    *,
    provider: str,
    adapter: BrokerAdapter,
    symbol: str,
    data_kind: Literal["bars", "ticks"],
) -> str:
    """Register a caller-owned connected adapter behind DATA read policy."""
    logger.info("Registering connected %s adapter as a DATA read source", provider)
    source_id = f"usage-{provider}"
    if source_id in _REGISTERED_EXTERNAL_SOURCES:
        return source_id
    descriptor = SourceDescriptor(
        source_id=source_id,
        readiness="staging",
        capabilities=(data_kind,),
        requires_credentials=provider in {"mt5", "ctrader"},
        requires_network=True,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="broker-adapter-v1",
        license_policy=SourceLicensePolicy(
            source_id=source_id,
            status="approved",
            permitted_workflows=("research",),
            export_allowed=False,
            attribution_required=True,
            attribution_text=f"Historical data supplied by {provider}",
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("manual-real-read",),
    )
    identity = SourceIdentity(
        source_id=source_id,
        canonical_symbol=symbol,
        friendly_name=f"{provider} {symbol}",
        provider_symbol=symbol,
        mapping_revision="mapping-v1",
        provenance={"provider": provider},
        request_id=generate_id("req"),
    )
    register_source(
        descriptor,
        lambda: ExternalMarketDataSource(source_id, adapter),
        identities=(identity,),
    )
    register_source_policy(
        SourcePolicyConfig(
            source_id=source_id,
            rate_limit=30,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=30,
        )
    )
    _REGISTERED_EXTERNAL_SOURCES.add(source_id)
    return source_id


def _run_real_provider_read(
    provider: str,
    *,
    symbol: str,
    data_kind: Literal["bars", "ticks"],
    timeframe: str | None,
    start: datetime,
    end: datetime,
) -> MarketDataset | None:
    """Connect a real provider and route one historical read through DATA."""
    logger.info("Preparing genuine %s historical retrieval", provider)
    if not _live_enabled(provider):
        logger.info(
            "Skipping %s: add it to DATA_USAGE_LIVE_PROVIDERS to run the real read",
            provider,
        )
        return None
    settings = _UsageSettings()
    if not _credentials_available(provider, settings):
        logger.warning("Skipping %s: enabled credentials are incomplete", provider)
        return None
    config = _provider_config(provider, settings)
    created = create_broker_adapter(config.broker_id, config)
    adapter = created.data
    if adapter is None:
        logger.error(
            "Provider adapter creation failed for %s: %s", provider, created.error
        )
        return None
    connected = asyncio.run(adapter.connect())
    if not connected.is_success:
        logger.error("Real %s connection failed: %s", provider, connected.error)
        return None
    try:
        source_id = _register_external_source(
            provider=provider,
            adapter=adapter,
            symbol=symbol,
            data_kind=data_kind,
        )
        request = _historical_request(
            source_id,
            symbol,
            data_kind=data_kind,
            timeframe=timeframe,
            start=start,
            end=end,
        )
        dataset = (
            get_tick_data(request) if data_kind == "ticks" else get_market_data(request)
        )
        logger.info(
            "Real %s retrieval returned %d normalized records",
            provider,
            dataset.record_count,
        )
        return dataset
    except DataError as error:
        logger.error("Real %s DATA read failed with code=%s", provider, error.code)
        return None
    finally:
        asyncio.run(adapter.disconnect())


def _print_dataset(dataset: MarketDataset | None) -> None:
    """Print a summary and all records of a MarketDataset to the console.

    Args:
        dataset: The dataset to display, or None if no dataset was retrieved.
    """
    if dataset is None:
        print("No dataset retrieved (provider not enabled or credentials missing).")
        return

    print(
        f"Dataset: symbol={dataset.symbol}, "
        f"timeframe={dataset.timeframe or 'N/A'}, "
        f"data_kind={dataset.data_kind}, "
        f"record_count={dataset.record_count}"
    )

    for index, record in enumerate(dataset.records):
        if isinstance(record, TickRecord):
            print(
                f"  [{index:02d}] {record.timestamp.isoformat()} | "
                f"Bid: {record.bid} | Ask: {record.ask} | "
                f"Last: {record.last} | V: {record.volume}"
            )
        elif isinstance(record, OHLCVRecord):
            print(
                f"  [{index:02d}] {record.timestamp.isoformat()} | "
                f"O: {record.open} | H: {record.high} | "
                f"L: {record.low} | C: {record.close} | V: {record.volume}"
            )
        elif isinstance(record, SpreadRecord):
            print(
                f"  [{index:02d}] {record.timestamp.isoformat()} | "
                f"Spread: {record.spread} {record.unit} (scale: {record.scale})"
            )
        else:
            print(f"  [{index:02d}] Unknown record type: {record}")


def _header(title: str) -> None:
    """Print the header for an example section."""
    print(f"\n{'=' * 100}")
    print(f"--- {title} ---")
    print(f"{'=' * 100}")


def example_01_metadata_and_discovery() -> None:
    """Discover symbols and inspect explicit local metadata."""
    _header("Example 01: metadata and discovery")
    _register_local_artifact_source(
        source_id="usage-local-csv",
        symbol="LOCALCSV",
        data_format="csv",
    )
    page = list_symbols(
        SymbolListRequest(
            source_id="usage-local-csv",
            limit=10,
            request_id=generate_id("req"),
        )
    )
    logger.info("Discovered local symbols=%s", page.items)


def example_02_mt5() -> None:
    """Retrieve genuine recent MT5 demo bars when explicitly configured."""
    _header("Example 02: MT5 historical retrieval")
    now = utc_now()
    dataset = _run_real_provider_read(
        "mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=now - timedelta(hours=2),
        end=now,
    )
    _print_dataset(dataset)


def example_03_ctrader() -> None:
    """Retrieve genuine recent cTrader demo bars when explicitly configured."""
    _header("Example 03: cTrader historical retrieval")
    now = utc_now()
    dataset = _run_real_provider_read(
        "ctrader",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=now - timedelta(hours=2),
        end=now,
    )
    _print_dataset(dataset)


def example_04_dukascopy() -> None:
    """Retrieve genuine recent Dukascopy ticks when explicitly enabled."""
    _header("Example 04: Dukascopy historical retrieval")
    now = utc_now()
    dataset = _run_real_provider_read(
        "dukascopy",
        symbol="EURUSD",
        data_kind="ticks",
        timeframe=None,
        start=now - timedelta(hours=3),
        end=now - timedelta(hours=2),
    )
    _print_dataset(dataset)


def example_05_yahoo() -> None:
    """Retrieve genuine Yahoo Finance daily bars when explicitly enabled."""
    _header("Example 05: Yahoo Finance historical retrieval")
    now = utc_now()
    dataset = _run_real_provider_read(
        "yahoo",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1d",
        start=now - timedelta(days=10),
        end=now,
    )
    _print_dataset(dataset)


def example_06_binance() -> None:
    """Retrieve genuine Binance testnet bars when explicitly enabled."""
    _header("Example 06: Binance historical retrieval")
    now = utc_now()
    dataset = _run_real_provider_read(
        "binance",
        symbol="BTCUSDT",
        data_kind="bars",
        timeframe="1h",
        start=now - timedelta(hours=5),
        end=now,
    )
    _print_dataset(dataset)


def example_07_csv() -> MarketDataset:
    """Save and retrieve normalized historical data through a CSV source."""
    _header("Example 07: CSV historical retrieval")
    _register_local_artifact_source(
        source_id="usage-local-csv",
        symbol="LOCALCSV",
        data_format="csv",
    )
    loaded = load_local_dataset(
        DatasetLoadRequest(
            relative_path=Path("data/raw/LOCALCSV.csv"),
            format="csv",
            request_id=generate_id("req"),
        )
    )
    dataset = get_market_data(
        _historical_request("usage-local-csv", "LOCALCSV", use_cache=False)
    )
    if loaded.record_count != dataset.record_count:
        raise AssertionError("CSV storage and source retrieval disagree")
    logger.info("CSV retrieval returned %d records", dataset.record_count)
    _print_dataset(dataset)
    return dataset


def example_08_parquet() -> MarketDataset:
    """Save and retrieve normalized historical data through a Parquet source."""
    _header("Example 08: Parquet historical retrieval")
    _register_local_artifact_source(
        source_id="usage-local-parquet",
        symbol="LOCALPARQUET",
        data_format="parquet",
    )
    loaded = load_local_dataset(
        DatasetLoadRequest(
            relative_path=Path("data/raw/LOCALPARQUET.parquet"),
            format="parquet",
            request_id=generate_id("req"),
        )
    )
    dataset = get_market_data(
        _historical_request("usage-local-parquet", "LOCALPARQUET", use_cache=False)
    )
    if loaded.record_count != dataset.record_count:
        raise AssertionError("Parquet storage and source retrieval disagree")
    logger.info("Parquet retrieval returned %d records", dataset.record_count)
    _print_dataset(dataset)
    return dataset


def example_09_caching() -> None:
    """Use the versioned query cache and prove the second request is a hit."""
    _header("Example 09: historical query caching")
    _register_local_artifact_source(
        source_id="usage-local-csv",
        symbol="LOCALCSV",
        data_format="csv",
    )
    request = _historical_request("usage-local-csv", "LOCALCSV", use_cache=True)
    first = get_market_data(request)
    second = get_market_data(
        request.model_copy(update={"request_id": generate_id("req")})
    )
    if first.cache_status != "miss" or second.cache_status != "hit":
        raise AssertionError("historical cache did not report miss then hit")
    logger.info("Cache sequence=%s -> %s", first.cache_status, second.cache_status)


class TimezoneAwareCalendar:
    """Return current exchange sessions using the requested IANA timezone label."""

    def get_schedule(
        self,
        *,
        source_id: str,
        symbol: str,
        timezone: str,
        observed_at: datetime,
        request_id: str,
    ) -> MarketSchedule:
        """Build an authoritative current schedule from injected observation time."""
        logger.info("Building current %s session in timezone %s", symbol, timezone)
        window = SessionWindow(
            label="regular",
            opens_at=observed_at - timedelta(hours=1),
            closes_at=observed_at + timedelta(hours=5, minutes=30),
        )
        return MarketSchedule(
            source_id=source_id,
            symbol=symbol,
            timezone=timezone,
            hours=(window,),
            sessions=(window,),
            observed_at=observed_at,
            request_id=request_id,
        )


def example_10_timezone_sessions() -> None:
    """Check current sessions using an explicit timezone-aware calendar boundary."""
    _header("Example 10: timezone-aware session checks")
    _register_local_artifact_source(
        source_id="usage-local-csv",
        symbol="LOCALCSV",
        data_format="csv",
    )
    schedule = get_trading_sessions(
        ScheduleRequest(
            source_id="usage-local-csv",
            symbol="LOCALCSV",
            view="sessions",
            timezone="America/New_York",
            request_id=generate_id("req"),
        ),
        TimezoneAwareCalendar(),
    )
    if any(window.opens_at.tzinfo is None for window in schedule.sessions):
        raise AssertionError("session contains a naive timestamp")
    logger.info(
        "Session timezone=%s opens_utc=%s closes_utc=%s",
        schedule.timezone,
        schedule.sessions[0].opens_at,
        schedule.sessions[0].closes_at,
    )


def example_11_resample_ohlcv() -> MarketDataset:
    """Resample four canonical H1 observations into one H4 bar."""
    _header("Example 11: general OHLCV resampling")
    result = resample_ohlcv(
        _bar_dataset(
            source_id="usage-resample",
            symbol="EURUSD",
            timeframe="H1",
            count=4,
        ),
        "H4",
    )
    logger.info("Resampled H1 records=%d into H4 records=%d", 4, result.record_count)
    _print_dataset(result)
    return result


def example_12_m1_to_m5() -> MarketDataset:
    """Resample exactly five M1 observations into one M5 bar."""
    _header("Example 12: M1-to-M5 resampling")
    result = resample_ohlcv(
        _bar_dataset(source_id="usage-resample", symbol="BTCUSDT"),
        "M5",
    )
    if result.timeframe != "M5" or result.record_count != 1:
        raise AssertionError("M1-to-M5 resampling produced an unexpected result")
    logger.info(
        "M5 close=%s volume=%s", result.records[0].close, result.records[0].volume
    )  # type: ignore[union-attr]
    _print_dataset(result)
    return result


def example_13_ticks_to_bars() -> MarketDataset:
    """Aggregate sorted ticks into one canonical minute bar."""
    _header("Example 13: tick-to-bar aggregation")
    result = aggregate_ticks_to_bars(_tick_dataset(), "M1", "last")
    logger.info("Aggregated ticks into %d M1 bars", result.record_count)
    _print_dataset(result)
    return result


def example_14_bar_to_tick_boundary() -> MarketDataset:
    """Show that DATA generates explicit synthetic ticks, never reconstructed ticks."""
    _header("Example 14: bar-to-tick ownership boundary")
    prohibited_names = {
        "bars_to_ticks",
        "generate_ticks_from_bars",
        "reconstruct_ticks",
    }
    if prohibited_names.intersection(data.__all__):
        raise AssertionError(
            "DATA unexpectedly exposes Simulation-owned reconstruction"
        )
    ticks = generate_synthetic_ticks(
        SyntheticRequest(
            symbol="SYNTHETIC_EURUSD",
            data_kind="ticks",
            timeframe=None,
            start=_START,
            record_count=20,
            method="gbm",
            seed=123,
            parameters={
                "mu": Decimal("0.01"),
                "sigma": Decimal("0.05"),
                "start_val": Decimal("1.10"),
            },
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
    )
    logger.info(
        "Generated %d explicitly synthetic ticks; none were reconstructed from bars",
        ticks.record_count,
    )
    _print_dataset(ticks)
    return ticks


def example_15_multitimeframe_alignment() -> None:
    """Align M1 and M5 datasets only after evidence becomes available."""
    _header("Example 15: no-lookahead multi-timeframe alignment")
    m1 = _bar_dataset(
        source_id="usage-alignment",
        symbol="BTCUSDT",
        count=10,
    )
    m5 = resample_ohlcv(m1, "M5")
    targets = (
        _START + timedelta(minutes=4, seconds=1),
        _START + timedelta(minutes=9, seconds=1),
    )
    aligned = align_multitimeframe_data({"M1": m1, "M5": m5}, targets)
    for name, dataset in aligned.items():
        for record, target in zip(dataset.records, targets, strict=True):
            if record.available_at > target:
                raise AssertionError(f"{name} alignment exposed future evidence")
    logger.info("Aligned timeframes=%s targets=%d", tuple(aligned), len(targets))


def example_16_merge_symbols() -> None:
    """Merge symbols as an identity-preserving keyed aligned mapping."""
    _header("Example 16: concatenate and merge symbols without losing identity")
    apple = _bar_dataset(source_id="usage-symbols", symbol="AAPL")
    microsoft = _bar_dataset(source_id="usage-symbols", symbol="MSFT")
    targets = tuple(_START + timedelta(minutes=index, seconds=1) for index in range(5))
    merged = align_multitimeframe_data(
        {"AAPL": apple, "MSFT": microsoft},
        targets,
    )
    if merged["AAPL"].symbol == merged["MSFT"].symbol:
        raise AssertionError("symbol identities were collapsed")
    logger.info(
        "Merged symbol keys=%s with %d aligned rows each", tuple(merged), len(targets)
    )


def example_17_synthetic_walk_bars() -> MarketDataset:
    """Generate a deterministic explicitly synthetic H1 random-walk dataset."""
    _header("Example 17: synthetic H1 walk bars")
    result = generate_synthetic_bars(
        SyntheticRequest(
            symbol="SYNTHETIC_SP500",
            data_kind="bars",
            timeframe="H1",
            start=_START,
            record_count=48,
            method="gbm",
            seed=2026,
            parameters={
                "mu": Decimal("0.04"),
                "sigma": Decimal("0.15"),
                "start_val": Decimal(6000),
            },
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
    )
    logger.info("Generated %d reproducible H1 bars with seed=2026", result.record_count)
    _print_dataset(result)
    return result


def _ensure_job_created() -> None:
    """Create the cookbook's recurrent job exactly once."""
    logger.info("Ensuring the recurrent usage job exists")
    if _STATE.created_job:
        return
    _register_local_artifact_source(
        source_id="usage-local-csv",
        symbol="LOCALCSV",
        data_format="csv",
    )
    status = create_data_update_job(
        JobDefinition(
            job_id="usage-localcsv-update",
            source_id="usage-local-csv",
            symbols=("LOCALCSV",),
            timeframes=("M1",),
            data_kinds=("ohlcv",),
            start=_START,
            end=_END,
            interval_seconds=300,
            enabled=False,
            created_at=_START,
            request_id=generate_id("req"),
        ),
        generate_id("req"),
    )
    _STATE.created_job = True
    logger.info("Created recurrent job=%s", status.job_id)


def example_18_create_recurrent_job() -> None:
    """Create a bounded recurrent historical-update job definition."""
    _header("Example 18: recurrent update-job configuration")
    _ensure_job_created()


def example_19_job_status() -> None:
    """Query persisted recurrent-job status without mutation."""
    _header("Example 19: update-job status query")
    _ensure_job_created()
    status = get_data_update_job_status(
        JobStatusRequest(
            job_id="usage-localcsv-update",
            request_id=generate_id("req"),
        )
    )
    logger.info(
        "Job state=%s enabled=%s next_run=%s",
        status.state,
        status.enabled,
        status.next_run_at,
    )


def example_20_start_stop_worker() -> None:
    """Start and stop a real in-process recurrent task, then run once manually."""
    _header("Example 20: recurrent worker start, stop, and run-once lifecycle")
    _ensure_job_created()

    async def exercise_worker() -> None:
        """Keep the event loop running while the recurrent task is registered."""
        logger.info("Starting the recurrent worker task")
        started = start_data_update_job("usage-localcsv-update", generate_id("req"))
        if not started.enabled:
            raise AssertionError("recurrent worker did not become enabled")
        await asyncio.sleep(0)
        result = run_data_update_job_once("usage-localcsv-update", generate_id("req"))
        if result.state != "succeeded":
            raise AssertionError(f"run-once failed: {result.error_code}")
        logger.info(
            "Run-once committed chunks=%d records=%d",
            result.committed_chunks,
            result.record_count,
        )
        stopped = stop_data_update_job("usage-localcsv-update", generate_id("req"))
        if stopped.enabled:
            raise AssertionError("recurrent worker did not stop")
        await asyncio.sleep(0)

    asyncio.run(exercise_worker())


def example_21_clear_cache_and_tidy() -> None:
    """Preview and clear matching cache rows through the public DATA boundary."""
    _header("Example 21: bounded cache clearing and isolated persistence tidy-up")
    _register_local_artifact_source(
        source_id="usage-local-csv",
        symbol="LOCALCSV",
        data_format="csv",
    )
    get_market_data(_historical_request("usage-local-csv", "LOCALCSV", use_cache=True))
    selector = {
        "namespace": "data",
        "source_id": "usage-local-csv",
        "symbol": "LOCALCSV",
        "data_kind": "bars",
        "max_entries": 100,
    }
    preview = clear_data_cache(
        CacheClearRequest(
            **selector,
            dry_run=True,
            request_id=generate_id("req"),
        )
    )
    cleared = clear_data_cache(
        CacheClearRequest(
            **selector,
            dry_run=False,
            request_id=generate_id("req"),
        )
    )
    if preview.matched_count != cleared.deleted_count:
        raise AssertionError("cache preview and deletion counts disagree")
    logger.info("Cleared %d matching cache rows", cleared.deleted_count)


def example_22_public_boundary_classification() -> None:
    """Classify broker reads versus mutations and verify DATA exposes reads only."""
    _header("Example 22: public-boundary and read-only broker contracts")
    read_capability = BrokerCapability(
        capability=BrokerCapabilityId.GET_HISTORICAL_BARS,
        implementation_status="IMPLEMENTED",
        availability="AVAILABLE",
        access_mode="READ",
        requirement="AUTHENTICATION",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
    )
    mutation_capability = BrokerCapability(
        capability=BrokerCapabilityId.PLACE_ORDER,
        implementation_status="IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode="WRITE",
        requirement="PERMISSION",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
        reason="DATA owns no broker mutation capability",
    )
    if read_capability.access_mode != "READ":
        raise AssertionError("historical bars are not classified as read-only")
    if mutation_capability.access_mode != "WRITE":
        raise AssertionError("place-order is not classified as a mutation")
    if "place_order" in data.__all__ or "cancel_order" in data.__all__:
        raise AssertionError("DATA exposes a prohibited broker mutation")
    logger.info(
        "Classified %s=%s and %s=%s; DATA mutation exports remain absent",
        read_capability.capability,
        read_capability.access_mode,
        mutation_capability.capability,
        mutation_capability.access_mode,
    )


def example_23_quality_and_lineage() -> None:
    """Summarize quality flags and record-level/provider-level lineage metadata."""
    _header("Example 23: data-quality summaries and lineage metadata")
    dataset = example_08_parquet()
    issue_summary = {
        issue.code: issue.affected_count for issue in dataset.quality_report.issues
    }
    record_sources = tuple(sorted({record.source for record in dataset.records}))
    logger.info(
        "Quality status=%s score=%s issues=%s",
        dataset.quality_report.quality_status,
        dataset.quality_report.quality_score,
        issue_summary,
    )
    logger.info(
        "Dataset lineage=%s record_sources=%s",
        dict(dataset.source_metadata),
        record_sources,
    )


def _run_example(label: str, example: Callable[[], object]) -> None:
    """Run one recipe and visibly confirm that it returned without an exception."""
    logger.info("RUNNING: %s", label)
    result = example()
    logger.info(
        "COMPLETED: %s (result=%s)",
        label,
        type(result).__name__,
    )


def main() -> None:
    """Run every recipe using the shared logger's approved default profile."""
    recipes: tuple[tuple[str, Callable[[], object]], ...] = (
        ("01 metadata and discovery", example_01_metadata_and_discovery),
        ("02 MT5 historical retrieval", example_02_mt5),
        ("03 cTrader historical retrieval", example_03_ctrader),
        ("04 Dukascopy historical retrieval", example_04_dukascopy),
        ("05 Yahoo Finance historical retrieval", example_05_yahoo),
        ("06 Binance historical retrieval", example_06_binance),
        ("07 CSV historical retrieval", example_07_csv),
        ("08 Parquet historical retrieval", example_08_parquet),
        ("09 historical query caching", example_09_caching),
        ("10 timezone-aware sessions", example_10_timezone_sessions),
        ("11 OHLCV resampling", example_11_resample_ohlcv),
        ("12 M1-to-M5 resampling", example_12_m1_to_m5),
        ("13 tick-to-bar aggregation", example_13_ticks_to_bars),
        ("14 bar-to-tick ownership boundary", example_14_bar_to_tick_boundary),
        ("15 no-lookahead alignment", example_15_multitimeframe_alignment),
        ("16 identity-preserving symbol merge", example_16_merge_symbols),
        ("17 synthetic H1 walk bars", example_17_synthetic_walk_bars),
        ("18 recurrent job configuration", example_18_create_recurrent_job),
        ("19 job status", example_19_job_status),
        ("20 recurrent worker lifecycle", example_20_start_stop_worker),
        ("21 cache clear and SQLite tidy-up", example_21_clear_cache_and_tidy),
        (
            "22 public-boundary classification",
            example_22_public_boundary_classification,
        ),
        ("23 quality and lineage", example_23_quality_and_lineage),
    )
    completed = 0
    try:
        for label, example in recipes:
            _run_example(label, example)
            completed += 1
        logger.info(
            "FINISHED: %d DATA usage recipes completed; provider outcomes were "
            "reported individually",
            completed,
        )
    finally:
        _cleanup_demo_environment()


if __name__ == "__main__":
    main()

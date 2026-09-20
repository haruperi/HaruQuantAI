"""Public semantic contracts, DTOs, protocols, and errors for the Data domain.

Domain:
    D-DATA (Data)

Authoritative Documentation:
    app/services/data/README.md

Invariants:
    * All DTOs are slotted immutable value records or dataclasses.
    * No service implementations are imported into this module.
    * Dates and timestamps are timezone-aware UTC instants unless explicitly typed.
    * All numeric properties carry explicit financial and market precision semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from app.kernel.capability import Capability

# ---------------------------------------------------------------------------
# Domain Error Hierarchy
# ---------------------------------------------------------------------------


class DataError(Exception):
    """Base exception for all Data domain errors."""


class InstrumentNotFoundError(DataError):
    """Raised when an instrument symbol cannot be found in the catalog."""


class InvalidInstrumentError(DataError):
    """Raised when instrument properties fail mathematical or financial constraints."""


class SessionNotFoundError(DataError):
    """Raised when a requested trading session profile does not exist."""


class InvalidSessionWindowError(DataError):
    """Raised when session window start/end times are malformed or invalid."""


class TimezoneError(DataError):
    """Raised when timezone resolution or DST calculation fails."""


class ImportParseError(DataError):
    """Raised when tabular data parsing encounters unrecoverable syntax errors."""


class ExportWriteError(DataError):
    """Raised when dataset export fails to write to the designated output format."""


class UnsupportedExportFormatError(DataError):
    """Raised when an export format is unrecognized or not supported."""


class DatasetNotFoundError(DataError):
    """Raised when a dataset version cannot be located in the catalog."""


class DatasetImmutableError(DataError):
    """Raised when attempting to overwrite or alter an immutable manifest."""


class QualityValidationError(DataError):
    """Raised when data fails mandatory quality gates."""


class ResamplingError(DataError):
    """Raised when resampling cannot be computed between requested timeframes."""


class UniverseNotFoundError(DataError):
    """Raised when an asset basket or universe cannot be found."""


# ---------------------------------------------------------------------------
# Instrument Catalog DTOs
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class InstrumentDefinition:
    """Slotted immutable representation of a financial instrument's specification."""

    symbol: str
    id: int = 0
    connection: str = ""
    broker_id: int = 0
    description: str = ""
    tick_size: float = 0.00001
    tick_step: float = 0.00001
    tick_value_in_money: float = 10.0
    point_value: float = 100000.0
    decimals: int = 5
    default_spread: float = 0.0001
    default_slippage: float = 0.0
    min_volume: float = 0.01
    max_volume: float = 100.0
    lot_step: float = 0.01
    margin_rate: float = 0.05
    swap_long: float = 0.0
    swap_short: float = 0.0
    swap_3day_day: int = 3  # 0=Monday .. 6=Sunday; 3=Wednesday
    commissions: str = "0.0"
    data_type: str = "Forex"  # Forex, CFD, Futures, Stock, Crypto
    alias: str = ""
    exchange: str = ""
    country: str = ""
    sector: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True, frozen=True)
class BrokerAlias:
    """Mapping between a broker-specific ticker symbol and a canonical symbol."""

    canonical_symbol: str
    alias_symbol: str
    id: int = 0
    broker_id: int = 0
    notes: str = ""


@dataclass(slots=True, frozen=True)
class InstrumentValidationResult:
    """Outcome of validating instrument parameters against constraints."""

    is_valid: bool
    errors: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Sessions & Timezones DTOs
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class SessionWindow:
    """An active trading window for a specific day of the week."""

    day_of_week: int  # 0=Monday .. 6=Sunday
    open_time: str  # "HH:MM:SS" (e.g. "09:30:00")
    close_time: str  # "HH:MM:SS" (e.g. "16:00:00")


@dataclass(slots=True)
class SessionDefinition:
    """A trading session definition specifying daily/weekly windows and timezone."""

    name: str
    id: int = 0
    description: str = ""
    timezone: str = "UTC"
    windows: list[SessionWindow] = field(default_factory=list)
    holidays: list[str] = field(default_factory=list)  # ISO dates: ["2026-12-25"]
    is_default: bool = False


# ---------------------------------------------------------------------------
# Market Data Records (Bars & Ticks)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class BarRecord:
    """Normalized OHLCV bar with millisecond UTC timestamp and anomaly flags."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    source: str = ""
    anomaly_flags: int = 0

    def is_valid_ohlc(self) -> bool:
        """Verify structural OHLC invariants: High >= max and Low <= min."""
        return self.high >= max(self.open, self.close, self.low) and self.low <= min(
            self.open, self.close, self.high
        )


@dataclass(slots=True, frozen=True)
class TickRecord:
    """Normalized market tick record."""

    timestamp: datetime
    bid: float
    ask: float
    sequence: int = 0
    bid_volume: float = 0.0
    ask_volume: float = 0.0
    flags: int = 0


# ---------------------------------------------------------------------------
# Tabular Ingestion & Egress Specifications
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class DataFormatSpecification:
    """Format configuration for parsing tabular CSV/TXT market data files."""

    delimiter: str = ","
    has_header: bool = True
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    date_col: int = 0
    time_col: int | None = None
    open_col: int = 1
    high_col: int = 2
    low_col: int = 3
    close_col: int = 4
    volume_col: int | None = 5
    bid_col: int | None = None
    ask_col: int | None = None


@dataclass(slots=True, frozen=True)
class ImportResult:
    """Result of importing a tabular market data file."""

    dataset_id: str
    records_imported: int
    error_count: int
    row_errors: tuple[str, ...]
    timeframe: str
    data_kind: str


@dataclass(slots=True, frozen=True)
class ExportResult:
    """Result of exporting a normalized dataset to disk."""

    destination_path: str
    records_exported: int
    sha256_hash: str
    bytes_written: int


# ---------------------------------------------------------------------------
# Governed Market Data Retrieval & Sync DTOs
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class MarketDataRequest:
    """Structured request for market data retrieval from a configured provider."""

    source_id: str
    symbol: str
    data_kind: str = "bars"  # "bars" or "ticks"
    timeframe: str = "M1"
    start: datetime | None = None
    end: datetime | None = None
    store_data: bool = True


def build_market_data_request(
    source_id: str,
    symbol: str,
    *,
    data_kind: str = "bars",
    timeframe: str = "M1",
    start: datetime | None = None,
    end: datetime | None = None,
    store_data: bool = True,
) -> MarketDataRequest:
    """Construct a validated MarketDataRequest specification."""
    if not source_id.strip():
        raise ValueError("source_id must not be empty")
    if not symbol.strip():
        raise ValueError("symbol must not be empty")
    if data_kind not in ("bars", "ticks"):
        raise ValueError("data_kind must be either 'bars' or 'ticks'")
    if start is not None and end is not None and start > end:
        raise ValueError("start timestamp must not be later than end timestamp")
    return MarketDataRequest(
        source_id=source_id.strip(),
        symbol=symbol.strip(),
        data_kind=data_kind,
        timeframe=timeframe.strip().upper(),
        start=start,
        end=end,
        store_data=store_data,
    )


@dataclass(slots=True, frozen=True)
class SyncInterval:
    """Record of synchronized market data range for a symbol from a provider."""

    provider: str
    symbol: str
    start: datetime
    end: datetime
    records_fetched: int
    records_deduplicated: int
    dataset_id: str = ""


@dataclass(slots=True, frozen=True)
class SyncReport:
    """Outcome of connector synchronization."""

    started_at: datetime
    completed_at: datetime
    providers_synced: tuple[str, ...]
    total_records: int
    errors: tuple[str, ...] = ()
    intervals: tuple[SyncInterval, ...] = ()


# ---------------------------------------------------------------------------
# Immutable Datasets DTOs
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class DatasetManifest:
    """Manifest describing an immutable normalized market dataset version."""

    dataset_id: str
    symbol: str
    timeframe: str
    data_kind: str  # "bars" or "ticks"
    source_id: str
    start_time: datetime
    end_time: datetime
    row_count: int
    parquet_path: str
    sha256_hash: str
    schema_version: int = 1
    quality_score: float = 1.0
    lineage: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Quality Validation & Repair DTOs
# ---------------------------------------------------------------------------


class QualityAnomalyType(StrEnum):
    """Exhaustive anomaly classification matching SQX DataProblemEvaluator."""

    GAP = "GAP"
    LOW_PROBLEM = "LOW_PROBLEM"
    HIGH_PROBLEM = "HIGH_PROBLEM"
    SPIKE = "SPIKE"
    CROSSED_QUOTE = "CROSSED_QUOTE"
    DUPLICATE = "DUPLICATE"
    NON_MONOTONIC = "NON_MONOTONIC"
    OUT_OF_SESSION = "OUT_OF_SESSION"


@dataclass(slots=True, frozen=True)
class QualityAnomaly:
    """An individual quality anomaly detected in a time series."""

    anomaly_type: QualityAnomalyType
    timestamp: datetime
    description: str
    severity: str = "warning"  # "warning" or "error"
    observed_value: float = 0.0
    expected_range: tuple[float, float] | None = None


@dataclass(slots=True)
class QualityReport:
    """Summary of data quality evaluation over a dataset."""

    report_id: str
    dataset_id: str
    quality_score: float  # 0.0 to 1.0
    total_records: int
    anomalies: list[QualityAnomaly] = field(default_factory=list)
    anomaly_counts: dict[str, int] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True, frozen=True)
class RepairPolicy:
    """Configurable repair options for defective market data."""

    drop_invalid_ohlc: bool = True
    clamp_spikes: bool = False
    fill_small_gaps: bool = False
    max_fill_gap_bars: int = 3


@dataclass(slots=True, frozen=True)
class RepairResult:
    """Audit ledger of repair actions applied to defective market records."""

    original_count: int
    repaired_count: int
    modifications_count: int
    repairs_applied: tuple[str, ...]


# ---------------------------------------------------------------------------
# Universes & Baskets DTOs
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class BasketConstituent:
    """Point-in-time constituent membership in an asset basket."""

    symbol: str
    id: int = 0
    basket_id: int = 0
    date_from: datetime | None = None
    date_to: datetime | None = None

    def is_active_at(self, as_of: datetime) -> bool:
        """Check if symbol was an active constituent at specified timestamp."""
        if self.date_from and as_of < self.date_from:
            return False
        return not (self.date_to and as_of > self.date_to)


@dataclass(slots=True)
class UniverseBasket:
    """Named collection of symbols forming a dynamic asset universe."""

    name: str
    id: int = 0
    description: str = ""
    is_system: bool = False
    constituents: list[BasketConstituent] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service Protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class InstrumentCatalog(Protocol):
    """Protocol for instrument metadata, constraint checking, and broker aliasing."""

    async def get_instrument(self, symbol: str) -> InstrumentDefinition | None:
        """Retrieve instrument definition by canonical symbol or alias."""
        ...

    async def list_instruments(
        self, data_type: str | None = None
    ) -> list[InstrumentDefinition]:
        """List all instruments in the catalog, optionally filtered by type."""
        ...

    async def save_instrument(
        self, instrument: InstrumentDefinition
    ) -> InstrumentDefinition:
        """Persist or update an instrument definition."""
        ...

    async def delete_instrument(self, symbol: str) -> bool:
        """Delete an instrument definition from the catalog."""
        ...

    async def resolve_alias(
        self, alias_or_symbol: str, broker_id: int | None = None
    ) -> str:
        """Translate a broker-specific alias to its canonical symbol."""
        ...

    async def add_alias(
        self, canonical: str, alias: str, broker_id: int = 0, notes: str = ""
    ) -> BrokerAlias:
        """Register a broker-specific symbol alias."""
        ...

    async def list_aliases(self, symbol: str | None = None) -> list[BrokerAlias]:
        """List all registered symbol aliases."""
        ...

    def validate_instrument(
        self, instrument: InstrumentDefinition
    ) -> InstrumentValidationResult:
        """Validate mathematical and financial constraints of an instrument."""
        ...


@runtime_checkable
class SessionService(Protocol):
    """Protocol for trading session evaluation, weekly schedules, and timezones."""

    async def get_session(self, name: str) -> SessionDefinition | None:
        """Retrieve session profile by name."""
        ...

    async def get_default_session(self) -> SessionDefinition:
        """Retrieve the system default trading session profile."""
        ...

    async def save_session(self, session: SessionDefinition) -> SessionDefinition:
        """Persist or update a trading session definition."""
        ...

    async def list_sessions(self) -> list[SessionDefinition]:
        """List all configured session profiles."""
        ...

    def is_in_session(self, dt: datetime, session: SessionDefinition) -> bool:
        """Determine whether timestamp falls within active session trading hours."""
        ...

    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert a datetime instant from one timezone to another deterministically."""
        ...


@runtime_checkable
class ImportExportService(Protocol):
    """Protocol for tabular market data ingestion and platform export."""

    async def import_tabular_file(
        self,
        file_path: str,
        symbol: str,
        timeframe: str,
        format_spec: DataFormatSpecification | None = None,
        session_name: str | None = None,
    ) -> ImportResult:
        """Parse, validate, and publish market data from a tabular CSV/TXT file."""
        ...

    async def export_dataset(
        self,
        dataset_id: str,
        destination_path: str,
        format_name: str = "csv",
        delimiter: str = ",",
        include_header: bool = True,
    ) -> ExportResult:
        """Export a normalized dataset into a target format (CSV, MT4 HST/FXT, MT5)."""
        ...


@runtime_checkable
class MarketDataClient(Protocol):
    """Protocol for governed market data retrieval across provider connectors."""

    async def fetch_market_data(
        self, request: MarketDataRequest
    ) -> list[BarRecord] | list[TickRecord]:
        """Fetch market data per request specification with transparent caching."""
        ...

    def clear_cache(self) -> None:
        """Clear the in-memory/on-disk request cache."""
        ...


@runtime_checkable
class SyncConnectorsCapability(Protocol):
    """Protocol for asynchronous connector synchronization."""

    async def sync_connectors(
        self,
        provider_ids: list[str] | None = None,
        symbols: list[str] | None = None,
    ) -> SyncReport:
        """Coordinate idempotent synchronization with registered external providers."""
        ...


@runtime_checkable
class DatasetService(Protocol):
    """Protocol for immutable normalized dataset versions and Parquet manifests."""

    async def get_manifest(self, dataset_id: str) -> DatasetManifest | None:
        """Retrieve dataset manifest by unique dataset ID."""
        ...

    async def list_manifests(
        self, symbol: str | None = None, timeframe: str | None = None
    ) -> list[DatasetManifest]:
        """List dataset manifests matching optional filter criteria."""
        ...

    async def save_manifest(self, manifest: DatasetManifest) -> DatasetManifest:
        """Register an immutable dataset manifest."""
        ...

    async def load_bars(
        self,
        dataset_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[BarRecord]:
        """Load normalized bars from a published dataset version."""
        ...

    async def load_ticks(
        self,
        dataset_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[TickRecord]:
        """Load normalized ticks from a published dataset version."""
        ...

    async def persist_bars(
        self,
        symbol: str,
        timeframe: str,
        source_id: str,
        bars: list[BarRecord],
        *,
        lineage: dict[str, Any] | None = None,
        quality_score: float | None = None,
    ) -> DatasetManifest:
        """Persist normalized bars into Parquet dataset and publish manifest."""
        ...

    async def persist_ticks(
        self,
        symbol: str,
        source_id: str,
        ticks: list[TickRecord],
        *,
        lineage: dict[str, Any] | None = None,
        quality_score: float | None = None,
    ) -> DatasetManifest:
        """Persist normalized ticks into Parquet dataset and publish manifest."""
        ...


@runtime_checkable
class QualityService(Protocol):
    """Protocol for detecting time-series anomalies and generating repair plans."""

    def evaluate_quality(
        self,
        bars: list[BarRecord],
        session: SessionDefinition | None = None,
        timeframe: str = "M1",
        spike_multiplier: float = 3.5,
    ) -> QualityReport:
        """Scan bars for gaps, high/low inversions, spikes, and session violations."""
        ...

    def evaluate_tick_quality(
        self,
        ticks: list[TickRecord],
    ) -> QualityReport:
        """Scan ticks for crossed quotes, duplicate sequences, and timing errors."""
        ...

    def repair_data(
        self, bars: list[BarRecord], policy: RepairPolicy
    ) -> tuple[list[BarRecord], RepairResult]:
        """Apply deterministic repair policy to defective bars and record audit."""
        ...


@runtime_checkable
class ResamplingService(Protocol):
    """Protocol for session-aware resampling, 4-price ticks, and timezone cloning."""

    def resample_bars(
        self,
        bars: list[BarRecord],
        target_timeframe: str,
        session: SessionDefinition | None = None,
    ) -> list[BarRecord]:
        """Resample base bars into higher timeframe bars with session alignment."""
        ...

    def resample_ticks_to_bars(
        self,
        ticks: list[TickRecord],
        target_timeframe: str,
        session: SessionDefinition | None = None,
    ) -> list[BarRecord]:
        """Aggregate raw ticks into OHLC bars with session alignment."""
        ...

    def generate_4price_ticks(self, bar: BarRecord) -> list[TickRecord]:
        """Generate 4-price intrabar ticks (Open -> High/Low -> Low/High -> Close)."""
        ...

    def clone_to_timezone(
        self,
        bars: list[BarRecord],
        target_timezone: str,
        session: SessionDefinition | None = None,
    ) -> list[BarRecord]:
        """Project bar series into target timezone and re-align session boundaries."""
        ...


@runtime_checkable
class UniverseManagerService(Protocol):
    """Protocol for asset baskets and point-in-time constituent tracking."""

    async def get_basket(self, name_or_id: str | int) -> UniverseBasket | None:
        """Retrieve basket definition and constituents by name or ID."""
        ...

    async def list_baskets(self) -> list[UniverseBasket]:
        """List all asset baskets."""
        ...

    async def save_basket(self, basket: UniverseBasket) -> UniverseBasket:
        """Persist or update an asset basket definition."""
        ...

    async def delete_basket(self, basket_id: int) -> bool:
        """Delete a basket definition from the database."""
        ...

    async def get_point_in_time_constituents(
        self, basket_id: int, as_of: datetime
    ) -> list[str]:
        """Query active constituent symbols in a basket at a historical instant."""
        ...


@runtime_checkable
class DataPersistenceService(Protocol):
    """Protocol for SQLite storage operations under namespace `data.v1`."""

    async def initialize_schema(self) -> None:
        """Create and migrate database tables for the data domain."""
        ...

    async def get_instrument(self, symbol: str) -> InstrumentDefinition | None:
        """Retrieve instrument definition by symbol."""
        ...

    async def list_instruments(
        self, data_type: str | None = None
    ) -> list[InstrumentDefinition]:
        """List all instruments, optionally filtered by type."""
        ...

    async def save_instrument(
        self, instrument: InstrumentDefinition
    ) -> InstrumentDefinition:
        """Save or update an instrument definition."""
        ...

    async def delete_instrument(self, symbol: str) -> bool:
        """Delete an instrument definition by symbol."""
        ...

    async def get_alias(
        self, alias_symbol: str, broker_id: int | None = None
    ) -> str | None:
        """Resolve alias symbol to canonical symbol."""
        ...

    async def save_alias(self, alias: BrokerAlias) -> BrokerAlias:
        """Save or update a broker alias mapping."""
        ...

    async def list_aliases(self, symbol: str | None = None) -> list[BrokerAlias]:
        """List registered broker aliases."""
        ...

    async def get_session(self, name: str) -> SessionDefinition | None:
        """Retrieve trading session definition by name."""
        ...

    async def list_sessions(self) -> list[SessionDefinition]:
        """List all configured trading sessions."""
        ...

    async def save_session(self, session: SessionDefinition) -> SessionDefinition:
        """Save or update a trading session definition."""
        ...

    async def get_dataset_manifest(self, dataset_id: str) -> DatasetManifest | None:
        """Retrieve dataset manifest by ID."""
        ...

    async def list_dataset_manifests(
        self, symbol: str | None = None, timeframe: str | None = None
    ) -> list[DatasetManifest]:
        """List dataset manifests matching filters."""
        ...

    async def save_dataset_manifest(self, manifest: DatasetManifest) -> DatasetManifest:
        """Save or update a dataset manifest."""
        ...

    async def get_basket(self, name_or_id: str | int) -> UniverseBasket | None:
        """Retrieve asset basket by name or ID."""
        ...

    async def list_baskets(self) -> list[UniverseBasket]:
        """List all asset baskets."""
        ...

    async def save_basket(self, basket: UniverseBasket) -> UniverseBasket:
        """Save or update an asset basket."""
        ...

    async def delete_basket(self, basket_id: int) -> bool:
        """Delete an asset basket by ID."""
        ...

    async def save_quality_report(self, report: QualityReport) -> QualityReport:
        """Save a quality evaluation report."""
        ...

    async def get_quality_report(self, report_id: str) -> QualityReport | None:
        """Retrieve a quality evaluation report by ID."""
        ...


# ---------------------------------------------------------------------------
# Capability Tokens
# ---------------------------------------------------------------------------

DATA_INSTRUMENTS: Capability[InstrumentCatalog] = Capability("data.instruments@1")
DATA_SESSIONS: Capability[SessionService] = Capability("data.sessions@1")
DATA_IMPORTS_EXPORTS: Capability[ImportExportService] = Capability(
    "data.imports_exports@1"
)
DATA_MARKET_DATA: Capability[MarketDataClient] = Capability("data.market_data@1")
DATA_SYNC: Capability[SyncConnectorsCapability] = Capability("data.sync@1")
DATA_DATASETS: Capability[DatasetService] = Capability("data.datasets@1")
DATA_QUALITY: Capability[QualityService] = Capability("data.quality@1")
DATA_RESAMPLING: Capability[ResamplingService] = Capability("data.resampling@1")
DATA_UNIVERSES: Capability[UniverseManagerService] = Capability("data.universes@1")
DATA_PERSISTENCE: Capability[DataPersistenceService] = Capability("data.persistence@1")

"""Data Manager workspace REST router, API contracts, and host integration.

Description:
    Workspace composition explicitly invokes idempotent instrument and trading
    session default initialization. Services call narrow stores; connections,
    cursors, SQL and database transactions remain in app.host.persistence.

    Provides the central FastAPI REST router for the Data Manager workspace
    (`app.workspace.data_manager`). Exposes strongly-typed endpoints for
    datasets, instruments, sessions, baskets, broker profiles, provider downloads,
    CFTC COT series, custom time series, quality review, timeframe transforms,
    workspace overview metrics, operational audit logs, and user help guides.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Expose unified Data Manager workspace capabilities via
    FastAPI HTTP endpoints.

Key Capabilities:
    - FR-DATA-INTEGRATION-DATASETS: REST endpoints for dataset listing, querying,
      deletion, availability checks, and ingestion.
      Associated: `get_datasets`, `get_dataset`, `delete_dataset`,
        `check_dataset_availability`, `import_dataset`, `edit_dataset`,
        `clear_dataset_data`, `review_chart`, `clone_to_timezone`
      Logging: Emits INFO on dataset mutations and ingestion completion.
    - FR-DATA-INTEGRATION-INSTRUMENTS: REST endpoints for instrument CRUD.
      Associated: `list_instruments`, `get_instrument`, `create_instrument`,
        `update_instrument`, `delete_instrument`
      Logging: Emits INFO on instrument creations, updates, and deletions.
    - FR-DATA-INTEGRATION-SESSIONS: REST endpoints for session templates.
      Associated: `list_sessions`, `get_session`, `create_session`,
        `delete_session`, `import_nt_sessions`
      Logging: Emits INFO on session creations and NinjaTrader imports.
    - FR-DATA-INTEGRATION-BASKETS: REST endpoints for synthetic basket math.
      Associated: `list_baskets`, `get_basket`, `create_basket`,
        `delete_basket`, `compute_basket`
      Logging: Emits INFO on basket creation and series computation.
    - FR-DATA-INTEGRATION-PROVIDERS: REST endpoints for provider matrix.
      Associated: `list_providers`, `download_provider_data`
      Logging: Emits INFO on provider download execution.
    - FR-DATA-INTEGRATION-COT: REST endpoints for COT catalog and updates.
      Associated: `list_cot_mappings`, `get_cot_symbol`, `update_cot_symbol`
      Logging: Emits INFO on COT observation updates and calculations.
    - FR-DATA-INTEGRATION-QUALITY: REST endpoint for data quality auditing.
      Associated: `audit_data_quality`
      Logging: Emits INFO when quality audits are executed with envelope scores.
    - FR-DATA-INTEGRATION-TRANSFORMS: REST endpoints for resample and export.
      Associated: `resample_timeframe`, `export_series`
      Logging: Emits INFO on resampling and export operations.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.routes import create_data_router

    db = DatabaseManager()
    db.initialize()
    router = create_data_router(db)
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.routes --list-routes
    ```
"""

from __future__ import annotations

import argparse
import sys
import uuid
from concurrent.futures import Future
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from app.host.jobs import JobManager
from app.host.logging import get_logger
from app.host.persistence import DatabaseManager, TypedRepository, get_database_manager
from app.host.resources import ResourceManager
from app.host.response import StandardError
from app.host.transport import ApiResponse, EventBus
from app.workspace.data_manager.actions.review.quality import DataQualityInspector
from app.workspace.data_manager.actions.transform.transforms import (
    TIMEFRAME_MINUTES,
    SeriesTransformer,
)
from app.workspace.data_manager.baskets import (
    BasketDefinition,
    BasketService,
    export_groups_xml,
    import_groups_xml,
)
from app.workspace.data_manager.broker import (
    BrokerSavePayload,
    BrokerService,
    BrokerStocksPayload,
)
from app.workspace.data_manager.connections import DownloadRequest, ProviderManager
from app.workspace.data_manager.custom_data import CotService, CustomDataService
from app.workspace.data_manager.data import (
    BarRecord,
    CatalogService,
    DataIngestionService,
    IngestionConfig,
)
from app.workspace.data_manager.help import DataManagerHelpService
from app.workspace.data_manager.home import DataManagerHomeService
from app.workspace.data_manager.instruments import (
    InstrumentDefinition,
    InstrumentService,
)
from app.workspace.data_manager.log import DataManagerLogService
from app.workspace.data_manager.sessions import (
    SessionService,
    TradingSessionDefinition,
)
from app.workspace.data_manager.storage import MarketDataStorage

logger = get_logger(__name__)

DEFAULT_EXPORT_SPREAD = 2.0


def _execute_async_import(
    db_path_str: str,
    storage_dir_str: str,
    file_path_str: str,
    *,
    symbol: str,
    timeframe: str,
    broker: str,
    config_dict: dict[str, Any],
) -> dict[str, Any]:
    """Execute background ingestion job in worker process."""
    db = DatabaseManager(database_path=Path(db_path_str))
    catalog = CatalogService(db)
    service = DataIngestionService(catalog=catalog, storage_dir=Path(storage_dir_str))
    config = IngestionConfig.model_validate(config_dict)
    res = service.ingest_file(
        file_path=Path(file_path_str),
        symbol=symbol,
        timeframe=timeframe,
        source=broker,
        config=config,
    )
    return res.model_dump(mode="json")


def _execute_async_download(
    provider_name: str,
    symbol: str,
    timeframe: str,
    date_from: str,
    date_to: str,
) -> dict[str, Any]:
    """Execute background provider download job in worker process."""
    manager = ProviderManager()
    req = DownloadRequest(
        provider_name=provider_name,
        symbol=symbol,
        timeframe=timeframe,
        date_from=date_from,
        date_to=date_to,
    )
    bars = manager.download(req)
    if bars:
        db = get_database_manager()
        catalog = CatalogService(db)
        catalog.save_bars(
            source=provider_name,
            symbol=symbol,
            timeframe=timeframe,
            bars=bars,
        )
    return {
        "provider": provider_name,
        "symbol": symbol,
        "bars_count": len(bars),
    }


# ---------------------------------------------------------------------------
# Request & Response Payloads
# ---------------------------------------------------------------------------


class DatasetImportPayload(BaseModel):
    """Payload for importing market data into the catalog."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., min_length=1, description="Symbol ticker")
    timeframe: str = Field(default="M1", description="Bar timeframe")
    content: str | None = Field(default=None, description="Inline raw CSV/text content")
    file_path: str | None = Field(default=None, description="Path to file on disk")
    broker: str = Field(default="default", description="Associated broker profile")
    timezone: str = Field(default="UTC", description="Data timezone")
    data_type: str = Field(default="M1", description="Input data type")
    delimiter: str | None = Field(default=None, description="Delimiter override")
    has_header: bool | None = Field(
        default=None, description="Header presence override"
    )
    async_job: bool = Field(
        default=False, description="Submit ingestion as background compute job"
    )


class SessionImportNTPayload(BaseModel):
    """Payload for importing NinjaTrader session templates."""

    model_config = ConfigDict(extra="forbid")

    xml_content: str | None = Field(default=None, description="Raw NT XML content")
    folder_path: str | None = Field(
        default=None, description="Path to NT templates directory"
    )
    conflict_policy: str = Field(
        default="overwrite", description="'overwrite' or 'skip'"
    )


class SessionClonePayload(BaseModel):
    """Payload for cloning an existing trading session."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1, description="Source session name")
    new_name: str = Field(..., min_length=1, description="New session name")
    broker_id: int = Field(
        default=-1, description="Broker profile ID (-1 for SQ default)"
    )
    broker_postfix: str = Field(
        default="", description="Optional postfix for broker session"
    )


class SessionMassDeletePayload(BaseModel):
    """Payload for batch deleting multiple trading sessions."""

    model_config = ConfigDict(extra="forbid")

    names: list[str] = Field(
        ..., min_length=1, description="List of session names to delete"
    )


class SessionImportXmlPayload(BaseModel):
    """Payload for importing StrategyQuant X Sessions.xml."""

    model_config = ConfigDict(extra="forbid")

    xml_content: str = Field(..., min_length=1, description="Raw SQX XML content")
    policy: str = Field(default="overwrite", description="'overwrite' or 'skip'")


class SessionExportXmlPayload(BaseModel):
    """Payload for exporting StrategyQuant X Sessions.xml."""

    model_config = ConfigDict(extra="forbid")

    names: list[str] = Field(
        default_factory=list, description="List of session names to export"
    )


class BasketComputePayload(BaseModel):
    """Payload for calculating synthetic composite basket series."""

    model_config = ConfigDict(extra="forbid")

    basket: BasketDefinition
    series: dict[str, list[BarRecord]]
    alignment_mode: str = Field(
        default="intersection", description="'intersection' or 'union'"
    )


class BasketCsvImportPayload(BaseModel):
    """Payload for importing stock constituents from CSV text."""

    model_config = ConfigDict(extra="forbid")

    basket_name: str = Field(..., description="Target basket name")
    csv_text: str = Field(..., description="Multi-line CSV text (Ticker;From;To)")


class BasketXmlImportPayload(BaseModel):
    """Payload for importing stock groups from SQX XML."""

    model_config = ConfigDict(extra="forbid")

    xml_content: str = Field(..., description="Canonical SQX XML string")
    overwrite: bool = Field(
        default=False, description="Whether to overwrite existing groups"
    )


class BasketXmlExportPayload(BaseModel):
    """Payload for exporting stock groups to SQX XML."""

    model_config = ConfigDict(extra="forbid")

    basket_names: list[str] = Field(
        default_factory=list, description="Optional subset of basket names"
    )


class BasketUpdateDataPayload(BaseModel):
    """Payload for triggering automatic data update for stock group(s)."""

    model_config = ConfigDict(extra="ignore")

    basket_ids: list[str] | list[int] | str | int = Field(
        ...,
        description="Single basket ID, list of IDs, or comma-separated string",
    )


class ProviderDownloadPayload(BaseModel):
    """Payload for triggering provider downloads."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(..., description="Provider name")
    symbol: str = Field(..., description="Target symbol")
    timeframe: str = Field(default="M1", description="Target timeframe")
    date_from: str = Field(default="2020-01-01", description="Start date (YYYY-MM-DD)")
    date_to: str = Field(default="2020-01-02", description="End date (YYYY-MM-DD)")
    async_job: bool = Field(
        default=False, description="Submit download as background compute job"
    )


class CotUpdatePayload(BaseModel):
    """Payload for updating COT observations."""

    model_config = ConfigDict(extra="forbid")

    reports: list[dict[str, Any]] = Field(
        default_factory=list, description="Raw CFTC report rows"
    )
    lookback_weeks: int = Field(default=26, description="Lookback window in weeks")


class QualityAuditPayload(BaseModel):
    """Payload for auditing bar data quality."""

    model_config = ConfigDict(extra="forbid")

    bars: list[BarRecord] = Field(..., description="List of bar records to audit")
    timeframe: str = Field(default="M1", description="Expected timeframe")
    strict: bool = Field(default=False, description="Strict anomaly mode")


class ResamplePayload(BaseModel):
    """Payload for resampling M1 bars."""

    model_config = ConfigDict(extra="forbid")

    bars: list[BarRecord] = Field(..., description="M1 source bars")
    target_timeframe: str = Field(
        ..., description="Target timeframe (M5, M15, M30, H1, H4, D1)"
    )


class ExportPayload(BaseModel):
    """Payload for exporting series in specified format."""

    model_config = ConfigDict(extra="forbid")

    bars: list[BarRecord] = Field(
        default_factory=list, description="Source bars to export"
    )
    dataset_id: str | None = Field(
        default=None, description="Optional source dataset ID to export"
    )
    format: str = Field(
        default="csv",
        description="'csv', 'mt4', 'mt4_hst', 'mt4_fxt', 'mt5', or 'custom'",
    )
    format_name: str | None = Field(
        default=None, description="Saved CSV format profile name"
    )
    items: list[str] | None = Field(
        default=None, description="Custom token list for CSV export"
    )
    delimiter: str = Field(default=",", description="Delimiter for CSV export")
    include_header: bool = Field(
        default=False, description="Whether to include CSV header"
    )
    symbol: str = Field(default="EURUSD", description="Symbol identifier")
    timeframe: str = Field(default="M1", description="Timeframe identifier")
    digits: int = Field(default=5, ge=0, le=8, description="Price decimals")
    output_path: str | None = Field(default=None, description="Optional output path")
    spread: float = Field(default=2.0, ge=0.0, description="Spread in pips/points")
    real_spread: bool = Field(
        default=False, description="Use real ask-bid spread for MT5"
    )


class DatasetEditPayload(BaseModel):
    """Payload for editing dataset configuration metadata."""

    model_config = ConfigDict(extra="forbid")

    symbol_new: str | None = Field(default=None, description="Updated symbol name")
    instrument: str | None = Field(
        default=None, description="Updated instrument symbol"
    )
    timezone: str | None = Field(default=None, description="Updated timezone")
    category: str | None = Field(default=None, description="Updated asset category")


class ReviewChartPayload(BaseModel):
    """Payload for chart review bar slice extraction."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., description="Target dataset ID")
    date_from: str | None = Field(default=None, description="Start date ISO string")
    date_to: str | None = Field(default=None, description="End date ISO string")
    limit: int = Field(default=1000, ge=1, le=50000, description="Max bars to return")
    offset: int = Field(default=0, ge=0, description="Offset in bars")


class CloneTimezonePayload(BaseModel):
    """Payload for cloning a dataset into another timezone."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., description="Target dataset ID")
    target_timezone: str | None = Field(
        default=None, description="Target timezone name (e.g. Europe/Prague)"
    )
    timezone_type: str = Field(default="zone", description="'zone' or 'hours'")
    shift_hours: int | None = Field(
        default=None, ge=-23, le=23, description="Fixed hour offset (-23 to 23)"
    )
    remove_weekends: bool = Field(
        default=False, description="Whether to drop Saturday and Sunday bars"
    )
    postfix: str | None = Field(
        default=None, description="Template postfix, e.g. '_{timeframe}_{cloneTime}'"
    )
    new_dataset_id: str | None = Field(
        default=None, description="Optional new dataset ID"
    )


class SaveDataChangesPayload(BaseModel):
    """Payload for updating modified cells or deleted rows in dataset storage."""

    model_config = ConfigDict(extra="ignore")

    dataset_id: str | None = Field(default=None, description="Dataset identifier")
    symbol: str | None = Field(default=None, description="Symbol")
    timeframe: str | None = Field(default=None, description="Timeframe")
    changed_bars: list[BarRecord] = Field(
        default_factory=list, description="List of modified or new bars"
    )
    deleted_timestamps: list[str] = Field(
        default_factory=list, description="List of ISO timestamps to delete"
    )


class MassDeletePayload(BaseModel):
    """Payload for batch delete or clear operations on datasets."""

    model_config = ConfigDict(extra="forbid")

    dataset_ids: list[str] = Field(
        ..., min_length=1, description="List of dataset IDs to delete/clear"
    )
    action: str = Field(
        default="remove", description="'remove' (full deletion) or 'clear' (wipe data)"
    )
    force: bool = Field(default=False, description="Override clone dependency guard")


class DatasetXmlExportPayload(BaseModel):
    """Payload for exporting datasets to SQX <Data> XML."""

    model_config = ConfigDict(extra="forbid")

    dataset_ids: list[str] | None = Field(
        default=None, description="Optional list of dataset IDs (all if omitted)"
    )


class DatasetXmlImportPayload(BaseModel):
    """Payload for importing datasets and brokers from SQX <Data> XML."""

    model_config = ConfigDict(extra="forbid")

    xml_content: str = Field(..., min_length=1, description="Raw SQX <Data> XML string")


class BrokerDeleteRequest(BaseModel):
    """Payload for deleting multiple broker profiles."""

    model_config = ConfigDict(extra="ignore")

    broker_ids: list[int] = Field(
        ..., min_length=1, description="List of broker IDs to delete"
    )


class BrokerImportStocksRequest(BaseModel):
    """Payload for importing stocks to a broker profile from CSV/text."""

    model_config = ConfigDict(extra="ignore")

    content: str = Field(..., min_length=1, description="Raw multi-line stock text")


class BrokerXmlExportRequest(BaseModel):
    """Payload for exporting broker profiles to XML."""

    model_config = ConfigDict(extra="ignore")

    broker_ids: list[int] | None = Field(
        default=None, description="Optional broker IDs filter"
    )


class BrokerXmlImportRequest(BaseModel):
    """Payload for importing broker profiles from XML text."""

    model_config = ConfigDict(extra="ignore")

    xml_content: str = Field(..., min_length=1, description="Raw <Brokers> XML string")


class BrokerXmlOverviewRequest(BaseModel):
    """Payload for inspecting MT XML overview."""

    model_config = ConfigDict(extra="ignore")

    xml_content: str = Field(..., min_length=1, description="Raw MetaTrader XML string")
    kind: str = Field(default="instrument", pattern="^(instrument|session)$")


class BrokerXmlImportRecordsRequest(BaseModel):
    """Payload for importing selected MT XML instruments or sessions."""

    model_config = ConfigDict(extra="ignore")

    xml_content: str = Field(..., min_length=1, description="Raw MetaTrader XML string")
    kind: str = Field(default="instrument", pattern="^(instrument|session)$")
    broker_id: int = Field(..., description="Target broker ID")
    postfix: str = Field(default="", description="Symbol postfix")
    selected_names: list[str] = Field(
        ..., min_length=1, description="Selected names to import"
    )


class UpdateSelectedPayload(BaseModel):
    """Payload for batch updating selected datasets."""

    model_config = ConfigDict(extra="forbid")

    dataset_ids: list[str] = Field(
        ..., min_length=1, description="List of dataset IDs to update"
    )


class CsvFormatProfile(BaseModel):
    """Saved CSV export token format profile."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, description="Format profile name")
    items: list[str] = Field(
        default_factory=list,
        description="Ordered token list, e.g. ['[date:yyyyMMdd]', ...]",
    )
    delimiter: str = Field(default=",", description="CSV column delimiter")
    header: bool | str = Field(
        default=False, description="Include column header row or custom header line"
    )
    date_format: str = Field(default="yyyyMMdd", description="Default date format")
    time_format: str = Field(default="HHmmss", description="Default time format")


CANONICAL_CSV_FORMATS: list[dict[str, Any]] = [
    {
        "name": "Generic bar format (comma delimited)",
        "items": [
            "[date:yyyyMMdd]",
            "[time:HHmmss]",
            "[open]",
            "[high]",
            "[low]",
            "[close]",
            "[volume]",
        ],
        "delimiter": ",",
        "header": False,
        "date_format": "yyyyMMdd",
        "time_format": "HHmmss",
    },
    {
        "name": "Generic bar format (semicolon delimited)",
        "items": [
            "[date:yyyyMMdd]",
            "[time:HHmmss]",
            "[open]",
            "[high]",
            "[low]",
            "[close]",
            "[volume]",
        ],
        "delimiter": ";",
        "header": False,
        "date_format": "yyyyMMdd",
        "time_format": "HHmmss",
    },
    {
        "name": "Generic tick format (comma delimited)",
        "items": ["[datetime:yyyyMMdd HH:mm:ss.SSS]", "[bid]", "[ask]", "[volume]"],
        "delimiter": ",",
        "header": False,
        "date_format": "yyyyMMdd HH:mm:ss.SSS",
        "time_format": "",
    },
    {
        "name": "MetaTrader 4 bar format",
        "items": [
            "[date:yyyy.MM.dd]",
            "[time:HH:mm]",
            "[open]",
            "[high]",
            "[low]",
            "[close]",
            "[volume]",
        ],
        "delimiter": ",",
        "header": False,
        "date_format": "yyyy.MM.dd",
        "time_format": "HH:mm",
    },
    {
        "name": "MetaTrader 5 bar format",
        "items": [
            "[date:yyyy.MM.dd]",
            "[time:HH:mm]",
            "[open]",
            "[high]",
            "[low]",
            "[close]",
            "[volume]",
            "[spread]",
        ],
        "delimiter": "\t",
        "header": False,
        "date_format": "yyyy.MM.dd",
        "time_format": "HH:mm",
    },
]


# ---------------------------------------------------------------------------
# Router Handler Service
# ---------------------------------------------------------------------------


class DataRouterService:
    """Service container encapsulating Data Manager workspace route handlers."""

    def __init__(
        self,
        db: DatabaseManager,
        res_dir: Path,
        *,
        job_manager: JobManager | None = None,
        event_bus: EventBus | None = None,
        provider_manager: ProviderManager | None = None,
    ) -> None:
        """Initialize all backing domain services."""
        self.db = db
        self.res_dir = res_dir
        self.job_manager = job_manager
        self.event_bus = event_bus
        self.storage = MarketDataStorage(base_dir=res_dir / "datasets")
        self.catalog = CatalogService(db, storage=self.storage)
        self.instruments = InstrumentService(db)
        self.sessions = SessionService(db)
        self.instruments.ensure_defaults()
        self.sessions.ensure_defaults()
        self.baskets = BasketService(db)
        self.baskets.ensure_defaults()
        self.broker = BrokerService(db)
        self.home = DataManagerHomeService(db)
        self.log = DataManagerLogService(db)
        self.help = DataManagerHelpService()
        self.ingestion = DataIngestionService(
            catalog=self.catalog, storage_dir=res_dir / "datasets"
        )
        self.quality = DataQualityInspector()
        self.transformer = SeriesTransformer()
        self.providers = (
            provider_manager if provider_manager is not None else ProviderManager()
        )
        self.custom_data = CustomDataService(db=db, storage_dir=res_dir / "custom_data")
        self.cot = CotService(db=db, storage_dir=res_dir / "cot")
        self.csv_formats_repo = TypedRepository(
            db,
            entity_type="csv_format",
            model_cls=CsvFormatProfile,
            scope="global",
        )

    def _emit_event(
        self, channel: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        """Publish real-time notification to host event bus if available."""
        if self.event_bus is not None:
            try:
                self.event_bus.publish(
                    channel=channel, event_type=event_type, payload=payload
                )
            except Exception:
                logger.exception("Failed to publish event to channel '%s'", channel)

    def _error_response(
        self,
        status_code: int,
        code: str,
        message: str,
        request_id: str | None = None,
    ) -> JSONResponse:
        """Construct standard error JSONResponse."""
        err = StandardError(code=code, message=message)
        resp = ApiResponse.failure(message=message, error=err, request_id=request_id)
        return JSONResponse(status_code=status_code, content=resp.to_dict())

    # Datasets
    def list_datasets(
        self,
        request: Request,
        source: str | None = None,
        symbol: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Response:
        """List catalog datasets."""
        req_id = request.headers.get("x-request-id")
        datasets = self.catalog.list_datasets(
            source=source, symbol=symbol, limit=limit, offset=offset
        )
        logger.debug(
            "FR-DATA-INTEGRATION-DATASETS: Listed %d datasets",
            len(datasets),
            extra={"fr_id": "FR-DATA-INTEGRATION-DATASETS", "count": len(datasets)},
        )
        resp = ApiResponse.success(
            data=[d.model_dump(mode="json") for d in datasets],
            message=f"Retrieved {len(datasets)} dataset(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_dataset(self, request: Request, dataset_id: str) -> Response:
        """Get dataset record by ID."""
        req_id = request.headers.get("x-request-id")
        record = self.catalog.get_dataset(dataset_id)
        if record is None:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "DATASET_NOT_FOUND",
                f"Dataset '{dataset_id}' not found",
                req_id,
            )
        logger.debug(
            "FR-DATA-INTEGRATION-DATASETS: Retrieved dataset '%s'",
            dataset_id,
            extra={"fr_id": "FR-DATA-INTEGRATION-DATASETS", "dataset_id": dataset_id},
        )
        resp = ApiResponse.success(
            data=record.model_dump(mode="json"),
            message="Dataset retrieved successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def delete_dataset(self, request: Request, dataset_id: str) -> Response:
        """Delete dataset from catalog."""
        req_id = request.headers.get("x-request-id")
        deleted = self.catalog.delete_dataset(dataset_id)
        if not deleted:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "DATASET_NOT_FOUND",
                f"Dataset '{dataset_id}' not found",
                req_id,
            )
        self._emit_event("data.dataset", "deleted", {"dataset_id": dataset_id})
        logger.info(
            "FR-DATA-INTEGRATION-DATASETS: Deleted dataset '%s'",
            dataset_id,
            extra={"fr_id": "FR-DATA-INTEGRATION-DATASETS", "dataset_id": dataset_id},
        )
        resp = ApiResponse.success(
            data={"deleted": True, "dataset_id": dataset_id},
            message=f"Dataset '{dataset_id}' deleted successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def edit_dataset(
        self, request: Request, dataset_id: str, payload: DatasetEditPayload
    ) -> Response:
        """Edit dataset metadata in catalog."""
        req_id = request.headers.get("x-request-id")
        success = self.catalog.edit_dataset(
            dataset_id,
            symbol_new=payload.symbol_new,
            instrument=payload.instrument,
            timezone=payload.timezone,
            category=payload.category,
        )
        if not success:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "DATASET_NOT_FOUND",
                f"Dataset '{dataset_id}' not found",
                req_id,
            )
        self._emit_event(
            "data.dataset",
            "updated",
            {"dataset_id": dataset_id, **payload.model_dump(exclude_none=True)},
        )
        logger.info(
            "FR-DATA-INTEGRATION-DATASETS: Edited dataset '%s'",
            dataset_id,
            extra={"fr_id": "FR-DATA-INTEGRATION-DATASETS", "dataset_id": dataset_id},
        )
        resp = ApiResponse.success(
            data={"dataset_id": dataset_id, "updated": True},
            message=f"Dataset '{dataset_id}' updated successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def clear_dataset_data(self, request: Request, dataset_id: str) -> Response:
        """Clear on-disk Parquet data while preserving catalog definition."""
        req_id = request.headers.get("x-request-id")
        success = self.catalog.clear_data(dataset_id)
        if not success:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "DATASET_NOT_FOUND",
                f"Dataset '{dataset_id}' not found",
                req_id,
            )
        self._emit_event("data.dataset", "cleared", {"dataset_id": dataset_id})
        logger.info(
            "FR-DATA-INTEGRATION-DATASETS: Cleared partition data for dataset '%s'",
            dataset_id,
            extra={"fr_id": "FR-DATA-INTEGRATION-DATASETS", "dataset_id": dataset_id},
        )
        resp = ApiResponse.success(
            data={"dataset_id": dataset_id, "cleared": True},
            message=f"Data for dataset '{dataset_id}' cleared successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def check_availability(
        self, request: Request, symbol: str, timeframe: str
    ) -> Response:
        """Check availability of symbol and timeframe."""
        req_id = request.headers.get("x-request-id")
        is_avail, status_str = self.catalog.check_availability(symbol, timeframe)
        logger.debug(
            "FR-DATA-INTEGRATION-DATASETS: Availability for %s %s: %s",
            symbol,
            timeframe,
            status_str,
            extra={
                "fr_id": "FR-DATA-INTEGRATION-DATASETS",
                "symbol": symbol,
                "timeframe": timeframe,
                "status": status_str,
            },
        )
        resp = ApiResponse.success(
            data={
                "symbol": symbol,
                "timeframe": timeframe,
                "is_available": is_avail,
                "status": status_str,
            },
            message="Availability check completed",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def import_dataset(
        self, request: Request, payload: DatasetImportPayload
    ) -> Response:
        """Import dataset from inline content or file."""
        req_id = request.headers.get("x-request-id")
        if payload.content is None and payload.file_path is None:
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "INVALID_ARGUMENT",
                "Either 'content' or 'file_path' must be provided",
                req_id,
            )

        config = IngestionConfig(
            delimiter=payload.delimiter,
            has_header=payload.has_header,
        )

        try:
            if payload.async_job and self.job_manager is not None:
                staging_target: Path
                if payload.content is not None:
                    staging_dir = self.res_dir / "staging"
                    staging_dir.mkdir(parents=True, exist_ok=True)
                    staging_target = staging_dir / f"import_{uuid.uuid4().hex[:8]}.csv"
                    staging_target.write_text(payload.content, encoding="utf-8")
                else:
                    staging_target = Path(payload.file_path or "")

                storage_dir = self.res_dir / "datasets"
                future = self.job_manager.submit(
                    "data_manager",
                    _execute_async_import,
                    str(self.db.database_path),
                    str(storage_dir),
                    str(staging_target),
                    symbol=payload.symbol,
                    timeframe=payload.timeframe,
                    broker=payload.broker,
                    config_dict=config.model_dump(),
                    kind="dataset_import",
                )
                job_id = self.job_manager.get_job_id_for_future(future) or ""

                def _on_import_done(fut: Future[Any]) -> None:
                    exc = fut.exception()
                    if exc is not None:
                        logger.warning(
                            "FR-DATA-INTEGRATION-DATASETS: Async import failed: %s",
                            exc,
                        )
                        return
                    res = fut.result()
                    self._emit_event("data.dataset", "created", res)

                future.add_done_callback(_on_import_done)

                resp = ApiResponse.success(
                    data={
                        "job_id": job_id,
                        "status": "pending",
                        "symbol": payload.symbol,
                    },
                    message=(f"Dataset import submitted as background job '{job_id}'"),
                    request_id=req_id,
                )
                return JSONResponse(
                    status_code=status.HTTP_202_ACCEPTED, content=resp.to_dict()
                )

            if payload.content is not None:
                staging_dir = self.res_dir / "staging"
                staging_dir.mkdir(parents=True, exist_ok=True)
                temp_file = staging_dir / f"import_{uuid.uuid4().hex[:8]}.csv"
                temp_file.write_text(payload.content, encoding="utf-8")
                res = self.ingestion.ingest_file(
                    file_path=temp_file,
                    symbol=payload.symbol,
                    timeframe=payload.timeframe,
                    source=payload.broker,
                    config=config,
                )
            elif payload.file_path is not None:
                res = self.ingestion.ingest_file(
                    file_path=Path(payload.file_path),
                    symbol=payload.symbol,
                    timeframe=payload.timeframe,
                    source=payload.broker,
                    config=config,
                )
            else:
                return self._error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "INVALID_ARGUMENT",
                    "Either 'content' or 'file_path' must be provided",
                    req_id,
                )

            self._emit_event("data.dataset", "created", res.model_dump(mode="json"))
            logger.info(
                "FR-DATA-INTEGRATION-DATASETS: Ingested %d bars for symbol '%s'",
                res.bar_count,
                payload.symbol,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-DATASETS",
                    "symbol": payload.symbol,
                    "bars_count": res.bar_count,
                    "dataset_id": res.dataset_id,
                },
            )
            resp = ApiResponse.success(
                data=res.model_dump(mode="json"),
                message=f"Dataset '{res.dataset_id}' imported successfully",
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-DATASETS: Ingestion failed for %s",
                payload.symbol,
                extra={"fr_id": "FR-DATA-INTEGRATION-DATASETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "INGESTION_ERROR",
                f"Data ingestion failed: {exc}",
                req_id,
            )

    def review_chart(self, request: Request, payload: ReviewChartPayload) -> Response:
        """Review chart bars slice from canonical Parquet partitions."""
        req_id = request.headers.get("x-request-id")
        bars = self.catalog.review_chart(
            payload.dataset_id,
            date_from=payload.date_from,
            date_to=payload.date_to,
            limit=payload.limit,
            offset=payload.offset,
        )
        logger.debug(
            "FR-DATA-INTEGRATION-DATASETS: Extracted %d chart review bars for %s",
            len(bars),
            payload.dataset_id,
            extra={
                "fr_id": "FR-DATA-INTEGRATION-DATASETS",
                "dataset_id": payload.dataset_id,
                "count": len(bars),
            },
        )
        resp = ApiResponse.success(
            data={
                "dataset_id": payload.dataset_id,
                "count": len(bars),
                "bars": bars,
            },
            message=f"Extracted {len(bars)} bar(s) for chart review",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def clone_to_timezone(
        self, request: Request, payload: CloneTimezonePayload
    ) -> Response:
        """Clone existing dataset into another timezone partition."""
        req_id = request.headers.get("x-request-id")
        try:
            new_id = self.catalog.clone_to_timezone(
                payload.dataset_id,
                target_timezone=payload.target_timezone,
                timezone_type=payload.timezone_type,
                shift_hours=payload.shift_hours,
                remove_weekends=payload.remove_weekends,
                postfix=payload.postfix,
                new_dataset_id=payload.new_dataset_id,
            )
            self._emit_event(
                "data.dataset",
                "cloned",
                {"source_id": payload.dataset_id, "cloned_id": new_id},
            )
            logger.info(
                "FR-DATA-INTEGRATION-DATASETS: Cloned dataset '%s' to '%s' "
                "(timezone=%s)",
                payload.dataset_id,
                new_id,
                payload.target_timezone,
                extra={"fr_id": "FR-DATA-INTEGRATION-DATASETS", "new_id": new_id},
            )
            resp = ApiResponse.success(
                data={"source_id": payload.dataset_id, "cloned_id": new_id},
                message=f"Cloned dataset to timezone '{payload.target_timezone}'",
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-DATASETS: Timezone clone failed",
                extra={"fr_id": "FR-DATA-INTEGRATION-DATASETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "CLONE_TIMEZONE_ERROR",
                f"Failed to clone dataset to timezone: {exc}",
                req_id,
            )

    def _resolve_dataset_id(
        self,
        dataset_id: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        source: str | None = None,
    ) -> str:
        """Resolve dataset ID from explicit ID or symbol/timeframe lookup."""
        if dataset_id:
            return dataset_id
        if symbol:
            all_ds = self.catalog.list_datasets()
            for ds in all_ds:
                if ds.symbol.upper() == symbol.upper():
                    if timeframe and ds.timeframe.upper() != timeframe.upper():
                        continue
                    if source and ds.source.upper() != source.upper():
                        continue
                    return ds.id
        raise ValueError(
            f"Could not resolve dataset for dataset_id={dataset_id}, "
            f"symbol={symbol}, timeframe={timeframe}"
        )

    def review_data(
        self,
        request: Request,
        dataset_id: str | None = None,
        *,
        symbol: str | None = None,
        timeframe: str | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
        session_name: str | None = None,
    ) -> Response:
        """Fetch paginated bar records for review/inspection."""
        req_id = request.headers.get("x-request-id")
        try:
            target_id = self._resolve_dataset_id(dataset_id, symbol, timeframe, source)
            res = self.catalog.get_review_rows(
                target_id, limit=limit, offset=offset, session_name=session_name
            )
            resp = ApiResponse.success(data=res, request_id=req_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", str(exc), req_id
            )

    def get_index_for_date(
        self,
        request: Request,
        dataset_id: str | None = None,
        *,
        symbol: str | None = None,
        timeframe: str | None = None,
        source: str | None = None,
        date: str | None = None,
        target_date: str | None = None,
    ) -> Response:
        """Find bar index matching or immediately after target date."""
        req_id = request.headers.get("x-request-id")
        target_dt = date or target_date
        if not target_dt:
            return self._error_response(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "VALIDATION_ERROR",
                "Missing 'date' or 'target_date' parameter.",
                req_id,
            )
        try:
            target_id = self._resolve_dataset_id(dataset_id, symbol, timeframe, source)
            idx = self.catalog.get_index_for_date(target_id, target_dt)
            resp = ApiResponse.success(
                data={"dataset_id": target_id, "date": target_dt, "index": idx},
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status.HTTP_404_NOT_FOUND, "NOT_FOUND", str(exc), req_id
            )

    def save_data_changes(
        self,
        request: Request,
        payload: SaveDataChangesPayload,
        dataset_id: str | None = None,
    ) -> Response:
        """Save edited or deleted bars directly into partitioned Parquet files."""
        req_id = request.headers.get("x-request-id")
        try:
            target_id = self._resolve_dataset_id(
                dataset_id=dataset_id or payload.dataset_id,
                symbol=payload.symbol,
                timeframe=payload.timeframe,
            )
            updated = self.catalog.save_data_changes(
                target_id,
                changed_bars=payload.changed_bars,
                deleted_timestamps=set(payload.deleted_timestamps),
            )
            self._emit_event(
                "data.dataset",
                "modified",
                {"dataset_id": target_id, "bars": updated.bars},
            )
            resp = ApiResponse.success(
                data=updated.model_dump(mode="json"),
                message="Data changes saved successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError, OSError) as exc:
            logger.exception("Failed to save data changes")
            return self._error_response(
                status.HTTP_400_BAD_REQUEST, "SAVE_CHANGES_FAILED", str(exc), req_id
            )

    def quality_summary(
        self,
        request: Request,
        dataset_id: str | None = None,
        *,
        symbol: str | None = None,
        timeframe: str | None = None,
        source: str | None = None,
    ) -> Response:
        """Retrieve quality defect summary and 24-hour error distribution."""
        req_id = request.headers.get("x-request-id")
        try:
            target_id = self._resolve_dataset_id(dataset_id, symbol, timeframe, source)
            summary = self.catalog.check_quality_summary(target_id)
            data_out = {
                **summary,
                "errorDistribution": summary.get("distribution", []),
                "problems": summary,
            }
            resp = ApiResponse.success(data=data_out, request_id=req_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status.HTTP_404_NOT_FOUND, "NOT_FOUND", str(exc), req_id
            )

    def quality_details(
        self,
        request: Request,
        dataset_id: str | None = None,
        *,
        symbol: str | None = None,
        timeframe: str | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Response:
        """Retrieve paginated defect bars for quality review."""
        req_id = request.headers.get("x-request-id")
        try:
            target_id = self._resolve_dataset_id(dataset_id, symbol, timeframe, source)
            details = self.catalog.check_quality_details(
                target_id, limit=limit, offset=offset
            )
            resp = ApiResponse.success(data=details, request_id=req_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status.HTTP_404_NOT_FOUND, "NOT_FOUND", str(exc), req_id
            )

    def mass_delete(self, request: Request, payload: MassDeletePayload) -> Response:
        """Execute batch delete or clear with clone dependency guard."""
        req_id = request.headers.get("x-request-id")
        try:
            res = self.catalog.mass_delete(
                dataset_ids=payload.dataset_ids,
                action=payload.action,
                force=payload.force,
            )
            self._emit_event(
                "data.dataset",
                "mass_delete",
                {"count": res["deleted_count"], "action": payload.action},
            )
            resp = ApiResponse.success(
                data=res,
                message=(
                    f"Batch {payload.action} completed for "
                    f"{res['deleted_count']} datasets."
                ),
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ValueError as exc:
            is_dep = "CLONE_DEPENDENCY" in str(exc)
            code = "CLONE_DEPENDENCY" if is_dep else "INVALID_PARAM"
            return self._error_response(
                status.HTTP_400_BAD_REQUEST, code, str(exc), req_id
            )
        except (KeyError, RuntimeError, OSError) as exc:
            logger.exception("Mass delete failed")
            return self._error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "MASS_DELETE_FAILED",
                str(exc),
                req_id,
            )

    def export_catalog_xml(
        self, request: Request, payload: DatasetXmlExportPayload
    ) -> Response:
        """Export datasets and brokers in SQX <Data> XML format."""
        req_id = request.headers.get("x-request-id")
        try:
            xml_str = self.catalog.export_catalog_xml(payload.dataset_ids)
            resp = ApiResponse.success(
                data={"xml_content": xml_str},
                message="Catalog XML exported successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError, OSError) as exc:
            logger.exception("Catalog XML export failed")
            return self._error_response(
                status.HTTP_400_BAD_REQUEST, "EXPORT_XML_FAILED", str(exc), req_id
            )

    def import_catalog_xml(
        self, request: Request, payload: DatasetXmlImportPayload
    ) -> Response:
        """Import datasets and brokers from SQX <Data> XML."""
        req_id = request.headers.get("x-request-id")
        try:
            counts = self.catalog.import_catalog_xml(payload.xml_content)
            self._emit_event("data.catalog", "imported_xml", counts)
            msg = (
                f"Imported {counts['datasets_imported']} datasets, "
                f"{counts['brokers_imported']} brokers."
            )
            resp = ApiResponse.success(
                data=counts,
                message=msg,
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError, OSError) as exc:
            logger.exception("Catalog XML import failed")
            return self._error_response(
                status.HTTP_400_BAD_REQUEST, "IMPORT_XML_FAILED", str(exc), req_id
            )

    def update_all_datasets(self, request: Request) -> Response:
        """Trigger update on all datasets."""
        req_id = request.headers.get("x-request-id")
        try:
            res = self.catalog.update_all_datasets()
            resp = ApiResponse.success(
                data=res, message="Updates started.", request_id=req_id
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError, OSError) as exc:
            return self._error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "UPDATE_FAILED", str(exc), req_id
            )

    def update_selected_datasets(
        self, request: Request, payload: UpdateSelectedPayload
    ) -> Response:
        """Trigger update on selected datasets."""
        req_id = request.headers.get("x-request-id")
        try:
            res = self.catalog.update_selected_datasets(payload.dataset_ids)
            resp = ApiResponse.success(
                data=res, message="Updates started.", request_id=req_id
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError, OSError) as exc:
            return self._error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "UPDATE_FAILED", str(exc), req_id
            )

    def list_csv_formats(self, request: Request) -> Response:
        """List all canonical and custom CSV export format profiles."""
        req_id = request.headers.get("x-request-id")
        page = self.csv_formats_repo.list(limit=100)
        custom_formats = [f.model_dump(mode="json") for f in page.items]
        combined = list(CANONICAL_CSV_FORMATS) + custom_formats
        resp = ApiResponse.success(
            data={"formats": combined, "canonical": CANONICAL_CSV_FORMATS},
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def save_csv_format(self, request: Request, payload: CsvFormatProfile) -> Response:
        """Save or update custom CSV export format profile."""
        req_id = request.headers.get("x-request-id")
        self.csv_formats_repo.save(payload.name, payload)
        resp = ApiResponse.success(
            data=payload.model_dump(mode="json"),
            message=f"Format '{payload.name}' saved.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def delete_csv_format(self, request: Request, name: str = "") -> Response:
        """Delete custom CSV format profile."""
        req_id = request.headers.get("x-request-id")
        target_name = name
        if not target_name:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    target_name = str(body.get("name", ""))
            except ValueError, TypeError, UnicodeDecodeError:
                target_name = ""
        if not target_name:
            target_name = request.query_params.get("name", "")
        deleted = self.csv_formats_repo.delete(target_name)
        if not deleted:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "FORMAT_NOT_FOUND",
                f"Format '{target_name}' not found.",
                req_id,
            )
        resp = ApiResponse.success(
            data={"name": target_name, "deleted": True},
            message=f"Format '{target_name}' deleted.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    # Instruments
    def list_instruments(
        self,
        request: Request,
        connection: str | None = None,
        data_type: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Response:
        """List instruments."""
        req_id = request.headers.get("x-request-id")
        instruments = self.instruments.list_instruments(
            connection=connection, data_type=data_type, limit=limit, offset=offset
        )
        logger.debug(
            "FR-DATA-INTEGRATION-INSTRUMENTS: Listed %d instruments",
            len(instruments),
            extra={
                "fr_id": "FR-DATA-INTEGRATION-INSTRUMENTS",
                "count": len(instruments),
            },
        )
        resp = ApiResponse.success(
            data=[inst.model_dump(mode="json") for inst in instruments],
            message=f"Retrieved {len(instruments)} instrument(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_instrument(self, request: Request, symbol: str) -> Response:
        """Get instrument by symbol."""
        req_id = request.headers.get("x-request-id")
        inst = self.instruments.get_instrument(symbol)
        if inst is None:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "INSTRUMENT_NOT_FOUND",
                f"Instrument '{symbol}' not found",
                req_id,
            )
        logger.debug(
            "FR-DATA-INTEGRATION-INSTRUMENTS: Retrieved instrument '%s'",
            symbol,
            extra={"fr_id": "FR-DATA-INTEGRATION-INSTRUMENTS", "symbol": symbol},
        )
        resp = ApiResponse.success(
            data=inst.model_dump(mode="json"),
            message="Instrument retrieved successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def create_instrument(
        self, request: Request, instrument: InstrumentDefinition
    ) -> Response:
        """Create instrument definition."""
        req_id = request.headers.get("x-request-id")
        try:
            inst_id = self.instruments.create_instrument(instrument)
            self._emit_event(
                "data.instrument", "created", instrument.model_dump(mode="json")
            )
            logger.info(
                "FR-DATA-INTEGRATION-INSTRUMENTS: Created instrument '%s' (id=%d)",
                instrument.symbol,
                inst_id,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-INSTRUMENTS",
                    "symbol": instrument.symbol,
                    "id": inst_id,
                },
            )
            resp = ApiResponse.success(
                data={"id": inst_id, "symbol": instrument.symbol},
                message=f"Instrument '{instrument.symbol}' created successfully",
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-INSTRUMENTS: Error creating instrument %s",
                instrument.symbol,
                extra={"fr_id": "FR-DATA-INTEGRATION-INSTRUMENTS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "INSTRUMENT_ERROR",
                f"Failed to create instrument: {exc}",
                req_id,
            )

    def update_instrument(
        self, request: Request, symbol: str, updates: dict[str, Any]
    ) -> Response:
        """Update instrument definition."""
        req_id = request.headers.get("x-request-id")
        updated = self.instruments.update_instrument(symbol, updates)
        if not updated:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "INSTRUMENT_NOT_FOUND",
                f"Instrument '{symbol}' not found",
                req_id,
            )
        self._emit_event(
            "data.instrument", "updated", {"symbol": symbol, "updates": updates}
        )
        logger.info(
            "FR-DATA-INTEGRATION-INSTRUMENTS: Updated instrument '%s'",
            symbol,
            extra={"fr_id": "FR-DATA-INTEGRATION-INSTRUMENTS", "symbol": symbol},
        )
        resp = ApiResponse.success(
            data={"updated": True, "symbol": symbol},
            message=f"Instrument '{symbol}' updated successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def delete_instrument(self, request: Request, symbol: str) -> Response:
        """Delete instrument definition."""
        req_id = request.headers.get("x-request-id")
        deleted = self.instruments.delete_instrument(symbol)
        if not deleted:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "INSTRUMENT_NOT_FOUND",
                f"Instrument '{symbol}' not found",
                req_id,
            )
        self._emit_event("data.instrument", "deleted", {"symbol": symbol})
        logger.info(
            "FR-DATA-INTEGRATION-INSTRUMENTS: Deleted instrument '%s'",
            symbol,
            extra={"fr_id": "FR-DATA-INTEGRATION-INSTRUMENTS", "symbol": symbol},
        )
        resp = ApiResponse.success(
            data={"deleted": True, "symbol": symbol},
            message=f"Instrument '{symbol}' deleted successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    # Sessions
    def list_sessions(
        self,
        request: Request,
        limit: int = 1000,
        offset: int = 0,
        broker_id: int | None = None,
        search: str | None = None,
    ) -> Response:
        """List sessions with optional broker and search filters."""
        req_id = request.headers.get("x-request-id")
        sessions = self.sessions.list_sessions(
            limit=limit, offset=offset, broker_id=broker_id, search=search
        )
        logger.debug(
            "FR-DATA-INTEGRATION-SESSIONS: Listed %d sessions",
            len(sessions),
            extra={"fr_id": "FR-DATA-INTEGRATION-SESSIONS", "count": len(sessions)},
        )
        resp = ApiResponse.success(
            data=[s.model_dump(mode="json") for s in sessions],
            message=f"Retrieved {len(sessions)} session(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_session(self, request: Request, name: str) -> Response:
        """Get session by name."""
        req_id = request.headers.get("x-request-id")
        sess = self.sessions.get_session(name)
        if sess is None:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "SESSION_NOT_FOUND",
                f"Session '{name}' not found",
                req_id,
            )
        logger.debug(
            "FR-DATA-INTEGRATION-SESSIONS: Retrieved session '%s'",
            name,
            extra={"fr_id": "FR-DATA-INTEGRATION-SESSIONS", "session": name},
        )
        resp = ApiResponse.success(
            data=sess.model_dump(mode="json"),
            message="Session retrieved successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def create_session(
        self, request: Request, session_def: TradingSessionDefinition
    ) -> Response:
        """Create session definition."""
        req_id = request.headers.get("x-request-id")
        try:
            sess_id = self.sessions.save_session(session_def)
            self._emit_event(
                "data.session", "created", session_def.model_dump(mode="json")
            )
            logger.info(
                "FR-DATA-INTEGRATION-SESSIONS: Saved session '%s' (id=%d)",
                session_def.name,
                sess_id,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-SESSIONS",
                    "session": session_def.name,
                    "id": sess_id,
                },
            )
            resp = ApiResponse.success(
                data={"id": sess_id, "name": session_def.name},
                message=f"Session '{session_def.name}' created successfully",
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except ValueError as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-SESSIONS: Error creating session %s",
                session_def.name,
                extra={"fr_id": "FR-DATA-INTEGRATION-SESSIONS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "SESSION_ERROR",
                f"Failed to create session: {exc}",
                req_id,
            )

    def delete_session(self, request: Request, name: str) -> Response:
        """Delete session definition."""
        req_id = request.headers.get("x-request-id")
        deleted = self.sessions.delete_session(name)
        if not deleted:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "SESSION_NOT_FOUND",
                f"Session '{name}' not found",
                req_id,
            )
        self._emit_event("data.session", "deleted", {"name": name})
        logger.info(
            "FR-DATA-INTEGRATION-SESSIONS: Deleted session '%s'",
            name,
            extra={"fr_id": "FR-DATA-INTEGRATION-SESSIONS", "session": name},
        )
        resp = ApiResponse.success(
            data={"deleted": True, "name": name},
            message=f"Session '{name}' deleted successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def clone_session(self, request: Request, payload: SessionClonePayload) -> Response:
        """Clone an existing session definition."""
        req_id = request.headers.get("x-request-id")
        try:
            cloned = self.sessions.clone_session(
                source_name=payload.source_name,
                new_name=payload.new_name,
                broker_id=payload.broker_id,
                broker_postfix=payload.broker_postfix,
            )
            self._emit_event("data.session", "cloned", cloned.model_dump(mode="json"))
            resp = ApiResponse.success(
                data=cloned.model_dump(mode="json"),
                message=f"Session '{cloned.name}' cloned successfully",
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except ValueError as exc:
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "SESSION_CLONE_ERROR",
                str(exc),
                req_id,
            )

    def mass_delete_sessions(
        self, request: Request, payload: SessionMassDeletePayload
    ) -> Response:
        """Delete multiple sessions in one batch."""
        req_id = request.headers.get("x-request-id")
        deleted_count = self.sessions.delete_sessions(payload.names)
        self._emit_event(
            "data.session",
            "mass_deleted",
            {"count": deleted_count, "names": payload.names},
        )
        resp = ApiResponse.success(
            data={"deleted_count": deleted_count},
            message=f"Deleted {deleted_count} session(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def list_nt_templates(
        self, request: Request, folder_path: str | None = None
    ) -> Response:
        """List NinjaTrader 8 TradingHours templates on disk."""
        req_id = request.headers.get("x-request-id")
        info = self.sessions.list_ninjatrader_templates(folder_path=folder_path)
        resp = ApiResponse.success(
            data=info,
            message="NinjaTrader templates listed",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def import_nt_sessions(
        self, request: Request, payload: SessionImportNTPayload
    ) -> Response:
        """Import NinjaTrader XML sessions."""
        req_id = request.headers.get("x-request-id")
        source = payload.folder_path or (payload.xml_content or "")
        if not source.strip():
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "SESSION_IMPORT_ERROR",
                "Either xml_content or folder_path must be provided",
                req_id,
            )
        try:
            result = self.sessions.import_ninjatrader_full(
                source, policy=payload.conflict_policy
            )
            self._emit_event(
                "data.session", "imported", {"count": len(result["imported"])}
            )
            resp = ApiResponse.success(
                data=result,
                message=result["success"],
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except (ValueError, OSError) as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-SESSIONS: NT XML import failed",
                extra={"fr_id": "FR-DATA-INTEGRATION-SESSIONS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "SESSION_IMPORT_ERROR",
                f"Failed to import NinjaTrader sessions: {exc}",
                req_id,
            )

    def export_sqx_xml(self, _request: Request, names: str | None = None) -> Response:
        """Export session definitions as StrategyQuant X Sessions.xml."""
        name_list: list[str] = []
        if names:
            name_list = [n.strip() for n in names.split(",") if n.strip()]
        else:
            name_list = [s.name for s in self.sessions.list_sessions()]
        xml_content = self.sessions.export_sqx_xml(name_list)
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": 'attachment; filename="Sessions.xml"'},
        )

    def export_sqx_xml_post(
        self, _request: Request, payload: SessionExportXmlPayload
    ) -> Response:
        """Export session definitions as StrategyQuant X Sessions.xml via POST."""
        name_list = payload.names or [s.name for s in self.sessions.list_sessions()]
        xml_content = self.sessions.export_sqx_xml(name_list)
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": 'attachment; filename="Sessions.xml"'},
        )

    def import_sqx_xml(
        self, request: Request, payload: SessionImportXmlPayload
    ) -> Response:
        """Import session definitions from StrategyQuant X Sessions.xml."""
        req_id = request.headers.get("x-request-id")
        try:
            imported, skipped = self.sessions.import_sqx_xml(
                payload.xml_content, policy=payload.policy
            )
            self._emit_event(
                "data.session",
                "xml_imported",
                {"imported": len(imported), "skipped": len(skipped)},
            )
            resp = ApiResponse.success(
                data={
                    "imported": [s.model_dump(mode="json") for s in imported],
                    "skipped": skipped,
                },
                message=f"Imported {len(imported)} session(s), skipped {len(skipped)}",
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except (ValueError, OSError) as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-SESSIONS: SQX XML import failed",
                extra={"fr_id": "FR-DATA-INTEGRATION-SESSIONS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "SESSION_XML_IMPORT_ERROR",
                f"Failed to import SQX sessions XML: {exc}",
                req_id,
            )

    # Baskets
    def list_baskets(self, request: Request) -> Response:
        """List baskets."""
        req_id = request.headers.get("x-request-id")
        baskets = self.baskets.list_baskets()
        logger.debug(
            "FR-DATA-INTEGRATION-BASKETS: Listed %d baskets",
            len(baskets),
            extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "count": len(baskets)},
        )
        resp = ApiResponse.success(
            data=[b.model_dump(mode="json") for b in baskets],
            message=f"Retrieved {len(baskets)} basket(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_basket(self, request: Request, name: str) -> Response:
        """Get basket by name."""
        req_id = request.headers.get("x-request-id")
        basket = self.baskets.get_basket(name)
        if basket is None:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "BASKET_NOT_FOUND",
                f"Basket '{name}' not found",
                req_id,
            )
        logger.debug(
            "FR-DATA-INTEGRATION-BASKETS: Retrieved basket '%s'",
            name,
            extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "basket_name": name},
        )
        resp = ApiResponse.success(
            data=basket.model_dump(mode="json"),
            message="Basket retrieved successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def create_basket(self, request: Request, basket: BasketDefinition) -> Response:
        """Create basket definition."""
        req_id = request.headers.get("x-request-id")
        try:
            basket_id = self.baskets.save_basket(basket)
            self._emit_event("data.basket", "created", basket.model_dump(mode="json"))
            logger.info(
                "FR-DATA-INTEGRATION-BASKETS: Saved basket '%s' (id=%d)",
                basket.name,
                basket_id,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-BASKETS",
                    "basket_name": basket.name,
                    "id": basket_id,
                },
            )
            resp = ApiResponse.success(
                data={"id": basket_id, "name": basket.name},
                message=f"Basket '{basket.name}' saved successfully",
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-BASKETS: Failed to save basket %s",
                basket.name,
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "BASKET_ERROR",
                f"Failed to save basket: {exc}",
                req_id,
            )

    def delete_basket(self, request: Request, name: str) -> Response:
        """Delete basket definition."""
        req_id = request.headers.get("x-request-id")
        deleted = self.baskets.delete_basket(name)
        if not deleted:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "BASKET_NOT_FOUND",
                f"Basket '{name}' not found",
                req_id,
            )
        self._emit_event("data.basket", "deleted", {"name": name})
        logger.info(
            "FR-DATA-INTEGRATION-BASKETS: Deleted basket '%s'",
            name,
            extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "basket_name": name},
        )
        resp = ApiResponse.success(
            data={"deleted": True, "name": name},
            message=f"Basket '{name}' deleted successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def compute_basket(
        self, request: Request, payload: BasketComputePayload
    ) -> Response:
        """Compute synthetic basket series."""
        req_id = request.headers.get("x-request-id")
        try:
            bars = self.baskets.compute_basket_series(
                basket=payload.basket,
                series_dict=payload.series,
                policy=payload.alignment_mode,
            )
            logger.info(
                "FR-DATA-INTEGRATION-BASKETS: Computed %d bars for basket '%s'",
                len(bars),
                payload.basket.name,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-BASKETS",
                    "basket": payload.basket.name,
                    "count": len(bars),
                },
            )
            resp = ApiResponse.success(
                data=[b.model_dump(mode="json") for b in bars],
                message=f"Computed {len(bars)} synthetic bar(s)",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-BASKETS: Basket calculation failed",
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "BASKET_COMPUTE_ERROR",
                f"Failed to compute basket series: {exc}",
                req_id,
            )

    def import_basket_csv(
        self, request: Request, payload: BasketCsvImportPayload
    ) -> Response:
        """Import constituents from CSV into an existing stock group."""
        req_id = request.headers.get("x-request-id")
        try:
            updated = self.baskets.import_stocks_from_csv(
                payload.basket_name, payload.csv_text
            )
            self._emit_event("data.basket", "updated", updated.model_dump(mode="json"))
            logger.info(
                "FR-DATA-INTEGRATION-BASKETS: Imported CSV into basket '%s'",
                payload.basket_name,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-BASKETS",
                    "basket_name": payload.basket_name,
                    "items": len(updated.items),
                },
            )
            resp = ApiResponse.success(
                data=updated.model_dump(mode="json"),
                message=(
                    f"Imported {len(updated.items)} stocks into basket "
                    f"'{payload.basket_name}'"
                ),
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-BASKETS: Failed to import CSV into basket %s",
                payload.basket_name,
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "BASKET_CSV_IMPORT_ERROR",
                f"Failed to import CSV: {exc}",
                req_id,
            )

    def export_basket_csv(self, request: Request, name: str) -> Response:
        """Export constituent list of a basket to CSV text."""
        req_id = request.headers.get("x-request-id")
        try:
            csv_text = self.baskets.export_stocks_to_csv(name)
            logger.info(
                "FR-DATA-INTEGRATION-BASKETS: Exported basket '%s' to CSV",
                name,
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "basket_name": name},
            )
            if "application/json" in request.headers.get("accept", ""):
                resp = ApiResponse.success(
                    data={"basket_name": name, "content": csv_text},
                    message=f"Exported stocks for basket '{name}'",
                    request_id=req_id,
                )
                return JSONResponse(
                    status_code=status.HTTP_200_OK, content=resp.to_dict()
                )
            return PlainTextResponse(content=csv_text, media_type="text/csv")
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-BASKETS: Failed to export basket %s to CSV",
                name,
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "BASKET_NOT_FOUND",
                f"Failed to export basket: {exc}",
                req_id,
            )

    def import_basket_xml(
        self, request: Request, payload: BasketXmlImportPayload
    ) -> Response:
        """Import baskets from canonical SQX XML format."""
        req_id = request.headers.get("x-request-id")
        try:
            imported = import_groups_xml(payload.xml_content)
            saved: list[dict[str, Any]] = []
            for b in imported:
                b_id = self.baskets.save_basket(b, override_system=payload.overwrite)
                saved.append({"id": b_id, "name": b.name, "items": len(b.items)})
            logger.info(
                "FR-DATA-INTEGRATION-BASKETS: Imported %d baskets from XML",
                len(saved),
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "count": len(saved)},
            )
            resp = ApiResponse.success(
                data=saved,
                message=f"Imported {len(saved)} basket(s) from XML",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-BASKETS: Failed to import baskets from XML",
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "BASKET_XML_IMPORT_ERROR",
                f"Failed to import XML: {exc}",
                req_id,
            )

    def export_basket_xml(
        self, request: Request, payload: BasketXmlExportPayload | None = None
    ) -> Response:
        """Export specified or all baskets to SQX XML format."""
        req_id = request.headers.get("x-request-id")
        try:
            if payload is not None and payload.basket_names:
                baskets = [
                    b
                    for name in payload.basket_names
                    if (b := self.baskets.get_basket(name)) is not None
                ]
            else:
                baskets = self.baskets.list_baskets()
            xml_text = export_groups_xml(baskets)
            logger.info(
                "FR-DATA-INTEGRATION-BASKETS: Exported %d baskets to XML",
                len(baskets),
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "count": len(baskets)},
            )
            if "application/json" in request.headers.get("accept", ""):
                resp = ApiResponse.success(
                    data={"xml_content": xml_text},
                    message=f"Exported {len(baskets)} basket(s) to XML",
                    request_id=req_id,
                )
                return JSONResponse(
                    status_code=status.HTTP_200_OK, content=resp.to_dict()
                )
            return Response(
                content=xml_text,
                media_type="application/xml",
                headers={
                    "Content-Disposition": 'attachment; filename="Groups.xml"',
                    "x-request-id": req_id or "",
                },
            )
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-BASKETS: Failed to export baskets to XML",
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "BASKET_XML_EXPORT_ERROR",
                f"Failed to export XML: {exc}",
                req_id,
            )

    def check_basket_readiness(self, request: Request, name: str) -> Response:
        """Evaluate data readiness diagnostics for a stock group."""
        req_id = request.headers.get("x-request-id")
        basket = self.baskets.get_basket(name)
        if basket is None:
            return self._error_response(
                status.HTTP_404_NOT_FOUND,
                "BASKET_NOT_FOUND",
                f"Basket '{name}' not found",
                req_id,
            )
        available_symbols = {d.symbol for d in self.catalog.list_datasets()}
        readiness = self.baskets.check_readiness(basket, available_symbols)
        logger.info(
            "FR-DATA-INTEGRATION-BASKETS: Evaluated readiness for basket '%s'",
            name,
            extra={
                "fr_id": "FR-DATA-INTEGRATION-BASKETS",
                "basket_name": name,
                "is_ready": readiness.is_ready,
            },
        )
        resp = ApiResponse.success(
            data=readiness.model_dump(mode="json"),
            message="Basket readiness evaluated successfully",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def list_baskets_overview(self, request: Request) -> Response:
        """List enriched overview rows matching the 8-column SQX table grid."""
        req_id = request.headers.get("x-request-id")
        overview = self.baskets.list_baskets_overview()
        logger.info(
            "FR-DATA-INTEGRATION-BASKETS: Listed %d basket overview rows",
            len(overview),
            extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "count": len(overview)},
        )
        resp = ApiResponse.success(
            data=[row.model_dump(mode="json") for row in overview],
            message=f"Retrieved {len(overview)} basket overview row(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def update_basket_data(
        self, request: Request, payload: BasketUpdateDataPayload
    ) -> Response:
        """Trigger automatic background data update for symbols in group(s)."""
        req_id = request.headers.get("x-request-id")
        try:
            ids_input = payload.basket_ids
            id_list: list[str | int]
            if isinstance(ids_input, list):
                id_list = list(ids_input)
            elif isinstance(ids_input, str):
                id_list = [i.strip() for i in ids_input.split(",") if i.strip()]
            else:
                id_list = [ids_input]

            results: list[dict[str, Any]] = []
            for bid in id_list:
                res = self.baskets.update_group_data(bid)
                results.append(res)

            logger.info(
                "FR-DATA-INTEGRATION-BASKETS: Initiated data update for %d basket(s)",
                len(results),
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "count": len(results)},
            )
            resp = ApiResponse.success(
                data=results,
                message=(
                    "Data update started, please check Log tab for more information."
                ),
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-BASKETS: Failed to initiate basket data update",
                extra={"fr_id": "FR-DATA-INTEGRATION-BASKETS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "BASKET_UPDATE_ERROR",
                str(exc),
                req_id,
            )

    # Providers
    def list_providers(self, request: Request) -> Response:
        """List provider capabilities."""
        req_id = request.headers.get("x-request-id")
        providers = [c.model_dump() for c in self.providers.list_capabilities()]
        logger.debug(
            "FR-DATA-INTEGRATION-PROVIDERS: Listed %d providers",
            len(providers),
            extra={"fr_id": "FR-DATA-INTEGRATION-PROVIDERS", "count": len(providers)},
        )
        resp = ApiResponse.success(
            data=providers,
            message=f"Retrieved {len(providers)} provider(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def download_provider_data(
        self, request: Request, payload: ProviderDownloadPayload
    ) -> Response:
        """Download provider data."""
        req_id = request.headers.get("x-request-id")
        try:
            req = DownloadRequest(
                provider_name=payload.provider,
                symbol=payload.symbol,
                timeframe=payload.timeframe,
                date_from=payload.date_from,
                date_to=payload.date_to,
            )
            if payload.async_job and self.job_manager is not None:
                future = self.job_manager.submit(
                    "data_manager",
                    _execute_async_download,
                    payload.provider,
                    payload.symbol,
                    payload.timeframe,
                    payload.date_from,
                    payload.date_to,
                    kind="provider_download",
                )
                job_id = self.job_manager.get_job_id_for_future(future) or ""

                def _on_download_done(fut: Future[Any]) -> None:
                    exc = fut.exception()
                    if exc is not None:
                        logger.warning(
                            "FR-DATA-INTEGRATION-PROVIDERS: Download failed: %s",
                            exc,
                        )
                        return
                    res = fut.result()
                    self._emit_event("data.provider", "downloaded", res)

                future.add_done_callback(_on_download_done)

                resp = ApiResponse.success(
                    data={
                        "job_id": job_id,
                        "status": "pending",
                        "provider": payload.provider,
                        "symbol": payload.symbol,
                    },
                    message=(f"Download submitted as background job '{job_id}'"),
                    request_id=req_id,
                )
                return JSONResponse(
                    status_code=status.HTTP_202_ACCEPTED, content=resp.to_dict()
                )

            bars = self.providers.download(req)
            if bars:
                self.catalog.save_bars(
                    source=payload.provider,
                    symbol=payload.symbol,
                    timeframe=payload.timeframe or "M1",
                    bars=bars,
                )
            self._emit_event(
                "data.provider",
                "downloaded",
                {
                    "provider": payload.provider,
                    "symbol": payload.symbol,
                    "bars_count": len(bars),
                },
            )
            logger.info(
                "FR-DATA-INTEGRATION-PROVIDERS: Downloaded %d bars from %s",
                len(bars),
                payload.provider,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-PROVIDERS",
                    "provider": payload.provider,
                    "symbol": payload.symbol,
                    "count": len(bars),
                },
            )
            res_data: dict[str, Any] = {
                "provider": payload.provider,
                "symbol": payload.symbol,
                "bars_count": len(bars),
                "bars": [b.model_dump(mode="json") for b in bars],
            }
            resp = ApiResponse.success(
                data=res_data,
                message=f"Downloaded {len(bars)} bar(s) from {payload.provider}",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-PROVIDERS: Download failed for provider %s",
                payload.provider,
                extra={"fr_id": "FR-DATA-INTEGRATION-PROVIDERS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "PROVIDER_DOWNLOAD_ERROR",
                f"Provider download failed: {exc}",
                req_id,
            )

    # COT
    def list_cot_mappings(self, request: Request) -> Response:
        """List COT mappings."""
        req_id = request.headers.get("x-request-id")
        mappings = self.cot.list_mappings()
        logger.debug(
            "FR-DATA-INTEGRATION-COT: Listed %d COT mappings",
            len(mappings),
            extra={"fr_id": "FR-DATA-INTEGRATION-COT", "count": len(mappings)},
        )
        resp = ApiResponse.success(
            data=[m.model_dump(mode="json") for m in mappings],
            message=f"Retrieved {len(mappings)} COT mapping(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_cot_symbol(self, request: Request, symbol: str) -> Response:
        """Get COT symbol observations."""
        req_id = request.headers.get("x-request-id")
        obs = self.cot.get_cot_data(symbol)
        logger.debug(
            "FR-DATA-INTEGRATION-COT: Retrieved %d COT observations for '%s'",
            len(obs),
            symbol,
            extra={
                "fr_id": "FR-DATA-INTEGRATION-COT",
                "symbol": symbol,
                "count": len(obs),
            },
        )
        resp = ApiResponse.success(
            data=[o.model_dump(mode="json") for o in obs],
            message=f"Retrieved {len(obs)} COT observation(s) for '{symbol}'",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def update_cot_symbol(
        self, request: Request, symbol: str, payload: CotUpdatePayload
    ) -> Response:
        """Update COT observations."""
        req_id = request.headers.get("x-request-id")
        try:
            if payload.reports:
                obs = self.cot.calculate_indices(
                    payload.reports, lookback_weeks=payload.lookback_weeks
                )
                self.cot.save_cot_data(symbol, obs)
            else:
                self.cot.update_cftc_reports(symbol)
                obs = self.cot.get_cot_data(symbol)

            logger.info(
                "FR-DATA-INTEGRATION-COT: Updated %d COT observations for '%s'",
                len(obs),
                symbol,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-COT",
                    "symbol": symbol,
                    "count": len(obs),
                },
            )
            resp = ApiResponse.success(
                data=[o.model_dump(mode="json") for o in obs],
                message=f"Updated {len(obs)} COT observation(s) for '{symbol}'",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-COT: Failed to update COT observations",
                extra={"fr_id": "FR-DATA-INTEGRATION-COT", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "COT_UPDATE_ERROR",
                f"Failed to update COT observations: {exc}",
                req_id,
            )

    # Quality
    def audit_data_quality(
        self, request: Request, payload: QualityAuditPayload
    ) -> Response:
        """Audit data quality."""
        req_id = request.headers.get("x-request-id")
        try:
            interval_map = {
                "M1": 60,
                "M5": 300,
                "M15": 900,
                "M30": 1800,
                "H1": 3600,
                "H4": 14400,
                "D1": 86400,
            }
            interval_secs = interval_map.get(payload.timeframe.upper(), 60)
            report = self.quality.inspect_series(
                bars=payload.bars,
                expected_interval_seconds=interval_secs,
            )
            logger.info(
                "FR-DATA-INTEGRATION-QUALITY: Audited %d bars (score=%.4f)",
                len(payload.bars),
                report.quality_score,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-QUALITY",
                    "score": report.quality_score,
                    "valid_bars": report.valid_bars,
                },
            )
            resp = ApiResponse.success(
                data=report.model_dump(mode="json"),
                message="Data quality audit completed successfully",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-QUALITY: Quality audit failed",
                extra={"fr_id": "FR-DATA-INTEGRATION-QUALITY", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "QUALITY_AUDIT_ERROR",
                f"Quality audit failed: {exc}",
                req_id,
            )

    # Transforms & Export
    def resample_timeframe(
        self, request: Request, payload: ResamplePayload
    ) -> Response:
        """Resample M1 bars."""
        req_id = request.headers.get("x-request-id")
        try:
            resampled = self.transformer.resample(
                bars=payload.bars,
                target_timeframe=payload.target_timeframe,
            )
            logger.info(
                "FR-DATA-INTEGRATION-TRANSFORMS: Resampled %d M1 bars into %d %s bars",
                len(payload.bars),
                len(resampled),
                payload.target_timeframe,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-TRANSFORMS",
                    "target": payload.target_timeframe,
                    "output_count": len(resampled),
                },
            )
            resp = ApiResponse.success(
                data=[b.model_dump(mode="json") for b in resampled],
                message=(
                    f"Resampled into {len(resampled)} {payload.target_timeframe} bar(s)"
                ),
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-TRANSFORMS: Resampling failed",
                extra={"fr_id": "FR-DATA-INTEGRATION-TRANSFORMS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "RESAMPLE_ERROR",
                f"Resampling failed: {exc}",
                req_id,
            )

    def _resolve_csv_tokens(
        self, payload: ExportPayload
    ) -> tuple[list[str], str, bool]:
        """Resolve items, delimiter, and header from format profile or custom fields."""
        if payload.items:
            return payload.items, payload.delimiter, payload.include_header
        if payload.format_name:
            for c in CANONICAL_CSV_FORMATS:
                if c["name"] == payload.format_name:
                    return list(c["items"]), str(c["delimiter"]), bool(c["header"])
            saved = self.csv_formats_repo.get(payload.format_name)
            if saved:
                hdr_bool = (
                    saved.header
                    if isinstance(saved.header, bool)
                    else bool(saved.header)
                )
                return saved.items, saved.delimiter, hdr_bool
        return (
            [
                "[date:yyyyMMdd]",
                "[time:HHmmss]",
                "[open]",
                "[high]",
                "[low]",
                "[close]",
                "[volume]",
            ],
            payload.delimiter,
            payload.include_header,
        )

    def _execute_export(
        self,
        fmt: str,
        bars: list[BarRecord],
        payload: ExportPayload,
        out_file: Path,
    ) -> Path:
        """Route to appropriate SeriesTransformer export function."""
        if fmt in ("mt4_hst", "mt4_binary"):
            period = TIMEFRAME_MINUTES.get(payload.timeframe.upper(), 1)
            out_path = self.transformer.export_mt4_binary(
                bars=bars,
                output_path=out_file,
                symbol=payload.symbol,
                period=period,
                digits=payload.digits,
            )
        elif fmt in ("mt4_fxt", "fxt"):
            out_path = self.transformer.export_mt4_fxt_binary(
                bars=bars,
                symbol=payload.symbol,
                timeframe=payload.timeframe,
                digits=payload.digits,
                spread=payload.spread,
                output_path=out_file,
            )
        elif fmt == "mt5" and (
            payload.real_spread or payload.spread != DEFAULT_EXPORT_SPREAD
        ):
            out_path = self.transformer.export_mt5_advanced(
                bars=bars,
                symbol=payload.symbol,
                real_spread=payload.real_spread,
                fixed_spread=payload.spread,
                output_path=out_file,
            )
        elif fmt in ("custom", "csv") and (payload.items or payload.format_name):
            items, delimiter, header = self._resolve_csv_tokens(payload)
            out_path = self.transformer.export_csv_custom(
                bars=bars,
                symbol=payload.symbol,
                items=items,
                delimiter=delimiter,
                include_header=header,
                output_path=out_file,
            )
        elif fmt == "mt4":
            out_path = self.transformer.export_mt4(bars=bars, output_path=out_file)
        elif fmt == "mt5":
            out_path = self.transformer.export_mt5(bars=bars, output_path=out_file)
        else:
            out_path = self.transformer.export_csv(bars=bars, output_path=out_file)
        return out_path

    def export_series(self, request: Request, payload: ExportPayload) -> Response:
        """Export series with support for tokens, MT4 binary, and MT5 advanced."""
        req_id = request.headers.get("x-request-id")
        try:
            bars = list(payload.bars)
            if not bars and payload.dataset_id:
                ds = self.catalog.get_dataset(payload.dataset_id)
                if ds:
                    bars = self.catalog.storage.read_bars_slice(
                        source=ds.source,
                        symbol=ds.symbol,
                        timeframe=ds.timeframe,
                        limit=ds.bars or 1000000,
                    )
            fmt = payload.format.lower()
            ext = (
                "fxt"
                if fmt in ("mt4_fxt", "fxt")
                else ("hst" if fmt in ("mt4_hst", "mt4_binary") else fmt)
            )
            out_file = (
                Path(payload.output_path)
                if payload.output_path
                else self.res_dir
                / "exports"
                / f"{payload.symbol}_{payload.timeframe}.{ext}"
            )
            out_path = self._execute_export(
                fmt=fmt,
                bars=bars,
                payload=payload,
                out_file=out_file,
            )

            if fmt in ("mt4_hst", "mt4_binary", "mt4_fxt", "fxt"):
                file_bytes = out_path.read_bytes()
                file_content = f"<binary {len(file_bytes)} bytes>"
                line_count = len(bars)
            else:
                file_content = out_path.read_text(encoding="utf-8")
                line_count = len(file_content.splitlines())

            logger.info(
                "FR-DATA-INTEGRATION-TRANSFORMS: Exported %d bars as %s",
                len(bars),
                fmt,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-TRANSFORMS",
                    "format": fmt,
                    "bars_count": len(bars),
                },
            )
            resp = ApiResponse.success(
                data={
                    "format": fmt,
                    "symbol": payload.symbol,
                    "timeframe": payload.timeframe,
                    "output_path": str(out_path),
                    "content": file_content,
                    "line_count": line_count,
                },
                message=f"Exported {len(bars)} bars as {fmt.upper()}",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except Exception as exc:
            logger.exception(
                "FR-DATA-INTEGRATION-TRANSFORMS: Export failed",
                extra={"fr_id": "FR-DATA-INTEGRATION-TRANSFORMS", "error": str(exc)},
            )
            return self._error_response(
                status.HTTP_400_BAD_REQUEST,
                "EXPORT_ERROR",
                f"Export failed: {exc}",
                req_id,
            )

    # Home overview
    def get_home_overview(self, request: Request) -> Response:
        """Get Data Manager workspace overview summary."""
        req_id = request.headers.get("x-request-id")
        active_providers = len(self.providers.list_capabilities())
        overview = self.home.get_overview(active_providers_count=active_providers)
        resp = ApiResponse.success(
            data=overview.model_dump(mode="json"),
            message="Workspace overview retrieved",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_home_doc_links(self, request: Request) -> Response:
        """Get documentation and tutorial links mirroring SQX DataManagerHome."""
        req_id = request.headers.get("x-request-id")
        links = [
            {
                "id": "import-mt4",
                "title": "Import History Data MT4",
                "description": "Learn how to import historical data to MetaTrader 4",
                "icon": "download",
                "url": "https://strategyquant.com/doc/quantdatamanager/import-history-data-metatrader-4/",
            },
            {
                "id": "test-mt4",
                "title": "Test Strategy MT4",
                "description": "Test your strategy in MT4 with tick precision",
                "icon": "speed",
                "url": "https://strategyquant.com/doc/quantdatamanager/test-strategy-metatrader-4-tick-precision/",
            },
            {
                "id": "import-mt5",
                "title": "Import Data to MT5",
                "description": "How to import data to MetaTrader 5",
                "icon": "input",
                "url": "https://strategyquant.com/doc/quantdatamanager/how-to-import-data-to-metatrader-5/",
            },
            {
                "id": "export-mt5",
                "title": "Export Data from MT5",
                "description": "How to export data from MetaTrader 5",
                "icon": "output",
                "url": "https://strategyquant.com/doc/quantdatamanager/how-to-export-data-from-metatrader-5/",
            },
            {
                "id": "intro-cli",
                "title": "Introduction to CLI",
                "description": "What is CLI and how to use it",
                "icon": "terminal",
                "url": "https://strategyquant.com/doc/cli-command-line/introduction-to-cli/",
            },
            {
                "id": "full-doc",
                "title": "Full Documentation",
                "description": "Browse complete QDM documentation",
                "icon": "menu_book",
                "url": "https://strategyquant.com/doc/quantdatamanager/",
            },
        ]
        resp = ApiResponse.success(
            data=links,
            message="Documentation links retrieved",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    # Broker profiles
    def list_brokers(self, request: Request) -> Response:
        """List configured broker profiles."""
        req_id = request.headers.get("x-request-id")
        brokers = self.broker.list_brokers()
        resp = ApiResponse.success(
            data=[b.model_dump(mode="json") for b in brokers],
            message=f"Retrieved {len(brokers)} broker profile(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def save_broker(self, request: Request, payload: BrokerSavePayload) -> Response:
        """Create or update a broker profile."""
        req_id = request.headers.get("x-request-id")
        try:
            if payload.id is not None:
                record = self.broker.update_broker(payload.id, payload)
                msg = f"Broker profile '{record.name}' updated"
            else:
                record = self.broker.create_broker(payload)
                msg = f"Broker profile '{record.name}' created"
            self._emit_event(
                channel="data_manager",
                event_type="BROKERS_CHANGED",
                payload={"broker_id": record.id, "action": "save"},
            )
            resp = ApiResponse.success(
                data=record.model_dump(mode="json"),
                message=msg,
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="BROKER_SAVE_FAILED",
                message=str(exc),
                request_id=req_id,
            )

    def get_broker_by_id(self, request: Request, broker_id: int) -> Response:
        """Get a single broker profile by ID."""
        req_id = request.headers.get("x-request-id")
        rec = self.broker.get_broker(broker_id)
        if rec is None:
            return self._error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                code="BROKER_NOT_FOUND",
                message=f"Broker profile '{broker_id}' not found",
                request_id=req_id,
            )
        resp = ApiResponse.success(
            data=rec.model_dump(mode="json"),
            message=f"Retrieved broker profile '{rec.name}'",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def update_broker_by_id(
        self, request: Request, broker_id: int, payload: BrokerSavePayload
    ) -> Response:
        """Update a broker profile by URL id."""
        payload.id = broker_id
        return self.save_broker(request, payload)

    def delete_brokers(
        self, request: Request, payload: BrokerDeleteRequest
    ) -> Response:
        """Delete multiple broker profiles."""
        req_id = request.headers.get("x-request-id")
        try:
            count = self.broker.delete_brokers(payload.broker_ids)
            self._emit_event(
                channel="data_manager",
                event_type="BROKERS_CHANGED",
                payload={"deleted_ids": payload.broker_ids, "count": count},
            )
            resp = ApiResponse.success(
                data={"deleted_count": count},
                message=f"Deleted {count} broker profile(s)",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="BROKER_DELETE_FAILED",
                message=str(exc),
                request_id=req_id,
            )

    def list_broker_stocks(self, request: Request, broker_id: int) -> Response:
        """List configured stocks for a broker profile."""
        req_id = request.headers.get("x-request-id")
        try:
            stocks = self.broker.list_stocks(broker_id)
            resp = ApiResponse.success(
                data={"broker_id": broker_id, "stocks": stocks},
                message=f"Retrieved {len(stocks)} stock(s) for broker ID {broker_id}",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                code="BROKER_NOT_FOUND",
                message=str(exc),
                request_id=req_id,
            )

    def edit_broker_stocks(
        self, request: Request, broker_id: int, payload: BrokerStocksPayload
    ) -> Response:
        """Replace configured stocks for a broker profile."""
        req_id = request.headers.get("x-request-id")
        try:
            self.broker.edit_stocks(broker_id, payload.stocks)
            self._emit_event(
                channel="data_manager",
                event_type="BROKERS_CHANGED",
                payload={"broker_id": broker_id, "action": "edit_stocks"},
            )
            resp = ApiResponse.success(
                data={"broker_id": broker_id, "count": len(payload.stocks)},
                message=f"Updated stocks for broker ID {broker_id}",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="BROKER_STOCKS_FAILED",
                message=str(exc),
                request_id=req_id,
            )

    def import_broker_stocks(
        self, request: Request, broker_id: int, payload: BrokerImportStocksRequest
    ) -> Response:
        """Import stocks from plain multi-line CSV/text."""
        req_id = request.headers.get("x-request-id")
        try:
            count = self.broker.import_stocks_csv(broker_id, payload.content)
            self._emit_event(
                channel="data_manager",
                event_type="BROKERS_CHANGED",
                payload={"broker_id": broker_id, "action": "import_stocks"},
            )
            resp = ApiResponse.success(
                data={"broker_id": broker_id, "count": count},
                message=f"Imported {count} stock(s) for broker ID {broker_id}",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="BROKER_STOCK_IMPORT_FAILED",
                message=str(exc),
                request_id=req_id,
            )

    def export_broker_stocks(self, request: Request, broker_id: int) -> Response:
        """Export configured stocks for a broker profile as plain text."""
        req_id = request.headers.get("x-request-id")
        try:
            content = self.broker.export_stocks_csv(broker_id)
            if "application/json" in request.headers.get("accept", ""):
                resp = ApiResponse.success(
                    data={"broker_id": broker_id, "content": content},
                    message="Exported broker stocks",
                    request_id=req_id,
                )
                return JSONResponse(
                    status_code=status.HTTP_200_OK, content=resp.to_dict()
                )
            return PlainTextResponse(
                content=content,
                media_type="text/plain",
                headers={
                    "Content-Disposition": (
                        f'attachment; filename="broker_{broker_id}_stocks.csv"'
                    ),
                    "x-request-id": req_id or "",
                },
            )
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                code="BROKER_NOT_FOUND",
                message=str(exc),
                request_id=req_id,
            )

    def export_brokers_xml(
        self, request: Request, payload: BrokerXmlExportRequest
    ) -> Response:
        """Export broker profiles to StrategyQuant X XML format."""
        req_id = request.headers.get("x-request-id")
        xml_content = self.broker.export_brokers_xml(payload.broker_ids)
        if "application/json" in request.headers.get("accept", ""):
            resp = ApiResponse.success(
                data={"xml_content": xml_content},
                message="Exported broker profiles to XML",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": 'attachment; filename="Brokers.xml"',
                "x-request-id": req_id or "",
            },
        )

    def import_brokers_xml(
        self, request: Request, payload: BrokerXmlImportRequest
    ) -> Response:
        """Import broker profiles from StrategyQuant X XML format."""
        req_id = request.headers.get("x-request-id")
        try:
            imported = self.broker.import_brokers_xml(payload.xml_content)
            self._emit_event(
                channel="data_manager",
                event_type="BROKERS_CHANGED",
                payload={"action": "import_xml", "count": len(imported)},
            )
            resp = ApiResponse.success(
                data=[b.model_dump(mode="json") for b in imported],
                message=f"Imported {len(imported)} broker profile(s) from XML",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="BROKER_XML_IMPORT_FAILED",
                message=str(exc),
                request_id=req_id,
            )

    def inspect_xml_overview(
        self, request: Request, payload: BrokerXmlOverviewRequest
    ) -> Response:
        """Inspect MetaTrader XML export overview."""
        req_id = request.headers.get("x-request-id")
        try:
            items = self.broker.inspect_xml_overview(payload.xml_content, payload.kind)
            resp = ApiResponse.success(
                data=[item.model_dump(mode="json") for item in items],
                message=f"Parsed {len(items)} {payload.kind}(s) from XML",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="XML_INSPECTION_FAILED",
                message=str(exc),
                request_id=req_id,
            )

    def import_xml_records(
        self, request: Request, payload: BrokerXmlImportRecordsRequest
    ) -> Response:
        """Import selected instruments or sessions from MetaTrader XML."""
        req_id = request.headers.get("x-request-id")
        try:
            count = self.broker.import_xml_records(
                payload.xml_content,
                payload.kind,
                payload.broker_id,
                payload.postfix,
                payload.selected_names,
            )
            event_type = (
                "INSTRUMENTS_CHANGED"
                if payload.kind == "instrument"
                else "SESSIONS_CHANGED"
            )
            self._emit_event(
                channel="data_manager",
                event_type=event_type,
                payload={"broker_id": payload.broker_id, "count": count},
            )
            resp = ApiResponse.success(
                data={"imported_count": count},
                message=(
                    f"Imported {count} {payload.kind}(s) for broker ID "
                    f"{payload.broker_id}"
                ),
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="XML_IMPORT_FAILED",
                message=str(exc),
                request_id=req_id,
            )

    def update_broker_data(self, request: Request, broker_id: int) -> Response:
        """Trigger historical data update for a broker profile."""
        req_id = request.headers.get("x-request-id")
        try:
            res = self.broker.update_data_for_broker(broker_id)
            resp = ApiResponse.success(
                data=res,
                message=res.get("message", "Data update initiated"),
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except (ValueError, KeyError, RuntimeError) as exc:
            return self._error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="BROKER_UPDATE_DATA_FAILED",
                message=str(exc),
                request_id=req_id,
            )

    # Logs
    def list_logs(
        self,
        request: Request,
        symbol: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> Response:
        """List activity logs."""
        req_id = request.headers.get("x-request-id")
        logs = self.log.list_logs(symbol=symbol, action=action, limit=limit)
        resp = ApiResponse.success(
            data=[entry.model_dump(mode="json") for entry in logs],
            message=f"Retrieved {len(logs)} log entry/entries",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    # Help topics
    def list_help_topics(self, request: Request) -> Response:
        """List help guide topics."""
        req_id = request.headers.get("x-request-id")
        topics = self.help.list_topics()
        resp = ApiResponse.success(
            data=[t.model_dump(mode="json") for t in topics],
            message=f"Retrieved {len(topics)} help topic(s)",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


# ---------------------------------------------------------------------------
# Route Registration Helpers
# ---------------------------------------------------------------------------


def _register_dataset_routes(router: APIRouter, service: DataRouterService) -> None:
    """Register all dataset manipulation and inspection routes."""
    router.add_api_route(
        "/datasets", service.list_datasets, methods=["GET"], summary="List datasets"
    )
    router.add_api_route(
        "/datasets/{dataset_id}",
        service.get_dataset,
        methods=["GET"],
        summary="Get dataset",
    )
    router.add_api_route(
        "/datasets/{dataset_id}",
        service.delete_dataset,
        methods=["DELETE"],
        summary="Delete dataset",
    )
    router.add_api_route(
        "/datasets/{dataset_id}/delete",
        service.delete_dataset,
        methods=["POST"],
        summary="Delete dataset (POST alias)",
    )
    router.add_api_route(
        "/datasets/{dataset_id}",
        service.edit_dataset,
        methods=["PUT"],
        summary="Edit dataset",
    )
    router.add_api_route(
        "/datasets/{dataset_id}/clear",
        service.clear_dataset_data,
        methods=["POST"],
        summary="Clear dataset data",
    )
    router.add_api_route(
        "/datasets/review-chart",
        service.review_chart,
        methods=["POST"],
        summary="Review chart bars slice",
    )
    router.add_api_route(
        "/datasets/clone-timezone",
        service.clone_to_timezone,
        methods=["POST"],
        summary="Clone dataset to timezone",
    )
    router.add_api_route(
        "/datasets/{dataset_id}/review-data",
        service.review_data,
        methods=["GET"],
        summary="Review paginated bar records",
    )
    router.add_api_route(
        "/datasets/{dataset_id}/index-for-date",
        service.get_index_for_date,
        methods=["GET"],
        summary="Get bar index for date",
    )
    router.add_api_route(
        "/datasets/{dataset_id}/save-changes",
        service.save_data_changes,
        methods=["POST"],
        summary="Save bar cell changes or row deletions",
    )
    router.add_api_route(
        "/datasets/{dataset_id}/quality-summary",
        service.quality_summary,
        methods=["GET"],
        summary="Data quality defect summary",
    )
    router.add_api_route(
        "/datasets/{dataset_id}/quality-details",
        service.quality_details,
        methods=["GET"],
        summary="Data quality defect details",
    )
    router.add_api_route(
        "/datasets/mass-delete",
        service.mass_delete,
        methods=["POST"],
        summary="Mass delete or clear datasets",
    )
    router.add_api_route(
        "/datasets/export-xml",
        service.export_catalog_xml,
        methods=["POST"],
        summary="Export datasets and brokers to SQX <Data> XML",
    )
    router.add_api_route(
        "/datasets/import-xml",
        service.import_catalog_xml,
        methods=["POST"],
        summary="Import datasets and brokers from SQX <Data> XML",
    )
    router.add_api_route(
        "/datasets/update-all",
        service.update_all_datasets,
        methods=["POST"],
        summary="Update all online datasets",
    )
    router.add_api_route(
        "/datasets/update-selected",
        service.update_selected_datasets,
        methods=["POST"],
        summary="Update selected online datasets",
    )
    # Direct SQX RPC path aliases
    router.add_api_route(
        "/reviewData",
        service.review_data,
        methods=["GET"],
        summary="Review paginated bar records (SQX alias)",
    )
    router.add_api_route(
        "/getIndexForDate",
        service.get_index_for_date,
        methods=["GET"],
        summary="Get bar index for date (SQX alias)",
    )
    router.add_api_route(
        "/saveDataChanges",
        service.save_data_changes,
        methods=["POST"],
        summary="Save bar cell changes (SQX alias)",
    )
    router.add_api_route(
        "/checkQualitySummary",
        service.quality_summary,
        methods=["GET"],
        summary="Quality summary (SQX alias)",
    )
    router.add_api_route(
        "/checkQualityDetails",
        service.quality_details,
        methods=["GET"],
        summary="Quality details (SQX alias)",
    )
    router.add_api_route(
        "/cloneToTimezone",
        service.clone_to_timezone,
        methods=["POST"],
        summary="Clone dataset to timezone (SQX alias)",
    )
    router.add_api_route(
        "/updateAll",
        service.update_all_datasets,
        methods=["POST"],
        summary="Update all datasets (SQX alias)",
    )
    router.add_api_route(
        "/updateSelected",
        service.update_selected_datasets,
        methods=["POST"],
        summary="Update selected datasets (SQX alias)",
    )
    router.add_api_route(
        "/save",
        service.export_catalog_xml,
        methods=["POST"],
        summary="Export catalog XML (SQX alias)",
    )
    router.add_api_route(
        "/load",
        service.import_catalog_xml,
        methods=["POST"],
        summary="Import catalog XML (SQX alias)",
    )
    router.add_api_route(
        "/datasets/{symbol}/{timeframe}/availability",
        service.check_availability,
        methods=["GET"],
        summary="Check availability",
    )
    router.add_api_route(
        "/datasets/import",
        service.import_dataset,
        methods=["POST"],
        summary="Import dataset",
    )


def _register_instrument_session_routes(
    router: APIRouter, service: DataRouterService
) -> None:
    """Register instrument and trading session template routes."""
    router.add_api_route(
        "/instruments",
        service.list_instruments,
        methods=["GET"],
        summary="List instruments",
    )
    router.add_api_route(
        "/instruments/{symbol}",
        service.get_instrument,
        methods=["GET"],
        summary="Get instrument",
    )
    router.add_api_route(
        "/instruments",
        service.create_instrument,
        methods=["POST"],
        summary="Create instrument",
    )
    router.add_api_route(
        "/instruments/{symbol}",
        service.update_instrument,
        methods=["PUT"],
        summary="Update instrument",
    )
    router.add_api_route(
        "/instruments/{symbol}",
        service.delete_instrument,
        methods=["DELETE"],
        summary="Delete instrument",
    )
    router.add_api_route(
        "/sessions",
        service.list_sessions,
        methods=["GET"],
        summary="List sessions",
    )
    router.add_api_route(
        "/sessions",
        service.create_session,
        methods=["POST"],
        summary="Create session",
    )
    router.add_api_route(
        "/sessions/clone",
        service.clone_session,
        methods=["POST"],
        summary="Clone session",
    )
    router.add_api_route(
        "/sessions/mass-delete",
        service.mass_delete_sessions,
        methods=["POST"],
        summary="Mass delete sessions",
    )
    router.add_api_route(
        "/sessions/nt-templates",
        service.list_nt_templates,
        methods=["GET"],
        summary="List NinjaTrader templates",
    )
    router.add_api_route(
        "/sessions/import-nt",
        service.import_nt_sessions,
        methods=["POST"],
        summary="Import NinjaTrader sessions",
    )
    router.add_api_route(
        "/sessions/export-xml",
        service.export_sqx_xml,
        methods=["GET"],
        summary="Export SQX sessions XML (GET)",
        name="sessions_export_xml_get",
    )
    router.add_api_route(
        "/sessions/export-xml",
        service.export_sqx_xml_post,
        methods=["POST"],
        summary="Export SQX sessions XML (POST)",
        name="sessions_export_xml_post",
    )
    router.add_api_route(
        "/sessions/import-xml",
        service.import_sqx_xml,
        methods=["POST"],
        summary="Import SQX sessions XML",
    )
    router.add_api_route(
        "/sessions/{name}",
        service.get_session,
        methods=["GET"],
        summary="Get session",
    )
    router.add_api_route(
        "/sessions/{name}",
        service.delete_session,
        methods=["DELETE"],
        summary="Delete session",
    )


def _register_basket_provider_routes(
    router: APIRouter, service: DataRouterService
) -> None:
    """Register basket, provider, and COT routes."""
    router.add_api_route(
        "/baskets",
        service.list_baskets,
        methods=["GET"],
        summary="List baskets",
    )
    router.add_api_route(
        "/baskets",
        service.create_basket,
        methods=["POST"],
        summary="Create basket",
    )
    router.add_api_route(
        "/baskets/overview",
        service.list_baskets_overview,
        methods=["GET"],
        summary="List stock groups overview with SQX readiness and metrics",
    )
    router.add_api_route(
        "/baskets/update-data",
        service.update_basket_data,
        methods=["POST"],
        summary="Trigger automatic historical data update for basket group(s)",
    )
    router.add_api_route(
        "/baskets/compute",
        service.compute_basket,
        methods=["POST"],
        summary="Compute synthetic basket",
    )
    router.add_api_route(
        "/baskets/import-csv",
        service.import_basket_csv,
        methods=["POST"],
        summary="Import basket constituents from CSV",
    )
    router.add_api_route(
        "/baskets/import-xml",
        service.import_basket_xml,
        methods=["POST"],
        summary="Import baskets from SQX XML",
    )
    router.add_api_route(
        "/baskets/export-xml",
        service.export_basket_xml,
        methods=["GET"],
        summary="Export baskets to SQX XML",
        name="export_basket_xml_get",
    )
    router.add_api_route(
        "/baskets/export-xml",
        service.export_basket_xml,
        methods=["POST"],
        summary="Export baskets to SQX XML",
        name="export_basket_xml_post",
    )
    router.add_api_route(
        "/basketOfStocks/list",
        service.list_baskets_overview,
        methods=["GET"],
        summary="List stock groups overview (SQX alias)",
        name="basket_of_stocks_list_get",
    )
    router.add_api_route(
        "/basketOfStocks/list",
        service.list_baskets_overview,
        methods=["POST"],
        summary="List stock groups overview (SQX alias)",
        name="basket_of_stocks_list_post",
    )
    router.add_api_route(
        "/basketOfStocks/updateData",
        service.update_basket_data,
        methods=["POST"],
        summary="Update stock group data (SQX alias)",
        name="basket_of_stocks_update_data_post",
    )
    router.add_api_route(
        "/basketOfStocks/saveXml",
        service.export_basket_xml,
        methods=["GET"],
        summary="Save stock groups XML (SQX alias)",
        name="basket_of_stocks_save_xml_get",
    )
    router.add_api_route(
        "/basketOfStocks/saveXml",
        service.export_basket_xml,
        methods=["POST"],
        summary="Save stock groups XML (SQX alias)",
        name="basket_of_stocks_save_xml_post",
    )
    router.add_api_route(
        "/basketOfStocks/loadXml",
        service.import_basket_xml,
        methods=["POST"],
        summary="Load stock groups XML (SQX alias)",
        name="basket_of_stocks_load_xml_post",
    )
    router.add_api_route(
        "/baskets/{name}",
        service.get_basket,
        methods=["GET"],
        summary="Get basket",
    )
    router.add_api_route(
        "/baskets/{name}",
        service.delete_basket,
        methods=["DELETE"],
        summary="Delete basket",
    )
    router.add_api_route(
        "/baskets/{name}/export-csv",
        service.export_basket_csv,
        methods=["GET"],
        summary="Export basket constituents to CSV",
    )
    router.add_api_route(
        "/baskets/{name}/readiness",
        service.check_basket_readiness,
        methods=["GET"],
        summary="Check basket data download readiness",
    )
    router.add_api_route(
        "/providers",
        service.list_providers,
        methods=["GET"],
        summary="List providers",
    )
    router.add_api_route(
        "/providers/download",
        service.download_provider_data,
        methods=["POST"],
        summary="Download provider data",
    )
    router.add_api_route(
        "/cot/mappings",
        service.list_cot_mappings,
        methods=["GET"],
        summary="List COT mappings",
    )
    router.add_api_route(
        "/cot/{symbol}",
        service.get_cot_symbol,
        methods=["GET"],
        summary="Get COT observations",
    )
    router.add_api_route(
        "/cot/{symbol}/update",
        service.update_cot_symbol,
        methods=["POST"],
        summary="Update COT observations",
    )


def _register_export_home_routes(router: APIRouter, service: DataRouterService) -> None:
    """Register export, quality, home, broker, and log routes."""
    router.add_api_route(
        "/quality/audit",
        service.audit_data_quality,
        methods=["POST"],
        summary="Audit data quality",
    )
    router.add_api_route(
        "/transforms/resample",
        service.resample_timeframe,
        methods=["POST"],
        summary="Resample M1 bars",
    )
    router.add_api_route(
        "/export",
        service.export_series,
        methods=["POST"],
        summary="Export bar series",
    )
    router.add_api_route(
        "/export/csv/formats",
        service.list_csv_formats,
        methods=["GET"],
        summary="List CSV export format profiles",
    )
    router.add_api_route(
        "/export/csv/formats",
        service.save_csv_format,
        methods=["POST"],
        summary="Save CSV export format profile",
    )
    router.add_api_route(
        "/export/csv/formats/{name}",
        service.delete_csv_format,
        methods=["DELETE"],
        summary="Delete CSV export format profile",
    )
    router.add_api_route(
        "/exportToCsvLoadSettings",
        service.list_csv_formats,
        methods=["GET"],
        summary="Export to CSV load settings (SQX alias)",
        name="export_to_csv_load_settings_get",
    )
    router.add_api_route(
        "/exportToCsvLoadSettings",
        service.list_csv_formats,
        methods=["POST"],
        summary="Export to CSV load settings (SQX alias)",
        name="export_to_csv_load_settings_post",
    )
    router.add_api_route(
        "/exportToCsvSaveFileFormat",
        service.save_csv_format,
        methods=["POST"],
        summary="Save CSV format (SQX alias)",
        name="export_to_csv_save_file_format_post",
    )
    router.add_api_route(
        "/exportToCsvSaveAsFileFormat",
        service.save_csv_format,
        methods=["POST"],
        summary="Save As CSV format (SQX alias)",
        name="export_to_csv_save_as_file_format_post",
    )
    router.add_api_route(
        "/exportToCsvDeleteFileFormat",
        service.delete_csv_format,
        methods=["POST"],
        summary="Delete CSV format (SQX alias)",
        name="export_to_csv_delete_file_format_post",
    )
    router.add_api_route(
        "/export/csv/formats/delete",
        service.delete_csv_format,
        methods=["POST"],
        summary="Delete CSV format (POST)",
        name="export_csv_formats_delete_post",
    )
    router.add_api_route(
        "/exportToCsvAction",
        service.export_series,
        methods=["POST"],
        summary="Export to CSV action (SQX alias)",
    )
    router.add_api_route(
        "/exportToMT4Action",
        service.export_series,
        methods=["POST"],
        summary="Export to MT4 action (SQX alias)",
    )
    router.add_api_route(
        "/exportToMT5Action",
        service.export_series,
        methods=["POST"],
        summary="Export to MT5 action (SQX alias)",
    )
    router.add_api_route(
        "/home/overview",
        service.get_home_overview,
        methods=["GET"],
        summary="Get workspace overview",
    )
    router.add_api_route(
        "/home/doc-links",
        service.get_home_doc_links,
        methods=["GET"],
        summary="Get home documentation links",
    )
    router.add_api_route(
        "/brokers",
        service.list_brokers,
        methods=["GET"],
        summary="List broker profiles",
    )
    router.add_api_route(
        "/brokers",
        service.save_broker,
        methods=["POST"],
        summary="Create or update a broker profile",
    )
    router.add_api_route(
        "/brokers/{broker_id}",
        service.get_broker_by_id,
        methods=["GET"],
        summary="Get broker profile by ID",
    )
    router.add_api_route(
        "/brokers/{broker_id}",
        service.update_broker_by_id,
        methods=["PUT"],
        summary="Update broker profile by ID",
    )
    router.add_api_route(
        "/brokers",
        service.delete_brokers,
        methods=["DELETE"],
        summary="Delete broker profiles",
    )
    router.add_api_route(
        "/brokers/delete",
        service.delete_brokers,
        methods=["POST"],
        summary="Delete broker profiles (POST alias)",
    )
    router.add_api_route(
        "/brokers/{broker_id}/stocks",
        service.list_broker_stocks,
        methods=["GET"],
        summary="List broker stocks",
    )
    router.add_api_route(
        "/brokers/{broker_id}/stocks",
        service.edit_broker_stocks,
        methods=["PUT"],
        summary="Edit broker stocks",
    )
    router.add_api_route(
        "/brokers/{broker_id}/stocks/import",
        service.import_broker_stocks,
        methods=["POST"],
        summary="Import broker stocks from CSV text",
    )
    router.add_api_route(
        "/brokers/{broker_id}/stocks/export",
        service.export_broker_stocks,
        methods=["GET"],
        summary="Export broker stocks to CSV",
    )
    router.add_api_route(
        "/brokers/save-xml",
        service.export_brokers_xml,
        methods=["POST"],
        summary="Export broker profiles to XML",
    )
    router.add_api_route(
        "/brokers/load-xml",
        service.import_brokers_xml,
        methods=["POST"],
        summary="Import broker profiles from XML",
    )
    router.add_api_route(
        "/brokers/import-get-overview",
        service.inspect_xml_overview,
        methods=["POST"],
        summary="Inspect MetaTrader XML overview",
    )
    router.add_api_route(
        "/brokers/import-session-instrument",
        service.import_xml_records,
        methods=["POST"],
        summary="Import instruments or sessions from MetaTrader XML",
    )
    router.add_api_route(
        "/brokers/{broker_id}/update-data",
        service.update_broker_data,
        methods=["POST"],
        summary="Trigger historical data update for a broker profile",
    )
    router.add_api_route(
        "/logs",
        service.list_logs,
        methods=["GET"],
        summary="List activity logs",
    )
    router.add_api_route(
        "/help/topics",
        service.list_help_topics,
        methods=["GET"],
        summary="List help topics",
    )


def create_data_router(
    db_manager: DatabaseManager | None = None,
    resource_manager: ResourceManager | None = None,
    *,
    job_manager: JobManager | None = None,
    event_bus: EventBus | None = None,
    provider_manager: ProviderManager | None = None,
) -> APIRouter:
    """Create and configure FastAPI APIRouter for Market Data workspace.

    Args:
        db_manager: Central host DatabaseManager instance.
        resource_manager: Central host ResourceManager instance.
        job_manager: Optional host JobManager instance for background compute jobs.
        event_bus: Optional host EventBus instance for real-time notification streaming.
        provider_manager: Optional host-discovered ProviderManager instance.

    Returns:
        Configured FastAPI APIRouter.
    """
    db = db_manager or get_database_manager()
    res_dir = (
        resource_manager.root_dir
        if resource_manager is not None
        else Path("data/resources")
    )

    service = DataRouterService(
        db,
        res_dir,
        job_manager=job_manager,
        event_bus=event_bus,
        provider_manager=provider_manager,
    )
    router = APIRouter(prefix="/data", tags=["Market Data"])
    _register_dataset_routes(router, service)
    _register_instrument_session_routes(router, service)
    _register_basket_provider_routes(router, service)
    _register_export_home_routes(router, service)
    return router


# Alias for SQX naming conventions
create_data_manager_router = create_data_router


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for inspecting market data endpoints."""
    parser = argparse.ArgumentParser(description="Market Data REST Router Inspection")
    parser.add_argument(
        "--list-routes", action="store_true", help="Print all registered API routes"
    )
    args = parser.parse_args(argv)

    router = create_data_router()
    if args.list_routes:
        print(f"Market Data Router (prefix='{router.prefix}'):")
        for route in router.routes:
            methods = getattr(route, "methods", {"*"})
            path = getattr(route, "path", "")
            print(f"  {', '.join(sorted(methods)):<8} {path}")
    else:
        print(f"Market Data Router initialized with {len(router.routes)} routes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

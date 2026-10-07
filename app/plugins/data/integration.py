"""Market data REST router, API contracts, and unified host integration.

Description:
    This module provides the central FastAPI REST router for the market data
    subsystem (`app.plugins.data`). It exposes clean, strongly-typed endpoints
    for dataset cataloging, instrument lifecycle, trading session definitions,
    data ingestion, quality auditing, timeframe transformations, provider
    downloads, synthetic baskets, and CFTC Commitments of Traders (COT) series.
    It links the frontend DataManager workspace with authoritative host persistence.

Purpose:
    FEAT-DATA-INTEGRATION: Expose unified market data via REST endpoints.

Key Capabilities:
    - FR-DATA-INTEGRATION-DATASETS: REST endpoints for dataset listing, querying,
      deletion, availability checks, and ingestion.
      Associated: `get_datasets`, `get_dataset`, `delete_dataset`,
        `check_dataset_availability`, `import_dataset`
      Logging: Emits INFO on dataset mutations and ingestion completion;
        emits DEBUG on listings.
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
    from app.plugins.data.integration import create_data_router

    db = DatabaseManager()
    db.initialize()
    router = create_data_router(db)
    ```

CLI Usage:
    ```bash
    uv run python -m app.plugins.data.integration --help
    ```
"""

from __future__ import annotations

import argparse
import sys
import uuid
from concurrent.futures import Future
from pathlib import Path
from typing import Any

from app.host.jobs import JobManager
from app.host.logging import get_logger
from app.host.persistence import DatabaseManager, get_database_manager
from app.host.resources import ResourceManager
from app.host.response import StandardError
from app.host.transport import ApiResponse, EventBus
from app.plugins.data.baskets import BasketDefinition, BasketService
from app.plugins.data.catalog import CatalogService
from app.plugins.data.cot import CotService
from app.plugins.data.custom_data import CustomDataService
from app.plugins.data.ingestion import (
    BarRecord,
    DataIngestionService,
    IngestionConfig,
)
from app.plugins.data.instruments import InstrumentDefinition, InstrumentService
from app.plugins.data.providers import DownloadRequest, ProviderManager
from app.plugins.data.quality import DataQualityInspector
from app.plugins.data.sessions import SessionService, TradingSessionDefinition
from app.plugins.data.transforms import SeriesTransformer
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

logger = get_logger(__name__)


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
    from app.host.persistence import DatabaseManager
    from app.plugins.data.catalog import CatalogService
    from app.plugins.data.ingestion import (
        DataIngestionService,
        IngestionConfig,
    )

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
    from app.plugins.data.providers import DownloadRequest, ProviderManager

    manager = ProviderManager()
    req = DownloadRequest(
        provider_name=provider_name,
        symbol=symbol,
        timeframe=timeframe,
        date_from=date_from,
        date_to=date_to,
    )
    bars = manager.download(req)
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

    xml_content: str = Field(..., min_length=1, description="Raw NT XML content")
    conflict_policy: str = Field(
        default="overwrite", description="'overwrite' or 'skip'"
    )


class BasketComputePayload(BaseModel):
    """Payload for calculating synthetic composite basket series."""

    model_config = ConfigDict(extra="forbid")

    basket: BasketDefinition
    series: dict[str, list[BarRecord]]
    alignment_mode: str = Field(
        default="intersection", description="'intersection' or 'union'"
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

    bars: list[BarRecord] = Field(..., description="Source bars to export")
    format: str = Field(default="csv", description="'csv', 'mt4', or 'mt5'")
    symbol: str = Field(default="EURUSD", description="Symbol identifier")
    timeframe: str = Field(default="M1", description="Timeframe identifier")
    digits: int = Field(default=5, ge=0, le=8, description="Price decimals")
    output_path: str | None = Field(default=None, description="Optional output path")


# ---------------------------------------------------------------------------
# Router Handler Service
# ---------------------------------------------------------------------------


class DataRouterService:
    """Service container encapsulating market data route handlers."""

    def __init__(
        self,
        db: DatabaseManager,
        res_dir: Path,
        *,
        job_manager: JobManager | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize all backing domain services."""
        self.db = db
        self.res_dir = res_dir
        self.job_manager = job_manager
        self.event_bus = event_bus
        self.catalog = CatalogService(db)
        self.instruments = InstrumentService(db)
        self.sessions = SessionService(db)
        self.baskets = BasketService(db)
        self.ingestion = DataIngestionService(
            catalog=self.catalog, storage_dir=res_dir / "datasets"
        )
        self.quality = DataQualityInspector()
        self.transformer = SeriesTransformer()
        self.providers = ProviderManager()
        self.custom_data = CustomDataService(db=db, storage_dir=res_dir / "custom_data")
        self.cot = CotService(db=db, storage_dir=res_dir / "cot")

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
        self, request: Request, limit: int = 1000, offset: int = 0
    ) -> Response:
        """List sessions."""
        req_id = request.headers.get("x-request-id")
        sessions = self.sessions.list_sessions(limit=limit, offset=offset)
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
        except Exception as exc:
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

    def import_nt_sessions(
        self, request: Request, payload: SessionImportNTPayload
    ) -> Response:
        """Import NinjaTrader XML sessions."""
        req_id = request.headers.get("x-request-id")
        try:
            imported = self.sessions.import_ninjatrader_xml(
                payload.xml_content, policy=payload.conflict_policy
            )
            self._emit_event("data.session", "imported", {"count": len(imported)})
            logger.info(
                "FR-DATA-INTEGRATION-SESSIONS: Imported %d NT session(s)",
                len(imported),
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-SESSIONS",
                    "count": len(imported),
                },
            )
            resp = ApiResponse.success(
                data=[s.model_dump(mode="json") for s in imported],
                message=f"Imported {len(imported)} session(s)",
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, content=resp.to_dict()
            )
        except Exception as exc:
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

    def export_series(self, request: Request, payload: ExportPayload) -> Response:
        """Export series."""
        req_id = request.headers.get("x-request-id")
        try:
            fmt = payload.format.lower()
            out_file = (
                Path(payload.output_path)
                if payload.output_path
                else self.res_dir
                / "exports"
                / f"{payload.symbol}_{payload.timeframe}.{fmt}"
            )
            if fmt == "mt4":
                out_path = self.transformer.export_mt4(
                    bars=payload.bars,
                    output_path=out_file,
                )
            elif fmt == "mt5":
                out_path = self.transformer.export_mt5(
                    bars=payload.bars,
                    output_path=out_file,
                )
            else:
                out_path = self.transformer.export_csv(
                    bars=payload.bars,
                    output_path=out_file,
                )

            file_content = out_path.read_text(encoding="utf-8")
            line_count = len(file_content.splitlines())

            logger.info(
                "FR-DATA-INTEGRATION-TRANSFORMS: Exported %d bars as %s",
                len(payload.bars),
                fmt,
                extra={
                    "fr_id": "FR-DATA-INTEGRATION-TRANSFORMS",
                    "format": fmt,
                    "bars_count": len(payload.bars),
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
                message=f"Exported {len(payload.bars)} bars as {fmt.upper()}",
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


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def create_data_router(
    db_manager: DatabaseManager | None = None,
    resource_manager: ResourceManager | None = None,
    *,
    job_manager: JobManager | None = None,
    event_bus: EventBus | None = None,
) -> APIRouter:
    """Create and configure FastAPI APIRouter for Market Data subsystem.

    Args:
        db_manager: Central host DatabaseManager instance.
        resource_manager: Central host ResourceManager instance.
        job_manager: Optional host JobManager instance for background compute jobs.
        event_bus: Optional host EventBus instance for real-time notification streaming.

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
        db, res_dir, job_manager=job_manager, event_bus=event_bus
    )
    router = APIRouter(prefix="/data", tags=["Market Data"])

    # Datasets
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

    # Instruments
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

    # Sessions
    router.add_api_route(
        "/sessions",
        service.list_sessions,
        methods=["GET"],
        summary="List sessions",
    )
    router.add_api_route(
        "/sessions/{name}",
        service.get_session,
        methods=["GET"],
        summary="Get session",
    )
    router.add_api_route(
        "/sessions",
        service.create_session,
        methods=["POST"],
        summary="Create session",
    )
    router.add_api_route(
        "/sessions/{name}",
        service.delete_session,
        methods=["DELETE"],
        summary="Delete session",
    )
    router.add_api_route(
        "/sessions/import-nt",
        service.import_nt_sessions,
        methods=["POST"],
        summary="Import NinjaTrader sessions",
    )

    # Baskets
    router.add_api_route(
        "/baskets",
        service.list_baskets,
        methods=["GET"],
        summary="List baskets",
    )
    router.add_api_route(
        "/baskets/{name}",
        service.get_basket,
        methods=["GET"],
        summary="Get basket",
    )
    router.add_api_route(
        "/baskets",
        service.create_basket,
        methods=["POST"],
        summary="Create basket",
    )
    router.add_api_route(
        "/baskets/{name}",
        service.delete_basket,
        methods=["DELETE"],
        summary="Delete basket",
    )
    router.add_api_route(
        "/baskets/compute",
        service.compute_basket,
        methods=["POST"],
        summary="Compute synthetic basket",
    )

    # Providers
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

    # COT
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

    # Quality
    router.add_api_route(
        "/quality/audit",
        service.audit_data_quality,
        methods=["POST"],
        summary="Audit data quality",
    )

    # Transforms & Export
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

    return router


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

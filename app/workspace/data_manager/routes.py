"""Unified FastAPI REST router and workspace facade for Data Manager.

Description:
    Provides the central workspace facade (`DataManagerWorkspace`) coordinating
    all 11 Data Manager domain services (`home`, `data`, `instruments`, `sessions`,
    `baskets`, `broker`, `connections`, `custom_data`, `log`, `help`, `quality`,
    `transforms`) and constructs the unified FastAPI `APIRouter` mounted under
    `/data`, `/api/v1/data`, and `/api/v2/data`. Wraps all endpoint responses
    in canonical `StandardResponse` JSON envelopes.

Purpose:
    FEAT-DATAMGR-ROUTES: Unified Data Manager workspace coordinator and REST router.

Key Capabilities:
    - FR-DATAMGR-ROUTES-WORKSPACE-FACADE: Coordinate all 11 Data Manager services.
      Associated: `DataManagerWorkspace`, `DataManagerWorkspace.initialize_defaults()`
      Logging: Emits INFO on workspace initialization and default seeding.
    - FR-DATAMGR-ROUTES-FASTAPI-GATEWAY: Expose authoritative REST endpoints
      under /data.
      Associated: `create_data_manager_router()`
      Logging: Emits INFO on route registration and request dispatch.

Python API Usage:
    ```python
    from app.workspace.data_manager.routes import (
        DataManagerWorkspace,
        create_data_manager_router,
    )

    workspace = DataManagerWorkspace()
    workspace.initialize_defaults()
    router = create_data_manager_router(workspace)
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.routes
    ```
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from app.host.discovery import PluginLifecycleManager
from app.host.logging import get_logger
from app.host.persistence.create import create_schema
from app.host.persistence.read import resolve_connection
from app.host.response import StandardError, StandardResponse
from app.host.session import SessionManager
from app.host.transport import EventBus, extract_bearer_token
from app.services.brokers.capabilities import ProviderError
from app.services.brokers.registry import BrokerRegistry
from app.workspace.data_manager.actions.review.quality import DataQualityInspector
from app.workspace.data_manager.actions.transform.transforms import (
    CloneTimezoneConfig,
    ResampleConfig,
    SeriesTransformer,
)
from app.workspace.data_manager.baskets import BasketsCatalogService
from app.workspace.data_manager.broker import BrokerProfilesService
from app.workspace.data_manager.connections import ProviderConnectionsService
from app.workspace.data_manager.custom_data import CustomDataService
from app.workspace.data_manager.data import DataManagerDataService
from app.workspace.data_manager.help import DataManagerHelpService
from app.workspace.data_manager.home import DataHomeService
from app.workspace.data_manager.instruments import InstrumentsCatalogService
from app.workspace.data_manager.log import DataManagerLogService
from app.workspace.data_manager.sessions import SessionsCatalogService
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

__all__ = [
    "DataManagerWorkspace",
    "create_data_manager_router",
]

logger = get_logger(__name__)

FACADE_FR = "FR-DATAMGR-ROUTES-WORKSPACE-FACADE"
GATEWAY_FR = "FR-DATAMGR-ROUTES-FASTAPI-GATEWAY"


class DataManagerWorkspace:
    """Authoritative workspace facade coordinating all 11 Data Manager domains."""

    def __init__(
        self,
        *,
        db_path: Path | str | None = None,
        data_dir: Path | str | None = None,
        event_bus: EventBus | None = None,
        plugin_mgr: PluginLifecycleManager | None = None,
        broker_registry: BrokerRegistry | None = None,
        job_manager: Any | None = None,
    ) -> None:
        """Instantiate workspace with database path and event broker."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.data_dir = Path(data_dir) if data_dir is not None else Path("data")
        self.event_bus = event_bus
        self.plugin_mgr = plugin_mgr
        self.broker_registry = broker_registry
        self.job_manager = job_manager

        # Initialize all 11 domain services
        self.log = DataManagerLogService(db_path=self.db_path)
        self.data = DataManagerDataService(
            db_path=self.db_path,
            data_dir=self.data_dir,
            log_service=self.log,
        )
        self.instruments = InstrumentsCatalogService(
            db_path=self.db_path,
            log_service=self.log,
        )
        self.sessions = SessionsCatalogService(
            db_path=self.db_path,
            data_dir=self.data_dir,
        )
        self.baskets = BasketsCatalogService(
            db_path=self.db_path,
            data_service=self.data,
        )
        self.broker = BrokerProfilesService(
            db_path=self.db_path,
            instruments_service=self.instruments,
            sessions_service=self.sessions,
            data_service=self.data,
        )
        self.connections = ProviderConnectionsService(
            db_path=self.db_path,
            data_dir=self.data_dir,
            data_service=self.data,
            log_service=self.log,
            event_bus=self.event_bus,
            plugin_mgr=self.plugin_mgr,
            broker_registry=self.broker_registry,
            job_manager=self.job_manager,
        )
        self.custom_data = CustomDataService(
            db_path=self.db_path,
            data_dir=self.data_dir,
        )
        self.help = DataManagerHelpService()
        self.quality = DataQualityInspector(
            db_path=self.db_path,
            data_service=self.data,
        )
        self.transforms = SeriesTransformer(
            data_service=self.data,
            log_service=self.log,
        )
        self.home = DataHomeService(
            active_providers_getter=self.connections.active_providers_count,
        )
        logger.info(
            "%s: Initialized DataManagerWorkspace (db=%s, data_dir=%s)",
            FACADE_FR,
            self.db_path,
            self.data_dir,
            extra={"fr_id": FACADE_FR},
        )

    def initialize_defaults(self) -> dict[str, int]:
        """Seed default canonical brokers, instruments, sessions, and baskets."""
        brokers = self.broker.ensure_default_brokers()
        instruments = self.instruments.ensure_default_instruments()
        sessions = self.sessions.ensure_default_sessions()
        baskets = self.baskets.ensure_default_baskets()

        counts = {
            "brokers": brokers,
            "instruments": instruments,
            "sessions": sessions,
            "baskets": baskets,
        }
        logger.info(
            "%s: Seeded default catalogs: %s",
            FACADE_FR,
            counts,
            extra={"fr_id": FACADE_FR, "seeded": counts},
        )
        return counts


def _success(data: Any, message: str = "Success") -> JSONResponse:
    return JSONResponse(
        content=StandardResponse.success(data=data, message=message).to_dict()
    )


def _error(code: str, message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        content=StandardResponse.failure(
            message=message, error=StandardError(code=code, message=message)
        ).to_dict(),
        status_code=status_code,
    )


def _register_home_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/home/overview")
    def get_home_overview() -> JSONResponse:
        data = ws.home.get_overview().to_dict()
        return _success(data)

    @router.get("/home/datasets")
    def get_home_datasets() -> JSONResponse:
        datasets = [d.to_dict() for d in ws.home.get_saved_datasets()]
        return _success(datasets)


def _register_logs_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/logs")
    def list_logs(
        symbol: str | None = None,
        action: str | None = None,
        limit: int = 200,
    ) -> JSONResponse:
        logs = [e.to_dict() for e in ws.log.list_logs(symbol, action, limit)]
        return _success(logs)

    @router.post("/logs")
    def append_log(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        entry = ws.log.append_log(
            action=str(p.get("action", "INFO")),
            message=str(p.get("message", "")),
            symbol=p.get("symbol"),
            details=p.get("details"),
        )
        return _success(entry.to_dict())

    @router.post("/logs/clear")
    def clear_logs(symbol: str | None = None) -> JSONResponse:
        res = ws.log.clear_logs(symbol=symbol)
        return _success(res)


def _register_export_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/export/csv/formats")
    def list_csv_formats() -> JSONResponse:
        return _success({"formats": ws.data.list_csv_formats()})

    @router.post("/export/csv/formats")
    def save_csv_format(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        res = ws.data.save_csv_format(p)
        return _success(res)

    @router.post("/export/csv/formats/delete")
    def delete_csv_format(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        name = str(p.get("name", ""))
        return _success(ws.data.delete_csv_format(name))

    @router.post("/export")
    def export_data(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        res = ws.data.export_datasets(p)
        return _success(res)


def _register_datasets_crud_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/datasets")
    def list_datasets(
        source: str | None = None,
        symbol: str | None = None,
    ) -> JSONResponse:
        data = [d.to_dict() for d in ws.data.list_datasets(source, symbol)]
        return _success(data)

    @router.post("/datasets")
    def create_dataset(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.data.upsert_dataset(p)
        return _success(rec.to_dict())

    @router.post("/datasets/mass-delete")
    def mass_delete_datasets(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        dids = p.get("dataset_ids") or []
        action = str(p.get("action", "remove"))
        force = bool(p.get("force", False))
        res = ws.data.mass_delete_datasets(dids, action=action, force=force)
        return _success(res)

    @router.post("/datasets/import")
    def import_dataset(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.data.import_dataset(p)
        return _success(rec.to_dict())

    @router.put("/datasets/{dataset_id}")
    def update_dataset(
        dataset_id: str,
        payload: dict[str, Any] | None = None,
    ) -> JSONResponse:
        p = payload or {}
        rec = ws.data.update_dataset(dataset_id, p)
        return _success(rec.to_dict())

    @router.post("/datasets/{dataset_id}/clear")
    def clear_dataset(dataset_id: str) -> JSONResponse:
        res = ws.data.clear_dataset(dataset_id)
        return _success(res)

    @router.post("/datasets/{dataset_id}/delete")
    def delete_dataset_post(dataset_id: str) -> JSONResponse:
        res = ws.data.delete_dataset(dataset_id)
        return _success(res)

    @router.delete("/datasets/{dataset_id}")
    def delete_dataset(dataset_id: str) -> JSONResponse:
        res = ws.data.delete_dataset(dataset_id)
        return _success(res)


def _register_datasets_review_routes(
    router: APIRouter, ws: DataManagerWorkspace
) -> None:
    @router.post("/datasets/review-chart")
    def get_review_chart(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        symbol = str(p.get("symbol", "EURUSD"))
        timeframe = str(p.get("timeframe", "M1"))
        limit = int(p["limit"]) if "limit" in p and p["limit"] is not None else None
        offset = int(p.get("offset", 0))
        max_bars = int(p.get("max_bars", 250))
        dataset_id = p.get("dataset_id")
        bars = ws.data.get_review_chart_bars(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            offset=offset,
            max_bars=max_bars,
            dataset_id=dataset_id,
        )
        return _success({"bars": bars})

    @router.get("/datasets/{dataset_id}/review-data")
    def get_review_rows(
        dataset_id: str,
        limit: int = 500,
        offset: int = 0,
    ) -> JSONResponse:
        rows = ws.data.get_review_rows(dataset_id, limit=limit, offset=offset)
        return _success({"rows": rows})

    @router.post("/datasets/{dataset_id}/save-changes")
    def save_review_changes(
        dataset_id: str,
        payload: dict[str, Any] | None = None,
    ) -> JSONResponse:
        p = payload or {}
        changed = p.get("changed_bars") or []
        deleted = p.get("deleted_timestamps") or []
        res = ws.data.save_review_changes(dataset_id, changed, deleted)
        return _success(res)

    @router.get("/datasets/{dataset_id}/index-for-date")
    def get_index_for_date(
        dataset_id: str,
        target_date: str = "",
    ) -> JSONResponse:
        idx = ws.data.get_index_for_date(dataset_id, target_date)
        return _success({"index": idx})


def _register_datasets_transform_quality_routes(
    router: APIRouter, ws: DataManagerWorkspace
) -> None:
    @router.post("/datasets/clone-timezone")
    def clone_timezone(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        cfg = CloneTimezoneConfig(
            dataset_id=str(p.get("dataset_id", "")),
            timezone_type=str(p.get("timezone_type", "shift")),
            shift_hours=int(p.get("shift_hours", 0)),
            timezone=str(p.get("timezone", "UTC")),
            remove_weekends=bool(p.get("remove_weekends", False)),
            postfix=str(p.get("postfix", "_clone")),
        )
        rec = ws.transforms.clone_timezone(cfg)
        return _success(rec.to_dict())

    @router.post("/datasets/resample")
    def resample_dataset(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        cfg = ResampleConfig(
            dataset_id=str(p.get("dataset_id", "")),
            target_timeframe=str(p.get("target_timeframe", "M5")),
            new_symbol=p.get("new_symbol"),
        )
        rec = ws.transforms.resample_dataset(cfg)
        return _success(rec.to_dict())

    @router.get("/datasets/{dataset_id}/quality-summary")
    def get_quality_summary(dataset_id: str) -> JSONResponse:
        summary = ws.quality.get_quality_summary(dataset_id)
        return _success(summary)

    @router.get("/datasets/{dataset_id}/quality-details")
    def get_quality_details(
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> JSONResponse:
        details = ws.quality.get_quality_details(dataset_id, limit=limit, offset=offset)
        return _success(details)


def _register_instruments_crud_routes(
    router: APIRouter, ws: DataManagerWorkspace
) -> None:
    @router.get("/instruments")
    def list_instruments(
        connection: str | None = None,
        data_type: str | None = None,
        broker_id: int | None = None,
        search: str | None = None,
    ) -> JSONResponse:
        items = [
            i.to_dict()
            for i in ws.instruments.list_instruments(
                connection=connection,
                data_type=data_type,
                broker_id=broker_id,
                search=search,
            )
        ]
        return _success(items)

    @router.post("/instruments")
    def create_instrument(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        inst = ws.instruments.save_instrument(p)
        return _success(inst.to_dict())

    @router.get("/instruments/{symbol}")
    def get_instrument(symbol: str) -> JSONResponse:
        inst = ws.instruments.get_instrument(symbol)
        if inst is None:
            return _error("NOT_FOUND", f"Instrument '{symbol}' not found", 404)
        return _success(inst.to_dict())

    @router.put("/instruments/{symbol}")
    def update_instrument(
        symbol: str, payload: dict[str, Any] | None = None
    ) -> JSONResponse:
        p = payload or {}
        inst = ws.instruments.update_instrument(symbol, p)
        return _success(inst.to_dict())

    @router.delete("/instruments/{symbol}")
    def delete_instrument(symbol: str) -> JSONResponse:
        deleted = ws.instruments.delete_instrument(symbol)
        return _success({"deleted": deleted})

    @router.post("/instruments/mass-edit")
    def mass_edit_instruments(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        symbols = p.get("symbols") or []
        updates = p.get("updates") or {}
        change_flags = p.get("change_flags")
        count = ws.instruments.mass_edit_instruments(symbols, updates, change_flags)
        return _success({"updated_count": count})

    @router.post("/instruments/mass-delete")
    def mass_delete_instruments(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        symbols = p.get("symbols") or []
        res = ws.instruments.mass_delete_instruments(symbols)
        return _success(res)


def _register_instruments_alias_routes(
    router: APIRouter, ws: DataManagerWorkspace
) -> None:
    @router.get("/instruments/aliases")
    def list_aliases() -> JSONResponse:
        aliases = [a.to_dict() for a in ws.instruments.list_aliases()]
        return _success(aliases)

    @router.post("/instruments/aliases")
    def create_alias(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.instruments.save_alias(
            alias=str(p.get("alias", "")),
            instrument=str(p.get("instrument", "")),
            description=str(p.get("description", "")),
        )
        return _success(rec.to_dict())

    @router.put("/instruments/aliases/{alias}")
    def update_alias(alias: str, payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.instruments.save_alias(
            alias=alias,
            instrument=str(p.get("instrument", "")),
            description=str(p.get("description", "")),
        )
        return _success(rec.to_dict())

    @router.delete("/instruments/aliases/{alias}")
    def delete_alias(alias: str) -> JSONResponse:
        removed = ws.instruments.delete_alias(alias)
        return _success({"removed": removed})

    @router.post("/instruments/clone")
    def clone_instrument(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.instruments.clone_instrument(
            symbol=str(p.get("symbol", "")),
            clone_name=str(p.get("clone_name", "")),
            broker_id=int(p.get("broker_id", -1)),
            broker_postfix=str(p.get("broker_postfix", "")),
        )
        return _success(rec.to_dict())

    @router.post("/instruments/save")
    def export_instruments_xml(
        payload: dict[str, Any] | None = None,
    ) -> JSONResponse:
        p = payload or {}
        symbols = p.get("symbols")
        xml_str = ws.instruments.export_xml(symbols)
        return _success({"xml": xml_str})

    @router.post("/instruments/load")
    def import_instruments_xml(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        xml_content = str(p.get("xml_content") or p.get("xml", ""))
        policy = str(p.get("conflict_policy", "overwrite_all"))
        res = ws.instruments.import_xml(xml_content, conflict_policy=policy)
        return _success(res)


def _register_sessions_crud_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/sessions")
    def list_sessions(
        broker_id: int | None = None,
        search: str | None = None,
    ) -> JSONResponse:
        items = [
            s.to_dict()
            for s in ws.sessions.list_sessions(broker_id=broker_id, search=search)
        ]
        return _success(items)

    @router.post("/sessions")
    def create_session(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.sessions.save_session(p)
        return _success(rec.to_dict())

    @router.get("/sessions/{name}")
    def get_session(name: str) -> JSONResponse:
        sess = ws.sessions.get_session(name)
        if sess is None:
            return _error("NOT_FOUND", f"Session '{name}' not found", 404)
        return _success(sess.to_dict())

    @router.delete("/sessions/{name}")
    def delete_session(name: str) -> JSONResponse:
        deleted = ws.sessions.delete_session(name)
        return _success({"deleted": deleted})

    @router.post("/sessions/clone")
    def clone_session(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.sessions.clone_session(
            source_name=str(p.get("source_name", "")),
            new_name=str(p.get("new_name", "")),
            broker_id=int(p.get("broker_id", -1)),
            broker_postfix=str(p.get("broker_postfix", "")),
        )
        return _success(rec.to_dict())

    @router.post("/sessions/mass-delete")
    def mass_delete_sessions(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        names = p.get("names") or []
        count = ws.sessions.mass_delete_sessions(names)
        return _success({"deleted_count": count})


def _register_sessions_template_routes(
    router: APIRouter, ws: DataManagerWorkspace
) -> None:
    @router.get("/sessions/nt-templates")
    def list_nt_templates(folder_path: str | None = None) -> JSONResponse:
        return _success(ws.sessions.list_nt_templates(folder_path))

    @router.post("/sessions/import-nt")
    def import_nt_sessions(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        xml_content = p.get("xml_content")
        folder = p.get("folder_path")
        policy = str(p.get("conflict_policy", "overwrite"))
        res = ws.sessions.import_nt_sessions(
            xml_content=xml_content, folder_path=folder, conflict_policy=policy
        )
        return _success(res)

    @router.post("/sessions/export-xml")
    def export_sessions_xml(
        payload: dict[str, Any] | None = None,
    ) -> JSONResponse:
        p = payload or {}
        names = p.get("names")
        xml_str = ws.sessions.export_sqx_xml(names)
        return _success(xml_str)

    @router.post("/sessions/import-xml")
    def import_sessions_xml(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        xml_content = str(p.get("xml_content") or p.get("xml", ""))
        policy = str(p.get("policy", "overwrite"))
        res = ws.sessions.import_sqx_xml(xml_content, policy=policy)
        return _success(res)


def _register_baskets_crud_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/baskets/overview")
    def get_baskets_overview() -> JSONResponse:
        overview = [o.to_dict() for o in ws.baskets.get_baskets_overview()]
        return _success(overview)

    @router.post("/baskets/update-data")
    def update_baskets_data(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        ids = p.get("basket_ids") or []
        res = ws.baskets.update_baskets_data(ids)
        return _success(res)

    @router.get("/baskets")
    def list_baskets() -> JSONResponse:
        items = [b.to_dict() for b in ws.baskets.list_baskets()]
        return _success(items)

    @router.post("/baskets")
    def create_basket(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.baskets.save_basket(p)
        return _success(rec.to_dict())

    @router.get("/baskets/{name}")
    def get_basket(name: str) -> JSONResponse:
        b = ws.baskets.get_basket(name)
        if b is None:
            return _error("NOT_FOUND", f"Basket '{name}' not found", 404)
        return _success(b.to_dict())

    @router.delete("/baskets/{name}")
    def delete_basket(name: str) -> JSONResponse:
        deleted = ws.baskets.delete_basket(name)
        return _success({"deleted": deleted})


def _register_baskets_io_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.post("/baskets/export-xml")
    def export_baskets_xml(
        payload: dict[str, Any] | None = None,
    ) -> JSONResponse:
        p = payload or {}
        names = p.get("basket_names")
        xml_content = ws.baskets.export_xml(names)
        return _success({"xml_content": xml_content})

    @router.post("/baskets/import-xml")
    def import_baskets_xml(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        content = str(p.get("xml_content") or p.get("xml", ""))
        ovr = bool(p.get("overwrite", False))
        res = ws.baskets.import_xml(content, overwrite=ovr)
        return _success(res)

    @router.post("/baskets/import-csv")
    def import_baskets_csv(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        name = str(p.get("basket_name", "Imported Basket"))
        csv_text = str(p.get("csv_text") or p.get("content", ""))
        rec = ws.baskets.import_csv(name, csv_text)
        return _success(rec.to_dict())

    @router.get("/baskets/{name}/export-csv")
    def export_basket_csv(name: str) -> JSONResponse:
        content = ws.baskets.export_csv(name)
        return _success({"basket_name": name, "content": content})


def _register_broker_crud_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.post("/brokers/delete")
    def delete_brokers(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        ids = p.get("broker_ids") or []
        count = ws.broker.delete_brokers(ids)
        return _success({"deleted_count": count})

    @router.post("/brokers/{broker_id}/update-data")
    def trigger_broker_update(broker_id: int) -> JSONResponse:
        res = ws.broker.trigger_broker_data_update(broker_id)
        return _success(res)

    @router.get("/brokers/{broker_id}")
    def get_broker(broker_id: int) -> JSONResponse:
        b = ws.broker.get_broker(broker_id)
        if b is None:
            return _error("NOT_FOUND", f"Broker '{broker_id}' not found", 404)
        return _success(b.to_dict())

    @router.get("/brokers")
    def list_brokers() -> JSONResponse:
        brokers = [b.to_dict() for b in ws.broker.list_brokers()]
        return _success(brokers)

    @router.post("/brokers")
    def create_broker(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.broker.save_broker(p)
        return _success(rec.to_dict())


def _register_broker_io_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.post("/brokers/save-xml")
    def export_brokers_xml(
        payload: dict[str, Any] | None = None,
    ) -> JSONResponse:
        p = payload or {}
        ids = p.get("broker_ids")
        xml_str = ws.broker.export_brokers_xml(ids)
        return _success({"xml_content": xml_str})

    @router.post("/brokers/load-xml")
    def import_brokers_xml(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        content = str(p.get("xml_content") or p.get("xml", ""))
        brokers = [b.to_dict() for b in ws.broker.import_brokers_xml(content)]
        return _success(brokers)

    @router.post("/brokers/import-get-overview")
    def inspect_xml_overview(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        content = str(p.get("xml_content") or p.get("xml", ""))
        kind = str(p.get("kind", "Broker"))
        items = [i.to_dict() for i in ws.broker.inspect_xml_overview(content, kind)]
        return _success(items)

    @router.post("/brokers/import-session-instrument")
    def import_xml_records(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        content = str(p.get("xml_content") or p.get("xml", ""))
        kind = str(p.get("kind", "Instrument"))
        bid = int(p.get("broker_id", 0))
        postfix = str(p.get("postfix", ""))
        selected = p.get("selected_names") or []
        count = ws.broker.import_xml_records(content, kind, bid, postfix, selected)
        return _success({"imported_count": count})


def _register_broker_stocks_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/brokers/{broker_id}/stocks/export")
    def export_broker_stocks_csv(broker_id: int) -> JSONResponse:
        content = ws.broker.export_broker_stocks_csv(broker_id)
        return _success({"broker_id": broker_id, "content": content})

    @router.get("/brokers/{broker_id}/stocks")
    def get_broker_stocks(broker_id: int) -> JSONResponse:
        stocks = ws.broker.get_broker_stocks(broker_id)
        return _success({"broker_id": broker_id, "stocks": stocks})

    @router.put("/brokers/{broker_id}/stocks")
    def save_broker_stocks(
        broker_id: int, payload: dict[str, Any] | None = None
    ) -> JSONResponse:
        p = payload or {}
        stocks = p.get("stocks") or []
        count = ws.broker.save_broker_stocks(broker_id, stocks)
        return _success({"broker_id": broker_id, "count": count})

    @router.post("/brokers/{broker_id}/stocks/import")
    def import_broker_stocks(
        broker_id: int, payload: dict[str, Any] | None = None
    ) -> JSONResponse:
        p = payload or {}
        content = str(p.get("content") or p.get("csv", ""))
        count = ws.broker.import_broker_stocks_csv(broker_id, content)
        return _success({"broker_id": broker_id, "count": count})


def _register_providers_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/providers/{provider_id}/health")
    def check_provider_health(provider_id: str) -> JSONResponse:
        try:
            status = ws.connections.check_connection(provider_id).to_dict()
            return _success(status)
        except ProviderError as exc:
            return _error(exc.code, exc.message, exc.status_code)

    @router.get("/providers")
    def list_providers() -> JSONResponse:
        providers = [p.to_dict() for p in ws.connections.list_providers()]
        return _success(providers)

    @router.post("/providers/download")
    async def download_data(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        try:
            res = await ws.connections.download_historical_data_async(p)
            return _success(res.to_dict())
        except ProviderError as exc:
            return _error(exc.code, exc.message, exc.status_code)
        except ValueError as exc:
            return _error("VALIDATION_ERROR", str(exc), 422)


def _register_custom_data_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.post("/custom-data/recognize-mq4")
    def recognize_mq4(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        fn = str(p.get("filename", "Indicator.mq4"))
        src = str(p.get("source_code") or p.get("source", ""))
        rec = ws.custom_data.recognize_mq4(fn, src)
        return _success(rec.to_dict())

    @router.post("/custom-data/{name}/clear")
    def clear_custom_data(name: str) -> JSONResponse:
        rec = ws.custom_data.clear_definition(name)
        return _success(rec.to_dict())

    @router.post("/custom-data/{name}/import")
    def import_custom_data_csv(
        name: str, payload: dict[str, Any] | None = None
    ) -> JSONResponse:
        p = payload or {}
        csv_text = str(p.get("csv_text") or p.get("content", ""))
        sep = str(p.get("separator", ","))
        skip = int(p.get("skip_rows", 0))
        rec = ws.custom_data.import_csv_records(
            name, csv_text, separator=sep, skip_rows=skip
        )
        return _success(rec.to_dict())

    @router.get("/custom-data/{name}")
    def get_custom_data(name: str) -> JSONResponse:
        defn = ws.custom_data.get_definition(name)
        if defn is None:
            return _error("NOT_FOUND", f"Custom data '{name}' not found", 404)
        return _success(defn.to_dict())

    @router.delete("/custom-data/{name}")
    def delete_custom_data(name: str) -> JSONResponse:
        deleted = ws.custom_data.delete_definition(name)
        return _success({"deleted": deleted})

    @router.get("/custom-data")
    def list_custom_data() -> JSONResponse:
        items = [c.to_dict() for c in ws.custom_data.list_definitions()]
        return _success(items)

    @router.post("/custom-data")
    def save_custom_data(payload: dict[str, Any] | None = None) -> JSONResponse:
        p = payload or {}
        rec = ws.custom_data.save_definition(p)
        return _success(rec.to_dict())


def _register_help_routes(router: APIRouter, ws: DataManagerWorkspace) -> None:
    @router.get("/help/topics")
    def list_help_topics(section: str | None = None) -> JSONResponse:
        topics = [t.to_dict() for t in ws.help.list_topics(section)]
        return _success(topics)

    @router.get("/help/topics/{topic_id}")
    def get_help_topic(topic_id: str) -> JSONResponse:
        t = ws.help.get_topic(topic_id)
        if t is None:
            return _error("NOT_FOUND", f"Topic '{topic_id}' not found", 404)
        return _success(t.to_dict())

    @router.get("/help/faqs")
    def search_faqs(query: str | None = None) -> JSONResponse:
        faqs = [f.to_dict() for f in ws.help.search_faqs(query)]
        return _success(faqs)


def create_data_manager_router(
    workspace: DataManagerWorkspace | None = None,
    session_mgr: SessionManager | None = None,
    require_auth: bool = False,
) -> APIRouter:
    """Create and configure the FastAPI APIRouter for all Data Manager endpoints."""
    ws = workspace or DataManagerWorkspace()
    dependencies: list[Any] = []
    if require_auth:

        async def _auth_dependency(
            request: Request,
            authorization: str | None = Header(None, alias="Authorization"),
        ) -> None:
            token = extract_bearer_token(
                authorization, request.query_params.get("token")
            )
            if token is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Active session required for Data Manager access.",
                )
            mgr: SessionManager | None = None
            if hasattr(request.app.state, "runtime") and request.app.state.runtime:
                mgr = getattr(request.app.state.runtime, "session_manager", None)
            if mgr is None:
                mgr = session_mgr
            if mgr is None:
                from app.host.session import session_manager as global_session_mgr

                mgr = global_session_mgr

            if mgr.validate_token(token) is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session token.",
                )

        dependencies.append(Depends(_auth_dependency))

    router = APIRouter(
        prefix="/data",
        tags=["Data Manager"],
        dependencies=dependencies,
    )

    _register_home_routes(router, ws)
    _register_logs_routes(router, ws)
    _register_export_routes(router, ws)
    _register_datasets_review_routes(router, ws)
    _register_datasets_transform_quality_routes(router, ws)
    _register_datasets_crud_routes(router, ws)
    _register_instruments_alias_routes(router, ws)
    _register_instruments_crud_routes(router, ws)
    _register_sessions_template_routes(router, ws)
    _register_sessions_crud_routes(router, ws)
    _register_baskets_io_routes(router, ws)
    _register_baskets_crud_routes(router, ws)
    _register_broker_io_routes(router, ws)
    _register_broker_stocks_routes(router, ws)
    _register_broker_crud_routes(router, ws)
    _register_providers_routes(router, ws)
    _register_custom_data_routes(router, ws)
    _register_help_routes(router, ws)

    logger.info(
        "%s: Registered Data Manager router with %d route rules",
        GATEWAY_FR,
        len(router.routes),
        extra={"fr_id": GATEWAY_FR, "routes_count": len(router.routes)},
    )
    return router


def main() -> None:
    """Execute real-usage demonstration of DataManagerWorkspace and router."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_workspace.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        workspace = DataManagerWorkspace(db_path=db_file, data_dir=temp_path / "data")
        seeded = workspace.initialize_defaults()
        print(f"Initialized defaults: {seeded}")

        router = create_data_manager_router(workspace)
        print(f"Created Data Manager router with {len(router.routes)} endpoints")

        overview = workspace.home.get_overview()
        print(f"Workspace overview: {overview.to_dict()}")


if __name__ == "__main__":
    main()

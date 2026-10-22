"""FastAPI route registration and workspace coordinator for Data Manager.

Description:
    Exposes RESTful endpoints for the Data Manager workspace, mounting
    authoritative routes under /data. Coordinates workspace lifecycle and
    delegates dashboard requests directly to Home. Emits structured telemetry
    with zero silent execution.

Purpose:
    FEAT-DATAMGR-SHELL: Dockable workspace and linked recorded-data selection.
    FEAT-DATAMGR-ROUTES: Authenticated Data Manager HTTP gateway.

Key Capabilities:
    - FR-DATAMGR-SHELL-INIT: Panels [AppDataManager.init_workspace()] -> INFO.
    - FR-DATAMGR-SHELL-TAB: Selection [AppDataManager.open_tab()] -> INFO/WARNING.
    - FR-DATAMGR-ROUTES-FASTAPI-GATEWAY: Routes (create_data_manager_router -> INFO).

Python API Usage:
    ```python
    from app.workspace.data_manager.routes import (
        AppDataManager,
        create_data_manager_router,
    )

    workspace = AppDataManager()
    layout = workspace.init_workspace()
    router = create_data_manager_router(workspace)
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.routes
    ```
"""

from __future__ import annotations

import json
import math
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.response import ApiResponse
from app.host.session import SessionManager, session_manager
from app.host.transport import extract_bearer_token
from app.services.brokers.files import read_parquet_bars
from app.services.include.contracts import DataInfo
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from .baskets import Basket
from .broker import Broker
from .data import Data
from .help import DMHelp
from .home import Home
from .instruments import Instruments
from .log import DataLog
from .sessions import Sessions

if TYPE_CHECKING:
    from app.host.discovery import PluginLifecycleManager
    from app.host.transport import EventBus
    from app.services.include.trading import Trading

__all__ = [
    "AppDataManager",
    "create_data_manager_router",
]

logger = get_logger(__name__)

FACADE_FR = "FR-DATAMGR-ROUTES-WORKSPACE-FACADE"
GATEWAY_FR = "FR-DATAMGR-ROUTES-FASTAPI-GATEWAY"
INIT_FR = "FR-DATAMGR-SHELL-INIT"
TAB_FR = "FR-DATAMGR-SHELL-TAB"
_CORE_TABS = frozenset({"data", "instruments", "sessions", "brokers", "custom-data"})
_TABS = (
    ("data", "Data"),
    ("instruments", "Instruments"),
    ("sessions", "Sessions"),
    ("brokers", "Brokers"),
    ("custom-data", "Custom Data"),
    ("chart", "Chart"),
    ("home", "Home"),
    ("stock-groups", "Stock groups"),
    ("log", "Log"),
)


@dataclass(frozen=True)
class _Config:
    preview_rows: int = 500
    preview_bytes: int = 32 * 1024 * 1024


def _preview_state(state: str, reason: str) -> dict[str, Any]:
    return {"state": state, "reason": reason, "rows": [], "limit": 500}


def _normalized_bars(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate and normalize one shared table/chart array of recorded bars."""
    by_time: dict[int, dict[str, Any]] = {}
    for row in rows:
        time = float(row["time"])
        prices = {key: float(row[key]) for key in ("open", "high", "low", "close")}
        volume = float(row.get("tick_volume", row.get("volume", 0)))
        if not all(math.isfinite(value) for value in (time, volume, *prices.values())):
            raise ValueError("Nonfinite historical bar.")
        if time < 0 or time != int(time) or volume < 0:
            raise ValueError("Invalid historical timestamp or volume.")
        if prices["low"] > min(prices.values()) or prices["high"] < max(
            prices.values()
        ):
            raise ValueError("Invalid historical price envelope.")
        stamp = int(time)
        by_time[stamp] = {"time": stamp, **prices, "volume": volume}
    return [by_time[stamp] for stamp in sorted(by_time)]


def _metatrader_trading() -> Trading:
    """Build a MetaTrader 5 trading facade from the bridge token env var."""
    from app.services.brokers.metatrader import MetaTraderClient
    from app.services.include.trading import Trading

    token = os.environ.get("MT5_BRIDGE_TOKEN", "").strip()
    if not token:
        raise ValueError("MT5_BRIDGE_TOKEN is not set.")
    return Trading(MetaTraderClient(auth_token=token))


class AppDataManager:
    """Authoritative workspace facade coordinating Data Manager domain services."""

    def __init__(
        self,
        *,
        data_dir: Path | str | None = None,
        event_bus: EventBus | None = None,
        plugin_mgr: PluginLifecycleManager | None = None,
        broker_registry: Any | None = None,
        job_manager: Any | None = None,
        trading_factory: Callable[[], Trading] | None = None,
    ) -> None:
        """Instantiate workspace with data directory and event broker."""
        self.data_dir = Path(data_dir) if data_dir is not None else Path("data")
        self.event_bus = event_bus
        self.plugin_mgr = plugin_mgr
        self.broker_registry = broker_registry
        self.job_manager = job_manager
        self.trading_factory = trading_factory or _metatrader_trading

        # Initialize retained Home, Log, and Help services
        self.home = Home()
        self.broker = Broker()
        self.baskets = Basket()
        self.instruments = Instruments()
        self.sessions = Sessions()
        self.data = Data()
        self.log = DataLog(event_bus=event_bus)
        self.help = DMHelp()

        logger.info(
            "%s: Initialized AppDataManager",
            FACADE_FR,
            extra={"fr_id": FACADE_FR},
        )

    def init_workspace(self) -> dict[str, Any]:
        """Return the deterministic Dockview panel catalog without saving state."""
        logger.info(
            "%s: Initialized dockable workspace", INIT_FR, extra={"fr_id": INIT_FR}
        )
        return {
            "tabs": [
                {"id": tab_id, "title": title, "core": tab_id in _CORE_TABS}
                for tab_id, title in _TABS
            ],
            "active_tab": "data",
            "layout": {"core_group": "catalogs", "chart_position": "right"},
        }

    def open_tab(
        self, tab_id: str, context: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        """Resolve a tab and dataset snapshot; selection is never shared globally."""
        try:
            return self._open_tab(tab_id, context)
        except ValueError, LookupError:
            logger.warning(
                "%s: Rejected workspace context", TAB_FR, extra={"fr_id": TAB_FR}
            )
            raise

    def _open_tab(
        self, tab_id: str, context: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        if tab_id not in dict(_TABS):
            raise ValueError("Unsupported Data Manager tab.")
        if context is not None and (
            not isinstance(context, Mapping) or set(context) - {"dataset_id"}
        ):
            raise ValueError("Context accepts only dataset_id.")
        selection = None
        preview = _preview_state("unavailable", "Select a saved dataset.")
        if context:
            dataset_id = context.get("dataset_id")
            if not isinstance(dataset_id, str) or not dataset_id.strip():
                raise ValueError("dataset_id must be a nonempty string.")
            dataset = next(
                (row for row in self.home.get_saved_datasets() if row.id == dataset_id),
                None,
            )
            if dataset is None:
                raise LookupError("Selected dataset is no longer in the catalog.")
            selection = dataset.to_dict()
            preview = self._preview(dataset)
        logger.info(
            "%s: Opened workspace tab %s", TAB_FR, tab_id, extra={"fr_id": TAB_FR}
        )
        return {"active_tab": tab_id, "selection": selection, "preview": preview}

    def _preview(self, dataset: DataInfo) -> dict[str, Any]:
        if str(dataset.timeframe).upper() == "TICK":
            return _preview_state("unavailable", "Tick preview is not supported.")
        if not dataset.path:
            return _preview_state("unavailable", "No recorded history path in catalog.")
        try:
            path = self._preview_path(dataset.path)
            if not path.is_file():
                return _preview_state(
                    "unavailable", "Recorded history file is missing."
                )
            if path.stat().st_size > _Config().preview_bytes:
                return _preview_state(
                    "unavailable", "History exceeds the 32 MiB preview limit."
                )
            rows = _normalized_bars(
                read_parquet_bars(path, count=_Config().preview_rows)
            )
            return (
                {"state": "ready", "reason": "", "rows": rows, "limit": 500}
                if rows
                else _preview_state("unavailable", "No recorded bars available.")
            )
        except OSError, ValueError, KeyError, TypeError, OverflowError:
            logger.warning(
                "%s: Recorded preview unavailable", TAB_FR, extra={"fr_id": TAB_FR}
            )
            return _preview_state("error", "Recorded history cannot be previewed.")

    def _preview_path(self, stored_path: str) -> Path:
        root = self.data_dir.resolve()
        candidate = Path(stored_path.replace("\\", "/"))
        if not candidate.is_absolute():
            parts = candidate.parts
            if parts and parts[0] == root.name:
                candidate = Path(*parts[1:])
            candidate = root / candidate
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root) or resolved.suffix.lower() != ".parquet":
            raise ValueError("History path is outside preview policy.")
        return resolved


def _success(data: Any, message: str = "Success") -> JSONResponse:
    return JSONResponse(content=ApiResponse.ok(data=data, meta={"message": message}))


def _register_home_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.get("/home/overview")
    def get_home_overview() -> JSONResponse:
        data = ws.home.get_overview()
        return _success(data)

    @router.get("/home/datasets")
    def get_home_datasets() -> JSONResponse:
        datasets = [d.to_dict() for d in ws.home.get_saved_datasets()]
        return _success(datasets)


def _register_workspace_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.get("/workspace")
    def init_workspace() -> JSONResponse:
        return _success(ws.init_workspace())

    @router.post("/workspace/tabs/{tab_id}")
    def open_tab(tab_id: str, payload: dict[str, Any]) -> JSONResponse:
        if set(payload) - {"context"}:
            return _workspace_error("Request accepts only context.", 422)
        try:
            return _success(ws.open_tab(tab_id, payload.get("context")))
        except (ValueError, LookupError) as error:
            code = 404 if isinstance(error, LookupError) else 422
            return _workspace_error(str(error), code)


def _catalog_response(
    operation: Any,
    *args: Any,
    code: int = 200,
    domain: str = "Instrument",
    **options: Any,
) -> JSONResponse:
    try:
        data = operation(*args, **options)
        return JSONResponse(status_code=code, content=ApiResponse.ok(data=data))
    except (ValueError, LookupError, FileExistsError) as error:
        error_code = (
            409
            if isinstance(error, FileExistsError)
            else 404
            if isinstance(error, LookupError)
            else 422
        )
        return JSONResponse(
            status_code=error_code,
            content=ApiResponse.error(
                f"{domain.upper()}_REQUEST", str(error), status_code=error_code
            ),
        )
    except RuntimeError:
        logger.error("%s storage unavailable", domain, extra={"fr_id": GATEWAY_FR})  # noqa: TRY400 - sanitized boundary
        return JSONResponse(
            status_code=503,
            content=ApiResponse.error(
                f"{domain.upper()}_STORAGE",
                f"{domain} storage is unavailable. Retry the operation.",
                status_code=503,
            ),
        )


def _register_basket_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.get("/baskets")
    def list_baskets() -> JSONResponse:
        return _catalog_response(ws.baskets.baskets, domain="Basket")

    @router.post("/baskets")
    def save_basket(payload: dict[str, Any]) -> JSONResponse:
        return _catalog_response(ws.baskets.add_basket, payload, domain="Basket")

    @router.post("/baskets/delete")
    def delete_baskets(payload: dict[str, Any]) -> JSONResponse:
        if set(payload) != {"ids"}:
            return _workspace_error("Supply only the selected basket IDs.", 422)
        return _catalog_response(
            ws.baskets.delete_basket, payload["ids"], domain="Basket"
        )

    @router.put("/baskets/{basket_id}/stocks")
    def save_basket_stocks(basket_id: str, payload: dict[str, Any]) -> JSONResponse:
        if set(payload) != {"symbols"}:
            return _workspace_error("Supply only the complete membership strings.", 422)
        return _catalog_response(
            ws.baskets.edit_stocks, basket_id, payload["symbols"], domain="Basket"
        )


def _register_broker_read_routes(router: APIRouter, ws: AppDataManager) -> None:
    def profile(broker_id: str) -> dict[str, Any]:
        if not broker_id.isascii() or not broker_id.isdigit() or int(broker_id) <= 0:
            raise ValueError("Choose a positive numeric broker ID.")
        for row in ws.broker.brokers():
            if row["id"] == broker_id:
                return row
        raise LookupError("Broker is no longer in the catalog.")

    @router.get("/brokers")
    def list_brokers() -> JSONResponse:
        return _catalog_response(ws.broker.brokers, domain="Broker")

    @router.get("/brokers/{broker_id}")
    def get_broker(broker_id: str) -> JSONResponse:
        return _catalog_response(profile, broker_id, domain="Broker")

    @router.get("/brokers/{broker_id}/stocks")
    def get_stocks(broker_id: str) -> JSONResponse:
        def stocks() -> dict[str, Any]:
            row = profile(broker_id)
            return {"broker_id": row["id"], "stocks": row["stocks"]}

        return _catalog_response(stocks, domain="Broker")


def _register_broker_write_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.post("/brokers")
    def save_broker(payload: dict[str, Any]) -> JSONResponse:
        return _catalog_response(ws.broker.add_broker, payload, domain="Broker")

    @router.post("/brokers/delete")
    def delete_brokers(payload: dict[str, Any]) -> JSONResponse:
        if set(payload) != {"ids"}:
            return _workspace_error("Supply only the selected broker IDs.", 422)
        return _catalog_response(
            ws.broker.delete_broker, payload["ids"], domain="Broker"
        )

    @router.put("/brokers/{broker_id}/stocks")
    def save_stocks(broker_id: str, payload: dict[str, Any]) -> JSONResponse:
        if set(payload) != {"stocks"}:
            return _workspace_error("Supply only the complete stocks list.", 422)
        return _catalog_response(
            ws.broker.edit_stocks, broker_id, payload["stocks"], domain="Broker"
        )

    @router.post("/brokers/{broker_id}/import-instruments")
    def import_instruments(broker_id: str, payload: dict[str, Any]) -> JSONResponse:
        return _catalog_response(
            ws.broker.import_instruments,
            broker_id,
            json.dumps(payload),
            domain="Broker",
        )

    @router.post("/brokers/{broker_id}/import-sessions")
    def import_sessions(broker_id: str, payload: dict[str, Any]) -> JSONResponse:
        return _catalog_response(
            ws.broker.import_sessions, broker_id, json.dumps(payload), domain="Broker"
        )


def _register_instrument_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.get("/instruments")
    def list_instruments(request: Request) -> JSONResponse:
        return _catalog_response(ws.instruments.instruments, dict(request.query_params))

    @router.post("/instruments")
    def add_instrument(payload: dict[str, Any]) -> JSONResponse:
        return _catalog_response(ws.instruments.add_instrument, payload, code=201)

    @router.post("/instruments/mass-edit")
    def mass_edit_instruments(payload: dict[str, Any]) -> JSONResponse:
        if set(payload) != {"instrument_ids", "updates"} or not isinstance(
            payload["instrument_ids"], list
        ):
            return JSONResponse(
                status_code=422,
                content=ApiResponse.error(
                    "INSTRUMENT_REQUEST",
                    "Expected instrument_ids array and updates.",
                    status_code=422,
                ),
            )
        return _catalog_response(
            ws.instruments.mass_edit_instruments,
            payload["instrument_ids"],
            payload["updates"],
        )

    @router.post("/instruments/clone")
    def clone_instrument(payload: dict[str, Any]) -> JSONResponse:
        if set(payload) != {"source_id", "new_symbol"}:
            return JSONResponse(
                status_code=422,
                content=ApiResponse.error(
                    "INSTRUMENT_REQUEST",
                    "Expected source_id and new_symbol.",
                    status_code=422,
                ),
            )
        return _catalog_response(
            ws.instruments.clone_instrument,
            payload["source_id"],
            payload["new_symbol"],
            code=201,
        )


def _register_instrument_job_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.post("/instruments/delete")
    def delete_instruments(payload: dict[str, Any]) -> JSONResponse:
        if set(payload) != {"instrument_ids"} or not isinstance(
            payload["instrument_ids"], list
        ):
            return JSONResponse(
                status_code=422,
                content=ApiResponse.error(
                    "INSTRUMENT_REQUEST",
                    "Expected instrument_ids array.",
                    status_code=422,
                ),
            )
        return _catalog_response(
            ws.instruments.delete_instruments, payload["instrument_ids"]
        )

    @router.post("/instruments/refresh")
    async def refresh_instruments(payload: dict[str, Any]) -> JSONResponse:
        symbols = payload.get("symbols")
        if set(payload) - {"symbols"} or not (
            symbols is None or isinstance(symbols, list)
        ):
            return JSONResponse(
                status_code=422,
                content=ApiResponse.error(
                    "INSTRUMENT_REQUEST",
                    "Expected optional symbols array.",
                    status_code=422,
                ),
            )
        try:
            trading = ws.trading_factory()
            await trading.start()
            try:
                await trading.wait_connected(timeout=30.0)
                data = await ws.instruments.refresh_instruments(trading, symbols)
            finally:
                await trading.close()
        except (ValueError, LookupError) as error:
            return JSONResponse(
                status_code=422,
                content=ApiResponse.error(
                    "INSTRUMENT_REQUEST", str(error), status_code=422
                ),
            )
        except (RuntimeError, OSError) as error:
            logger.error(  # noqa: TRY400 - sanitized boundary
                "Instrument refresh failed: %s",
                type(error).__name__,
                extra={"fr_id": GATEWAY_FR},
            )
            return JSONResponse(
                status_code=503,
                content=ApiResponse.error(
                    "INSTRUMENT_REFRESH",
                    "MetaTrader 5 is unavailable. Check the bridge and retry.",
                    status_code=503,
                ),
            )
        return JSONResponse(content=ApiResponse.ok(data=data))


def _register_session_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.get("/sessions")
    def list_sessions(request: Request) -> JSONResponse:
        return _catalog_response(
            ws.sessions.sessions, dict(request.query_params), domain="Session"
        )

    @router.post("/sessions")
    def save_session(payload: dict[str, Any]) -> JSONResponse:
        return _catalog_response(
            ws.sessions.session_template,
            payload,
            domain="Session",
            code=200 if "id" in payload else 201,
        )

    @router.post("/sessions/clone")
    def clone_session(payload: dict[str, Any]) -> JSONResponse:
        if not {"session_id", "new_name"} <= set(payload) or set(payload) - {
            "session_id",
            "new_name",
            "timezone_offset",
        }:
            logger.warning(
                "Invalid session clone request",
                extra={"fr_id": "FR-DATAMGR-SESS-CLONE"},
            )
            return JSONResponse(
                status_code=422,
                content=ApiResponse.error(
                    "SESSION_REQUEST",
                    "Expected session_id, new_name and optional timezone_offset.",
                    status_code=422,
                ),
            )
        return _catalog_response(
            ws.sessions.clone_session,
            payload["session_id"],
            payload["new_name"],
            timezone_offset=payload.get("timezone_offset", 0),
            domain="Session",
            code=201,
        )

    @router.delete("/sessions/{session_id}")
    def delete_session(session_id: str) -> JSONResponse:
        return _catalog_response(
            ws.sessions.clone_session, session_id, "", delete=True, domain="Session"
        )

    @router.post("/sessions/{session_id}/elements")
    def session_element(session_id: str, payload: dict[str, Any]) -> JSONResponse:
        return _catalog_response(
            ws.sessions.session_element, session_id, payload, domain="Session"
        )


def _register_log_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.get("/logs")
    def get_data_logs(limit: int = 100) -> JSONResponse:
        try:
            return _success(ws.log.data_log(limit=limit))
        except ValueError as error:
            return _workspace_error(str(error), 422)

    @router.post("/logs")
    def create_data_log(payload: dict[str, Any]) -> JSONResponse:
        try:
            return _success(ws.log.data_log(entry=payload)[0])
        except ValueError as error:
            return _workspace_error(str(error), 422)

    @router.post("/logs/clear")
    def clear_data_logs() -> JSONResponse:
        return _success(ws.log.clear_log())


def _register_help_routes(router: APIRouter, ws: AppDataManager) -> None:
    @router.get("/help")
    def get_data_help(topic: str = "overview") -> JSONResponse:
        try:
            return _success(ws.help.help(topic=topic))
        except ValueError as error:
            return _workspace_error(str(error), 422)


def _workspace_error(message: str, code: int) -> JSONResponse:
    logger.warning("%s: Rejected workspace request", TAB_FR, extra={"fr_id": TAB_FR})
    return JSONResponse(
        status_code=code,
        content=ApiResponse.error(
            "WORKSPACE_CONTEXT",
            message,
            status_code=code,
        ),
    )


def create_data_manager_router(
    workspace: AppDataManager | None = None,
    session_mgr: SessionManager | None = None,
    require_auth: bool = False,
) -> APIRouter:
    """Create and configure the FastAPI APIRouter for Data Manager endpoints."""
    ws = workspace or AppDataManager()
    effective_session_mgr = session_mgr or session_manager
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
            runtime = getattr(request.app.state, "runtime", None)
            mgr: SessionManager = (
                getattr(runtime, "session_manager", None) or effective_session_mgr
            )
            if mgr.verify_session(token) is None:
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
    _register_workspace_routes(router, ws)
    _register_basket_routes(router, ws)
    _register_broker_read_routes(router, ws)
    _register_broker_write_routes(router, ws)
    _register_instrument_routes(router, ws)
    _register_instrument_job_routes(router, ws)
    _register_session_routes(router, ws)
    _register_log_routes(router, ws)
    _register_help_routes(router, ws)

    logger.info(
        "%s: Registered Data Manager router with %d route rules",
        GATEWAY_FR,
        len(router.routes),
        extra={"fr_id": GATEWAY_FR, "routes_count": len(router.routes)},
    )
    return router


def main() -> None:
    """Execute real-usage demonstration of AppDataManager and router."""
    workspace = AppDataManager()
    workspace.init_workspace()
    router = create_data_manager_router(workspace)
    logger.info("Created Data Manager router with %d endpoints", len(router.routes))


if __name__ == "__main__":
    main()

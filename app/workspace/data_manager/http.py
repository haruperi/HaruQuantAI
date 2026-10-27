"""Authenticated Data Manager HTTP adapter for the browser workspace."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import Any, cast

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.host.persistence import HostPersistence, RecordFilter
from app.host.response import ErrorCode
from app.host.transport import (
    TransportError,
    _require,  # pyright: ignore[reportPrivateUsage]
)
from app.workspace.data_manager.baskets import Baskets
from app.workspace.data_manager.brokers import Brokers
from app.workspace.data_manager.custom_http import register_custom_routes
from app.workspace.data_manager.data import Data
from app.workspace.data_manager.dukascopy_http import register_dukascopy_routes
from app.workspace.data_manager.help import Help
from app.workspace.data_manager.http_fields import (
    symbol_to_ui as _ui,
)
from app.workspace.data_manager.http_fields import (
    symbol_updates as _updates,
)
from app.workspace.data_manager.sessions import Sessions
from app.workspace.data_manager.symbols import Symbols

TABS = (
    "data",
    "symbols",
    "sessions",
    "brokers",
    "custom-data",
    "chart",
    "home",
    "stock-groups",
    "log",
)
CORE_TABS = {"data", "symbols", "sessions", "brokers", "custom-data"}
MAX_CSV_BYTES = 10_000_000
MAX_BROKER_STOCKS = 10000
MAX_TICKER_LENGTH = 50
_BASKET_JOB_LOCK = Lock()
_MAX_BASKET_TRANSFER_BYTES = 20 * 1024 * 1024


def _access(request: Request) -> None:
    """Apply the host's UI session and scope checks to domain requests."""
    scope = "data:read" if request.method == "GET" else "data:write"
    if request.headers.get("x-peer-id") == "cli" and request.url.path.startswith(
        "/api/v1/data/logs"
    ):
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        sessions = request.app.state.sessions
        if sessions.validate_session(token, "cli") is None:
            raise TransportError(ErrorCode.UNAUTHORIZED, "A CLI session is required")
        if not sessions.authorize(token, "cli", scope):
            raise TransportError(ErrorCode.FORBIDDEN, "Capability is not granted")
    else:
        _require(request, scope)


def _response(result: dict[str, Any]) -> JSONResponse:
    """Keep service errors and HTTP status consistent with the host envelope."""
    statuses = {"validation": 422, "not_found": 404, "conflict": 409}
    body = {**result, "status": "success" if result["success"] else "error"}
    code = (
        200
        if result["success"]
        else statuses.get(
            cast("dict[str, Any]", result.get("error") or {}).get("code", "internal"),
            503,
        )
    )
    return JSONResponse(jsonable_encoder(body), status_code=code)


def _ok(data: Any) -> dict[str, Any]:
    return {"status": "success", "success": True, "data": data}


def _json(value: Any) -> dict[str, Any]:
    return json.loads(value) if isinstance(value, str) else value or {}


def _rows(
    gateway: HostPersistence,
    table: str = "datamgr_symbols",
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset: int | None = 0
    while offset is not None:
        data = _service_data(
            gateway.read_records(table, filters=filters, limit=1000, offset=offset)
        )
        rows.extend(data["records"])
        offset = data["pagination"].get("next_offset")
    return rows


def _names(rows: list[dict[str, Any]], ids: list[str]) -> list[str]:
    found = {str(row["id"]): row["name"] for row in rows}
    if not ids or any(key not in found for key in ids):
        raise TransportError(ErrorCode.NOT_FOUND, "Select existing symbols")
    return list(dict.fromkeys(found[key] for key in ids))


def create_router() -> APIRouter:
    """Register browser workspace and symbol commands within their domain."""
    router = APIRouter(prefix="/api/v1/data", dependencies=[Depends(_access)])

    @router.get("/home/datasets")
    def datasets() -> dict[str, Any]:
        return _ok(_service_data(Data().list()))

    @router.get("/workspace")
    def workspace() -> dict[str, Any]:
        return _ok(
            {
                "tabs": [
                    {
                        "id": key,
                        "title": key.replace("-", " ").title(),
                        "core": key in CORE_TABS,
                    }
                    for key in TABS
                ],
                "active_tab": "data",
                "layout": {"core_group": "catalogs", "chart_position": "right"},
            }
        )

    @router.post("/workspace/tabs/{tab}")
    def open_tab(tab: str) -> dict[str, Any]:
        tab = "symbols" if tab == "instruments" else tab
        if tab not in TABS:
            raise TransportError(ErrorCode.NOT_FOUND, "Unknown workspace tab")
        return _ok(
            {
                "active_tab": tab,
                "selection": None,
                "preview": {
                    "state": "unavailable",
                    "reason": "Select a saved dataset to preview bars.",
                    "rows": [],
                    "limit": 500,
                },
            }
        )

    @router.get("/instruments")
    @router.get("/symbols")
    def list_symbols(request: Request) -> dict[str, Any]:
        return _ok([_ui(row) for row in _rows(request.app.state.persistence)])

    @router.post("/instruments")
    @router.post("/symbols")
    def add_symbol(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        name = str(body.get("symbol") or "").strip()
        datasource = str(body.get("datasource") or "SQ default").strip()
        result = Symbols(gateway).add(
            name=name, datasource=datasource, **_updates(body)
        )
        if not result["success"]:
            return _response(result)
        saved = result["data"]["name"]
        return _ok(_ui(next(row for row in _rows(gateway) if row["name"] == saved)))

    @router.post("/instruments/{command}")
    @router.post("/symbols/{command}")
    def symbol_command(command: str, request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        return _execute(command, body, Symbols(gateway), gateway)

    _source_routes(router)

    _session_routes(router)
    _broker_routes(router)
    _basket_routes(router)
    _log_routes(router)
    register_custom_routes(router)
    _help_routes(router)
    register_dukascopy_routes(router)
    return router


def _execute(
    command: str, body: dict[str, Any], service: Symbols, gateway: HostPersistence
) -> Any:
    if command in {"load", "save"}:
        return _transfer(command, body, service, gateway)
    rows = _rows(gateway)
    if command == "clone":
        name = _names(rows, [body["source_id"]])[0]
        result = service.clone(name, body["new_symbol"])
        if result["success"]:
            saved = result["data"]["name"]
            return _ok(_ui(next(row for row in _rows(gateway) if row["name"] == saved)))
    elif command == "delete":
        names = _names(rows, body.get("instrument_ids", body.get("symbol_ids", [])))
        result = service.delete(names)
        if result["success"]:
            return _ok({"deleted_count": len(result["data"])})
    elif command in {"mass-edit", "update"}:
        return _edit_or_update(command, body, service, gateway, rows)
    elif command == "refresh":
        return _ok({"deleted_count": 0, "inserted_count": len(rows)})
    else:
        raise TransportError(ErrorCode.NOT_FOUND, "Unknown symbol command")
    return _response(result)


def _edit_or_update(
    command: str,
    body: dict[str, Any],
    service: Symbols,
    gateway: HostPersistence,
    rows: list[dict[str, Any]],
) -> Any:
    """Update requested rows, or bootstrap an empty catalog from MT5."""
    ids = body.get("instrument_ids", body.get("symbol_ids", []))
    names = _names(rows, ids) if ids or command != "update" else None
    result = (
        service.mt5update(names)
        if command == "update"
        else service.edit(names or [], updates=_updates(body["updates"]))
    )
    if result["success"]:
        return _ok(
            {
                "updated_count": len(result["data"]),
                "symbols": [
                    _ui(row)
                    for row in _rows(gateway)
                    if not ids or str(row["id"]) in ids
                ],
            }
        )
    return _response(result)


def _transfer(
    command: str, body: dict[str, Any], service: Symbols, gateway: HostPersistence
) -> Any:
    with TemporaryDirectory(prefix="haru-symbols-") as folder:
        path = Path(folder) / "symbols.csv"
        if command == "load":
            content = body.get("content")
            if (
                not isinstance(content, str)
                or len(content.encode("utf-8")) > MAX_CSV_BYTES
            ):
                raise TransportError(
                    ErrorCode.VALIDATION, "Choose a CSV file up to 10 MB"
                )
            path.write_text(content, encoding="utf-8-sig")
            result = service.load(path)
            if result["success"]:
                return _ok(
                    {
                        "loaded_count": len(result["data"]["loaded"]),
                        "errors": result["data"]["errors"],
                        "total": result["data"]["total"],
                    }
                )
        else:
            rows = _rows(gateway)
            ids = body.get("instrument_ids", body.get("symbol_ids", []))
            names = _names(rows, ids) if ids else [row["name"] for row in rows]
            result = service.save(names, path)
            if result["success"]:
                return _ok(
                    {
                        "content": path.read_text(encoding="utf-8-sig"),
                        "count": result["data"]["count"],
                    }
                )
        return _response(result)


def _session_rows(service: Sessions) -> list[dict[str, Any]]:
    return [{**row, "id": str(row["id"])} for row in _service_data(service.list())]


def _session_name(service: Sessions, identifier: Any) -> str:
    if not isinstance(identifier, str):
        raise TransportError(ErrorCode.VALIDATION, "Session ID must be a string")
    for row in _session_rows(service):
        if row["id"] == identifier:
            return str(row["name"])
    raise TransportError(ErrorCode.NOT_FOUND, "Session not found")


def _session_result(result: dict[str, Any]) -> Any:
    data = _service_data(result)
    return _ok({**data, "id": str(data["id"])})


def _catalog_transfer(
    command: str, body: dict[str, Any], service: Any, identifier: int | None = None
) -> Any:
    with TemporaryDirectory(prefix="haru-catalog-") as folder:
        path = Path(folder) / (
            "stocks.csv" if identifier is not None else "catalog.json"
        )
        if command in {"load", "import-stocks"}:
            content = body.get("content")
            maximum = (
                _MAX_BASKET_TRANSFER_BYTES
                if isinstance(service, Baskets)
                else MAX_CSV_BYTES
            )
            if not isinstance(content, str) or len(content.encode("utf-8")) > maximum:
                raise TransportError(
                    ErrorCode.VALIDATION, f"Choose a file up to {maximum} bytes"
                )
            path.write_text(content, encoding="utf-8")
            result = (
                service.load(path)
                if identifier is None
                else service.import_stocks(identifier, path)
            )
            rows = _service_data(result)
            return (
                _ok({"loaded_count": len(rows)})
                if identifier is None
                else _ok(_basket_record(service, identifier))
            )
        if identifier is not None:
            result = service.export_stocks(identifier, path)
        elif isinstance(service, Baskets) and "ids" in body:
            result = service.save(path, _basket_ids(body["ids"]))
        else:
            result = service.save(path)
        data = _service_data(result)
        return _ok(
            {"content": path.read_text(encoding="utf-8"), "count": data["count"]}
        )


def _session_routes(router: APIRouter) -> None:
    """Expose session service operations using the browser's stable identities."""

    @router.get("/sessions")
    def list_sessions(request: Request) -> Any:
        return _ok(_session_rows(Sessions(request.app.state.persistence)))

    @router.post("/sessions")
    def save_session(request: Request, body: dict[str, Any]) -> Any:
        service = Sessions(request.app.state.persistence)
        fields = {key: value for key, value in body.items() if key != "id"}
        if "id" in body:
            result = service.edit(_session_name(service, body["id"]), fields)
            if result["success"]:
                result = {**result, "data": result["data"][0]}
        else:
            result = service.add(**fields)
        return _session_result(result)

    @router.post("/sessions/clone")
    def clone_session(request: Request, body: dict[str, Any]) -> Any:
        service = Sessions(request.app.state.persistence)
        return _session_result(
            service.clone(
                _session_name(service, body.get("session_id")),
                body.get("new_name", ""),
                minutes=body.get("timezone_offset", 0),
            )
        )

    @router.post("/sessions/delete")
    def delete_sessions(request: Request, body: dict[str, Any]) -> Any:
        service = Sessions(request.app.state.persistence)
        ids = body.get("session_ids")
        if not isinstance(ids, list) or not ids:
            raise TransportError(ErrorCode.VALIDATION, "Select sessions to delete")
        result = service.delete(
            [_session_name(service, item) for item in cast("Any", ids)]
        )
        return (
            _ok({"deleted": list(dict.fromkeys(cast("Any", ids)))})
            if result["success"]
            else _response(result)
        )

    @router.delete("/sessions/{identifier}")
    def delete_session(identifier: str, request: Request) -> Any:
        service = Sessions(request.app.state.persistence)
        result = service.delete(_session_name(service, identifier))
        return (
            _ok({"id": identifier, "deleted": True})
            if result["success"]
            else _response(result)
        )

    _session_element_route(router)

    _session_transfer_route(router)


def _session_element_route(router: APIRouter) -> None:
    @router.post("/sessions/{identifier}/elements")
    def session_element(identifier: str, request: Request, body: dict[str, Any]) -> Any:
        service = Sessions(request.app.state.persistence)
        name = _session_name(service, identifier)
        row = next(row for row in _session_rows(service) if row["id"] == identifier)
        windows = list(row["windows"])
        action, index = body.get("action"), body.get("index")
        if action == "add":
            windows.append(body.get("window"))
        elif action in {"update", "remove"}:
            if type(index) is not int or not 0 <= index < len(windows):
                raise TransportError(
                    ErrorCode.VALIDATION, "Select an existing interval"
                )
            if action == "update":
                windows[index] = body.get("window")
            else:
                windows.pop(index)
        else:
            raise TransportError(ErrorCode.VALIDATION, "Unknown interval operation")
        result = service.edit(name, windows=windows)
        if result["success"]:
            result = {**result, "data": result["data"][0]}
        return _session_result(result)


def _session_transfer_route(router: APIRouter) -> None:
    @router.post("/sessions/{command}")
    def session_transfer(command: str, request: Request, body: dict[str, Any]) -> Any:
        if command not in {"load", "save"}:
            raise TransportError(ErrorCode.NOT_FOUND, "Unknown session command")
        return _catalog_transfer(command, body, Sessions(request.app.state.persistence))


def _service_data(response: dict[str, Any]) -> Any:
    if not response["success"]:
        error: dict[str, Any] = response.get("error") or {}
        raise TransportError(
            ErrorCode(error.get("code", "internal")), response["message"]
        )
    return response["data"]


def _broker_stocks(gateway: HostPersistence, identifier: int) -> list[str]:
    return [
        row["TICKER"]
        for row in _rows(gateway, "datamgr_broker_stock", {"BROKER_ID": identifier})
    ]


def _broker_ui(row: dict[str, Any], gateway: HostPersistence) -> dict[str, Any]:
    stocks = _broker_stocks(gateway, row["id"]) if row["customized_stocks"] else []
    return {
        **row,
        "id": str(row["id"]),
        "timezone": row["server_timezone"],
        "stocks": stocks,
        "total_symbols": row["customized_instruments"],
        "total_sessions": row["customized_sessions"],
        "spread_model": {"model": "inherit"},
        "commission_model": {"model": "inherit"},
    }


def _selected_brokers(service: Brokers, ids: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(ids, list)
        or not ids
        or any(
            not isinstance(value, str) or not value.isdecimal() or int(value) < 1
            for value in cast("Any", ids)
        )
    ):
        raise TransportError(ErrorCode.VALIDATION, "Choose saved broker profiles")
    rows = {str(row["id"]): row for row in _service_data(service.list())}
    if any(value not in rows for value in cast("Any", ids)):
        raise TransportError(ErrorCode.NOT_FOUND, "Broker profile not found")
    return [rows[value] for value in dict.fromkeys(cast("Any", ids))]


def _broker_routes(router: APIRouter) -> None:
    """Install listing, CRUD, JSON transfer, and stock membership routes."""

    @router.get("/brokers")
    def listing(request: Request) -> Any:
        gateway = request.app.state.persistence
        return _ok(
            [_broker_ui(row, gateway) for row in _service_data(Brokers(gateway).list())]
        )

    _broker_save_route(router)

    @router.post("/brokers/edit")
    def edit(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        fields = body.get("updates")
        if not isinstance(fields, dict):
            raise TransportError(ErrorCode.VALIDATION, "Choose broker fields to edit")
        with gateway.transaction() as tx:
            service = Brokers(tx, manage_transactions=False)
            rows = _selected_brokers(service, body.get("ids"))
            fields = cast("dict[str, Any]", fields)
            _validate_broker_changes(tx, rows, fields)
            result = service.edit([row["name"] for row in rows], fields)
            _service_data(result)
        return _ok(
            [
                _broker_ui(row, gateway)
                for row in _service_data(Brokers(gateway).list())
                if str(row["id"]) in body["ids"]
            ]
        )

    @router.post("/brokers/delete")
    def delete(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        with gateway.transaction() as tx:
            service = Brokers(tx, manage_transactions=False)
            rows = _selected_brokers(service, body.get("ids"))
            for row in rows:
                _check_broker_unused(tx, row)
                _clear_broker_stocks(tx, row["id"])
            _service_data(service.delete([row["name"] for row in rows]))
        ids = [str(row["id"]) for row in rows]
        return _ok({"deleted_ids": ids, "deleted_count": len(ids)})

    _broker_transfer_routes(router)
    _broker_stock_routes(router)


def _broker_save_route(router: APIRouter) -> None:
    @router.post("/brokers")
    def save(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        fields = {key: value for key, value in body.items() if key != "id"}
        if "timezone" in fields:
            fields["server_timezone"] = fields.pop("timezone")
        # Accept inherited costs from older clients; there are no cost columns.
        for key in ("spread_model", "commission_model"):
            if fields.pop(key, {"model": "inherit"}) != {"model": "inherit"}:
                raise TransportError(
                    ErrorCode.VALIDATION, "Broker cost defaults are unavailable"
                )
        with gateway.transaction() as tx:
            service = Brokers(tx, manage_transactions=False)
            if "id" in body:
                rows = _selected_brokers(service, [body["id"]])
                _validate_broker_changes(tx, rows, fields)
                result = service.edit(rows[0]["name"], fields)
                row = _service_data(result)[0]
            else:
                result = service.add(**fields)
                row = _service_data(result)
        saved = next(
            item
            for item in _service_data(Brokers(gateway).list())
            if item["id"] == row["id"]
        )
        return _ok(_broker_ui(saved, gateway))


def _broker_transfer_routes(router: APIRouter) -> None:
    @router.post("/brokers/{command}")
    def transfer(command: str, request: Request, body: dict[str, Any]) -> Any:
        if command not in {"load", "save"}:
            raise TransportError(ErrorCode.NOT_FOUND, "Unknown broker operation")
        return _catalog_transfer(command, body, Brokers(request.app.state.persistence))


def _broker_stock_routes(router: APIRouter) -> None:
    @router.get("/brokers/{identifier}")
    def get(identifier: str, request: Request) -> Any:
        gateway = request.app.state.persistence
        return _ok(
            _broker_ui(_selected_brokers(Brokers(gateway), [identifier])[0], gateway)
        )

    @router.get("/brokers/{identifier}/stocks")
    def stocks(identifier: str, request: Request) -> Any:
        gateway = request.app.state.persistence
        _selected_brokers(Brokers(gateway), [identifier])
        return _ok(
            {
                "broker_id": identifier,
                "stocks": _broker_stocks(gateway, int(identifier)),
            }
        )

    @router.put("/brokers/{identifier}/stocks")
    def save_stocks(identifier: str, request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        values = body.get("stocks")
        if (
            not isinstance(values, list)
            or len(cast("Any", values)) > MAX_BROKER_STOCKS
            or any(
                not isinstance(value, str)
                or not value.strip()
                or len(value.strip()) > MAX_TICKER_LENGTH
                for value in cast("Any", values)
            )
        ):
            raise TransportError(ErrorCode.VALIDATION, "Choose valid stock tickers")
        values = list(
            dict.fromkeys(value.strip() for value in cast("list[str]", values))
        )
        with gateway.transaction() as tx:
            rows = _selected_brokers(Brokers(tx), [identifier])
            if rows[0]["is_system"]:
                raise TransportError(
                    ErrorCode.VALIDATION, "System broker profiles cannot be changed"
                )
            if not rows[0]["stockpicker_use"]:
                raise TransportError(
                    ErrorCode.VALIDATION, "Enable stock filtering first"
                )
            _clear_broker_stocks(tx, int(identifier))
            for start in range(0, len(values), 1000):
                _service_data(
                    tx.create_records(
                        "datamgr_broker_stock",
                        [
                            {"BROKER_ID": int(identifier), "TICKER": value}
                            for value in values[start : start + 1000]
                        ],
                    )
                )
        return _ok({"broker_id": identifier, "stocks": values, "count": len(values)})


def _check_broker_unused(gateway: HostPersistence, row: dict[str, Any]) -> None:
    broker_name = str(row.get("name", "")).strip()
    clean_name = (
        broker_name[2:-2].strip()
        if broker_name.startswith("[[") and broker_name.endswith("]]")
        else broker_name
    )
    for table, column, value in (
        ("datamgr_symbols", "broker_id", row["id"]),
        ("datamgr_sessions", "broker_id", row["id"]),
        ("datamgr_datasets", "broker", clean_name),
    ):
        data = _service_data(
            gateway.read_records(table, filters={column: value}, limit=1)
        )
        if data["records"]:
            raise TransportError(
                ErrorCode.CONFLICT,
                "Broker is used by symbols, sessions or saved datasets",
            )
    for alt_val in (str(row["id"]), broker_name):
        if alt_val and alt_val != clean_name:
            data = _service_data(
                gateway.read_records(
                    "datamgr_datasets", filters={"broker": alt_val}, limit=1
                )
            )
            if data["records"]:
                raise TransportError(
                    ErrorCode.CONFLICT,
                    "Broker is used by symbols, sessions or saved datasets",
                )


def _clear_broker_stocks(gateway: HostPersistence, identifier: int) -> None:
    while True:
        records = _service_data(
            gateway.read_records(
                "datamgr_broker_stock", filters={"BROKER_ID": identifier}, limit=1000
            )
        )["records"]
        if not records:
            return
        _service_data(
            gateway.delete_record(
                "datamgr_broker_stock",
                filters=[RecordFilter("ID", "in", [row["ID"] for row in records])],
            )
        )


def _validate_broker_changes(
    gateway: HostPersistence, rows: list[dict[str, Any]], fields: dict[str, Any]
) -> None:
    for row in rows:
        if fields.get("stockpicker_use") is False and row["customized_stocks"]:
            raise TransportError(
                ErrorCode.CONFLICT,
                "Remove broker stocks before disabling stock filtering",
            )
        if fields.get("mt_use") is False and (
            row["customized_instruments"] or row["customized_sessions"]
        ):
            raise TransportError(
                ErrorCode.CONFLICT, "Broker is used by symbols or sessions"
            )
        timezone = fields.get("server_timezone", row["server_timezone"])
        if timezone != row["server_timezone"]:
            broker_name = str(row.get("name", "")).strip()
            clean_name = (
                broker_name[2:-2].strip()
                if broker_name.startswith("[[") and broker_name.endswith("]]")
                else broker_name
            )
            for chk_val in (clean_name, str(row["id"]), broker_name):
                if not chk_val:
                    continue
                data = _service_data(
                    gateway.read_records(
                        "datamgr_datasets", filters={"broker": chk_val}, limit=1
                    )
                )
                if data["records"]:
                    raise TransportError(
                        ErrorCode.CONFLICT, "Broker timezone is used by saved datasets"
                    )


def _basket_ids(values: Any) -> list[int]:
    if (
        not isinstance(values, list)
        or not values
        or any(
            not isinstance(value, str)
            or not value.isascii()
            or not value.isdecimal()
            or int(value) < 1
            for value in cast("Any", values)
        )
    ):
        raise TransportError(ErrorCode.VALIDATION, "Select saved stock groups")
    return list(dict.fromkeys(int(value) for value in cast("list[str]", values)))


def _basket_ui(row: dict[str, Any]) -> dict[str, Any]:
    def date(value: int, missing: int) -> str | None:
        return (
            None
            if value == missing
            else (datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=value))
            .date()
            .isoformat()
        )

    return {
        **row,
        "id": str(row["id"]),
        "items": [
            {
                "symbol": item["ticker"],
                "date_from": date(item["date_from"], 0),
                "date_to": date(item["date_to"], -1),
                "date_from_ms": item["date_from"],
                "date_to_ms": item["date_to"],
            }
            for item in row["stocks"]
        ],
    }


def _basket_record(service: Baskets, identifier: int) -> dict[str, Any]:
    for row in _service_data(service.list()):
        if row["id"] == identifier:
            return _basket_ui(row)
    raise TransportError(ErrorCode.NOT_FOUND, "Stock group not found")


def _basket_jobs(request: Request, *, create: bool = False) -> Any:
    from app.host.jobs import JobManager

    with _BASKET_JOB_LOCK:
        jobs = getattr(request.app.state, "basket_jobs", None)
        if jobs is None and create:
            jobs = JobManager(
                persistence=request.app.state.persistence,
                max_workers=1,
                use_process_pool=False,
            )
            request.app.state.basket_jobs = jobs
    if jobs is None:
        raise TransportError(ErrorCode.NOT_FOUND, "No stock group update job")
    return jobs


def _basket_routes(router: APIRouter) -> None:
    @router.get("/baskets")
    def listing(request: Request) -> Any:
        return _ok(
            [
                _basket_ui(row)
                for row in _service_data(Baskets(request.app.state.persistence).list())
            ]
        )

    @router.post("/baskets")
    def save(request: Request, body: dict[str, Any]) -> Any:
        service = Baskets(request.app.state.persistence)
        fields = {k: body[k] for k in ("name", "description", "system") if k in body}
        if "id" in body:
            result = service.edit(_basket_ids([body["id"]]), fields)
            row = _service_data(result)[0]
        else:
            row = _service_data(service.add(**fields))
        return _ok(_basket_record(service, row["id"]))

    @router.post("/baskets/{command}")
    def action(command: str, request: Request, body: dict[str, Any]) -> Any:
        service = Baskets(request.app.state.persistence)
        if command == "delete":
            rows = _service_data(service.delete(_basket_ids(body.get("ids"))))
            return _ok(
                {
                    "deleted_ids": [str(row["id"]) for row in rows],
                    "deleted_count": len(rows),
                }
            )
        if command == "edit":
            fields = body.get("updates")
            if not isinstance(fields, dict):
                raise TransportError(
                    ErrorCode.VALIDATION, "Choose group fields to edit"
                )
            rows = _service_data(
                service.edit(
                    _basket_ids(body.get("ids")), cast("dict[str, Any]", fields)
                )
            )
            return _ok([_basket_record(service, row["id"]) for row in rows])
        if command == "update-data":
            ids = _basket_ids(body.get("ids"))
            return _response(
                Baskets(
                    service.gateway,
                    jobs=_basket_jobs(request, create=True),
                    logs=request.app.state.data_logs,
                ).update_data(ids)
            )
        if command in {"load", "save"}:
            return _catalog_transfer(command, body, service)
        raise TransportError(ErrorCode.NOT_FOUND, "Unknown stock group operation")

    _basket_stock_routes(router)
    _basket_job_routes(router)


def _basket_stock_routes(router: APIRouter) -> None:
    @router.get("/baskets/{identifier}/stocks")
    def stocks(identifier: str, request: Request) -> Any:
        service = Baskets(request.app.state.persistence)
        number = _basket_ids([identifier])[0]
        _service_data(service.list_stocks(number))
        return _ok(_basket_record(service, number))

    @router.put("/baskets/{identifier}/stocks")
    def edit(identifier: str, request: Request, body: dict[str, Any]) -> Any:
        service = Baskets(request.app.state.persistence)
        number = _basket_ids([identifier])[0]
        symbols = body.get("symbols")
        if not isinstance(symbols, list) or any(
            not isinstance(row, str) for row in cast("Any", symbols)
        ):
            raise TransportError(
                ErrorCode.VALIDATION, "Supply ticker;from;to membership lines"
            )
        _service_data(
            service.edit_stocks(number, "\n".join(cast("list[str]", symbols)))
        )
        return _ok(_basket_record(service, number))

    @router.post("/baskets/{identifier}/{command}")
    def transfer(
        identifier: str, command: str, request: Request, body: dict[str, Any]
    ) -> Any:
        if command not in {"import-stocks", "export-stocks"}:
            raise TransportError(ErrorCode.NOT_FOUND, "Unknown stock operation")
        return _catalog_transfer(
            command,
            body,
            Baskets(request.app.state.persistence),
            _basket_ids([identifier])[0],
        )


def _basket_job_routes(router: APIRouter) -> None:
    @router.get("/basket-jobs/{job_id}")
    @router.post("/basket-jobs/{job_id}/{action}")
    def job(job_id: str, request: Request, action: str | None = None) -> Any:
        jobs = _basket_jobs(request)
        record = jobs.get_job(job_id)
        if record is None or record.kind != "baskets.update_data":
            raise TransportError(
                ErrorCode.NOT_FOUND, "Stock group update job not found"
            )
        if request.method == "POST":
            handlers = {
                "pause": jobs.pause_job,
                "resume": jobs.resume_job,
                "stop": jobs.cancel_job,
            }
            if action not in handlers:
                raise TransportError(ErrorCode.NOT_FOUND, "Unknown job action")
            if not handlers[action](job_id):
                raise TransportError(
                    ErrorCode.CONFLICT, "Job cannot perform that action"
                )
            record = jobs.get_job(job_id)
        return _ok(record.to_dict())


def _log_routes(router: APIRouter) -> None:
    @router.get("/logs")
    def logs(
        request: Request, task_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> Any:
        return _response(
            request.app.state.data_logs.list(
                task_id=task_id, limit=limit, offset=offset
            )
        )

    @router.get("/logs/active")
    def active_logs(request: Request) -> Any:
        return _response(request.app.state.data_logs.list_active())

    @router.post("/logs/clear")
    def clear_logs(request: Request) -> Any:
        return _response(request.app.state.data_logs.clear())


def _help_routes(router: APIRouter) -> None:
    @router.get("/help")
    def get_help_guide(request: Request, topic: str = "overview") -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.get_topic(topic))

    @router.get("/help/topics")
    def list_help_topics(request: Request) -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.list_topics())

    @router.get("/help/tutorials")
    def list_help_tutorials(request: Request, topic: str | None = None) -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.list_tutorials(topic))

    @router.get("/help/articles")
    def list_help_articles(request: Request, topic: str | None = None) -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.list_articles(topic))

    @router.get("/help/search")
    def search_help(request: Request, query: str = "") -> Any:
        service = Help(request.app.state.persistence)
        return _response(service.search(query))


def _source_routes(router: APIRouter) -> None:
    @router.get("/sources/{provider}/{action}")
    @router.post("/sources/{provider}/{action}")
    async def source_command(
        provider: str, action: str, request: Request, body: dict[str, Any] | None = None
    ) -> Any:
        from app.workspace.data_manager.source_mt5 import bridge_action
        from app.workspace.data_manager.sources import Sources, capabilities

        try:
            if action == "capabilities":
                return _ok(capabilities(provider))
            if provider == "mt5" and (
                action == "status" or (action == "connect" and request.method == "POST")
            ):
                return _ok(await bridge_action(action, request.app))
            if action == "add" and request.method == "POST":
                return _response(
                    Sources(request.app.state.persistence).add(
                        provider, (body or {}).get("definitions", [])
                    )
                )
            raise TransportError(ErrorCode.VALIDATION, "Unknown source operation")
        except (ValueError, TypeError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error

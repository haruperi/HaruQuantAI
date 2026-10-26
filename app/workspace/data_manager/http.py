"""Authenticated Data Manager HTTP adapter for the browser workspace."""

from __future__ import annotations

import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.host.persistence import HostPersistence
from app.host.response import ErrorCode
from app.host.transport import TransportError, _require
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
DAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
CORE_TABS = {"data", "symbols", "sessions", "brokers", "custom-data"}
MAX_CSV_BYTES = 10_000_000


def _access(request: Request) -> None:
    """Apply the host's UI session and scope checks to domain requests."""
    _require(request, "data:read" if request.method == "GET" else "data:write")


def _response(result: dict[str, Any]) -> JSONResponse:
    """Keep service errors and HTTP status consistent with the host envelope."""
    statuses = {"validation": 422, "not_found": 404, "conflict": 409}
    body = {**result, "status": "success" if result["success"] else "error"}
    code = (
        200
        if result["success"]
        else statuses.get((result.get("error") or {}).get("code", "internal"), 503)
    )
    return JSONResponse(jsonable_encoder(body), status_code=code)


def _ok(data: Any) -> dict[str, Any]:
    return {"status": "success", "success": True, "data": data}


def _json(value: Any) -> dict[str, Any]:
    return json.loads(value) if isinstance(value, str) else value or {}


def _rows(gateway: HostPersistence) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset: int | None = 0
    while offset is not None:
        result = gateway.read_records("datamgr_symbols", limit=1000, offset=offset)
        if not result["success"]:
            raise TransportError(
                ErrorCode.UNAVAILABLE, "Unable to read the symbol catalog"
            )
        data = result["data"]
        rows.extend(data["records"])
        offset = data.get("pagination", {}).get("next_offset")
    return rows


def _ui(row: dict[str, Any]) -> dict[str, Any]:
    """Translate the persisted nested specification into existing browser fields."""
    price, volume, spread, swap, margin, trade = (
        _json(row.get(key))
        for key in ("price", "volume", "spread", "swap", "margin", "trade")
    )
    rollover = str(swap.get("rollover3days", "Wednesday")).upper()
    return {
        "id": str(row["id"]),
        "symbol": row["name"],
        "description": row.get("description") or "",
        "broker_id": row.get("broker_id") or 0,
        "data_type": row.get("data_type") or "",
        "point_value": price.get("point_value")
        if price.get("point_value") is not None
        else price.get("contract_size", 100000),
        "tick_size": price.get("tick_size", 0.0001),
        "tick_step": price.get("tick_step", 0.00001),
        "contract_size": price.get("contract_size", 100000),
        "pip_size": price.get("pip_size")
        if price.get("pip_size") is not None
        else price.get("tick_size", 0.0001),
        "margin_rate": margin.get("rate", 0),
        "decimals": price.get("digits", 5),
        "tick_value_in_money": price.get("tick_value", 0),
        "min_volume": volume.get("min", 0.01),
        "max_volume": volume.get("max", 100),
        "lot_step": volume.get("step", 0.01),
        "default_spread": spread.get("default", 0),
        "default_slippage": spread.get("slippage", 0),
        "min_distance": trade.get("min_distance", 0),
        "order_size_multiplier": volume.get("min", 0.01),
        "order_size_step": volume.get("step", 0.01),
        "commissions": trade.get("commission_settings")
        or str(row.get("commission") or 0),
        "swap_long": swap.get("long", 0),
        "swap_short": swap.get("short", 0),
        "swap_3day_day": DAYS.index(rollover) if rollover in DAYS else 3,
        "swap_settings": swap.get("settings"),
    }


def _updates(values: dict[str, Any]) -> dict[str, Any]:
    """Validate browser field values before invoking the symbol service."""
    numeric = {
        "broker_id",
        "point_value",
        "contract_size",
        "tick_size",
        "pip_size",
        "tick_step",
        "decimals",
        "tick_value_in_money",
        "min_volume",
        "max_volume",
        "lot_step",
        "margin_rate",
        "default_spread",
        "default_slippage",
        "min_distance",
        "order_size_multiplier",
        "order_size_step",
    }
    if not isinstance(values, dict):
        raise TransportError(ErrorCode.VALIDATION, "Invalid symbol field values")
    for key in numeric & values.keys():
        value = values[key]
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise TransportError(ErrorCode.VALIDATION, f"Invalid numeric field: {key}")
    try:
        return _map_updates(values)
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise TransportError(
            ErrorCode.VALIDATION, "Invalid symbol field values"
        ) from error


def _map_updates(values: dict[str, Any]) -> dict[str, Any]:
    """Map explicitly supplied browser fields to service fields."""
    direct = {
        "description",
        "data_type",
        "broker_id",
        "default_spread",
        "min_distance",
        "order_size_multiplier",
        "order_size_step",
    }
    result = {key: value for key, value in values.items() if key in direct}
    nested = {
        "price": {
            "point_value": "point_value",
            "contract_size": "contract_size",
            "tick_size": "tick_size",
            "pip_size": "pip_size",
            "tick_step": "tick_step",
            "decimals": "digits",
            "tick_value_in_money": "tick_value",
        },
        "volume": {"min_volume": "min", "max_volume": "max", "lot_step": "step"},
        "margin": {"margin_rate": "rate"},
        "spread": {"default_slippage": "slippage"},
    }
    for section, keys in nested.items():
        data = {
            target: values[source]
            for source, target in keys.items()
            if source in values and values[source] is not None
        }
        if data:
            result[section] = data
    if "commissions" in values:
        commission = json.loads(values["commissions"])
        result["commission"] = float(
            commission
            if isinstance(commission, (float, int))
            else commission["settings"]["value"]
        )
        result["trade"] = {"commission_settings": values["commissions"]}
    if "swap_settings" in values:
        swap = values["swap_settings"]
        result["swap"] = {
            "settings": swap,
            "long": swap["long"] if swap["use"] else 0,
            "short": swap["short"] if swap["use"] else 0,
            "mode": swap["type"],
            "rollover3days": swap["tripleSwapOn"].capitalize(),
        }
    return result


def _names(rows: list[dict[str, Any]], ids: list[str]) -> list[str]:
    found = {str(row["id"]): row["name"] for row in rows}
    if not ids or any(key not in found for key in ids):
        raise TransportError(ErrorCode.NOT_FOUND, "Select existing symbols")
    return list(dict.fromkeys(found[key] for key in ids))


def create_router() -> APIRouter:
    """Register browser workspace and symbol commands within their domain."""
    router = APIRouter(prefix="/api/v1/data", dependencies=[Depends(_access)])

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

    _session_routes(router)
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
    result = service.list()
    if not result["success"]:
        raise TransportError(ErrorCode.UNAVAILABLE, "Unable to read session catalog")
    return [{**row, "id": str(row["id"])} for row in result["data"]]


def _session_name(service: Sessions, identifier: Any) -> str:
    if not isinstance(identifier, str):
        raise TransportError(ErrorCode.VALIDATION, "Session ID must be a string")
    for row in _session_rows(service):
        if row["id"] == identifier:
            return str(row["name"])
    raise TransportError(ErrorCode.NOT_FOUND, "Session not found")


def _session_result(result: dict[str, Any]) -> Any:
    if not result["success"]:
        return _response(result)
    return _ok({**result["data"], "id": str(result["data"]["id"])})


def _session_transfer(command: str, body: dict[str, Any], service: Sessions) -> Any:
    with TemporaryDirectory(prefix="haru-sessions-") as folder:
        path = Path(folder) / "sessions.json"
        if command == "load":
            content = body.get("content")
            if (
                not isinstance(content, str)
                or len(content.encode("utf-8")) > MAX_CSV_BYTES
            ):
                raise TransportError(
                    ErrorCode.VALIDATION, "Choose a JSON file up to 10 MB"
                )
            path.write_text(content, encoding="utf-8")
            result = service.load(path)
            if result["success"]:
                return _ok({"loaded_count": len(result["data"])})
        else:
            result = service.save(path)
            if result["success"]:
                return _ok(
                    {
                        "content": path.read_text(encoding="utf-8"),
                        "count": result["data"]["count"],
                    }
                )
        return _response(result)


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
        result = service.delete([_session_name(service, item) for item in ids])
        return (
            _ok({"deleted": list(dict.fromkeys(ids))})
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
        return _session_transfer(command, body, Sessions(request.app.state.persistence))

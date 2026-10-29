"""HTTP routes and browser field mapping for Data Manager symbols."""

from __future__ import annotations

import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.host.persistence import HostPersistence
from app.core.host.transport import TransportError
from app.core.lib.responses import ErrorCode

from .feature import Symbols

DAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
MAX_CSV_BYTES = 10_000_000

__all__ = [
    "DAYS",
    "MAX_CSV_BYTES",
    "register_symbol_routes",
    "symbol_to_ui",
    "symbol_updates",
]


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


def _service_data(response: dict[str, Any]) -> Any:
    if not response["success"]:
        error: dict[str, Any] = response.get("error") or {}
        raise TransportError(
            ErrorCode(error.get("code", "internal")), response["message"]
        )
    return response["data"]


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


def symbol_to_ui(row: dict[str, Any]) -> dict[str, Any]:
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


def symbol_updates(values: dict[str, Any]) -> dict[str, Any]:
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
        "exchange",
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
    if values.get("expiry"):
        from datetime import date

        result.setdefault("trade", {})["contract_expiry"] = date.fromisoformat(
            values["expiry"]
        ).isoformat()
    return result


def register_symbol_routes(router: APIRouter) -> None:
    """Register symbol and instrument routes on the domain router."""

    @router.get("/instruments")
    @router.get("/symbols")
    def list_symbols(request: Request) -> dict[str, Any]:
        return _ok([symbol_to_ui(row) for row in _rows(request.app.state.persistence)])

    @router.post("/instruments")
    @router.post("/symbols")
    def add_symbol(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        name = str(body.get("symbol") or "").strip()
        datasource = str(body.get("datasource") or "SQ default").strip()
        result = Symbols(gateway).add(
            name=name, datasource=datasource, **symbol_updates(body)
        )
        if not result["success"]:
            return _response(result)
        saved = result["data"]["name"]
        return _ok(
            symbol_to_ui(next(row for row in _rows(gateway) if row["name"] == saved))
        )

    @router.post("/instruments/{command}")
    @router.post("/symbols/{command}")
    def symbol_command(command: str, request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        return _execute(command, body, Symbols(gateway), gateway)


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
            return _ok(
                symbol_to_ui(
                    next(row for row in _rows(gateway) if row["name"] == saved)
                )
            )
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
        else service.edit(names or [], updates=symbol_updates(body["updates"]))
    )
    if result["success"]:
        return _ok(
            {
                "updated_count": len(result["data"]),
                "symbols": [
                    symbol_to_ui(row)
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

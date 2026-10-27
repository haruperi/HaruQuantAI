"""HTTP routes and data adapters for Data Manager broker profiles."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.host.persistence import HostPersistence, RecordFilter
from app.host.response import ErrorCode
from app.host.transport import TransportError

from .feature import Brokers

MAX_CSV_BYTES = 10_000_000
MAX_BROKER_STOCKS = 10000
MAX_TICKER_LENGTH = 50

__all__ = [
    "MAX_BROKER_STOCKS",
    "MAX_CSV_BYTES",
    "MAX_TICKER_LENGTH",
    "register_broker_routes",
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


def _service_data(response: dict[str, Any]) -> Any:
    if not response["success"]:
        error: dict[str, Any] = response.get("error") or {}
        raise TransportError(
            ErrorCode(error.get("code", "internal")), response["message"]
        )
    return response["data"]


def _rows(
    gateway: HostPersistence,
    table: str = "datamgr_broker_stock",
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
        "spread_model": row.get("spread_model", {"model": "inherit"}),
        "commission_model": row.get("commission_model", {"model": "inherit"}),
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


def _broker_transfer(command: str, body: dict[str, Any], service: Brokers) -> Any:
    with TemporaryDirectory(prefix="haru-catalog-") as folder:
        path = Path(folder) / "catalog.json"
        if command == "load":
            content = body.get("content")
            if (
                not isinstance(content, str)
                or len(content.encode("utf-8")) > MAX_CSV_BYTES
            ):
                raise TransportError(
                    ErrorCode.VALIDATION, f"Choose a file up to {MAX_CSV_BYTES} bytes"
                )
            path.write_text(content, encoding="utf-8")
            result = service.load(path)
            rows = _service_data(result)
            return _ok({"loaded_count": len(rows)})
        result = service.save(path)
        data = _service_data(result)
        return _ok(
            {"content": path.read_text(encoding="utf-8"), "count": data["count"]}
        )


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


def register_broker_routes(router: APIRouter) -> None:
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

    from .imports import register_broker_import_routes

    register_broker_import_routes(router)
    _broker_transfer_routes(router)
    _broker_stock_routes(router)


def _broker_save_route(router: APIRouter) -> None:
    @router.post("/brokers")
    def save(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        fields = {key: value for key, value in body.items() if key != "id"}
        if "timezone" in fields:
            fields["server_timezone"] = fields.pop("timezone")
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
        return _broker_transfer(command, body, Brokers(request.app.state.persistence))


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

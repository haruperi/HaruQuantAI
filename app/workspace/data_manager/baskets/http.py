"""HTTP routes and job integration for Data Manager baskets (stock groups)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.host.response import ErrorCode
from app.host.transport import TransportError

from .feature import Baskets

_BASKET_JOB_LOCK = Lock()
_MAX_BASKET_TRANSFER_BYTES = 20 * 1024 * 1024
MAX_CSV_BYTES = 10_000_000

__all__ = [
    "MAX_CSV_BYTES",
    "_BASKET_JOB_LOCK",
    "_MAX_BASKET_TRANSFER_BYTES",
    "register_basket_routes",
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


def _catalog_transfer(
    command: str, body: dict[str, Any], service: Baskets, identifier: int | None = None
) -> Any:
    with TemporaryDirectory(prefix="haru-catalog-") as folder:
        path = Path(folder) / (
            "stocks.csv" if identifier is not None else "catalog.json"
        )
        if command in {"load", "import-stocks"}:
            content = body.get("content")
            maximum = _MAX_BASKET_TRANSFER_BYTES
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
        elif "ids" in body:
            result = service.save(path, _basket_ids(body["ids"]))
        else:
            result = service.save(path)
        data = _service_data(result)
        return _ok(
            {"content": path.read_text(encoding="utf-8"), "count": data["count"]}
        )


def register_basket_routes(router: APIRouter) -> None:
    """Register stock group (basket) routes on the domain router."""

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

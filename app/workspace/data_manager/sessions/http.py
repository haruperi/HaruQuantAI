"""HTTP routes for Data Manager trading sessions."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.host.response import ErrorCode
from app.host.transport import TransportError

from .feature import Sessions

MAX_CSV_BYTES = 10_000_000

__all__ = [
    "MAX_CSV_BYTES",
    "register_session_routes",
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


def _session_transfer(command: str, body: dict[str, Any], service: Sessions) -> Any:
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


def register_session_routes(router: APIRouter) -> None:
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
        return _session_transfer(command, body, Sessions(request.app.state.persistence))

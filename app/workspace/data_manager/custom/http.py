"""HTTP routes and job integration for Data Manager custom indicators."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.host.transport import TransportError
from app.host.response import ErrorCode

from .feature import CustomData

_CUSTOM_JOB_LOCK = Lock()


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


def _custom_jobs(request: Request, *, create: bool = False) -> Any:
    """Reuse the application-owned data-operation pool, preserving injected managers."""
    jobs = getattr(request.app.state, "custom_jobs", None) or getattr(
        request.app.state, "download_jobs", None
    )
    if jobs is None and create:
        from app.workspace.data_manager.sources.download_jobs import manager

        jobs = manager(request)
    return jobs


def _custom_service(
    request: Request, *, with_jobs: bool = False, create_jobs: bool = False
) -> CustomData:
    jobs = (
        _custom_jobs(request, create=create_jobs)
        if (with_jobs or create_jobs)
        else None
    )
    logs = getattr(request.app.state, "data_logs", None)
    return CustomData(request.app.state.persistence, jobs=jobs, logs=logs)


def register_custom_routes(router: APIRouter) -> None:
    """Register all external indicator routes on the domain router."""
    _custom_crud_routes(router)
    _custom_preview_routes(router)
    _custom_import_routes(router)
    _custom_format_routes(router)
    _custom_export_routes(router)
    _custom_transfer_routes(router)
    _custom_job_routes(router)


def _custom_crud_routes(router: APIRouter) -> None:
    @router.get("/custom-data")
    def list_custom_data(request: Request) -> Any:
        return _response(_custom_service(request).list())

    @router.post("/custom-data")
    def add_custom_data(request: Request, body: dict[str, Any]) -> Any:
        service = _custom_service(request)
        return _response(
            service.add(
                str(body.get("name") or "").strip(),
                values=body.get("values", []),
                data_type=body.get("data_type", "custom"),
                timeframe=body.get("timeframe", "D1"),
                system=bool(body.get("system", False)),
            )
        )

    @router.post("/custom-data/edit")
    def edit_custom_data(request: Request, body: dict[str, Any]) -> Any:
        name = str(body.get("indicator_name") or body.get("name") or "").strip()
        updates = body.get("updates")
        if not isinstance(updates, dict):
            updates = {
                k: v
                for k, v in body.items()
                if k in {"name", "values", "data_type", "timeframe"}
            }
        return _response(_custom_service(request).edit(name, updates))

    @router.post("/custom-data/delete")
    @router.post("/custom-data/remove")
    def delete_custom_data(request: Request, body: dict[str, Any]) -> Any:
        names = body.get("names", body.get("indicator_names", []))
        return _response(_custom_service(request).delete(names))

    @router.post("/custom-data/clear")
    def clear_custom_data(request: Request, body: dict[str, Any]) -> Any:
        names = body.get("names", body.get("indicator_names", []))
        return _response(_custom_service(request).clear(names))

    @router.get("/custom-data/review")
    @router.get("/custom-data/{name}/records")
    def review_custom_data(
        request: Request,
        name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Any:
        target = name or request.query_params.get("name") or ""
        return _response(
            _custom_service(request).review_data(target, limit=limit, offset=offset)
        )


def _custom_preview_routes(router: APIRouter) -> None:
    @router.post("/custom-data/recognize")
    def recognize_custom_data(request: Request, body: dict[str, Any]) -> Any:
        service = _custom_service(request)
        if "file_path" in body:
            return _response(service.recognize_from_file(body["file_path"]))
        content = body.get("content")
        filename = body.get("filename", "indicator.json")
        if not isinstance(content, str):
            raise TransportError(ErrorCode.VALIDATION, "Supply content or file_path")
        with TemporaryDirectory(prefix="haru-custom-recognize-") as folder:
            path = Path(folder) / filename
            path.write_text(content, encoding="utf-8")
            return _response(service.recognize_from_file(path))

    @router.post("/custom-data/import-preview")
    def preview_custom_data(request: Request, body: dict[str, Any]) -> Any:
        name = str(body.get("indicator_name") or body.get("name") or "").strip()
        limit = int(body.get("limit", 20))
        service = _custom_service(request)
        options = {
            k: v
            for k, v in body.items()
            if k
            in {
                "separator",
                "date_format",
                "skip_rows",
                "skip_columns",
                "columns",
                "error_handling",
            }
        }
        format_name = body.get("format_name")
        if "file_path" in body:
            return _response(
                service.import_preview(
                    name,
                    body["file_path"],
                    format_name=format_name,
                    limit=limit,
                    **options,
                )
            )
        content = body.get("content")
        if not isinstance(content, str):
            raise TransportError(ErrorCode.VALIDATION, "Supply content or file_path")
        with TemporaryDirectory(prefix="haru-custom-preview-") as folder:
            path = Path(folder) / "preview.csv"
            path.write_text(content, encoding="utf-8")
            return _response(
                service.import_preview(
                    name,
                    path,
                    format_name=format_name,
                    limit=limit,
                    **options,
                )
            )

    @router.get("/custom-data/import-info")
    def import_info(request: Request) -> Any:
        return _response(_custom_service(request).import_get_info())


def _custom_import_routes(router: APIRouter) -> None:
    @router.post("/custom-data/import")
    def import_custom_data(request: Request, body: dict[str, Any]) -> Any:
        name = str(body.get("indicator_name") or body.get("name") or "").strip()
        background = bool(body.get("background", False))
        service = _custom_service(request, with_jobs=background, create_jobs=background)
        options = {
            k: v
            for k, v in body.items()
            if k
            in {
                "separator",
                "date_format",
                "skip_rows",
                "skip_columns",
                "columns",
                "error_handling",
            }
        }
        format_name = body.get("format_name")
        replace = bool(body.get("replace", False))
        if "file_path" in body:
            return _response(
                service.import_data(
                    name,
                    body["file_path"],
                    format_name=format_name,
                    replace=replace,
                    **options,
                )
            )
        content = body.get("content")
        if not isinstance(content, str):
            raise TransportError(ErrorCode.VALIDATION, "Supply content or file_path")
        with TemporaryDirectory(prefix="haru-custom-import-") as folder:
            path = Path(folder) / "data.csv"
            path.write_text(content, encoding="utf-8")
            return _response(
                service.import_data(
                    name,
                    path,
                    format_name=format_name,
                    replace=replace,
                    **options,
                )
            )


def _custom_format_routes(router: APIRouter) -> None:
    @router.post("/custom-data/formats")
    def add_format(request: Request, body: dict[str, Any]) -> Any:
        name = str(body.get("name") or "").strip()
        config = cast(
            "dict[str, Any]",
            body.get("config") if isinstance(body.get("config"), dict) else body,
        )
        return _response(_custom_service(request).add_import_format(name, config))

    @router.post("/custom-data/formats/edit")
    def edit_format(request: Request, body: dict[str, Any]) -> Any:
        name = str(body.get("name") or "").strip()
        config = cast(
            "dict[str, Any]",
            body.get("config") if isinstance(body.get("config"), dict) else body,
        )
        return _response(_custom_service(request).edit_import_format(name, config))

    @router.delete("/custom-data/formats/{name}")
    def delete_format(name: str, request: Request) -> Any:
        return _response(_custom_service(request).delete_import_format(name))


def _custom_export_routes(router: APIRouter) -> None:
    @router.post("/custom-data/export")
    def export_values(request: Request, body: dict[str, Any]) -> Any:
        name = str(body.get("indicator_name") or body.get("name") or "").strip()
        service = _custom_service(request)
        if "csv_path" in body:
            return _response(service.export_values(name, body["csv_path"]))
        with TemporaryDirectory(prefix="haru-custom-export-") as folder:
            path = Path(folder) / f"{name}.csv"
            res = service.export_values(name, path)
            if not res["success"]:
                return _response(res)
            return _ok(
                {
                    "content": path.read_text(encoding="utf-8-sig"),
                    "count": res["data"]["count"],
                }
            )

    @router.post("/custom-data/update-cot")
    def update_cot(request: Request, body: dict[str, Any] | None = None) -> Any:
        years = (body or {}).get("years")
        return _response(_custom_service(request).update_cot(years=years))


def _custom_transfer_routes(router: APIRouter) -> None:
    @router.post("/custom-data/save")
    def save_definitions(request: Request, body: dict[str, Any]) -> Any:
        service = _custom_service(request)
        names = body.get("names", body.get("indicators"))
        if "json_path" in body:
            return _response(service.save(body["json_path"], names=names))
        with TemporaryDirectory(prefix="haru-custom-save-") as folder:
            path = Path(folder) / "indicators.json"
            res = service.save(path, names=names)
            if not res["success"]:
                return _response(res)
            return _ok(
                {
                    "content": path.read_text(encoding="utf-8"),
                    "count": res["data"]["count"],
                }
            )

    @router.post("/custom-data/load")
    def load_definitions(request: Request, body: dict[str, Any]) -> Any:
        service = _custom_service(request)
        on_conflict = str(body.get("on_conflict", "error"))
        if "json_path" in body:
            return _response(service.load(body["json_path"], on_conflict=on_conflict))
        content = body.get("content")
        if not isinstance(content, str):
            raise TransportError(ErrorCode.VALIDATION, "Supply content or json_path")
        with TemporaryDirectory(prefix="haru-custom-load-") as folder:
            path = Path(folder) / "load.json"
            path.write_text(content, encoding="utf-8")
            return _response(service.load(path, on_conflict=on_conflict))


def _custom_job_routes(router: APIRouter) -> None:
    @router.get("/custom-data-jobs/{job_id}")
    @router.post("/custom-data-jobs/{job_id}/{action}")
    def custom_job(job_id: str, request: Request, action: str | None = None) -> Any:
        service = _custom_service(request, with_jobs=True)
        if request.method == "POST":
            if action not in {"pause", "resume", "stop"}:
                raise TransportError(ErrorCode.NOT_FOUND, "Unknown job action")
            return _response(service.import_action(job_id, action))
        if service.jobs is None:
            raise TransportError(ErrorCode.NOT_FOUND, "No custom import job manager")
        record = service.jobs.get_job(job_id)
        if record is None or record.kind != "custom.import":
            raise TransportError(ErrorCode.NOT_FOUND, "Custom import job not found")
        return _ok(record.to_dict())

"""Backend-owned Dukascopy download jobs and truthful progress/control endpoints."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, cast

from fastapi import APIRouter, Request

from app.host.jobs import JobContext, JobManager
from app.host.response import ErrorCode
from app.host.transport import TransportError
from app.include.market_storage import safe_component
from app.workspace.data_manager.data import require_data

from .dukascopy import Dukascopy

_LOCK = Lock()
_MONTHS = 12


def manager(request: Request) -> JobManager:
    """Lazily allocate one application-owned worker pool."""
    with _LOCK:
        if not hasattr(request.app.state, "download_jobs"):
            # A new application has no workers for persisted downloads. Reconcile
            # only this manager's jobs, never another workspace's live workers.
            gateway = request.app.state.persistence
            for kind in (
                "dukascopy.download",
                "market.download",
                "market.import",
                "market.export",
                "market.clone",
                "custom.import",
                "custom.cot",
            ):
                for status in ("QUEUED", "RUNNING", "PAUSED"):
                    while True:
                        rows = require_data(
                            gateway.read_records(
                                "host_jobs",
                                filters={"kind": kind, "status": status},
                            )
                        )["records"]
                        if not rows:
                            break
                        for row in rows:
                            if kind == "market.import":
                                from .files import _cleanup_inputs

                                _cleanup_inputs(
                                    str(
                                        Path(tempfile.gettempdir())
                                        / (
                                            "haru-history-import-"
                                            + safe_component(row["job_id"])
                                        )
                                    )
                                )
                            require_data(
                                gateway.update_record(
                                    "host_jobs",
                                    {
                                        "status": "INTERRUPTED",
                                        "message": "Interrupted by host restart",
                                        "finished_at_utc": datetime.now(
                                            UTC
                                        ).isoformat(),
                                        "error_message": (
                                            "Download worker ended when the backend "
                                            "restarted. Start a new download."
                                        ),
                                    },
                                    filters={"job_id": row["job_id"]},
                                )
                            )
            request.app.state.download_jobs = JobManager(
                persistence=request.app.state.persistence,
                max_workers=2,
                use_process_pool=False,
            )
    return cast("JobManager", request.app.state.download_jobs)


def start_download(request: Request, body: dict[str, Any]) -> dict[str, Any]:
    """Validate a complete request before accepting a background job."""
    service = Dukascopy(request.app.state.persistence, logs=request.app.state.data_logs)
    targets = body.get("targets") or [body]
    lower = service.parse_date_bound(body.get("date_from"))
    upper = service.parse_date_bound(body.get("date_to"), is_end=True)
    mode = body.get("download_type", "cdn")
    overwrite = body.get("overwrite", False)
    if (
        not isinstance(targets, list)
        or not targets
        or lower is None
        or upper is None
        or lower > upper
        or not isinstance(overwrite, bool)
        or mode not in ("standard", "cdn")
    ):
        raise TransportError(
            ErrorCode.VALIDATION,
            "Choose targets, valid dates, overwrite and mode (standard or cdn)",
        )
    confirmed = []
    seen = set()
    for target in targets:
        if not isinstance(target, dict):
            raise TransportError(ErrorCode.VALIDATION, "Invalid download target")
        symbol = str(target.get("symbol", "")).upper()
        timeframe = str(target.get("timeframe", "M1")).upper()
        if timeframe not in ("M1", "TICK"):
            raise TransportError(ErrorCode.VALIDATION, "Choose M1 or TICK")
        row = _target(service, symbol, timeframe)
        if row["id"] not in seen:
            confirmed.append(row)
            seen.add(row["id"])
    return (
        manager(request)
        .submit_job(
            _run,
            service,
            confirmed,
            lower,
            upper,
            mode=mode,
            overwrite=overwrite,
            owner="data-manager",
            kind="dukascopy.download",
            executor_kind="thread",
            pass_context=True,
        )
        .to_dict()
    )


def _target(service: Dukascopy, symbol: str, timeframe: str) -> dict[str, Any]:
    try:
        safe_component(symbol)
        return service.catalog_record(symbol, timeframe)
    except ValueError as error:
        raise TransportError(ErrorCode.VALIDATION, str(error)) from error


def _intervals(
    start: datetime, stop: datetime, timeframe: str
) -> list[tuple[datetime, datetime]]:
    result = []
    current = start
    while current <= stop:
        if timeframe == "TICK":
            boundary = current.replace(minute=0, second=0, microsecond=0) + timedelta(
                hours=1
            )
        else:
            boundary = datetime(
                current.year + (current.month == _MONTHS),
                current.month % _MONTHS + 1,
                1,
                tzinfo=UTC,
            )
        end = min(stop, boundary - timedelta(microseconds=1))
        result.append((current, end))
        current = boundary
    return result


def _run(
    context: JobContext,
    service: Dukascopy,
    targets: list[dict[str, Any]],
    start: datetime,
    stop: datetime,
    *,
    mode: str,
    overwrite: bool,
) -> dict[str, Any]:
    units = [
        (row, lower, upper)
        for row in targets
        for lower, upper in _intervals(start, stop, row["timeframe"])
    ]
    logs = service.logs
    completed = []
    if logs is not None:
        logs.record_progress(
            context.job_id, progress=0, message="Dukascopy download started"
        )
    try:
        for index, (row, lower, upper) in enumerate(units):
            context.wait_if_paused()
            scope = _ChunkContext(context, index, len(units))
            result = service.download(
                row["symbol"],
                timeframe=row["timeframe"],
                underlying=row["underlying"],
                broker=row["broker"],
                date_from=lower,
                date_to=upper,
                download_type=mode,
                overwrite=overwrite,
                context=scope,
            )
            context.raise_if_cancelled()
            if not result["success"]:
                # Skip only genuine closed-market intervals.
                if result.get("error", {}).get("code") != "not_found":
                    require_data(result)
            else:
                completed.append(result["data"])
            progress = 100 * (index + 1) / len(units)
            context.report_progress(progress, f"{row['symbol']} {upper.date()}")
            if logs is not None:
                logs.record_progress(
                    context.job_id,
                    progress=min(progress, 99),
                    message=f"Downloaded {row['symbol']} through {upper.date()}",
                )
    except BaseException:
        if logs is not None:
            logs.record_progress(
                context.job_id,
                progress=-1,
                level="error",
                message="Download stopped or failed; committed intervals retained",
            )
        raise
    if logs is not None:
        logs.record_progress(
            context.job_id, progress=100, message="Dukascopy download completed"
        )
    return {
        "completed_intervals": len(completed),
        "datasets": [row["id"] for row in targets],
    }


class _ChunkContext:
    def __init__(self, context: JobContext, index: int, total: int) -> None:
        self.context, self.index, self.total = context, index, total

    def wait_if_paused(self) -> None:
        self.context.wait_if_paused()

    def raise_if_cancelled(self) -> None:
        self.context.raise_if_cancelled()

    def report_progress(self, progress: float, message: str = "") -> None:
        self.context.report_progress(
            100 * (self.index + progress / 100) / self.total, message
        )


def register_download_jobs(router: APIRouter) -> None:
    """Expose persisted job status and real pause/resume/stop controls."""

    @router.get("/download-jobs/{job_id}")
    @router.post("/download-jobs/{job_id}/{action}")
    def job(request: Request, job_id: str, action: str | None = None) -> Any:
        jobs = manager(request)
        record = jobs.get_job(job_id)
        if (
            record is None
            or record.owner != "data-manager"
            or record.kind
            not in (
                "dukascopy.download",
                "market.download",
                "market.import",
                "market.export",
                "market.clone",
                "custom.import",
                "custom.cot",
            )
        ):
            raise TransportError(ErrorCode.NOT_FOUND, "Download job not found")
        if request.method == "POST":
            controls = {
                "pause": jobs.pause_job,
                "resume": jobs.resume_job,
                "stop": jobs.cancel_job,
            }
            if action not in controls:
                raise TransportError(ErrorCode.VALIDATION, "Unknown job control")
            if not controls[action](job_id):
                raise TransportError(
                    ErrorCode.CONFLICT, "Job cannot perform that action"
                )
            record = jobs.get_job(job_id)
        if record is None:
            raise TransportError(ErrorCode.NOT_FOUND, "Download job not found")
        if record.kind == "market.import" and record.status == "CANCELLED":
            from .files import _cleanup_inputs

            _cleanup_inputs(
                str(
                    Path(tempfile.gettempdir())
                    / ("haru-history-import-" + safe_component(job_id))
                )
            )
        data = record.to_dict()
        if (
            record.kind == "market.export"
            and record.status == "COMPLETED"
            and data.get("result") is None
        ):
            import json

            from app.workspace.data_manager.data.exports import ARTIFACT_ROOT

            manifest = ARTIFACT_ROOT / safe_component(job_id) / "manifest.json"
            if manifest.is_file():
                data["result"] = json.loads(manifest.read_text(encoding="utf-8"))
        return {"success": True, "status": "success", "data": data}

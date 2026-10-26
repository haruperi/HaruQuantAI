"""Backend-owned downloads for historical data sources beyond Dukascopy."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.host.jobs import JobContext
from app.host.response import ErrorCode
from app.host.transport import TransportError
from app.workspace.data_manager.download_jobs import manager
from app.workspace.data_manager.dukascopy import Dukascopy
from app.workspace.data_manager.sources import Sources, provider_id


def start_source_download(request: Request, body: dict[str, Any]) -> dict[str, Any]:
    """Validate persisted targets before accepting a real download job."""
    service = Sources(request.app.state.persistence)
    try:
        records, lower, upper, overwrite = _validate(service, body)
    except (ValueError, TypeError) as error:
        raise TransportError(ErrorCode.VALIDATION, str(error)) from error
    return (
        manager(request)
        .submit_job(
            _run,
            service,
            records,
            lower,
            upper,
            overwrite=overwrite,
            logs=request.app.state.data_logs,
            owner="data-manager",
            kind="market.download",
            executor_kind="thread",
            pass_context=True,
        )
        .to_dict()
    )


_MAX_TARGETS = 1000


def _validate(
    service: Sources, body: dict[str, Any]
) -> tuple[list[str], Any, Any, bool]:
    targets = body.get("targets")
    lower = Dukascopy.parse_date_bound(body.get("date_from"))
    upper = Dukascopy.parse_date_bound(body.get("date_to"), is_end=True)
    overwrite = body.get("overwrite", False)
    if not isinstance(targets, list) or not 1 <= len(targets) <= _MAX_TARGETS:
        raise ValueError("Choose between one and 1,000 datasets")
    if (
        lower is None
        or upper is None
        or lower > upper
        or not isinstance(overwrite, bool)
    ):
        raise ValueError("Choose valid dates and overwrite option")
    records = []
    for target in targets:
        if not isinstance(target, dict):
            raise TypeError("Invalid download target")
        dataset_id = target.get("id")
        if not dataset_id:
            source = provider_id(body.get("provider", ""))
            symbol = str(target.get("symbol", "")).upper()
            timeframe = str(target.get("timeframe", "M1")).upper()
            dataset_id = f"{source}:{symbol}:{timeframe}"
        row = service.record(str(dataset_id))
        if row["id"] not in records:
            records.append(row["id"])
    return records, lower, upper, overwrite


def _run(
    context: JobContext,
    service: Sources,
    targets: list[str],
    lower: Any,
    upper: Any,
    *,
    overwrite: bool,
    logs: Any,
) -> dict[str, Any]:
    completed = []
    logs.record_progress(
        context.job_id, progress=0, message="Historical download started"
    )
    try:
        for index, dataset_id in enumerate(targets):
            completed.append(
                service.download(
                    dataset_id,
                    lower,
                    upper,
                    overwrite=overwrite,
                    context=TargetContext(context, index, len(targets)),
                )
            )
        logs.record_progress(
            context.job_id, progress=100, message="Historical download completed"
        )
    except BaseException:
        logs.record_progress(
            context.job_id,
            progress=-1,
            level="error",
            message="Download stopped or failed; committed intervals retained",
        )
        raise
    return {"datasets": targets, "completed": len(completed)}


class TargetContext:
    """Map per-dataset progress onto an entire multi-source batch."""

    def __init__(self, context: JobContext, index: int, total: int) -> None:
        self.context, self.index, self.total = context, index, total

    def wait_if_paused(self) -> None:
        """Wait cooperatively between intervals."""
        self.context.wait_if_paused()

    def raise_if_cancelled(self) -> None:
        """Abort work before publication."""
        self.context.raise_if_cancelled()

    def report_progress(self, progress: float, message: str = "") -> None:
        """Report real progress across selected datasets."""
        self.context.report_progress(
            100 * (self.index + progress / 100) / self.total, message
        )

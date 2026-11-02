"""Persist history clones with explicit source and clock lineage."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd  # type: ignore[import-untyped]
from fastapi import APIRouter, Request

from app.core.data.market_storage import safe_component
from app.core.host.transport import TransportError
from app.core.lib.responses import ErrorCode

from .partition_files import dataset_lock
from .review import DatasetReview
from .storage import publish_frame, require_data

_MAX_SHIFT = 23
_WEEKDAYS = 5


def clone_to_timezone(
    context: Any, gateway: Any, body: dict[str, Any], logs: Any
) -> dict[str, Any]:
    """Copy confirmed recorded prices; fixed clock shifts and zone display differ."""
    source = DatasetReview(gateway, body["dataset_id"])
    with dataset_lock(Path(source.record["path"]), context):
        source = DatasetReview(gateway, body["dataset_id"])
        frame = source.frame()
    if frame.empty:
        raise ValueError("Cannot clone empty history")
    mode = body.get("timezone_type", "shift")
    shift = body.get("shift_hours", 0)
    if (
        mode not in {"shift", "zone"}
        or type(shift) not in {float, int}
        or not -_MAX_SHIFT <= shift <= _MAX_SHIFT
    ):
        raise ValueError("Choose a valid clock shift or timezone")
    zone = body.get("timezone") or "UTC"
    ZoneInfo(zone)
    label = str(shift).replace(".", "-") if mode == "shift" else zone.rsplit("/", 1)[-1]
    postfix = (
        str(body.get("postfix") or "_{timeframe}_{cloneTime}")
        .replace("{timeframe}", source.record["timeframe"])
        .replace("{cloneTime}", label)
    )
    symbol = safe_component(source.record["symbol"] + postfix)
    identifier = f"{source.record['source']}:{symbol}:{source.record['timeframe']}"
    if require_data(
        gateway.read_records("datamgr_datasets", filters={"id": identifier}, limit=1)
    )["records"]:
        raise ValueError("Clone name already exists; choose another postfix")
    if mode == "shift":
        frame.index += pd.Timedelta(hours=shift)
    if body.get("remove_weekends"):
        local = frame.index if mode == "shift" else frame.index.tz_convert(zone)
        frame = frame[local.weekday < _WEEKDAYS]
    if frame.empty:
        raise ValueError("No observations remain after filtering")
    now = datetime.now(UTC).isoformat()
    lineage = json.loads(source.record["lineage_json"])
    lineage.update(
        partitions=[],
        source_dataset=source.record["id"],
        source_revision=source.record["updated_at"],
        clock_transform={
            "type": mode,
            "hours": shift if mode == "shift" else 0,
            "display_timezone": zone,
            "shifted_labels": mode == "shift",
        },
    )
    record = {
        **source.record,
        "id": identifier,
        "symbol": symbol,
        "bars": 0,
        "date_from": "",
        "date_to": "",
        "timezone": "UTC" if mode == "shift" else zone,
        "created_at": now,
        "updated_at": now,
        "lineage_json": json.dumps(lineage),
    }
    context.wait_if_paused()
    context.raise_if_cancelled()
    result = publish_frame(
        gateway,
        Path(source.record["path"]).parent.parent,
        record,
        frame,
        lineage["tick_size"],
        context=context,
    )
    logs.record_progress(
        context.job_id, progress=100, message=f"Published real history clone {symbol}"
    )
    return result


def register_transform_routes(router: APIRouter) -> None:
    """Submit clock clones to the existing owned worker pool."""
    from app.workspace.data_manager.logs import Logs
    from app.workspace.data_manager.sources.download_jobs import manager

    @router.post("/datasets/clone-timezone")
    def clone(request: Request, body: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(body.get("dataset_id"), str):
            raise TransportError(ErrorCode.VALIDATION, "Select a saved dataset")
        DatasetReview(request.app.state.persistence, body["dataset_id"])
        record = manager(request).submit_job(
            clone_to_timezone,
            request.app.state.persistence,
            body,
            getattr(request.app.state, "data_logs", None) or Logs(),
            owner="data-manager",
            kind="market.clone",
            executor_kind="thread",
            pass_context=True,
        )
        return {"success": True, "data": record.to_dict()}

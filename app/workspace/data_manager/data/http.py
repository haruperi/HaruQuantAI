"""FastAPI HTTP routes for Data Manager datasets catalog and workspace."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.host.response import ErrorCode
from app.host.transport import TransportError

from .feature import Data
from .storage import require_data

__all__ = ["register_data_routes"]

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


def _ok(data: Any) -> dict[str, Any]:
    return {"status": "success", "success": True, "data": data}


def register_data_routes(router: APIRouter) -> None:
    """Register dataset catalog and workspace routes on the domain router."""

    @router.get("/home/datasets")
    def datasets(request: Request) -> dict[str, Any]:
        res = Data(request.app.state.persistence).list()
        if not res["success"]:
            error: dict[str, Any] = res.get("error") or {}
            raise TransportError(
                ErrorCode(error.get("code", "internal")), res["message"]
            )
        return _ok(res["data"])

    @router.get("/home/overview")
    def home_overview(request: Request) -> dict[str, Any]:
        return _ok(require_data(Data(request.app.state.persistence).overview()))

    @router.put("/datasets/{dataset_id}")
    def edit_dataset(
        dataset_id: str, request: Request, body: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            return _ok(Data(request.app.state.persistence).edit(dataset_id, body))
        except (ValueError, TypeError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error

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

    router.add_api_route("/workspace/tabs/{tab}", open_tab, methods=["POST"])


def open_tab(tab: str, request: Request, body: dict[str, Any]) -> dict[str, Any]:
    """Return the selected catalog identity and its real recorded preview."""
    tab = "symbols" if tab == "instruments" else tab
    if tab not in TABS:
        raise TransportError(ErrorCode.NOT_FOUND, "Unknown workspace tab")
    selection = None
    preview = {
        "state": "unavailable",
        "reason": "Select a saved dataset to preview bars.",
        "rows": [],
        "limit": 500,
    }
    context = body.get("context")
    if context is not None:
        if not isinstance(context, dict) or not isinstance(
            context.get("dataset_id"), str
        ):
            raise TransportError(ErrorCode.VALIDATION, "Choose a saved dataset")
        gateway = request.app.state.persistence
        records = require_data(
            gateway.read_records(
                "datamgr_datasets", filters={"id": context["dataset_id"]}, limit=1
            )
        )["records"]
        if not records:
            raise TransportError(ErrorCode.NOT_FOUND, "Dataset not found")
        row = records[0]
        selection = {
            "id": row["id"],
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "broker_name": row["broker"],
            "timezone": row["timezone"],
        }
        result = Data(gateway).review_chart(row["id"], limit=500)
        if not result["success"]:
            preview.update(state="error", reason=result["message"])
        else:
            from datetime import datetime

            bars = [
                {
                    **bar,
                    "time": int(
                        datetime.fromisoformat(bar["datetime"]).timestamp() * 1000
                    ),
                }
                for bar in result["data"]["bars"]
            ]
            preview.update(
                state="ready" if bars else "unavailable",
                reason="" if bars else "This dataset has no recorded history.",
                rows=bars,
            )
    return _ok({"active_tab": tab, "selection": selection, "preview": preview})

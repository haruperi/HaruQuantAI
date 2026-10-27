"""FastAPI HTTP routes for Data Manager datasets catalog and workspace."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.host.response import ErrorCode
from app.host.transport import TransportError

from .feature import Data

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
    def datasets() -> dict[str, Any]:
        res = Data().list()
        if not res["success"]:
            error: dict[str, Any] = res.get("error") or {}
            raise TransportError(
                ErrorCode(error.get("code", "internal")), res["message"]
            )
        return _ok(res["data"])

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

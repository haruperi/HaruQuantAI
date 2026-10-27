"""FastAPI HTTP routes for Data Manager datasets catalog and workspace."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from .feature import Data

__all__ = ["register_data_routes"]


def register_data_routes(router: APIRouter) -> None:
    """Register dataset catalog routes on the domain router."""

    @router.get("/home/datasets")
    def datasets() -> dict[str, Any]:
        from app.host.response import ErrorCode
        from app.host.transport import TransportError

        res = Data().list()
        if not res["success"]:
            error: dict[str, Any] = res.get("error") or {}
            raise TransportError(
                ErrorCode(error.get("code", "internal")), res["message"]
            )
        return {"status": "success", "success": True, "data": res["data"]}

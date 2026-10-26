"""HTTP routes for Dukascopy market data, catalog, and dataset integration."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.workspace.data_manager.data import Data
from app.workspace.data_manager.download_jobs import (
    register_download_jobs,
    start_download,
)
from app.workspace.data_manager.dukascopy import Dukascopy


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


def _register_dukascopy_provider_routes(router: APIRouter) -> None:
    """Register direct Dukascopy and donor provider routes."""

    @router.get("/dukascopy/disclaimer")
    @router.get("/dataSourceDukascopy/disclaimer")
    def dukascopy_disclaimer() -> Any:
        return _response(Dukascopy().disclaimer())

    @router.get("/dukascopy/catalog")
    @router.get("/dataSourceDukascopy/getDataList")
    def dukascopy_catalog(
        category: str | None = Query(None),
        search: str | None = Query(None),
    ) -> Any:
        return _response(Dukascopy().get_catalog(category=category, search=search))

    @router.post("/dukascopy/add")
    @router.post("/dataSourceDukascopy/addData")
    def dukascopy_add(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        symbols = body.get("symbols", [])
        data_type = body.get("dataType") or body.get("data_type") or "M1"
        broker = str(body.get("broker", "default"))
        postfix = str(body.get("postfix", ""))
        instruments = body.get("instruments") or body.get("symbol_definitions")
        confirmed = body.get("disclaimerConfirmed", True)
        if confirmed is None:
            confirmed = True

        service = Dukascopy(gateway)
        result = service.add(
            symbols=symbols,
            data_type=data_type,
            broker=broker,
            postfix=postfix,
            symbol_definitions=instruments,
            disclaimer_confirmed=bool(confirmed),
        )
        return _response(result)

    @router.post("/dukascopy/download")
    @router.post("/dataSourceDukascopy/importData")
    def dukascopy_download(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        symbol = str(body.get("symbol") or body.get("symbols") or "")
        timeframe = str(body.get("timeframe") or body.get("dateType") or "M1")
        date_from = body.get("date_from") or body.get("dateFrom")
        date_to = body.get("date_to") or body.get("dateTo")
        underlying = body.get("underlying") or body.get("dukasSymbols")
        overwrite = bool(body.get("overwrite", False))

        service = Dukascopy(gateway)
        if body.get("async_job") is True:
            return _ok(
                start_download(
                    request,
                    {
                        **body,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "date_from": date_from,
                        "date_to": date_to,
                    },
                )
            )
        result = service.download(
            symbol=symbol,
            timeframe=timeframe,
            date_from=date_from,
            date_to=date_to,
            underlying=underlying,
            overwrite=overwrite,
            download_type=body.get("download_type", "cdn"),
        )
        return _response(result)


def _handle_dukascopy_create(gateway: Any, body: dict[str, Any]) -> Any:
    """Handle Dukascopy dataset creation with derived postfix."""
    symbol = str(body.get("symbol", "")).strip()
    underlying = str(body.get("underlying", symbol)).strip()
    timeframe = str(body.get("timeframe", "M1")).strip().upper()
    broker = str(body.get("broker", "default")).strip()
    sym_def = str(body.get("symbolDefinition", body.get("instrument", "-1"))).strip()

    service = Dukascopy(gateway)
    postfix = ""
    if symbol.upper().startswith(underlying.upper()):
        postfix = symbol[len(underlying) :]
    result = service.add(
        symbols=[underlying],
        data_type=timeframe,
        broker=broker,
        postfix=postfix,
        symbol_definitions=[sym_def],
    )
    if not result["success"]:
        return _response(result)
    records = (result.get("data") or {}).get("records") or []
    if records:
        rec = records[0]
        rec["symbolDefinition"] = sym_def
        return _ok(rec)
    return _response(result)


def _register_dataset_lifecycle_routes(router: APIRouter) -> None:
    """Register UI dataset creation, download, and review routes."""

    @router.post("/datasets")
    def create_dataset(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        source = str(body.get("source", "")).lower()
        if source == "dukascopy":
            return _handle_dukascopy_create(gateway, body)

        from app.workspace.data_manager.sources import Sources

        try:
            return _response(Sources(gateway).add(source, [body]))
        except (ValueError, TypeError) as error:
            return JSONResponse(
                {
                    "success": False,
                    "status": "error",
                    "error": {"code": "validation", "message": str(error)},
                },
                status_code=422,
            )

    @router.post("/providers/download")
    def provider_download(request: Request, body: dict[str, Any]) -> Any:
        provider = str(body.get("provider", "")).lower()
        if provider == "dukascopy":
            return _ok(start_download(request, body))
        from app.workspace.data_manager.source_jobs import start_source_download

        return _ok(start_source_download(request, body))

    @router.post("/datasets/{dataset_id}/clear")
    def clear_dataset(request: Request, dataset_id: str) -> Any:
        return _response(Data(request.app.state.persistence).clear(dataset_id))

    @router.post("/datasets/{dataset_id}/delete")
    def delete_dataset(request: Request, dataset_id: str) -> Any:
        return _response(Data(request.app.state.persistence).delete(dataset_id))

    @router.post("/datasets/review-chart")
    def dataset_review_chart(request: Request, body: dict[str, Any]) -> Any:
        dataset_id = str(body.get("dataset_id", "")).strip()
        limit = int(body.get("limit", 500))
        offset = int(body.get("offset", 0))
        return _response(
            Data(request.app.state.persistence).review_chart(
                dataset_id, limit=limit, offset=offset
            )
        )


def register_dukascopy_routes(router: APIRouter) -> None:
    """Register Dukascopy ingestion and dataset mutation routes."""
    _register_dukascopy_provider_routes(router)
    _register_dataset_lifecycle_routes(router)
    register_download_jobs(router)

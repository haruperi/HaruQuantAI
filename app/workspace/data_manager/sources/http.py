"""FastAPI HTTP routes and download jobs for Data Manager historical sources."""

from __future__ import annotations

import sys
from typing import Any, cast

from fastapi import APIRouter, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.host.transport import TransportError
from app.core.jobs.manager import JobContext
from app.core.lib.responses import ErrorCode
from app.workspace.brokers.base import get_broker
from app.workspace.data_manager.data.feature import Data

from ._base import Sources
from ._helpers import capabilities, provider_id
from .download_jobs import (
    manager,
    register_download_jobs,
    start_download,
)
from .dukascopy import Dukascopy

__all__ = [
    "bridge_action",
    "register_dukascopy_routes",
    "register_source_routes",
    "start_download",
    "start_source_download",
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


async def bridge_action(action: str, application: Any) -> dict[str, Any]:
    """Start the local EA listener without arming trading or submitting orders."""
    client = get_broker("metatrader")
    if action == "connect" and not client.bridge.listening:
        await client.start()
        application.state.data_mt5 = client
    result: dict[str, Any] = {
        "connected": client.bridge.connected,
        "listening": client.bridge.listening,
        "host": client.bridge.host,
        "port": client.bridge.port,
    }
    if action == "connect":
        result["auth_token"] = client.bridge.auth_token
    if client.bridge.connected:
        payload = await client.symbol.SymbolsGet()
        result["symbols"] = payload
    return result


def _get_start_download() -> Any:
    mod = sys.modules.get("app.workspace.data_manager.sources")
    if mod and hasattr(mod, "start_download"):
        return mod.start_download
    return start_download


def _get_sources() -> type[Sources]:
    mod = sys.modules.get("app.workspace.data_manager.sources")
    if mod and hasattr(mod, "Sources"):
        return cast("type[Sources]", mod.Sources)
    return Sources


# --- Dukascopy Routes ---


def _register_dukascopy_provider_routes(router: APIRouter) -> None:
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
                _get_start_download()(
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
        )
        return _response(result)


def _handle_dukascopy_create(gateway: Any, body: dict[str, Any]) -> Any:
    """Handle Dukascopy dataset creation with derived postfix."""
    symbol = str(body.get("symbol", "")).strip()
    underlying = str(body.get("underlying", symbol)).strip()
    timeframe = str(body.get("timeframe", "M1")).strip().upper()
    broker = str(body.get("broker", "default")).strip()
    sym_def = str(
        body.get("symbolDefinition")
        or body.get("instrument")
        or body.get("symbol_definition")
        or "-1"
    ).strip()

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
    @router.post("/datasets/create")
    def create_dataset(request: Request, body: dict[str, Any]) -> Any:
        gateway = request.app.state.persistence
        source = str(body.get("source", "")).strip().lower()
        if source == "dukascopy":
            return _handle_dukascopy_create(gateway, body)

        from app.workspace.data_manager.data._helpers import validate_dataset_updates
        from app.workspace.data_manager.data.storage import require_data

        try:
            record = validate_dataset_updates(
                {key: value for key, value in body.items() if key != "market_root"}
            )
            require_data(gateway.ensure_datasets_schema())
            with gateway.transaction() as tx:
                from app.workspace.data_manager.data._helpers import (
                    resolve_dataset_links,
                )

                resolve_dataset_links(tx, record)
                result = require_data(tx.create_records("datamgr_datasets", record))
            return _ok(result["records"][0])
        except (ValueError, TypeError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error

    @router.post("/providers/download")
    def download_dataset(request: Request, body: dict[str, Any]) -> Any:
        provider = str(body.get("provider", "")).strip().lower()
        if provider == "dukascopy":
            return _ok(_get_start_download()(request, body))
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


# --- Broker Sources Routes ---


def _provider_catalog(request: Request, provider: str) -> list[str]:
    """Read catalog symbols using the selected provider connection and lifecycle."""
    from app.core.host.transport import ServletConnection

    from ._helpers import make_client, resolve_result

    connection = None
    connection_id = request.query_params.get("connection_id")
    if connection_id:
        vault = getattr(request.app.state, "vault", None)
        saved = ServletConnection(request.app.state.persistence, vault=vault).get(
            connection_id
        )
        if saved.provider != provider or (saved.vault_refs and vault is None):
            raise ValueError("Choose an available connection for this provider")
        credentials = (
            {key: vault.resolve(ref) for key, ref in saved.vault_refs.items()}
            if vault is not None
            else {}
        )
        connection = {
            **saved.model_dump(),
            "credentials": credentials,
        }
    client = make_client(provider, connection)
    try:
        return list(
            resolve_result(
                client.symbol.SymbolsGet()
                if provider == "mt5"
                else client.get_symbols(),
                client,
            )
        )
    finally:
        if provider != "mt5":
            client.disconnect()


def register_source_routes(router: APIRouter) -> None:
    """Register generic source commands on the domain router."""

    @router.get("/sources/{provider}/{action}")
    @router.post("/sources/{provider}/{action}")
    async def source_command(
        provider: str, action: str, request: Request, body: dict[str, Any] | None = None
    ) -> Any:
        try:
            if action == "capabilities":
                return _ok(capabilities(provider))
            if provider == "mt5" and (
                action == "status" or (action == "connect" and request.method == "POST")
            ):
                return _ok(await bridge_action(action, request.app))
            if action == "catalog" and request.method == "GET":
                from asyncio import to_thread

                return _ok(await to_thread(_provider_catalog, request, provider))
            if action == "add" and request.method == "POST":
                return _response(
                    _get_sources()(request.app.state.persistence).add(
                        provider, (body or {}).get("definitions", [])
                    )
                )
            raise TransportError(ErrorCode.VALIDATION, "Unknown source operation")
        except (ValueError, TypeError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error


# --- Source Background Jobs ---

_MAX_TARGETS = 1000


def start_source_download(request: Request, body: dict[str, Any]) -> dict[str, Any]:
    """Validate persisted targets before accepting a real download job."""
    service = _get_sources()(request.app.state.persistence)
    try:
        records, lower, upper, overwrite = _validate_source_job(service, body)
        import json

        from app.core.host.transport import ServletConnection

        connection_ids = {
            json.loads(service.record(identifier).get("lineage_json") or "{}").get(
                "connection_id"
            )
            for identifier in records
        }
        connection_id = body.get("connection_id") or next(
            iter(connection_ids - {None}), None
        )
        if len(connection_ids - {None}) > 1 and not body.get("connection_id"):
            raise ValueError("Download datasets from one saved connection at a time")  # noqa: TRY301 - enclosing scope owns rollback
        if connection_id:
            vault = getattr(request.app.state, "vault", None)
            connection = ServletConnection(
                request.app.state.persistence, vault=vault
            ).get(connection_id)
            if any(
                service.record(identifier)["source"] != connection.provider
                for identifier in records
            ):
                raise ValueError("Selected connection belongs to another provider")  # noqa: TRY301 - enclosing scope owns rollback
            if connection.vault_refs and vault is None:
                raise ValueError("Credential vault is unavailable")  # noqa: TRY301 - enclosing scope owns rollback
            credentials = (
                {key: vault.resolve(ref) for key, ref in connection.vault_refs.items()}
                if vault is not None
                else {}
            )
            service.connection = {
                **connection.model_dump(),
                "credentials": credentials,
            }

    except (ValueError, TypeError) as error:
        raise TransportError(ErrorCode.VALIDATION, str(error)) from error
    return (
        manager(request)
        .submit_job(
            _run_source_job,
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


def _validate_source_job(
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


def _run_source_job(
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

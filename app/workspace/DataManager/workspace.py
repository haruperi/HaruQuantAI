"""Data Manager's resource-facing workflow and versioned extension boundary.

Acquisition providers are not implemented here. The workspace can inspect retained
resources with zero attached providers and never imports another owner's code.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue

from app.host.capabilities import HostCapabilities
from app.host.composition import Binding, PreparedContribution
from app.host.logging import get_logger
from app.host.resource_store import ResourceRef
from app.workspace.DataManager.actions import (
    broker_data,
    broker_data_update,
    clone_to_timezone,
    delete_datasets,
    export_to_csv,
    export_to_mt4,
    export_to_mt5,
    list_datasets,
    load_definitions,
    review_chart,
    review_data,
    review_quality,
    save_data_changes,
    save_definitions,
    update_all,
    update_selected,
)

logger = get_logger(__name__)

PLUGIN = {
    "id": "workspace.data_manager",
    "kind": "workspace",
    "version": "1.0.0",
    "compatibility": "1",
    "route_base": "/api/v1/data-manager",
    "requires": [{"id": "host.resources", "version": "1.0.0"}],
    "slots": [
        {"id": "data_source.presentation", "version": "1.0.0"},
        {"id": "data_source.acquisition", "version": "1.0.0"},
    ],
}


def _resolve_paths() -> tuple[Path, Path]:
    """Resolve database path and data root from working directory."""
    root = Path.cwd()
    return root / "data" / "database" / "haruquantai.db", root / "data"


def _invoke_action(  # noqa: C901, PLR0911, PLR0912, PLR0915
    operation: str,
    payload_dict: dict[str, Any],
    db_path: Path,
    data_root: Path,
) -> JsonValue:
    """Execute Data Manager actions and return JSON-compatible values."""
    logger.info("Executing Data Manager action: %s", operation)
    target_db = Path(payload_dict["db_path"]) if "db_path" in payload_dict else db_path
    target_data_root = (
        Path(payload_dict["data_root"]) if "data_root" in payload_dict else data_root
    )
    if operation == "actions.broker_data":
        query = payload_dict.get("query")
        broker_id = payload_dict.get("broker_id")
        return cast(
            "JsonValue", broker_data(target_db, query=query, broker_id=broker_id)
        )

    if operation == "actions.broker_data_update":
        profile_ids = payload_dict.get("profile_ids")
        symbols = payload_dict.get("symbols")
        return cast(
            "JsonValue",
            broker_data_update(target_db, profile_ids=profile_ids, symbols=symbols),
        )

    if operation == "actions.clone_to_timezone":
        symbols = payload_dict.get("symbols", [])
        shift_hours = int(payload_dict.get("shift_hours", 0))
        timezone_name = str(payload_dict.get("timezone", "UTC"))
        postfix = str(payload_dict.get("postfix", "_{timeframe}_{cloneTime}"))
        remove_weekends = bool(payload_dict.get("remove_weekends", False))
        return cast(
            "JsonValue",
            clone_to_timezone(
                target_db,
                target_data_root,
                symbols,
                shift_hours=shift_hours,
                timezone_name=timezone_name,
                postfix=postfix,
                remove_weekends=remove_weekends,
            ),
        )

    if operation == "actions.delete":
        symbols = payload_dict.get("symbols", [])
        mode = str(payload_dict.get("mode", "remove"))
        return cast(
            "JsonValue",
            delete_datasets(target_db, target_data_root, symbols, mode=mode),
        )

    if operation == "actions.export_to_csv":
        symbol = str(payload_dict.get("symbol", ""))
        timeframe = str(payload_dict.get("timeframe", "M1"))
        date_from = payload_dict.get("date_from")
        date_to = payload_dict.get("date_to")
        output_path = payload_dict.get("output_path")
        target_timezone = payload_dict.get("target_timezone")
        header = payload_dict.get("header")
        include_header = bool(payload_dict.get("include_header", True))
        return cast(
            "JsonValue",
            export_to_csv(
                target_db,
                target_data_root,
                symbol,
                timeframe=timeframe,
                date_from=date_from,
                date_to=date_to,
                output_path=output_path,
                target_timezone=target_timezone,
                header=header,
                include_header=include_header,
            ),
        )

    if operation == "actions.export_to_mt4":
        sq_symbol = str(payload_dict.get("sq_symbol", payload_dict.get("symbol", "")))
        mt4_symbol = payload_dict.get("mt4_symbol")
        output_dir = payload_dict.get("output_dir")
        timeframe = str(payload_dict.get("timeframe", "All"))
        export_mode = str(payload_dict.get("export_mode", "All"))
        target_timezone = payload_dict.get("target_timezone")
        server_name = str(payload_dict.get("server_name", "MetaQuotes-Demo"))
        spread = int(payload_dict.get("spread", 20))
        digits = int(payload_dict.get("digits", 5))
        return cast(
            "JsonValue",
            export_to_mt4(
                target_db,
                target_data_root,
                sq_symbol,
                mt4_symbol=mt4_symbol,
                output_dir=output_dir,
                timeframe=timeframe,
                export_mode=export_mode,
                target_timezone=target_timezone,
                server_name=server_name,
                spread=spread,
                digits=digits,
            ),
        )

    if operation == "actions.export_to_mt5":
        symbol = str(payload_dict.get("symbol", ""))
        timeframe = str(payload_dict.get("timeframe", "M1"))
        spread_mode = str(payload_dict.get("spread_mode", "real"))
        spread_points = int(payload_dict.get("spread_points", 10))
        date_from = payload_dict.get("date_from")
        date_to = payload_dict.get("date_to")
        output_path = payload_dict.get("output_path")
        target_timezone = payload_dict.get("target_timezone")
        return cast(
            "JsonValue",
            export_to_mt5(
                target_db,
                target_data_root,
                symbol,
                timeframe=timeframe,
                spread_mode=spread_mode,
                spread_points=spread_points,
                date_from=date_from,
                date_to=date_to,
                output_path=output_path,
                target_timezone=target_timezone,
            ),
        )

    if operation == "actions.save":
        symbols = payload_dict.get("symbols")
        file_path = payload_dict.get("file_path")
        return cast(
            "JsonValue",
            save_definitions(
                target_db, target_data_root, symbols=symbols, file_path=file_path
            ),
        )

    if operation == "actions.load":
        file_path = str(payload_dict.get("file_path", ""))
        return cast(
            "JsonValue",
            load_definitions(target_db, target_data_root, file_path=file_path),
        )

    if operation == "actions.review_data":
        symbol = str(payload_dict.get("symbol", ""))
        timeframe = str(payload_dict.get("timeframe", "M1"))
        session = str(payload_dict.get("session", "Default"))
        offset = int(payload_dict.get("offset", 0))
        limit = int(payload_dict.get("limit", 100))
        date_from = payload_dict.get("date_from")
        date_to = payload_dict.get("date_to")
        return cast(
            "JsonValue",
            review_data(
                target_db,
                target_data_root,
                symbol,
                timeframe=timeframe,
                session=session,
                offset=offset,
                limit=limit,
                date_from=date_from,
                date_to=date_to,
            ),
        )

    if operation == "actions.review_chart":
        symbol = str(payload_dict.get("symbol", ""))
        timeframe = str(payload_dict.get("timeframe", "M1"))
        session = str(payload_dict.get("session", "Default"))
        index_from = int(payload_dict.get("index_from", -1))
        index_to = int(payload_dict.get("index_to", -1))
        limit = int(payload_dict.get("limit", 500))
        return cast(
            "JsonValue",
            review_chart(
                target_db,
                target_data_root,
                symbol,
                timeframe=timeframe,
                session=session,
                index_from=index_from,
                index_to=index_to,
                limit=limit,
            ),
        )

    if operation == "actions.review_quality":
        symbol = str(payload_dict.get("symbol", ""))
        timeframe = str(payload_dict.get("timeframe", "M1"))
        session = str(payload_dict.get("session", "Default"))
        return cast(
            "JsonValue",
            review_quality(
                target_db,
                target_data_root,
                symbol,
                timeframe=timeframe,
                session=session,
            ),
        )

    if operation == "actions.save_data_changes":
        symbol = str(payload_dict.get("symbol", ""))
        timeframe = str(payload_dict.get("timeframe", "M1"))
        session = str(payload_dict.get("session", "Default"))
        changes = payload_dict.get("changes", {})
        return cast(
            "JsonValue",
            save_data_changes(
                target_db,
                target_data_root,
                symbol,
                timeframe=timeframe,
                session=session,
                changes=changes,
            ),
        )

    if operation == "actions.update_all":
        provider = str(payload_dict.get("provider", "dukascopy"))
        return cast(
            "JsonValue",
            update_all(target_db, target_data_root, provider=provider),
        )

    if operation == "actions.update_selected":
        symbols = payload_dict.get("symbols", [])
        provider = str(payload_dict.get("provider", "dukascopy"))
        return cast(
            "JsonValue",
            update_selected(target_db, target_data_root, symbols, provider=provider),
        )

    if operation == "actions.list_datasets":
        return cast(
            "JsonValue",
            list_datasets(target_db, target_data_root),
        )

    logger.warning("Unknown Data Manager action: %s", operation)
    raise ValueError(f"Unknown workspace action: {operation}")


async def prepare(  # noqa: C901
    context: HostCapabilities,
) -> PreparedContribution:
    """Prepare a usable empty workspace with explicit host resource access."""
    resources = context.resources
    if resources is None:
        raise ValueError("Missing host.resources capability")
    bindings: tuple[Binding, ...] = ()
    db_path, data_root = _resolve_paths()
    logger.info(
        "Preparing Data Manager workspace (db_path=%s, data_root=%s)",
        db_path,
        data_root,
    )

    async def attach(children: tuple[Binding, ...]) -> None:
        """Retain immutable accepted child handles supplied only by the host."""
        nonlocal bindings
        bindings = children
        logger.info(
            "Data Manager attached %d child binding(s): %s",
            len(children),
            [binding.package_id for binding in children],
        )

    async def invoke(operation: str, payload: JsonValue) -> JsonValue:
        """Inspect published resources or execute workspace actions."""
        logger.info("Data Manager invoking: %s", operation)
        if operation == "resources.list":
            return [reference.model_dump(mode="json") for reference in resources.list()]
        if operation == "resources.read":
            reference = ResourceRef.model_validate(payload)
            content, schema = resources.read(reference)
            return {
                "content_base64": base64.b64encode(content).decode(),
                "schema": schema,
            }
        if operation == "capabilities":
            return {"providers": [binding.package_id for binding in bindings]}

        # --- Data Manager Actions Parity ---
        if operation.startswith("actions."):
            payload_dict: dict[str, Any] = payload if isinstance(payload, dict) else {}
            return _invoke_action(operation, payload_dict, db_path, data_root)

        # --- Dukascopy Acquisition Delegation ---
        if operation.startswith("sources.dukascopy."):
            acquisition = next(
                (
                    binding
                    for binding in bindings
                    if binding.slot_id == "data_source.acquisition"
                    and binding.package_id == "plugin.data_manager.dukascopy"
                ),
                None,
            )
            if acquisition is None:
                logger.warning(
                    "Dukascopy acquisition unavailable for operation: %s", operation
                )
                raise ValueError("Dukascopy acquisition unavailable")
            action = operation.removeprefix("sources.dukascopy.")
            if action not in acquisition.operations:
                logger.warning("Missing Dukascopy acquisition operation: %s", action)
                raise ValueError("Missing acquisition operation")
            return await acquisition.invoke(action, payload)

        logger.warning("Missing capability for operation: %s", operation)
        raise ValueError("Missing acquisition capability")

    async def close() -> None:
        """Release local attachment handles; host retains published resources."""
        nonlocal bindings
        bindings = ()
        logger.info("Data Manager workspace closed")

    return PreparedContribution(
        (
            "resources.list",
            "resources.read",
            "capabilities",
            "actions.broker_data",
            "actions.broker_data_update",
            "actions.clone_to_timezone",
            "actions.delete",
            "actions.export_to_csv",
            "actions.export_to_mt4",
            "actions.export_to_mt5",
            "actions.load",
            "actions.save",
            "actions.review_data",
            "actions.review_chart",
            "actions.review_quality",
            "actions.save_data_changes",
            "actions.update_all",
            "actions.update_selected",
            "actions.list_datasets",
            "sources.dukascopy.catalog",
            "sources.dukascopy.add",
            "sources.dukascopy.definitions.add",
            "sources.dukascopy.download.start",
            "sources.dukascopy.download.status",
            "sources.dukascopy.download.cancel",
            "sources.dukascopy.files.list",
            "sources.dukascopy.delete",
            "sources.dukascopy.clear",
        ),
        invoke,
        close,
        attach,
    )

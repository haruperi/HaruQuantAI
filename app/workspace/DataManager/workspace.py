"""DataManager Workspace Lifecycle, Extension Boundary, and Action Router.

Description:
    Provides the central composition root, lifecycle coordination, and action
    routing boundary for the Data Manager workspace (`workspace.data_manager`).

    External relations and workflows:
    - Host composition: Discovered by host catalog (`app.host.discovery`),
      instantiated and initialized by `prepare(HostCapabilities)` where
      `HostCapabilities.resources` is injected.
    - Workspace router & actions: Invocations matching `actions.*` are mapped
      to internal action executors (`app.workspace.DataManager.actions`).
    - Acquisition plugin delegation: Subordinate acquisition plugins attaching
      to `data_source.acquisition` (such as Dukascopy acquisition) are dispatched
      via discovered `sources.<provider>.*` routes.

    Internal coordination:
    - PLUGIN: Manifest dictionary defining workspace ID, version, contract
      version, route base, required host capabilities (`host.resources`), and
      extension slots (`data_source.presentation`, `data_source.acquisition`).
    - prepare: Asynchronous lifecycle hook setting up local binding state and
      returning a `PreparedContribution`.
    - attach: Dynamic slot attachment hook for child acquisition plugins.
    - invoke: Operation dispatcher for resource inspection, capabilities
      queries, and DataManager action routing.
    - close: Clean teardown hook releasing child bindings.

Purpose:
    FEAT-WORKSPACE-DATAMANAGER: Data Manager workspace composition, lifecycle
    orchestration, host capability binding, and plugin extension boundary.

Key Capabilities:
    - FR-WORKSPACE-DATAMANAGER-LIFECYCLE: Prepares workspace contribution, binds
      explicit host resource access, and manages dynamic child plugin
      attachments via prepare(), attach(), and close().
      * Verified via: logger.info("Preparing Data Manager workspace...")
    - FR-WORKSPACE-DATAMANAGER-DISPATCH: Dispatches operations to DataManager
      actions, inspects retained resources, and delegates acquisition requests
      to attached plugins via explicit bindings and retained custody.
      * Verified via: logger.info("Data Manager invoking: %s")
    - FR-WORKSPACE-DATAMANAGER-RESOURCES: Reads and lists retained host-level
      quantitative resources via resources.list and resources.read operations
      under explicit capability boundaries.
      * Verified via: logger.info("Data Manager invoking: %s")

Python API Usage:
    ```python
    from app.host.capabilities import HostCapabilities
    from app.workspace.DataManager.workspace import prepare

    contribution = await prepare(capabilities)
    result = await contribution.invoke("actions.list_datasets", {})
    await contribution.close()
    ```

CLI Usage:
    ```bash
    # Verified through DataManager workspace test suite:
    uv run python -m pytest tests/workspace/DataManager/test_workspace.py
    ```
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any, cast

from pydantic import JsonValue

from app.host.capabilities import HostCapabilities
from app.host.contracts import DatasetMetadataDocument
from app.host.logging import get_logger
from app.host.packages import Binding, PreparedContribution
from app.persistence.resources import ResourceRef
from app.workspace.DataManager.actions import (
    inspect_source,
)
from app.workspace.DataManager.catalogs import (
    broker_clock_operation,
    broker_operation,
    catalog_operation,
)
from app.workspace.DataManager.operations import execute, inventory_presentation

logger = get_logger(__name__)

PLUGIN = {
    "id": "workspace.data_manager",
    "kind": "workspace",
    "version": "1.0.0",
    "compatibility": "1",
    "route_base": "/api/v1/data-manager",
    "requires": [
        {"id": "host.resources", "version": "1.0.0"},
        {"id": "host.market_data", "version": "1.0.0", "required": False},
        {"id": "host.settings", "version": "1.0.0", "required": False},
    ],
    "slots": [
        {"id": "data_source.presentation", "version": "1.0.0"},
        {"id": "data_source.acquisition", "version": "1.0.0"},
    ],
}


async def prepare(  # noqa: C901, PLR0915 -- workspace lifecycle and bound operations.
    context: HostCapabilities,
) -> PreparedContribution:
    """Prepare a usable empty workspace with explicit host resource access."""
    resources = context.resources
    if resources is None:
        raise ValueError("Missing host.resources capability")
    bindings: tuple[Binding, ...] = ()
    logger.info("Preparing Data Manager workspace with injected custody")

    async def attach(children: tuple[Binding, ...]) -> None:
        """Retain immutable accepted child handles supplied only by the host."""
        nonlocal bindings
        bindings = children
        logger.info(
            "Data Manager attached %d child binding(s): %s",
            len(children),
            [binding.package_id for binding in children],
        )

    async def submit_updates(  # noqa: C901, PLR0912 -- report per-target admission failures.
        operation: str, values: dict[str, JsonValue]
    ) -> JsonValue:
        """Submit actual attached acquisition jobs and report each rejected target."""
        selected = values.get("dataset_ids", values.get("symbols", []))
        if not isinstance(selected, list) or any(
            not isinstance(item, str) for item in selected
        ):
            raise ValueError("Invalid update selection")
        if operation == "actions.update_selected" and not selected:
            raise ValueError("Choose datasets to update")
        jobs: list[JsonValue] = []
        errors: list[JsonValue] = []
        requested_provider = values.get("provider")
        admitted_providers = 0
        matched: set[str] = set()
        for binding in bindings:
            provider = binding.package_id.rsplit(".", 1)[-1]
            if binding.slot_id != "data_source.acquisition" or (
                requested_provider and requested_provider != provider
            ):
                continue
            if (
                "catalog" not in binding.operations
                or "download.start" not in binding.operations
            ):
                continue
            admitted_providers += 1
            try:
                catalog = await binding.invoke("catalog", {})
            except ValueError, TypeError, PermissionError:
                errors.append({"reason": "Provider catalog unavailable: " + provider})
                continue
            rows = catalog.get("datasets") if isinstance(catalog, dict) else None
            if not isinstance(rows, (list, tuple)):
                errors.append({"reason": "Invalid acquisition catalog: " + provider})
                continue
            for row in rows:
                if not isinstance(row, dict):
                    raise TypeError("Invalid acquisition dataset")
                dataset_id, symbol = row.get("id"), row.get("symbol")
                if (
                    operation == "actions.update_selected"
                    and dataset_id not in selected
                    and symbol not in selected
                ):
                    continue
                matched.update(
                    item for item in (dataset_id, symbol) if isinstance(item, str)
                )
                first = (
                    values.get("date_from")
                    or row.get("to")
                    or row.get("date_to")
                    or row.get("from")
                    or row.get("date_from")
                )
                if not isinstance(first, str) or not first:
                    errors.append(
                        {
                            "dataset_id": dataset_id,
                            "reason": "Choose an initial download date range",
                        }
                    )
                    continue
                try:
                    started = await binding.invoke(
                        "download.start",
                        {
                            "dataset_id": dataset_id,
                            "date_from": first[:10],
                            "date_to": values.get("date_to")
                            or datetime.now(UTC).date().isoformat(),
                        },
                    )
                except ValueError, TypeError, PermissionError:
                    errors.append(
                        {
                            "dataset_id": dataset_id,
                            "reason": "Acquisition was not admitted",
                        }
                    )
                    continue
                if not isinstance(started, dict) or not isinstance(
                    started.get("job_id"), str
                ):
                    raise TypeError("Acquisition did not return a host job")
                jobs.append(
                    {
                        "dataset_id": dataset_id,
                        "provider": provider,
                        "job_id": started["job_id"],
                    }
                )
        if not admitted_providers:
            errors.append(
                {"reason": "No compatible acquisition capability is available"}
            )
        if operation == "actions.update_selected":
            errors.extend(
                {
                    "dataset_id": missing,
                    "reason": "Dataset has no available acquisition capability",
                }
                for missing in sorted(set(cast("list[str]", selected)) - matched)
            )
        logger.info(
            "Submitted dataset updates: jobs=%d rejected=%d", len(jobs), len(errors)
        )
        return {
            "success": not errors,
            "queued": len(jobs),
            "queuedUpdates": len(jobs),
            "jobs": jobs,
            "errors": errors,
        }

    async def invoke(operation: str, payload: JsonValue) -> JsonValue:  # noqa: C901, PLR0911, PLR0912, PLR0915 -- one workspace operation boundary.
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

        if operation in ("catalogs.get", "catalogs.replace"):
            if context.settings is None or context.market_data is None:
                raise ValueError("Catalog custody unavailable")
            return cast(
                "JsonValue",
                catalog_operation(
                    context.settings,
                    context.market_data,
                    operation,
                    payload if isinstance(payload, dict) else {},
                ),
            )

        if operation in ("broker_clock.get", "broker_clock.replace"):
            if context.settings is None or context.market_data is None:
                raise ValueError("Broker clock custody unavailable")
            return cast(
                "JsonValue",
                broker_clock_operation(
                    context.settings,
                    context.market_data,
                    operation,
                    payload if isinstance(payload, dict) else {},
                ),
            )

        if operation == "actions.clock_provenance":
            if context.market_data is None or not isinstance(payload, dict):
                raise ValueError("Clock provenance custody unavailable")
            provenance = context.market_data.source_clock_provenance(
                str(payload.get("dataset_id", "")), str(payload.get("period", ""))
            )
            return cast(
                "JsonValue",
                provenance.model_dump(mode="json")
                if provenance
                else {"status": "legacy_unverified"},
            )

        if operation in ("actions.broker_data", "actions.broker_data_update"):
            if context.settings is None or context.market_data is None:
                raise ValueError("Catalog custody unavailable")
            return cast(
                "JsonValue",
                broker_operation(
                    context.settings,
                    context.market_data,
                    operation,
                    payload if isinstance(payload, dict) else {},
                ),
            )

        if operation == "actions.list_datasets":
            if context.market_data is None:
                raise ValueError("Market inventory capability unavailable")
            rows = inventory_presentation(context.market_data, context.settings)
            by_id = {row["id"]: row for row in rows}
            for binding in bindings:
                if (
                    binding.slot_id != "data_source.acquisition"
                    or "dataset_metadata" not in binding.operations
                ):
                    continue
                selected_ids = [
                    row["id"] for row in rows if row.get("owner") == binding.package_id
                ]
                if not selected_ids:
                    # Inventory intentionally contains no provider implementation data.
                    selected_ids = [
                        row["id"]
                        for row in rows
                        if context.market_data.retained_source(row["id"])["owner"]
                        == binding.package_id
                    ]
                try:
                    metadata = DatasetMetadataDocument.model_validate(
                        await binding.invoke(
                            "dataset_metadata", {"dataset_ids": selected_ids}
                        )
                    )
                    if len({item.dataset_id for item in metadata.datasets}) != len(
                        metadata.datasets
                    ) or any(
                        item.dataset_id not in selected_ids
                        for item in metadata.datasets
                    ):
                        raise ValueError("Provider metadata ownership mismatch")  # noqa: TRY301 -- handled optional response validation failure.
                    for item in metadata.datasets:
                        by_id[item.dataset_id].update(
                            barType=item.bar_type,
                            dataType=item.data_type,
                            typeSource=item.type_source,
                            brokerUtcOffset=item.broker_utc_offset,
                            clockStatus=item.clock_status,
                            checkedAt=item.checked_at.isoformat()
                            if item.checked_at
                            else None,
                        )
                except ValueError, TypeError, PermissionError, OSError, TimeoutError:
                    logger.warning(
                        "Optional dataset metadata unavailable: provider=%s",
                        binding.package_id,
                    )
            return cast("JsonValue", rows)

        if operation in ("actions.update_all", "actions.update_selected"):
            if not isinstance(payload, dict):
                raise ValueError("Invalid update request")
            return await submit_updates(operation, payload)

        if (
            operation
            in ("actions.review_data", "actions.review_chart", "actions.review_quality")
            and isinstance(payload, dict)
            and payload.get("dataset_id")
        ):
            if context.market_data is None:
                raise ValueError("Market inspection capability unavailable")
            return cast(
                "JsonValue", inspect_source(context.market_data, operation, payload)
            )

        # --- Data Manager Actions Parity ---
        if operation.startswith("actions."):
            payload_dict: dict[str, Any] = payload if isinstance(payload, dict) else {}
            if context.market_data is None:
                raise ValueError("Market management capability unavailable")
            return cast(
                "JsonValue",
                execute(context.market_data, operation, payload_dict, context.settings),
            )

        if operation.startswith("sources."):
            route = operation.removeprefix("sources.")
            provider, separator, action = route.partition(".")
            acquisition = next(
                (
                    binding
                    for binding in bindings
                    if binding.slot_id == "data_source.acquisition"
                    and binding.package_id.rsplit(".", 1)[-1] == provider
                ),
                None,
            )
            if not separator or acquisition is None:
                logger.warning("Acquisition unavailable: %s", operation)
                raise ValueError("Missing acquisition capability")
            if action not in acquisition.operations:
                raise ValueError("Missing acquisition operation")
            return await acquisition.invoke(action, payload)

        logger.warning("Missing capability for operation: %s", operation)
        raise ValueError("Missing acquisition capability")

    def attached_operations() -> tuple[str, ...]:
        """Expose only operations contributed by accepted acquisition bindings."""
        return tuple(
            f"sources.{binding.package_id.rsplit('.', 1)[-1]}.{operation}"
            for binding in bindings
            if binding.slot_id == "data_source.acquisition"
            for operation in binding.operations
        )

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
            "catalogs.get",
            "catalogs.replace",
            "broker_clock.get",
            "broker_clock.replace",
            "actions.clock_provenance",
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
        ),
        invoke,
        close,
        attach,
        attached_operations,
        invocation_seconds=120,
    )

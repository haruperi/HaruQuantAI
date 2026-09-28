"""Data Manager's resource-facing workflow and versioned extension boundary.

Acquisition providers are not implemented here. The workspace can inspect retained
resources with zero attached providers and never imports another owner's code.
"""

import base64

from pydantic import JsonValue

from app.host.capabilities import HostCapabilities
from app.host.composition import Binding, PreparedContribution
from app.host.resource_store import ResourceRef

PLUGIN = {
    "id": "workspace.data_manager",
    "kind": "workspace",
    "version": "1.0.0",
    "compatibility": "1",
    "route_base": "/api/v1/data-manager",
    "requires": [{"id": "host.resources", "version": "1.0.0"}],
    "slots": [{"id": "data_source.presentation", "version": "1.0.0"}],
}


async def prepare(context: HostCapabilities) -> PreparedContribution:
    """Prepare a usable empty workspace with explicit host resource access."""
    resources = context.resources
    if resources is None:
        raise ValueError("Missing host.resources capability")
    bindings: tuple[Binding, ...] = ()

    async def attach(children: tuple[Binding, ...]) -> None:
        """Retain immutable accepted child handles supplied only by the host."""
        nonlocal bindings
        bindings = children

    async def invoke(operation: str, payload: JsonValue) -> JsonValue:
        """Inspect published resources or explicitly report absent acquisition."""
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
        raise ValueError("Missing acquisition capability")

    async def close() -> None:
        """Release local attachment handles; host retains published resources."""
        nonlocal bindings
        bindings = ()

    return PreparedContribution(
        ("resources.list", "resources.read", "capabilities"), invoke, close, attach
    )

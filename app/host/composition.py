"""Validated trusted contribution activation and owner-local slot binding.

No runtime peer lookup is exposed to contributions. Package validation and literal
descriptor inspection precede imports. UI-only packages never imply executability.
"""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from uuid import uuid4

from pydantic import JsonValue

from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    ResourceAccess,
    SettingsAccess,
)
from app.host.catalog import read_descriptor
from app.host.contracts import PluginDescriptor
from app.host.jobs import JobManager
from app.host.logging import get_logger
from app.host.packages import Package, PackageInventory, PackageIssue, confined_file
from app.host.resource_store import ResourceStore

ACTIVATION_TIMEOUT = 5.0
HOST_SERVICES = frozenset(
    {"host.resources", "host.jobs", "host.logging", "host.settings"}
)


@dataclass(frozen=True)
class PreparedContribution:
    """Accepted owner-local operations with explicit disposal and optional binding."""

    operations: tuple[str, ...]
    invoke: Callable[[str, JsonValue], Awaitable[JsonValue]]
    close: Callable[[], Awaitable[None]]
    attach: Callable[[tuple[Binding, ...]], Awaitable[None]] | None = None


@dataclass(frozen=True)
class Binding:
    """One child handle visible only to its owning workspace composition."""

    package_id: str
    slot_id: str
    contract_version: str
    operations: tuple[str, ...]
    invoke: Callable[[str, JsonValue], Awaitable[JsonValue]]


Factory = Callable[[HostCapabilities], Awaitable[PreparedContribution]]


class Composition:
    """Composition root with explicit lifecycle and no ambient provider registration."""

    def __init__(
        self,
        root: Path,
        resources: ResourceStore,
        jobs: JobManager,
        settings: Any = None,
    ) -> None:
        self.root = root
        self.resources = resources
        self.jobs = jobs
        self.settings = settings
        self.active: dict[str, PreparedContribution] = {}
        self.issues: list[PackageIssue] = []
        self._modules: dict[str, ModuleType] = {}
        self._descriptors: dict[str, PluginDescriptor] = {}

    def _descriptor(self, package: Package) -> PluginDescriptor:
        """Validate literal semantic identity and declared host authority."""
        if package.backend_entry is None:
            raise ValueError("No backend entry")
        descriptor, _ = read_descriptor(confined_file(self.root, package.backend_entry))
        if (descriptor.id, descriptor.version, descriptor.kind) != (
            package.id,
            package.version,
            package.kind,
        ):
            raise ValueError("Descriptor identity mismatch")
        if package.attachment is not None and (
            descriptor.owner_workspace_id,
            descriptor.slot_id,
            descriptor.contract_version,
        ) != (
            package.owner_workspace_id,
            package.attachment.slot_id,
            package.attachment.contract_version,
        ):
            raise ValueError("Descriptor attachment mismatch")
        if any(
            r.id not in HOST_SERVICES or r.version != "1.0.0"
            for r in descriptor.requires
        ):
            raise ValueError("Missing host capability")
        if len({slot.id for slot in descriptor.slots}) != len(descriptor.slots):
            raise ValueError("Ambiguous workspace slots")
        return descriptor

    def _load(self, package: Package) -> Factory:
        """Import one validated trusted file; no namespaced sibling import lookup."""
        if package.backend_entry is None:
            raise ValueError("No backend entry")
        path = confined_file(self.root, package.backend_entry)
        spec = importlib.util.spec_from_file_location("_haru_" + uuid4().hex, path)
        if spec is None or spec.loader is None:
            raise ValueError("Invalid backend loader")
        module = importlib.util.module_from_spec(spec)
        self._modules[package.id] = module
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        factory = getattr(module, "prepare", None)
        if not inspect.iscoroutinefunction(factory):
            raise TypeError("Entrypoint must expose async prepare")
        return cast("Factory", factory)

    def _context(
        self, package: Package, descriptor: PluginDescriptor
    ) -> HostCapabilities:
        """Grant only declared services, with one immutable owner identity."""
        requirements = {r.id for r in descriptor.requires}
        logger = get_logger("app.contribution." + package.id)
        return HostCapabilities(
            ResourceAccess(package.id, package.version, self.resources)
            if "host.resources" in requirements
            else None,
            JobAccess(package.id, self.jobs) if "host.jobs" in requirements else None,
            logger.info if "host.logging" in requirements else None,
            SettingsAccess(package.id, self.settings)
            if "host.settings" in requirements and self.settings is not None
            else None,
        )

    async def _prepare(self, package: Package, descriptor: PluginDescriptor) -> None:
        """Prepare with a finite cooperative deadline and isolate ordinary failure."""
        try:
            factory = self._load(package)
            async with asyncio.timeout(ACTIVATION_TIMEOUT):
                contribution = await factory(self._context(package, descriptor))
            if not isinstance(contribution, PreparedContribution):
                raise TypeError("Invalid prepared contribution")  # noqa: TRY301 -- validate foreign result at boundary.
            self.active[package.id] = contribution
        except Exception:  # noqa: BLE001 -- attributed contribution boundary, no secret diagnostics.
            self.issues.append(
                PackageIssue(package_id=package.id, code="activation_failed")
            )
            await self._close_one(package.id)

    async def start(self, inventory: PackageInventory) -> None:
        """Validate descriptors, prepare parents, then bind accepted children."""
        descriptors: dict[str, PluginDescriptor] = {}
        self.issues.extend(inventory.issues)
        for package in inventory.packages:
            if package.backend_entry is not None:
                try:
                    descriptors[package.id] = self._descriptor(package)
                except OSError, ValueError, SyntaxError, TypeError:
                    self.issues.append(
                        PackageIssue(package_id=package.id, code="invalid_descriptor")
                    )
        for package in inventory.packages:
            if package.kind == "workspace" and package.id in descriptors:
                await self._prepare(package, descriptors[package.id])
        await self._children(inventory, descriptors)
        self._descriptors = descriptors

    def catalog(self) -> dict[str, Any]:
        """Describe actual activation separately from accepted packaging metadata."""
        return {
            "domains": [
                {
                    **descriptor.model_dump(mode="json"),
                    "route_base": "/api/v1/contributions/" + identity,
                    "mounted": identity in self.active,
                    "available": identity in self.active,
                    "reason": "activated" if identity in self.active else "unavailable",
                    "operations": list(self.active[identity].operations)
                    if identity in self.active
                    else [],
                }
                for identity, descriptor in self._descriptors.items()
            ],
            "issues": [issue.model_dump(mode="json") for issue in self.issues],
        }

    async def _children(
        self, inventory: PackageInventory, descriptors: dict[str, PluginDescriptor]
    ) -> None:
        """Bind children by exact owner/slot version; peers never receive handles."""
        for parent in inventory.packages:
            if parent.kind != "workspace" or parent.id not in self.active:
                continue
            slots = {slot.id: slot for slot in descriptors[parent.id].slots}
            children = [
                p for p in inventory.packages if p.owner_workspace_id == parent.id
            ]
            bindings: list[Binding] = []
            for child in children:
                attachment = child.attachment
                if child.id not in descriptors or attachment is None:
                    continue
                slot = slots.get(attachment.slot_id)
                count = sum(p.attachment == attachment for p in children)
                if (
                    slot is None
                    or slot.version != attachment.contract_version
                    or count > slot.maximum
                ):
                    self.issues.append(
                        PackageIssue(package_id=child.id, code="incompatible_slot")
                    )
                    continue
                await self._prepare(child, descriptors[child.id])
                if child.id in self.active:
                    item = self.active[child.id]
                    bindings.append(
                        Binding(
                            child.id,
                            slot.id,
                            slot.version,
                            item.operations,
                            item.invoke,
                        )
                    )
            parent_runtime = self.active[parent.id]
            if parent_runtime.attach is not None:
                try:
                    async with asyncio.timeout(ACTIVATION_TIMEOUT):
                        await parent_runtime.attach(tuple(bindings))
                except Exception:  # noqa: BLE001 -- fail the affected owner, dispose its children.
                    self.issues.append(
                        PackageIssue(package_id=parent.id, code="attachment_failed")
                    )
                    for child in reversed(children):
                        await self._close_one(child.id)
                    await self._close_one(parent.id)

    async def invoke(self, owner: str, operation: str, payload: JsonValue) -> JsonValue:
        """Dispatch an authenticated command to an accepted owner operation."""
        runtime = self.active.get(owner)
        if runtime is None or operation not in runtime.operations:
            raise ValueError("Missing capability")
        async with asyncio.timeout(ACTIVATION_TIMEOUT):
            return await runtime.invoke(operation, payload)

    async def _close_one(self, owner: str) -> None:
        """Attempt all cleanup for an owner without hiding attributed failures."""
        runtime = self.active.pop(owner, None)
        try:
            if runtime is not None:
                async with asyncio.timeout(ACTIVATION_TIMEOUT):
                    await runtime.close()
        except Exception:  # noqa: BLE001 -- continue cleanup for other owners.
            self.issues.append(PackageIssue(package_id=owner, code="cleanup_failed"))
        try:
            await self.jobs.close(owner)
        except TimeoutError:
            self.issues.append(PackageIssue(package_id=owner, code="jobs_unfinished"))
        module = self._modules.pop(owner, None)
        if module is not None and sys.modules.get(module.__name__) is module:
            del sys.modules[module.__name__]

    async def close(self) -> None:
        """Dispose children before parents and retain cleanup diagnostics."""
        for owner in reversed(tuple(self.active)):
            await self._close_one(owner)

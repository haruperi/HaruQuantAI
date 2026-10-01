"""Non-Executing Package Inventory, Dynamic Slot Composition, and Cascading Removal.

Description:
    This module provides package inventory discovery, path confinement verification,
    runtime capability slot composition, exclusive installation leasing, and
    cascading uninstallation. It exists to enforce modularity, isolate workspace
    capability injection, prevent unauthorized sibling imports, and ensure atomic,
    journaled package removals without corrupting persistent storage. Externally, it
    participates in three key workflows: (1) `BootstrapCoordinator` acquires an
    `InstallationLease`, invokes `scan_packages()` to build an immutable inventory,
    and calls `Composition.start()` to activate workspaces and bind plugin slots; (2)
    The ASGI transport layer (`app.host.transport`) dispatches client operations
    through `Composition.invoke()` and queries `Composition.catalog()` to expose
    available domain routes; and (3) The release verification pipeline and management
    scripts (`scripts/removal_check.py`) compute removal closures via `plan_removal()`,
    execute atomic file quarantines with `apply_removal()`, and verify restoration
    with `restore_removal()`. Internally, `scan_packages()` statically parses
    manifests and computes an SHA-256 fingerprint; `InstallationLease` guards against
    concurrent package operations; and `Composition` imports entrypoints in isolation,
    injecting sandboxed `HostCapabilities` facades.

Purpose:
    FEAT-HOST-PACKAGES: Package Inventory, Slot Composition, and Removal.
    Provides non-executing package inventory discovery, dynamic capability slot
    composition, exclusive installation leasing, and atomic journaled package
    removal.

Key Capabilities:
    - FR-HOST-PACKAGES-INVENTORY-SCAN: Non-Executing Inventory Discovery
      Associated: `scan_packages()`, `PackageInventory`
      Logging: Emits debug log on package discovery with accepted counts,
      issue tallies, and computed inventory digest.
    - FR-HOST-PACKAGES-INSTALLATION-LEASE: Exclusive Lifecycle Fencing
      Associated: `InstallationLease.acquire()`, `InstallationLease.release()`
      Logging: Emits info log when an installation lease is acquired and
      released; emits warning log when a stale fence is reclaimed.
    - FR-HOST-PACKAGES-CASCADING-REMOVAL: Atomic Journaled Removal & Recovery
      Associated: `plan_removal()`, `apply_removal()`, `restore_removal()`
      Logging: Emits info logs on removal plan generation, quarantine
      execution, and verified restoration completion.
    - FR-HOST-PACKAGES-RUNTIME-COMPOSITION: Dynamic Slot Composition Graph
      Associated: `Composition.start()`, `Composition.catalog()`,
      `Composition.invoke()`, `Composition.close()`
      Logging: Emits info logs when composition graph activates or closes,
      and debug logs on operation dispatch.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.jobs import JobManager
    from app.host.packages import Composition, scan_packages
    from app.persistence.resources import ResourceStore

    # 1. Discover installed packages statically
    root = Path(".")
    inventory = scan_packages(root)

    # 2. Build and start runtime composition graph
    resources = ResourceStore(root / "data" / "resources")
    jobs = JobManager(workers=2, memory_limit_bytes=1024**3)
    composition = Composition(root, resources, jobs)
    await composition.start(inventory)

    # 3. Query catalog and invoke operations
    catalog = composition.catalog()
    result = await composition.invoke("workspace.datamanager", "list", {})

    # 4. Gracefully dispose composition graph
    await composition.close()
    ```

CLI Usage:
    Package inventory and single-package removal verification are executed
    via maintenance scripts:
    ```bash
    # Verify package inventory and manifest boundaries
    uv run python scripts/package_inventory.py

    # Execute isolated single-package removal and restore verification
    uv run python scripts/removal_check.py
    ```
"""

from __future__ import annotations

import ast
import asyncio
import atexit
import contextlib
import hashlib
import importlib.util
import inspect
import json
import os
import re
import sys
from collections import Counter
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import IO, Any, Literal, Self, cast
from uuid import uuid4

from pydantic import Field, JsonValue, model_validator

from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    MarketAccess,
    NetworkAccess,
    ResourceAccess,
    SettingsAccess,
    TerminalAccess,
)
from app.host.contracts import Document, PluginDescriptor
from app.host.jobs import JobManager
from app.host.logging import get_logger
from app.host.network import HistoricalNetwork, SourceCredentials
from app.persistence.market import MarketDataStore
from app.persistence.resources import ResourceStore

logger = get_logger(__name__)

MAX_MANIFEST_BYTES = 262144
MAX_CONTRIBUTION_BYTES = 4 * 1024 * 1024
MAX_PACKAGES = 4096
IDENTITY = r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$"
VERSION = r"^\d+\.\d+\.\d+$"
PACKAGE_ROOTS = (
    "app/workspace",
    "app/plugin",
    "app/plugins",
    "app/ui/app/workspace",
    "app/ui/app/plugins",
)
OWNED_ROOTS = (
    *PACKAGE_ROOTS,
    "tests/workspace",
    "tests/plugin",
    "tests/plugins",
    "tests/examples",
    "app/ui/tests/unit/workspace",
    "app/ui/tests/unit/plugins",
    "app/ui/tests/e2e",
)

ACTIVATION_TIMEOUT = 5.0
MAX_INVOCATION_SECONDS = 120.0
HOST_SERVICES = frozenset(
    {
        "host.resources",
        "host.jobs",
        "host.logging",
        "host.settings",
        "host.market_data",
        "host.network",
        "host.terminal",
    }
)


class Attachment(Document):
    """One exact version of one owner's extension slot."""

    slot_id: str = Field(pattern=IDENTITY)
    contract_version: str = Field(pattern=VERSION)


class OwnedPaths(Document):
    """Exact exclusively owned files; no glob or data-root authority."""

    source: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    metadata: tuple[str, ...] = ()

    def files(self) -> tuple[str, ...]:
        """Return all declared files, retaining duplicates for validation."""
        return self.source + self.tests + self.assets + self.examples + self.metadata


class Package(Document):
    """Immutable packaging identity, exclusive ownership and entry locations."""

    schema_version: Literal[1]
    id: str = Field(pattern=IDENTITY)
    kind: Literal["workspace", "plugin"]
    version: str = Field(pattern=VERSION)
    host_contract: Literal["1.0.0"]
    mode: Literal["ui_only", "headless", "paired"]
    owner_workspace_id: str | None = Field(default=None, pattern=IDENTITY)
    attachment: Attachment | None = None
    backend_entry: str | None = None
    ui_entry: str | None = None
    owned_paths: OwnedPaths

    @model_validator(mode="after")
    def coherent(self) -> Self:
        """Reject contradictory modes, attachment, or duplicate owned paths."""
        if self.kind == "plugin":
            if self.owner_workspace_id is None or self.attachment is None:
                raise ValueError("Plugin requires one owner and attachment")
        elif self.owner_workspace_id is not None or self.attachment is not None:
            raise ValueError("Workspace cannot attach to another workspace")
        present = (self.backend_entry is not None, self.ui_entry is not None)
        expected = {"ui_only": (False, True), "headless": (True, False)}
        if present != expected.get(self.mode, (True, True)):
            raise ValueError("Counterpart mode mismatch")
        files = self.owned_paths.files()
        if len(files) != len(set(files)):
            raise ValueError("Duplicate owned path")
        for entry in (self.backend_entry, self.ui_entry):
            if entry is not None and entry not in self.owned_paths.source:
                raise ValueError("Entrypoint must be an owned source file")
        return self


class PackageIssue(Document):
    """Safe attributed validation failure; contains no source or exception text."""

    package_id: str
    code: str
    path: str = ""


class PackageInventory(Document):
    """Validated accepted packages and isolated failures at one source fingerprint."""

    packages: tuple[Package, ...]
    issues: tuple[PackageIssue, ...]
    fingerprint: str


def confined_file(
    root: Path,
    relative: str,
    *,
    exists: bool = True,
    client_workspace_ids: tuple[str, ...] = (),
) -> Path:
    """Validate one normal relative package file without following links.

    Args:
        root: Explicit installation boundary.
        relative: POSIX relative path under a permitted package/test root.
        exists: Require an existing regular file when true.
        client_workspace_ids: Validated workspace identities permitting only their
            exact named external CLI and CLI test files. Empty grants no extension.

    Returns:
        Absolute lexical path confined to root.

    Raises:
        ValueError: Invalid, protected, missing, linked, or escaped path.
    """
    parts = PurePosixPath(relative).parts
    client_paths = {
        name
        for identity in client_workspace_ids
        if re.fullmatch(IDENTITY, identity)
        for name in (
            f"scripts/{identity.rsplit('.', 1)[-1]}_cli.py",
            f"tests/test_{identity.rsplit('.', 1)[-1]}_cli.py",
        )
    }
    if (
        not parts
        or PurePosixPath(relative).as_posix() != relative
        or any(part in {".", ".."} for part in relative.split("/"))
        or re.search(r"[\\:*?]", relative)
        or (
            relative not in client_paths
            and not any(relative.startswith(prefix + "/") for prefix in OWNED_ROOTS)
        )
    ):
        raise ValueError("Invalid or protected package path")
    boundary = root.resolve()
    path = boundary.joinpath(*parts)
    if not path.resolve().is_relative_to(boundary):
        raise ValueError("Escaped package path")
    for item in (path, *path.parents):
        if item == boundary:
            break
        if item.is_symlink() or item.is_junction():
            raise ValueError("Linked package path")
    if exists and not path.is_file():
        raise ValueError("Incomplete package")
    return path


def _read_package(root: Path, path: Path) -> Package:
    """Read one bounded nonexecuting declaration and verify its owned files."""
    relative = path.relative_to(root).as_posix()
    confined_file(root, relative)
    with path.open("rb") as stream:
        data = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(data) > MAX_MANIFEST_BYTES:
        raise ValueError("Package manifest too large")
    package = Package.model_validate_json(data)
    if relative not in package.owned_paths.metadata:
        raise ValueError("Manifest must own itself")
    for name in package.owned_paths.files():
        confined_file(
            root,
            name,
            client_workspace_ids=(package.id,) if package.kind == "workspace" else (),
        )
    return package


def _relationships(packages: list[Package]) -> list[PackageIssue]:
    """Check exclusive file/identity ownership and workspace presence."""
    issues: list[PackageIssue] = []
    ids = Counter(package.id for package in packages)
    files = Counter(
        name.casefold() for package in packages for name in package.owned_paths.files()
    )
    owners = {p.id for p in packages if p.kind == "workspace" and ids[p.id] == 1}
    for package in packages:
        if ids[package.id] != 1:
            issues.append(
                PackageIssue(package_id=package.id, code="ambiguous_identity")
            )
        if any(files[p.casefold()] != 1 for p in package.owned_paths.files()):
            issues.append(PackageIssue(package_id=package.id, code="overlapping_paths"))
        if package.kind == "plugin" and package.owner_workspace_id not in owners:
            issues.append(PackageIssue(package_id=package.id, code="missing_owner"))
    return issues


def scan_packages(root: Path) -> PackageInventory:
    """Discover and isolate malformed ownership documents without importing code.

    Args:
        root: Explicit installation root; only declared contribution roots are read.

    Returns:
        Immutable accepted packages and bounded attributed issues.
    """
    root = root.resolve()
    packages: list[Package] = []
    issues: list[PackageIssue] = []
    for prefix in PACKAGE_ROOTS:
        directory = root / prefix
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("package.json", recurse_symlinks=False)):
            if len(packages) + len(issues) >= MAX_PACKAGES:
                issues.append(PackageIssue(package_id="", code="package_limit"))
                break
            try:
                packages.append(_read_package(root, path))
            except OSError, ValueError:
                issues.append(
                    PackageIssue(
                        package_id="",
                        code="invalid_package",
                        path=path.relative_to(root).as_posix(),
                    )
                )
    issues.extend(_relationships(packages))
    rejected = {issue.package_id for issue in issues}
    accepted = [p for p in packages if p.id not in rejected]
    available_owners = {p.id for p in accepted if p.kind == "workspace"}
    for package in tuple(accepted):
        if (
            package.kind == "plugin"
            and package.owner_workspace_id not in available_owners
        ):
            issues.append(PackageIssue(package_id=package.id, code="missing_owner"))
            accepted.remove(package)
    digest = hashlib.sha256()
    for package in sorted(accepted, key=lambda p: p.id):
        digest.update(package.model_dump_json().encode())
        for name in sorted(package.owned_paths.files()):
            digest.update(name.encode())
            digest.update(hashlib.sha256((root / name).read_bytes()).digest())
    digest.update(json.dumps([i.model_dump() for i in issues], sort_keys=True).encode())
    logger.info(
        "Scanned packages in %s: %d accepted, %d issue(s)",
        root,
        len(accepted),
        len(issues),
    )
    return PackageInventory(
        packages=tuple(accepted), issues=tuple(issues), fingerprint=digest.hexdigest()
    )


# --- Removal & Installation Lease ---


class RemovalPlan(Document):
    """Bounded immutable target closure tied to one validated inventory fingerprint."""

    fingerprint: str
    target_ids: tuple[str, ...]
    files: tuple[str, ...]
    hashes: tuple[str, ...]
    client_workspace_ids: tuple[str, ...] = ()


def _lock_file(fd: int) -> None:
    """Acquire a non-blocking exclusive OS-level lock on the file descriptor."""
    if sys.platform == "win32":
        import msvcrt

        cur = os.lseek(fd, 0, os.SEEK_CUR)
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        finally:
            os.lseek(fd, cur, os.SEEK_SET)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_file(fd: int) -> None:
    """Release an OS-level lock on the file descriptor."""
    if sys.platform == "win32":
        import msvcrt

        cur = os.lseek(fd, 0, os.SEEK_CUR)
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.lseek(fd, cur, os.SEEK_SET)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)


class InstallationLease:
    """Exclusive lifecycle/removal fence; stale files are automatically reclaimed."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.held = False
        self.token = uuid4().hex
        self._file: IO[bytes] | None = None
        self._atexit_hook: Callable[[], None] | None = None

    def acquire(self) -> None:
        """Refuse linked installations or active owners; reclaim stale fences."""
        if self.held:
            raise ValueError("Lease already held")
        if any(
            p.is_symlink() or p.is_junction() for p in (self.root, *self.root.parents)
        ):
            raise ValueError("Linked installation")
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = self.root / ".package-operation.lock"
        file_obj = lock_path.open("a+b")
        try:
            _lock_file(file_obj.fileno())
        except OSError as error:
            file_obj.close()
            raise FileExistsError(
                f"Installation lease already held by active process: root={self.root}"
            ) from error

        file_obj.seek(0)
        existing = file_obj.read()
        if existing:
            logger.warning("Reclaimed stale installation fence: root=%s", self.root)

        file_obj.seek(0)
        file_obj.truncate(0)
        file_obj.write(self.token.encode("utf-8"))
        file_obj.flush()

        self._file = file_obj
        self.held = True
        self._atexit_hook = self._cleanup_on_exit
        atexit.register(self._cleanup_on_exit)
        logger.info("Installation lease acquired: root=%s", self.root)

    def release(self) -> None:
        """Release only this lease's fence; never clear another owner's marker."""
        if not self.held:
            return
        if self._atexit_hook is not None:
            atexit.unregister(self._atexit_hook)
            self._atexit_hook = None

        path = self.root / ".package-operation.lock"
        if self._file is not None:
            try:
                self._file.seek(0)
                content = self._file.read().decode("utf-8")
                if content != self.token:
                    raise ValueError("Installation lease changed")
            finally:
                with contextlib.suppress(OSError):
                    _unlock_file(self._file.fileno())
                self._file.close()
                self._file = None
        elif path.is_file() and path.read_text(encoding="utf-8") != self.token:
            raise ValueError("Installation lease changed")

        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)
        self.held = False
        logger.info("Installation lease released: root=%s", self.root)

    def _cleanup_on_exit(self) -> None:
        """Best-effort release on process exit."""
        if self.held:
            with contextlib.suppress(OSError, ValueError):
                self.release()


def plan_removal(root: Path, inventory: PackageInventory, target: str) -> RemovalPlan:
    """Compute one complete pair or workspace-child closure, excluding all data.

    Raises:
        ValueError: Inventory is invalid or the requested package does not exist.
    """
    if inventory.issues:
        raise ValueError("Cannot remove from an invalid inventory")
    packages = {p.id: p for p in inventory.packages}
    if target not in packages:
        raise ValueError("Unknown removal target")
    targets = {target}
    if packages[target].kind == "workspace":
        targets.update(
            p.id for p in packages.values() if p.owner_workspace_id == target
        )
    files = sorted({f for key in targets for f in packages[key].owned_paths.files()})
    client_workspace_ids = tuple(
        sorted(
            key
            for key in targets
            if packages[key].kind == "workspace"
            and any(
                name.startswith(("scripts/", "tests/test_"))
                for name in packages[key].owned_paths.files()
            )
        )
    )
    hashes = tuple(
        hashlib.sha256(
            confined_file(
                root, f, client_workspace_ids=client_workspace_ids
            ).read_bytes()
        ).hexdigest()
        for f in files
    )
    logger.info("Removal plan generated for target: %s", target)
    return RemovalPlan(
        fingerprint=inventory.fingerprint,
        target_ids=tuple(sorted(targets)),
        files=tuple(files),
        hashes=hashes,
        client_workspace_ids=client_workspace_ids,
    )


def _write_journal(
    path: Path, plan: RemovalPlan, moved: tuple[str, ...], state: str
) -> None:
    """Replace a journal atomically before/after each reversible operation."""
    temp = path.with_suffix(".pending")
    temp.write_text(
        json.dumps({"plan": plan.model_dump(), "moved": moved, "state": state}),
        encoding="utf-8",
    )
    temp.replace(path)


def apply_removal(root: Path, plan: RemovalPlan) -> Path:
    """Apply only an exact current plan under an exclusive stopped-installation fence.

    Files move to a generated quarantine under root. Interrupted apply retains a
    journal; recovery reconciles actual file locations rather than guessing targets.
    No resources, databases or capabilities' other owners are removal targets.

    Returns:
        Journal path for an explicit restore operation.

    Raises:
        ValueError: Plan was forged/stale or a target fails confinement checks.
        OSError: Active/stale fence or filesystem mutation failed.
    """
    lease = InstallationLease(root)
    lease.acquire()
    logger.info(
        "Executing removal for %d package(s): %s (%d files)",
        len(plan.target_ids),
        plan.target_ids,
        len(plan.files),
    )
    try:
        current = scan_packages(root)
        if current.fingerprint != plan.fingerprint or current.issues:
            raise ValueError("Stale removal plan")
        candidates = [plan_removal(root, current, key) for key in plan.target_ids]
        if plan not in candidates:
            raise ValueError("Removal closure mismatch")
        quarantine = root / ".package-quarantine" / uuid4().hex
        if (root / ".package-quarantine").is_symlink() or (
            root / ".package-quarantine"
        ).is_junction():
            raise ValueError("Linked quarantine")
        quarantine.mkdir(parents=True)
        journal = quarantine / "journal.json"
        moved: tuple[str, ...] = ()
        _write_journal(journal, plan, moved, "applying")
        for name in plan.files:
            source = confined_file(
                root, name, client_workspace_ids=plan.client_workspace_ids
            )
            target = quarantine / name
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
            moved += (name,)
            _write_journal(journal, plan, moved, "applying")
        _write_journal(journal, plan, moved, "removed")
        logger.info(
            "Removal completed for targets: %s (quarantine journal=%s)",
            plan.target_ids,
            journal,
        )
        return journal
    finally:
        lease.release()


def restore_removal(root: Path, journal: Path) -> None:
    """Restore verified quarantined bytes without overwriting an installed file.

    Recovery validates the journal, all destinations and content hashes first.
    Repeated recovery is safe when a file was already restored with the same bytes.
    """
    logger.info("Restoring package removal from journal: %s", journal)
    lease = InstallationLease(root)
    lease.acquire()
    try:
        _restore_locked(root.resolve(), journal.absolute())
    finally:
        lease.release()


def _restore_locked(root: Path, journal: Path) -> None:
    """Reconcile interrupted moves using only journaled exact paths and hashes."""
    base = root / ".package-quarantine"
    if (
        journal != journal.resolve()
        or not journal.is_relative_to(base)
        or journal.name != "journal.json"
    ):
        raise ValueError("Invalid recovery journal")
    if any(p.is_symlink() or p.is_junction() for p in (journal, *journal.parents)):
        raise ValueError("Linked recovery path")
    raw = json.loads(journal.read_text(encoding="utf-8"))
    plan = RemovalPlan.model_validate(raw["plan"])
    if len(plan.files) != len(plan.hashes):
        raise ValueError("Invalid recovery hashes")
    pairs: list[tuple[Path, Path]] = []
    for name, digest in zip(plan.files, plan.hashes, strict=True):
        destination = confined_file(
            root, name, exists=False, client_workspace_ids=plan.client_workspace_ids
        )
        source = journal.parent / name
        if any(p.is_symlink() or p.is_junction() for p in (source, *source.parents)):
            raise ValueError("Linked recovery content")
        present = source if source.is_file() else destination
        if (
            present.is_symlink()
            or hashlib.sha256(present.read_bytes()).hexdigest() != digest
        ):
            raise ValueError("Recovery content changed")
        if source.exists() and destination.exists():
            raise ValueError("Recovery would overwrite installed file")
        if source.exists():
            pairs.append((source, destination))
    for source, destination in pairs:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
    _write_journal(journal, plan, (), "restored")
    logger.info(
        "Package restoration completed for plan targets: %s (%d files)",
        plan.target_ids,
        len(pairs),
    )


# --- Runtime Composition & Dynamic Activation ---


@dataclass(frozen=True)
class PreparedContribution:
    """Accepted owner-local operations with explicit disposal and optional binding."""

    operations: tuple[str, ...]
    invoke: Callable[[str, JsonValue], Awaitable[JsonValue]]
    close: Callable[[], Awaitable[None]]
    attach: Callable[[tuple[Binding, ...]], Awaitable[None]] | None = None
    attached_operations: Callable[[], tuple[str, ...]] | None = None
    invocation_seconds: float = 5.0

    def __post_init__(self) -> None:
        """Bound owner-requested invocation budgets independently of activation."""
        if not 0 < self.invocation_seconds <= MAX_INVOCATION_SECONDS:
            raise ValueError(
                "Contribution invocation budget must be within 120 seconds"
            )


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
        source_credentials: tuple[SourceCredentials, ...] = (),
    ) -> None:
        self.root = root
        self.resources = resources
        self.jobs = jobs
        self.settings = settings
        data_root = resources.root.parent
        self.market_data = MarketDataStore(
            data_root, data_root / "database" / "haruquantai.db"
        )
        self.network = HistoricalNetwork(credentials=source_credentials)
        self.active: dict[str, PreparedContribution] = {}
        self.issues: list[PackageIssue] = []
        self._modules: dict[str, ModuleType] = {}
        self._descriptors: dict[str, PluginDescriptor] = {}

    def _descriptor(self, package: Package) -> PluginDescriptor:
        """Validate literal semantic identity and declared host authority."""
        if package.backend_entry is None:
            raise ValueError("No backend entry")
        path = confined_file(self.root, package.backend_entry)
        with path.open("rb") as stream:
            content = stream.read(MAX_CONTRIBUTION_BYTES + 1)
        if len(content) > MAX_CONTRIBUTION_BYTES:
            raise ValueError("Contribution source exceeds size limit")
        tree = ast.parse(content.decode("utf-8"))
        values = [
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "PLUGIN"
                for target in node.targets
            )
        ]
        if len(values) != 1:
            raise ValueError("Expected one literal PLUGIN descriptor")
        descriptor = PluginDescriptor.model_validate(ast.literal_eval(values[0]))
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
        module_name = package.backend_entry.removesuffix(".py").replace("/", ".")
        spec = importlib.util.spec_from_file_location(module_name, path)
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
        contribution_logger = get_logger("app.contribution." + package.id)
        return HostCapabilities(
            ResourceAccess(package.id, package.version, self.resources)
            if "host.resources" in requirements
            else None,
            JobAccess(package.id, self.jobs) if "host.jobs" in requirements else None,
            contribution_logger.info if "host.logging" in requirements else None,
            SettingsAccess(package.id, self.settings)
            if "host.settings" in requirements and self.settings is not None
            else None,
            market_data=MarketAccess(package.id, self.market_data)
            if "host.market_data" in requirements
            else None,
            network=NetworkAccess(package.id, self.network)
            if "host.network" in requirements
            else None,
            terminal=TerminalAccess(package.id)
            if "host.terminal" in requirements
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
        logger.info(
            "Composition graph started: %d active contribution(s)",
            len(self.active),
        )

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
                    self._publish_attached_operations(parent.id, parent_runtime)
                except Exception:  # noqa: BLE001 -- fail the affected owner, dispose its children.
                    self.issues.append(
                        PackageIssue(package_id=parent.id, code="attachment_failed")
                    )
                    for child in reversed(children):
                        await self._close_one(child.id)
                    await self._close_one(parent.id)

    def _publish_attached_operations(
        self, owner: str, runtime: PreparedContribution
    ) -> None:
        """Freeze an unambiguous post-attachment operation allowlist."""
        if runtime.attached_operations is None:
            return
        operations = (*runtime.operations, *runtime.attached_operations())
        if len(operations) != len(set(operations)):
            raise ValueError("Ambiguous attached operation")
        self.active[owner] = replace(runtime, operations=operations)

    async def invoke(self, owner: str, operation: str, payload: JsonValue) -> JsonValue:
        """Dispatch an authenticated command to an accepted owner operation."""
        runtime = self.active.get(owner)
        if runtime is None or operation not in runtime.operations:
            raise ValueError("Missing capability")
        logger.info("Dispatching operation '%s' to owner '%s'", operation, owner)
        async with asyncio.timeout(runtime.invocation_seconds):
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
        await self.network.aclose()
        logger.info("Composition graph closed")

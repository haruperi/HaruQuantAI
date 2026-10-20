# ruff: noqa: INP001
"""Dynamic plugin discovery engine, dependency resolver, and lifecycle manager.

Description:
    Implements the HaruQuant plugin architecture: slot registry, manifest schema
    validation, 1-level/2-level/AST scanning, containment guards, topological
    dependency resolution, isolated module loading, and lazy lifecycle control.

Purpose:
    FEAT-HOST-DISCOVERY: Orthogonal, fail-closed plugin discovery, validation,
    dependency resolution, and thread-safe lazy lifecycle engine.

Key Capabilities:
    - FR-HOST-DISC-SLOT-REGISTRY: Extension slot registry (register_slot -> INFO).
    - FR-HOST-DISC-MANIFEST-SCHEMA: Validate manifests (_check_pat -> ERROR).
    - FR-HOST-DISC-FILESYSTEM-SCANNER: Scan plugin dirs (discover_plugins -> INFO).
    - FR-HOST-DISC-CONTAINMENT-GUARD: Path containment (verify_containment -> DEBUG).
    - FR-HOST-DISC-DEPENDENCY-RESOLVER: Dependency DAG (resolve_dependencies -> INFO).
    - FR-HOST-DISC-LIFECYCLE-MANAGER: Lazy load plugins (attach_plugin -> INFO).
    - FR-HOST-DISC-INSPECTION-API: FastAPI router (create_discovery_router -> INFO).

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.discovery import PluginDiscovery

    engine = PluginDiscovery(search_dirs=[Path("app/plugins")])
    engine.discover_plugins()
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.discovery --scan-dir app/plugins
    ```
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import inspect
import json
import re
import sys
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from fastapi import APIRouter, HTTPException, status
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

__all__ = [
    "PluginDiscovery",
    "PluginHostContext",
    "PluginLifecycleManager",
    "PluginManifest",
    "SlotDefinition",
    "SlotRegistry",
    "create_discovery_router",
]

logger = get_logger(__name__)

SLOT_FR = "FR-HOST-DISC-SLOT-REGISTRY"
SCHEMA_FR = "FR-HOST-DISC-MANIFEST-SCHEMA"
SCAN_FR = "FR-HOST-DISC-FILESYSTEM-SCANNER"
GUARD_FR = "FR-HOST-DISC-CONTAINMENT-GUARD"
DEP_FR = "FR-HOST-DISC-DEPENDENCY-RESOLVER"
LIFE_FR = "FR-HOST-DISC-LIFECYCLE-MANAGER"
API_FR = "FR-HOST-DISC-INSPECTION-API"

PLUGIN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$")
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
ENTRYPOINT_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*:[a-zA-Z_][a-zA-Z0-9_]*$")
MAX_MANIFEST_BYTES = 1_048_576
_EP_ALIAS = AliasChoices("entry_point", "entrypoint")


def _log(level: str, fr_id: str, msg: str, **extra: Any) -> None:
    """Emit structured FR log record with fr_id context."""
    getattr(logger, level)("%s: %s", fr_id, msg, extra={"fr_id": fr_id, **extra})


def _check_pat(val: str, pat: re.Pattern[str], label: str) -> str:
    """Validate string against regex pattern or log and raise ValueError."""
    if not pat.match(val):
        _log("error", SCHEMA_FR, f"Rejected invalid {label} '{val}'.")
        raise ValueError(f"Invalid {label} '{val}'.")
    return val


def _parse_semver_tuple(version_str: str) -> tuple[int, int, int]:
    """Extract (major, minor, patch) integers from a validated semver string."""
    if not (m := SEMVER_PATTERN.match(version_str.strip())):
        raise ValueError(f"Invalid semantic version string: '{version_str}'")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _strict_json_loads(raw_text: str) -> Any:
    """Parse JSON while rejecting duplicate keys and non-finite constants."""

    def _no_dups(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        res: dict[str, Any] = {}
        for k, v in pairs:
            if k in res:
                raise ValueError(f"Duplicate JSON key detected: '{k}'")
            res[k] = v
        return res

    def _no_inf(tok: str) -> Any:
        raise ValueError(f"Non-finite JSON constant rejected: '{tok}'")

    return json.loads(raw_text, object_pairs_hook=_no_dups, parse_constant=_no_inf)


class SlotDefinition(BaseModel):
    """Formal contract for a host extension slot."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    slot_id: str
    description: str
    allow_multiple: bool = True
    required_capabilities: tuple[str, ...] = Field(default_factory=tuple)


_CORE_SLOTS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("workspace.root", "Top-level workspace view.", ("ui.workspace",)),
    ("workspace.panel", "Auxiliary workspace panel.", ()),
    ("data.provider", "Market data source adapter.", ("data.fetch",)),
    ("engine.evaluator", "Strategy candidate evaluator.", ("engine.evaluate",)),
    ("export.platform", "Target platform exporter.", ("export.codegen",)),
    ("export.formatter", "Artifact report formatter.", ()),
    ("validation.crosscheck", "Robustness validation stage.", ("validation.run",)),
    ("diagnostic.probe", "System diagnostic probe.", ()),
    ("broker", "Execution broker gateway adapter.", ("broker.execute",)),
)


class SlotRegistry:
    """Registry of host extension slots available for plugin binding."""

    def __init__(self) -> None:
        self._slots: dict[str, SlotDefinition] = {
            s: SlotDefinition(slot_id=s, description=d, required_capabilities=c)
            for s, d, c in _CORE_SLOTS
        }

    def register_slot(self, slot: SlotDefinition) -> None:
        """Register a custom extension slot definition."""
        self._slots[slot.slot_id] = slot
        _log("info", SLOT_FR, f"Registered slot '{slot.slot_id}'.")

    def get_slot(self, slot_id: str) -> SlotDefinition | None:
        """Look up a registered slot definition by ID."""
        slot = self._slots.get(slot_id)
        _log("debug", SLOT_FR, f"Slot lookup '{slot_id}' (found={slot is not None}).")
        return slot

    def list_slots(self) -> list[SlotDefinition]:
        """Return all registered slot definitions sorted by ID."""
        slots = [self._slots[k] for k in sorted(self._slots)]
        _log("debug", SLOT_FR, f"Listed {len(slots)} registered slots.")
        return slots


class PluginState(StrEnum):
    """Lifecycle states for a discovered plugin."""

    DISCOVERED = "DISCOVERED"
    VALIDATED = "VALIDATED"
    ATTACHED = "ATTACHED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"
    UNINSTALLED = "UNINSTALLED"


_S = PluginState
_ACTIVE = (_S.ENABLED, _S.ATTACHED)
_ATTACHABLE = (_S.VALIDATED, _S.DISABLED, _S.DISCOVERED)
_PRE_ATTACH = (_S.DISCOVERED, _S.VALIDATED)
_INACTIVE = (_S.DISABLED, _S.QUARANTINED, _S.FAILED, _S.UNINSTALLED)


class PluginDependency(BaseModel):
    """Dependency specification declared by a plugin manifest."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    plugin_id: str
    min_version: str | None = None
    max_version: str | None = None
    optional: bool = False

    @model_validator(mode="after")
    def _validate_dep(self) -> PluginDependency:
        _check_pat(self.plugin_id, PLUGIN_ID_PATTERN, "dependency plugin_id")
        if self.min_version is not None:
            _check_pat(self.min_version, SEMVER_PATTERN, "semver")
        if self.max_version is not None:
            _check_pat(self.max_version, SEMVER_PATTERN, "semver")
        return self


class PluginManifest(BaseModel):
    """Validated metadata manifest describing a HaruQuant plugin."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)
    id: str
    name: str = Field(..., min_length=1, max_length=120)
    version: str
    description: str = Field(default="", max_length=2000)
    author: str = Field(default="HaruQuant", max_length=200)
    slot: str = Field(..., min_length=1)
    entry_point: str = Field(..., validation_alias=_EP_ALIAS)
    capabilities: list[str] = Field(default_factory=list)
    dependencies: list[PluginDependency] = Field(default_factory=list)
    settings_schema: dict[str, Any] = Field(default_factory=dict)
    ui_bundle: str | None = None
    enabled_by_default: bool = True

    @property
    def entrypoint(self) -> str:
        """Backward-compatible alias returning ``entry_point``."""
        return self.entry_point

    @model_validator(mode="after")
    def _validate_fields(self) -> PluginManifest:
        _check_pat(self.id, PLUGIN_ID_PATTERN, "plugin id")
        _check_pat(self.version, SEMVER_PATTERN, "version")
        _check_pat(self.entry_point, ENTRYPOINT_PATTERN, "entry_point")
        if self.ui_bundle is not None:
            c = self.ui_bundle.strip()
            if not c or c.startswith(("/", "\\")) or ".." in Path(c).parts:
                _log("error", SCHEMA_FR, f"Unsafe ui_bundle '{self.ui_bundle}'.")
                raise ValueError(f"Unsafe ui_bundle path '{self.ui_bundle}'.")
        return self


class DiscoveryDiagnostic(BaseModel):
    """Structured diagnostic event generated during plugin discovery or loading."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    plugin_id: str | None = None
    source_path: str
    severity: str = "ERROR"
    code: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PluginRecord(BaseModel):
    """Runtime registry record tracking a discovered plugin's state and metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
    manifest: PluginManifest
    package_dir: Path
    manifest_path: Path
    is_single_file: bool = False
    state: PluginState = PluginState.DISCOVERED
    enabled: bool = True
    load_order: int | None = None
    diagnostics: list[DiscoveryDiagnostic] = Field(default_factory=list)
    attached_at: str | None = None
    instance: Any = Field(default=None, exclude=True)

    def to_summary_dict(self) -> dict[str, Any]:
        """Serialize the plugin record into a JSON-safe summary dictionary."""
        excl = {"settings_schema", "ui_bundle", "enabled_by_default"}
        inc = {"enabled", "load_order", "is_single_file", "attached_at", "diagnostics"}
        res = {**self.manifest.model_dump(exclude=excl), **self.model_dump(include=inc)}
        ep, st, pd = self.manifest.entrypoint, self.state.value, str(self.package_dir)
        res.update(entrypoint=ep, state=st, package_dir=pd)
        return res


class DiscoveryReport(BaseModel):
    """Consolidated report emitted after scanning and resolving plugins."""

    model_config = ConfigDict(extra="forbid")
    scanned_dirs: list[str]
    total_discovered: int
    validated_count: int
    attached_count: int
    enabled_count: int
    quarantined_count: int
    failed_count: int
    load_order: list[str]
    diagnostics: list[DiscoveryDiagnostic]


def verify_containment(target_path: Path, allowed_root: Path) -> Path:
    """Verify that ``target_path`` resolves strictly inside ``allowed_root``."""
    root = allowed_root.resolve()
    try:
        resolved = target_path.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        msg = f"Target path does not exist or OS error: {target_path} ({exc})"
        _log("exception", GUARD_FR, msg)
        raise ValueError(msg) from exc
    if not resolved.is_relative_to(root):
        msg = f"Containment violation: '{target_path}' outside '{root}'."
        _log("error", GUARD_FR, msg)
        raise ValueError(msg)
    _log("debug", GUARD_FR, f"Verified containment of '{resolved}'.")
    return resolved


class PluginHostContext:
    """Sandboxed host interface provided to plugins during initialization."""

    def __init__(
        self,
        plugin_id: str,
        manifest: PluginManifest,
        package_dir: Path,
        data_dir: Path,
        settings: dict[str, Any] | None = None,
    ) -> None:
        self.plugin_id = plugin_id
        self.manifest = manifest
        self.package_dir = package_dir
        self.data_dir = data_dir
        self.settings: dict[str, Any] = dict(settings or {})
        self.logger = get_logger(f"app.plugins.{plugin_id}")
        self.routers: list[APIRouter] = []
        self.teardown_callbacks: list[Callable[[], None]] = []
        self.event_handlers: dict[str, list[Callable[..., Any]]] = {}
        self.job_handlers: dict[str, Callable[..., Any]] = {}

    def ensure_data_dir(self) -> Path:
        """Create and return the plugin's isolated persistent data directory."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir

    def register_router(self, router: APIRouter) -> None:
        """Register a FastAPI ``APIRouter`` owned by this plugin."""
        self.routers.append(router)

    def register_teardown(self, callback: Callable[[], None]) -> None:
        """Register a cleanup callback invoked when the plugin is disabled."""
        self.teardown_callbacks.append(callback)

    def subscribe_event(self, event_topic: str, handler: Callable[..., Any]) -> None:
        """Subscribe a handler callable to a named host event topic."""
        self.event_handlers.setdefault(event_topic, []).append(handler)

    def register_job_handler(self, job_type: str, handler: Callable[..., Any]) -> None:
        """Register a background job handler callable for a specific job type."""
        self.job_handlers[job_type] = handler


class PluginDiscovery:
    """Scans plugin directories, validates manifests, and resolves dependencies."""

    def __init__(
        self, search_dirs: list[Path], slot_registry: SlotRegistry | None = None
    ) -> None:
        self.search_dirs = [Path(d) for d in search_dirs]
        self.slot_registry = slot_registry or SlotRegistry()
        self.registry: dict[str, PluginRecord] = {}
        self.diagnostics: list[DiscoveryDiagnostic] = []
        self.load_order: list[str] = []
        self.default_lifecycle: PluginLifecycleManager | None = None

    def diag(
        self, pid: Any, path: Any, code: str, msg: str, sev: str = "ERROR"
    ) -> None:
        """Create and store a structured discovery diagnostic."""
        kw: Any = {"plugin_id": pid, "source_path": str(path), "severity": sev}
        d = DiscoveryDiagnostic(**kw, code=code, message=msg)
        self.diagnostics.append(d)
        if pid and pid in self.registry:
            self.registry[pid].diagnostics.append(d)
        lvl = {"ERROR": "error", "WARNING": "warning"}.get(sev, "info")
        _log(lvl, SCAN_FR, f"[{code}] plugin={pid or '<unknown>'}: {msg}")

    def _quarantine(self, r: PluginRecord, c: str, msg: str, p: Any = None) -> bool:
        r.state = _S.QUARANTINED
        self.diag(r.manifest.id, p or r.manifest_path, c, msg)
        return False

    def _check_path(
        self, p: Path, root: Path, r: Any = None, c: str = ""
    ) -> Path | None:
        try:
            return verify_containment(p, root)
        except ValueError as exc:
            err_c = c or "CONTAINMENT_VIOLATION"
            if r is not None:
                self._quarantine(r, err_c, str(exc), p)
            else:
                self.diag(None, p, err_c, str(exc))
            return None

    def discover_plugins(self) -> dict[str, PluginRecord]:
        """Scan configured ``search_dirs`` and populate the plugin registry."""
        self.registry.clear()
        self.diagnostics.clear()
        self.load_order.clear()
        _log("info", SCAN_FR, f"Starting discovery in {len(self.search_dirs)} dirs.")
        skip = (".", "__pycache__", "exchanges")
        for s_dir in self.search_dirs:
            if not s_dir.exists():
                _log("info", SCAN_FR, f"Skipping non-existent search dir: {s_dir}")
            elif not s_dir.is_dir():
                self.diag(None, s_dir, "SEARCH_PATH_NOT_DIR", "Not a dir.", "WARNING")
            else:
                root = s_dir.resolve()
                for item in sorted(root.iterdir()):
                    if not item.name.startswith(skip):
                        self._inspect_root_entry(item, root)
        _log("info", SCAN_FR, f"Discovery complete ({len(self.registry)} plugins).")
        return self.registry

    def _inspect_root_entry(self, item: Path, root: Path) -> None:
        if not self._check_path(item, root):
            return
        if item.is_dir():
            if (man := self._find_manifest(item)) is not None:
                self._scan_pkg(item, man, root)
            else:
                self._scan_slot_family_dir(item, root)
        elif item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            self._scan_file(item, root)

    def _scan_slot_family_dir(self, family_dir: Path, root: Path) -> None:
        cands = [s for s in family_dir.iterdir() if s.is_dir() or s.is_symlink()]
        subs = sorted(s for s in cands if not s.name.startswith((".", "__pycache__")))
        miss = "Directory plugin missing plugin.json or manifest.json."
        if not subs:
            self.diag(None, family_dir, "MISSING_MANIFEST", miss)
        for sub in subs:
            if self._check_path(sub, root) and sub.is_dir():
                if (man := self._find_manifest(sub)) is not None:
                    self._scan_pkg(sub, man, root)
                else:
                    self.diag(None, sub, "MISSING_MANIFEST", miss)

    @staticmethod
    def _find_manifest(d: Path) -> Path | None:
        names = ("plugin.json", "manifest.json")
        return next((c for n in names if (c := d / n).exists() or c.is_symlink()), None)

    def _scan_pkg(self, pkg_dir: Path, man_path: Path, root: Path) -> None:
        res_man = self._check_path(man_path, root)
        if not res_man or not self._check_path(res_man, pkg_dir.resolve()):
            return
        try:
            if res_man.stat().st_size > MAX_MANIFEST_BYTES:
                self.diag(None, res_man, "MANIFEST_TOO_LARGE", "Manifest too large.")
                return
            raw_data = _strict_json_loads(res_man.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            _log("exception", SCHEMA_FR, f"Malformed JSON manifest at {res_man}")
            self.diag(None, res_man, "MALFORMED_MANIFEST_JSON", str(exc))
            return
        if not isinstance(raw_data, dict):
            _log("error", SCHEMA_FR, f"Manifest root not object at {res_man}.")
            self.diag(None, res_man, "INVALID_MANIFEST_ROOT", "Root must be object.")
            return
        self._reg_man(raw_data, pkg_dir.resolve(), res_man, False, root)

    def _scan_file(self, path: Path, root: Path) -> None:
        try:
            if path.stat().st_size > MAX_MANIFEST_BYTES:
                self.diag(None, path, "PLUGIN_FILE_TOO_LARGE", "File too large.")
                return
            tree = ast.parse(path.read_text("utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            self.diag(None, path, "AST_PARSE_ERROR", str(exc))
            return
        for n in tree.body:
            tgts = getattr(n, "targets", [getattr(n, "target", None)])
            if any(getattr(t, "id", None) == "PLUGIN_MANIFEST" for t in tgts) and (
                val := getattr(n, "value", None)
            ):
                try:
                    ev = ast.literal_eval(val)
                except (ValueError, SyntaxError) as exc:
                    self.diag(None, path, "INVALID_AST_MANIFEST", str(exc))
                    return
                if isinstance(ev, dict):
                    self._reg_man(ev, path.parent.resolve(), path.resolve(), True, root)
                return

    def _reg_man(self, raw: Any, pkg: Path, mp: Path, single: bool, root: Path) -> None:
        cid = raw.get("id") if isinstance(raw.get("id"), str) else None
        _log("debug", SCHEMA_FR, f"Validating manifest '{cid}' at {mp}.")
        try:
            man = PluginManifest.model_validate(raw)
        except ValidationError as exc:
            self.diag(cid, mp, "MANIFEST_SCHEMA_INVALID", str(exc))
            return
        if man.id in self.registry:
            self.diag(man.id, mp, "DUPLICATE_PLUGIN_ID", "Duplicate ID.")
            return
        kw: Any = {"package_dir": pkg, "manifest_path": mp, "is_single_file": single}
        rec = PluginRecord(manifest=man, enabled=man.enabled_by_default, **kw)
        self.registry[man.id] = rec
        self._verify_record_artifacts(rec, root)

    def _verify_record_artifacts(self, r: PluginRecord, root: Path) -> None:
        mod_part, _ = r.manifest.entry_point.split(":", 1)
        if r.is_single_file:
            if mod_part != r.manifest_path.stem:
                self._quarantine(r, "SINGLE_FILE_ENTRYPOINT_MISMATCH", "Bad stem.")
            return
        rel = Path(*mod_part.split("."))
        py_f, init_f = r.package_dir / f"{rel}.py", r.package_dir / rel / "__init__.py"
        t = py_f if (py_f.exists() or py_f.is_symlink()) else init_f
        if not t.exists() and not t.is_symlink():
            self._quarantine(r, "ENTRYPOINT_MODULE_MISSING", f"Missing '{mod_part}'.")
            return
        ec = "ENTRYPOINT_CONTAINMENT_VIOLATION"
        if not (
            self._check_path(t, root, r, ec)
            and self._check_path(t, r.package_dir, r, ec)
        ):
            return
        if (ub := r.manifest.ui_bundle) is not None:
            bp = r.package_dir / ub
            if not bp.exists() and not bp.is_symlink():
                self._quarantine(r, "UI_BUNDLE_MISSING", "Missing bundle.", bp)
            else:
                self._check_path(
                    bp, r.package_dir, r, "UI_BUNDLE_CONTAINMENT_VIOLATION"
                )

    def resolve_dependencies(self) -> list[str]:
        """Validate slots, capabilities, and dependencies; compute topological order."""
        self.load_order.clear()
        self._validate_slots_and_capabilities()
        items, q = sorted(self.registry.items()), _S.QUARANTINED
        while any(r.state != q and not self._check_deps(p, r) for p, r in items):
            pass
        ordered = self._compute_topological_order()
        for idx, pid in enumerate(ordered):
            self.registry[pid].state = _S.VALIDATED
            self.registry[pid].load_order = idx
        self.load_order = ordered
        _log("info", DEP_FR, f"Resolved {len(ordered)} plugins: {ordered}")
        return list(self.load_order)

    def _validate_slots_and_capabilities(self) -> None:
        bindings: dict[str, str] = {}
        for pid, rec in sorted(self.registry.items()):
            if rec.state == _S.QUARANTINED:
                continue
            s_def = self.slot_registry.get_slot(rec.manifest.slot)
            if s_def is None:
                self._quarantine(rec, "UNKNOWN_EXTENSION_SLOT", "Unknown slot.")
                continue
            caps = rec.manifest.capabilities
            if miss := [c for c in s_def.required_capabilities if c not in caps]:
                self._quarantine(rec, "MISSING_REQUIRED_CAPABILITIES", f"Need {miss}.")
                continue
            if not s_def.allow_multiple and rec.enabled:
                if s_def.slot_id in bindings:
                    self._quarantine(rec, "SLOT_CARDINALITY_CONFLICT", "Slot bound.")
                    continue
                bindings[s_def.slot_id] = pid

    def _check_deps(self, pid: str, rec: PluginRecord) -> bool:
        path = rec.manifest_path
        for dep in rec.manifest.dependencies:
            did = dep.plugin_id
            if did == pid:
                return self._quarantine(rec, "SELF_DEPENDENCY", "Self dependency.")
            t = self.registry.get(did)
            if t is None or t.state == _S.QUARANTINED:
                if dep.optional:
                    c = "OPTIONAL_DEPENDENCY_UNAVAILABLE"
                    self.diag(pid, path, c, "Opt.", "WARNING")
                    continue
                _log("error", DEP_FR, f"'{pid}' missing required dep '{did}'.")
                return self._quarantine(rec, "MISSING_REQUIRED_DEPENDENCY", f"No {did}")
            if not self._v_ok(t.manifest.version, dep.min_version, dep.max_version):
                if dep.optional:
                    c = "OPTIONAL_DEPENDENCY_VERSION_MISMATCH"
                    self.diag(pid, path, c, "Ver.", "WARNING")
                    continue
                _log("error", DEP_FR, f"'{pid}' incompatible with '{did}'.")
                return self._quarantine(rec, "DEPENDENCY_VERSION_INCOMPATIBLE", "Ver.")
        return True

    def _compute_topological_order(self) -> list[str]:
        q = _S.QUARANTINED
        active = sorted(p for p, r in self.registry.items() if r.state != q)
        in_deg: dict[str, int] = dict.fromkeys(active, 0)
        dep_map: dict[str, list[str]] = {pid: [] for pid in active}
        for pid in active:
            for d in self.registry[pid].manifest.dependencies:
                t = self.registry.get(d.plugin_id)
                v = d.min_version, d.max_version
                if t and d.plugin_id in in_deg and self._v_ok(t.manifest.version, *v):
                    in_deg[pid] += 1
                    dep_map[d.plugin_id].append(pid)

        ready = sorted(pid for pid, deg in in_deg.items() if deg == 0)
        ordered: list[str] = []
        while ready:
            ordered.append(curr := ready.pop(0))
            for dep_id in sorted(dep_map[curr]):
                in_deg[dep_id] -= 1
                if in_deg[dep_id] == 0:
                    ready = sorted([*ready, dep_id])

        if len(ordered) < len(active):
            for pid in (p for p in active if p not in ordered):
                _log("error", DEP_FR, f"Circular dependency involving '{pid}'.")
                self._quarantine(self.registry[pid], "CIRCULAR_DEPENDENCY", "Cycle.")
        return ordered

    @staticmethod
    def _v_ok(act: str, min_v: str | None, max_v: str | None) -> bool:
        t = _parse_semver_tuple(act)
        if min_v is not None and t < _parse_semver_tuple(min_v):
            return False
        return not (max_v is not None and t > _parse_semver_tuple(max_v))

    def _lc(self) -> PluginLifecycleManager:
        if self.default_lifecycle is None:
            base = self.search_dirs[0].parent if self.search_dirs else Path()
            self.default_lifecycle = PluginLifecycleManager(self, base / "data/plugins")
        return self.default_lifecycle

    def get_instance(self, plugin_id: str) -> Any:
        """Thread-safe lazy instantiation and caching of a validated plugin."""
        return self._lc().get_instance(plugin_id)

    def get_instances_for_slot(self, slot_id: str) -> list[Any]:
        """Return all active plugin instances registered for ``slot_id``."""
        return self._lc().get_instances_for_slot(slot_id)


type _FactoryHook = Callable[[str, PluginRecord, PluginHostContext], Any]


class PluginLifecycleManager:
    """Manages thread-safe plugin loading, lazy caching, enable/disable, and reload."""

    def __init__(
        self,
        discovery_engine: PluginDiscovery,
        data_root: Path,
        plugin_settings: dict[str, dict[str, Any]] | None = None,
        instance_factory_hook: _FactoryHook | None = None,
    ) -> None:
        self.discovery = discovery_engine
        self.data_root = Path(data_root)
        self.plugin_settings: dict[str, dict[str, Any]] = dict(plugin_settings or {})
        self.instance_factory_hook = instance_factory_hook
        self.contexts: dict[str, PluginHostContext] = {}
        self._loaded_modules: dict[str, list[str]] = {}
        self._lock = threading.RLock()
        self.discovery.default_lifecycle = self

    def _fail(self, rec: PluginRecord, code: str, msg: str) -> bool:
        rec.instance, rec.state = None, _S.FAILED
        for name in self._loaded_modules.pop(rec.manifest.id, []):
            sys.modules.pop(name, None)
        self.discovery.diag(rec.manifest.id, rec.manifest_path, code, msg)
        return False

    def load_and_attach_all(self) -> DiscoveryReport:
        """Attach and enable all validated plugins in topological load order."""
        with self._lock:
            if not self.discovery.load_order and self.discovery.registry:
                self.discovery.resolve_dependencies()
            for pid in self.discovery.load_order:
                if (rec := self.discovery.registry.get(pid)) is not None:
                    if not rec.enabled:
                        rec.state = _S.DISABLED
                        _log("info", LIFE_FR, f"Plugin '{pid}' disabled; skipping.")
                    else:
                        self.attach_plugin(pid)
            return self.build_report()

    def attach_plugin(self, pid: str) -> bool:
        """Dynamically import and attach a single validated plugin."""
        with self._lock:
            rec = self.discovery.registry.get(pid)
            if rec is None:
                _log("error", LIFE_FR, f"Cannot attach unknown plugin '{pid}'.")
                return False
            if rec.state in _ACTIVE and rec.instance is not None:
                return True
            if rec.state not in _ATTACHABLE:
                _log("error", LIFE_FR, f"Cannot attach '{pid}' ({rec.state}).")
                return False
            if not self._ensure_deps_attached(rec):
                return False
            cfg, d_dir = self.plugin_settings.get(pid, {}), self.data_root / pid
            ctx = PluginHostContext(pid, rec.manifest, rec.package_dir, d_dir, cfg)
            try:
                inst = self._call_ep(pid, rec, ctx)
            except Exception as exc:  # noqa: BLE001
                _log("exception", LIFE_FR, f"Failed to attach plugin '{pid}'")
                return self._fail(rec, "ATTACHMENT_RUNTIME_FAILURE", str(exc))
            self.contexts[pid] = ctx
            rec.instance = inst if inst is not None else ctx
            rec.attached_at = datetime.now(UTC).isoformat()
            rec.state, rec.enabled = _S.ENABLED, True
            _log("info", LIFE_FR, f"Attached and enabled plugin '{pid}'.")
            return True

    def _ensure_deps_attached(self, rec: PluginRecord) -> bool:
        for dep in rec.manifest.dependencies:
            if dep.optional:
                continue
            d_rec = self.discovery.registry.get(dep.plugin_id)
            if d_rec is None:
                return self._fail(rec, "DEPENDENCY_NOT_ENABLED", "Missing dep.")
            if d_rec.state in _PRE_ATTACH and d_rec.enabled:
                self.attach_plugin(dep.plugin_id)
            if d_rec.state != _S.ENABLED:
                return self._fail(rec, "DEPENDENCY_NOT_ENABLED", "Dep not enabled.")
        return True

    def _call_ep(self, pid: str, rec: PluginRecord, ctx: PluginHostContext) -> Any:
        hook = self.instance_factory_hook
        if hook and (inst := hook(pid, rec, ctx)) is not None:
            return inst
        mod_p, attr = rec.manifest.entry_point.split(":", 1)
        mod = self._load_plugin_module(pid, rec, mod_p)
        if not callable(target := getattr(mod, attr, None)):
            raise TypeError(f"Entrypoint '{mod_p}:{attr}' missing or not callable.")
        try:
            params = list(inspect.signature(target).parameters.values())
        except ValueError, TypeError:
            return target(ctx)
        if not params:
            return target()
        p0 = params[0]
        pos = (p0.POSITIONAL_ONLY, p0.POSITIONAL_OR_KEYWORD)
        names = {"ctx", "context", "host_context", "host"}
        ann = "PluginHostContext" in str(p0.annotation)
        c_arg = p0.default is p0.empty or p0.name in names or ann
        takes_ctx = p0.kind == p0.VAR_POSITIONAL or (p0.kind in pos and c_arg)
        return target(ctx) if takes_ctx else target()

    def _load_plugin_module(self, pid: str, rec: PluginRecord, mod_part: str) -> Any:
        ns = f"_haruquant_plugins.{re.sub(r'[^a-zA-Z0-9_]', '_', pid)}"
        loaded: list[str] = []
        self._loaded_modules[pid] = loaded
        locs = None if rec.is_single_file else [str(rec.package_dir)]
        im_spec = importlib.util.spec_from_file_location

        def _load(name: str, path: Path) -> Any:
            s = im_spec(name, path, submodule_search_locations=locs)
            if s is None or s.loader is None:
                raise ImportError(f"Could not create module spec for '{name}'.")
            m = importlib.util.module_from_spec(s)
            sys.modules[name] = m
            loaded.append(name)
            s.loader.exec_module(m)
            return m

        pkg_init = rec.package_dir / "__init__.py"
        if not rec.is_single_file and pkg_init.exists():
            _load(ns, pkg_init)
        rel = Path(*mod_part.split("."))
        py_f = rec.package_dir / f"{rel}.py"
        pkg_f = py_f if py_f.exists() else rec.package_dir / rel / "__init__.py"
        t_f = rec.manifest_path if rec.is_single_file else pkg_f
        return _load(f"{ns}.{mod_part}", t_f)

    def get_instance(self, plugin_id: str) -> Any:
        """Thread-safe lazy instantiation and caching of a validated plugin."""
        with self._lock:
            rec = self.discovery.registry.get(plugin_id)
            if rec is None:
                _log("debug", LIFE_FR, f"get_instance('{plugin_id}') -> None.")
                return None
            if rec.instance is not None and rec.state in _ACTIVE:
                _log("debug", LIFE_FR, f"Returning cached instance for '{plugin_id}'.")
                return rec.instance
            if not rec.enabled or rec.state in _INACTIVE:
                return None
            if rec.state == _S.DISCOVERED:
                self.discovery.resolve_dependencies()
                rec = self.discovery.registry.get(plugin_id)
            if rec and rec.state == _S.VALIDATED and self.attach_plugin(plugin_id):
                _log("info", LIFE_FR, f"Lazily instantiated '{plugin_id}'.")
                return rec.instance
            return None

    def get_instances_for_slot(self, slot_id: str) -> list[Any]:
        """Return all active plugin instances bound to ``slot_id``."""
        with self._lock:
            regs, s, d = self.discovery.registry, slot_id, _S.DISCOVERED
            if any(r.manifest.slot == s and r.state == d for r in regs.values()):
                self.discovery.resolve_dependencies()
            order = list(dict.fromkeys([*self.discovery.load_order, *sorted(regs)]))
            ok = {p for p, r in regs.items() if r.manifest.slot == s and r.enabled}
            insts = [self.get_instance(p) for p in order if p in ok]
            res = [i for i in insts if i is not None]
            _log("debug", LIFE_FR, f"Resolved {len(res)} instances for '{slot_id}'.")
            return res

    def disable_plugin(self, pid: str, *, cascade: bool = True) -> bool:
        """Disable an active plugin and invoke its teardown callbacks."""
        with self._lock:
            if (rec := self.discovery.registry.get(pid)) is None:
                return False
            if rec.state == _S.DISABLED:
                return True
            if cascade:
                for oid, r in self.discovery.registry.items():
                    deps = r.manifest.dependencies
                    need = any(d.plugin_id == pid and not d.optional for d in deps)
                    if oid != pid and r.state == _S.ENABLED and need:
                        self.disable_plugin(oid, cascade=True)
            self._run_teardown(pid, rec)
            for name in self._loaded_modules.pop(pid, []):
                sys.modules.pop(name, None)
            rec.instance, rec.state, rec.enabled = None, _S.DISABLED, False
            _log("info", LIFE_FR, f"Disabled plugin '{pid}'.")
            return True

    def _run_teardown(self, pid: str, rec: PluginRecord) -> None:
        if (ctx := self.contexts.pop(pid, None)) is None:
            return
        for cb in reversed(ctx.teardown_callbacks):
            try:
                cb()
            except Exception as exc:  # noqa: BLE001
                _log("exception", LIFE_FR, f"Teardown error for '{pid}'")
                c = "TEARDOWN_CALLBACK_ERROR"
                self.discovery.diag(pid, rec.manifest_path, c, str(exc), "WARNING")

    def enable_plugin(self, pid: str) -> bool:
        """Enable a previously disabled or validated plugin."""
        with self._lock:
            rec = self.discovery.registry.get(pid)
            if rec is None or rec.state in (_S.QUARANTINED, _S.UNINSTALLED):
                return False
            if rec.state == _S.ENABLED:
                return True
            s_def = self.discovery.slot_registry.get_slot(rec.manifest.slot)
            if s_def and not s_def.allow_multiple:
                sid, en = s_def.slot_id, _S.ENABLED
                for oid, r in self.discovery.registry.items():
                    if oid != pid and r.manifest.slot == sid and r.state == en:
                        c = "SLOT_CARDINALITY_CONFLICT"
                        self.discovery.diag(pid, rec.manifest_path, c, oid)
                        return False
            rec.enabled = True
            return self.attach_plugin(pid)

    def reload_plugin(self, plugin_id: str) -> bool:
        """Disable and re-attach a plugin to pick up code changes."""
        with self._lock:
            if (rec := self.discovery.registry.get(plugin_id)) is None:
                return False
            if rec.state == _S.ENABLED:
                self.disable_plugin(plugin_id, cascade=False)
            rec.state, rec.enabled = _S.VALIDATED, True
            return self.attach_plugin(plugin_id)

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Disable and remove a plugin from the runtime registry."""
        with self._lock:
            if (rec := self.discovery.registry.get(plugin_id)) is None:
                return False
            if rec.state == _S.ENABLED:
                self.disable_plugin(plugin_id, cascade=True)
            rec.state = _S.UNINSTALLED
            self.discovery.registry.pop(plugin_id, None)
            if plugin_id in self.discovery.load_order:
                self.discovery.load_order.remove(plugin_id)
            _log("info", LIFE_FR, f"Unregistered plugin '{plugin_id}'.")
            return True

    def build_report(self) -> DiscoveryReport:
        """Build a consolidated ``DiscoveryReport`` of current plugin states."""
        with self._lock:
            st = [r.state for r in self.discovery.registry.values()]
            kw: Any = {
                "scanned_dirs": [str(d) for d in self.discovery.search_dirs],
                "total_discovered": len(st),
                "validated_count": sum(s in (_S.VALIDATED, _S.ENABLED) for s in st),
                "attached_count": sum(s in _ACTIVE for s in st),
                "enabled_count": st.count(_S.ENABLED),
                "quarantined_count": st.count(_S.QUARANTINED),
                "failed_count": st.count(_S.FAILED),
                "load_order": list(self.discovery.load_order),
                "diagnostics": list(self.discovery.diagnostics),
            }
            return DiscoveryReport(**kw)


def _req_rec(lc: PluginLifecycleManager, pid: str) -> PluginRecord:
    if (rec := lc.discovery.registry.get(pid)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Plugin '{pid}' not found.")
    return rec


def create_discovery_router(lifecycle: PluginLifecycleManager) -> APIRouter:
    """Create a FastAPI router exposing plugin discovery and lifecycle controls."""
    router = APIRouter(prefix="/discovery", tags=["plugin-discovery"])
    _log("info", API_FR, "Created FastAPI plugin discovery router.")

    @router.get("/plugins")
    def list_plugins() -> dict[str, Any]:
        vals = lifecycle.discovery.registry.values()
        recs = sorted(
            vals, key=lambda r: (r.load_order is None, r.load_order or 0, r.manifest.id)
        )
        rep = lifecycle.build_report().model_dump()
        return {"report": rep, "plugins": [r.to_summary_dict() for r in recs]}

    @router.get("/plugins/{plugin_id}")
    def get_plugin_detail(plugin_id: str) -> dict[str, Any]:
        return _req_rec(lifecycle, plugin_id).to_summary_dict()

    @router.post("/plugins/{plugin_id}/enable")
    def enable_plugin_endpoint(plugin_id: str) -> dict[str, Any]:
        rec = _req_rec(lifecycle, plugin_id)
        ok = lifecycle.enable_plugin(plugin_id)
        _log("info", API_FR, f"API enable for '{plugin_id}' (success={ok}).")
        if not ok:
            diags = [d.model_dump() for d in rec.diagnostics]
            err = {"state": rec.state.value, "diagnostics": diags}
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err)
        return rec.to_summary_dict()

    @router.post("/plugins/{plugin_id}/disable")
    def disable_plugin_endpoint(plugin_id: str) -> dict[str, Any]:
        rec = _req_rec(lifecycle, plugin_id)
        lifecycle.disable_plugin(plugin_id)
        _log("info", API_FR, f"API disable completed for '{plugin_id}'.")
        return rec.to_summary_dict()

    @router.post("/plugins/{plugin_id}/reload")
    def reload_plugin_endpoint(plugin_id: str) -> dict[str, Any]:
        rec = _req_rec(lifecycle, plugin_id)
        ok = lifecycle.reload_plugin(plugin_id)
        _log("info", API_FR, f"API reload for '{plugin_id}' (success={ok}).")
        if not ok:
            raise HTTPException(status.HTTP_409_CONFLICT, "Reload failed.")
        return rec.to_summary_dict()

    @router.get("/slots")
    def list_slots_endpoint() -> dict[str, Any]:
        regs = lifecycle.discovery.registry.values()
        act_m = [r.manifest for r in regs if r.state == _S.ENABLED]
        slots = [
            {
                **s.model_dump(),
                "required_capabilities": list(s.required_capabilities),
                "bound_plugins": sorted(m.id for m in act_m if m.slot == s.slot_id),
            }
            for s in lifecycle.discovery.slot_registry.list_slots()
        ]
        return {"slots": slots}

    return router


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint to scan plugin directories and print a discovery report."""
    parser = argparse.ArgumentParser(prog="app.host.discovery")
    parser.add_argument("--scan-dir", action="append", default=[])
    args = parser.parse_args(argv)
    paths = [Path(p) for p in args.scan_dir] if args.scan_dir else [Path("app/plugins")]
    engine = PluginDiscovery(search_dirs=paths)
    engine.discover_plugins()
    engine.resolve_dependencies()
    lifecycle = PluginLifecycleManager(engine, data_root=Path("data/plugins"))
    report = lifecycle.build_report()
    sys.stdout.write(json.dumps(report.model_dump(), indent=2) + "\n")
    return 0 if report.quarantined_count == 0 and report.failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

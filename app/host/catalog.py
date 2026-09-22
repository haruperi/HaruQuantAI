"""Host catalog owner: discovery, snapshots, and admission."""

from __future__ import annotations

import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, override

from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import Feature, FeatureSpec
from app.plugins.schema import validate_identifier
from app.plugins.spec import (
    CURRENT_METAMODEL_MAJOR,
    CatalogEntryView,
    CatalogView,
    OperationContribution,
    OperationSpec,
    PluginContribution,
    PluginRef,
)
from app.plugins.wire import catalog_entry_view_to_wire, to_canonical_json_bytes


class CatalogError(RuntimeError):
    """Base error for catalog failures."""


class CatalogUnavailableError(CatalogError):
    """Raised when catalog operations are attempted on an unready catalog."""


class CatalogAdmissionError(CatalogError):
    """Raised when an operation cannot be admitted."""


@dataclass(frozen=True, slots=True)
class CatalogRoot:
    """Configuration for an explicit filesystem plugin family root."""

    logical_family: str
    path: Path
    accepted_kinds: tuple[str, ...]
    max_files: int = 100
    max_source_bytes: int = 1_000_000

    def __post_init__(self) -> None:
        """Validate catalog root configuration."""
        validate_identifier(self.logical_family, "CatalogRoot logical_family")
        if not isinstance(self.path, Path):
            raise TypeError("CatalogRoot path must be a pathlib.Path")
        if not isinstance(self.accepted_kinds, tuple) or not self.accepted_kinds:
            raise ValueError("CatalogRoot accepted_kinds must be a non-empty tuple")
        for kind in self.accepted_kinds:
            validate_identifier(kind, "CatalogRoot accepted_kind")
        if self.max_files <= 0:
            raise ValueError("CatalogRoot max_files must be > 0")
        if self.max_source_bytes <= 0:
            raise ValueError("CatalogRoot max_source_bytes must be > 0")


@dataclass(frozen=True, slots=True)
class CatalogSnapshot:
    """Immutable published catalog state."""

    view: CatalogView
    whole_fingerprint: str
    entry_fingerprints: tuple[tuple[PluginRef, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate snapshot fields."""
        if not isinstance(self.view, CatalogView):
            raise TypeError("CatalogSnapshot view must be a CatalogView")
        if not isinstance(self.whole_fingerprint, str) or not self.whole_fingerprint:
            raise ValueError(
                "CatalogSnapshot whole_fingerprint must be a non-empty string"
            )
        if not isinstance(self.entry_fingerprints, tuple):
            raise TypeError("CatalogSnapshot entry_fingerprints must be a tuple")

    def get_entry_fingerprint(self, ref: PluginRef) -> str | None:
        """Get entry fingerprint for an exact PluginRef."""
        for r, fp in self.entry_fingerprints:
            if r == ref:
                return fp
        return None


@dataclass(frozen=True, slots=True)
class CatalogRefreshResult:
    """Result of scanning and refreshing catalog roots."""

    success: bool
    snapshot: CatalogSnapshot | None = None
    added: tuple[PluginRef, ...] = ()
    removed: tuple[PluginRef, ...] = ()
    issues: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate refresh result."""
        if not isinstance(self.success, bool):
            raise TypeError("success must be a bool")
        if not isinstance(self.added, tuple):
            raise TypeError("added must be a tuple")
        if not isinstance(self.removed, tuple):
            raise TypeError("removed must be a tuple")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be a tuple")


@dataclass(frozen=True, slots=True)
class SelectionRequest:
    """Explicit parameters for evaluating operation availability."""

    enabled_refs: tuple[PluginRef, ...] = ()
    allowed_effects: tuple[str, ...] = ("pure",)
    allowed_kinds: tuple[str, ...] = ()
    available_capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate selection request."""
        if not isinstance(self.enabled_refs, tuple):
            raise TypeError("enabled_refs must be a tuple of PluginRef")
        if not isinstance(self.allowed_effects, tuple):
            raise TypeError("allowed_effects must be a tuple of str")
        if not isinstance(self.allowed_kinds, tuple):
            raise TypeError("allowed_kinds must be a tuple of str")
        if not isinstance(self.available_capabilities, tuple):
            raise TypeError("available_capabilities must be a tuple of str")
        if not isinstance(self.permissions, tuple):
            raise TypeError("permissions must be a tuple of str")


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """Result of evaluating operation availability against selection constraints."""

    snapshot: CatalogSnapshot
    available_operations: tuple[tuple[PluginRef, str], ...] = ()
    unavailable_reasons: tuple[tuple[PluginRef, str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate selection result."""
        if not isinstance(self.snapshot, CatalogSnapshot):
            raise TypeError("snapshot must be a CatalogSnapshot")
        if not isinstance(self.available_operations, tuple):
            raise TypeError("available_operations must be a tuple")
        if not isinstance(self.unavailable_reasons, tuple):
            raise TypeError("unavailable_reasons must be a tuple")


@dataclass(frozen=True, slots=True)
class AdmittedOperation:
    """Admitted operation pinned to exact source and catalog identity."""

    ref: PluginRef
    operation_id: str
    spec: OperationSpec
    contribution: OperationContribution
    source_digest: str
    entry_fingerprint: str
    dependency_fingerprint: str
    snapshot_fingerprint: str

    def __post_init__(self) -> None:
        """Validate admitted operation."""
        if not isinstance(self.ref, PluginRef):
            raise TypeError("ref must be a PluginRef")
        validate_identifier(self.operation_id, "operation_id")
        if not isinstance(self.spec, OperationSpec):
            raise TypeError("spec must be an OperationSpec")
        if not isinstance(self.contribution, OperationContribution):
            raise TypeError("contribution must be an OperationContribution")
        for name, val in (
            ("source_digest", self.source_digest),
            ("entry_fingerprint", self.entry_fingerprint),
            ("dependency_fingerprint", self.dependency_fingerprint),
            ("snapshot_fingerprint", self.snapshot_fingerprint),
        ):
            if not isinstance(val, str) or not val:
                raise ValueError(f"{name} must be a non-empty string")


class Catalog(Protocol):
    """Public catalog protocol."""

    def is_ready(self) -> bool:
        """Return whether catalog has a valid active snapshot."""
        ...

    def snapshot(self) -> CatalogSnapshot:
        """Return the current immutable catalog snapshot."""
        ...

    def refresh(self) -> CatalogRefreshResult:
        """Discover approved local plugin files and publish an atomic snapshot."""
        ...

    def select(self, request: SelectionRequest) -> SelectionResult:
        """Evaluate operation availability against explicit selection constraints."""
        ...

    def admit(self, ref: PluginRef, operation_id: str) -> AdmittedOperation:
        """Pin an exact operation by version and source identity."""
        ...


HOST_CATALOG = Capability[Catalog]("host.catalog", major=1)


def _is_candidate_filename(name: str) -> bool:
    if name.startswith("_") or not name.endswith(".py"):
        return False
    return not (
        name.endswith("_test.py") or name.startswith("test_") or name == "conftest.py"
    )


class _CandidateDiscovery:
    """Private helper to scan, filter, and load candidate plugin files."""

    def __init__(self, root: CatalogRoot) -> None:
        self.root = root

    def _check_candidate(
        self, child: Path, resolved_root: Path
    ) -> tuple[Path | None, str | None]:
        try:
            resolved_child = child.resolve()
            if not resolved_child.is_relative_to(resolved_root):
                return None, f"Rejected symlink escaping catalog root: {child}"
        except OSError as err:
            return None, f"Failed to resolve file {child}: {err}"

        if not child.is_file() or not _is_candidate_filename(child.name):
            return None, None

        try:
            size = child.stat().st_size
            if size > self.root.max_source_bytes:
                return None, (
                    f"Candidate file {child.name} exceeds max bytes "
                    f"({size} > {self.root.max_source_bytes})"
                )
        except OSError as err:
            return None, f"Failed to stat candidate file {child}: {err}"

        return child, None

    def collect_candidate_files(self) -> tuple[list[Path], list[str]]:
        issues: list[str] = []
        resolved_root = self.root.path.resolve()
        if not resolved_root.exists() or not resolved_root.is_dir():
            issues.append(
                "Catalog root path does not exist or is not a directory: "
                f"{self.root.path}"
            )
            return [], issues

        try:
            entries = sorted(resolved_root.iterdir(), key=lambda p: p.name)
        except OSError as err:
            issues.append(f"Failed to list directory {resolved_root}: {err}")
            return [], issues

        candidates: list[Path] = []
        for child in entries:
            cand, issue = self._check_candidate(child, resolved_root)
            if issue is not None:
                issues.append(issue)
            elif cand is not None:
                candidates.append(cand)

        if len(candidates) > self.root.max_files:
            issues.append(
                f"Candidate count in {self.root.logical_family} exceeds limit "
                f"({len(candidates)} > {self.root.max_files})"
            )
            return [], issues

        return candidates, issues


_PLUGIN_LOAD_ERRORS = (
    ImportError,
    SyntaxError,
    TypeError,
    ValueError,
    AttributeError,
    RuntimeError,
    NameError,
    LookupError,
    ArithmeticError,
    OSError,
)


@dataclass(frozen=True, slots=True)
class _LoadedCandidate:
    contribution: PluginContribution
    source_digest: str
    entry_fingerprint: str
    entry_view: CatalogEntryView


def _load_plugin_module(file_path: Path, module_name: str) -> tuple[Any, str | None]:
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None, f"Failed to create module spec for {file_path}"
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, None
    except _PLUGIN_LOAD_ERRORS as err:
        return None, f"Import failed for {file_path.name}: {err}"


def _extract_contribution(
    mod: Any, file_path: Path
) -> tuple[PluginContribution | None, str | None]:
    factory = getattr(mod, "plugin", None)
    if not callable(factory):
        return None, (
            f"Candidate {file_path.name} does not expose zero-arg 'plugin()' factory"
        )

    try:
        contribution = factory()
    except _PLUGIN_LOAD_ERRORS as err:
        return None, f"Factory execution failed for {file_path.name}: {err}"

    if not isinstance(contribution, PluginContribution):
        return None, (
            f"Factory in {file_path.name} returned "
            f"{type(contribution).__name__}, expected PluginContribution"
        )
    return contribution, None


def _validate_contribution_policy(
    contribution: PluginContribution,
    root: CatalogRoot,
    seen_plugin_ids: set[str],
) -> str | None:
    spec_obj = contribution.spec
    if spec_obj.metamodel_major != CURRENT_METAMODEL_MAJOR:
        return (
            f"Plugin {spec_obj.ref.id} metamodel major "
            f"{spec_obj.metamodel_major} != {CURRENT_METAMODEL_MAJOR}"
        )
    if spec_obj.kind not in root.accepted_kinds:
        return (
            f"Plugin {spec_obj.ref.id} kind {spec_obj.kind!r} "
            f"not accepted by root {root.logical_family}"
        )
    if spec_obj.ref.id in seen_plugin_ids:
        return f"Duplicate plugin ID detected globally: {spec_obj.ref.id}"
    return None


def _load_candidate_file(
    file_path: Path,
    root: CatalogRoot,
    seen_plugin_ids: set[str],
) -> tuple[_LoadedCandidate | None, str | None]:
    try:
        source_bytes = file_path.read_bytes()
    except OSError as err:
        return None, f"Failed to read file {file_path}: {err}"

    source_digest = hashlib.sha256(source_bytes).hexdigest()
    module_name = f"_haru_plugin_{source_digest[:16]}_{file_path.stem}"

    mod, mod_err = _load_plugin_module(file_path, module_name)
    if mod_err is not None:
        return None, mod_err

    contribution, contrib_err = _extract_contribution(mod, file_path)
    if contrib_err is not None or contribution is None:
        return None, contrib_err

    policy_err = _validate_contribution_policy(contribution, root, seen_plugin_ids)
    if policy_err is not None:
        return None, policy_err

    seen_plugin_ids.add(contribution.spec.ref.id)
    entry_view = CatalogEntryView.from_spec(contribution.spec)
    canonical_descriptor_bytes = to_canonical_json_bytes(
        catalog_entry_view_to_wire(entry_view)
    )
    entry_fingerprint = hashlib.sha256(
        canonical_descriptor_bytes + source_digest.encode("utf-8")
    ).hexdigest()

    return (
        _LoadedCandidate(
            contribution=contribution,
            source_digest=source_digest,
            entry_fingerprint=entry_fingerprint,
            entry_view=entry_view,
        ),
        None,
    )


def _evaluate_operation(
    op: OperationSpec,
    allowed_effects: set[str],
    available_caps: set[str],
    permissions: set[str],
) -> str | None:
    unsupported_effects = set(op.effects) - allowed_effects
    if unsupported_effects:
        return f"UNSUPPORTED_EFFECTS:{sorted(unsupported_effects)}"
    missing_caps = set(op.required_capabilities) - available_caps
    if missing_caps:
        return f"MISSING_CAPABILITIES:{sorted(missing_caps)}"
    missing_perms = set(op.permissions) - permissions
    if missing_perms:
        return f"MISSING_PERMISSIONS:{sorted(missing_perms)}"
    return None


class _CatalogProvider:
    """In-memory implementation of the Catalog protocol."""

    def __init__(self, roots: tuple[CatalogRoot, ...] = ()) -> None:
        self._roots = roots
        self._snapshot: CatalogSnapshot | None = None
        self._contributions: dict[PluginRef, PluginContribution] = {}
        self._source_digests: dict[PluginRef, str] = {}
        self._entry_fingerprints: dict[PluginRef, str] = {}
        self._issues: list[str] = []

    def is_ready(self) -> bool:
        return self._snapshot is not None

    def clear(self) -> None:
        """Clear all active catalog state."""
        self._contributions.clear()
        self._source_digests.clear()
        self._entry_fingerprints.clear()
        self._snapshot = None
        self._issues = []

    @property
    def issues(self) -> tuple[str, ...]:
        return tuple(self._issues)

    def snapshot(self) -> CatalogSnapshot:
        if self._snapshot is None:
            raise CatalogUnavailableError(
                "Catalog is not ready; no valid snapshot available"
            )
        return self._snapshot

    def refresh(self) -> CatalogRefreshResult:
        new_contributions: dict[PluginRef, PluginContribution] = {}
        new_source_digests: dict[PluginRef, str] = {}
        new_entry_fingerprints: dict[PluginRef, str] = {}
        new_entry_views: list[CatalogEntryView] = []
        all_issues: list[str] = []
        seen_plugin_ids: set[str] = set()

        for root in self._roots:
            discovery = _CandidateDiscovery(root)
            candidates, issues = discovery.collect_candidate_files()
            all_issues.extend(issues)
            if issues:
                continue

            for file_path in candidates:
                loaded, err = _load_candidate_file(file_path, root, seen_plugin_ids)
                if err is not None:
                    all_issues.append(err)
                    continue
                if loaded is not None:
                    ref = loaded.contribution.spec.ref
                    new_contributions[ref] = loaded.contribution
                    new_source_digests[ref] = loaded.source_digest
                    new_entry_fingerprints[ref] = loaded.entry_fingerprint
                    new_entry_views.append(loaded.entry_view)

        if all_issues and self._snapshot is None:
            self._issues = all_issues
            return CatalogRefreshResult(
                success=False,
                snapshot=None,
                issues=tuple(all_issues),
            )

        if all_issues and self._snapshot is not None:
            self._issues = all_issues
            return CatalogRefreshResult(
                success=False,
                snapshot=self._snapshot,
                issues=tuple(all_issues),
            )

        new_entry_views.sort(key=lambda e: e.ref.to_string())
        sorted_entry_fps = [new_entry_fingerprints[e.ref] for e in new_entry_views]
        if not sorted_entry_fps:
            whole_fingerprint = hashlib.sha256(b"").hexdigest()
        else:
            whole_fingerprint = hashlib.sha256(
                ":".join(sorted_entry_fps).encode("utf-8")
            ).hexdigest()

        view = CatalogView(
            entries=tuple(new_entry_views),
            catalog_fingerprint=whole_fingerprint,
        )

        entry_fp_pairs = tuple(
            (e.ref, new_entry_fingerprints[e.ref]) for e in new_entry_views
        )
        new_snapshot = CatalogSnapshot(
            view=view,
            whole_fingerprint=whole_fingerprint,
            entry_fingerprints=entry_fp_pairs,
        )

        old_refs = (
            set(self._contributions.keys()) if self._snapshot is not None else set()
        )
        current_refs = set(new_contributions.keys())
        added = tuple(sorted(current_refs - old_refs, key=lambda r: r.to_string()))
        removed = tuple(sorted(old_refs - current_refs, key=lambda r: r.to_string()))

        self._snapshot = new_snapshot
        self._contributions = new_contributions
        self._source_digests = new_source_digests
        self._entry_fingerprints = new_entry_fingerprints
        self._issues = []

        return CatalogRefreshResult(
            success=True,
            snapshot=new_snapshot,
            added=added,
            removed=removed,
            issues=(),
        )

    def select(self, request: SelectionRequest) -> SelectionResult:
        if self._snapshot is None:
            raise CatalogUnavailableError("Cannot select on an unready catalog")

        available_ops: list[tuple[PluginRef, str]] = []
        unavailable_reasons: list[tuple[PluginRef, str, str]] = []

        enabled_set = set(request.enabled_refs)
        allowed_effects_set = set(request.allowed_effects)
        allowed_kinds_set = (
            set(request.allowed_kinds) if request.allowed_kinds else None
        )
        available_caps_set = set(request.available_capabilities)
        permissions_set = set(request.permissions)

        for entry in self._snapshot.view.entries:
            ref = entry.ref
            if ref not in enabled_set:
                unavailable_reasons.extend(
                    (ref, op.operation_id, "NOT_ENABLED") for op in entry.operations
                )
                continue

            if allowed_kinds_set is not None and entry.kind not in allowed_kinds_set:
                unavailable_reasons.extend(
                    (ref, op.operation_id, f"KIND_NOT_ALLOWED:{entry.kind}")
                    for op in entry.operations
                )
                continue

            for op in entry.operations:
                reason = _evaluate_operation(
                    op,
                    allowed_effects_set,
                    available_caps_set,
                    permissions_set,
                )
                if reason is not None:
                    unavailable_reasons.append((ref, op.operation_id, reason))
                else:
                    available_ops.append((ref, op.operation_id))

        return SelectionResult(
            snapshot=self._snapshot,
            available_operations=tuple(available_ops),
            unavailable_reasons=tuple(unavailable_reasons),
        )

    def admit(self, ref: PluginRef, operation_id: str) -> AdmittedOperation:
        if self._snapshot is None:
            raise CatalogUnavailableError(
                "Cannot admit operation; catalog is not ready"
            )

        entry = self._snapshot.view.get_entry(ref)
        if entry is None or ref not in self._contributions:
            raise CatalogAdmissionError(
                f"Plugin {ref.to_string()} is not installed in the catalog"
            )

        op_spec = (
            entry.get_operation(operation_id)
            if hasattr(entry, "get_operation")
            else None
        )
        if op_spec is None:
            for op in entry.operations:
                if op.operation_id == operation_id:
                    op_spec = op
                    break
        if op_spec is None:
            raise CatalogAdmissionError(
                f"Operation {operation_id!r} not found on plugin {ref.to_string()}"
            )

        contrib = self._contributions[ref]
        op_contrib = None
        for c in contrib.operations:
            if c.operation_id == operation_id:
                op_contrib = c
                break
        if op_contrib is None:
            raise CatalogAdmissionError(
                f"Implementation for {operation_id!r} not found on "
                f"plugin {ref.to_string()}"
            )

        source_digest = self._source_digests[ref]
        entry_fp = self._entry_fingerprints[ref]
        dep_fp = hashlib.sha256(entry_fp.encode("utf-8")).hexdigest()

        return AdmittedOperation(
            ref=ref,
            operation_id=operation_id,
            spec=op_spec,
            contribution=op_contrib,
            source_digest=source_digest,
            entry_fingerprint=entry_fp,
            dependency_fingerprint=dep_fp,
            snapshot_fingerprint=self._snapshot.whole_fingerprint,
        )


class _CatalogFeature(Feature):
    """Host lifecycle feature for the Catalog capability."""

    spec = FeatureSpec("host.catalog", provides=frozenset({HOST_CATALOG}))

    def __init__(self, roots: tuple[CatalogRoot, ...] = ()) -> None:
        self._roots = roots
        self._provider = _CatalogProvider(roots)

    @override
    async def start(self, context: FeatureContext) -> None:
        """Publish catalog capability upon successful initialization."""
        refresh_res = self._provider.refresh()
        if not refresh_res.success:
            raise CatalogUnavailableError(
                f"Initial catalog refresh failed: {'; '.join(refresh_res.issues)}"
            )
        context.on_close(self._provider.clear)
        context.provide(HOST_CATALOG, self._provider)


def _catalog_feature(roots: tuple[CatalogRoot, ...] = ()) -> Feature:
    """Construct the private catalog feature. Imported only by app.host.bootstrap."""
    return _CatalogFeature(roots)

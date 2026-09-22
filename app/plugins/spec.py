"""Plugin identity, operations, capability declarations, and catalog views."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, override

from app.kernel.capability import Capability
from app.plugins.lowering import LoweringContext, LoweringResult, LoweringTarget
from app.plugins.schema import (
    FrozenObject,
    NumericalPolicy,
    ParameterBindingResult,
    ParameterSchema,
    PortSpec,
    validate_identifier,
)

PLUGIN_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
MAX_PLUGIN_ID_LENGTH = 128
CURRENT_METAMODEL_MAJOR = 1
VERSION_PARTS_COUNT = 3


def validate_plugin_id(plugin_id: str) -> str:
    """Validate that a string is a lowercase dot-namespaced plugin identifier."""
    if not isinstance(plugin_id, str):
        raise TypeError(f"Plugin ID must be a string, got {type(plugin_id).__name__}")
    if (
        not plugin_id
        or len(plugin_id) > MAX_PLUGIN_ID_LENGTH
        or not PLUGIN_ID_PATTERN.match(plugin_id)
    ):
        raise ValueError(
            f"Plugin ID must be lowercase dot-namespaced identifier <= "
            f"{MAX_PLUGIN_ID_LENGTH} chars (e.g. 'indicator.rsi'): {plugin_id!r}"
        )
    return plugin_id


@dataclass(frozen=True, slots=True)
class PluginRef:
    """Exact identity and semantic version of a plugin."""

    id: str
    version: tuple[int, int, int]

    def __post_init__(self) -> None:
        """Validate plugin reference."""
        validate_plugin_id(self.id)
        if (
            not isinstance(self.version, tuple)
            or len(self.version) != VERSION_PARTS_COUNT
        ):
            raise TypeError(
                "PluginRef version must be a 3-tuple of (major, minor, patch)"
            )
        for v in self.version:
            if not isinstance(v, int) or v < 0:
                raise ValueError(
                    "PluginRef version parts must be non-negative integers"
                )
        if self.version[0] == 0 and self.version[1] == 0 and self.version[2] == 0:
            raise ValueError("PluginRef version cannot be 0.0.0")

    @classmethod
    def parse(cls, text: str) -> PluginRef:
        """Parse 'plugin.id@major.minor.patch' into a PluginRef."""
        if not isinstance(text, str) or "@" not in text:
            raise ValueError(f"Invalid plugin ref string format: {text!r}")
        pid, ver = text.split("@", maxsplit=1)
        ver_parts = ver.split(".")
        if len(ver_parts) != VERSION_PARTS_COUNT:
            raise ValueError(f"Invalid semantic version in plugin ref: {text!r}")
        try:
            version = (int(ver_parts[0]), int(ver_parts[1]), int(ver_parts[2]))
        except ValueError as err:
            raise ValueError(f"Invalid integer in version string: {text!r}") from err
        return cls(id=pid, version=version)

    def to_string(self) -> str:
        """Return canonical 'id@major.minor.patch' string."""
        return f"{self.id}@{self.version[0]}.{self.version[1]}.{self.version[2]}"

    @override
    def __str__(self) -> str:
        """Return canonical string."""
        return self.to_string()


DEFAULT_PARAMETER_SCHEMA = ParameterSchema()
DEFAULT_NUMERICAL_POLICY = NumericalPolicy()


def _validate_ports(ports: tuple[PortSpec, ...], label: str) -> None:
    if not isinstance(ports, tuple):
        raise TypeError(f"OperationSpec {label} must be a tuple of PortSpec")
    seen: set[str] = set()
    for p in ports:
        if not isinstance(p, PortSpec):
            raise TypeError(f"{label} port must be a PortSpec")
        if p.key in seen:
            raise ValueError(f"Duplicate {label} port key: {p.key!r}")
        seen.add(p.key)


def _validate_strings(items: tuple[str, ...], label: str) -> None:
    for item in items:
        if not isinstance(item, str) or not item:
            raise ValueError(f"{label} must be non-empty string")


@dataclass(frozen=True, slots=True)
class OperationSpec:
    """Introspectable declaration of one quantitative operation."""

    operation_id: str
    title: str
    description: str = ""
    parameters: ParameterSchema = DEFAULT_PARAMETER_SCHEMA
    inputs: tuple[PortSpec, ...] = ()
    outputs: tuple[PortSpec, ...] = ()
    determinism: bool = True
    numerical_policy: NumericalPolicy = DEFAULT_NUMERICAL_POLICY
    effects: tuple[str, ...] = ("pure",)
    required_capabilities: tuple[str, ...] = ()
    optional_capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    lowering_targets: tuple[LoweringTarget, ...] = ()

    def __post_init__(self) -> None:
        """Validate operation specification."""
        validate_identifier(self.operation_id, "OperationSpec operation_id")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("OperationSpec title must be a non-empty string")
        if not isinstance(self.description, str):
            raise TypeError("OperationSpec description must be a string")
        if not isinstance(self.parameters, ParameterSchema):
            raise TypeError("OperationSpec parameters must be a ParameterSchema")
        _validate_ports(self.inputs, "input")
        _validate_ports(self.outputs, "output")
        if not isinstance(self.determinism, bool):
            raise TypeError("OperationSpec determinism must be a bool")
        if not isinstance(self.numerical_policy, NumericalPolicy):
            raise TypeError("OperationSpec numerical_policy must be a NumericalPolicy")
        for effect in self.effects:
            validate_identifier(effect, "OperationSpec effect")
        _validate_strings(self.required_capabilities, "Capability requirement")
        _validate_strings(self.optional_capabilities, "Optional capability requirement")
        _validate_strings(self.permissions, "Permission")


class OperationBindings(Protocol):
    """Capability bindings restricted strictly to the operation declaration."""

    def require[T](self, token: Capability[T]) -> T:
        """Resolve a declared required capability."""
        ...

    def optional[T](self, token: Capability[T]) -> T | None:
        """Resolve a declared optional capability."""
        ...


class OperationImplementation(Protocol):
    """Protocol for an operation's execution and lowering implementation."""

    def validate_parameters(self, values: FrozenObject) -> ParameterBindingResult:
        """Validate parameter values against cross-field constraints."""
        ...

    def warmup_samples(self, values: FrozenObject) -> int:
        """Return dynamic warm-up sample count required for these parameters."""
        ...

    def execute(
        self,
        inputs: Mapping[str, Any],
        parameters: FrozenObject,
        bindings: OperationBindings,
    ) -> Mapping[str, Any]:
        """Execute operation against inputs and parameters."""
        ...

    def lower(
        self,
        context: LoweringContext,
        parameters: FrozenObject,
    ) -> LoweringResult:
        """Lower operation into semantic IR for target."""
        ...


@dataclass(frozen=True, slots=True)
class OperationContribution:
    """Pair an operation ID with its executable implementation."""

    operation_id: str
    implementation: Any

    def __post_init__(self) -> None:
        """Validate contribution."""
        validate_identifier(self.operation_id, "OperationContribution operation_id")
        if self.implementation is None:
            raise ValueError("OperationContribution implementation cannot be None")


@dataclass(frozen=True, slots=True)
class WorkspaceCommand:
    """Declared command exposed by a workspace plugin."""

    command_id: str
    title: str
    description: str = ""

    def __post_init__(self) -> None:
        """Validate workspace command."""
        validate_identifier(self.command_id, "WorkspaceCommand command_id")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("WorkspaceCommand title must be a non-empty string")
        if not isinstance(self.description, str):
            raise TypeError("WorkspaceCommand description must be a string")


@dataclass(frozen=True, slots=True)
class WorkspaceView:
    """Declared view exposed by a workspace plugin."""

    view_id: str
    title: str
    component: str

    def __post_init__(self) -> None:
        """Validate workspace view."""
        validate_identifier(self.view_id, "WorkspaceView view_id")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("WorkspaceView title must be a non-empty string")
        if not isinstance(self.component, str) or not self.component:
            raise ValueError("WorkspaceView component must be a non-empty string")


@dataclass(frozen=True, slots=True)
class WorkspaceSpec:
    """Introspectable descriptor for a workspace plugin."""

    ref: PluginRef
    title: str
    description: str = ""
    commands: tuple[WorkspaceCommand, ...] = ()
    views: tuple[WorkspaceView, ...] = ()
    accepted_kinds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate workspace specification."""
        if not isinstance(self.ref, PluginRef):
            raise TypeError("WorkspaceSpec ref must be a PluginRef")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("WorkspaceSpec title must be a non-empty string")
        if not isinstance(self.description, str):
            raise TypeError("WorkspaceSpec description must be a string")
        for k in self.accepted_kinds:
            validate_identifier(k, "WorkspaceSpec accepted_kind")


@dataclass(frozen=True, slots=True)
class PluginSpec:
    """Introspectable descriptor for a quantitative plugin."""

    ref: PluginRef
    kind: str
    title: str
    description: str = ""
    metamodel_major: int = CURRENT_METAMODEL_MAJOR
    operations: tuple[OperationSpec, ...] = ()
    workspace: WorkspaceSpec | None = None

    def __post_init__(self) -> None:
        """Validate plugin specification."""
        if not isinstance(self.ref, PluginRef):
            raise TypeError("PluginSpec ref must be a PluginRef")
        validate_identifier(self.kind, "PluginSpec kind")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("PluginSpec title must be a non-empty string")
        if not isinstance(self.description, str):
            raise TypeError("PluginSpec description must be a string")
        if not isinstance(self.metamodel_major, int) or self.metamodel_major < 1:
            raise ValueError("PluginSpec metamodel_major must be an integer >= 1")
        if not isinstance(self.operations, tuple):
            raise TypeError("PluginSpec operations must be a tuple of OperationSpec")
        seen_ops: set[str] = set()
        for op in self.operations:
            if not isinstance(op, OperationSpec):
                raise TypeError(
                    "PluginSpec operations must contain OperationSpec instances"
                )
            if op.operation_id in seen_ops:
                raise ValueError(
                    f"Duplicate operation_id in PluginSpec: {op.operation_id!r}"
                )
            seen_ops.add(op.operation_id)
        if self.workspace is not None and not isinstance(self.workspace, WorkspaceSpec):
            raise TypeError("PluginSpec workspace must be a WorkspaceSpec")

    def get_operation(self, operation_id: str) -> OperationSpec | None:
        """Find an operation spec by operation_id."""
        for op in self.operations:
            if op.operation_id == operation_id:
                return op
        return None


@dataclass(frozen=True, slots=True)
class PluginContribution:
    """Side-effect-free return value of a plugin's zero-argument factory."""

    spec: PluginSpec
    operations: tuple[OperationContribution, ...] = ()

    def __post_init__(self) -> None:
        """Validate that operation implementations match declared specs 1-to-1."""
        if not isinstance(self.spec, PluginSpec):
            raise TypeError("PluginContribution spec must be a PluginSpec")
        if not isinstance(self.operations, tuple):
            raise TypeError("PluginContribution operations must be a tuple")

        spec_op_ids = {op.operation_id for op in self.spec.operations}
        impl_op_ids = set()
        for contrib in self.operations:
            if not isinstance(contrib, OperationContribution):
                raise TypeError(
                    "PluginContribution operations must contain OperationContribution"
                )
            if contrib.operation_id in impl_op_ids:
                raise ValueError(
                    f"Duplicate operation contribution: {contrib.operation_id!r}"
                )
            impl_op_ids.add(contrib.operation_id)

        if spec_op_ids != impl_op_ids:
            missing = spec_op_ids - impl_op_ids
            extra = impl_op_ids - spec_op_ids
            raise ValueError(
                f"PluginContribution operations mismatch for {self.spec.ref.id}: "
                f"missing={missing}, extra={extra}"
            )

    def get_implementation(self, operation_id: str) -> Any:
        """Return implementation for operation_id."""
        for contrib in self.operations:
            if contrib.operation_id == operation_id:
                return contrib.implementation
        return None


@dataclass(frozen=True, slots=True)
class CatalogEntryView:
    """Wire-safe immutable view of an installed plugin descriptor."""

    ref: PluginRef
    kind: str
    title: str
    description: str = ""
    metamodel_major: int = CURRENT_METAMODEL_MAJOR
    operations: tuple[OperationSpec, ...] = ()
    workspace: WorkspaceSpec | None = None

    def __post_init__(self) -> None:
        """Validate wire-safe entry view."""
        if not isinstance(self.ref, PluginRef):
            raise TypeError("CatalogEntryView ref must be a PluginRef")
        validate_identifier(self.kind, "CatalogEntryView kind")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("CatalogEntryView title must be a non-empty string")
        if not isinstance(self.description, str):
            raise TypeError("CatalogEntryView description must be a string")
        if not isinstance(self.metamodel_major, int) or self.metamodel_major < 1:
            raise ValueError("CatalogEntryView metamodel_major must be >= 1")
        if not isinstance(self.operations, tuple):
            raise TypeError("CatalogEntryView operations must be a tuple")
        for op in self.operations:
            if not isinstance(op, OperationSpec):
                raise TypeError("CatalogEntryView operations must be OperationSpec")
        if self.workspace is not None and not isinstance(self.workspace, WorkspaceSpec):
            raise TypeError("CatalogEntryView workspace must be a WorkspaceSpec")

    @classmethod
    def from_spec(cls, spec: PluginSpec) -> CatalogEntryView:
        """Create a wire-safe CatalogEntryView from a PluginSpec."""
        return cls(
            ref=spec.ref,
            kind=spec.kind,
            title=spec.title,
            description=spec.description,
            metamodel_major=spec.metamodel_major,
            operations=spec.operations,
            workspace=spec.workspace,
        )


@dataclass(frozen=True, slots=True)
class CatalogView:
    """Wire-safe immutable snapshot view of the catalog."""

    entries: tuple[CatalogEntryView, ...] = ()
    catalog_fingerprint: str = ""

    def __post_init__(self) -> None:
        """Validate catalog view."""
        if not isinstance(self.entries, tuple):
            raise TypeError("CatalogView entries must be a tuple of CatalogEntryView")
        if not isinstance(self.catalog_fingerprint, str):
            raise TypeError("CatalogView catalog_fingerprint must be a string")
        seen_refs: set[str] = set()
        for e in self.entries:
            if not isinstance(e, CatalogEntryView):
                raise TypeError(
                    "CatalogView entries must be CatalogEntryView instances"
                )
            ref_str = e.ref.to_string()
            if ref_str in seen_refs:
                raise ValueError(f"Duplicate entry in CatalogView: {ref_str}")
            seen_refs.add(ref_str)

    def get_entry(self, ref: PluginRef) -> CatalogEntryView | None:
        """Find an entry view by exact PluginRef."""
        for e in self.entries:
            if e.ref == ref:
                return e
        return None

    def get_entry_by_id(self, plugin_id: str) -> CatalogEntryView | None:
        """Find an entry view by plugin ID."""
        for e in self.entries:
            if e.ref.id == plugin_id:
                return e
        return None

    def get_operation(self, ref: PluginRef, operation_id: str) -> OperationSpec | None:
        """Find an operation spec on an exact entry."""
        entry = self.get_entry(ref)
        if entry is None:
            return None
        for op in entry.operations:
            if op.operation_id == operation_id:
                return op
        return None

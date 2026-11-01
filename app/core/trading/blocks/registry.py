"""Independent block registry, descriptors, staged publication, and snapshots."""

from __future__ import annotations

import functools
import importlib.util
import inspect
import sys
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Self, get_type_hints

from pydantic import BaseModel, ConfigDict, ValidationError, create_model

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue
from app.core.trading.blocks.base import BaseBlock
from app.core.trading.blocks.metadata import BlockSpec, _freeze_mapping

if TYPE_CHECKING:
    from app.core.trading.blocks.composition import CompositionSpec

logger = get_logger(__name__)


def _normalize_source_path(source_file: str | Path | None) -> str:
    """Normalize source file paths to consistent POSIX forward-slash strings."""
    if not source_file:
        return "<in-memory>"
    try:
        p = Path(source_file)
        cwd = Path.cwd()
        if p.is_absolute() and p.is_relative_to(cwd):
            return p.relative_to(cwd).as_posix()
        return p.as_posix()
    except ValueError, OSError:
        return str(source_file).replace("\\", "/")


def _verify_safe_path(p: Path, authorized_root: str | Path | None) -> None:
    """Confirm path is strictly within the authorized root."""
    if authorized_root is None:
        return
    auth = Path(authorized_root).resolve()
    try:
        p.relative_to(auth)
    except ValueError as err:
        raise BlockRegistryError(
            f"Path '{p}' escapes authorized root '{authorized_root}'",
            code="PATH_TRAVERSAL_DETECTED",
        ) from err
    if p.is_symlink():
        target = p.resolve()
        try:
            target.relative_to(auth)
        except ValueError as err:
            raise BlockRegistryError(
                f"Symlink target for '{p}' escapes authorized root",
                code="PATH_TRAVERSAL_DETECTED",
            ) from err


def _load_module_blocks(p: Path) -> list[type[BaseBlock] | Callable[..., Any]]:
    """Execute python module and extract BaseBlock classes and @block callables."""
    module_name = f"haru_blocks_{p.stem}_{abs(hash(str(p))) & 0xFFFFFFFF}"
    spec = importlib.util.spec_from_file_location(module_name, p)
    if spec is None or spec.loader is None:
        raise BlockRegistryError(
            f"Could not load module spec for '{p}'",
            code="MODULE_LOAD_ERROR",
        )
    mod = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(module_name)
    sys.modules[module_name] = mod
    try:
        # Read current source rather than a potentially stale same-size pyc.
        exec(compile(p.read_bytes(), str(p), "exec"), mod.__dict__)  # noqa: S102 - explicit source loading
    except Exception:
        if previous is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous
        raise

    targets: list[type[BaseBlock] | Callable[..., Any]] = []
    seen: set[int] = set()
    for obj in vars(mod).values():
        if getattr(obj, "__module__", None) != mod.__name__:
            continue
        if id(obj) in seen:
            continue
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseBlock)
            and not inspect.isabstract(obj)
        ):
            if hasattr(obj, "spec") and isinstance(obj.spec, BlockSpec):
                seen.add(id(obj))
                targets.append(obj)
        elif callable(obj) and hasattr(obj, "_block_spec"):
            seen.add(id(obj))
            targets.append(obj)
    return targets


class BlockRegistryError(DomainError):
    """Raised when block validation, registration, or catalog resolution fails."""

    def __init__(
        self,
        message: str = "Block registry error",
        *,
        code: str = "BLOCK_REGISTRY_ERROR",
        details: dict[str, JSONValue] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details)


@dataclass(frozen=True)
class BlockDescriptor:
    """Immutable runtime descriptor of a registered block."""

    spec: BlockSpec
    target: type[BaseBlock] | Callable[..., Any]
    parameter_schema: Mapping[str, Any]
    source_file: str | None = None
    is_class: bool = True
    composition: CompositionSpec | None = None
    input_bindings: Mapping[str, Any] = field(default_factory=dict)
    _config_model: type[BaseModel] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Deeply freeze parameter schema and spec metadata."""
        object.__setattr__(
            self, "parameter_schema", _freeze_mapping(dict(self.parameter_schema))
        )
        object.__setattr__(
            self, "input_bindings", _freeze_mapping(dict(self.input_bindings))
        )
        if isinstance(self.spec.parameter_search_space, (dict, Mapping)):
            object.__setattr__(
                self.spec,
                "parameter_search_space",
                _freeze_mapping(dict(self.spec.parameter_search_space)),
            )

    def instantiate(self, **parameters: Any) -> Any:
        """Instantiate class block with parameters or configure callable."""
        if self.is_class and inspect.isclass(self.target):
            try:
                return self.target(**parameters)
            except ValidationError as e:
                raise BlockRegistryError(
                    f"Invalid configuration parameter(s) for block "
                    f"'{self.spec.id}': {e}",
                    code="INVALID_CONFIGURATION",
                ) from e

        # For callable blocks, validate against parameter_schema
        allowed_params = set(self.parameter_schema.get("properties", {}).keys())
        unknown = set(parameters) - allowed_params
        if unknown:
            raise BlockRegistryError(
                f"Unknown configuration parameter(s) for block '{self.spec.id}': "
                f"{', '.join(sorted(unknown))}",
                code="INVALID_CONFIGURATION",
            )

        self._validate_composition_configuration(parameters)

        if not parameters:
            # Validate that any required configuration parameters are satisfied
            if self._config_model is not None:
                try:
                    self._config_model()
                except ValidationError as e:
                    raise BlockRegistryError(
                        f"Missing required configuration parameter(s) for block "
                        f"'{self.spec.id}': {e}",
                        code="MISSING_CONFIGURATION",
                    ) from e
            return self.target

        # Validate provided parameter values and types
        if self._config_model is not None:
            try:
                self._config_model(**parameters)
            except ValidationError as e:
                raise BlockRegistryError(
                    f"Invalid configuration parameter(s) for block "
                    f"'{self.spec.id}': {e}",
                    code="INVALID_CONFIGURATION",
                ) from e

        return functools.partial(self.target, **parameters)

    def _validate_composition_configuration(
        self, parameters: Mapping[str, Any]
    ) -> None:
        if self.composition is None:
            return
        from app.core.trading.blocks.composition_runtime import CompositionExecutor

        if (
            not isinstance(self.target, CompositionExecutor)
            or self._config_model is None
        ):
            raise BlockRegistryError(
                "Composition descriptor has no validated executor",
                code="INVALID_COMPOSITION",
            )
        try:
            configured = self._config_model(**parameters).model_dump()
            self.target.validate(configured)
        except (ValueError, TypeError) as error:
            raise BlockRegistryError(
                f"Invalid configuration for composition '{self.spec.id}': {error}",
                code="INVALID_CONFIGURATION",
                details={"block_id": self.spec.id, "error": str(error)},
            ) from error


@dataclass(frozen=True)
class CatalogSnapshot:
    """Immutable snapshot of the block catalog for compilation and execution plans."""

    revision: str
    blocks: Mapping[str, BlockDescriptor] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Wrap blocks in an immutable MappingProxyType."""
        object.__setattr__(self, "blocks", MappingProxyType(dict(self.blocks)))

    def get(self, block_id: str) -> BlockDescriptor | None:
        """Retrieve descriptor by block ID or return None."""
        return self.blocks.get(block_id)

    def require(self, block_id: str) -> BlockDescriptor:
        """Retrieve descriptor by block ID or raise BlockRegistryError."""
        desc = self.get(block_id)
        if desc is None:
            raise BlockRegistryError(
                f"Block '{block_id}' not found in catalog snapshot",
                code="BLOCK_NOT_FOUND",
                details={"block_id": block_id},
            )
        return desc

    def __contains__(self, block_id: str) -> bool:
        """Check if block ID is registered in snapshot."""
        return block_id in self.blocks

    def __iter__(self) -> Iterator[BlockDescriptor]:
        """Iterate over all block descriptors in snapshot."""
        return iter(self.blocks.values())

    def __len__(self) -> int:
        """Return number of registered blocks in snapshot."""
        return len(self.blocks)


class DiscoveredBlocks(int):
    """Integer count of discovered blocks, iterable over discovered descriptors."""

    _descriptors: list[BlockDescriptor]

    def __new__(cls, descriptors: list[BlockDescriptor]) -> Self:
        inst = super().__new__(cls, len(descriptors))
        inst._descriptors = list(descriptors)
        return inst

    def __iter__(self) -> Iterator[BlockDescriptor]:
        return iter(self._descriptors)

    def __len__(self) -> int:
        return len(self._descriptors)

    def __getitem__(self, index: int) -> BlockDescriptor:
        return self._descriptors[index]


class BlockRegistry:
    """Central independent registry for all strategy building blocks.

    Provides staged publication to guarantee atomic updates and safe rollback.
    Does not import workspace, UI, or broker code.
    """

    def __init__(self) -> None:
        self._blocks: dict[str, BlockDescriptor] = {}
        self._by_source: dict[str, list[str]] = {}
        self._staging_blocks: dict[str, BlockDescriptor] | None = None
        self._staging_by_source: dict[str, list[str]] | None = None
        self._staging_stack: list[
            tuple[dict[str, BlockDescriptor], dict[str, list[str]]]
        ] = []
        self._diagnostics: list[dict[str, Any]] = []
        self._revision: int = 1

    @property
    def is_staging(self) -> bool:
        """Check whether a staging transaction is active."""
        return len(self._staging_stack) > 0

    @property
    def staging_depth(self) -> int:
        """Return nesting depth of active staging transactions."""
        return len(self._staging_stack)

    @property
    def diagnostics(self) -> list[dict[str, Any]]:
        """Return collected discovery and registration diagnostics."""
        return list(self._diagnostics)

    def clear_diagnostics(self) -> None:
        """Clear collected diagnostics."""
        self._diagnostics.clear()

    @property
    def revision(self) -> str:
        """Return catalog revision identifier."""
        return f"rev-{self._revision}"

    def register_block(
        self,
        target: BlockDescriptor | type[BaseBlock] | Callable[..., Any] | None = None,
        source_file: str | Path | None = None,
        *,
        descriptor: BlockDescriptor | None = None,
        overwrite: bool = False,
    ) -> BlockDescriptor:
        """Validate and register a single block descriptor, class, or callable.

        Enforces unique block IDs unless overwrite=True; raises DomainError
        with code DUPLICATE_BLOCK_ID when an existing ID collision is detected.
        """
        candidate = descriptor if descriptor is not None else target
        if candidate is None:
            raise BlockRegistryError(
                "No block target or descriptor provided",
                code="INVALID_ARGUMENT",
            )
        if isinstance(candidate, BlockDescriptor):
            desc = candidate
        else:
            desc = self._create_descriptor(candidate, source_file)
        return self._publish_descriptor(desc, overwrite=overwrite)

    def _publish_descriptor(
        self, desc: BlockDescriptor, *, overwrite: bool = False
    ) -> BlockDescriptor:
        """Publish one validated descriptor with staging and ownership checks."""
        block_id = desc.spec.id

        target_blocks = (
            self._staging_blocks if self._staging_blocks is not None else self._blocks
        )
        target_by_source = (
            self._staging_by_source
            if self._staging_by_source is not None
            else self._by_source
        )

        if block_id in target_blocks:
            if not overwrite:
                # Check for source ownership conflict first to preserve specific message
                if (
                    target_blocks[block_id].source_file is not None
                    and desc.source_file is not None
                    and target_blocks[block_id].source_file != desc.source_file
                    and target_blocks[block_id].source_file != "<in-memory>"
                    and desc.source_file != "<in-memory>"
                ):
                    logger.warning(
                        "Block '%s' ownership conflict: owned by '%s', "
                        "candidate from '%s'",
                        block_id,
                        target_blocks[block_id].source_file,
                        desc.source_file,
                    )
                    raise BlockRegistryError(
                        f"Block '{block_id}' is already owned by source "
                        f"'{target_blocks[block_id].source_file}'; "
                        f"cannot be re-registered by '{desc.source_file}'",
                        code="SOURCE_OWNERSHIP_CONFLICT",
                        details={
                            "block_id": block_id,
                            "owned_by": target_blocks[block_id].source_file,
                            "requested_by": str(desc.source_file),
                        },
                    )
                logger.warning("Duplicate block ID rejected: %s", block_id)
                raise BlockRegistryError(
                    f"Duplicate block ID: Block ID already registered ('{block_id}')",
                    code="DUPLICATE_BLOCK_ID",
                    details={"block_id": block_id},
                )

            # Overwrite path: clean up previous source mapping if source changed
            old_desc = target_blocks[block_id]
            if old_desc.source_file:
                old_src_key = _normalize_source_path(old_desc.source_file)
                if (
                    old_src_key in target_by_source
                    and block_id in target_by_source[old_src_key]
                ):
                    target_by_source[old_src_key].remove(block_id)
            logger.info("Overwriting existing block registration: %s", block_id)

        target_blocks[block_id] = desc

        src_key = _normalize_source_path(desc.source_file)
        target_by_source.setdefault(src_key, [])
        if block_id not in target_by_source[src_key]:
            target_by_source[src_key].append(block_id)

        if not self.is_staging:
            self._revision += 1

        logger.debug("Registered block '%s' from source '%s'", block_id, src_key)
        return desc

    def unregister_source(self, source_file: str | Path) -> None:
        """Remove all blocks originating from the specified source file."""
        src_key = _normalize_source_path(source_file)
        target_blocks = (
            self._staging_blocks if self._staging_blocks is not None else self._blocks
        )
        target_by_source = (
            self._staging_by_source
            if self._staging_by_source is not None
            else self._by_source
        )

        block_ids = target_by_source.pop(src_key, [])
        for bid in block_ids:
            target_blocks.pop(bid, None)

        if not self.is_staging:
            self._revision += 1

        logger.debug(
            "Unregistered source '%s' (%d blocks removed)",
            src_key,
            len(block_ids),
        )

    def begin_staging(self) -> None:
        """Start a staged transaction or push a nested savepoint."""
        if not self.is_staging:
            self._staging_blocks = dict(self._blocks)
            self._staging_by_source = {k: list(v) for k, v in self._by_source.items()}
        if self._staging_blocks is None or self._staging_by_source is None:
            raise BlockRegistryError(
                "Staging state is uninitialized",
                code="STAGING_UNINITIALIZED",
            )
        savepoint = (
            dict(self._staging_blocks),
            {k: list(v) for k, v in self._staging_by_source.items()},
        )
        self._staging_stack.append(savepoint)
        logger.debug("Begin staging savepoint (depth=%d)", len(self._staging_stack))

    def commit_staging(self) -> CatalogSnapshot:
        """Commit current savepoint or transaction, returning catalog snapshot."""
        if not self._staging_stack:
            raise BlockRegistryError(
                "No active staging transaction to commit",
                code="NO_ACTIVE_TRANSACTION",
            )
        self._staging_stack.pop()
        if not self._staging_stack:
            if self._staging_blocks is None or self._staging_by_source is None:
                raise BlockRegistryError(
                    "Staging state is uninitialized",
                    code="STAGING_UNINITIALIZED",
                )
            self._blocks = self._staging_blocks
            self._by_source = self._staging_by_source
            self._staging_blocks = None
            self._staging_by_source = None
            self._revision += 1
            logger.info(
                "Committed outermost staging transaction; revision %s (%d blocks)",
                self.revision,
                len(self._blocks),
            )
        else:
            logger.debug(
                "Committed nested staging savepoint (depth remaining=%d)",
                len(self._staging_stack),
            )
        return self.snapshot()

    def rollback_staging(self) -> None:
        """Roll back staged changes to previous savepoint or abort staging."""
        if not self._staging_stack:
            return
        saved_blocks, saved_sources = self._staging_stack.pop()
        if self._staging_stack:
            self._staging_blocks = saved_blocks
            self._staging_by_source = saved_sources
            logger.debug(
                "Rolled back to nested savepoint (depth remaining=%d)",
                len(self._staging_stack),
            )
        else:
            self._staging_blocks = None
            self._staging_by_source = None
            logger.info("Rolled back outermost staging transaction; changes discarded")

    def snapshot(self) -> CatalogSnapshot:
        """Return an immutable snapshot of current committed registrations."""
        return CatalogSnapshot(
            revision=self.revision,
            blocks=dict(self._blocks),
        )

    def get(self, block_id: str) -> BlockDescriptor | None:
        """Retrieve descriptor by block ID or return None."""
        target_blocks = (
            self._staging_blocks if self._staging_blocks is not None else self._blocks
        )
        return target_blocks.get(block_id)

    def require(self, block_id: str) -> BlockDescriptor:
        """Retrieve descriptor by block ID or raise BlockRegistryError."""
        desc = self.get(block_id)
        if desc is None:
            raise BlockRegistryError(
                f"Block '{block_id}' is not registered",
                code="BLOCK_NOT_FOUND",
                details={"block_id": block_id},
            )
        return desc

    def register_file(
        self,
        file_path: str | Path,
        authorized_root: str | Path | None = None,
    ) -> list[BlockDescriptor]:
        """Validate, stage, and atomically register all blocks declared in a file.

        Retains the last valid registration on syntax or runtime failure.
        """
        p = Path(file_path).resolve()
        _verify_safe_path(p, authorized_root)

        if not p.is_file() or not p.name.endswith(".py"):
            return []

        internal_names = (
            "__init__.py",
            "base.py",
            "metadata.py",
            "registry.py",
            "series.py",
        )
        if p.name.startswith((".", "_")) or p.name in internal_names:
            return []

        src_key = _normalize_source_path(p)

        self.begin_staging()
        try:
            self.unregister_source(src_key)
            targets = _load_module_blocks(p)
            registered = [self.register_block(t, source_file=src_key) for t in targets]
            from app.core.trading.blocks.composition import (
                bind_composition,
                owned_compositions,
                owned_specializations,
            )
            from app.core.trading.blocks.indicator import BaseIndicator

            for target in targets:
                if inspect.isclass(target) and issubclass(target, BaseIndicator):
                    for definition in owned_compositions(target.spec.id):
                        executable, config_model, composition_spec = bind_composition(
                            definition,
                            target,
                            {
                                key: descriptor.target
                                for key, descriptor in (
                                    self._staging_blocks or self._blocks
                                ).items()
                                if descriptor.is_class
                            },
                        )
                        descriptor = BlockDescriptor(
                            spec=composition_spec,
                            target=executable,
                            parameter_schema=config_model.model_json_schema(),
                            source_file=src_key,
                            is_class=False,
                            _config_model=config_model,
                            composition=definition,
                        )
                        self._publish_descriptor(descriptor)
                        registered.append(descriptor)
                    for helper, helper_spec, bindings in owned_specializations(target):
                        descriptor = self._create_descriptor(
                            helper, source_file=src_key, declared_spec=helper_spec
                        )
                        descriptor = replace(descriptor, input_bindings=bindings)
                        self._publish_descriptor(descriptor)
                        registered.append(descriptor)
            self.commit_staging()
            return registered
        except Exception as e:
            self.rollback_staging()
            raise BlockRegistryError(
                f"Failed to register block file '{src_key}': {e}",
                code="FILE_REGISTRATION_FAILED",
                details={"file": src_key, "error": str(e)},
            ) from e

    def discover(
        self,
        root_dir: Path | str | None = None,
        *,
        authorized_root: Path | str | None = None,
    ) -> int:
        """Discovers blocks and registers them within an atomic staging transaction."""
        if root_dir is None:
            candidate = Path.cwd() / "app" / "extend" / "blocks"
            if candidate.is_dir():
                dir_path = candidate.resolve()
            else:
                dir_path = Path(__file__).resolve().parent
        else:
            dir_path = Path(root_dir).resolve()

        if not dir_path.is_dir():
            return DiscoveredBlocks([])

        auth_root = Path(authorized_root).resolve() if authorized_root else dir_path
        try:
            dir_path.relative_to(auth_root)
        except ValueError as err:
            raise BlockRegistryError(
                f"Discovery directory '{dir_path}' "
                f"escapes authorized root '{auth_root}'",
                code="PATH_TRAVERSAL_DETECTED",
            ) from err

        internal_names = (
            "__init__.py",
            "base.py",
            "metadata.py",
            "registry.py",
            "series.py",
        )
        self.begin_staging()
        try:
            self._diagnostics.clear()
            all_discovered: list[BlockDescriptor] = []
            for file_path in sorted(dir_path.rglob("*.py")):
                if file_path.name.startswith((".", "_")):
                    continue
                if file_path.name in internal_names or "test_" in file_path.name:
                    continue
                try:
                    descriptors = self.register_file(
                        file_path, authorized_root=auth_root
                    )
                    all_discovered.extend(descriptors)
                except BlockRegistryError as err:
                    src_key = _normalize_source_path(file_path)
                    logger.warning("Discovery error in %s: %s", src_key, err)
                    self._diagnostics.append({"file": src_key, "error": str(err)})
            self.commit_staging()
            logger.info(
                "Discovery complete: %d blocks registered from %s",
                len(all_discovered),
                dir_path,
            )
            return DiscoveredBlocks(all_discovered)
        except Exception:
            self.rollback_staging()
            logger.exception("Discovery failed, rolling back")
            raise

    def _create_descriptor(
        self,
        target: type[BaseBlock] | Callable[..., Any],
        source_file: str | Path | None = None,
        declared_spec: BlockSpec | None = None,
    ) -> BlockDescriptor:
        src = _normalize_source_path(source_file) if source_file is not None else None

        # Case 1: BaseBlock subclass
        if inspect.isclass(target) and issubclass(target, BaseBlock):
            spec = getattr(target, "spec", None)
            if not isinstance(spec, BlockSpec):
                raise BlockRegistryError(
                    f"Class {target.__name__} must define ClassVar BlockSpec 'spec'",
                    code="INVALID_BLOCK_SPEC",
                )
            schema = target.get_parameter_schema()
            return BlockDescriptor(
                spec=spec,
                target=target,
                parameter_schema=schema,
                source_file=src,
                is_class=True,
            )

        # Case 2: Callable decorated with @block
        if callable(target):
            spec = declared_spec or getattr(target, "_block_spec", None)
            if not isinstance(spec, BlockSpec):
                name = getattr(target, "__name__", str(target))
                raise BlockRegistryError(
                    f"Callable {name} must be decorated with @block(spec)",
                    code="INVALID_BLOCK_SPEC",
                )
            # Exclude runtime input ports from configuration schema
            input_port_names = {p.name for p in spec.inputs}
            sig = inspect.signature(target)
            annotations = get_type_hints(target, include_extras=True)
            fields: dict[str, Any] = {}
            for pname, param in sig.parameters.items():
                if pname in ("self", "cls"):
                    continue
                if pname in input_port_names:
                    continue
                if param.annotation is not inspect.Parameter.empty:
                    anno = annotations.get(pname, param.annotation)
                elif param.default is not inspect.Parameter.empty and type(
                    param.default
                ) in (int, float, str, bool):
                    anno = type(param.default)
                else:
                    anno = Any

                default = (
                    param.default
                    if param.default is not inspect.Parameter.empty
                    else ...
                )
                fields[pname] = (anno, default)

            clean_name = (
                "".join(
                    c
                    for c in (spec.name or getattr(target, "__name__", "Callable"))
                    if c.isalnum()
                )
                or "Callable"
            )
            config_model: type[BaseModel] = create_model(
                f"{clean_name}Config",
                __config__=ConfigDict(
                    extra="forbid",
                    frozen=True,
                    validate_default=True,
                    strict=True,
                ),
                **fields,
            )
            raw_schema = config_model.model_json_schema()
            raw_schema["title"] = spec.name or getattr(
                target, "__name__", "CallableBlock"
            )
            raw_schema.setdefault("required", [])

            return BlockDescriptor(
                spec=spec,
                target=target,
                parameter_schema=raw_schema,
                source_file=src,
                is_class=False,
                _config_model=config_model,
            )

        raise BlockRegistryError(
            f"Unsupported block target: {target}",
            code="UNSUPPORTED_BLOCK_TARGET",
        )


# Default global block registry
block_registry = BlockRegistry()

__all__ = [
    "BlockDescriptor",
    "BlockRegistry",
    "BlockRegistryError",
    "CatalogSnapshot",
    "block_registry",
]

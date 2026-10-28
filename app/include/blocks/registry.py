"""Independent block registry, descriptors, staged publication, and snapshots."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, create_model

from app.include.blocks.base import BaseBlock
from app.include.blocks.metadata import BlockSpec, _freeze_mapping


class BlockRegistryError(Exception):
    """Raised when block validation, registration, or catalog resolution fails."""


@dataclass(frozen=True)
class BlockDescriptor:
    """Immutable runtime descriptor of a registered block."""

    spec: BlockSpec
    target: type[BaseBlock] | Callable[..., Any]
    parameter_schema: Mapping[str, Any]
    source_file: str | None = None
    is_class: bool = True
    _config_model: type[BaseModel] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Deeply freeze parameter schema and spec metadata."""
        object.__setattr__(
            self, "parameter_schema", _freeze_mapping(dict(self.parameter_schema))
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
                    f"'{self.spec.id}': {e}"
                ) from e

        # For callable blocks, validate against parameter_schema
        allowed_params = set(self.parameter_schema.get("properties", {}).keys())
        unknown = set(parameters) - allowed_params
        if unknown:
            raise BlockRegistryError(
                f"Unknown configuration parameter(s) for block '{self.spec.id}': "
                f"{', '.join(sorted(unknown))}"
            )

        if not parameters:
            # Validate that any required configuration parameters are satisfied
            if self._config_model is not None:
                try:
                    self._config_model()
                except ValidationError as e:
                    raise BlockRegistryError(
                        f"Missing required configuration parameter(s) for block "
                        f"'{self.spec.id}': {e}"
                    ) from e
            return self.target

        # Validate provided parameter values and types
        if self._config_model is not None:
            try:
                self._config_model(**parameters)
            except ValidationError as e:
                raise BlockRegistryError(
                    f"Invalid configuration parameter(s) for block "
                    f"'{self.spec.id}': {e}"
                ) from e

        return functools.partial(self.target, **parameters)


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
                f"Block '{block_id}' not found in catalog snapshot"
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
        self._revision: int = 1

    @property
    def is_staging(self) -> bool:
        """Check whether a staging transaction is active."""
        return self._staging_blocks is not None

    @property
    def revision(self) -> str:
        """Return catalog revision identifier."""
        return f"rev-{self._revision}"

    def register_block(
        self,
        target: type[BaseBlock] | Callable[..., Any],
        source_file: str | Path | None = None,
    ) -> BlockDescriptor:
        """Validate and register a single class or callable block."""
        desc = self._create_descriptor(target, source_file)
        block_id = desc.spec.id

        target_blocks = (
            self._staging_blocks if self._staging_blocks is not None else self._blocks
        )
        target_by_source = (
            self._staging_by_source
            if self._staging_by_source is not None
            else self._by_source
        )

        # Collision detection (same ID with different target)
        if block_id in target_blocks and target_blocks[block_id].target != desc.target:
            raise BlockRegistryError(
                f"Duplicate block ID registration: '{block_id}' already registered"
            )

        target_blocks[block_id] = desc

        src_key = str(source_file) if source_file else "<in-memory>"
        target_by_source.setdefault(src_key, [])
        if block_id not in target_by_source[src_key]:
            target_by_source[src_key].append(block_id)

        if not self.is_staging:
            self._revision += 1

        return desc

    def unregister_source(self, source_file: str | Path) -> None:
        """Remove all blocks originating from the specified source file."""
        src_key = str(source_file)
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

    def begin_staging(self) -> None:
        """Start a staged transaction."""
        self._staging_blocks = dict(self._blocks)
        self._staging_by_source = {k: list(v) for k, v in self._by_source.items()}

    def commit_staging(self) -> None:
        """Commit the staged transaction atomically."""
        if self._staging_blocks is None or self._staging_by_source is None:
            raise BlockRegistryError("No active staging transaction to commit")
        self._blocks = self._staging_blocks
        self._by_source = self._staging_by_source
        self._staging_blocks = None
        self._staging_by_source = None
        self._revision += 1

    def rollback_staging(self) -> None:
        """Roll back staged changes without modifying live catalog."""
        self._staging_blocks = None
        self._staging_by_source = None

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
            raise BlockRegistryError(f"Block '{block_id}' is not registered")
        return desc

    def _create_descriptor(
        self,
        target: type[BaseBlock] | Callable[..., Any],
        source_file: str | Path | None = None,
    ) -> BlockDescriptor:
        src = str(source_file) if source_file else None

        # Case 1: BaseBlock subclass
        if inspect.isclass(target) and issubclass(target, BaseBlock):
            spec = getattr(target, "spec", None)
            if not isinstance(spec, BlockSpec):
                raise BlockRegistryError(
                    f"Class {target.__name__} must define ClassVar BlockSpec 'spec'"
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
            spec = getattr(target, "_block_spec", None)
            if not isinstance(spec, BlockSpec):
                name = getattr(target, "__name__", str(target))
                raise BlockRegistryError(
                    f"Callable {name} must be decorated with @block(spec)"
                )
            # Exclude runtime input ports from configuration schema
            input_port_names = {p.name for p in spec.inputs}
            sig = inspect.signature(target)
            fields: dict[str, Any] = {}
            for pname, param in sig.parameters.items():
                if pname in ("self", "cls"):
                    continue
                if pname in input_port_names:
                    continue
                if param.annotation is not inspect.Parameter.empty:
                    anno = param.annotation
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

        raise BlockRegistryError(f"Unsupported block target: {target}")


# Default global block registry
block_registry = BlockRegistry()

__all__ = [
    "BlockDescriptor",
    "BlockRegistry",
    "BlockRegistryError",
    "CatalogSnapshot",
    "block_registry",
]

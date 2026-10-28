"""Shared validated block contract and callable decorator."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar, TypeVar, override

from pydantic import BaseModel, ConfigDict

from app.include.blocks.metadata import BlockSpec

F = TypeVar("F", bound=Callable[..., Any])


class BaseBlock(BaseModel):
    """Abstract base class for all validated strategy blocks.

    Configuration fields are defined as Pydantic model attributes.
    Unknown fields are forbidden, defaults are validated, configuration is frozen,
    and metadata is specified strictly via ClassVar[BlockSpec].
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
        validate_default=True,
    )

    spec: ClassVar[BlockSpec]

    def on_init(self) -> None:
        """Lifecycle hook called once after validation to initialize constants."""

    @override
    def model_post_init(self, context: Any, /) -> None:
        """Post-initialization hook invoking on_init."""
        super().model_post_init(context)
        self.on_init()

    @classmethod
    def get_parameter_schema(cls) -> dict[str, Any]:
        """Derive parameter schema strictly from configurable model fields.

        Excludes `spec` ClassVar and private attributes.
        """
        schema = cls.model_json_schema()
        properties = schema.get("properties", {})
        cleaned_props = {
            k: v for k, v in properties.items() if not k.startswith("_") and k != "spec"
        }
        schema["properties"] = cleaned_props
        return schema


def block(spec: BlockSpec) -> Callable[[F], F]:
    """Decorator for callable strategy blocks, including asynchronous operations.

    Attaches the BlockSpec to the callable without mutating the global registry
    during module import.
    """

    def decorator(fn: F) -> F:
        setattr(fn, "_block_spec", spec)  # noqa: B010
        return fn

    return decorator


__all__ = [
    "BaseBlock",
    "block",
]

"""Validated custom building blocks and callable AI extension catalog."""

from __future__ import annotations

import inspect
import symtable
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from app.include.indicators.base import BaseIndicator
from app.workspace.code_editor._common import INCLUDE_DIR, CodeEditorError


class BaseMetric(ABC):
    """Contract for custom strategy performance columns."""

    @abstractmethod
    def compute(
        self, trades: Sequence[dict[str, Any]], initial_capital: float = 10000.0
    ) -> float:
        """Compute a scalar metric from executed trades."""


class BasePositionSizer(ABC):
    """Contract for custom trade volume calculation."""

    @abstractmethod
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Calculate lots from account equity and stop distance."""


class SnippetRegistry:
    """Replace registrations by file so recompilation cannot leave stale classes."""

    def __init__(self) -> None:
        self.blocks: dict[str, dict[str, type[Any]]] = {}
        self.tools: dict[str, Any] = {}
        self._tools_by_path: dict[str, list[str]] = {}

    def unregister(self, path: str) -> None:
        """Remove a file or directory and its registered tools."""
        for key in list(self.blocks):
            if key == path or key.startswith(path + "/"):
                self.blocks.pop(key)
                for name in self._tools_by_path.pop(key, []):
                    self.tools.pop(name, None)

    def register(self, path: Path, module: Any) -> list[str]:
        """Validate inheritance and required contracts before publishing changes."""
        classes = {
            name: value
            for name, value in vars(module).items()
            if inspect.isclass(value) and value.__module__ == module.__name__
        }
        base: type[Any] | None = None
        if "indicators" in path.parts:
            base = BaseIndicator
        elif "metrics" in path.parts:
            base = BaseMetric
        elif "money_management" in path.parts:
            base = BasePositionSizer

        if path.resolve() == (INCLUDE_DIR / "indicators/base.py").resolve():
            classes = {}
            base = None
        if base:
            classes = {
                name: cls
                for name, cls in classes.items()
                if issubclass(cls, base) and not inspect.isabstract(cls)
            }
            if not classes:
                raise CodeEditorError(
                    f"Custom {path.parent.name} must implement {base.__name__}"
                )
        tools = {}
        if "ai_tools" in path.parts:
            if not classes:
                raise CodeEditorError(
                    "AI tool files must declare at least one tool class"
                )
            for cls in classes.values():
                tool = cls()
                if not all(
                    callable(getattr(tool, member, None))
                    for member in ("run", "get_input_schema")
                ):
                    raise CodeEditorError(
                        "AI tools require run() and get_input_schema()"
                    )
                if not tool.name or not isinstance(tool.get_input_schema(), dict):
                    raise CodeEditorError("AI tools require a name and input schema")
                if tool.name in self.tools and tool.name not in self._tools_by_path.get(
                    str(path), []
                ):
                    raise CodeEditorError(f"Duplicate AI tool: {tool.name}")
                tools[tool.name] = tool
        self.unregister(str(path))
        self.blocks[str(path)] = classes
        self.tools.update(tools)
        self._tools_by_path[str(path)] = list(tools)
        return list(classes)

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any:
        """Dispatch a registered extension using its declared JSON schema."""
        import jsonschema

        if name not in self.tools:
            raise CodeEditorError(f"Unknown extension tool: {name}")
        tool = self.tools[name]
        try:
            jsonschema.validate(dict(arguments), tool.get_input_schema())
        except (jsonschema.ValidationError, jsonschema.SchemaError) as exc:
            raise CodeEditorError(
                f"Invalid AI tool arguments or schema: {exc.message}"
            ) from exc
        return tool.run(arguments)


registry = SnippetRegistry()


def unresolved_symbols(source: str, filename: str) -> list[dict[str, Any]]:
    """Find global references absent from builtins and module bindings."""
    import builtins

    root = symtable.symtable(source, filename, "exec")
    known = (
        set(dir(builtins))
        | {
            "__name__",
            "__file__",
            "__package__",
            "__doc__",
            "__builtins__",
            "__conditional_annotations__",  # Python 3.14 creates this symbol for annotations.
        }
    )
    known.update(
        symbol.get_name()
        for symbol in root.get_symbols()
        if symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()
    )
    errors = []

    def visit(table: Any) -> None:
        for symbol in table.get_symbols():
            if (
                symbol.is_referenced()
                and symbol.is_global()
                and symbol.get_name() not in known
            ):
                errors.append(
                    {
                        "line": table.get_lineno() or 1,
                        "column": 1,
                        "message": f"Unresolved symbol: {symbol.get_name()}",
                        "severity": "error",
                    }
                )
        for child in table.get_children():
            visit(child)

    visit(root)
    return errors

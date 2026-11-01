"""Registry editor contracts and workflows.

Description:
    Validates dynamic extension classes and tool schemas before registration. Tool
    input/output boundaries use finite JSON and declared callable contracts.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-registry-call-tool: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-registry-init: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-registry-register: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-registry-unregister: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-registry-unresolved-symbols: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-registry-visit: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor.registry
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import inspect
import logging
import symtable
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from app.core.lib.errors import JSONValue, copy_json
from app.core.trading.statistics.base import BaseMetric as _BaseMetric
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.money_management.base import (
    BasePositionSizer as _BasePositionSizer,
)
from app.extend.what_if.base import BaseWhatIf as _ExtendBaseWhatIf
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor.results import Diagnostic

logger = logging.getLogger(__name__)


class ExtensionTool(Protocol):
    """Required callable surface after runtime extension validation."""

    name: str
    description: str

    def get_input_schema(self) -> dict[str, JSONValue]:
        """Return the declared finite JSON schema."""
        ...

    def run(self, arguments: Mapping[str, JSONValue]) -> object:
        """Execute the tool; its untrusted return is validated at the boundary."""
        ...


class SnippetRegistry:
    """Replace registrations by file so recompilation cannot leave stale classes."""

    def __init__(self) -> None:
        logger.debug("FR-code-editor-registry-init: invoked")
        self.blocks: dict[str, dict[str, type[object]]] = {}
        self.tools: dict[str, ExtensionTool] = {}
        self._tools_by_path: dict[str, list[str]] = {}

    def unregister(self, path: str) -> None:
        """Remove a file or directory and its registered tools."""
        logger.debug("FR-code-editor-registry-unregister: invoked")
        for key in list(self.blocks):
            if key == path or key.startswith(path + "/"):
                self.blocks.pop(key)
                for name in self._tools_by_path.pop(key, []):
                    self.tools.pop(name, None)

    def register(self, path: Path, module: ModuleType) -> list[str]:
        """Validate inheritance and required contracts before publishing changes."""
        logger.debug("FR-code-editor-registry-register: invoked")
        classes = {
            name: value
            for name, value in vars(module).items()
            if inspect.isclass(value) and value.__module__ == module.__name__
        }
        base: type[object] | tuple[type[object], ...] | None = None
        if "indicators" in path.parts:
            base = BaseIndicator
        elif "what_if" in path.parts:
            base = _ExtendBaseWhatIf
        elif "metrics" in path.parts:
            base = _BaseMetric
        elif "money_management" in path.parts:
            base = _BasePositionSizer

        internal_block_files = {
            "base.py",
            "metadata.py",
            "registry.py",
            "series.py",
            "ma.py",
        }
        if path.name in internal_block_files or path.name.startswith("__"):
            classes = {}
            base = None
        if base:
            classes = {
                name: cls
                for name, cls in classes.items()
                if issubclass(cls, base) and not inspect.isabstract(cls)
            }
            if not classes:
                base_name = (
                    base[0].__name__ if isinstance(base, tuple) else base.__name__
                )
                raise CodeEditorError(
                    f"Custom {path.parent.name} must implement {base_name}"
                )
        tools = {}
        if "ai_tools" in path.parts:
            if not classes:
                raise CodeEditorError(
                    "AI tool files must declare at least one tool class"
                )
            for cls in classes.values():
                tool = cast("ExtensionTool", cls())
                if not all(
                    callable(getattr(tool, member, None))
                    for member in ("run", "get_input_schema")
                ):
                    raise CodeEditorError(
                        "AI tools require run() and get_input_schema()"
                    )
                schema = copy_json(cast("JSONValue", tool.get_input_schema()))
                if (
                    not isinstance(tool.name, str)
                    or not isinstance(tool.description, str)
                    or not tool.name
                    or not isinstance(schema, dict)
                ):
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

    def call_tool(self, name: str, arguments: Mapping[str, JSONValue]) -> JSONValue:
        """Dispatch a registered extension using its declared JSON schema."""
        logger.debug("FR-code-editor-registry-call-tool: invoked")
        import jsonschema

        if name not in self.tools:
            raise CodeEditorError(f"Unknown extension tool: {name}")
        tool = self.tools[name]
        try:
            jsonschema.validate(dict(arguments), tool.get_input_schema())
        except (jsonschema.ValidationError, jsonschema.SchemaError) as exc:
            raise CodeEditorError("Invalid AI tool arguments or schema") from exc
        output = tool.run(arguments)
        try:
            return copy_json(cast("JSONValue", output))
        except ValueError:
            from app.core.lib.responses import ErrorCode

            logger.error("FR-code-editor-tool-result: rejected")
            raise CodeEditorError(
                "Invalid extension tool result", code=ErrorCode.INTERNAL
            ) from None


registry = SnippetRegistry()


def unresolved_symbols(source: str, filename: str) -> list[Diagnostic]:
    """Find global references absent from builtins and module bindings."""
    logger.debug("FR-code-editor-registry-unresolved-symbols: invoked")
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
    errors: list[Diagnostic] = []

    def visit(table: symtable.SymbolTable) -> None:
        logger.debug("FR-code-editor-registry-visit: invoked")
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

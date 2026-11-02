"""Static symbol/member and typed indicator catalogues.

Description:
    Indexes public declarations without importing arbitrary snippets. Indicator
    metadata is resolved through the existing authorized indicator capability.
Purpose:
    FEAT-CODE-EDITOR-COMMANDS: Supply completion and indicator selection.
Key Capabilities:
    - FR-editor-catalogue: Log index completion and skipped invalid source;
      tests verify symbols, members, identities and safe diagnostics.
Python API Usage:
    symbols = symbol_catalogue()
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

import ast
import logging
from pathlib import Path

from app.core.lib.errors import copy_json
from app.workspace.code_editor._common import EXTEND_DIR, PROJECT_ROOT
from app.workspace.code_editor._indicator_resolver import resolve_indicator
from app.workspace.code_editor.command_models import IndicatorInfo, SymbolInfo
from app.workspace.code_editor.path_policy import inspect_path

logger = logging.getLogger(__name__)


def symbol_catalogue(root: Path = EXTEND_DIR) -> list[SymbolInfo]:
    """Return deterministic declarations, excluding symlinks and private paths."""
    logger.debug("FR-editor-catalogue: invoked")
    symbols: list[SymbolInfo] = []
    for path in sorted(root.rglob("*.py")):
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            continue
        if any(p.startswith(".") or p == "__pycache__" for p in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except OSError, UnicodeError, SyntaxError:
            logger.warning("FR-editor-catalogue: invalid source skipped")
            continue
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        module = relative.removesuffix(".py").replace("/", ".")
        if module.endswith(".__init__"):
            module = module.removesuffix(".__init__")
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                members = (
                    sorted(
                        {
                            n.name
                            for n in node.body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and not n.name.startswith("_")
                        }
                    )
                    if isinstance(node, ast.ClassDef)
                    else []
                )
                symbols.append(
                    SymbolInfo(
                        name=node.name,
                        module=module,
                        file_path=relative,
                        kind="class" if isinstance(node, ast.ClassDef) else "function",
                        members=members,
                    )
                )
    logger.info("FR-editor-catalogue: completed")
    from app.workspace.code_editor.registry import registry

    for key, classes in list(registry.blocks.items()):
        path = Path(key)
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            continue
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        symbols = [
            s for s in symbols if not (s.file_path == relative and s.kind == "class")
        ]
        for name, cls in list(classes.items()):
            if not name.startswith("_"):
                symbols.append(
                    SymbolInfo(
                        name=name,
                        module=relative.removesuffix(".py").replace("/", "."),
                        file_path=relative,
                        kind="class",
                        members=sorted(
                            name for name in dir(cls) if not name.startswith("_")
                        ),
                    )
                )
    return symbols


def indicator_catalogue() -> list[IndicatorInfo]:
    """List concrete indicators using canonical defaults and output metadata."""
    logger.debug("FR-editor-catalogue: indicators invoked")
    records: list[IndicatorInfo] = []
    indicator_root = EXTEND_DIR / "blocks" / "indicators"
    for symbol in symbol_catalogue(indicator_root):
        if symbol.kind != "class":
            continue
        try:
            cls = resolve_indicator(symbol.file_path + "::" + symbol.name)
            if cls.__name__ != symbol.name:
                continue
            parameters = copy_json(cls().model_dump(mode="json"))
            if not isinstance(parameters, dict):
                raise ValueError("Invalid parameters")
            records.append(
                IndicatorInfo(
                    identity=symbol.file_path + "::" + symbol.name,
                    name=symbol.name,
                    file_path=symbol.file_path,
                    outputs=[o.name for o in cls.spec.outputs],
                    parameters=parameters,
                    protected=inspect_path(symbol.file_path).protected,
                )
            )
        except Exception:
            logger.warning("FR-editor-catalogue: indicator unavailable")
    logger.info("FR-editor-catalogue: indicators completed")
    return records

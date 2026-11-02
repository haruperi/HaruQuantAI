"""Common editor contracts and workflows.

Description:
    Resolves authorized paths, builds typed diagnostic/tab records, and imports the
    exact supplied snippet source with rollback of failed module publication.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-common-dynamic-import-from-path: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-common-dynamic-import-source: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-common-resolve-safe-path: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-common-to-dict: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-common-validate-python-syntax: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-common-writable-snippet-path: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-path-validation: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor._common
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Literal, cast

from app.workspace.code_editor.errors import CodeEditorError
from app.workspace.code_editor.results import CursorPosition, Diagnostic, Tab

__all__ = [
    "CodeEditorError",
    "SyntaxDiagnostic",
    "EditorTab",
    "PROJECT_ROOT",
    "EXTEND_DIR",
    "SNIPPETS_DIR",
    "resolve_safe_path",
    "validate_python_syntax",
    "dynamic_import_from_path",
    "writable_snippet_path",
    "dynamic_import_source",
]

logger = logging.getLogger(__name__)

# Canonical roots for user extensions and standard include blocks
PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXTEND_DIR = PROJECT_ROOT / "app" / "extend"
SNIPPETS_DIR = EXTEND_DIR


@dataclass
class SyntaxDiagnostic:
    """Represents a Python syntax or linting error in a file."""

    line: int
    column: int
    message: str
    severity: Literal["error", "warning", "info"] = "error"
    source_line: str = ""

    def to_dict(self) -> Diagnostic:
        logger.debug("FR-code-editor-common-to-dict: invoked")
        return cast("Diagnostic", asdict(self))


@dataclass
class EditorTab:
    """State tracking for an active code editor document tab."""

    file_path: str
    title: str
    is_dirty: bool = False
    content: str = ""
    mode: str = "python"
    cursor_position: CursorPosition = field(
        default_factory=lambda: CursorPosition(line=1, column=1)
    )

    def to_dict(self) -> Tab:
        logger.debug("FR-code-editor-common-to-dict: invoked")
        return cast("Tab", asdict(self))


def resolve_safe_path(target_path: str | Path, base_dir: Path = PROJECT_ROOT) -> Path:
    """Resolve and verify that a target path resides within an authorized root.

    Args:
        target_path: Relative or absolute path to check.
        base_dir: Root directory the path must reside within.

    Returns:
        Resolved absolute Path.

    Raises:
        CodeEditorError: If the path escapes the authorized directory.
    """
    logger.debug("FR-code-editor-common-resolve-safe-path: invoked")
    resolved_base = base_dir.resolve()
    resolved_target = (
        (resolved_base / target_path).resolve()
        if not Path(target_path).is_absolute()
        else Path(target_path).resolve()
    )

    try:
        resolved_target.relative_to(resolved_base)
    except ValueError as exc:
        msg = f"Path '{target_path}' is outside the authorized root '{base_dir}'."
        logger.error("FR-code-editor-path-validation: rejected")
        raise CodeEditorError(msg) from exc

    return resolved_target


def validate_python_syntax(source_code: str) -> list[SyntaxDiagnostic]:
    """Parse Python source code with AST and return syntax error diagnostics.

    Args:
        source_code: Python string to parse.

    Returns:
        List of SyntaxDiagnostic records (empty if valid).
    """
    logger.debug("FR-code-editor-common-validate-python-syntax: invoked")
    diagnostics: list[SyntaxDiagnostic] = []
    try:
        ast.parse(source_code)
    except SyntaxError as err:
        diagnostics.append(
            SyntaxDiagnostic(
                line=err.lineno or 1,
                column=err.offset or 1,
                message=str(err.msg),
                severity="error",
                source_line=err.text.strip() if err.text else "",
            )
        )
    return diagnostics


def dynamic_import_from_path(file_path: Path) -> ModuleType:
    """Dynamically load or reload a Python module from an absolute file path.

    Args:
        file_path: Absolute Path to the python file.

    Returns:
        Loaded Python module object.
    """
    logger.debug("FR-code-editor-common-dynamic-import-from-path: invoked")
    return dynamic_import_source(file_path, file_path.read_text(encoding="utf-8"))


def writable_snippet_path(target_path: str | Path) -> Path:
    """Reject mutations outside authorized extend directory and protected files."""
    logger.debug("FR-code-editor-common-writable-snippet-path: invoked")
    resolved = resolve_safe_path(target_path)
    try:
        parts = resolved.relative_to(EXTEND_DIR.resolve()).parts
    except ValueError as exc:
        raise CodeEditorError("Only files in app/extend can be modified") from exc
    if not parts or any(part.startswith((".", "__")) for part in parts):
        raise CodeEditorError("Protected snippet package path")
    from app.workspace.code_editor.path_policy import inspect_path

    if inspect_path(resolved).protected:
        logger.warning("FR-editor-path-policy: mutation rejected")
        raise CodeEditorError("Protected builtin or package path")
    return resolved


def dynamic_import_source(file_path: Path, source: str) -> ModuleType:
    """Execute the exact supplied source, bypassing stale bytecode caches."""
    logger.debug("FR-code-editor-common-dynamic-import-source: invoked")
    module_name = (
        "dynamic_snippet_"
        + hashlib.sha256(str(file_path.resolve()).encode()).hexdigest()
    )
    if file_path.resolve().is_relative_to(PROJECT_ROOT):
        package = ".".join(file_path.resolve().relative_to(PROJECT_ROOT).parent.parts)
        if package:
            module_name = f"{package}.{module_name}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise CodeEditorError(f"Could not load module spec for {file_path}")

    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        exec(compile(source, str(file_path), "exec"), module.__dict__)  # noqa: S102
    except BaseException:
        if previous is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous
        raise
    return module

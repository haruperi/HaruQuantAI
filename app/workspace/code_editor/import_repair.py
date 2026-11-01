"""Conservative Python import repair over the editor symbol index.

Description:
    Adds uniquely resolved imports to a returned buffer without writing disk.
    Ambiguity requires an explicit module selection; unknown symbols stay visible.
Purpose:
    FEAT-CODE-EDITOR-COMMANDS: Repair imports without guessing authority.
Key Capabilities:
    - FR-editor-import-repair: Log completion and invalid selection rejection;
      tests verify ambiguity, idempotence and future/docstring placement.
Python API Usage:
    result = repair_imports(RepairRequest(file_path="app/extend/user/a.py", content=""))
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

import ast
import logging

from app.workspace.code_editor._common import CodeEditorError, writable_snippet_path
from app.workspace.code_editor.catalogue import symbol_catalogue
from app.workspace.code_editor.command_models import (
    ImportChoice,
    RepairRequest,
    RepairResult,
)
from app.workspace.code_editor.registry import unresolved_symbols

logger = logging.getLogger(__name__)


def repair_imports(request: RepairRequest) -> RepairResult:
    """Return a repaired buffer; never execute indexed code or change the file."""
    logger.debug("FR-editor-import-repair: invoked")
    path = writable_snippet_path(request.file_path)
    try:
        tree = ast.parse(request.content)
    except SyntaxError:
        raise CodeEditorError("Repair syntax errors before fixing imports") from None
    index: dict[str, set[str]] = {}
    for standard_module, names in {
        "pathlib": ["Path", "PurePath"],
        "dataclasses": ["dataclass", "field"],
        "typing": [
            "Any",
            "ClassVar",
            "Literal",
            "Protocol",
            "Mapping",
            "Sequence",
            "override",
        ],
        "datetime": ["datetime", "timedelta", "UTC"],
        "pydantic": ["BaseModel", "Field"],
    }.items():
        for name in names:
            index.setdefault(name, set()).add(standard_module)
    for symbol in symbol_catalogue():
        if symbol.file_path != request.file_path:
            index.setdefault(symbol.name, set()).add(symbol.module)
    names = sorted(
        {
            d["message"].removeprefix("Unresolved symbol: ")
            for d in unresolved_symbols(request.content, str(path))
        }
    )
    if set(request.selections) - set(names):
        raise CodeEditorError("Import selection does not match an unresolved symbol")
    added: list[str] = []
    pending: list[ImportChoice] = []
    for name in names:
        candidates = sorted(index.get(name, set()))
        selected = request.selections.get(name)
        if selected is not None and selected not in candidates:
            logger.warning("FR-editor-import-repair: selection rejected")
            raise CodeEditorError("Import selection is not an indexed candidate")
        module = selected or (candidates[0] if len(candidates) == 1 else None)
        if module:
            added.append(f"from {module} import {name}")
        else:
            pending.append(ImportChoice(symbol=name, candidates=candidates))
    # Preserve module docstring, __future__, shebang and encoding comments.
    insertion = 0
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and insertion == 0
        ) or (isinstance(node, ast.ImportFrom) and node.module == "__future__"):
            insertion = node.end_lineno or node.lineno
        else:
            break
    lines = request.content.splitlines(keepends=True)
    while insertion < len(lines) and lines[insertion].startswith("#"):
        insertion += 1
    if added:
        if insertion and not lines[insertion - 1].endswith("\n"):
            lines[insertion - 1] += "\n"
        lines[insertion:insertion] = [text + "\n" for text in added]
    logger.info("FR-editor-import-repair: completed")
    return RepairResult(content="".join(lines), added=added, unresolved=pending)

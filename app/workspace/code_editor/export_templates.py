"""Source-authoring export templates and explicit supported formats.

Description:
    Creates new Python or pseudocode templates from selected public Python symbols.
    Output is editable source text; this capability does not compile trading targets.
Purpose:
    FEAT-CODE-EDITOR-COMMANDS: Supply path-aware source-export authoring.
Key Capabilities:
    - FR-editor-export-template: Log creation and format/path rejection;
      tests verify content, format filtering, collisions and protection.
Python API Usage:
    formats = supported_formats()
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

import ast
import logging

from app.workspace.code_editor._common import (
    CodeEditorError,
    resolve_safe_path,
    writable_snippet_path,
)
from app.workspace.code_editor._storage import atomic_create_file
from app.workspace.code_editor.command_models import ExportTemplateRequest, FormatInfo
from app.workspace.code_editor.results import SaveResult

logger = logging.getLogger(__name__)


def supported_formats(file_path: str | None = None) -> list[FormatInfo]:
    """Filter by explicit authoring-format directory when one is selected."""
    logger.debug("FR-editor-export-template: formats invoked")
    formats = [
        FormatInfo(
            format_id="python", name="Python source template", extension=".py.tpl"
        ),
        FormatInfo(
            format_id="pseudocode", name="Pseudocode template", extension=".txt.tpl"
        ),
    ]
    if file_path:
        parts = resolve_safe_path(file_path).parts
        selected = next((f.format_id for f in formats if f.format_id in parts), None)
        if selected:
            formats = [f for f in formats if f.format_id == selected]
    return formats


def create_export_template(request: ExportTemplateRequest) -> SaveResult:
    """Publish a complete new template; never replace an existing destination."""
    logger.debug("FR-editor-export-template: creation invoked")
    target = writable_snippet_path(request.target_path)
    formats = supported_formats(request.target_path)
    chosen = next((f for f in formats if f.format_id == request.format_id), None)
    if chosen is None or not target.name.endswith(chosen.extension):
        raise CodeEditorError("Destination does not match the selected export format")
    chunks: list[str] = []
    for source in dict.fromkeys(request.source_paths):
        path = resolve_safe_path(source)
        if path.suffix != ".py" or not path.is_file():
            raise CodeEditorError("Export templates require existing Python sources")
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError, UnicodeError:
            raise CodeEditorError(
                "Export template source is not valid Python"
            ) from None
        names = [
            n.name
            for n in tree.body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef))
            and not n.name.startswith("_")
        ]
        for name in names:
            from app.workspace.code_editor._common import PROJECT_ROOT

            module = (
                path.relative_to(PROJECT_ROOT)
                .as_posix()
                .removesuffix(".py")
                .replace("/", ".")
            )
            if request.format_id == "python":
                chunks.append(f"from {module} import {name}\n")
            else:
                chunks.append(f"USE {name} FROM {module}\n")
    if not chunks:
        raise CodeEditorError("Selected sources declare no public classes or functions")
    content = "".join(chunks).encode("utf-8")
    atomic_create_file(target, content)
    logger.info("FR-editor-export-template: created")
    from app.workspace.code_editor._common import PROJECT_ROOT

    return {
        "status": "saved",
        "file_path": target.relative_to(PROJECT_ROOT).as_posix(),
        "bytes_written": len(content),
        "diagnostics": [],
    }

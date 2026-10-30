"""Init editor contracts and workflows.

Description:
    Exports the retained editor services and router; HTTP owns request execution. No
    workspace logging handlers or workers are installed here.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-http-operation: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from app.workspace.code_editor._common import (
    CodeEditorError,
    EditorTab,
    SyntaxDiagnostic,
)
from app.workspace.code_editor.editor import AppCodeEditor
from app.workspace.code_editor.http import router as code_editor_router
from app.workspace.code_editor.import_export import ImportExport
from app.workspace.code_editor.indicator_tester import IndicatorTester
from app.workspace.code_editor.routes import CodeEditor
from app.workspace.code_editor.templates import (
    get_template,
    list_templates,
    render_template,
)

__all__ = [
    "AppCodeEditor",
    "CodeEditor",
    "CodeEditorError",
    "EditorTab",
    "ImportExport",
    "IndicatorTester",
    "SyntaxDiagnostic",
    "code_editor_router",
    "get_template",
    "list_templates",
    "render_template",
]

"""AppCodeEditor workspace package for HaruQuantAI.

Reimplementation of StrategyQuant X's CodeEditor module, featuring:
- Document session manager and multi-tab code editor
- 12 snippet boilerplate code generators
- Workspace file navigator, clone, rename, delete, and search
- AST syntax validation and dynamic module hot-reloading
- Interactive Indicator Tester with Lightweight Charts candlestick & plot series
- Extension package import/export (.zip with manifest)
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

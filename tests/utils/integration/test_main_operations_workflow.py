"""Structural integration evidence for WF-UTL-010."""

import ast
from pathlib import Path

_WORKFLOW = (
    Path(__file__).parents[1] / "usage" / "workflows" / "wf_utl_010_main_operations.py"
)


def test_main_operations_workflow_uses_current_public_boundaries() -> None:
    """Verify the workflow exists, is executable, and avoids retired imports."""
    source = _WORKFLOW.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }

    assert "app.utils" in imported_modules
    assert "app.services.utils" not in source
    assert "app.services.notification" not in source
    assert 'if __name__ == "__main__":' in source


def test_main_operations_workflow_is_registered() -> None:
    """Verify the aggregate workflow runner includes WF-UTL-010."""
    runner = _WORKFLOW.with_name("run_all.py").read_text(encoding="utf-8")
    assert '"wf_utl_010_main_operations.py"' in runner

"""Unit tests for AppCodeEditor workspace session management."""

from pathlib import Path

import pytest
from app.workspace.code_editor._common import PROJECT_ROOT, CodeEditorError
from app.workspace.code_editor.editor import AppCodeEditor


def test_init_workspace():
    """Verify clean workspace initialization."""
    editor = AppCodeEditor()
    state = editor.init_workspace()
    assert state["status"] == "ready"
    assert state["active_file"] is None
    assert state["open_tabs"] == []
    assert state["layout"]["navigator_visible"] is True


def test_open_save_and_close_tab(tmp_path: Path):
    """Verify document lifecycle: opening, editing, saving, and closing tabs."""
    editor = AppCodeEditor()
    # Create a temporary file relative to project root
    test_rel = "app/include/blocks/indicators/custom/test_snippet_temp.py"
    test_abs = PROJECT_ROOT / test_rel
    test_abs.parent.mkdir(parents=True, exist_ok=True)
    test_abs.write_text("x = 42\n", encoding="utf-8")

    try:
        # Open tab
        res_open = editor.open_file_tab(test_rel)
        assert res_open["status"] == "opened"
        assert res_open["active_file"] == test_rel

        # Re-opening switches tab
        res_switch = editor.open_file_tab(test_rel)
        assert res_switch["status"] == "switched"

        # Save with valid code
        res_save = editor.save_file(test_rel, "x = 100\n")
        assert res_save["status"] == "saved"
        assert len(res_save["diagnostics"]) == 0
        assert test_abs.read_text(encoding="utf-8") == "x = 100\n"

        # Save with syntax error captures diagnostic
        res_err = editor.save_file(test_rel, "def invalid_syntax(\n")
        assert len(res_err["diagnostics"]) > 0
        assert res_err["diagnostics"][0]["severity"] == "error"

        # Mark tab dirty
        editor._tabs[test_rel].is_dirty = True
        close_refused = editor.close_file_tab(test_rel, force=False)
        assert close_refused["status"] == "unsaved_changes"

        # Force close
        close_forced = editor.close_file_tab(test_rel, force=True)
        assert close_forced["status"] == "closed"
        assert editor._active_file is None
    finally:
        if test_abs.exists():
            test_abs.unlink()


def test_open_nonexistent_file_raises():
    """Verify attempting to open a non-existent file raises CodeEditorError."""
    editor = AppCodeEditor()
    with pytest.raises(CodeEditorError):
        editor.open_file_tab(
            "app/include/blocks/indicators/custom/non_existent_file_abc.py"
        )

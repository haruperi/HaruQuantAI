"""Unit tests for CodeEditor navigation, actions, and compilation."""

import pytest
from app.workspace.code_editor._common import (
    PROJECT_ROOT,
)
from app.workspace.code_editor.routes import CodeEditor


@pytest.fixture
def service():
    return CodeEditor()


def test_menu_and_tabs_layout(service: CodeEditor):
    """Verify toolbar and panel layout queries."""
    menu = service.menu()
    assert "toolbar" in menu
    assert len(menu["toolbar"]) >= 6

    righttabs = service.righttabs()
    assert "navigator" in righttabs["tabs"]

    bottomtabs = service.bottomtabs()
    assert "log" in bottomtabs["tabs"]


def test_navigator_tree(service: CodeEditor):
    """Verify navigator builds a tree."""
    tree = service.navigator()
    assert tree["type"] == "directory"
    assert "children" in tree


def test_create_new_snippet_and_delete(service: CodeEditor):
    """Verify template snippet creation and subsequent deletion."""
    test_name = "UnitTesterIndicator"
    res = service.create_new("BlocksIndicators", test_name)
    assert res["status"] == "created"
    file_path = PROJECT_ROOT / res["file_path"]
    assert file_path.exists()

    try:
        # File should be compiled successfully
        comp = service.compile_file(res["file_path"])
        assert comp["success"] is True

        # Search should find the class name
        matches = service.find_in_files(test_name)
        assert len(matches) > 0
    finally:
        service.delete_file(res["file_path"])
        assert not file_path.exists()


def test_clone_and_rename(service: CodeEditor):
    """Verify clone and rename file operations."""
    src_rel = "app/include/indicators/custom/test_clone_src.py"
    clone_rel = "app/include/indicators/custom/test_clone_dst.py"
    renamed_rel = "app/include/indicators/custom/test_clone_renamed.py"

    src_abs = PROJECT_ROOT / src_rel
    clone_abs = PROJECT_ROOT / clone_rel
    renamed_abs = PROJECT_ROOT / renamed_rel

    src_abs.parent.mkdir(parents=True, exist_ok=True)
    src_abs.write_text("# Clone source file\n", encoding="utf-8")

    try:
        # Clone
        res_clone = service.clone(src_rel, clone_rel)
        assert res_clone["status"] == "saved"
        assert clone_abs.exists()

        # Rename
        res_rename = service.rename_file(clone_rel, renamed_rel)
        assert res_rename["status"] == "renamed"
        assert not clone_abs.exists()
        assert renamed_abs.exists()
    finally:
        for p in (src_abs, clone_abs, renamed_abs):
            if p.exists():
                p.unlink()

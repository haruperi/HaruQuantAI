"""Behavioral regressions for the pre-commit editor review findings."""

import json
import os
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from app.workspace.code_editor._common import (
    PROJECT_ROOT,
    SNIPPETS_DIR,
    CodeEditorError,
)
from app.workspace.code_editor.editor import AppCodeEditor
from app.workspace.code_editor.import_export import ImportExport
from app.workspace.code_editor.indicator_tester import IndicatorTester
from app.workspace.code_editor.registry import registry
from app.workspace.code_editor.routes import CodeEditor
from app.workspace.code_editor.templates import list_templates, render_template


@pytest.fixture
def snippets():
    with TemporaryDirectory(dir=SNIPPETS_DIR, prefix="regression_") as folder:
        yield Path(folder)


def test_dirty_buffer_survives_restart_and_close_requires_force(snippets):
    path = snippets / "dirty.py"
    path.write_text("original = 1", encoding="utf-8")
    relative = path.relative_to(PROJECT_ROOT).as_posix()
    editor = AppCodeEditor()
    tab = editor.open_file_tab(str(path))["tab"]
    tab["content"] = ""
    editor.sync_session([tab], relative)
    restored = AppCodeEditor()
    state = restored.init_workspace()
    assert state["open_tabs"][0]["content"] == ""
    assert state["open_tabs"][0]["is_dirty"]
    assert restored.close_file_tab(str(path))["status"] == "unsaved_changes"
    assert path.read_text(encoding="utf-8") == "original = 1"


def test_rename_directory_preserves_dirty_descendants(snippets):
    folder = snippets / "original"
    folder.mkdir()
    path = folder / "dirty.py"
    path.write_text("x = 1", encoding="utf-8")
    editor = AppCodeEditor()
    tab = editor.open_file_tab(str(path))["tab"]
    tab["content"] = "x = 2"
    editor.sync_session([tab], tab["file_path"])
    CodeEditor(editor).rename_file(str(folder), str(snippets / "moved"))
    state = AppCodeEditor().init_workspace()
    assert state["active_file"].endswith("/moved/dirty.py")
    assert state["open_tabs"][0]["content"] == "x = 2"
    assert state["open_tabs"][0]["is_dirty"]
    editor.save_all_files()
    assert (snippets / "moved/dirty.py").read_text(encoding="utf-8") == "x = 2"
    assert not folder.exists()


@pytest.mark.parametrize(
    "path",
    [
        "app/main.py",
        "app/include",
        "app/include/blocks/indicators/__init__.py",
        "app/include/blocks/actions/__init__.py",
        ".",
    ],
)
def test_delete_protected_paths_is_rejected(path):
    with pytest.raises(CodeEditorError):
        CodeEditor().delete_file(path)
    assert (PROJECT_ROOT / path).exists()


def test_save_all_rolls_back_replaced_and_new_files(snippets):
    old = snippets / "old.py"
    new = snippets / "new.py"
    old.write_text("old", encoding="utf-8")
    replace = os.replace
    failed = False

    def fail_second(source, target):
        nonlocal failed
        if Path(target) == new and not failed:
            failed = True
            raise OSError("simulated disk failure")
        return replace(source, target)

    with (
        patch("app.workspace.code_editor._storage.os.replace", side_effect=fail_second),
        pytest.raises(OSError),
    ):
        AppCodeEditor().save_all_files(
            [
                {"file_path": str(old), "content": "new"},
                {"file_path": str(new), "content": "created"},
            ]
        )
    assert old.read_text(encoding="utf-8") == "old"
    assert not new.exists()
    assert not list(snippets.glob(".editor-*"))


def test_compile_executes_unsaved_buffer_and_checks_function_globals(snippets):
    path = snippets / "buffer.py"
    path.write_text("class Example:\n    value = 1\n", encoding="utf-8")
    service = CodeEditor()
    result = service.compile_file(str(path), "class Example:\n    value = 2\n")
    assert result["success"]
    assert registry.blocks[str(path)]["Example"].value == 2
    assert "value = 1" in path.read_text(encoding="utf-8")
    invalid = service.compile_file(str(path), "def f():\n    return missing_name\n")
    assert not invalid["success"]
    assert "missing_name" in invalid["errors"][0]["message"]


def test_compile_enforces_indicator_inheritance(snippets):
    directory = snippets / "indicators"
    directory.mkdir()
    result = CodeEditor().compile_file(
        str(directory / "invalid.py"), "class Invalid: pass"
    )
    assert not result["success"]
    assert "BaseIndicator" in result["errors"][0]["message"]


@pytest.mark.parametrize("template", [item["template_id"] for item in list_templates()])
def test_every_template_imports_and_registers(snippets, template):
    source, target = render_template(template, "ReviewExample")
    path = snippets / Path(target).parent.name / "review_example.py"
    path.parent.mkdir()
    result = CodeEditor().compile_file(str(path), source)
    assert result["success"], result
    if template == "AITools":
        assert (
            "EURUSD"
            in registry.call_tool("ext_review_example", {"target_symbol": "EURUSD"})[
                "result"
            ]
        )


def test_clone_changes_class_and_self_references(snippets):
    source, target = snippets / "source.py", snippets / "new_name.py"
    source.write_text(
        "class Source:\n    def clone(self):\n        return Source()\n",
        encoding="utf-8",
    )
    CodeEditor().clone(str(source), str(target))
    text = target.read_text(encoding="utf-8")
    assert "class NewName" in text
    assert "return NewName()" in text


def test_import_rename_preserves_existing_renamed_files_and_reloads(snippets, tmp_path):
    target = snippets / "example.py"
    target.write_text("original", encoding="utf-8")
    renamed = snippets / "example_imported.py"
    renamed.write_text("keep", encoding="utf-8")
    archive = tmp_path / "package.zip"
    relative = target.relative_to(PROJECT_ROOT).as_posix()
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr(relative, "class Imported: pass")
        stream.writestr("manifest.json", json.dumps({"files": [relative]}))
    result = ImportExport().overwrite_confirm(archive, {relative: "rename"})
    assert renamed.read_text(encoding="utf-8") == "keep"
    assert result["extracted"][0].endswith("example_imported_2.py")
    assert result["reload_results"][0]["module_reloaded"]


def test_import_preflights_all_paths_before_writing(snippets, tmp_path):
    target = snippets / "safe.py"
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr(target.relative_to(PROJECT_ROOT).as_posix(), "x = 1")
        stream.writestr("app/main.py", "x = 2")
    with pytest.raises(CodeEditorError):
        ImportExport().overwrite_confirm(archive)
    assert not target.exists()


def test_tester_reads_history_and_rejects_missing_symbol():
    tester = IndicatorTester()
    result = tester.indicator_tester("SMA", params={"period": 5}, bar_count=5)
    assert result["data_source"] == "historical"
    assert result["candlesticks"][-1]["close"] == pytest.approx(1.10299)
    assert tester.indicator_tester("SMA", symbol="MISSING")["status"] == "failed"


def test_tester_preserves_nan_gaps_and_multiple_outputs():
    tester = IndicatorTester()
    nan = tester.indicator_tester(
        "SMA", params={"period": 200}, bars_to_reserve=0, bar_count=10
    )
    assert nan["status"] == "success"
    assert all("value" not in point for point in nan["indicator_plots"])
    assert len(tester.indicator_tester_error(nan["test_id"])) == 10
    bands = tester.indicator_tester("BollingerBands", bar_count=10)
    assert bands["status"] == "success", bands
    assert len(bands["plot_series"]) > 1
    assert {plot["pane"] for plot in bands["plot_series"]} == {"main", "oscillator"}


def test_config_roundtrip_and_param_edit_preserve_identity_and_history():
    tester = IndicatorTester()
    result = tester.indicator_tester(
        "SMA", bar_count=10, bars_to_reserve=20, params={"period": 5}
    )
    identifier = result["test_id"]
    tester.save_test_config(identifier, "Saved")
    restarted = IndicatorTester()
    restored = restarted.load_test_config(identifier)["config"]
    assert restored["params"] == {"period": 5}
    edited = restarted.edit_indy_params(identifier, {"period": 10})
    assert edited["test_id"] == identifier
    assert len(edited["candlesticks"]) == 10
    assert edited["candlesticks"] == result["candlesticks"]
    assert restarted.new_indy_test("MACD")["params"] == {
        "fast": 12,
        "slow": 26,
        "smooth": 9,
    }
    with pytest.raises(CodeEditorError):
        restarted.save_test_config("unknown", "Nope")

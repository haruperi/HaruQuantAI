"""Save As publication, protection, identity and failure semantics."""

import logging
import tempfile
from pathlib import Path

import pytest
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor import _storage
from app.workspace.code_editor._common import EXTEND_DIR, PROJECT_ROOT
from app.workspace.code_editor.editor import AppCodeEditor
from app.workspace.code_editor.errors import CodeEditorError


@pytest.fixture
def documents():
    with tempfile.TemporaryDirectory(dir=EXTEND_DIR, prefix="save_as_") as name:
        folder = Path(name).resolve()
        assert folder.is_relative_to(EXTEND_DIR.resolve())
        source = folder / "source.py"
        other = folder / "other.py"
        source.write_text("original = 1\n", encoding="utf-8")
        other.write_text("other = 2\n", encoding="utf-8")
        editor = AppCodeEditor()
        editor.open_file_tab(str(source))
        editor.open_file_tab(str(other))
        editor.sync_session(
            [
                {"file_path": str(source), "content": "unsaved = 3\n"},
                {"file_path": str(other), "content": "other_dirty = 4\n"},
            ],
            source.relative_to(PROJECT_ROOT).as_posix(),
        )
        yield editor, source, other, folder


@pytest.mark.parametrize("content", ["", "saved = 'λ'\n"])
def test_save_as_publishes_buffer_and_replaces_only_source_identity(
    documents, content, caplog
):
    editor, source, other, folder = documents
    destination = folder / "new.py"
    before = editor.init_workspace()
    caplog.set_level(logging.DEBUG, logger="app.workspace.code_editor")
    result = editor.save_as(str(source), str(destination), content)
    assert result["status"] == "saved_as"
    assert result["bytes_written"] == len(content.encode("utf-8"))
    assert destination.read_text(encoding="utf-8") == content
    assert source.read_text(encoding="utf-8") == "original = 1\n"
    after = editor.init_workspace()
    assert after["open_tabs"][0] == result["tab"]
    assert after["open_tabs"][1] == before["open_tabs"][1]
    assert after["open_tabs"][1]["is_dirty"] is True
    assert result["tab"]["is_dirty"] is False
    assert after["active_file"] == result["file_path"]
    assert after["active_file"] != source.relative_to(PROJECT_ROOT).as_posix()
    assert AppCodeEditor().init_workspace() == after
    assert "FR-code-editor-save-as: completed" in caplog.text
    assert "FR-code-editor-create-file: completed" in caplog.text


@pytest.mark.parametrize(
    "target_kind", ["existing", "same", "alias", "directory", "open_missing"]
)
def test_collisions_preserve_disk_and_session(documents, target_kind):
    editor, source, other, folder = documents
    target = folder / "new.py"
    if target_kind == "existing":
        target.write_text("keep = 5", encoding="utf-8")
    elif target_kind == "same":
        target = source
    elif target_kind == "alias":
        target = folder / ".." / folder.name / source.name
    elif target_kind == "directory":
        target.mkdir()
    else:
        current = editor.init_workspace()
        editor.sync_session(
            [
                *[
                    {"file_path": tab["file_path"], "content": tab["content"]}
                    for tab in current["open_tabs"]
                ],
                {"file_path": str(target), "content": "pending = 1"},
            ],
            current["active_file"],
        )
    before = editor.init_workspace()
    with pytest.raises(CodeEditorError) as rejected:
        editor.save_as(str(source), str(target), "replacement = 0")
    assert rejected.value.category is ErrorCode.CONFLICT
    assert editor.init_workspace() == before
    assert source.read_text(encoding="utf-8") == "original = 1\n"
    if target_kind == "existing":
        assert target.read_text(encoding="utf-8") == "keep = 5"
    if target_kind == "open_missing":
        assert not target.exists()


@pytest.mark.parametrize(
    "target",
    [
        "app/extend/__init__.py",
        "app/extend/.protected/new.py",
        "app/main.py",
        "app/extend",
    ],
)
def test_protected_destinations_are_rejected_before_publication(documents, target):
    editor, source, _, folder = documents
    before = editor.init_workspace()
    with pytest.raises(CodeEditorError):
        editor.save_as(str(source), target, "replacement = 0")
    assert editor.init_workspace() == before
    assert sorted(path.name for path in folder.iterdir()) == ["other.py", "source.py"]


def test_missing_source_tab_does_not_create_destination(documents):
    editor, _, _, folder = documents
    with pytest.raises(CodeEditorError) as rejected:
        editor.save_as(str(folder / "closed.py"), str(folder / "new.py"), "")
    assert rejected.value.category is ErrorCode.NOT_FOUND
    assert not (folder / "new.py").exists()


def test_publication_race_never_replaces_a_new_destination(documents, monkeypatch):
    editor, source, _, folder = documents
    target = folder / "new.py"
    before = editor.init_workspace()
    link = _storage.os.link

    def competing_link(staged, destination):
        Path(destination).write_text("racer = 1", encoding="utf-8")
        link(staged, destination)

    monkeypatch.setattr(_storage.os, "link", competing_link)
    with pytest.raises(CodeEditorError) as rejected:
        editor.save_as(str(source), str(target), "mine = 2")
    assert rejected.value.category is ErrorCode.CONFLICT
    assert target.read_text(encoding="utf-8") == "racer = 1"
    assert editor.init_workspace() == before
    assert not list(folder.glob(".editor-new-*"))


@pytest.mark.parametrize("failure", ["fsync", "link"])
def test_staging_failure_does_not_publish_partial_content(
    documents, monkeypatch, failure
):
    editor, source, _, folder = documents
    target = folder / "new.py"
    before = editor.init_workspace()

    def fail_sync(*_args):
        raise OSError("private-marker")

    monkeypatch.setattr(_storage.os, failure, fail_sync)
    with pytest.raises(CodeEditorError) as rejected:
        editor.save_as(str(source), str(target), "mine = 2")
    assert rejected.value.category is ErrorCode.UNAVAILABLE
    assert "private-marker" not in str(rejected.value)
    assert not target.exists()
    assert not list(folder.glob(".editor-new-*"))
    assert editor.init_workspace() == before


def test_persistence_failure_retains_new_file_and_original_session(
    documents, monkeypatch, caplog
):
    editor, source, _, folder = documents
    target = folder / "new.py"
    before = editor.init_workspace()
    stored = editor._store.read("workspace")

    def fail_write(*_args):
        raise RuntimeError("private-marker")

    monkeypatch.setattr(editor._store, "write", fail_write)
    with pytest.raises(CodeEditorError) as rejected:
        editor.save_as(str(source), str(target), "recoverable = 2")
    assert rejected.value.category is ErrorCode.UNAVAILABLE
    assert "File created; workspace state could not be saved" in str(rejected.value)
    assert "private-marker" not in str(rejected.value)
    assert "private-marker" not in caplog.text
    assert target.read_text(encoding="utf-8") == "recoverable = 2"
    assert source.read_text(encoding="utf-8") == "original = 1\n"
    assert editor.init_workspace() == before
    assert editor._store.read("workspace") == stored


def test_save_as_returns_syntax_diagnostics_without_compiling(documents):
    editor, source, _, folder = documents
    result = editor.save_as(str(source), str(folder / "invalid.py"), "def invalid(:")
    assert result["diagnostics"][0]["severity"] == "error"
    assert result["tab"]["content"] == "def invalid(:"

"""Command acceptance against isolated source trees and real host jobs."""

import ast
import logging
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest
from app.core.host.resources import ResourceMonitor
from app.core.jobs.manager import JobManager
from app.main import create_app
from app.workspace.code_editor import catalogue
from app.workspace.code_editor._common import EXTEND_DIR, PROJECT_ROOT
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.command_models import (
    CompilationRequest,
    ExportTemplateRequest,
    RepairRequest,
)
from app.workspace.code_editor.compilation import CompilationService
from app.workspace.code_editor.editor import AppCodeEditor
from app.workspace.code_editor.errors import CodeEditorError
from app.workspace.code_editor.export_templates import (
    create_export_template,
    supported_formats,
)
from app.workspace.code_editor.import_repair import repair_imports
from app.workspace.code_editor.path_policy import inspect_path
from app.workspace.code_editor.registry import registry
from app.workspace.code_editor.routes import CodeEditor
from app.workspace.code_editor.templates import list_templates, render_template
from fastapi.testclient import TestClient


@pytest.fixture
def source_tree():
    with tempfile.TemporaryDirectory(dir=EXTEND_DIR, prefix="commands_") as name:
        root = Path(name).resolve()
        assert root.is_relative_to(EXTEND_DIR.resolve())
        yield root


@pytest.fixture
def service(isolated_editor, tmp_path):
    manager = JobManager(
        max_workers=1,
        persistence=isolated_editor,
        resource_mgr=ResourceMonitor(scratch_root=tmp_path / "scratch"),
        min_available_ram_pct=0,
    )
    service = CompilationService(manager, StateStore(isolated_editor))
    yield service
    manager.shutdown(wait=True, cancel_futures=True)


def relative(path):
    return path.relative_to(PROJECT_ROOT).as_posix()


def test_reload_requires_confirmation_and_preserves_other_buffers(source_tree, caplog):
    caplog.set_level(logging.DEBUG)
    source = source_tree / "first.py"
    other = source_tree / "second.py"
    source.write_text("disk = 1", encoding="utf-8")
    other.write_text("other = 1", encoding="utf-8")
    editor = AppCodeEditor()
    editor.open_file_tab(str(source))
    editor.open_file_tab(str(other))
    editor.sync_session(
        [
            {"file_path": relative(source), "content": "dirty = 1"},
            {"file_path": relative(other), "content": "dirty_other = 2"},
        ],
        relative(source),
    )
    before = editor.init_workspace()
    with pytest.raises(CodeEditorError, match="Confirm"):
        editor.reload_disk(str(source))
    assert editor.init_workspace() == before
    source.write_text("external = 3", encoding="utf-8")
    assert (
        editor.reload_disk(str(source), discard_dirty=True)["content"] == "external = 3"
    )
    assert editor.init_workspace()["open_tabs"][1] == before["open_tabs"][1]
    assert "FR-editor-reload: completed" in caplog.text
    source.unlink()
    before = editor.init_workspace()
    with pytest.raises(CodeEditorError):
        editor.reload_disk(str(source), discard_dirty=True)
    assert editor.init_workspace() == before


def test_missing_file_restart_retains_buffer_dirty(source_tree):
    source = source_tree / "missing.py"
    source.write_text("recover = 1", encoding="utf-8")
    editor = AppCodeEditor()
    editor.open_file_tab(str(source))
    source.unlink()
    restored = AppCodeEditor().init_workspace()["open_tabs"][0]
    assert restored["content"] == "recover = 1"
    assert restored["is_dirty"]


def test_corrupt_session_is_not_rewritten(isolated_editor):
    store = StateStore(isolated_editor)
    store.write("workspace", {"open_tabs": "corrupt", "active_file": None})
    before = store.read("workspace")
    with pytest.raises(CodeEditorError):
        AppCodeEditor(store).init_workspace()
    assert store.read("workspace") == before


def test_builtin_policy_clone_and_mutation(source_tree):
    source = "app/extend/what_if/by_days.py"
    info = inspect_path(source)
    assert info.protected and info.ownership == "builtin"
    assert info.clone_target.startswith("app/extend/user/")
    with pytest.raises(CodeEditorError):
        AppCodeEditor().save_file(source, "do_not_write = 1")
    with pytest.raises(CodeEditorError):
        CodeEditor().delete_file("app/extend/what_if")
    target = source_tree / "cloned.py"
    CodeEditor().clone(source, str(target))
    assert "class Cloned" in target.read_text(encoding="utf-8")
    assert inspect_path(target).ownership == "user"


def test_navigator_ownership_and_search_controls(source_tree):
    source = source_tree / "alpha.py"
    source.write_text("Alpha alphabet ALPHA\n", encoding="utf-8")
    editor = CodeEditor()
    tree = editor.navigator(str(source_tree), ownership="user", filter_text="alpha")
    assert tree["children"][0]["ownership"] == "user"
    assert editor.navigator(str(source_tree), ownership="builtin")["children"] == []
    matches = editor.find_in_files(
        "Alpha", search_dir=str(source_tree), whole_word=True, case_sensitive=True
    )
    assert len(matches) == 1
    assert (
        len(editor.find_in_files("alpha", search_dir=str(source_tree), whole_word=True))
        == 2
    )
    with pytest.raises(CodeEditorError, match="regular expression"):
        editor.find_in_files("[", regex=True)


def test_static_symbols_members_and_invalid_source(source_tree, caplog):
    (source_tree / "symbols.py").write_text(
        "class Marker:\n    def member(self): pass\n\ndef helper(): pass",
        encoding="utf-8",
    )
    (source_tree / "bad.py").write_text("def (", encoding="utf-8")
    records = catalogue.symbol_catalogue(source_tree)
    assert [(r.name, r.members) for r in records] == [
        ("Marker", ["member"]),
        ("helper", []),
    ]
    assert "invalid source skipped" in caplog.text


def test_indicator_catalogue_has_canonical_defaults():
    records = catalogue.indicator_catalogue()
    sma = next(record for record in records if record.name == "SMA")
    assert sma.outputs == ["value"]
    assert sma.parameters["period"] > 0
    assert sma.protected


def test_import_repair_unique_ambiguous_selection_and_idempotence(
    source_tree, monkeypatch
):
    for name in ("first", "second"):
        (source_tree / f"{name}.py").write_text(
            "class Shared: pass\n", encoding="utf-8"
        )
    (source_tree / "unique.py").write_text("class Unique: pass\n", encoding="utf-8")
    monkeypatch.setattr(
        "app.workspace.code_editor.import_repair.symbol_catalogue",
        lambda: catalogue.symbol_catalogue(source_tree),
    )
    target = relative(source_tree / "consumer.py")
    source = '"""Module docs."""\nfrom __future__ import annotations\nvalue = Unique()\nother = Shared()\n'
    result = repair_imports(RepairRequest(file_path=target, content=source))
    assert len(result.added) == 1
    assert result.unresolved[0].symbol == "Shared"
    assert len(result.unresolved[0].candidates) == 2
    assert result.content.index("from __future__") < result.content.index(
        result.added[0]
    )
    ast.parse(result.content)
    selected = result.unresolved[0].candidates[0]
    result = repair_imports(
        RepairRequest(file_path=target, content=source, selections={"Shared": selected})
    )
    assert not result.unresolved
    assert (
        repair_imports(RepairRequest(file_path=target, content=result.content)).added
        == []
    )
    with pytest.raises(CodeEditorError):
        repair_imports(
            RepairRequest(
                file_path=target, content=source, selections={"Shared": "untrusted"}
            )
        )


@pytest.mark.parametrize("kind", ["Manipulation", "Retest"])
def test_monte_carlo_subtype_and_path_catalogues(kind):
    content, path = render_template("MonteCarlo", "NewSimulation", mc_type=kind)
    ast.parse(content)
    assert kind.lower() in path
    assert all(
        item["template_id"].startswith("MonteCarlo")
        for item in list_templates("app/extend/monte_carlo")
    )
    assert list_templates("app/extend/user/code_templates") == []


@pytest.mark.parametrize("action", ["Open", "Modify", "Close"])
def test_order_action_mapping(action):
    content, path = render_template(
        "BlocksOrder", "NewAction", order_action_type=action
    )
    ast.parse(content)
    assert f"/{action.lower()}/" in path
    assert f"ACTION_KIND = '{action.lower()}'" in content


def test_indicator_derived_signal_mapping():
    content, path = render_template("BlocksSignal", "NewSignal", indicator="SMA")
    ast.parse(content)
    assert "/sma/" in path
    assert "INDICATOR = 'SMA'" in content
    with pytest.raises(CodeEditorError):
        render_template("BlocksSignal", "NewSignal", indicator="MissingIndicator")


@pytest.mark.parametrize(
    "format_id,extension", [("python", ".py.tpl"), ("pseudocode", ".txt.tpl")]
)
def test_export_template_formats_and_collisions(source_tree, format_id, extension):
    source = source_tree / "source.py"
    source.write_text("class Example: pass", encoding="utf-8")
    target = source_tree / ("example" + extension)
    request = ExportTemplateRequest(
        source_paths=[relative(source)],
        target_path=relative(target),
        format_id=format_id,
    )
    result = create_export_template(request)
    assert result["bytes_written"] == target.stat().st_size
    assert "Example" in target.read_text(encoding="utf-8")
    with pytest.raises(CodeEditorError):
        create_export_template(request)
    assert [
        f.format_id for f in supported_formats("app/extend/user/code_templates/python")
    ] == ["python"]


def test_real_package_job_diagnostics_and_restart(service, source_tree):
    (source_tree / "good.py").write_text("class Example: pass", encoding="utf-8")
    (source_tree / "bad.py").write_text("def invalid(:", encoding="utf-8")
    started = service.start(
        CompilationRequest(scope="package", file_path=str(source_tree))
    )
    service.manager.wait_for_job(started.job_id, timeout=15)
    result = service.get(started.job_id)
    assert result.status == "COMPLETED"
    assert result.progress == 100
    assert len(result.results) == 2
    assert sum(r["success"] for r in result.results) == 1
    restarted = CompilationService(service.manager, service.store)
    assert restarted.get().model_dump() == result.model_dump()


def test_live_cancellation_waits_for_current_import(service, source_tree, monkeypatch):
    first = source_tree / "first.py"
    first.write_text("value = 1", encoding="utf-8")
    (source_tree / "second.py").write_text("value = 2", encoding="utf-8")
    entered, release = threading.Event(), threading.Event()
    compile_file = CodeEditor.compile_file
    calls = []

    def blocked(self, path, content=None):
        calls.append(path)
        entered.set()
        assert release.wait(10)
        return compile_file(self, path, content)

    monkeypatch.setattr(CodeEditor, "compile_file", blocked)
    started = service.start(
        CompilationRequest(scope="package", file_path=str(source_tree))
    )
    try:
        assert entered.wait(10)
        with pytest.raises(CodeEditorError, match="already running"):
            service.start(CompilationRequest(file_path=str(first)))
        pending = service.cancel(started.job_id)
        assert pending.cancellation_requested
        assert pending.status not in ("CANCELLED", "COMPLETED")
    finally:
        release.set()
    service.manager.wait_for_job(started.job_id, timeout=15)
    assert service.get(started.job_id).status == "CANCELLED"
    assert len(calls) == 1


def test_orphan_snapshot_is_interrupted(service):
    service.store.write(
        "compilation:latest",
        {"job_id": "orphan", "status": "RUNNING", "progress": 20, "results": []},
    )
    assert service.get().status == "INTERRUPTED"


def test_registered_reload_removes_missing_and_failed_extensions(service, source_tree):
    path = source_tree / "registered.py"
    path.write_text("class Previous: pass", encoding="utf-8")
    assert CodeEditor().compile_file(str(path))["success"]
    path.write_text("def invalid(:", encoding="utf-8")
    job = service.start(CompilationRequest(scope="registered"))
    service.manager.wait_for_job(job.job_id, timeout=15)
    assert str(path) not in registry.blocks


def test_http_commands_live_job_and_validation(service, source_tree):
    source = source_tree / "http.py"
    source.write_text("value = 1", encoding="utf-8")
    app = create_app()
    app.state.code_editor_compilation = service
    client = TestClient(app)
    base = "/api/v1/code-editor"
    assert (
        client.get(base + "/file/info", params={"file_path": relative(source)}).json()[
            "data"
        ]["ownership"]
        == "user"
    )
    assert client.get(base + "/export-formats").status_code == 200
    assert (
        client.post(base + "/compilations", json={"scope": "wrong"}).status_code == 422
    )
    response = client.post(
        base + "/compilations",
        json={"file_path": relative(source), "content": "def invalid(:"},
    )
    assert response.status_code == 200, response.text
    job_id = response.json()["data"]["job_id"]
    service.manager.wait_for_job(job_id, timeout=15)
    result = client.get(base + "/compilations", params={"job_id": job_id}).json()[
        "data"
    ]
    assert not result["results"][0]["success"]
    assert result["results"][0]["errors"]
    assert (
        client.post(base + f"/compilations/{job_id}/cancel", json={}).status_code == 200
    )


def test_package_relative_import_and_live_registry_index(service, source_tree):
    (source_tree / "__init__.py").write_text("", encoding="utf-8")
    (source_tree / "helper.py").write_text("class Helper: pass", encoding="utf-8")
    source = source_tree / "consumer.py"
    source.write_text(
        "from .helper import Helper\nclass Consumer(Helper): pass", encoding="utf-8"
    )
    job = service.start(CompilationRequest(scope="package", file_path=str(source_tree)))
    service.manager.wait_for_job(job.job_id, timeout=15)
    assert all(result["success"] for result in service.get(job.job_id).results)
    assert CodeEditor().compile_file(
        str(source), "class UnsavedConsumer:\n    def live_member(self): pass"
    )["success"]
    symbols = catalogue.symbol_catalogue(source_tree)
    assert any(
        s.name == "UnsavedConsumer" and "live_member" in s.members for s in symbols
    )
    assert not any(s.name == "Consumer" for s in symbols)


def test_empty_registered_reload_and_unknown_cancellation(service):
    job = service.start(CompilationRequest(scope="registered"))
    service.manager.wait_for_job(job.job_id, timeout=15)
    assert service.get(job.job_id).progress == 100
    assert service.get(job.job_id).results == []
    with pytest.raises(CodeEditorError, match="not found"):
        service.cancel("unknown")


def test_corrupted_compilation_state_fails_closed(service):
    service.store.write(
        "compilation:latest", {"job_id": "corrupt", "status": "unknown", "progress": 50}
    )
    with pytest.raises(CodeEditorError, match="Invalid stored"):
        service.get()
    assert service.store.read("compilation:latest")["status"] == "unknown"


def test_duplicate_session_input_preserves_original_state(source_tree):
    source = source_tree / "session.py"
    source.write_text("keep = 1", encoding="utf-8")
    editor = AppCodeEditor()
    editor.open_file_tab(str(source))
    before = editor.init_workspace()
    with pytest.raises(CodeEditorError, match="Duplicate"):
        editor.sync_session(
            [
                {"file_path": relative(source), "content": "one"},
                {"file_path": str(source), "content": "two"},
            ],
            relative(source),
        )
    assert editor.init_workspace() == before


def test_code_types_and_path_catalogue_http(service):
    app = create_app()
    client = TestClient(app)
    base = "/api/v1/code-editor"
    types = client.get(base + "/code-types").json()["data"]
    assert len(types) == 14
    assert next(t for t in types if t["type_id"] == "BlocksOrder")["subtypes"] == [
        "Open",
        "Modify",
        "Close",
    ]
    templates = client.get(
        base + "/templates", params={"file_path": "app/extend/monte_carlo"}
    ).json()["data"]
    assert len(templates) == 2
    assert (
        client.post(
            base + "/templates/render",
            json={"template_id": "MonteCarlo", "name": "Sample", "mc_type": "invalid"},
        ).status_code
        == 422
    )


def test_editor_worker_lifecycle_is_host_owned(monkeypatch, caplog):
    import app.main as backend

    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=Mock()))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}
    app = backend.create_app(gateway)
    manager = Mock()
    caplog.set_level(logging.INFO)
    with TestClient(app):
        app.state.code_editor_jobs = manager
        app.state.code_editor_compilation = object()
    manager.shutdown.assert_called_once_with(wait=True, cancel_futures=True)
    assert not hasattr(app.state, "code_editor_jobs")
    assert not hasattr(app.state, "code_editor_compilation")
    assert "FR-host-editor-job-lifecycle: worker service released" in caplog.text


def test_path_catalogue_maps_indicator_categories_and_user_clones():
    for path in (
        "app/extend/blocks/indicators/trend/sma.py",
        "app/extend/user/blocks/indicators/trend/sma_copy.py",
    ):
        assert [item["template_id"] for item in list_templates(path)] == [
            "BlocksIndicators"
        ]
    assert [
        item["template_id"]
        for item in list_templates("app/extend/user/orders/close/example.py")
    ] == ["BlocksOrder"]


def test_indicator_catalogue_disambiguates_multiple_classes_in_one_file():
    from app.workspace.code_editor._indicator_resolver import resolve_indicator

    with tempfile.TemporaryDirectory(
        dir=EXTEND_DIR / "blocks/indicators", prefix="catalogue_"
    ) as name:
        path = Path(name) / "multiple.py"
        path.write_text(
            "from app.extend.blocks.indicators.trend.sma import SMA\nclass First(SMA): pass\nclass Second(SMA): pass\n",
            encoding="utf-8",
        )
        records = [
            r for r in catalogue.indicator_catalogue() if r.file_path == relative(path)
        ]
        assert {r.name for r in records} == {"First", "Second"}
        assert len({r.identity for r in records}) == 2
        for record in records:
            assert resolve_indicator(record.identity).__name__ == record.name

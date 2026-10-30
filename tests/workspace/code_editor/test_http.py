"""Integration tests for Code Editor FastAPI HTTP router."""

import pytest
from app.main import create_app
from fastapi.testclient import TestClient


def test_http_save_as_identity_collision_and_validation(client):
    import tempfile
    from pathlib import Path

    from app.workspace.code_editor._common import INCLUDE_DIR, PROJECT_ROOT

    with tempfile.TemporaryDirectory(dir=INCLUDE_DIR, prefix="http_save_as_") as name:
        folder = Path(name).resolve()
        assert folder.is_relative_to(INCLUDE_DIR.resolve())
        source = folder / "source.py"
        target = folder / "new.py"
        source.write_text("original = 1", encoding="utf-8")
        source_key = source.relative_to(PROJECT_ROOT).as_posix()
        target_key = target.relative_to(PROJECT_ROOT).as_posix()
        assert (
            client.post(
                "/api/v1/code-editor/tabs/open", json={"file_path": source_key}
            ).status_code
            == 200
        )
        endpoint = "/api/v1/code-editor/file/save-as"
        assert (
            client.post(
                endpoint, json={"source_path": source_key, "target_path": target_key}
            ).status_code
            == 422
        )
        response = client.post(
            endpoint,
            json={"source_path": source_key, "target_path": target_key, "content": ""},
        )
        assert response.status_code == 200
        result = response.json()["data"]
        assert result["status"] == "saved_as"
        assert result["source_path"] == source_key
        assert result["file_path"] == result["active_file"] == target_key
        assert result["bytes_written"] == 0
        assert result["tab"]["is_dirty"] is False
        assert target.read_bytes() == b""
        assert source.read_text(encoding="utf-8") == "original = 1"
        collision = client.post(
            endpoint,
            json={
                "source_path": target_key,
                "target_path": source_key,
                "content": "overwrite",
                "overwrite": True,
            },
        )
        assert collision.status_code == 409
        assert collision.json()["error"]["code"] == "conflict"
        assert source.read_text(encoding="utf-8") == "original = 1"


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("file/save-all", {"files": [{"file_path": "missing.py"}]}),
        ("session", {"tabs": [{"file_path": "missing.py"}]}),
        (
            "import-export/import",
            {"archive_path": "absent.zip", "resolution_rules": {"a.py": "invalid"}},
        ),
        ("indicator-test/run", {"indicator_name": "SMA", "bar_count": 0}),
    ],
)
def test_invalid_nested_requests_use_host_error_envelope(client, endpoint, payload):
    response = client.post("/api/v1/code-editor/" + endpoint, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "validation"
    assert body["error"]["message"] == "Invalid editor request"


def test_unexpected_and_malformed_results_are_safe_host_errors(
    client, monkeypatch, caplog
):
    from app.workspace.code_editor import http

    def fail():
        raise RuntimeError("credential-marker")

    monkeypatch.setattr(http._code_editor.editor, "init_workspace", fail)
    response = client.get("/api/v1/code-editor/init")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "internal"
    assert "credential-marker" not in response.text
    assert "credential-marker" not in caplog.text
    monkeypatch.setattr(
        http._code_editor.editor, "init_workspace", lambda: {"surprise": True}
    )
    response = client.get("/api/v1/code-editor/init")
    assert response.status_code == 503
    assert response.json()["error"]["message"] == "Invalid editor result"


def test_extra_session_fields_and_empty_save_all_are_compatible(client):
    response = client.post(
        "/api/v1/code-editor/session",
        json={"tabs": [], "active_file": None, "layout": {}},
    )
    assert response.status_code == 200
    assert response.json()["data"]["open_tabs"] == []
    response = client.post("/api/v1/code-editor/file/save-all", json={"files": []})
    assert response.json()["data"] == {"status": "saved_all", "count": 0, "files": []}


def test_every_editor_http_operation_declares_a_success_contract():
    from app.workspace.code_editor.http import router
    from fastapi.routing import APIRoute

    routes = [route for route in router.routes if isinstance(route, APIRoute)]
    assert len(routes) >= 30
    for route in routes:
        if not route.path.endswith("/mcp"):
            assert route.response_model is not None, route.path


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_http_init_and_navigator(client: TestClient):
    """Verify init workspace and navigator endpoints return successful envelopes."""
    res_init = client.get("/api/v1/code-editor/init")
    assert res_init.status_code == 200
    data = res_init.json()["data"]
    assert data["status"] == "ready"

    res_nav = client.get("/api/v1/code-editor/navigator")
    assert res_nav.status_code == 200
    nav_data = res_nav.json()["data"]
    assert "children" in nav_data


def test_http_templates_list_and_render(client: TestClient):
    """Verify templates list and render preview endpoints."""
    res = client.get("/api/v1/code-editor/templates")
    assert res.status_code == 200
    templates = res.json()["data"]
    assert len(templates) == 12

    res_render = client.post(
        "/api/v1/code-editor/templates/render",
        json={"template_id": "BlocksIndicators", "name": "SampleTest"},
    )
    assert res_render.status_code == 200
    preview = res_render.json()["data"]
    assert "class SampleTest(BaseIndicator):" in preview["content"]
    assert preview["file_path"].endswith("sample_test.py")


def test_http_indicator_test_run(client: TestClient):
    """Verify running indicator test via HTTP returns chart and table data."""
    res = client.post(
        "/api/v1/code-editor/indicator-test/run",
        json={
            "indicator_name": "SMA",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "params": {"period": 5},
            "bar_count": 50,
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "success"
    assert len(data["candlesticks"]) == 50
    assert len(data["indicator_plots"]) == 50


def test_http_errors_and_session_validation(client: TestClient):
    response = client.post(
        "/api/v1/code-editor/file/delete", json={"file_path": "app/main.py"}
    )
    assert response.status_code == 422
    response = client.post(
        "/api/v1/code-editor/search", json={"query": "[", "regex": True}
    )
    assert response.status_code == 422
    response = client.post(
        "/api/v1/code-editor/session", json={"tabs": [{"file_path": "a.py"}]}
    )
    assert response.status_code == 422


def test_http_saved_test_survives_service_restart(client: TestClient, monkeypatch):
    from app.workspace.code_editor import http
    from app.workspace.code_editor.indicator_tester import IndicatorTester

    run = client.post(
        "/api/v1/code-editor/indicator-test/run",
        json={"indicator_name": "MACD", "bar_count": 10},
    )
    result = run.json()["data"]
    assert result["status"] == "success"
    identifier = result["test_id"]
    saved = client.post(
        "/api/v1/code-editor/indicator-test/save",
        json={"test_id": identifier, "name": "MACD config"},
    )
    assert saved.json()["data"]["config_id"] == identifier
    monkeypatch.setattr(http, "_indicator_tester", IndicatorTester())
    loaded = client.get(
        "/api/v1/code-editor/indicator-test/load", params={"config_id": identifier}
    )
    assert loaded.json()["data"]["config"]["bar_count"] == 10


def test_http_mcp_discovers_and_calls_compiled_tools(client: TestClient, tmp_path):
    from app.workspace.code_editor._common import SNIPPETS_DIR
    from app.workspace.code_editor.routes import CodeEditor
    from app.workspace.code_editor.templates import render_template

    source, _ = render_template("AITools", "ReviewTool")
    # Compile the buffer without writing to the snippet repository.
    result = CodeEditor().compile_file(
        str(SNIPPETS_DIR / "ai_tools/review_tool.py"), source
    )
    assert result["success"], result
    endpoint = "/api/v1/code-editor/mcp"
    initialized = client.post(
        endpoint, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert "tools" in initialized.json()["result"]["capabilities"]
    listed = client.post(
        endpoint, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    )
    assert listed.json()["result"]["tools"][0]["name"] == "ext_review_tool"
    called = client.post(
        endpoint,
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "ext_review_tool",
                "arguments": {"target_symbol": "EURUSD"},
            },
        },
    )
    assert not called.json()["result"]["isError"]
    assert "EURUSD" in called.json()["result"]["content"][0]["text"]
    invalid = client.post(
        endpoint,
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "ext_review_tool", "arguments": {}},
        },
    )
    assert invalid.json()["result"]["isError"]

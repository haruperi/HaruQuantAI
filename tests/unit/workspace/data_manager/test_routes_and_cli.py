"""End-to-end FastAPI router tests, headless CLI validation, and AST invariant checks."""

from __future__ import annotations

import ast
from pathlib import Path

from app.cli import run_cli
from app.host.bootstrap import BootstrapConfig, create_bootstrap_app
from app.workspace.data_manager import routes
from fastapi.testclient import TestClient


def test_routes_fastapi_contracts(tmp_path: Path) -> None:
    """Test all Data Manager FastAPI endpoints return 200 and StandardResponse envelopes."""
    data_dir = tmp_path / "data"
    db_file = data_dir / "haruquantai.db"
    cfg = BootstrapConfig(
        data_dir=data_dir,
        db_path=db_file,
        headless=False,
    )
    app = create_bootstrap_app(cfg)

    with TestClient(app) as client:
        # 1. Home Dashboard
        res = client.get("/api/v1/data/home/overview")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "success"
        assert "datasets_count" in body["data"]

        # Also verify un-prefixed mount /data/home/overview
        res_raw = client.get("/data/home/overview")
        assert res_raw.status_code == 200

        res = client.get("/api/v1/data/home/datasets")
        assert res.status_code == 200
        assert isinstance(res.json()["data"], list)

        # 2. Catalogs (Seeded on startup)
        res = client.get("/api/v1/data/instruments")
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 7

        res = client.get("/api/v1/data/sessions")
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 4

        res = client.get("/api/v1/data/baskets")
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 3

        res = client.get("/api/v1/data/baskets/overview")
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 3

        res = client.get("/api/v1/data/brokers")
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 6

        # 3. Providers & Health
        res = client.get("/api/v1/data/providers")
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 7

        res = client.get("/api/v1/data/providers/dukascopy/health")
        assert res.status_code == 200
        assert res.json()["data"]["connected"] is True

        # 4. Data Import, Review, and Quality
        sample_csv = "timestamp,open,high,low,close,volume,spread\n" + "\n".join(
            f"2026-01-01 00:{i:02d}:00,1.1000,1.1005,1.0995,1.1002,150,1"
            for i in range(50)
        )
        import_res = client.post(
            "/api/v1/data/datasets/import",
            json={
                "symbol": "EURUSD",
                "timeframe": "M1",
                "source": "file",
                "csv_content": sample_csv,
            },
        )
        assert import_res.status_code == 200
        ds_id = import_res.json()["data"]["id"]

        chart_res = client.post(
            "/api/v1/data/datasets/review-chart",
            json={"dataset_id": ds_id, "limit": 5, "offset": 0},
        )
        assert chart_res.status_code == 200
        bars = chart_res.json()["data"]["bars"]
        assert len(bars) == 5
        assert "datetime" in bars[0]

        review_rows_res = client.get(f"/api/v1/data/datasets/{ds_id}/review-data")
        assert review_rows_res.status_code == 200
        assert len(review_rows_res.json()["data"]["rows"]) > 0

        qual_res = client.get(f"/api/v1/data/datasets/{ds_id}/quality-summary")
        assert qual_res.status_code == 200
        assert "quality_score" in qual_res.json()["data"]

        qual_det = client.get(f"/api/v1/data/datasets/{ds_id}/quality-details")
        assert qual_det.status_code == 200

        # 5. Transforms (Resample & Timezone Clone)
        resamp_res = client.post(
            "/api/v1/data/datasets/resample",
            json={"dataset_id": ds_id, "target_timeframe": "M5"},
        )
        assert resamp_res.status_code == 200
        assert resamp_res.json()["data"]["timeframe"] == "M5"

        clone_res = client.post(
            "/api/v1/data/datasets/clone-timezone",
            json={"dataset_id": ds_id, "shift_hours": 2, "postfix": "_EET"},
        )
        assert clone_res.status_code == 200
        assert "_EET" in clone_res.json()["data"]["id"]

        # 6. Export Formats & Export
        fmt_res = client.get("/api/v1/data/export/csv/formats")
        assert fmt_res.status_code == 200

        exp_res = client.post(
            "/api/v1/data/export",
            json={"dataset_ids": [ds_id], "format": "CSV"},
        )
        assert exp_res.status_code == 200
        assert exp_res.json()["data"]["exported_count"] == 1

        # 7. Custom Data & MQ4
        cd_res = client.get("/api/v1/data/custom-data")
        assert cd_res.status_code == 200

        mq4_res = client.post(
            "/api/v1/data/custom-data/recognize-mq4",
            json={
                "filename": "RSI_Buffer.mq4",
                "source_code": "#property indicator_buffers 1\nvoid init() { SetIndexBuffer(0, Buf); }",
            },
        )
        assert mq4_res.status_code == 200
        assert mq4_res.json()["data"]["name"] == "RSI_Buffer"

        # 8. Help & FAQs
        topics_res = client.get("/api/v1/data/help/topics")
        assert topics_res.status_code == 200
        assert len(topics_res.json()["data"]) >= 5

        faqs_res = client.get("/api/v1/data/help/faqs?query=simulation")
        assert faqs_res.status_code == 200
        assert len(faqs_res.json()["data"]) >= 1

        # 9. Logs
        logs_res = client.get("/api/v1/data/logs")
        assert logs_res.status_code == 200

    routes.main()


def test_routes_auth_enforcement(tmp_path: Path) -> None:
    """Verify Data Manager routes reject unauthenticated requests when require_auth=True."""
    data_dir = tmp_path / "auth_data"
    db_file = data_dir / "haruquantai.db"
    cfg = BootstrapConfig(
        data_dir=data_dir,
        db_path=db_file,
        headless=False,
        require_auth=True,
    )
    app = create_bootstrap_app(cfg)

    with TestClient(app) as client:
        # Unauthenticated calls should return 401 across all mounts
        res1 = client.get("/data/home/overview")
        assert res1.status_code == 401

        res2 = client.get("/api/v1/data/datasets")
        assert res2.status_code == 401

        res3 = client.post("/api/v2/data/instruments", json={"symbol": "TEST"})
        assert res3.status_code == 401

        # Now authenticate with a valid session
        runtime = getattr(app.state, "runtime", None)
        assert runtime is not None
        raw_token, _ = runtime.session_manager.create_session("operator_1", "127.0.0.1")

        auth_headers = {"Authorization": f"Bearer {raw_token}"}
        res_auth = client.get("/api/v1/data/home/overview", headers=auth_headers)
        assert res_auth.status_code == 200
        assert res_auth.json()["status"] == "success"


def test_headless_cli_data_operations(tmp_path: Path) -> None:
    """Test headless CLI data command execution across all actions."""
    data_dir = tmp_path / "cli_data"
    actions = [
        "home",
        "overview",
        "datasets",
        "instruments",
        "sessions",
        "baskets",
        "brokers",
        "providers",
        "logs",
    ]
    for act in actions:
        exit_code, output = run_cli(
            ["data", "--action", act, "--data-dir", str(data_dir), "--json"]
        )
        assert exit_code == 0, f"Action '{act}' failed with output: {output}"
        assert '"status": "success"' in output or '"command": "data"' in output

    # Test positional subcommand syntax and text mode rendering
    exit_code_pos, out_pos = run_cli(["data", "home", "--data-dir", str(data_dir)])
    assert exit_code_pos == 0
    assert "=== Data Manager Home: Live Database Overview ===" in out_pos
    assert "Saved Datasets Catalog" in out_pos


def _check_no_sqlite(tree: ast.AST, py_file: Path) -> None:
    """Verify absence of direct sqlite3 imports."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "sqlite3", (
                    f"Violation in {py_file}: Direct 'sqlite3' import is strictly forbidden."
                )
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "sqlite3", (
                f"Violation in {py_file}: Direct 'sqlite3' import is strictly forbidden."
            )


def _check_file_invariants(py_file: Path) -> None:
    """Validate invariants for an individual Data Manager Python module."""
    content = py_file.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(py_file))

    # Invariant 1: ZERO direct sqlite3 imports
    _check_no_sqlite(tree, py_file)

    # Skip docstring check for package markers
    if py_file.name in ("__init__.py",):
        return

    # Invariant 2: 5-section docstring
    docstring = ast.get_docstring(tree) or ""
    assert "Description:" in docstring, f"{py_file} missing 'Description:'"
    assert "Purpose:" in docstring, f"{py_file} missing 'Purpose:'"
    assert "Key Capabilities:" in docstring, f"{py_file} missing 'Key Capabilities:'"
    assert "Python API Usage:" in docstring, f"{py_file} missing 'Python API Usage:'"
    assert "CLI Usage:" in docstring, f"{py_file} missing 'CLI Usage:'"

    # Invariant 3: Count FR-* in docstring and verify __all__ budget
    fr_ids = [line for line in docstring.splitlines() if "- FR-DATAMGR-" in line]
    assert len(fr_ids) > 0, f"{py_file} declares zero FR-DATAMGR-* capabilities."

    all_node = None
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    all_node = stmt.value
                    break
    assert all_node is not None, f"{py_file} missing __all__ declaration."
    if isinstance(all_node, ast.List):
        assert len(all_node.elts) <= len(fr_ids), (
            f"{py_file} has {len(all_node.elts)} exports in __all__, "
            f"exceeding {len(fr_ids)} FR capabilities."
        )

    # Invariant 4: logger = get_logger(__name__)
    assert "logger = get_logger(__name__)" in content, (
        f"{py_file} must initialize logger using 'get_logger(__name__)'"
    )

    # Invariant 5: def main() -> None: or if __name__ == "__main__":
    has_main = any(
        isinstance(node, ast.FunctionDef) and node.name == "main" for node in tree.body
    )
    has_if_main = any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        for node in tree.body
    )
    assert has_main or has_if_main, (
        f"{py_file} missing entrypoint ('def main() -> None:' or 'if __name__ == \"__main__\":')"
    )


def test_ast_architectural_invariants() -> None:
    """Verify clean-room architectural invariants across app/workspace/data_manager/."""
    pkg_dir = Path("app/workspace/data_manager")
    py_files = list(pkg_dir.rglob("*.py"))
    assert len(py_files) >= 11, f"Expected >= 11 Python files, found {len(py_files)}"

    for py_file in py_files:
        _check_file_invariants(py_file)

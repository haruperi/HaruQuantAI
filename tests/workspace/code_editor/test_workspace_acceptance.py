"""Full 43-command workspace acceptance and lifecycle verification test suite."""

from __future__ import annotations

import hashlib
import shutil
import time
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from app.include.blocks.price import BarPrice
from app.main import create_app
from app.workspace.code_editor._common import INCLUDE_DIR, PROJECT_ROOT
from app.workspace.code_editor.command_models import (
    SuiteConfigModel,
    SuiteTestCaseModel,
)
from app.workspace.code_editor.indicator_suite import suite_config_to_xml
from fastapi.testclient import TestClient


@pytest.fixture
def acceptance_env(isolated_editor, tmp_path: Path):
    sandbox = (INCLUDE_DIR / f"accept_{uuid.uuid4().hex[:8]}").resolve()
    sandbox.mkdir(parents=True, exist_ok=True)
    tests_dir = tmp_path / "suite_tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    app = create_app()
    app.state.persistence = isolated_editor
    app.state.code_editor_tests_dir = tests_dir

    def _fake_loader(symbol: str, timeframe: str, count: int):
        closes = np.linspace(1.1000, 1.1500, count)
        bars = BarPrice(
            open_data=closes - 0.0005,
            high_data=closes + 0.0010,
            low_data=closes - 0.0010,
            close_data=closes,
            volume_data=np.full(count, 500.0),
        )
        return bars, [1704067200 + i * 3600 for i in range(count)]

    app.state.code_editor_history_loader = _fake_loader
    try:
        yield app, sandbox, tests_dir
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_all_43_donor_commands_end_to_end(acceptance_env, tmp_path: Path):
    """Verify CE-01..CE-26, IE-01..IE-08, and IT-01..IT-09 end-to-end."""
    app, sandbox, tests_dir = acceptance_env
    rel_sandbox = sandbox.relative_to(PROJECT_ROOT).as_posix()

    with TestClient(app) as client:
        # CE-01..CE-08: Workspace init, navigator, tabs, code-types, catalogues, formats
        r_init = client.get("/api/v1/code-editor/init")
        assert r_init.status_code == 200
        assert r_init.json()["status"] == "success"

        r_nav = client.get(
            "/api/v1/code-editor/navigator",
            params={"ownership": "all", "filter_text": ""},
        )
        assert r_nav.status_code == 200

        r_types = client.get("/api/v1/code-editor/code-types")
        assert r_types.status_code == 200
        assert len(r_types.json()["data"]) >= 14

        r_syms = client.get("/api/v1/code-editor/catalogue/symbols")
        assert r_syms.status_code == 200
        assert len(r_syms.json()["data"]) > 50

        r_inds = client.get("/api/v1/code-editor/catalogue/indicators")
        assert r_inds.status_code == 200
        assert len(r_inds.json()["data"]) >= 80

        r_tpls = client.get("/api/v1/code-editor/templates")
        assert r_tpls.status_code == 200

        r_fmts = client.get("/api/v1/code-editor/export-formats")
        assert r_fmts.status_code == 200

        # CE-09..CE-18: File CRUD, new-dir, clone, save, save-as, save-all, reload, rename, delete
        new_dir_rel = f"{rel_sandbox}/subpkg"
        assert (
            client.post(
                "/api/v1/code-editor/file/new-dir",
                json={"dir_path": new_dir_rel},
            ).status_code
            == 200
        )

        f1_rel = f"{new_dir_rel}/alpha.py"
        assert (
            client.post(
                "/api/v1/code-editor/file/new",
                json={"file_path": f1_rel, "content": "class Alpha:\n    pass\n"},
            ).status_code
            == 200
        )

        assert (
            client.get(
                "/api/v1/code-editor/file/info", params={"file_path": f1_rel}
            ).json()["data"]["ownership"]
            == "user"
        )

        assert (
            client.post(
                "/api/v1/code-editor/tabs/open",
                json={"file_path": f1_rel, "mode": "python"},
            ).status_code
            == 200
        )
        assert len(client.get("/api/v1/code-editor/tabs").json()["data"]) >= 1

        assert (
            client.post(
                "/api/v1/code-editor/file/save",
                json={"file_path": f1_rel, "content": "class Alpha:\n    v = 1\n"},
            ).status_code
            == 200
        )

        f2_rel = f"{new_dir_rel}/alpha_copy.py"
        assert (
            client.post(
                "/api/v1/code-editor/file/save-as",
                json={
                    "source_path": f1_rel,
                    "target_path": f2_rel,
                    "content": "class AlphaCopy:\n    v = 2\n",
                },
            ).status_code
            == 200
        )

        assert (
            client.post(
                "/api/v1/code-editor/file/save-all",
                json={
                    "files": [
                        {
                            "file_path": f2_rel,
                            "content": "class AlphaCopy:\n    v = 3\n",
                        }
                    ]
                },
            ).status_code
            == 200
        )

        assert (
            client.post(
                "/api/v1/code-editor/file/reload",
                json={"file_path": f2_rel, "discard_dirty": True},
            ).status_code
            == 200
        )

        f3_rel = f"{new_dir_rel}/alpha_cloned.py"
        assert (
            client.post(
                "/api/v1/code-editor/file/clone",
                json={"source_path": f1_rel, "target_path": f3_rel},
            ).status_code
            == 200
        )

        f3_renamed = f"{new_dir_rel}/alpha_renamed.py"
        assert (
            client.post(
                "/api/v1/code-editor/file/rename",
                json={"old_path": f3_rel, "new_path": f3_renamed},
            ).status_code
            == 200
        )

        assert (
            client.post(
                "/api/v1/code-editor/file/delete",
                json={"file_path": f3_renamed},
            ).status_code
            == 200
        )

        # CE-19..CE-26: Search, repair imports, export template, compile, compilations job
        r_search = client.post(
            "/api/v1/code-editor/search",
            json={
                "query": "Alpha",
                "case_sensitive": True,
                "regex": False,
                "whole_word": True,
                "search_dir": new_dir_rel,
            },
        )
        assert r_search.status_code == 200
        assert len(r_search.json()["data"]) >= 1

        r_repair = client.post(
            "/api/v1/code-editor/imports/repair",
            json={
                "file_path": f1_rel,
                "content": "x = BaseIndicator\n",
                "selections": {},
            },
        )
        assert r_repair.status_code == 200

        tpl_target = f"{new_dir_rel}/export_authoring.py.tpl"
        r_exp_tpl = client.post(
            "/api/v1/code-editor/export-templates",
            json={
                "source_paths": [f1_rel],
                "target_path": tpl_target,
                "format_id": "python",
            },
        )
        assert r_exp_tpl.status_code == 200

        r_comp = client.post(
            "/api/v1/code-editor/compilations",
            json={"scope": "file", "file_path": f1_rel},
        )
        assert r_comp.status_code == 200
        comp_job_id = r_comp.json()["data"]["job_id"]
        for _ in range(30):
            snap = client.get(
                "/api/v1/code-editor/compilations", params={"job_id": comp_job_id}
            ).json()["data"]
            if snap["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
                break
            time.sleep(0.03)

        # IE-01..IE-08: Exportable list, export, inspect, interactive import session & actions
        assert (
            client.get(
                "/api/v1/code-editor/import-export/list",
                params={"filter_text": "alpha"},
            ).status_code
            == 200
        )

        pack_path = tmp_path / "exported_pack.sxp"
        r_export = client.post(
            "/api/v1/code-editor/import-export/export",
            json={
                "file_paths": [f1_rel, f2_rel],
                "archive_path": str(pack_path),
                "metadata": {"name": "AcceptancePack"},
            },
        )
        assert r_export.status_code == 200

        assert (
            client.post(
                "/api/v1/code-editor/import-export/inspect",
                json={"archive_path": str(pack_path)},
            ).status_code
            == 200
        )

        r_sess = client.post(
            "/api/v1/code-editor/import-export/session/start",
            json={"archive_paths": [str(pack_path)]},
        )
        assert r_sess.status_code == 200
        sess_id = r_sess.json()["data"]["session_id"]
        assert r_sess.json()["data"]["status"] == "AWAITING_DECISION"

        r_skip = client.post(
            f"/api/v1/code-editor/import-export/session/{sess_id}/skip"
        )
        assert r_skip.status_code == 200
        assert r_skip.json()["data"]["status"] == "AWAITING_DECISION"

        r_ovw_all = client.post(
            f"/api/v1/code-editor/import-export/session/{sess_id}/overwrite-always"
        )
        assert r_ovw_all.status_code == 200
        assert r_ovw_all.json()["data"]["status"] == "COMPLETED"

        # IT-01..IT-09: Indicator suite, test distribution, and calibration
        assert (
            client.get("/api/v1/code-editor/indicator-suite/indicators").status_code
            == 200
        )
        assert (
            client.post(
                "/api/v1/code-editor/indicator-suite/config/new",
                json={
                    "indicators": ["ATR"],
                    "engine": "MetaTrader4",
                    "bars_to_reserve": 300,
                },
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/v1/code-editor/indicator-suite/config/add-tests",
                json={"indicators": ["RSI"], "allow_duplicates": False},
            ).status_code
            == 200
        )
        r_cfg = client.get("/api/v1/code-editor/indicator-suite/config")
        assert r_cfg.status_code == 200
        assert len(r_cfg.json()["data"]["config"]["tests"]) == 2

        assert (
            client.post(
                "/api/v1/code-editor/indicator-suite/config/save",
                json={"xml_content": r_cfg.json()["data"]["xml_content"]},
            ).status_code
            == 200
        )

        r_suite_start = client.post(
            "/api/v1/code-editor/indicator-suite/start",
            json={"selected_only": True},
        )
        assert r_suite_start.status_code == 200
        suite_job = r_suite_start.json()["data"]["job_id"]
        for _ in range(40):
            st = client.get(
                "/api/v1/code-editor/indicator-suite/status",
                params={"job_id": suite_job},
            ).json()["data"]
            if st["status"] in {"COMPLETED", "STOPPED", "FAILED"}:
                break
            time.sleep(0.03)
        assert (
            client.post(
                "/api/v1/code-editor/indicator-suite/stop",
                params={"job_id": suite_job},
            ).status_code
            == 200
        )

        # IT-08: Test distribution
        bundle_buf = BytesIO()
        with zipfile.ZipFile(bundle_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "IndicatorTester.xml",
                suite_config_to_xml(
                    SuiteConfigModel(
                        engine="MetaTrader4",
                        bars_to_reserve=300,
                        tests=[
                            SuiteTestCaseModel(
                                test_id="t1",
                                indicator="ATR",
                                parameters="14",
                                file_name="ATR_14.csv",
                            )
                        ],
                    )
                ),
            )
            zf.writestr(
                "MetaTrader4/ATR_14.csv",
                "2024.01.01 00:00:00;1.1;1.2;1.0;1.15;100;0.01\n",
            )
        bundle_file = tmp_path / "dist_bundle.zip"
        bundle_file.write_bytes(bundle_buf.getvalue())
        sha = hashlib.sha256(bundle_buf.getvalue()).hexdigest()
        r_dist = client.post(
            "/api/v1/code-editor/indicator-suite/download-tests",
            json={"archive_path": str(bundle_file), "expected_sha256": sha},
        )
        assert r_dist.status_code == 200
        assert r_dist.json()["data"]["completed"] is True
        assert (
            client.get(
                "/api/v1/code-editor/indicator-suite/download-status"
            ).status_code
            == 200
        )

        # IT-09: Calibration
        r_cal = client.post(
            "/api/v1/code-editor/indicator-suite/calibrate",
            json={
                "project_name": "AcceptProj",
                "symbols": ["EURUSD"],
                "timeframes": ["H1"],
                "engine": "MetaTrader4",
                "indicators": ["ATR"],
                "bars_count": 60,
            },
        )
        assert r_cal.status_code == 200
        assert r_cal.json()["data"]["calibrated_count"] == 1

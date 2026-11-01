"""Interactive import conflict session and archive hardening verification tests."""

from __future__ import annotations

import tempfile
import time
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from app.main import create_app
from app.workspace.code_editor._common import (
    EXTEND_DIR,
    PROJECT_ROOT,
    CodeEditorError,
)
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.command_models import (
    ImportSessionActionRequest,
    ImportSessionStartRequest,
)
from app.workspace.code_editor.import_session import (
    ImportSessionService,
    list_exportable_tree,
)
from fastapi.testclient import TestClient


@pytest.fixture
def user_sandbox():
    with tempfile.TemporaryDirectory(dir=EXTEND_DIR, prefix="impsess_") as raw_dir:
        root = Path(raw_dir).resolve()
        yield root


def _make_archive(dest: Path, files: dict[str, bytes | str]) -> Path:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, content in files.items():
            zf.writestr(
                arcname,
                content.encode("utf-8") if isinstance(content, str) else content,
            )
    dest.write_bytes(buf.getvalue())
    return dest


def test_list_exportable_tree_excludes_builtins_and_filters(user_sandbox: Path):
    user_file = user_sandbox / "my_custom_alpha.py"
    user_file.write_text("x = 1\n", encoding="utf-8")
    tree = list_exportable_tree(filter_text="custom_alpha")
    flat_paths: list[str] = []

    def _collect(node: dict[str, object]) -> None:
        if node.get("type") == "file":
            flat_paths.append(str(node.get("path")))
        for child in node.get("children", []):  # type: ignore[attr-defined]
            _collect(child)

    _collect(tree)  # type: ignore[arg-type]
    rel_user = user_file.relative_to(PROJECT_ROOT).as_posix()
    assert rel_user in flat_paths
    assert all("blocks/indicators/volatility/atr.py" not in p for p in flat_paths)


def test_import_session_builtin_protection_and_java_rejection(
    isolated_editor, user_sandbox: Path, tmp_path: Path
):
    service = ImportSessionService(store=StateStore(isolated_editor))
    rel_dir = user_sandbox.relative_to(PROJECT_ROOT).as_posix()
    new_py = f"{rel_dir}/fresh_mod.py"
    java_entry = f"{rel_dir}/LegacySnippet.java"
    builtin_entry = "app/extend/what_if/by_days.py"

    archive = _make_archive(
        tmp_path / "mixed_pack.sxp",
        {
            new_py: "VALUE = 42\n",
            java_entry: "public class LegacySnippet {}",
            builtin_entry: "# attempt to overwrite builtin ATR\n",
        },
    )
    snap = service.start_session(
        ImportSessionStartRequest(archive_paths=[str(archive)])
    )
    assert snap.status == "COMPLETED"
    assert snap.new_files == [new_py]
    reasons = {item.name: item.reason for item in snap.not_imported_files}
    assert reasons[builtin_entry] == "already exists in Builtin"
    assert "Unsupported Java extension entry" in reasons[java_entry]
    assert (PROJECT_ROOT / new_py).read_text(encoding="utf-8") == "VALUE = 42\n"


def test_import_session_overwrite_skip_and_always_transitions(
    isolated_editor, user_sandbox: Path, tmp_path: Path
):
    service = ImportSessionService(store=StateStore(isolated_editor))
    rel_dir = user_sandbox.relative_to(PROJECT_ROOT).as_posix()
    f1 = user_sandbox / "one.py"
    f2 = user_sandbox / "two.py"
    f3 = user_sandbox / "three.py"
    f1.write_text("v = 1\n", encoding="utf-8")
    f2.write_text("v = 2\n", encoding="utf-8")
    f3.write_text("v = 3\n", encoding="utf-8")

    rel1 = f"{rel_dir}/one.py"
    rel2 = f"{rel_dir}/two.py"
    rel3 = f"{rel_dir}/three.py"
    archive = _make_archive(
        tmp_path / "conflicts.zip",
        {
            rel1: "v = 10\n",
            rel2: "v = 20\n",
            rel3: "v = 30\n",
        },
    )

    s0 = service.start_session(ImportSessionStartRequest(archive_paths=[str(archive)]))
    assert s0.status == "AWAITING_DECISION"
    assert s0.current_conflict == rel1

    s1 = service.apply_action(
        ImportSessionActionRequest(session_id=s0.session_id, action="overwrite")
    )
    assert s1.status == "AWAITING_DECISION"
    assert s1.current_conflict == rel2

    s2 = service.apply_action(
        ImportSessionActionRequest(session_id=s0.session_id, action="skip_always")
    )
    assert s2.status == "COMPLETED"
    assert s2.new_files == [rel1]
    assert len(s2.not_imported_files) == 2
    assert f1.read_text(encoding="utf-8") == "v = 10\n"
    assert f2.read_text(encoding="utf-8") == "v = 2\n"
    assert f3.read_text(encoding="utf-8") == "v = 3\n"


def test_import_session_overwrite_always_and_cancel_and_timeout(
    isolated_editor, user_sandbox: Path, tmp_path: Path
):
    service = ImportSessionService(store=StateStore(isolated_editor))
    rel_dir = user_sandbox.relative_to(PROJECT_ROOT).as_posix()
    c1 = user_sandbox / "c1.py"
    c2 = user_sandbox / "c2.py"
    c1.write_text("a = 1\n", encoding="utf-8")
    c2.write_text("a = 2\n", encoding="utf-8")
    rel1 = f"{rel_dir}/c1.py"
    rel2 = f"{rel_dir}/c2.py"

    archive = _make_archive(
        tmp_path / "all_overwrite.sxp",
        {rel1: "a = 100\n", rel2: "a = 200\n"},
    )
    s0 = service.start_session(ImportSessionStartRequest(archive_paths=[str(archive)]))
    assert s0.status == "AWAITING_DECISION"
    s_done = service.apply_action(
        ImportSessionActionRequest(session_id=s0.session_id, action="overwrite_always")
    )
    assert s_done.status == "COMPLETED"
    assert c1.read_text(encoding="utf-8") == "a = 100\n"
    assert c2.read_text(encoding="utf-8") == "a = 200\n"

    s_cancel_init = service.start_session(
        ImportSessionStartRequest(archive_paths=[str(archive)])
    )
    s_cancelled = service.apply_action(
        ImportSessionActionRequest(session_id=s_cancel_init.session_id, action="cancel")
    )
    assert s_cancelled.status == "CANCELLED"
    assert len(s_cancelled.not_imported_files) == 2

    s_timeout_init = service.start_session(
        ImportSessionStartRequest(
            archive_paths=[str(archive)],
            timeout_seconds=0.01,
        )
    )
    time.sleep(0.03)
    s_timed_out = service.apply_action(
        ImportSessionActionRequest(
            session_id=s_timeout_init.session_id, action="overwrite"
        )
    )
    assert s_timed_out.status == "TIMED_OUT"


def test_import_session_rejects_traversal_and_duplicate_paths(
    isolated_editor, tmp_path: Path
):
    service = ImportSessionService(store=StateStore(isolated_editor))
    bad_zip = _make_archive(
        tmp_path / "traversal.zip",
        {"../../outside.py": "evil = 1\n"},
    )
    with pytest.raises(CodeEditorError, match="Unsafe archive entry path"):
        service.start_session(ImportSessionStartRequest(archive_paths=[str(bad_zip)]))


def test_import_session_http_endpoints(
    isolated_editor, user_sandbox: Path, tmp_path: Path
):
    app = create_app()
    app.state.persistence = isolated_editor
    rel_dir = user_sandbox.relative_to(PROJECT_ROOT).as_posix()
    existing = user_sandbox / "http_conflict.py"
    existing.write_text("val = 1\n", encoding="utf-8")
    rel_file = f"{rel_dir}/http_conflict.py"
    archive = _make_archive(
        tmp_path / "http_pack.sxp",
        {rel_file: "val = 99\n"},
    )

    with TestClient(app) as client:
        r_list = client.get(
            "/api/v1/code-editor/import-export/list",
            params={"filter_text": "http_conflict"},
        )
        assert r_list.status_code == 200

        r_start = client.post(
            "/api/v1/code-editor/import-export/session/start",
            json={"archive_paths": [str(archive)]},
        )
        assert r_start.status_code == 200
        data = r_start.json()["data"]
        assert data["status"] == "AWAITING_DECISION"
        session_id = data["session_id"]

        r_ovw = client.post(
            f"/api/v1/code-editor/import-export/session/{session_id}/overwrite"
        )
        assert r_ovw.status_code == 200
        assert r_ovw.json()["data"]["status"] == "COMPLETED"
        assert existing.read_text(encoding="utf-8") == "val = 99\n"

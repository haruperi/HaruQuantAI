"""Verify original local guides through the public welcome contract.

Description:
    Confirms bundled help remains complete and malformed summaries stay hidden.
Purpose:
    FEAT-HOME-DASHBOARD: Offline guide and summary qualification.
Key Capabilities:
    - FR-HOME-INDEX: Verify content and structured completion logs.
    - FR-HOME-RECENT: Verify malformed metadata warnings.
Python API Usage:
    pytest.main(["tests/unit/workspace/home/test_content.py", "--no-cov"])
CLI Usage:
    uv run pytest tests/unit/workspace/home/test_content.py --no-cov
"""

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from app.host.persistence import HostPersistence
from app.host.transport import ServletConstants
from app.workspace.home import Home
from app.workspace.home._releases import ReleaseFeed


def test_local_guides_match_shared_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "content.db")
    caplog.set_level(logging.INFO)
    content = Home(Mock(spec=ServletConstants), ReleaseFeed(None)).index()
    assert len(content["tutorials"]) == 3
    assert all(item["body"] for item in content["help"])
    path = (
        Path(__file__).resolve().parents[4] / "ui/app/workspace/Home/homeContent.json"
    )
    assert content["actions"] == json.loads(path.read_text())["actions"]
    assert any(r.__dict__.get("fr_id") == "FR-HOME-INDEX" for r in caplog.records)


@pytest.mark.parametrize(
    "patch",
    [{"workspace": "trading"}, {"name": " "}, {"name": 12}, {"workspace": None}],
)
def test_malformed_project_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, patch: dict[str, Any]
) -> None:
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "content.db")
    row = {
        "entity_id": "example",
        "payload": json.dumps({"name": "Project", "workspace": "projects", **patch}),
        "updated_at_utc": "2026-10-21T00:00:00Z",
    }
    monkeypatch.setattr(HostPersistence, "read_records", Mock(return_value=[row]))
    assert (
        Home(Mock(spec=ServletConstants), ReleaseFeed(None)).get_recent_projects() == []
    )

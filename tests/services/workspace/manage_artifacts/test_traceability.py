from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path

import pytest

from app.contracts.workspace.artifacts import DownloadGrant
from app.services.workspace.manage_artifacts.manage_artifacts import _safe_path


def test_path_escape_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ARTIFACT_PATH_ESCAPE"):
        _safe_path(tmp_path, "../../secret")


def test_grant_fixture_is_finite() -> None:
    content = b"fixture"
    grant = DownloadGrant("g", "a", "acct", "principal", datetime.now(timezone.utc)+timedelta(minutes=1), hashlib.sha256(content).hexdigest())
    assert grant.expires_at.tzinfo is not None

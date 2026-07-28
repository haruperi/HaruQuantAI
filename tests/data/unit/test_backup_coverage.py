"""Unit tests for app/services/data/persistence/backup.py to reach >80% coverage."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.services.data.contracts import DataError
from app.services.data.persistence.backup import (
    _commit_directory,
    _commit_restore,
    _license_retention_days,
    _load_manifest,
    _purge_expired,
    _require,
    _target_files,
    enforce_retention_policy,
    restore_from_backup,
)
from app.services.data.persistence.contracts import BackupTarget

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def test_require_helper() -> None:
    """Test _require raises DataError when condition is False."""
    _require(True, "INVALID_INPUT", _REQ_ID, "test_op")
    with pytest.raises(DataError) as exc_info:
        _require(False, "INVALID_INPUT", _REQ_ID, "test_op")
    assert exc_info.value.code == "INVALID_INPUT"


def test_target_files_empty_targets() -> None:
    """Test _target_files raises DB_WRITE_FAILED for empty targets tuple."""
    with pytest.raises(DataError) as exc_info:
        _target_files((), Path("artifacts/data"), _REQ_ID)
    assert exc_info.value.code == "DB_WRITE_FAILED"


def test_target_files_nonexistent_target() -> None:
    """Test _target_files raises DataError for non-existent target path."""
    target = BackupTarget(
        relative_path=Path("raw/nonexistent_file.csv"),
        schema_version="v1",
        normalization_version="v1",
    )
    with pytest.raises(DataError):
        _target_files((target,), Path("artifacts/data"), _REQ_ID)


def test_commit_directory_permission_error_retry() -> None:
    """Test _commit_directory retry mechanism raising PermissionError on max attempts."""
    mock_staging = MagicMock()
    mock_staging.replace.side_effect = PermissionError("Access denied")
    mock_dest = MagicMock()

    with patch("time.sleep"), pytest.raises(PermissionError):
        _commit_directory(mock_staging, mock_dest)


def test_load_manifest_invalid_manifest_id() -> None:
    """Test _load_manifest raises DATA_NOT_FOUND for invalid or blank manifest_id."""
    with pytest.raises(DataError) as exc_info:
        _load_manifest("", _REQ_ID)
    assert exc_info.value.code == "DATA_NOT_FOUND"

    with pytest.raises(DataError) as exc_info:
        _load_manifest("nonexistent_id_123456789", _REQ_ID)
    assert exc_info.value.code == "DATA_NOT_FOUND"


def test_restore_from_backup_nonexistent_manifest() -> None:
    """Test restore_from_backup raises DATA_NOT_FOUND for non-existent manifest_id."""
    response = restore_from_backup("nonexistent_manifest_id")
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "DATA_NOT_FOUND"


def test_license_retention_days_invalid_manifest() -> None:
    """Test _license_retention_days raises LICENSE_RESTRICTION when manifest missing/invalid."""
    mock_path = MagicMock()
    mock_manifest_path = MagicMock()
    mock_manifest_path.exists.return_value = True
    mock_manifest_path.read_text.return_value = "{invalid_json"
    mock_path.with_suffix.return_value = mock_manifest_path

    with pytest.raises(DataError) as exc_info:
        _license_retention_days(mock_path, _REQ_ID)
    assert exc_info.value.code == "LICENSE_RESTRICTION"


def test_enforce_retention_policy_invalid_age() -> None:
    """Test enforce_retention_policy raises DataError when max_age_days <= 0."""
    response = enforce_retention_policy("mt5", max_age_days=0)
    assert response.status == "error"
    assert response.error is not None


def test_enforce_retention_policy_nonexistent_dataset() -> None:
    """Test enforce_retention_policy raises DataError for nonexistent dataset."""
    response = enforce_retention_policy("nonexistent_dataset_12345", max_age_days=30)
    assert response.status == "error"
    assert response.error is not None


def test_commit_restore_rollback_on_error() -> None:
    """Test _commit_restore triggers rollback when error occurs during restore."""
    prepared = [("entry", Path("target.csv"), Path("stage.csv"), Path("rollback.csv"))]
    with (
        patch("app.services.data.persistence.backup._acquire_write_lock_raw"),
        patch(
            "app.services.data.persistence.backup._stage_restore",
            side_effect=RuntimeError("Stage failed"),
        ),
    ):
        with pytest.raises(DataError) as exc_info:
            _commit_restore("man-123", prepared, Path("dir"), _REQ_ID, _NOW)
        assert exc_info.value.code == "DB_WRITE_FAILED"


def test_purge_expired_rollback_on_error() -> None:
    """Test _purge_expired triggers _rollback_retention when error occurs."""
    mock_root = MagicMock()
    mock_root.name = "test_ds"
    mock_root.parent = Path("artifacts/data")

    with (
        patch("app.services.data.persistence.backup._acquire_write_lock_raw"),
        patch(
            "app.services.data.persistence.backup._audit",
            side_effect=RuntimeError("Audit failed"),
        ),
    ):
        with pytest.raises(DataError) as exc_info:
            _purge_expired(
                mock_root,
                [Path("artifacts/data/file1.csv")],
                "test_ds",
                _REQ_ID,
                _NOW,
            )
        assert exc_info.value.code == "DB_WRITE_FAILED"

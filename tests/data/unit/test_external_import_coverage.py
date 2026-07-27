"""
Unit tests for app/services/data/persistence/external_import.py to reach >80% coverage.
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import ColumnMapping, ExternalImportRequest
from app.services.data.persistence.external_import import (
    _decimal,
    _read_frame,
    _require_columns,
    _resolve_source_path,
    describe_import_dialects,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def _make_import_req(**kwargs) -> ExternalImportRequest:
    mapping = ColumnMapping(
        timestamp="time",
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
    )
    defaults = {
        "relative_path": Path("raw/test.csv"),
        "destination_path": Path("storage/test.parquet"),
        "source_id": "external",
        "symbol": "EURUSD",
        "data_kind": "bars",
        "timeframe": "M1",
        "format": "csv",
        "dialect": "standard",
        "mapping": mapping,
        "workflow_context": "research",
        "precision_policy": "decimal_string",
        "price_unit": "USD",
        "volume_unit": "units",
        "request_id": _REQ_ID,
    }
    defaults.update(kwargs)
    return ExternalImportRequest(**defaults)


def test_describe_import_dialects() -> None:
    """Test describe_import_dialects returns non-empty dict."""
    dialects = describe_import_dialects()
    assert "standard" in dialects


def test_resolve_source_path_missing_data_dir() -> None:
    """Test _resolve_source_path raises DB_CONNECTION_ERROR when DATA_DIR is None."""
    req = _make_import_req()
    mock_settings = MagicMock()
    mock_settings.data_dir = None

    with patch(
        "app.services.data.persistence.external_import.get_data_settings",
        return_value=mock_settings,
    ):
        with pytest.raises(DataError) as exc_info:
            _resolve_source_path(req)
        assert exc_info.value.code == "DB_CONNECTION_ERROR"


def test_resolve_source_path_missing_file() -> None:
    """Test _resolve_source_path raises FILE_CORRUPTED when file does not exist."""
    req = _make_import_req(relative_path=Path("raw/nonexistent_file_123.csv"))
    mock_settings = MagicMock()
    mock_settings.data_dir = Path("artifacts/data")

    with patch(
        "app.services.data.persistence.external_import.get_data_settings",
        return_value=mock_settings,
    ):
        with pytest.raises(DataError) as exc_info:
            _resolve_source_path(req)
        assert exc_info.value.code == "FILE_CORRUPTED"


def test_read_frame_decode_failure() -> None:
    """Test _read_frame raises FILE_CORRUPTED on pd decoding failure."""
    req = _make_import_req()
    with patch("pandas.read_csv", side_effect=ValueError("Invalid csv")):
        with pytest.raises(DataError) as exc_info:
            _read_frame(Path("dummy.csv"), req)
        assert exc_info.value.code == "FILE_CORRUPTED"


def test_require_columns_missing() -> None:
    """Test _require_columns raises VALIDATION_FAILED when columns are missing."""
    req = _make_import_req()
    mock_df = MagicMock()
    mock_df.columns = ["time", "open"]  # missing high, low, close, volume

    with pytest.raises(DataError) as exc_info:
        _require_columns(mock_df, req)
    assert exc_info.value.code == "VALIDATION_FAILED"


def test_decimal_invalid() -> None:
    """Test _decimal raises DATA_QUALITY_FAILED for non-numeric value."""
    with pytest.raises(DataError) as exc_info:
        _decimal("not_a_number", "field", _REQ_ID)
    assert exc_info.value.code == "DATA_QUALITY_FAILED"

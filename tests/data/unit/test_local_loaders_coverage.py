"""Unit tests for local_datasets/csv_loader.py and parquet_loader.py to reach 100% coverage."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.local_datasets.csv_loader import load_csv
from app.services.data.local_datasets.parquet_loader import load_parquet


def test_load_csv() -> None:
    """Test load_csv delegates to _load_local_dataset_raw."""
    mock_ds = MagicMock()
    with patch(
        "app.services.data.local_datasets.csv_loader._load_local_dataset_raw",
        return_value=mock_ds,
    ):
        response = load_csv("raw/test.csv")
    assert response.status == "success"
    assert (
        unwrap_data_response(
            response,
            operation="data.local_datasets.load_csv",
            request_id=response.metadata.request_id,
        )
        == mock_ds
    )


def test_load_parquet() -> None:
    """Test load_parquet delegates to _load_local_dataset_raw."""
    mock_ds = MagicMock()
    with patch(
        "app.services.data.local_datasets.parquet_loader._load_local_dataset_raw",
        return_value=mock_ds,
    ):
        response = load_parquet(Path("storage/test.parquet"))
    assert response.status == "success"
    assert (
        unwrap_data_response(
            response,
            operation="data.local_datasets.load_parquet",
            request_id=response.metadata.request_id,
        )
        == mock_ds
    )

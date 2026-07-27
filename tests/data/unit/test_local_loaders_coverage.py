"""Unit tests for local_datasets/csv_loader.py and parquet_loader.py to reach 100% coverage."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.data.local_datasets.csv_loader import load_csv
from app.services.data.local_datasets.parquet_loader import load_parquet


def test_load_csv() -> None:
    """Test load_csv delegates to load_local_dataset."""
    mock_ds = MagicMock()
    with patch(
        "app.services.data.local_datasets.csv_loader.load_local_dataset",
        return_value=mock_ds,
    ):
        res = load_csv("raw/test.csv")
        assert res == mock_ds


def test_load_parquet() -> None:
    """Test load_parquet delegates to load_local_dataset."""
    mock_ds = MagicMock()
    with patch(
        "app.services.data.local_datasets.parquet_loader.load_local_dataset",
        return_value=mock_ds,
    ):
        res = load_parquet(Path("storage/test.parquet"))
        assert res == mock_ds

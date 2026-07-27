"""Unit tests for local dataset manifest verification boundary."""

from unittest.mock import MagicMock, patch

from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.local_datasets.manifest import verify_dataset_manifest


def test_verify_dataset_manifest_delegates_to_load_dataset() -> None:
    """Verify verify_dataset_manifest delegates to load_dataset."""
    request = MagicMock(spec=DatasetLoadRequest)
    expected_dataset = MagicMock()
    with patch(
        "app.services.data.local_datasets.manifest.load_dataset",
        return_value=expected_dataset,
    ) as mock_load:
        result = verify_dataset_manifest(request)
        mock_load.assert_called_once_with(request)
        assert result is expected_dataset

"""Dataset-manifest verification boundary."""

from typing import TYPE_CHECKING

from app.services.data.persistence.dataset_writer import _load_dataset_raw

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset
    from app.services.data.local_datasets.contracts import DatasetLoadRequest


def verify_dataset_manifest(request: DatasetLoadRequest) -> MarketDataset:
    """Verify a dataset manifest and return its canonical dataset."""
    return _load_dataset_raw(request)


__all__ = ["verify_dataset_manifest"]

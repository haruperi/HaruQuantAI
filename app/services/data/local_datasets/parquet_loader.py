"""Focused Parquet dataset loading through the governed local loader."""

from pathlib import Path
from typing import TYPE_CHECKING

from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.persistence.dataset_writer import load_local_dataset
from app.utils import generate_id, logger

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset


def load_parquet(path: Path | str) -> MarketDataset:
    """Load one manifest-backed Parquet dataset.

    Args:
        path: Approved-root-relative Parquet artifact path.

    Returns:
        The normalized canonical market dataset.
    """
    logger.info("Loading a local Parquet dataset")
    return load_local_dataset(
        DatasetLoadRequest(
            relative_path=Path(path),
            format="parquet",
            request_id=generate_id("req"),
        )
    )


__all__ = ["load_parquet"]

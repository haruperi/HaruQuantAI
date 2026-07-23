"""Focused CSV dataset loading through the governed local loader."""

from pathlib import Path
from typing import TYPE_CHECKING

from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.persistence.dataset_writer import load_local_dataset
from app.utils import generate_id, logger

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset


def load_csv(path: Path | str) -> MarketDataset:
    """Load one manifest-backed CSV dataset.

    Args:
        path: Approved-root-relative CSV artifact path.

    Returns:
        The normalized canonical market dataset.
    """
    logger.info("Loading a local CSV dataset")
    return load_local_dataset(
        DatasetLoadRequest(
            relative_path=Path(path),
            format="csv",
            request_id=generate_id("req"),
        )
    )


__all__ = ["load_csv"]

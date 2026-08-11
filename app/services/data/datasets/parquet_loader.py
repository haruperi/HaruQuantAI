"""Focused Parquet dataset loading through the governed local loader."""

from pathlib import Path
from typing import TYPE_CHECKING

from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.datasets.contracts import DatasetLoadRequest
from app.services.data.persistence.dataset_writer import _load_local_dataset_raw
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset


def load_parquet(path: Path | str) -> StandardResponse[MarketDataset]:
    """Load one manifest-backed Parquet dataset.

    Args:
        path: Approved-root-relative Parquet artifact path.

    Returns:
        Standard response carrying the normalized canonical market dataset.
    """
    logger.info("Loading a local Parquet dataset")
    request = DatasetLoadRequest(
        relative_path=Path(path),
        format="parquet",
        request_id=generate_id("req"),
    )
    return run_data_operation(
        operation="data.local_datasets.load_parquet",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _load_local_dataset_raw(request),
    )


__all__ = ["load_parquet"]

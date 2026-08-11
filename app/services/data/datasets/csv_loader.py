"""Focused CSV dataset loading through the governed local loader."""

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


def load_csv(path: Path | str) -> StandardResponse[MarketDataset]:
    """Load one manifest-backed CSV dataset.

    Args:
        path: Approved-root-relative CSV artifact path.

    Returns:
        Standard response carrying the normalized canonical market dataset.
    """
    logger.info("Loading a local CSV dataset")
    request = DatasetLoadRequest(
        relative_path=Path(path),
        format="csv",
        request_id=generate_id("req"),
    )
    return run_data_operation(
        operation="data.local_datasets.load_csv",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _load_local_dataset_raw(request),
    )


__all__ = ["load_csv"]

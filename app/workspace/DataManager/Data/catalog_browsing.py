"""Filter metadata with deterministic symbol and ID ordering.

Description:
    Filter metadata with deterministic symbol and ID ordering.
    Accepts caller-supplied immutable data and returns an explicit result.
    No persistence, network calls, scheduling or import-time work is performed.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-CATALOG-BROWSING: Filter metadata with deterministic symbol and ID
      ordering.
      Associated: `browse_catalog()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.catalog_browsing import (
        browse_catalog,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = browse_catalog(Catalog((dataset,)))
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_catalog_browsing.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import dataclass

from app.host.logging import get_logger
from app.host.response import StandardResponse
from app.workspace.DataManager.Data.contracts import Catalog, Dataset


@dataclass(frozen=True, slots=True)
class BrowseResult:
    """Filtered datasets and the displayed dataset count."""

    datasets: tuple[Dataset, ...]
    count: int


def browse_catalog(
    catalog: Catalog,
    *,
    text: str = "",
    source_id: str | None = None,
    asset_type: str | None = None,
    broker_id: str | None = None,
    group: str | None = None,
) -> StandardResponse[BrowseResult]:
    """Apply combined filters without changing the complete supplied catalog."""
    search = text.lower()
    items = tuple(
        sorted(
            (
                item
                for item in catalog.datasets
                if (search in item.symbol.lower() or search in item.instrument.lower())
                and (source_id is None or item.source_id == source_id)
                and (asset_type is None or item.asset_type == asset_type)
                and (broker_id is None or item.broker_id == broker_id)
                and (group is None or group in item.groups)
            ),
            key=lambda item: (item.symbol, item.id),
        )
    )
    logger.info(
        "Dataset operation completed", extra={"outcome": "success", "count": len(items)}
    )
    return StandardResponse.success(data=BrowseResult(items, len(items)))


logger = get_logger(__name__).bind(requirement="FR-DATASET-CATALOG-BROWSING")

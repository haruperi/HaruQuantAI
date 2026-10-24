"""Data Manager baskets (stock groups) catalog service.

Description:
    Provides stock groups / baskets and their constituent ticker memberships
    for the Data Manager workspace, reading from the authoritative SQLite database
    (datamgr_stock_group and datamgr_stock tables). Exposes basket definitions,
    constituent counts, and membership items.

Purpose:
    FEAT-DATAMGR-BASKETS: Data Manager baskets and stock groups catalog service.

Key Capabilities:
    - FR-DATAMGR-BASKETS-CATALOG: Baskets catalog (Baskets.list).

Python API Usage:
    ```python
    from app.workspace.data_manager.baskets import Baskets

    baskets_svc = Baskets()
    baskets = baskets_svc.list()
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.baskets
    ```
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

__all__ = [
    "BasketInfo",
    "BasketStockItem",
    "Baskets",
]

logger = get_logger(__name__)
persistence = HostPersistence()

BASKETS_CATALOG_FR = "FR-DATAMGR-BASKETS-CATALOG"
DESC_PARTS_MIN_LEN: int = 3


def _ms_to_date(ms: int) -> str:
    """Convert millisecond timestamp to DD.MM.YYYY string."""
    if ms <= 0:
        return "-"
    try:
        dt = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=ms)
        return dt.strftime("%d.%m.%Y")
    except OverflowError, OSError, ValueError:
        return "-"


@dataclass(slots=True)
class BasketStockItem:
    """Constituent stock membership in a basket."""

    id: int = 0
    ticker: str = ""
    basket_id: int = 0
    date_from: int = 0
    date_to: int = -1

    def to_dict(self) -> dict[str, Any]:
        """Serialize BasketStockItem to a dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> BasketStockItem:
        """Construct BasketStockItem from datamgr_stock table row."""
        raw_date_to = row.get("DATE_TO")
        if raw_date_to is None:
            raw_date_to = row.get("date_to")
        date_to = int(raw_date_to) if raw_date_to is not None else -1
        return cls(
            id=int(row.get("ID") or row.get("id") or 0),
            ticker=str(row.get("TICKER") or row.get("ticker") or ""),
            basket_id=int(row.get("BASKET_ID") or row.get("basket_id") or 0),
            date_from=int(row.get("DATE_FROM") or row.get("date_from") or 0),
            date_to=date_to,
        )


@dataclass(slots=True)
class BasketInfo:
    """Basket (stock group) catalog record definition."""

    id: int = 0
    name: str = ""
    system: bool = False
    description: str = ""
    stocks_count: int = 0
    active_count: int = 0
    symbols_count: int = 0
    downloaded_count: int = 0
    ready: bool = False
    date_from: str = "-"
    date_to: str = "-"
    stocks: list[BasketStockItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize BasketInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_group_row(
        cls,
        row: Mapping[str, Any],
        stocks: list[BasketStockItem] | None = None,
        downloaded_symbols: set[str] | None = None,
    ) -> BasketInfo:
        """Construct BasketInfo from datamgr_stock_group row and constituent stocks."""
        desc = str(row.get("description") or row.get("DESC") or "")
        stock_list = stocks if stocks is not None else []
        stocks_count = len(stock_list)

        now_ms = int(time.time() * 1000)
        active_count = sum(
            1 for s in stock_list if s.date_to == -1 or s.date_to >= now_ms
        )

        downloaded_set = downloaded_symbols if downloaded_symbols is not None else set()
        downloaded_count = sum(
            1
            for s in stock_list
            if (
                s.ticker.upper().split(".")[0] in downloaded_set
                or s.ticker.upper() in downloaded_set
            )
        )
        symbols_count = downloaded_count

        ready = stocks_count > 0 and downloaded_count >= stocks_count

        valid_from = [s.date_from for s in stock_list if s.date_from > 0]
        date_from = _ms_to_date(min(valid_from)) if valid_from else "-"

        valid_to = [s.date_to for s in stock_list if s.date_to > 0]
        date_to = _ms_to_date(max(valid_to)) if valid_to else "-"

        if (date_from == "-" or date_to == "-") and ";" in desc:
            parts = [p.strip() for p in desc.split(";")]
            if len(parts) >= DESC_PARTS_MIN_LEN:
                if date_from == "-" and parts[1]:
                    date_from = parts[1]
                if date_to == "-" and parts[2]:
                    date_to = parts[2]

        return cls(
            id=int(row.get("ID") or row.get("id") or 0),
            name=str(row.get("NAME") or row.get("name") or ""),
            system=bool(row.get("SYSTEM") or row.get("system") or 0),
            description=desc,
            stocks_count=stocks_count,
            active_count=active_count,
            symbols_count=symbols_count,
            downloaded_count=downloaded_count,
            ready=ready,
            date_from=date_from,
            date_to=date_to,
            stocks=stock_list,
        )


class Baskets:
    """Service providing baskets and stock groups catalog presentation."""

    def _read_stock_groups(self) -> list[dict[str, Any]]:
        """Read all stock groups from datamgr_stock_group table."""
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_stock_group", limit=1000, offset=offset
            )
            if not response["success"]:
                err = response.get("error") or {}
                msg = (
                    err.get("message")
                    or response.get("message")
                    or "Database read failure"
                )
                raise RuntimeError(msg)
            data = response.get("data") or {}
            rows.extend(data.get("records") or [])
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return rows

    def _read_stocks(self) -> list[dict[str, Any]]:
        """Read all constituent stocks from datamgr_stock table."""
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_stock", limit=1000, offset=offset
            )
            if not response["success"]:
                err = response.get("error") or {}
                msg = (
                    err.get("message")
                    or response.get("message")
                    or "Database read failure"
                )
                raise RuntimeError(msg)
            data = response.get("data") or {}
            rows.extend(data.get("records") or [])
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return rows

    def _read_downloaded_symbols(self) -> set[str]:
        """Read set of downloaded symbol names from datamgr_datasets table."""
        downloaded: set[str] = set()
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_datasets", limit=1000, offset=offset
            )
            if not response["success"]:
                break
            data = response.get("data") or {}
            for rec in data.get("records") or []:
                sym = str(rec.get("symbol") or rec.get("SYMBOL") or "").strip()
                bars = int(rec.get("bars") or rec.get("BARS") or 0)
                if sym and bars > 0:
                    downloaded.add(sym.upper())
                    downloaded.add(sym.upper().split(".")[0])
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return downloaded

    def list(self, *, include_stocks: bool = True) -> dict[str, Any]:
        """Retrieve basket catalog items wrapped in StandardResponse.

        Args:
            include_stocks: Whether to query and populate constituent stock items.
        """
        start = time.perf_counter()
        try:
            group_rows = self._read_stock_groups()
            downloaded_symbols = self._read_downloaded_symbols()

            stocks_by_basket: dict[int, list[BasketStockItem]] = defaultdict(list)
            if include_stocks:
                stock_rows = self._read_stocks()
                for sr in stock_rows:
                    item = BasketStockItem.from_row(sr)
                    stocks_by_basket[item.basket_id].append(item)

            baskets = [
                BasketInfo.from_group_row(
                    gr,
                    stocks=stocks_by_basket.get(int(gr.get("ID") or gr.get("id") or 0)),
                    downloaded_symbols=downloaded_symbols,
                )
                for gr in group_rows
            ]

            logger.debug(
                "%s: Retrieved %d basket catalog items",
                BASKETS_CATALOG_FR,
                len(baskets),
                extra={"fr_id": BASKETS_CATALOG_FR, "count": len(baskets)},
            )
            return StandardResponse.success(
                message=f"Retrieved {len(baskets)} basket catalog items",
                metadata=ResponseMetadata(
                    operation="baskets.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=baskets,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("%s: Failed to list baskets", BASKETS_CATALOG_FR)
            return StandardResponse.failure(
                message=str(error) or "Failed to retrieve baskets",
                metadata=ResponseMetadata(
                    operation="baskets.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error) or "Internal error listing baskets",
                ),
            )


if __name__ == "__main__":
    from app.workspace.data_manager.cli import format_basket_table

    baskets_svc = Baskets()
    response = baskets_svc.list()
    if response["success"]:
        print(format_basket_table(response))
    else:
        print(f"Failed: {response['message']}")

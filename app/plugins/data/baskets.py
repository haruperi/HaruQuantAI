"""Market data baskets, stock groups, and multi-symbol series alignment.

Description:
    Service managing multi-asset baskets, stock groups, and cross-instrument
    series alignment for portfolio analysis and synthetic instrument generation.
    Supports stock group persistence in datamgr_stock_group and datamgr_stock
    tables, configurable weighting schemes (equal or custom), and chronological
    timestamp alignment across heterogeneous series using intersection (inner join)
    or union (outer join with forward-fill / notNaN) policies.

Purpose:
    FEAT-DATA-BASKETS: Manage stock groups, baskets, and multi-series alignment.

Key Capabilities:
    FR-DATA-BASKETS-GROUPS: Manage stock groups and basket compositions.
    FR-DATA-BASKETS-ALIGNMENT: Multi-symbol alignment and synthetic bar math.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.plugins.data.baskets import BasketDefinition, BasketItem, BasketService

    db = DatabaseManager()
    db.initialize()
    service = BasketService(db)

    basket = BasketDefinition(
        name="Tech_Trio",
        description="Top technology basket",
        items=[
            BasketItem(symbol="AAPL", weight=0.4),
            BasketItem(symbol="MSFT", weight=0.4),
            BasketItem(symbol="GOOGL", weight=0.2),
        ],
    )
    service.save_basket(basket)
    synthetic_bars = service.compute_basket_series(basket, series_dict)
    ```

CLI Usage:
    ```bash
    python -m app.plugins.data.baskets --list
    ```
"""

from __future__ import annotations

import argparse
import sys

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.plugins.data.ingestion import BarRecord
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = get_logger(__name__)


class BasketItem(BaseModel):
    """Specification of a single constituent within a market basket."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1, description="Constituent symbol")
    weight: float = Field(default=1.0, gt=0.0, description="Relative weighting factor")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize basket constituent symbol."""
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Basket constituent symbol cannot be empty.")
        return clean


class BasketDefinition(BaseModel):
    """Authoritative domain specification of a multi-asset market basket."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=128, description="Basket name")
    description: str = Field(default="", description="Descriptive label")
    items: list[BasketItem] = Field(
        min_length=1, description="List of basket constituents"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate non-empty basket name."""
        clean = v.strip()
        if not clean:
            raise ValueError("Basket name cannot be empty.")
        return clean


class BasketService:
    """Service managing stock groups, baskets, and multi-symbol alignment."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize basket service with host DatabaseManager."""
        self._db = db

    def save_basket(self, basket: BasketDefinition) -> int:
        """Upsert basket and its constituent items in datamgr_stock_group.

        Fires FR-DATA-BASKETS-GROUPS.
        """
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM datamgr_stock_group WHERE name = ?;",
                (basket.name,),
            )
            row = cur.fetchone()
            if row is not None:
                group_id = int(row[0])
                cur.execute(
                    "UPDATE datamgr_stock_group SET description = ? WHERE id = ?;",
                    (basket.description, group_id),
                )
                cur.execute(
                    "DELETE FROM datamgr_stock WHERE basket_id = ?;", (group_id,)
                )
            else:
                cur.execute(
                    "INSERT INTO datamgr_stock_group (name, description, system) "
                    "VALUES (?, ?, ?);",
                    (basket.name, basket.description, 0),
                )
                group_id = cur.lastrowid or 0

            for item in basket.items:
                cur.execute(
                    "INSERT INTO datamgr_stock (ticker, basket_id, date_from) "
                    "VALUES (?, ?, ?);",
                    (item.symbol, group_id, "1900-01-01"),
                )

        logger.info(
            "FR-DATA-BASKETS-GROUPS: Saved basket '%s' (id=%d, items=%d)",
            basket.name,
            group_id,
            len(basket.items),
            extra={
                "basket_name": basket.name,
                "group_id": group_id,
                "item_count": len(basket.items),
                "fr_id": "FR-DATA-BASKETS-GROUPS",
            },
        )
        return group_id

    def get_basket(self, name: str) -> BasketDefinition | None:
        """Retrieve basket definition and constituents by name.

        Fires FR-DATA-BASKETS-GROUPS.
        """
        clean_name = name.strip()
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, description FROM datamgr_stock_group WHERE name = ?;",
                (clean_name,),
            )
            group_row = cur.fetchone()
            if group_row is None:
                return None
            group_id = int(group_row[0])
            desc = str(group_row[2] or "")

            cur.execute(
                "SELECT ticker FROM datamgr_stock WHERE basket_id = ? ORDER BY id ASC;",
                (group_id,),
            )
            stock_rows = cur.fetchall()
            items = [BasketItem(symbol=str(r[0]), weight=1.0) for r in stock_rows]

        return BasketDefinition(name=clean_name, description=desc, items=items)

    def list_baskets(self) -> list[BasketDefinition]:
        """List all defined baskets in the database."""
        with self._db.connection(query_only=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM datamgr_stock_group ORDER BY name ASC;")
            names = [str(r[0]) for r in cur.fetchall()]

        baskets: list[BasketDefinition] = []
        for n in names:
            b = self.get_basket(n)
            if b is not None:
                baskets.append(b)
        return baskets

    def delete_basket(self, name: str) -> bool:
        """Delete basket and its constituents by name.

        Fires FR-DATA-BASKETS-GROUPS.
        """
        clean_name = name.strip()
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM datamgr_stock_group WHERE name = ?;",
                (clean_name,),
            )
            row = cur.fetchone()
            if row is None:
                return False
            group_id = int(row[0])
            cur.execute("DELETE FROM datamgr_stock WHERE basket_id = ?;", (group_id,))
            cur.execute("DELETE FROM datamgr_stock_group WHERE id = ?;", (group_id,))

        logger.info(
            "FR-DATA-BASKETS-GROUPS: Deleted basket '%s' (id=%d)",
            clean_name,
            group_id,
            extra={
                "basket_name": clean_name,
                "group_id": group_id,
                "fr_id": "FR-DATA-BASKETS-GROUPS",
            },
        )
        return True

    def align_series(
        self,
        series_dict: dict[str, list[BarRecord]],
        policy: str = "intersection",
    ) -> list[dict[str, BarRecord]]:
        """Align multiple symbol bar series along common timestamps.

        Supported policies:
            - 'intersection': Only timestamps present in every series (inner join).
            - 'union': All timestamps across all series with forward-fill (outer join).

        Fires FR-DATA-BASKETS-ALIGNMENT.
        """
        if not series_dict:
            return []

        # Index each series by timestamp
        sym_maps: dict[str, dict[str, BarRecord]] = {}
        for sym, bars in series_dict.items():
            sym_maps[sym] = {b.timestamp_utc: b for b in bars}

        symbols = list(series_dict.keys())
        all_timestamps_sets = [set(m.keys()) for m in sym_maps.values()]

        if policy == "intersection":
            common_timestamps = sorted(
                set.intersection(*all_timestamps_sets) if all_timestamps_sets else set()
            )
            aligned: list[dict[str, BarRecord]] = []
            for ts in common_timestamps:
                row = {sym: sym_maps[sym][ts] for sym in symbols}
                aligned.append(row)
            return aligned

        # Union with forward-fill
        all_timestamps = sorted(set.union(*all_timestamps_sets))
        aligned_union: list[dict[str, BarRecord]] = []
        last_known: dict[str, BarRecord] = {}

        for ts in all_timestamps:
            row = {}
            for sym in symbols:
                if ts in sym_maps[sym]:
                    bar = sym_maps[sym][ts]
                    last_known[sym] = bar
                    row[sym] = bar
                elif sym in last_known:
                    # Forward-fill previous bar with updated timestamp
                    prev = last_known[sym]
                    row[sym] = prev.model_copy(update={"timestamp_utc": ts})
            # Only include row if at least one symbol is present
            if len(row) == len(symbols):
                aligned_union.append(row)

        return aligned_union

    def compute_basket_series(
        self,
        basket: BasketDefinition,
        series_dict: dict[str, list[BarRecord]],
        policy: str = "intersection",
    ) -> list[BarRecord]:
        """Compute synthetic aggregate OHLCV bars for a weighted basket.

        Fires FR-DATA-BASKETS-ALIGNMENT.
        """
        aligned_rows = self.align_series(series_dict, policy=policy)
        if not aligned_rows:
            return []

        total_weight = sum(item.weight for item in basket.items)
        if total_weight <= 0.0:
            raise ValueError("Total basket weight must be strictly positive.")

        weights_map = {item.symbol: item.weight for item in basket.items}
        synthetic_bars: list[BarRecord] = []

        for row in aligned_rows:
            # Check all constituent symbols present in aligned row
            if not all(sym in row for sym in weights_map):
                continue

            ts = next(iter(row.values())).timestamp_utc

            agg_open = (
                sum(row[sym].open * weights_map[sym] for sym in weights_map)
                / total_weight
            )
            agg_high = (
                sum(row[sym].high * weights_map[sym] for sym in weights_map)
                / total_weight
            )
            agg_low = (
                sum(row[sym].low * weights_map[sym] for sym in weights_map)
                / total_weight
            )
            agg_close = (
                sum(row[sym].close * weights_map[sym] for sym in weights_map)
                / total_weight
            )
            agg_vol = sum(row[sym].volume * weights_map[sym] for sym in weights_map)

            synthetic_bars.append(
                BarRecord(
                    timestamp_utc=ts,
                    open=round(agg_open, 5),
                    high=round(agg_high, 5),
                    low=round(agg_low, 5),
                    close=round(agg_close, 5),
                    volume=round(agg_vol, 2),
                )
            )

        logger.info(
            "FR-DATA-BASKETS-ALIGNMENT: Computed %d synthetic bars for basket '%s'",
            len(synthetic_bars),
            basket.name,
            extra={
                "basket": basket.name,
                "bars": len(synthetic_bars),
                "policy": policy,
                "fr_id": "FR-DATA-BASKETS-ALIGNMENT",
            },
        )
        return synthetic_bars


def main() -> int:
    """CLI tool for inspecting market baskets."""
    parser = argparse.ArgumentParser(description="Manage market baskets")
    parser.add_argument("--list", action="store_true", help="List all baskets")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = BasketService(db)

    if args.list:
        baskets = service.list_baskets()
        print(f"Configured Baskets ({len(baskets)}):")
        for b in baskets:
            constituents = ", ".join(f"{i.symbol}:{i.weight}" for i in b.items)
            print(f"  {b.name:20} [{constituents}]")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

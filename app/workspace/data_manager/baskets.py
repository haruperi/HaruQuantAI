"""Stock groups and composite baskets with survivorship-bias-free tracking.

Description:
    Provides domain logic for stock groups and composite baskets (`datamgr_stock_group`
    and `datamgr_stock`), supporting survivorship-bias-free historical constituent
    membership windows, readiness evaluation against downloaded datasets, batch
    historical dataset provisioning, CSV constituent import/export, and StrategyQuant X
    `<Groups>` XML transfer.

Purpose:
    FEAT-DATAMGR-BASKETS: Stock groups, survivorship-bias-free membership,
    and readiness.

Key Capabilities:
    - FR-DATAMGR-BASKETS-CRUD: Manage stock groups and constituents in
      SQLite tables.
      Associated: `BasketsCatalogService.list_baskets()`,
      `BasketsCatalogService.save_basket()`,
      `BasketsCatalogService.delete_basket()`
      Logging: Emits INFO on creation, update, and deletion of baskets and
      members.
    - FR-DATAMGR-BASKETS-OVERVIEW-READINESS: Calculate 8-column overview
      and data readiness.
      Associated: `BasketsCatalogService.get_baskets_overview()`
      Logging: Emits DEBUG when computing constituent readiness and missing symbols.
    - FR-DATAMGR-BASKETS-CSV-AND-XML: Constituent CSV and SQX XML import/export.
      Associated: `BasketsCatalogService.export_xml()`,
      `BasketsCatalogService.import_xml()`,
      `BasketsCatalogService.import_csv()`
      Logging: Emits INFO on XML and CSV transfer operations.
    - FR-DATAMGR-BASKETS-DATA-UPDATE: Trigger batch data provisioning for
      constituents.
      Associated: `BasketsCatalogService.update_baskets_data()`
      Logging: Emits INFO on provisioning historical datasets for basket tickers.

Python API Usage:
    ```python
    from app.workspace.data_manager.baskets import BasketsCatalogService

    service = BasketsCatalogService()
    overview = service.get_baskets_overview()
    for item in overview:
        print(
            f"Basket {item.name}: ready={item.is_ready} ({item.symbols_count} symbols)"
        )
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.baskets
    ```
"""

from __future__ import annotations

import csv
import io
import json
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as DefusedET  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.host.persistence.create import create_schema, insert_row
from app.host.persistence.delete import delete_row_by_pk, delete_rows
from app.host.persistence.read import count_rows, read_rows, resolve_connection
from app.host.persistence.update import update_row_by_pk
from app.workspace.data_manager.data import DataManagerDataService

__all__ = [
    "BasketDefinition",
    "BasketMember",
    "BasketOverviewItem",
    "BasketsCatalogService",
]

logger = get_logger(__name__)

BASKETS_CRUD_FR = "FR-DATAMGR-BASKETS-CRUD"
OVERVIEW_READINESS_FR = "FR-DATAMGR-BASKETS-OVERVIEW-READINESS"
CSV_XML_FR = "FR-DATAMGR-BASKETS-CSV-AND-XML"
DATA_UPDATE_FR = "FR-DATAMGR-BASKETS-DATA-UPDATE"


@dataclass(frozen=True)
class BasketMember:
    """Represents a single constituent stock in a basket."""

    symbol: str
    weight: float = 1.0
    date_from: str | None = None
    date_to: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert constituent member to dictionary representation."""
        return {
            "symbol": self.symbol,
            "weight": self.weight,
            "date_from": self.date_from,
            "date_to": self.date_to,
        }


@dataclass
class BasketDefinition:
    """Represents a composite stock group / basket."""

    id: int | None = None
    name: str = ""
    description: str = ""
    system: bool = False
    items: list[BasketMember] = field(default_factory=list)

    def active_members_on(self, date_iso: str) -> list[BasketMember]:
        """Filter constituent members active on target date (survivorship-bias-free)."""
        active: list[BasketMember] = []
        for m in self.items:
            if m.date_from and m.date_from > date_iso:
                continue
            if m.date_to and m.date_to < date_iso:
                continue
            active.append(m)
        return active

    def to_dict(self) -> dict[str, Any]:
        """Convert basket definition to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system": self.system,
            "items": [m.to_dict() for m in self.items],
            "symbols_count": len(self.items),
        }


@dataclass(frozen=True)
class BasketOverviewItem:
    """Represents the 8-column overview item for a stock group."""

    id: int
    name: str
    description: str
    system: bool
    active_count: int
    total_count: int
    symbols_count: int
    downloaded_count: int
    is_ready: bool
    missing_symbols: list[str]
    data_from: str
    data_to: str
    data_from_sqx: str
    data_to_sqx: str

    def to_dict(self) -> dict[str, Any]:
        """Convert overview item to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system": self.system,
            "active_count": self.active_count,
            "total_count": self.total_count,
            "symbols_count": self.symbols_count,
            "downloaded_count": self.downloaded_count,
            "is_ready": self.is_ready,
            "missing_symbols": self.missing_symbols,
            "data_from": self.data_from,
            "data_to": self.data_to,
            "data_from_sqx": self.data_from_sqx,
            "data_to_sqx": self.data_to_sqx,
        }


_DEFAULT_SEEDED_BASKETS: tuple[dict[str, Any], ...] = (
    {
        "NAME": "S&P 100 limited",
        "description": "Top US Large Cap Equities",
        "SYSTEM": 1,
        "stocks": ["AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "META", "TSLA", "JPM"],
    },
    {
        "NAME": "NASDAQ 100 Core",
        "description": "Core Technology and Growth Equities",
        "SYSTEM": 1,
        "stocks": ["AAPL", "MSFT", "NVDA", "AVGO", "COST", "ASML", "ADBE"],
    },
    {
        "NAME": "Dow 30",
        "description": "Dow Jones Industrial Average constituents",
        "SYSTEM": 1,
        "stocks": ["AAPL", "MSFT", "JPM", "UNH", "V", "PG", "HD", "DIS"],
    },
)


def _parse_basket_date(raw_val: Any, default: int | None = None) -> int | None:
    if raw_val is None:
        return default
    try:
        return int(str(raw_val).replace("-", ""))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid date value '{raw_val}'") from exc


def _validate_basket_constituents(
    items: Sequence[Any],
) -> list[tuple[str, int, int | None, float]]:
    validated: list[tuple[str, int, int | None, float]] = []
    for item in items:
        if isinstance(item, str):
            sym = item.strip().upper()
            if not sym:
                raise ValueError("Constituent symbol cannot be empty.")
            validated.append((sym, 20200101, None, 1.0))
        elif isinstance(item, (dict, Mapping)):
            sym = str(item.get("symbol") or item.get("TICKER", "")).strip().upper()
            if not sym:
                raise ValueError("Constituent symbol cannot be empty.")
            df_int = _parse_basket_date(
                item.get("date_from")
                if item.get("date_from") is not None
                else item.get("DATE_FROM"),
                default=20200101,
            )
            dt_int = _parse_basket_date(
                item.get("date_to")
                if item.get("date_to") is not None
                else item.get("DATE_TO")
            )
            try:
                weight_val = float(item.get("weight", 1.0))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid weight value for {sym}") from exc
            validated.append((sym, df_int or 20200101, dt_int, weight_val))
        else:
            raise TypeError(f"Invalid constituent specification: {item}")
    return validated


class BasketsCatalogService:
    """Service governing stock groups, memberships, and CSV/XML transfer."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        data_service: DataManagerDataService | None = None,
    ) -> None:
        """Initialize baskets service with database path and data service."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.data_service = data_service

    def ensure_default_baskets(self) -> int:
        """Seed default canonical stock groups if table is empty."""
        with resolve_connection(self.db_path) as conn:
            existing = count_rows(conn, "datamgr_stock_group")
            if existing > 0:
                return 0

            seeded = 0
            for item in _DEFAULT_SEEDED_BASKETS:
                grp_data = {
                    "NAME": item["NAME"],
                    "description": item["description"],
                    "SYSTEM": item["SYSTEM"],
                    "DESC": item["description"],
                }
                inserted = insert_row(conn, "datamgr_stock_group", grp_data)
                grp_id = int(inserted)

                for ticker in item["stocks"]:
                    insert_row(
                        conn,
                        "datamgr_stock",
                        {
                            "TICKER": ticker,
                            "BASKET_ID": grp_id,
                            "DATE_FROM": 20200101,
                            "DATE_TO": None,
                        },
                    )
                seeded += 1

        logger.info(
            "%s: Seeded %d default stock groups",
            BASKETS_CRUD_FR,
            seeded,
            extra={"fr_id": BASKETS_CRUD_FR, "seeded": seeded},
        )
        return seeded

    def list_baskets(self) -> list[BasketDefinition]:
        """List all stock groups and their constituent members."""
        with resolve_connection(self.db_path) as conn:
            grp_rows = read_rows(conn, "datamgr_stock_group", order_by="NAME ASC")
            stock_rows = read_rows(conn, "datamgr_stock", order_by="ID ASC")
            entity_rows = read_rows(
                conn,
                "host_entities",
                where={"entity_type": "datamgr_basket_constituents"},
            )

        weights_by_basket: dict[int, dict[str, float]] = {}
        for er in entity_rows:
            try:
                bid = int(er.get("entity_id", 0))
                raw_payload = er.get("payload", "{}")
                weights_by_basket[bid] = (
                    json.loads(raw_payload)
                    if isinstance(raw_payload, str)
                    else raw_payload
                )
            except ValueError, TypeError, json.JSONDecodeError:
                pass

        grp_stocks_map: dict[int, list[BasketMember]] = {}
        for s in stock_rows:
            bid = int(s.get("BASKET_ID", 0))
            if bid not in grp_stocks_map:
                grp_stocks_map[bid] = []
            df_val = s.get("DATE_FROM")
            dt_val = s.get("DATE_TO")
            sym = str(s.get("TICKER", "")).upper()
            w = weights_by_basket.get(bid, {}).get(sym, float(s.get("WEIGHT", 1.0)))
            grp_stocks_map[bid].append(
                BasketMember(
                    symbol=sym,
                    weight=float(w),
                    date_from=str(df_val) if df_val else None,
                    date_to=str(dt_val) if dt_val else None,
                )
            )

        baskets: list[BasketDefinition] = []
        for g in grp_rows:
            gid = int(g.get("ID", 0))
            baskets.append(
                BasketDefinition(
                    id=gid,
                    name=str(g.get("NAME", "")),
                    description=str(g.get("description") or g.get("DESC") or ""),
                    system=bool(g.get("SYSTEM", False)),
                    items=grp_stocks_map.get(gid, []),
                )
            )
        return baskets

    def get_basket(self, name_or_id: str | int) -> BasketDefinition | None:
        """Retrieve a stock group by ID or name."""
        all_baskets = self.list_baskets()
        target = str(name_or_id).strip().lower()
        for b in all_baskets:
            if str(b.id) == target or b.name.lower() == target:
                return b
        return None

    def get_baskets_overview(self) -> list[BasketOverviewItem]:
        """Calculate the 8-column overview cross-referencing downloaded datasets."""
        baskets = self.list_baskets()
        with resolve_connection(self.db_path) as conn:
            dataset_rows = read_rows(conn, "datamgr_datasets")

        datasets_by_symbol = {str(d.get("symbol", "")).upper(): d for d in dataset_rows}
        today_iso = datetime.now(UTC).strftime("%Y%m%d")

        overview_items: list[BasketOverviewItem] = []
        for b in baskets:
            bid = b.id or 0
            symbols = [m.symbol.upper() for m in b.items]
            active_members = b.active_members_on(today_iso)

            downloaded: list[str] = []
            missing: list[str] = []
            earliest_dates: list[str] = []
            latest_dates: list[str] = []

            for sym in symbols:
                if sym in datasets_by_symbol:
                    rec = datasets_by_symbol[sym]
                    if int(rec.get("bars", 0)) > 0:
                        downloaded.append(sym)
                        if rec.get("date_from"):
                            earliest_dates.append(str(rec["date_from"]))
                        if rec.get("date_to"):
                            latest_dates.append(str(rec["date_to"]))
                        continue
                missing.append(sym)

            is_ready = len(symbols) > 0 and len(downloaded) == len(symbols)
            data_from = min(earliest_dates) if earliest_dates else ""
            data_to = max(latest_dates) if latest_dates else ""

            overview_items.append(
                BasketOverviewItem(
                    id=bid,
                    name=b.name,
                    description=b.description,
                    system=b.system,
                    active_count=len(active_members),
                    total_count=len(b.items),
                    symbols_count=len(b.items),
                    downloaded_count=len(downloaded),
                    is_ready=is_ready,
                    missing_symbols=missing,
                    data_from=data_from,
                    data_to=data_to,
                    data_from_sqx=data_from.replace("-", ".") if data_from else "",
                    data_to_sqx=data_to.replace("-", ".") if data_to else "",
                )
            )

        logger.debug(
            "%s: Computed overview for %d baskets",
            OVERVIEW_READINESS_FR,
            len(overview_items),
            extra={"fr_id": OVERVIEW_READINESS_FR, "count": len(overview_items)},
        )
        return overview_items

    def save_basket(self, payload: Mapping[str, Any]) -> BasketDefinition:
        """Create or update a stock group and constituent stocks."""
        clean_name = str(payload.get("name") or payload.get("NAME", "")).strip()
        if not clean_name:
            raise ValueError("Stock group name is required.")

        desc = str(payload.get("description") or payload.get("DESC", ""))
        is_sys = 1 if payload.get("system") or payload.get("SYSTEM") else 0

        # Validate candidate constituents before mutating database (R21)
        items = payload.get("items") or payload.get("stocks", [])
        validated_items = _validate_basket_constituents(items)

        existing = self.get_basket(clean_name)
        with resolve_connection(self.db_path) as conn, conn:
            if existing is not None and existing.id is not None:
                grp_id = existing.id
                update_row_by_pk(
                    conn,
                    "datamgr_stock_group",
                    {"ID": grp_id},
                    {
                        "NAME": clean_name,
                        "description": desc,
                        "DESC": desc,
                        "SYSTEM": is_sys,
                    },
                )
                delete_rows(conn, "datamgr_stock", where={"BASKET_ID": grp_id})
            else:
                inserted = insert_row(
                    conn,
                    "datamgr_stock_group",
                    {
                        "NAME": clean_name,
                        "description": desc,
                        "DESC": desc,
                        "SYSTEM": is_sys,
                    },
                )
                grp_id = int(inserted)

            weights_map: dict[str, float] = {}
            for sym, df_int, dt_int, weight in validated_items:
                insert_row(
                    conn,
                    "datamgr_stock",
                    {
                        "TICKER": sym,
                        "BASKET_ID": grp_id,
                        "DATE_FROM": df_int,
                        "DATE_TO": dt_int,
                    },
                )
                weights_map[sym] = weight

            now_iso = datetime.now(UTC).isoformat()
            delete_rows(
                conn,
                "host_entities",
                where={
                    "entity_id": str(grp_id),
                    "entity_type": "datamgr_basket_constituents",
                },
            )
            insert_row(
                conn,
                "host_entities",
                {
                    "entity_id": str(grp_id),
                    "entity_type": "datamgr_basket_constituents",
                    "scope": "workspace:data_manager",
                    "payload": json.dumps(weights_map),
                    "revision": 1,
                    "created_at_utc": now_iso,
                    "updated_at_utc": now_iso,
                },
            )

        updated = self.get_basket(grp_id)
        if updated is None:
            raise RuntimeError("Failed to retrieve saved basket.")

        logger.info(
            "%s: Saved basket name=%s id=%s members=%d",
            BASKETS_CRUD_FR,
            updated.name,
            updated.id,
            len(updated.items),
            extra={
                "fr_id": BASKETS_CRUD_FR,
                "basket_name": updated.name,
                "id": updated.id,
            },
        )
        return updated

    def delete_basket(self, name_or_id: str | int) -> bool:
        """Delete a stock group and constituent stocks."""
        basket = self.get_basket(name_or_id)
        if basket is None or basket.id is None:
            return False

        with resolve_connection(self.db_path) as conn:
            delete_rows(conn, "datamgr_stock", where={"BASKET_ID": basket.id})
            deleted = delete_row_by_pk(conn, "datamgr_stock_group", {"ID": basket.id})

        logger.info(
            "%s: Deleted basket name=%s deleted=%s",
            BASKETS_CRUD_FR,
            basket.name,
            deleted,
            extra={
                "fr_id": BASKETS_CRUD_FR,
                "basket_name": basket.name,
                "deleted": deleted,
            },
        )
        return bool(deleted)

    def update_baskets_data(
        self, basket_ids: Sequence[str | int]
    ) -> list[dict[str, Any]]:
        """Trigger historical dataset provisioning for all constituent symbols."""
        results: list[dict[str, Any]] = []
        for bid in basket_ids:
            basket = self.get_basket(bid)
            if basket is None:
                continue

            symbols = [m.symbol for m in basket.items]
            provisioned = 0
            if self.data_service:
                for sym in symbols:
                    self.data_service.import_dataset(
                        {"symbol": sym, "source": "file", "timeframe": "M1"}
                    )
                    provisioned += 1

            results.append(
                {
                    "basket_id": basket.id,
                    "basket_name": basket.name,
                    "symbols_count": len(symbols),
                    "provisioned_count": provisioned,
                    "status": "completed",
                }
            )

        logger.info(
            "%s: Updated data for %d stock groups",
            DATA_UPDATE_FR,
            len(results),
            extra={"fr_id": DATA_UPDATE_FR, "groups_count": len(results)},
        )
        return results

    def export_xml(self, basket_names: Sequence[str] | None = None) -> str:
        """Export stock groups to native StrategyQuant X XML format."""
        baskets = self.list_baskets()
        target_names = (
            {n.strip().lower() for n in basket_names} if basket_names else None
        )

        root = ET.Element("Groups")
        for b in baskets:
            if target_names and b.name.lower() not in target_names:
                continue
            grp = ET.SubElement(root, "Group")
            grp.set("name", b.name)
            grp.set("system", "true" if b.system else "false")
            grp.set("desc", b.description)

            items_elem = ET.SubElement(grp, "Items")
            for m in b.items:
                item = ET.SubElement(items_elem, "Item")
                item.set("ticker", m.symbol)
                item.set("weight", str(m.weight))
                if m.date_from:
                    item.set("from", m.date_from)
                if m.date_to:
                    item.set("to", m.date_to)

        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
        logger.info(
            "%s: Exported %d stock groups to SQX XML",
            CSV_XML_FR,
            len(root),
            extra={"fr_id": CSV_XML_FR, "count": len(root)},
        )
        return str(xml_str)

    def import_xml(
        self, xml_content: str, overwrite: bool = False
    ) -> list[dict[str, Any]]:
        """Safely import SQX Stock Groups XML."""
        root = DefusedET.fromstring(xml_content)
        imported_list: list[dict[str, Any]] = []

        for grp in root.findall("Group"):
            name = grp.get("name", "").strip()
            if not name:
                continue

            existing = self.get_basket(name)
            if existing and not overwrite:
                continue

            members: list[dict[str, Any]] = []
            for item in grp.findall(".//Item"):
                ticker = item.get("ticker", "").strip().upper()
                if ticker:
                    members.append(
                        {
                            "symbol": ticker,
                            "weight": float(item.get("weight", 1.0)),
                            "date_from": item.get("from"),
                            "date_to": item.get("to"),
                        }
                    )

            saved = self.save_basket(
                {
                    "name": name,
                    "description": grp.get("desc", ""),
                    "system": grp.get("system", "false").lower() == "true",
                    "items": members,
                }
            )
            imported_list.append(
                {"id": saved.id, "name": saved.name, "items": len(saved.items)}
            )

        logger.info(
            "%s: Imported %d stock groups from XML",
            CSV_XML_FR,
            len(imported_list),
            extra={"fr_id": CSV_XML_FR, "count": len(imported_list)},
        )
        return imported_list

    def import_csv(self, basket_name: str, csv_text: str) -> BasketDefinition:
        """Import constituent stocks from CSV text into specified basket."""
        reader = csv.reader(io.StringIO(csv_text.strip()), delimiter=";")
        members: list[BasketMember] = []
        min_cols_for_date_to = 3
        for raw_row in reader:
            if not raw_row:
                continue
            # If comma delimited instead of semicolon
            row = (
                raw_row[0].split(",")
                if len(raw_row) == 1 and "," in raw_row[0]
                else raw_row
            )

            ticker = row[0].strip().upper()
            if not ticker or ticker.lower() in ("ticker", "symbol"):
                continue

            df_val = row[1].strip() if len(row) > 1 and row[1].strip() else None
            dt_val = (
                row[2].strip()
                if len(row) >= min_cols_for_date_to and row[2].strip()
                else None
            )
            members.append(
                BasketMember(symbol=ticker, date_from=df_val, date_to=dt_val)
            )

        saved = self.save_basket(
            {
                "name": basket_name,
                "description": f"Imported CSV basket ({basket_name})",
                "items": [m.to_dict() for m in members],
            }
        )
        logger.info(
            "%s: Imported %d members from CSV for basket %s",
            CSV_XML_FR,
            len(members),
            basket_name,
            extra={
                "fr_id": CSV_XML_FR,
                "basket": basket_name,
                "count": len(members),
            },
        )
        return saved

    def export_csv(self, basket_name: str) -> str:
        """Export basket constituent stocks to CSV format (Ticker;From;To)."""
        basket = self.get_basket(basket_name)
        if basket is None:
            raise KeyError(f"Basket '{basket_name}' not found.")

        lines = ["Ticker;From;To;Weight"]
        lines.extend(
            f"{m.symbol};{m.date_from or ''};{m.date_to or ''};{m.weight}"
            for m in basket.items
        )

        content = "\n".join(lines)
        logger.info(
            "%s: Exported %d members to CSV for basket %s",
            CSV_XML_FR,
            len(basket.items),
            basket_name,
            extra={
                "fr_id": CSV_XML_FR,
                "basket": basket_name,
                "count": len(basket.items),
            },
        )
        return content


def main() -> None:
    """Execute real-usage demonstration of BasketsCatalogService."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_baskets.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        data_svc = DataManagerDataService(db_path=db_file, data_dir=temp_path / "data")
        service = BasketsCatalogService(db_path=db_file, data_service=data_svc)
        seeded = service.ensure_default_baskets()
        print(f"Seeded {seeded} default stock groups")

        overview = service.get_baskets_overview()
        print(f"Baskets overview count: {len(overview)}")
        for item in overview:
            print(f" - {item.name}: total={item.total_count}, ready={item.is_ready}")

        csv_text = "NVDA;20200101;\nAMD;20200101;\nINTC;20200101;\n"
        custom = service.import_csv("Semiconductors", csv_text)
        print(f"Imported custom basket: {custom.name} ({len(custom.items)} items)")

        xml_out = service.export_xml(["Semiconductors"])
        print(f"Exported XML snippet:\n{xml_out[:180]}...")


if __name__ == "__main__":
    main()

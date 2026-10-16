"""Broker profile governance, broker stock lists, and XML migration.

Description:
    Provides domain logic for broker profiles (`datamgr_broker`) and broker-specific
    stock lists (`datamgr_broker_stock`), timezone defaults, symbol postfix mappings,
    SQX Broker XML import/export, and selective instrument/session component
    extraction from broker XML bundles without importing `sqlite3`.

Purpose:
    FEAT-DATAMGR-BROKER: Broker profiles, custom tickers, and platform configurations.

Key Capabilities:
    - FR-DATAMGR-BROKER-PROFILE-CRUD: Manage broker profiles and default
      system brokers.
      Associated: `BrokerProfilesService.list_brokers()`,
      `BrokerProfilesService.save_broker()`,
      `BrokerProfilesService.delete_brokers()`
      Logging: Emits INFO on creation, update, and deletion of broker
      profiles.
    - FR-DATAMGR-BROKER-STOCKS-MANAGEMENT: Manage broker stock lists and CSV
      transfer.
      Associated: `BrokerProfilesService.get_broker_stocks()`,
      `BrokerProfilesService.save_broker_stocks()`,
      `BrokerProfilesService.import_broker_stocks_csv()`
      Logging: Emits INFO on updating and importing broker stock lists.
    - FR-DATAMGR-BROKER-XML-TRANSFER: SQX XML transfer and selective
      component import.
      Associated: `BrokerProfilesService.export_brokers_xml()`,
      `BrokerProfilesService.import_brokers_xml()`,
      `BrokerProfilesService.import_xml_records()`
      Logging: Emits INFO on XML export, inspection, and selective
      component import.

Python API Usage:
    ```python
    from app.workspace.data_manager.broker import BrokerProfilesService

    service = BrokerProfilesService()
    brokers = service.list_brokers()
    for b in brokers:
        print(
            f"Broker: {b.name} (postfix='{b.postfix}', timezone='{b.broker_timezone}')"
        )
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.broker
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
from defusedxml.common import DefusedXmlException  # type: ignore[import-untyped]

from .data import DataManagerDataService
from .instruments import Instruments
from .sessions import SessionsCatalogService

__all__ = [
    "BrokerProfileRecord",
    "BrokerProfilesService",
    "XmlOverviewItem",
]

logger = get_logger(__name__)

PROFILE_CRUD_FR = "FR-DATAMGR-BROKER-PROFILE-CRUD"
STOCKS_MGMT_FR = "FR-DATAMGR-BROKER-STOCKS-MANAGEMENT"
XML_TRANSFER_FR = "FR-DATAMGR-BROKER-XML-TRANSFER"


@dataclass
class BrokerProfileRecord:
    """Represents a broker profile record matching RemoteBrokerRecord."""

    id: int
    name: str
    description: str = ""
    stockpicker_use: bool = False
    mt_use: bool = False
    broker_timezone: str = "UTC"
    postfix: str = ""
    is_system: bool = False
    stocks: list[str] = field(default_factory=list)
    customized_stocks: int = 0
    total_instruments: int = 0
    total_sessions: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert broker profile to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "stockpicker_use": self.stockpicker_use,
            "mt_use": self.mt_use,
            "broker_timezone": self.broker_timezone,
            "postfix": self.postfix,
            "is_system": self.is_system,
            "stocks": self.stocks,
            "customized_stocks": self.customized_stocks,
            "total_instruments": self.total_instruments,
            "total_sessions": self.total_sessions,
        }


@dataclass(frozen=True)
class XmlOverviewItem:
    """Represents an overview item discovered in imported XML."""

    name: str
    description: str = ""
    source: str = "XML"

    def to_dict(self) -> dict[str, Any]:
        """Convert XML overview item to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source,
        }


_DEFAULT_SEEDED_BROKERS: tuple[dict[str, Any], ...] = (
    {
        "name": "Default",
        "description": "Standard market default settings",
        "is_system": 1,
        "server_timezone": "UTC",
        "postfix": "",
        "mt_use": 0,
        "stockpicker_use": 1,
    },
    {
        "name": "MetaTrader 4",
        "description": "Standard MT4 terminal profile (Eastern European Time)",
        "is_system": 1,
        "server_timezone": "EET",
        "postfix": "",
        "mt_use": 1,
        "stockpicker_use": 0,
    },
    {
        "name": "MetaTrader 5",
        "description": "Standard MT5 terminal profile (Eastern European Time)",
        "is_system": 1,
        "server_timezone": "EET",
        "postfix": "",
        "mt_use": 1,
        "stockpicker_use": 0,
    },
    {
        "name": "Interactive Brokers",
        "description": "Interactive Brokers TWS feed (US Eastern Time)",
        "is_system": 1,
        "server_timezone": "America/New_York",
        "postfix": "",
        "mt_use": 0,
        "stockpicker_use": 1,
    },
    {
        "name": "Dukascopy",
        "description": "Dukascopy Swiss Forex feed (UTC)",
        "is_system": 1,
        "server_timezone": "UTC",
        "postfix": "",
        "mt_use": 0,
        "stockpicker_use": 0,
    },
    {
        "name": "Binance",
        "description": "Binance Spot and Futures (UTC)",
        "is_system": 1,
        "server_timezone": "UTC",
        "postfix": "",
        "mt_use": 0,
        "stockpicker_use": 0,
    },
)


def _resolve_broker_is_system(
    payload: Mapping[str, Any], existing: BrokerProfileRecord | None
) -> int:
    """Determine is_system flag preserving existing state if omitted."""
    if "is_system" in payload:
        return 1 if payload["is_system"] else 0
    if existing is not None:
        return 1 if existing.is_system else 0
    return 0


def _find_target_broker(
    brokers: Sequence[BrokerProfileRecord],
    target_id: Any,
    clean_name: str,
) -> tuple[int | None, BrokerProfileRecord | None]:
    """Find existing broker by ID or name."""
    if target_id is not None:
        tid = int(target_id)
        for b in brokers:
            if b.id == tid:
                return tid, b
    clean_lower = clean_name.lower()
    for b in brokers:
        if b.name.strip().lower() == clean_lower:
            return b.id, b
    return (int(target_id) if target_id is not None else None), None


class BrokerProfilesService:
    """Service governing broker profiles, stock lists, and XML migrations."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        instruments_service: Instruments | None = None,
        sessions_service: SessionsCatalogService | None = None,
        data_service: DataManagerDataService | None = None,
    ) -> None:
        """Initialize broker profiles service with optional catalog dependencies."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.instruments_service = instruments_service
        self.sessions_service = sessions_service
        self.data_service = data_service

    def ensure_default_brokers(self) -> int:
        """Seed default system broker profiles if table is empty."""
        with resolve_connection(self.db_path) as conn:
            existing = count_rows(conn, "datamgr_broker")
            if existing > 0:
                return 0

            seeded = 0
            now_iso = datetime.now(UTC).isoformat()
            for item in _DEFAULT_SEEDED_BROKERS:
                data = dict(item)
                data["created_at_utc"] = now_iso
                data["updated_at_utc"] = now_iso
                insert_row(conn, "datamgr_broker", data)
                seeded += 1

        logger.info(
            "%s: Seeded %d default broker profiles",
            PROFILE_CRUD_FR,
            seeded,
            extra={"fr_id": PROFILE_CRUD_FR, "seeded": seeded},
        )
        return seeded

    def list_brokers(self) -> list[BrokerProfileRecord]:
        """List all broker profiles with correlated stock counts and associations."""
        with resolve_connection(self.db_path) as conn:
            broker_rows = read_rows(conn, "datamgr_broker", order_by="name ASC")
            stock_rows = read_rows(conn, "datamgr_broker_stock")
            instrument_rows = read_rows(conn, "datamgr_instruments")
            session_rows = read_rows(conn, "datamgr_sessions")

        # Map stocks by broker_id
        stocks_by_broker: dict[int, list[str]] = {}
        for s in stock_rows:
            bid = int(s.get("BROKER_ID", 0))
            if bid not in stocks_by_broker:
                stocks_by_broker[bid] = []
            stocks_by_broker[bid].append(str(s.get("TICKER", "")))

        # Count instruments and sessions by broker_id
        inst_counts: dict[int, int] = {}
        for i in instrument_rows:
            bid = int(i.get("broker_id", -1))
            inst_counts[bid] = inst_counts.get(bid, 0) + 1

        sess_counts: dict[int, int] = {}
        for ss in session_rows:
            bid = int(ss.get("broker_id", -1))
            sess_counts[bid] = sess_counts.get(bid, 0) + 1

        brokers: list[BrokerProfileRecord] = []
        for r in broker_rows:
            bid = int(r.get("id", 0))
            stocks = stocks_by_broker.get(bid, [])
            brokers.append(
                BrokerProfileRecord(
                    id=bid,
                    name=str(r.get("name", "")),
                    description=str(r.get("description", "")),
                    stockpicker_use=bool(r.get("stockpicker_use", False)),
                    mt_use=bool(r.get("mt_use", False)),
                    broker_timezone=str(r.get("server_timezone", "UTC")),
                    postfix=str(r.get("postfix", "")),
                    is_system=bool(r.get("is_system", False)),
                    stocks=stocks,
                    customized_stocks=len(stocks),
                    total_instruments=inst_counts.get(bid, 0),
                    total_sessions=sess_counts.get(bid, 0),
                )
            )
        return brokers

    def get_broker(self, broker_id: int) -> BrokerProfileRecord | None:
        """Retrieve a broker profile by its ID."""
        for b in self.list_brokers():
            if b.id == broker_id:
                return b
        return None

    def save_broker(self, payload: Mapping[str, Any]) -> BrokerProfileRecord:
        """Create or update a broker profile record."""
        clean_name = str(payload.get("name", "")).strip()
        if not clean_name:
            raise ValueError("Broker name is required.")

        desc = str(payload.get("description") or payload.get("desc") or "")
        server_tz = str(
            payload.get("server_timezone")
            or payload.get("broker_timezone")
            or payload.get("mt_timezone")
            or "UTC"
        )

        all_brokers = self.list_brokers()
        target_id, existing_broker = _find_target_broker(
            all_brokers, payload.get("id"), clean_name
        )
        is_sys = _resolve_broker_is_system(payload, existing_broker)

        now_iso = datetime.now(UTC).isoformat()
        row_data: dict[str, Any] = {
            "name": clean_name,
            "description": desc,
            "stockpicker_use": 1 if payload.get("stockpicker_use") else 0,
            "mt_use": 1 if payload.get("mt_use") else 0,
            "server_timezone": server_tz,
            "postfix": str(payload.get("postfix", "")),
            "is_system": is_sys,
            "updated_at_utc": now_iso,
        }

        with resolve_connection(self.db_path) as conn:
            if target_id is not None and int(target_id) > 0:
                row_data["id"] = int(target_id)
                update_row_by_pk(
                    conn, "datamgr_broker", {"id": int(target_id)}, row_data
                )
                broker_id = int(target_id)
            else:
                row_data["created_at_utc"] = now_iso
                row_data.pop("id", None)
                inserted = insert_row(conn, "datamgr_broker", row_data)
                broker_id = int(inserted)

        # Handle stocks if supplied
        if "stocks" in payload:
            raw_stocks = payload["stocks"]
            if isinstance(raw_stocks, list):
                self.save_broker_stocks(broker_id, raw_stocks)

        broker = self.get_broker(broker_id)
        if broker is None:
            raise RuntimeError("Failed to retrieve saved broker profile.")

        logger.info(
            "%s: Saved broker profile name=%s id=%d",
            PROFILE_CRUD_FR,
            broker.name,
            broker.id,
            extra={
                "fr_id": PROFILE_CRUD_FR,
                "broker_name": broker.name,
                "id": broker.id,
            },
        )
        return broker

    def delete_brokers(self, broker_ids: Sequence[int]) -> int:
        """Delete non-system broker profiles by ID."""
        deleted_count = 0
        with resolve_connection(self.db_path) as conn:
            for bid in broker_ids:
                rows = read_rows(conn, "datamgr_broker", where={"id": bid}, limit=1)
                if not rows or bool(rows[0].get("is_system", False)):
                    continue

                delete_rows(conn, "datamgr_broker_stock", where={"BROKER_ID": bid})
                delete_row_by_pk(conn, "datamgr_broker", {"id": bid})
                deleted_count += 1

        logger.info(
            "%s: Deleted %d non-system broker profiles",
            PROFILE_CRUD_FR,
            deleted_count,
            extra={"fr_id": PROFILE_CRUD_FR, "deleted_count": deleted_count},
        )
        return deleted_count

    def get_broker_stocks(self, broker_id: int) -> list[str]:
        """Retrieve stock tickers configured for a broker."""
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn, "datamgr_broker_stock", where={"BROKER_ID": broker_id}
            )
        return [str(r.get("TICKER", "")) for r in rows if r.get("TICKER")]

    def save_broker_stocks(self, broker_id: int, stocks: Sequence[str]) -> int:
        """Overwrite stock tickers configured for a broker."""
        with resolve_connection(self.db_path) as conn:
            delete_rows(conn, "datamgr_broker_stock", where={"BROKER_ID": broker_id})
            count = 0
            for ticker in stocks:
                clean = ticker.strip().upper()
                if clean:
                    insert_row(
                        conn,
                        "datamgr_broker_stock",
                        {"TICKER": clean, "BROKER_ID": broker_id},
                    )
                    count += 1

        logger.info(
            "%s: Saved %d stocks for broker id=%d",
            STOCKS_MGMT_FR,
            count,
            broker_id,
            extra={
                "fr_id": STOCKS_MGMT_FR,
                "broker_id": broker_id,
                "count": count,
            },
        )
        return count

    def import_broker_stocks_csv(self, broker_id: int, csv_content: str) -> int:
        """Import tickers from CSV content and replace broker stocks."""
        reader = csv.reader(io.StringIO(csv_content.strip()))
        tickers: list[str] = []
        for row in reader:
            if not row:
                continue
            ticker = row[0].strip().upper()
            if ticker and ticker.lower() not in ("ticker", "symbol"):
                tickers.append(ticker)
        return self.save_broker_stocks(broker_id, tickers)

    def export_broker_stocks_csv(self, broker_id: int) -> str:
        """Export broker stock tickers as newline-separated text."""
        stocks = self.get_broker_stocks(broker_id)
        content = "\n".join(stocks)
        logger.info(
            "%s: Exported %d stocks to CSV for broker id=%d",
            STOCKS_MGMT_FR,
            len(stocks),
            broker_id,
            extra={
                "fr_id": STOCKS_MGMT_FR,
                "broker_id": broker_id,
                "count": len(stocks),
            },
        )
        return content

    def export_brokers_xml(self, broker_ids: Sequence[int] | None = None) -> str:
        """Export broker profiles to native StrategyQuant X XML format."""
        brokers = self.list_brokers()
        target_ids = set(broker_ids) if broker_ids else None

        root = ET.Element("Brokers")
        for b in brokers:
            if target_ids and b.id not in target_ids:
                continue
            item = ET.SubElement(root, "Broker")
            item.set("id", str(b.id))
            item.set("name", b.name)
            item.set("description", b.description)
            item.set("serverTimezone", b.broker_timezone)
            item.set("postfix", b.postfix)
            item.set("isSystem", "true" if b.is_system else "false")
            item.set("mtUse", "true" if b.mt_use else "false")
            item.set("stockpickerUse", "true" if b.stockpicker_use else "false")

            stocks_elem = ET.SubElement(item, "Stocks")
            for ticker in b.stocks:
                st = ET.SubElement(stocks_elem, "Stock")
                st.set("ticker", ticker)

        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
        logger.info(
            "%s: Exported %d broker profiles to SQX XML",
            XML_TRANSFER_FR,
            len(root),
            extra={"fr_id": XML_TRANSFER_FR, "count": len(root)},
        )
        return str(xml_str)

    def import_brokers_xml(self, xml_content: str) -> list[BrokerProfileRecord]:
        """Safely import SQX Brokers XML."""
        root = DefusedET.fromstring(xml_content)
        imported: list[BrokerProfileRecord] = []

        for item in root.findall("Broker"):
            name = item.get("name", "").strip()
            if not name:
                continue

            stocks: list[str] = []
            for st in item.findall(".//Stock"):
                tk = st.get("ticker", "").strip().upper()
                if tk:
                    stocks.append(tk)

            saved = self.save_broker(
                {
                    "name": name,
                    "description": item.get("description", ""),
                    "server_timezone": item.get("serverTimezone", "UTC"),
                    "postfix": item.get("postfix", ""),
                    "is_system": item.get("isSystem", "false").lower() == "true",
                    "mt_use": item.get("mtUse", "false").lower() == "true",
                    "stockpicker_use": item.get("stockpickerUse", "false").lower()
                    == "true",
                    "stocks": stocks,
                }
            )
            imported.append(saved)

        logger.info(
            "%s: Imported %d broker profiles from XML",
            XML_TRANSFER_FR,
            len(imported),
            extra={"fr_id": XML_TRANSFER_FR, "count": len(imported)},
        )
        return imported

    def inspect_xml_overview(
        self, xml_content: str, kind: str
    ) -> list[XmlOverviewItem]:
        """Inspect XML bundle and return overview of available items."""
        try:
            root = DefusedET.fromstring(xml_content)
        except DefusedXmlException, ET.ParseError, ValueError, TypeError:
            return []

        clean_kind = kind.strip().lower()

        if "session" in clean_kind:
            return [
                XmlOverviewItem(
                    name=s.get("name", ""),
                    description=s.get("description", ""),
                    source="Sessions XML",
                )
                for s in root.findall(".//Session")
            ]
        if "instrument" in clean_kind:
            return [
                XmlOverviewItem(
                    name=inst.get("symbol", ""),
                    description=inst.get("description", ""),
                    source="Instruments XML",
                )
                for inst in root.findall(".//Instrument")
            ]
        return [
            XmlOverviewItem(
                name=b.get("name", ""),
                description=b.get("description", ""),
                source="Brokers XML",
            )
            for b in root.findall(".//Broker")
        ]

    def import_xml_records(
        self,
        xml_content: str,
        kind: str,
        broker_id: int,
        postfix: str,
        selected_names: Sequence[str],
    ) -> int:
        """Selectively import instruments or sessions with broker ID."""
        clean_kind = kind.strip().lower()
        selected_set = {n.strip().lower() for n in selected_names}
        imported_count = 0

        if "instrument" in clean_kind and self.instruments_service:
            root = DefusedET.fromstring(xml_content)
            for item in root.findall(".//Instrument"):
                sym = item.get("symbol", "").strip()
                if not sym or sym.lower() not in selected_set:
                    continue
                target_sym = f"{sym}{postfix}".strip().upper()
                self.instruments_service.save_instrument(
                    {
                        "symbol": target_sym,
                        "description": item.get("description", ""),
                        "broker_id": broker_id,
                        "tick_size": float(item.get("tickSize", 0.0001)),
                        "point_value": float(item.get("pointValue", 100000.0)),
                    }
                )
                imported_count += 1
        elif "session" in clean_kind and self.sessions_service:
            root = DefusedET.fromstring(xml_content)
            for s in root.findall(".//Session"):
                name = s.get("name", "").strip()
                if not name or name.lower() not in selected_set:
                    continue
                target_name = f"{name}{postfix}".strip()
                window_nodes = s.findall(".//Window")
                if not window_nodes:
                    window_nodes = s.findall(".//SessionElement")
                windows = [
                    {
                        "day_from": (
                            we.get("dayFrom")
                            or we.get("day_from")
                            or we.get("startDay")
                            or we.get("Day")
                            or "Mon"
                        ),
                        "day_to": (
                            we.get("dayTo")
                            or we.get("day_to")
                            or we.get("endDay")
                            or we.get("Day")
                            or "Mon"
                        ),
                        "start_time": (
                            we.get("startTime")
                            or we.get("start_time")
                            or we.get("StartTime")
                            or "00:00"
                        ),
                        "end_time": (
                            we.get("endTime")
                            or we.get("end_time")
                            or we.get("EndTime")
                            or "23:59"
                        ),
                        "session_type": (
                            we.get("sessionType")
                            or we.get("session_type")
                            or we.get("SessionType")
                            or "Regular"
                        ),
                        "eod": (
                            we.get("eod") or we.get("Eod") or we.get("seoc") or "false"
                        ).lower()
                        in ("true", "1", "yes"),
                    }
                    for we in window_nodes
                ]
                holidays = [
                    {
                        "date_str": (
                            he.get("date")
                            or he.get("Date")
                            or he.findtext("Date")
                            or ""
                        ),
                        "description": (
                            he.get("description")
                            or he.get("Description")
                            or he.findtext("Description")
                            or ""
                        ),
                    }
                    for he in s.findall(".//Holiday")
                ]
                self.sessions_service.save_session(
                    {
                        "name": target_name,
                        "description": s.get("description", ""),
                        "broker_id": broker_id,
                        "timezone": s.get("timezone", "UTC"),
                        "windows_json": json.dumps(windows),
                        "holidays_json": json.dumps(holidays),
                    }
                )
                imported_count += 1

        logger.info(
            "%s: Selectively imported %d %s records for broker id=%d",
            XML_TRANSFER_FR,
            imported_count,
            kind,
            broker_id,
            extra={
                "fr_id": XML_TRANSFER_FR,
                "count": imported_count,
                "kind": kind,
                "broker_id": broker_id,
            },
        )
        return imported_count

    def trigger_broker_data_update(self, broker_id: int) -> dict[str, Any]:
        """Provision or synchronize historical datasets for all broker stocks."""
        stocks = self.get_broker_stocks(broker_id)
        updated_count = 0
        if self.data_service:
            for s in stocks:
                self.data_service.import_dataset(
                    {"symbol": s, "source": "file", "timeframe": "M1"}
                )
                updated_count += 1

        logger.info(
            "%s: Triggered data update for broker id=%d (%d stocks)",
            PROFILE_CRUD_FR,
            broker_id,
            updated_count,
            extra={
                "fr_id": PROFILE_CRUD_FR,
                "broker_id": broker_id,
                "stocks_updated": updated_count,
            },
        )
        return {
            "broker_id": broker_id,
            "updated_count": updated_count,
            "status": "completed",
        }


def main() -> None:
    """Execute real-usage demonstration of BrokerProfilesService."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_broker.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        service = BrokerProfilesService(db_path=db_file)
        seeded = service.ensure_default_brokers()
        print(f"Seeded {seeded} default broker profiles")

        brokers = service.list_brokers()
        print(f"Total brokers: {len(brokers)}")
        for b in brokers:
            print(f" - {b.name} (tz={b.broker_timezone}, sys={b.is_system})")

        custom_stocks = ["AAPL", "MSFT", "GOOGL"]
        service.save_broker_stocks(1, custom_stocks)
        loaded_stocks = service.get_broker_stocks(1)
        print(f"Broker 1 stocks: {loaded_stocks}")

        xml_out = service.export_brokers_xml([1])
        print(f"Exported XML snippet:\n{xml_out[:180]}...")


if __name__ == "__main__":
    main()

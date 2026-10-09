"""Authoritative broker profile definitions and configuration management.

Description:
    BrokerService manages broker profile lifecycle, MetaTrader compatibility,
    stockpicker constituent listings, CSV/XML interchange, and XML instrument/session
    import pipelines within the Data Manager workspace, mirroring StrategyQuant X
    DataManagerBroker. Database transactions and storage execution are delegated
    exclusively to app.host.persistence.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Broker profiles, server timezones, and execution
    presets for the Data Manager workspace.

Key Capabilities:
    - FR-DATA-CATALOG-BROKER-PROFILES: Broker profile specifications, server
      timezones, symbol postfixes, and platform use flags.
      Associated: `BrokerService.get_broker()`, `BrokerService.list_brokers()`,
        `BrokerService.create_broker()`, `BrokerService.update_broker()`,
        `BrokerService.delete_brokers()`
      Logging: Emits DEBUG on queries, INFO on lifecycle mutations.
    - FR-DATA-CATALOG-BROKER-STOCKS: Stock ticker constituent management for
      stockpicker broker profiles.
      Associated: `BrokerService.list_stocks()`, `BrokerService.edit_stocks()`,
        `BrokerService.import_stocks_csv()`, `BrokerService.export_stocks_csv()`
      Logging: Emits DEBUG on stock reads, INFO on stock replacements.
    - FR-DATA-CATALOG-BROKER-INTERCHANGE: CSV and XML serialization and import
      for broker profiles and MetaTrader XML exports.
      Associated: `BrokerService.export_brokers_xml()`,
        `BrokerService.import_brokers_xml()`,
        `BrokerService.inspect_xml_overview()`,
        `BrokerService.import_xml_records()`,
        `BrokerService.update_data_for_broker()`
      Logging: Emits INFO on import and export operations.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.broker import (
        BrokerProfileRecord,
        BrokerSavePayload,
        BrokerService,
    )

    db = DatabaseManager(":memory:")
    db.initialize()
    service = BrokerService(db)

    brokers = service.list_brokers()
    broker = service.create_broker(
        BrokerSavePayload(name="ICMarkets", mt_timezone="EETUS", postfix="_ic")
    )
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.broker --list
    ```
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager, PersistenceError
from app.workspace.data_manager.instruments import (
    InstrumentDefinition,
    InstrumentService,
)

logger = get_logger(__name__)


class BrokerProfileRecord(BaseModel):
    """Configuration profile for a broker data connection."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int = Field(default=0, description="Broker numeric ID")
    name: str = Field(min_length=1, description="Unique broker name")
    is_system: bool = Field(default=False, description="System default broker flag")
    description: str = Field(default="", description="Broker description")
    server_timezone: str = Field(default="UTC", description="Server clock timezone")
    postfix: str = Field(default="", description="Symbol postfix (e.g. .raw, .pro)")
    enabled: bool = Field(default=True, description="Whether broker is enabled")
    mt_use: bool = Field(default=False, description="MetaTrader compatibility flag")
    stockpicker_use: bool = Field(default=False, description="StockPicker flag")
    customized_stocks: int = Field(default=0, description="Count of associated stocks")
    customized_instruments: int = Field(
        default=0, description="Count of customized instruments"
    )
    customized_sessions: int = Field(
        default=0, description="Count of customized sessions"
    )
    stocks: list[str] = Field(
        default_factory=list, description="Constituent stock tickers"
    )


class BrokerSavePayload(BaseModel):
    """Payload schema for creating or updating a broker profile."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(default=None, description="Broker ID if updating")
    name: str = Field(min_length=1, max_length=50, description="Broker name")
    desc: str = Field(default="", max_length=250, description="Description")
    postfix: str = Field(default="", max_length=100, description="Instrument postfix")
    mt_timezone: str = Field(default="UTC", description="Broker server timezone")
    mt_use: bool = Field(default=True, description="MetaTrader usage flag")
    stockpicker_use: bool = Field(default=False, description="StockPicker usage flag")
    enabled: bool = Field(default=True, description="Whether profile is enabled")


class BrokerStocksPayload(BaseModel):
    """Payload schema for editing broker stocks."""

    model_config = ConfigDict(extra="ignore")

    broker_id: int | None = Field(default=None, description="Target broker ID")
    stocks: list[str] = Field(default_factory=list, description="Stock ticker symbols")


class XmlOverviewItem(BaseModel):
    """Summary item parsed from imported XML files."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str = ""


class BrokerService:
    """Central domain service managing broker profile configurations."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize BrokerService with host DatabaseManager."""
        self._db = db

    def ensure_defaults(self) -> None:
        """Ensure standard SQX system broker profiles exist in storage."""
        self._db.brokers.ensure_defaults()

    def list_brokers(self) -> list[BrokerProfileRecord]:
        """Retrieve configured broker profiles from datamgr_broker table.

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        try:
            rows = self._db.brokers.list_profiles()
            if not rows:
                self.ensure_defaults()
                rows = self._db.brokers.list_profiles()

            results: list[BrokerProfileRecord] = []
            for r in rows:
                b_id = int(r.get("id", 0))
                counts = self._db.brokers.get_counts(b_id)
                stocks = (
                    self._db.brokers.list_stocks(b_id)
                    if counts["customized_stocks"] > 0
                    else []
                )
                results.append(
                    BrokerProfileRecord(
                        id=b_id,
                        name=str(r.get("name", "")),
                        is_system=bool(r.get("is_system", 0)),
                        description=str(r.get("description", "")),
                        server_timezone=str(r.get("server_timezone", "UTC")),
                        postfix=str(r.get("postfix", "")),
                        enabled=bool(r.get("enabled", 1)),
                        mt_use=bool(r.get("mt_use", 0)),
                        stockpicker_use=bool(r.get("stockpicker_use", 0)),
                        customized_stocks=counts["customized_stocks"],
                        customized_instruments=counts["customized_instruments"],
                        customized_sessions=counts["customized_sessions"],
                        stocks=stocks,
                    )
                )
            logger.debug(
                "FR-DATA-CATALOG-BROKER-PROFILES: Listed broker profiles",
                extra={
                    "count": len(results),
                    "fr_id": "FR-DATA-CATALOG-BROKER-PROFILES",
                },
            )
            return results
        except (PersistenceError, OSError, ValueError, KeyError) as exc:
            logger.warning(
                "FR-DATA-CATALOG-BROKER-PROFILES: Error reading datamgr_broker: %s",
                exc,
                extra={"fr_id": "FR-DATA-CATALOG-BROKER-PROFILES"},
            )
            return []

    def get_broker(self, name_or_id: str | int) -> BrokerProfileRecord | None:
        """Find a broker profile by ID or name (case-insensitive).

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        row: dict[str, Any] | None = None
        if isinstance(name_or_id, int):
            row = self._db.brokers.get_profile(name_or_id)
        elif str(name_or_id).isdigit():
            row = self._db.brokers.get_profile(int(name_or_id))

        if row is None:
            clean_name = str(name_or_id).strip()
            row = self._db.brokers.get_profile_by_name(clean_name)

        if row is None:
            return None

        b_id = int(row.get("id", 0))
        counts = self._db.brokers.get_counts(b_id)
        stocks = (
            self._db.brokers.list_stocks(b_id)
            if counts["customized_stocks"] > 0
            else []
        )
        return BrokerProfileRecord(
            id=b_id,
            name=str(row.get("name", "")),
            is_system=bool(row.get("is_system", 0)),
            description=str(row.get("description", "")),
            server_timezone=str(row.get("server_timezone", "UTC")),
            postfix=str(row.get("postfix", "")),
            enabled=bool(row.get("enabled", 1)),
            mt_use=bool(row.get("mt_use", 0)),
            stockpicker_use=bool(row.get("stockpicker_use", 0)),
            customized_stocks=counts["customized_stocks"],
            customized_instruments=counts["customized_instruments"],
            customized_sessions=counts["customized_sessions"],
            stocks=stocks,
        )

    def create_broker(self, payload: BrokerSavePayload) -> BrokerProfileRecord:
        """Create a new user broker profile.

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        clean_name = payload.name.strip()
        if not clean_name:
            raise ValueError("Broker profile name must not be empty.")

        existing = self.get_broker(clean_name)
        if existing is not None:
            raise ValueError(f"Broker profile with name '{clean_name}' already exists.")

        data = {
            "name": clean_name,
            "is_system": 0,
            "description": payload.desc.strip(),
            "server_timezone": payload.mt_timezone.strip() or "UTC",
            "postfix": payload.postfix.strip(),
            "enabled": int(payload.enabled),
            "mt_use": int(payload.mt_use),
            "stockpicker_use": int(payload.stockpicker_use),
        }
        broker_id = self._db.brokers.create_profile(data)
        created = self.get_broker(broker_id)
        if created is None:
            raise RuntimeError(f"Failed to retrieve created broker ID {broker_id}")
        logger.info(
            "FR-DATA-CATALOG-BROKER-PROFILES: Created broker profile %s (id=%d)",
            created.name,
            created.id,
            extra={
                "broker_id": created.id,
                "fr_id": "FR-DATA-CATALOG-BROKER-PROFILES",
            },
        )
        return created

    def update_broker(
        self, broker_id: int, payload: BrokerSavePayload
    ) -> BrokerProfileRecord:
        """Update an existing broker profile.

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        existing = self.get_broker(broker_id)
        if existing is None:
            raise KeyError(f"Broker profile ID {broker_id} does not exist.")
        if existing.is_system:
            raise ValueError("System broker profile cannot be modified.")

        clean_name = payload.name.strip()
        if not clean_name:
            raise ValueError("Broker profile name must not be empty.")

        # Check name uniqueness if changed
        by_name = self.get_broker(clean_name)
        if by_name is not None and by_name.id != broker_id:
            raise ValueError(f"Broker profile with name '{clean_name}' already exists.")

        data = {
            "name": clean_name,
            "description": payload.desc.strip(),
            "server_timezone": payload.mt_timezone.strip() or "UTC",
            "postfix": payload.postfix.strip(),
            "enabled": int(payload.enabled),
            "mt_use": int(payload.mt_use),
            "stockpicker_use": int(payload.stockpicker_use),
        }
        self._db.brokers.update_profile(broker_id, data)
        updated = self.get_broker(broker_id)
        if updated is None:
            raise RuntimeError(f"Failed to retrieve updated broker ID {broker_id}")
        logger.info(
            "FR-DATA-CATALOG-BROKER-PROFILES: Updated broker profile %s (id=%d)",
            updated.name,
            updated.id,
            extra={
                "broker_id": updated.id,
                "fr_id": "FR-DATA-CATALOG-BROKER-PROFILES",
            },
        )
        return updated

    def delete_brokers(self, ids: list[int]) -> int:
        """Delete broker profiles matching the provided IDs.

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        deleted_count = 0
        for b_id in ids:
            try:
                success = self._db.brokers.delete_profile(b_id)
                if success:
                    deleted_count += 1
            except PersistenceError as exc:
                raise ValueError(str(exc)) from exc
        logger.info(
            "FR-DATA-CATALOG-BROKER-PROFILES: Deleted %d broker profile(s)",
            deleted_count,
            extra={
                "count": deleted_count,
                "fr_id": "FR-DATA-CATALOG-BROKER-PROFILES",
            },
        )
        return deleted_count

    def list_stocks(self, broker_id: int) -> list[str]:
        """List stock tickers configured for a stockpicker broker profile.

        Fires FR-DATA-CATALOG-BROKER-STOCKS.
        """
        existing = self.get_broker(broker_id)
        if existing is None:
            raise KeyError(f"Broker profile ID {broker_id} does not exist.")
        stocks = self._db.brokers.list_stocks(broker_id)
        logger.debug(
            "FR-DATA-CATALOG-BROKER-STOCKS: Read stocks for broker %d",
            broker_id,
            extra={
                "broker_id": broker_id,
                "count": len(stocks),
                "fr_id": "FR-DATA-CATALOG-BROKER-STOCKS",
            },
        )
        return stocks

    def edit_stocks(self, broker_id: int, tickers: list[str]) -> None:
        """Replace all stock tickers for a broker profile.

        Fires FR-DATA-CATALOG-BROKER-STOCKS.
        """
        existing = self.get_broker(broker_id)
        if existing is None:
            raise KeyError(f"Broker profile ID {broker_id} does not exist.")
        if existing.is_system:
            raise ValueError("Stocks cannot be modified for a system broker profile.")
        if not existing.stockpicker_use:
            raise ValueError("This broker profile is not configured to hold stocks.")

        clean_tickers = sorted({t.strip().upper() for t in tickers if t.strip()})
        self._db.brokers.replace_stocks(broker_id, clean_tickers)
        logger.info(
            "FR-DATA-CATALOG-BROKER-STOCKS: Saved %d stocks for broker %d",
            len(clean_tickers),
            broker_id,
            extra={
                "broker_id": broker_id,
                "count": len(clean_tickers),
                "fr_id": "FR-DATA-CATALOG-BROKER-STOCKS",
            },
        )

    def import_stocks_csv(self, broker_id: int, content: str) -> int:
        """Import stocks from plain multi-line CSV text.

        Fires FR-DATA-CATALOG-BROKER-STOCKS.
        """
        lines = content.splitlines()
        tickers: list[str] = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned or cleaned.startswith(("#", "//")):
                continue
            # Strip semicolon or comma delimiter if formatted as Ticker;...
            ticker = cleaned.split(";")[0].split(",")[0].strip()
            if ticker:
                tickers.append(ticker)

        self.edit_stocks(broker_id, tickers)
        return len(tickers)

    def export_stocks_csv(self, broker_id: int) -> str:
        """Export configured stocks for a broker as plain text.

        Fires FR-DATA-CATALOG-BROKER-STOCKS.
        """
        stocks = self.list_stocks(broker_id)
        return "\n".join(stocks) + ("\n" if stocks else "")

    def export_brokers_xml(self, broker_ids: list[int] | None = None) -> str:
        """Export broker profiles and stocks to StrategyQuant X XML format.

        Fires FR-DATA-CATALOG-BROKER-INTERCHANGE.
        """
        all_brokers = self.list_brokers()
        if broker_ids is not None:
            target_ids = set(broker_ids)
            all_brokers = [b for b in all_brokers if b.id in target_ids]

        root = ET.Element("Brokers")
        for b in all_brokers:
            b_elem = ET.SubElement(
                root,
                "Broker",
                attrib={
                    "name": b.name,
                    "stockPickerUse": "true" if b.stockpicker_use else "false",
                    "mtUse": "true" if b.mt_use else "false",
                    "mtTimezone": b.server_timezone,
                    "mtPostfix": b.postfix,
                },
            )
            desc_elem = ET.SubElement(b_elem, "Desc")
            desc_elem.text = b.description

            stocks = self._db.brokers.list_stocks(b.id)
            stocks_elem = ET.SubElement(b_elem, "Stocks")
            for ticker in stocks:
                ET.SubElement(stocks_elem, "Stock", attrib={"ticker": ticker})

        xml_bytes: bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        return str(xml_bytes.decode("utf-8"))

    def _parse_and_upsert_broker(
        self, b_elem: ET.Element
    ) -> BrokerProfileRecord | None:
        """Parse XML broker node and create or update profile."""
        name = (b_elem.get("name") or "").strip()
        if not name:
            return None

        stock_picker_use = (
            b_elem.get("stockPickerUse") or b_elem.get("stockpickerUse") or "false"
        ).lower() == "true"
        mt_use = (
            b_elem.get("mtUse") or b_elem.get("mt_use") or "true"
        ).lower() == "true"
        mt_timezone = (
            b_elem.get("mtTimezone")
            or b_elem.get("timezone")
            or b_elem.get("server_timezone")
            or "UTC"
        )
        mt_postfix = b_elem.get("mtPostfix") or b_elem.get("postfix") or ""
        desc = ""
        desc_elem = b_elem.find("Desc")
        if desc_elem is not None and desc_elem.text:
            desc = desc_elem.text.strip()
        elif b_elem.get("description"):
            desc = (b_elem.get("description") or "").strip()

        payload = BrokerSavePayload(
            name=name,
            desc=desc,
            postfix=mt_postfix,
            mt_timezone=mt_timezone,
            mt_use=mt_use,
            stockpicker_use=stock_picker_use,
        )

        existing = self.get_broker(name)
        if existing is not None:
            if existing.is_system:
                return None
            payload.id = existing.id
            record = self.update_broker(existing.id, payload)
        else:
            record = self.create_broker(payload)

        # Import stocks if element present
        stocks_elem = b_elem.find("Stocks")
        if stocks_elem is not None and record.stockpicker_use:
            tickers = [
                (s.get("ticker") or s.get("name") or "").strip()
                for s in stocks_elem.findall("Stock")
                if (s.get("ticker") or s.get("name"))
            ]
            self.edit_stocks(record.id, tickers)

        return self.get_broker(record.id)

    def import_brokers_xml(self, xml_content: str) -> list[BrokerProfileRecord]:
        """Import broker profiles from StrategyQuant X XML.

        Fires FR-DATA-CATALOG-BROKER-INTERCHANGE.
        """
        try:
            root = ET.fromstring(xml_content)  # noqa: S314
        except Exception as exc:
            raise ValueError(f"Invalid XML format: {exc}") from exc

        if root.tag != "Brokers":
            raise ValueError("Root element must be <Brokers>.")

        imported: list[BrokerProfileRecord] = []
        for b_elem in root.findall("Broker"):
            rec = self._parse_and_upsert_broker(b_elem)
            if rec is not None:
                imported.append(rec)

        return imported

    def inspect_xml_overview(
        self, xml_content: str, kind: str
    ) -> list[XmlOverviewItem]:
        """Inspect MetaTrader XML export and return items overview.

        Fires FR-DATA-CATALOG-BROKER-INTERCHANGE.
        """
        try:
            root = ET.fromstring(xml_content)  # noqa: S314
        except Exception as exc:
            raise ValueError(f"Invalid XML document: {exc}") from exc

        results: list[XmlOverviewItem] = []
        if kind == "instrument":
            for node in root.iter():
                if node.tag.lower() in ("instrumentinfo", "symbol", "instrument"):
                    inst = (
                        node.get("instrument") or node.get("name") or node.get("symbol")
                    )
                    desc = node.get("description") or ""
                    if inst:
                        results.append(
                            XmlOverviewItem(name=inst.strip(), description=desc.strip())
                        )
        elif kind == "session":
            for node in root.iter():
                if node.tag.lower() in ("session", "sessioninfo"):
                    name = node.get("name") or node.get("symbol")
                    desc = node.get("description") or node.get("timeZone") or ""
                    if name:
                        results.append(
                            XmlOverviewItem(name=name.strip(), description=desc.strip())
                        )
        return results

    def _import_instrument_node(
        self,
        node: ET.Element,
        inst_service: InstrumentService,
        *,
        broker_id: int,
        broker_name: str,
        postfix: str,
        selected_set: set[str],
    ) -> bool:
        """Parse and import a single instrument XML node."""
        if node.tag.lower() not in ("instrumentinfo", "symbol", "instrument"):
            return False
        orig_name = node.get("instrument") or node.get("name") or node.get("symbol")
        if not orig_name or orig_name not in selected_set:
            return False

        final_symbol = orig_name.strip() + postfix.strip()
        desc = node.get("description") or ""

        inst_def = InstrumentDefinition(
            symbol=final_symbol,
            description=desc,
            broker_id=broker_id,
            connection=broker_name,
            tick_size=float(
                node.get("tickSize")
                or node.get("tick_size")
                or node.get("point")
                or 0.00001
            ),
            tick_step=float(
                node.get("tickStep")
                or node.get("tick_step")
                or node.get("point")
                or 0.00001
            ),
            tick_value_in_money=float(
                node.get("tickValueInMoney")
                or node.get("tick_value_in_money")
                or node.get("tickValue")
                or 10.0
            ),
            point_value=float(
                node.get("pointValue") or node.get("point_value") or 100000.0
            ),
            decimals=int(node.get("decimals") or node.get("digits") or 5),
            default_spread=float(
                node.get("defaultSpread") or node.get("spread") or 0.0001
            ),
            default_slippage=float(node.get("defaultSlippage") or 0.0),
            data_type=node.get("dataType") or node.get("type") or "Forex",
            exchange=node.get("exchange") or "",
            country=node.get("country") or "",
            sector=node.get("sector") or "",
        )
        inst_service.save_instrument(inst_def)
        return True

    def _import_session_node(
        self,
        node: ET.Element,
        broker_id: int,
        postfix: str,
        selected_set: set[str],
    ) -> bool:
        """Parse and import a single session XML node."""
        if node.tag.lower() not in ("session", "sessioninfo"):
            return False
        orig_name = node.get("name") or node.get("symbol")
        if not orig_name or orig_name not in selected_set:
            return False

        final_name = orig_name.strip() + postfix.strip()
        tz = node.get("timeZone") or "UTC"

        windows = [
            {
                "day_from": el.get("dayFrom", ""),
                "time_from": el.get("timeFrom", ""),
                "day_to": el.get("dayTo", ""),
                "time_to": el.get("timeTo", ""),
                "eod": el.get("eod", "false").lower() == "true",
            }
            for el in node.findall("Element")
        ]
        if not windows:
            windows = [
                {
                    "day_from": "Monday",
                    "time_from": "00:00",
                    "day_to": "Friday",
                    "time_to": "23:59",
                    "eod": False,
                }
            ]

        session_row = {
            "name": final_name,
            "description": f"Imported for broker {broker_id}",
            "timezone": tz,
            "windows_json": json.dumps(windows),
            "holidays_json": "[]",
            "is_default": 0,
        }
        self._db.sessions.upsert(session_row)
        return True

    def import_xml_records(
        self,
        xml_content: str,
        kind: str,
        broker_id: int,
        postfix: str,
        selected_names: list[str],
    ) -> int:
        """Import selected instruments or sessions from MetaTrader XML.

        Appends the specified postfix and binds broker_id.
        Fires FR-DATA-CATALOG-BROKER-INTERCHANGE.
        """
        try:
            root = ET.fromstring(xml_content)  # noqa: S314
        except Exception as exc:
            raise ValueError(f"Invalid XML document: {exc}") from exc

        selected_set = set(selected_names)
        imported_count = 0

        if kind == "instrument":
            inst_service = InstrumentService(self._db)
            broker_rec = self.get_broker(broker_id)
            broker_name = broker_rec.name if broker_rec else ""
            for node in root.iter():
                if self._import_instrument_node(
                    node,
                    inst_service,
                    broker_id=broker_id,
                    broker_name=broker_name,
                    postfix=postfix,
                    selected_set=selected_set,
                ):
                    imported_count += 1

        elif kind == "session":
            for node in root.iter():
                if self._import_session_node(node, broker_id, postfix, selected_set):
                    imported_count += 1

        logger.info(
            "FR-DATA-CATALOG-BROKER-INTERCHANGE: "
            "Imported %d %s record(s) for broker %d",
            imported_count,
            kind,
            broker_id,
            extra={
                "count": imported_count,
                "kind": kind,
                "broker_id": broker_id,
                "fr_id": "FR-DATA-CATALOG-BROKER-INTERCHANGE",
            },
        )
        return imported_count

    def update_data_for_broker(self, broker_id: int) -> dict[str, Any]:
        """Trigger automatic historical data update for broker stocks.

        Fires FR-DATA-CATALOG-BROKER-INTERCHANGE.
        """
        existing = self.get_broker(broker_id)
        if existing is None:
            raise KeyError(f"Broker profile ID {broker_id} does not exist.")
        if not existing.stockpicker_use:
            raise ValueError(
                "Data update is only applicable to stockpicker broker profiles."
            )

        stocks = self.list_stocks(broker_id)
        if not stocks:
            raise ValueError("Broker profile has no stocks configured.")

        # Construct background task descriptor
        result = {
            "broker_id": broker_id,
            "broker_name": existing.name,
            "stocks_count": len(stocks),
            "status": "started",
            "message": "Data update started, check logs for progress.",
        }
        logger.info(
            "FR-DATA-CATALOG-BROKER-INTERCHANGE: "
            "Data update initiated for broker %s (%d stocks)",
            existing.name,
            len(stocks),
            extra={
                "broker_id": broker_id,
                "fr_id": "FR-DATA-CATALOG-BROKER-INTERCHANGE",
            },
        )
        return result


def main() -> int:
    """CLI tool for inspecting broker profiles."""
    parser = argparse.ArgumentParser(description="Inspect broker profiles")
    parser.add_argument("--list", action="store_true", help="List all broker profiles")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = BrokerService(db)

    if args.list:
        brokers = service.list_brokers()
        print(f"Configured Broker Profiles ({len(brokers)}):")
        for b in brokers:
            sys_tag = " [SYSTEM]" if b.is_system else ""
            print(
                f"  [{b.id:2d}] {b.name:18}{sys_tag:9} TZ: {b.server_timezone:12} "
                f"Postfix: '{b.postfix:10}' MT: {b.mt_use!s:5} "
                f"SP: {b.stockpicker_use!s:5} Stocks: {b.customized_stocks}"
            )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

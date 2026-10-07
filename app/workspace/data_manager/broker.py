"""Authoritative broker profile definitions and configuration management.

Description:
    Provides broker profile configurations, server timezones, symbol postfixes,
    and platform execution/spread/commission profiles within the Data Manager
    workspace, mirroring SQX DataManagerBroker.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Broker profiles, server timezones, and execution
    presets for the Data Manager workspace.

Key Capabilities:
    - FR-DATA-CATALOG-BROKER-PROFILES: Broker profile specifications, server
      timezones, symbol postfixes, and platform use flags.
      Associated: `[BrokerService.get_broker()]`, `[BrokerService.list_brokers()]`
      Logging: Emits DEBUG on broker profile queries.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.broker import BrokerProfileRecord, BrokerService

    db = DatabaseManager(":memory:")
    db.initialize()
    service = BrokerService(db)

    brokers = service.list_brokers()
    default_broker = service.get_broker("Default")
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.broker --list
    ```
"""

from __future__ import annotations

import argparse
import sys

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager, PersistenceError

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


class BrokerService:
    """Central domain service managing broker profile configurations."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize BrokerService with host DatabaseManager."""
        self._db = db

    def list_brokers(self) -> list[BrokerProfileRecord]:
        """Retrieve configured broker profiles from datamgr_broker table.

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        default_profiles = [
            BrokerProfileRecord(
                id=1,
                name="Default",
                is_system=True,
                description="Default system broker profile",
                server_timezone="UTC",
                postfix="",
                enabled=True,
                mt_use=True,
            ),
            BrokerProfileRecord(
                id=2,
                name="Dukascopy",
                is_system=True,
                description="Dukascopy Bank SA historical data",
                server_timezone="UTC",
                postfix="",
                enabled=True,
                mt_use=False,
            ),
            BrokerProfileRecord(
                id=3,
                name="Darwinex",
                is_system=True,
                description="Darwinex institutional tick feeds",
                server_timezone="UTC",
                postfix="",
                enabled=True,
                mt_use=False,
            ),
        ]
        try:
            with self._db.connection(query_only=True) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='datamgr_broker';"
                )
                if cur.fetchone() is not None:
                    cur.execute("SELECT * FROM datamgr_broker ORDER BY id ASC;")
                    rows = cur.fetchall()
                    if rows:
                        results: list[BrokerProfileRecord] = []
                        for r in rows:
                            r_dict = dict(r)
                            results.append(
                                BrokerProfileRecord(
                                    id=r_dict.get("id", 0),
                                    name=r_dict.get("name", ""),
                                    is_system=bool(r_dict.get("is_system", 0)),
                                    description=r_dict.get("description", ""),
                                    server_timezone=r_dict.get(
                                        "server_timezone", "UTC"
                                    ),
                                    postfix=r_dict.get("postfix", ""),
                                    enabled=bool(r_dict.get("enabled", 1)),
                                    mt_use=bool(r_dict.get("mt_use", 0)),
                                    stockpicker_use=bool(
                                        r_dict.get("stockpicker_use", 0)
                                    ),
                                )
                            )
                        return results
        except (PersistenceError, OSError, ValueError, KeyError) as exc:
            logger.warning(
                "FR-DATA-CATALOG-BROKER-PROFILES: Error reading datamgr_broker: %s",
                exc,
                extra={"fr_id": "FR-DATA-CATALOG-BROKER-PROFILES"},
            )

        return default_profiles

    def get_broker(self, name: str) -> BrokerProfileRecord | None:
        """Find a broker profile by name (case-insensitive).

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        clean_name = name.strip().lower()
        for b in self.list_brokers():
            if b.name.lower() == clean_name:
                return b
        return None


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
            print(
                f"  [{b.id}] {b.name:15} TZ: {b.server_timezone:15} "
                f"Postfix: '{b.postfix}' MT: {b.mt_use}"
            )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

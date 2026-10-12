"""Stock baskets and constituent membership storage repository.

Description:
    Provides transactional CRUD operations against `datamgr_baskets` and
    `datamgr_basket_stocks`, managing stock groups, constituents, date ranges,
    and atomic membership replacement. Group metrics and readiness calculations
    belong to BasketService in the workspace.

Purpose:
    FEAT-HOST-PERSISTENCE: Stock baskets and constituent membership CRUD.

Key Capabilities:
    - FR-HOST-PERSISTENCE-BASKETS: Transactional group and membership CRUD.
      Associated: `BasketStore.save()`, `BasketStore.get()`, `BasketStore.get_by_id()`,
        `BasketStore.list_names()`, `BasketStore.list_groups()`, `BasketStore.delete()`,
        `BasketStore.count()`, `BasketStore.read_overview_rows()`,
        `BasketStore.seed_defaults()`
      Logging: DEBUG reads; INFO write/delete results.

Python API Usage:
    ```python
    from app.host.persistence.engine import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()
    db.baskets.save("group", "tech", [{"ticker": "AAPL", "date_from": "2020-01-01"}])
    ```

CLI Usage:
    No direct CLI. Inspected via diagnostics:
    ```bash
    uv run python -m app.host.diagnostics --status
    ```
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistence.errors import ValidationError

if TYPE_CHECKING:
    from app.host.persistence.engine import DatabaseManager

logger = get_logger(__name__)


class BasketStore:
    """Own group/member CRUD and their shared transaction boundary."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def save(
        self,
        name: str,
        description: str,
        members: list[dict[str, Any]],
        *,
        system: int = 0,
    ) -> int:
        """Replace a group's membership atomically without domain defaults."""
        with self._db.transaction() as conn:
            cols = {
                r[1].lower()
                for r in conn.execute(
                    "PRAGMA table_info(datamgr_stock_group)"
                ).fetchall()
            }
            row = conn.execute(
                "SELECT id FROM datamgr_stock_group WHERE name = ?", (name,)
            ).fetchone()
            if row is not None:
                group_id = int(row["id"])
                if "description" in cols:
                    conn.execute(
                        "UPDATE datamgr_stock_group SET description = ?, system = ? "
                        "WHERE id = ?",
                        (description, system, group_id),
                    )
                else:
                    conn.execute(
                        "UPDATE datamgr_stock_group SET desc = ?, system = ? "
                        "WHERE id = ?",
                        (description, system, group_id),
                    )
            else:
                if "description" in cols:
                    conn.execute(
                        "INSERT INTO datamgr_stock_group (name, description, system) "
                        "VALUES (?, ?, ?)",
                        (name, description, system),
                    )
                else:
                    conn.execute(
                        "INSERT INTO datamgr_stock_group (name, desc, system) "
                        "VALUES (?, ?, ?)",
                        (name, description, system),
                    )
                new_row = conn.execute(
                    "SELECT id FROM datamgr_stock_group WHERE name = ?", (name,)
                ).fetchone()
                group_id = int(new_row["id"])

            conn.execute("DELETE FROM datamgr_stock WHERE basket_id = ?", (group_id,))
            stock_info = {
                r[1].lower(): bool(r[3])
                for r in conn.execute("PRAGMA table_info(datamgr_stock)").fetchall()
            }
            date_to_not_null = stock_info.get("date_to", False)
            date_from_not_null = stock_info.get("date_from", False)

            rows_to_insert = []
            for m in members:
                df = m["date_from"]
                if df is None and date_from_not_null:
                    df = "1900-01-01"
                dt = m.get("date_to")
                if dt is None and date_to_not_null:
                    dt = -1
                rows_to_insert.append((m["ticker"], group_id, df, dt))

            conn.executemany(
                "INSERT INTO datamgr_stock (ticker, basket_id, date_from, date_to) "
                "VALUES (?, ?, ?, ?)",
                rows_to_insert,
            )
        logger.info("Basket rows saved", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"})
        return group_id

    def _get_group(
        self,
        column: str,
        value: Any,
        log_suffix: str = "",
    ) -> dict[str, Any] | None:
        """Internal helper to retrieve a group and its ordered members by column."""
        with self._db.connection(query_only=True) as conn:
            conn.execute("BEGIN")
            try:
                if column == "id":
                    sql = "SELECT * FROM datamgr_stock_group WHERE id = ?"
                else:
                    sql = "SELECT * FROM datamgr_stock_group WHERE name = ?"
                row = conn.execute(sql, (value,)).fetchone()
                if row is None:
                    record = None
                else:
                    record = {k.lower(): v for k, v in dict(row).items()}
                    record["description"] = (
                        record.get("description") or record.get("desc") or ""
                    )
                    group_id = int(row["id"])
                    members_rows = conn.execute(
                        "SELECT * FROM datamgr_stock WHERE basket_id = ? ORDER BY id",
                        (group_id,),
                    ).fetchall()
                    record["members"] = [
                        {
                            **{k.lower(): v for k, v in dict(m).items()},
                            "ticker": str(
                                dict(m).get("ticker") or dict(m).get("TICKER", "")
                            ).strip(),
                            "date_from": dict(m).get("date_from")
                            or dict(m).get("DATE_FROM"),
                            "date_to": dict(m).get("date_to") or dict(m).get("DATE_TO"),
                        }
                        for m in members_rows
                    ]
            finally:
                conn.execute("ROLLBACK")
        logger.debug(
            "Basket rows read%s",
            log_suffix,
            extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"},
        )
        return record

    def get(self, name: str) -> dict[str, Any] | None:
        """Read a group and its ordered members in one read transaction."""
        return self._get_group("name", name)

    def get_by_id(self, basket_id: int) -> dict[str, Any] | None:
        """Read a group and its ordered members by ID in one read transaction."""
        return self._get_group("id", basket_id, " by id")

    def list_names(self) -> list[str]:
        """Read group names in alphabetical order."""
        with self._db.connection(query_only=True) as conn:
            rows = conn.execute(
                "SELECT name FROM datamgr_stock_group ORDER BY name"
            ).fetchall()
        logger.debug(
            "Basket names read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        return [str(row["name"]) for row in rows]

    def list_groups(self) -> list[dict[str, Any]]:
        """Read all stock groups with constituent counts in alphabetical order."""
        with self._db.connection(query_only=True) as conn:
            group_rows = conn.execute(
                "SELECT * FROM datamgr_stock_group ORDER BY name"
            ).fetchall()
            counts_map = dict(
                conn.execute(
                    "SELECT basket_id, COUNT(id) FROM datamgr_stock GROUP BY basket_id"
                ).fetchall()
            )
        logger.debug(
            "Basket groups list read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        results: list[dict[str, Any]] = []
        for row in group_rows:
            rec = {k.lower(): v for k, v in dict(row).items()}
            rec["description"] = rec.get("description") or rec.get("desc") or ""
            rec["member_count"] = counts_map.get(rec["id"], 0)
            results.append(rec)
        return results

    def delete(self, name: str) -> bool:
        """Delete a non-system group and its members in one transaction."""
        with self._db.transaction() as conn:
            row: sqlite3.Row | None = conn.execute(
                "SELECT id, system FROM datamgr_stock_group WHERE name = ?", (name,)
            ).fetchone()
            if row is not None:
                if int(row["system"]) == 1:
                    logger.warning(
                        "Cannot delete system stock group",
                        extra={
                            "basket_name": name,
                            "fr_id": "FR-HOST-PERSISTENCE-BASKETS",
                        },
                    )
                    return False
                conn.execute(
                    "DELETE FROM datamgr_stock WHERE basket_id = ?", (row["id"],)
                )
                conn.execute(
                    "DELETE FROM datamgr_stock_group WHERE id = ?", (row["id"],)
                )
        deleted: bool = row is not None
        logger.info(
            "Basket delete completed",
            extra={"deleted": deleted, "fr_id": "FR-HOST-PERSISTENCE-BASKETS"},
        )
        return deleted

    def count(self) -> int:
        """Return the number of stored groups."""
        with self._db.connection(query_only=True) as conn:
            row = conn.execute("SELECT COUNT(*) FROM datamgr_stock_group").fetchone()
        logger.debug(
            "Basket count read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        return int(row[0])

    @staticmethod
    def _validate_seed_member(m: Any, group_name: str) -> None:
        """Validate that a constituent member in a group is complete."""
        if not isinstance(m, dict):
            raise ValidationError(
                f"Member in group '{group_name}' must be a dictionary."
            )
        ticker = str(m.get("ticker", "")).strip()
        if not ticker:
            raise ValidationError(
                f"Member in group '{group_name}' must have a non-empty 'ticker'."
            )
        if "date_from" not in m or m["date_from"] is None:
            raise ValidationError(
                f"Member '{ticker}' in group '{group_name}' must have "
                "explicit 'date_from'."
            )
        if "date_to" not in m:
            raise ValidationError(
                f"Member '{ticker}' in group '{group_name}' must have "
                "explicit 'date_to'."
            )

    @classmethod
    def _validate_seed_group(cls, item: dict[str, Any]) -> None:
        """Validate that a group seed record and its members are complete."""
        if not isinstance(item, dict):
            raise ValidationError("Group seed record must be a dictionary.")
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValidationError("Group seed record must contain a non-empty 'name'.")
        if "system" not in item:
            raise ValidationError(
                f"Group seed record '{name}' is missing required 'system' field."
            )
        if "description" not in item and "desc" not in item:
            raise ValidationError(
                f"Group seed record '{name}' is missing required 'description' field."
            )
        members = item.get("members")
        if not isinstance(members, list):
            raise ValidationError(
                f"Group seed record '{name}' is missing required 'members' list."
            )
        for m in members:
            cls._validate_seed_member(m, name)

    def seed_defaults(self, groups: list[dict[str, Any]]) -> None:
        """Seed default StrategyQuant X stock groups from caller-provided records.

        Raises:
            ValidationError: If any group or constituent record is incomplete.
        """
        for item in groups:
            self._validate_seed_group(item)

        with self._db.transaction() as conn:
            cols = {
                r[1].lower()
                for r in conn.execute(
                    "PRAGMA table_info(datamgr_stock_group)"
                ).fetchall()
            }
            for item in groups:
                name = str(item["name"]).strip()
                exists = conn.execute(
                    "SELECT id FROM datamgr_stock_group WHERE name = ?", (name,)
                ).fetchone()
                if exists is None:
                    desc_val = str(
                        item["description"] if "description" in item else item["desc"]
                    )
                    system_val = int(bool(item["system"]))
                    if "description" in cols:
                        insert_sql = (
                            "INSERT INTO datamgr_stock_group "
                            "(name, system, description) VALUES (?, ?, ?)"
                        )
                    else:
                        insert_sql = (
                            "INSERT INTO datamgr_stock_group "
                            "(name, system, desc) VALUES (?, ?, ?)"
                        )
                    conn.execute(
                        insert_sql,
                        (name, system_val, desc_val),
                    )
                    row = conn.execute(
                        "SELECT id FROM datamgr_stock_group WHERE name = ?", (name,)
                    ).fetchone()
                    group_id = int(row["id"])
                    members = item["members"]
                    conn.executemany(
                        "INSERT INTO datamgr_stock "
                        "(ticker, basket_id, date_from, date_to) VALUES (?, ?, ?, ?)",
                        [
                            (
                                str(m["ticker"]).strip(),
                                group_id,
                                str(m["date_from"]),
                                m["date_to"],
                            )
                            for m in members
                        ],
                    )
        logger.info(
            "Seeded default StrategyQuant X stock groups",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"},
        )

    def read_overview_rows(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Read groups, members, and dataset symbol bounds in 3 fixed queries."""
        with self._db.connection(query_only=True) as conn:
            conn.execute("BEGIN")
            try:
                groups_rows = [
                    {
                        **{k.lower(): v for k, v in dict(r).items()},
                        "description": (
                            dict(r).get("description") or dict(r).get("desc") or ""
                        ),
                    }
                    for r in conn.execute(
                        "SELECT * FROM datamgr_stock_group ORDER BY name"
                    ).fetchall()
                ]
                stocks_rows = [
                    {k.lower(): v for k, v in dict(r).items()}
                    for r in conn.execute(
                        "SELECT * FROM datamgr_stock ORDER BY basket_id, id"
                    ).fetchall()
                ]
                ds_rows = [
                    {k.lower(): v for k, v in dict(r).items()}
                    for r in conn.execute(
                        "SELECT UPPER(symbol) AS sym, "
                        "MIN(date_from) AS df, "
                        "MAX(date_to) AS dt, "
                        "SUM(bars) AS tb "
                        "FROM datamgr_datasets "
                        "GROUP BY UPPER(symbol)"
                    ).fetchall()
                ]
            finally:
                conn.execute("ROLLBACK")
        logger.debug(
            "Basket overview snapshot read",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"},
        )
        return groups_rows, stocks_rows, ds_rows

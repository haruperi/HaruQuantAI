"""Stock baskets and constituent membership storage repository.

Description:
    Provides transactional CRUD operations against `datamgr_baskets` and
    `datamgr_basket_stocks`, managing stock groups, constituents, date ranges,
    group metrics calculation, and atomic membership replacement.

Purpose:
    FEAT-HOST-PERSISTENCE: Stock baskets and constituent membership CRUD.

Key Capabilities:
    - FR-HOST-PERSISTENCE-BASKETS: Transactional group and membership CRUD.
      Associated: `BasketStore.save()`, `BasketStore.get()`, `BasketStore.delete()`,
        `BasketStore.count()`, `BasketStore.list_overview()`
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

import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistence.stores.jobs import normalize_sqx_date

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

    def get(self, name: str) -> dict[str, Any] | None:
        """Read a group and its ordered members in one read transaction."""
        with self._db.connection(query_only=True) as conn:
            conn.execute("BEGIN")
            try:
                row = conn.execute(
                    "SELECT * FROM datamgr_stock_group WHERE name = ?", (name,)
                ).fetchone()
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
                            "date_from": normalize_sqx_date(
                                dict(m).get("date_from") or dict(m).get("DATE_FROM")
                            ),
                            "date_to": normalize_sqx_date(
                                dict(m).get("date_to") or dict(m).get("DATE_TO")
                            ),
                        }
                        for m in members_rows
                    ]
            finally:
                conn.execute("ROLLBACK")
        logger.debug("Basket rows read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"})
        return record

    def get_by_id(self, basket_id: int) -> dict[str, Any] | None:
        """Read a group and its ordered members by ID in one read transaction."""
        with self._db.connection(query_only=True) as conn:
            conn.execute("BEGIN")
            try:
                row = conn.execute(
                    "SELECT * FROM datamgr_stock_group WHERE id = ?", (basket_id,)
                ).fetchone()
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
                            "date_from": normalize_sqx_date(
                                dict(m).get("date_from") or dict(m).get("DATE_FROM")
                            ),
                            "date_to": normalize_sqx_date(
                                dict(m).get("date_to") or dict(m).get("DATE_TO")
                            ),
                        }
                        for m in members_rows
                    ]
            finally:
                conn.execute("ROLLBACK")
        logger.debug(
            "Basket rows read by id", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        return record

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

    def ensure_defaults(self) -> None:
        """Seed the 10 authoritative StrategyQuant X default groups."""
        defaults: list[dict[str, Any]] = [
            {
                "name": "[[Dow Jones Industrial Average]]",
                "system": 1,
                "description": "Dow Jones Industrial Average index",
                "stocks": [
                    "AAPL",
                    "AMGN",
                    "AXP",
                    "BA",
                    "CAT",
                    "CRM",
                    "CSCO",
                    "CVX",
                    "DIS",
                    "DOW",
                    "GS",
                    "HD",
                    "HON",
                    "IBM",
                    "INTC",
                    "JNJ",
                    "JPM",
                    "KO",
                    "MCD",
                    "MMM",
                    "MRK",
                    "MSFT",
                    "NKE",
                    "PG",
                    "TRV",
                    "UNH",
                    "V",
                    "VZ",
                    "WBA",
                    "WMT",
                ],
            },
            {
                "name": "[[Nasdaq 100]]",
                "system": 1,
                "description": "Nasdaq 100 index",
                "stocks": [
                    "AAPL",
                    "ABNB",
                    "ADBE",
                    "ADI",
                    "ADP",
                    "ADSK",
                    "AEP",
                    "AMAT",
                    "AMD",
                    "AMGN",
                    "AMZN",
                    "ANSS",
                    "ASML",
                    "AVGO",
                    "AZN",
                    "BIIB",
                    "BKNG",
                    "BKR",
                    "CDNS",
                    "CEG",
                    "CHTR",
                    "CMCSA",
                    "COST",
                    "CPRT",
                    "CRWD",
                    "CSCO",
                    "CSGP",
                    "CSX",
                    "CTAS",
                    "CTSH",
                    "DDOG",
                    "DLTR",
                    "DXCM",
                    "EA",
                    "EXC",
                    "FANG",
                    "FAST",
                    "FTNT",
                    "GEHC",
                    "GFS",
                    "GILD",
                    "GOOG",
                    "GOOGL",
                    "HON",
                    "IDXX",
                    "ILMN",
                    "INTC",
                    "INTU",
                    "ISRG",
                    "KDP",
                    "KHC",
                    "KLAC",
                    "LRCX",
                    "LULU",
                    "MAR",
                    "MCHP",
                    "MDLZ",
                    "MELI",
                    "META",
                    "MNST",
                    "MRNA",
                    "MRVL",
                    "MSFT",
                    "MU",
                    "NFLX",
                    "NVDA",
                    "NXPI",
                    "ODFL",
                    "ON",
                    "ORLY",
                    "PANW",
                    "PAYX",
                    "PCAR",
                    "PDD",
                    "PEP",
                    "PYPL",
                    "QCOM",
                    "REGN",
                    "ROP",
                    "ROST",
                    "SBUX",
                    "SIRI",
                    "SNPS",
                    "SPLK",
                    "TEAM",
                    "TMUS",
                    "TSLA",
                    "TTD",
                    "TXN",
                    "VRSK",
                    "VRTX",
                    "WBA",
                    "WBD",
                    "WDAY",
                    "XEL",
                    "ZS",
                ],
            },
            {
                "name": "[[Nasdaq Biotechnology]]",
                "system": 1,
                "description": "Nasdaq Biotechnology index",
                "stocks": [
                    "AMGN",
                    "GILD",
                    "VRTX",
                    "REGN",
                    "BIIB",
                    "MRNA",
                    "ALNY",
                    "ILMN",
                    "SGEN",
                    "BMRN",
                ],
            },
            {
                "name": "[[Russell 1000]]",
                "system": 1,
                "description": "Russell 1000 index",
                "stocks": [
                    "AAPL",
                    "MSFT",
                    "AMZN",
                    "NVDA",
                    "GOOGL",
                    "META",
                    "GOOG",
                    "BRK.B",
                    "TSLA",
                    "UNH",
                ],
            },
            {
                "name": "[[Russell 2000]]",
                "system": 1,
                "description": "Russell 2000 index",
                "stocks": [
                    "SMCI",
                    "FTAI",
                    "VRT",
                    "SAIA",
                    "ELF",
                    "FN",
                    "ENSG",
                    "COHR",
                    "MEDP",
                    "ONTO",
                ],
            },
            {
                "name": "[[Russell 3000]]",
                "system": 1,
                "description": "Russell 3000 index",
                "stocks": [
                    "AAPL",
                    "MSFT",
                    "AMZN",
                    "NVDA",
                    "GOOGL",
                    "META",
                    "TSLA",
                    "UNH",
                    "JNJ",
                    "JPM",
                ],
            },
            {
                "name": "[[S&P 100 limited]]",
                "system": 1,
                "description": "S&P 100 limited index sample for clean installation",
                "stocks": [
                    "AAPL",
                    "ABBV",
                    "ABT",
                    "ACN",
                    "ADBE",
                    "AIG",
                    "AMD",
                    "AMGN",
                    "AMT",
                    "AMZN",
                    "AVGO",
                    "AXP",
                    "BA",
                    "BAC",
                    "BK",
                    "BKNG",
                    "BLK",
                    "BMY",
                    "BRK.B",
                    "C",
                    "CAT",
                    "CHTR",
                    "CL",
                    "CMCSA",
                    "COF",
                    "COP",
                    "COST",
                    "CRM",
                    "CSCO",
                    "CVS",
                    "CVX",
                    "DE",
                    "DHR",
                    "DIS",
                    "DOW",
                    "DUK",
                    "EMR",
                    "EXC",
                    "F",
                    "FDX",
                    "GD",
                    "GE",
                    "GILD",
                    "GM",
                    "GOOG",
                    "GOOGL",
                    "GS",
                    "HD",
                    "HON",
                    "IBM",
                    "INTC",
                    "INTU",
                    "ISRG",
                    "JNJ",
                    "JPM",
                    "KHC",
                    "KO",
                    "LIN",
                    "LLY",
                    "LMT",
                    "LOW",
                    "MA",
                    "MCD",
                    "MDLZ",
                    "MDT",
                    "MET",
                    "META",
                    "MMM",
                    "MO",
                    "MRK",
                    "MS",
                    "MSFT",
                    "NEE",
                    "NFLX",
                    "NKE",
                    "NVDA",
                    "ORCL",
                    "PEP",
                    "PFE",
                    "PG",
                    "PM",
                    "PYPL",
                    "QCOM",
                    "RTX",
                    "SBUX",
                    "SCHW",
                    "SO",
                    "SPG",
                    "T",
                    "TGT",
                    "TMO",
                    "TMUS",
                    "TSLA",
                    "TXN",
                    "UNH",
                    "UNP",
                    "UPS",
                    "USB",
                    "V",
                    "VZ",
                    "WBA",
                    "WFC",
                    "WMT",
                    "XOM",
                ],
            },
            {
                "name": "[[S&P 100]]",
                "system": 1,
                "description": "S&P 100 index",
                "stocks": [
                    "AAPL",
                    "ABBV",
                    "ABT",
                    "ACN",
                    "ADBE",
                    "AIG",
                    "AMD",
                    "AMGN",
                    "AMT",
                    "AMZN",
                    "AVGO",
                    "AXP",
                    "BA",
                    "BAC",
                    "BK",
                    "BKNG",
                    "BLK",
                    "BMY",
                    "BRK.B",
                    "C",
                ],
            },
            {
                "name": "[[S&P 500]]",
                "system": 1,
                "description": "S&P 500 index",
                "stocks": [
                    "AAPL",
                    "MSFT",
                    "AMZN",
                    "NVDA",
                    "GOOGL",
                    "META",
                    "GOOG",
                    "BRK.B",
                    "TSLA",
                    "UNH",
                    "JNJ",
                    "JPM",
                    "V",
                    "PG",
                    "XOM",
                    "MA",
                    "HD",
                    "CVX",
                    "MRK",
                    "ABBV",
                ],
            },
            {
                "name": "[[S&P MidCap 400]]",
                "system": 1,
                "description": "S&P MidCap 400 index",
                "stocks": [
                    "DECK",
                    "SAIA",
                    "MANH",
                    "RL",
                    "WSO",
                    "FIX",
                    "RPM",
                    "RS",
                    "SFM",
                    "HUBB",
                ],
            },
        ]
        with self._db.transaction() as conn:
            for item in defaults:
                name = item["name"]
                exists = conn.execute(
                    "SELECT id FROM datamgr_stock_group WHERE name = ?", (name,)
                ).fetchone()
                if exists is None:
                    conn.execute(
                        "INSERT INTO datamgr_stock_group "
                        "(name, system, description) VALUES (?, ?, ?)",
                        (name, item["system"], item["description"]),
                    )
                    row = conn.execute(
                        "SELECT id FROM datamgr_stock_group WHERE name = ?", (name,)
                    ).fetchone()
                    group_id = int(row["id"])
                    conn.executemany(
                        "INSERT INTO datamgr_stock "
                        "(ticker, basket_id, date_from, date_to) VALUES (?, ?, ?, ?)",
                        [(tkr, group_id, "1900-01-01", None) for tkr in item["stocks"]],
                    )
        logger.info(
            "Seeded default StrategyQuant X stock groups",
            extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"},
        )

    @staticmethod
    def _calculate_group_metrics(
        g_dict: dict[str, Any],
        stocks: list[sqlite3.Row],
        available_map: dict[str, dict[str, Any]],
        today: str,
    ) -> dict[str, Any]:
        """Compute constituent metrics, bounds, and readiness for a group."""
        total_count = len(stocks)
        active_count = 0
        distinct_tickers: set[str] = set()
        downloaded_tickers: set[str] = set()
        group_dfs: list[str] = []
        group_dts: list[str] = []

        for s in stocks:
            s_dict = {k.lower(): v for k, v in dict(s).items()}
            tkr = str(s_dict.get("ticker") or s_dict.get("TICKER", "")).strip().upper()
            if not tkr:
                continue
            distinct_tickers.add(tkr)
            df = normalize_sqx_date(s_dict.get("date_from") or s_dict.get("DATE_FROM"))
            dt = normalize_sqx_date(s_dict.get("date_to") or s_dict.get("DATE_TO"))
            if (not df or df <= today) and (not dt or dt >= today):
                active_count += 1
            if tkr in available_map:
                downloaded_tickers.add(tkr)
                ds_info = available_map[tkr]
                if ds_info["date_from"]:
                    group_dfs.append(str(ds_info["date_from"]))
                if ds_info["date_to"]:
                    group_dts.append(str(ds_info["date_to"]))

        missing = sorted(distinct_tickers - downloaded_tickers)
        num_symbols = len(distinct_tickers)
        downloaded_count = len(downloaded_tickers)
        desc = g_dict.get("description") or g_dict.get("desc") or ""

        return {
            "id": int(g_dict["id"]),
            "name": str(g_dict.get("name", "")),
            "description": str(desc),
            "system": bool(g_dict.get("system", 0)),
            "active_count": active_count,
            "total_count": total_count,
            "symbols_count": num_symbols,
            "downloaded_count": downloaded_count,
            "is_ready": num_symbols > 0 and len(missing) == 0,
            "missing_symbols": missing,
            "data_from": min(group_dfs) if group_dfs else "",
            "data_to": max(group_dts) if group_dts else "",
        }

    def list_groups_overview(self) -> list[dict[str, Any]]:
        """Read all stock groups with constituent metrics and dataset bounds."""
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        with self._db.connection(query_only=True) as conn:
            conn.execute("BEGIN")
            try:
                groups_rows = conn.execute(
                    "SELECT * FROM datamgr_stock_group ORDER BY name"
                ).fetchall()

                ds_rows: list[sqlite3.Row] = []
                try:
                    ds_rows = conn.execute(
                        "SELECT UPPER(symbol) AS sym, "
                        "MIN(date_from) AS df, "
                        "MAX(date_to) AS dt, "
                        "SUM(bars) AS tb "
                        "FROM datamgr_datasets "
                        "GROUP BY UPPER(symbol)"
                    ).fetchall()
                except sqlite3.OperationalError:
                    ds_rows = []
                available_map: dict[str, dict[str, Any]] = {
                    str(row["sym"]): {
                        "date_from": row["df"],
                        "date_to": row["dt"],
                        "bars": row["tb"],
                    }
                    for row in ds_rows
                    if row["tb"] is not None and int(row["tb"]) > 0
                }

                results: list[dict[str, Any]] = []
                for g in groups_rows:
                    g_dict = {k.lower(): v for k, v in dict(g).items()}
                    group_id = int(g_dict["id"])
                    stocks = conn.execute(
                        "SELECT * FROM datamgr_stock WHERE basket_id = ? ORDER BY id",
                        (group_id,),
                    ).fetchall()
                    results.append(
                        self._calculate_group_metrics(
                            g_dict, stocks, available_map, today
                        )
                    )
            finally:
                conn.execute("ROLLBACK")
        logger.debug(
            "Basket overview list read", extra={"fr_id": "FR-HOST-PERSISTENCE-BASKETS"}
        )
        return results

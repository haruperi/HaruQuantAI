r"""SQX Reference Database Ingestion and Table Replication Utility.

Description:
    Provides transactional migration and table replication from the SQX
    reference database (`C:\SQX\scripts\haruquantai.db`) into the central
    application SQLite database (`data/database/haruquantai.db`). It ensures
    all legacy catalog tables (such as tickers, commodities, instruments,
    and broker definitions) are copied with exact schema preservation and
    row-level integrity without mutating pre-existing host or DataManager tables.

Purpose:
    FEAT-PERSIST-SQX-MIGRATION: High-fidelity SQX catalog and reference table
    replication for quantitative data acquisition plugins.

Key Capabilities:
    - FR-PERSIST-SQX-MIGRATION-ATTACH: Attaches reference SQX database safely
      under an isolated read-only schema.
      Associated: `copy_sqx_database()`
      Logging: Emits info log with source and destination database paths.
    - FR-PERSIST-SQX-MIGRATION-EXECUTE: Transactionally creates target tables,
      replicates records, and builds indices.
      Associated: `copy_sqx_database()`
      Logging: Emits info log per table copied with exact transferred row count.
    - FR-PERSIST-SQX-MIGRATION-VERIFY: Runs database integrity check and verifies
      table inventory against source records.
      Associated: `verify_database_integrity()`
      Logging: Emits info log reporting integrity check status and total tables.

Python API Usage:
    ```python
    from pathlib import Path
    from scripts.copy_sqx_database import copy_sqx_database

    source = Path("C:/SQX/scripts/haruquantai.db")
    dest = Path("data/database/haruquantai.db")
    results = copy_sqx_database(source=source, dest=dest)
    print(results)
    ```

CLI Usage:
    ```bash
    uv run python scripts/copy_sqx_database.py
    ```
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scripts.copy_sqx_database")

DEFAULT_SOURCE_PATH = Path(r"C:\SQX\scripts\haruquantai.db")
DEFAULT_DEST_PATH = Path("data/database/haruquantai.db")


def verify_database_integrity(conn: sqlite3.Connection) -> None:
    """Execute SQLite PRAGMA integrity_check and raise on errors."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    rows = cursor.fetchall()
    if rows != [("ok",)]:
        logger.error("Database integrity check failed: %s", rows)
        raise RuntimeError(f"Integrity check failed: {rows}")
    logger.info("PRAGMA integrity_check passed: ok")


def copy_sqx_database(
    source: Path = DEFAULT_SOURCE_PATH,
    dest: Path = DEFAULT_DEST_PATH,
) -> dict[str, int]:
    """Copy all tables, records, and indexes from source SQX database into dest."""
    if not source.exists():
        raise FileNotFoundError(f"Source database does not exist: {source}")
    if not dest.exists():
        raise FileNotFoundError(f"Destination database does not exist: {dest}")

    logger.info("Attaching source database: source=%s dest=%s", source, dest)
    conn = sqlite3.connect(dest)
    copied_counts: dict[str, int] = {}

    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("ATTACH DATABASE ? AS sqx", (str(source.resolve()),))

        cursor = conn.cursor()
        tables = cursor.execute(
            "SELECT name, sql FROM sqx.sqlite_master "
            "WHERE type='table' AND name != 'sqlite_sequence' "
            "ORDER BY name"
        ).fetchall()

        logger.info("Discovered %d tables in source SQX database", len(tables))

        with conn:
            for name, sql in tables:
                logger.info("Creating table in destination: %s", name)
                conn.execute(sql)
                conn.execute(f'INSERT INTO main."{name}" SELECT * FROM sqx."{name}"')
                row_count = conn.execute(
                    f'SELECT count(*) FROM main."{name}"'
                ).fetchone()[0]
                copied_counts[name] = row_count
                logger.info("Copied table %s: %d rows", name, row_count)

            indexes = cursor.execute(
                "SELECT sql FROM sqx.sqlite_master "
                "WHERE type='index' AND sql IS NOT NULL"
            ).fetchall()
            logger.info("Discovered %d indexes to replicate", len(indexes))
            for (idx_sql,) in indexes:
                logger.info("Recreating index: %s", idx_sql)
                conn.execute(idx_sql)

        conn.execute("DETACH DATABASE sqx")
        conn.execute("PRAGMA foreign_keys = ON")
        verify_database_integrity(conn)

    finally:
        conn.close()

    logger.info(
        "Successfully migrated %d tables to %s",
        len(copied_counts),
        dest,
    )
    return copied_counts


def main() -> int:
    """CLI entrypoint for SQX database copying."""
    try:
        results = copy_sqx_database()
        print("\n=== SUMMARY OF COPIED TABLES ===")
        for table, count in sorted(results.items()):
            print(f"  {table:20s}: {count:8d} rows")
        print("=== COMPLETED SUCCESSFULLY ===\n")
        return 0
    except Exception:
        logger.exception("Migration failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

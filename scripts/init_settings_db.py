"""CLI tool to initialize the central HaruQuantAI database and settings table."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

# Add workspace root to Python path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.workspace.runtime_configuration.runtime_configuration import (  # noqa: E402
    DEFAULT_CENTRAL_DB_PATH,
    init_central_database,
    list_settings_records,
)

SAMPLE_LIMIT = 15
KNOWN_TABLES = ("permissions", "sessions", "settings", "settings_history", "users")


def main() -> None:
    """Entry point for initializing and inspecting the central database."""
    parser = argparse.ArgumentParser(
        description="Initialize and inspect HaruQuantAI central database."
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_CENTRAL_DB_PATH,
        help=f"Target database path (default: {DEFAULT_CENTRAL_DB_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print database summary and table contents without re-creating.",
    )
    args = parser.parse_args()

    db_path: Path = args.db_path
    print("=" * 70)
    print("  HaruQuantAI Central Settings Database Initializer")
    print("=" * 70)
    print(f"Target Database: {db_path.resolve()}\n")

    # Initialize
    actual_path = init_central_database(db_path)
    print(f"[OK] Database initialized successfully at: {actual_path}")

    # Inspect tables
    conn = sqlite3.connect(str(actual_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
        print(f"\nCreated Tables ({len(tables)}):")
        for table in tables:
            if table in KNOWN_TABLES:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")  # noqa: S608
                count = cursor.fetchone()[0]
                print(f"  * {table:20s} : {count:4d} rows")

        # Category Breakdown for settings
        cursor.execute(
            """
            SELECT category, COUNT(*), SUM(is_secret)
            FROM settings
            GROUP BY category
            ORDER BY category;
            """
        )
        categories = cursor.fetchall()
        print("\nSettings by Category:")
        for cat, total, secrets in categories:
            print(f"  - {cat:15s} : {total:2d} settings (secrets: {secrets})")

        # Users
        cursor.execute("SELECT user_id, username, roles_json, active FROM users;")
        users = cursor.fetchall()
        print("\nUsers:")
        for uid, uname, roles, active in users:
            print(
                f"  - {uname:10s} (id: {uid}, roles: {roles}, active: {bool(active)})"
            )

        # Sample Settings Preview
        print("\nSample Settings Preview:")
        records = list_settings_records(db_path=actual_path)
        for rec in records[:SAMPLE_LIMIT]:
            display_val = (
                "******" if rec["is_secret"] and rec["raw_value"] else rec["raw_value"]
            )
            vtype = rec["value_type"]
            cat = rec["category"]
            k = rec["key"]
            print(f"  [{cat:12s}] {k:35s} = {display_val} ({vtype})")
        if len(records) > SAMPLE_LIMIT:
            remaining = len(records) - SAMPLE_LIMIT
            print(f"  ... and {remaining} more settings.")

    finally:
        conn.close()

    print("\n" + "=" * 70)
    print("  Initialization & Dry-Run Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()

"""Subprocess test proving provider state retention across uninstall and reinstall.

Traces to: P8-T03, Gate G8
"""

# ruff: noqa: S608
from __future__ import annotations

from pathlib import Path

from tests.removability.harness import run_in_fresh_process

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_gate_g8_state_retention_across_uninstall_and_reinstall(
    tmp_path: Path,
) -> None:
    """Gate G8: Prove full install -> migrate -> uninstall with tombstone -> absent restart -> reinstall cycle in fresh processes."""
    db_dir = tmp_path / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_dir_str = str(db_dir).replace("\\", "/")

    # Environment setup header for subprocesses
    env_header = f"""
import os
os.environ["DATA_DIR"] = {db_dir_str!r}
os.environ["DATABASE_URL"] = "sqlite:///migrations.sqlite3"
os.environ["SQLITE_BUSY_TIMEOUT_SECONDS"] = "1"
os.environ["WRITE_LOCK_LEASE_SECONDS"] = "30"
"""

    # Phase 1: Process 1 - Initial migration and data insertion
    p1_script = (
        env_header
        + """
import sqlite3
from app.services.data.persistence.contracts import MigrationRequest, MigrationStep
from app.services.data.persistence.migrations import _run_domain_migrations_raw
from app.kernel.identity import generate_id

step1 = MigrationStep(
    domain="trading",
    migration_id="0001_init",
    checksum="checksum_v1_orders",
    statements=(
        "CREATE TABLE trading_orders (order_id INTEGER PRIMARY KEY, symbol TEXT NOT NULL);",
    ),
)
req1 = MigrationRequest(
    domain="trading",
    steps=(step1,),
    request_id=generate_id("req"),
    complete_manifest=True,
)
res = _run_domain_migrations_raw(req1)
assert res.applied_ids == ("0001_init",)

db_path = os.path.join(os.environ["DATA_DIR"], "migrations.sqlite3")
with sqlite3.connect(db_path) as conn:
    conn.execute("INSERT INTO trading_orders (order_id, symbol) VALUES (101, 'EURUSD');")
    conn.commit()

print("PHASE_1_OK")
"""
    )

    res1 = run_in_fresh_process(repository_root=_REPO_ROOT, script=p1_script)
    assert res1.returncode == 0, f"Phase 1 failed: {res1.stderr}"
    assert "PHASE_1_OK" in res1.stdout

    # Phase 2: Process 2 - Provider absent, startup with matching tombstone
    p2_script = (
        env_header
        + """
import sqlite3
from app.services.data.persistence.contracts import MigrationRequest, MigrationStep, MigrationTombstone
from app.services.data.persistence.migrations import _run_domain_migrations_raw
from app.kernel.identity import generate_id

tombstone = MigrationTombstone(
    domain="trading",
    migration_id="0001_init",
    checksum="checksum_v1_orders",
    owner_provider_id="trading.orders.provider",
    state_schema_id="trading_orders",
)
req2 = MigrationRequest(
    domain="trading",
    steps=(
        MigrationStep(
            domain="trading",
            migration_id="0002_core_trading",
            checksum="checksum_v1_core",
            statements=("CREATE TABLE core_account (id INT PRIMARY KEY);",),
        ),
    ),
    tombstones=(tombstone,),
    request_id=generate_id("req"),
    complete_manifest=True,
)
res2 = _run_domain_migrations_raw(req2)
assert res2.applied_ids == ("0002_core_trading",)

# Verify historical table data is preserved
db_path = os.path.join(os.environ["DATA_DIR"], "migrations.sqlite3")
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM trading_orders WHERE order_id=101")
    row = cursor.fetchone()
    assert row is not None and row[0] == "EURUSD"

print("PHASE_2_OK")
"""
    )

    res2 = run_in_fresh_process(repository_root=_REPO_ROOT, script=p2_script)
    assert res2.returncode == 0, f"Phase 2 failed: {res2.stderr}"
    assert "PHASE_2_OK" in res2.stdout

    # Phase 3: Process 3 - Provider absent without tombstone (fails complete manifest check)
    p3_script = (
        env_header
        + """
from app.services.data.persistence.contracts import MigrationRequest, MigrationStep
from app.services.data.persistence.migrations import _run_domain_migrations_raw
from app.kernel.identity import generate_id

req3 = MigrationRequest(
    domain="trading",
    steps=(
        MigrationStep(
            domain="trading",
            migration_id="0002_core_trading",
            checksum="checksum_v1_core",
            statements=("CREATE TABLE core_account (id INT PRIMARY KEY);",),
        ),
    ),
    tombstones=(),  # Missing tombstone for 0001_init
    request_id=generate_id("req"),
    complete_manifest=True,
)
_run_domain_migrations_raw(req3)
"""
    )

    res3 = run_in_fresh_process(repository_root=_REPO_ROOT, script=p3_script)
    assert res3.returncode != 0, (
        "Phase 3 should have failed closed due to missing tombstone"
    )

    # Phase 4: Process 4 - Tombstone with checksum mismatch (fails checksum verification)
    p4_script = (
        env_header
        + """
from app.services.data.persistence.contracts import MigrationRequest, MigrationStep, MigrationTombstone
from app.services.data.persistence.migrations import _run_domain_migrations_raw
from app.kernel.identity import generate_id

tombstone_bad = MigrationTombstone(
    domain="trading",
    migration_id="0001_init",
    checksum="checksum_WRONG",
    owner_provider_id="trading.orders.provider",
    state_schema_id="trading_orders",
)
req4 = MigrationRequest(
    domain="trading",
    steps=(
        MigrationStep(
            domain="trading",
            migration_id="0002_core_trading",
            checksum="checksum_v1_core",
            statements=("CREATE TABLE core_account (id INT PRIMARY KEY);",),
        ),
    ),
    tombstones=(tombstone_bad,),
    request_id=generate_id("req"),
    complete_manifest=True,
)
_run_domain_migrations_raw(req4)
"""
    )

    res4 = run_in_fresh_process(repository_root=_REPO_ROOT, script=p4_script)
    assert res4.returncode != 0, (
        "Phase 4 should have failed closed due to checksum mismatch"
    )

    # Phase 5: Process 5 - Reinstall compatible provider, apply incremental migration, access both records
    p5_script = (
        env_header
        + """
import sqlite3
from app.services.data.persistence.contracts import MigrationRequest, MigrationStep
from app.services.data.persistence.migrations import _run_domain_migrations_raw
from app.kernel.identity import generate_id

step1 = MigrationStep(
    domain="trading",
    migration_id="0001_init",
    checksum="checksum_v1_orders",
    statements=(
        "CREATE TABLE trading_orders (order_id INTEGER PRIMARY KEY, symbol TEXT NOT NULL);",
    ),
)
step2 = MigrationStep(
    domain="trading",
    migration_id="0002_core_trading",
    checksum="checksum_v1_core",
    statements=("CREATE TABLE core_account (id INT PRIMARY KEY);",),
)
step3 = MigrationStep(
    domain="trading",
    migration_id="0003_orders_v2_column",
    checksum="checksum_v2_orders",
    statements=("ALTER TABLE trading_orders ADD COLUMN notes TEXT DEFAULT '';",),
)

req5 = MigrationRequest(
    domain="trading",
    steps=(step1, step2, step3),
    tombstones=(),
    request_id=generate_id("req"),
    complete_manifest=True,
)
res5 = _run_domain_migrations_raw(req5)
assert "0003_orders_v2_column" in res5.applied_ids
assert "0001_init" in res5.skipped_ids

# Insert new record using newly added column
db_path = os.path.join(os.environ["DATA_DIR"], "migrations.sqlite3")
with sqlite3.connect(db_path) as conn:
    conn.execute("INSERT INTO trading_orders (order_id, symbol, notes) VALUES (102, 'GBPUSD', 'reinstalled');")
    conn.commit()

    cursor = conn.cursor()
    cursor.execute("SELECT order_id, symbol, notes FROM trading_orders ORDER BY order_id")
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert rows[0] == (101, 'EURUSD', '')
    assert rows[1] == (102, 'GBPUSD', 'reinstalled')

print("PHASE_5_OK")
"""
    )

    res5 = run_in_fresh_process(repository_root=_REPO_ROOT, script=p5_script)
    assert res5.returncode == 0, f"Phase 5 failed: {res5.stderr}"
    assert "PHASE_5_OK" in res5.stdout

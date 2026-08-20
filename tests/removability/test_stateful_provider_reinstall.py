"""Subprocess test proving stateful provider absence and compatible reinstall.

Traces to: P8-T03, Gate G8
"""

# ruff: noqa: S608
from __future__ import annotations

import json
from pathlib import Path

from app.kernel.errors import ManifestValidationError
from app.kernel.manifests import load_manifest

from tests.removability.harness import run_in_fresh_process

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "stateful_provider"


def test_stateful_provider_absence_and_compatible_reinstall(tmp_path: Path) -> None:
    """Execute complete install -> migrate -> absent with tombstone -> reinstall cycle in fresh processes."""
    db_dir = tmp_path / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_dir_str = str(db_dir).replace("\\", "/")

    manifest = load_manifest(_FIXTURE_DIR / "manifest.toml")
    assert manifest.state_schema_id is not None
    migration_path = _FIXTURE_DIR / "migration.json"
    mig_data = json.loads(migration_path.read_text(encoding="utf-8"))

    # Stage 1: Install & migrate stateful provider
    p1_script = f"""
import os, sqlite3
os.environ["DATA_DIR"] = {db_dir_str!r}
os.environ["DATABASE_URL"] = "sqlite:///migrations.sqlite3"
os.environ["SQLITE_BUSY_TIMEOUT_SECONDS"] = "1"
os.environ["WRITE_LOCK_LEASE_SECONDS"] = "30"

from app.services.data.persistence.contracts import MigrationRequest, MigrationStep
from app.services.data.persistence.migrations import _run_domain_migrations_raw
from app.utils import generate_id

step1 = MigrationStep(
    domain={mig_data["domain"]!r},
    migration_id={mig_data["migration_id"]!r},
    checksum={mig_data["checksum"]!r},
    statements=({mig_data["sql"]!r},),
)
req1 = MigrationRequest(
    domain={mig_data["domain"]!r},
    steps=(step1,),
    request_id=generate_id("req"),
    complete_manifest=True,
)
res = _run_domain_migrations_raw(req1)
assert res.applied_ids == ({mig_data["migration_id"]!r},)

db_path = os.path.join(os.environ["DATA_DIR"], "migrations.sqlite3")
conn = sqlite3.connect(db_path)
try:
    conn.execute("INSERT INTO test_stateful_records (record_id, value) VALUES ('record-1', 'preserved');")
    conn.commit()
finally:
    conn.close()

print("STAGE_1_OK")
"""
    res1 = run_in_fresh_process(repository_root=_REPO_ROOT, script=p1_script)
    assert res1.returncode == 0, f"Stage 1 failed: {res1.stderr}"
    assert "STAGE_1_OK" in res1.stdout

    # Stage 2: Absent restart with tombstone, provider module absent
    p2_script = f"""
import os, sys, sqlite3
os.environ["DATA_DIR"] = {db_dir_str!r}
os.environ["DATABASE_URL"] = "sqlite:///migrations.sqlite3"
os.environ["SQLITE_BUSY_TIMEOUT_SECONDS"] = "1"
os.environ["WRITE_LOCK_LEASE_SECONDS"] = "30"

from app.services.data.persistence.contracts import MigrationRequest, MigrationStep, MigrationTombstone
from app.services.data.persistence.migrations import _run_domain_migrations_raw
from app.utils import generate_id

tombstone = MigrationTombstone(
    domain={mig_data["domain"]!r},
    migration_id={mig_data["migration_id"]!r},
    checksum={mig_data["checksum"]!r},
    owner_provider_id="test.stateful.default",
    state_schema_id="test_stateful",
)
req2 = MigrationRequest(
    domain={mig_data["domain"]!r},
    steps=(
        MigrationStep(
            domain={mig_data["domain"]!r},
            migration_id="002_core_state",
            checksum="chk_core_v1",
            statements=("CREATE TABLE core_placeholder (id INT PRIMARY KEY);",),
        ),
    ),
    tombstones=(tombstone,),
    request_id=generate_id("req"),
    complete_manifest=True,
)
res2 = _run_domain_migrations_raw(req2)
assert res2.applied_ids == ("002_core_state",)

# Assert no provider code was loaded
assert "fake_module" not in sys.modules

# Assert historical table and row survived
db_path = os.path.join(os.environ["DATA_DIR"], "migrations.sqlite3")
conn = sqlite3.connect(db_path)
try:
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM test_stateful_records WHERE record_id='record-1'")
    row = cursor.fetchone()
    assert row is not None and row[0] == "preserved"
finally:
    conn.close()

print("STAGE_2_OK")
"""
    res2 = run_in_fresh_process(repository_root=_REPO_ROOT, script=p2_script)
    assert res2.returncode == 0, f"Stage 2 failed: {res2.stderr}"
    assert "STAGE_2_OK" in res2.stdout

    # Stage 3: Reinstall compatible provider, verify row access
    p3_script = f"""
import os, sqlite3
os.environ["DATA_DIR"] = {db_dir_str!r}
os.environ["DATABASE_URL"] = "sqlite:///migrations.sqlite3"
os.environ["SQLITE_BUSY_TIMEOUT_SECONDS"] = "1"
os.environ["WRITE_LOCK_LEASE_SECONDS"] = "30"

from app.services.data.persistence.contracts import MigrationRequest, MigrationStep
from app.services.data.persistence.migrations import _run_domain_migrations_raw
from app.utils import generate_id

step1 = MigrationStep(
    domain={mig_data["domain"]!r},
    migration_id={mig_data["migration_id"]!r},
    checksum={mig_data["checksum"]!r},
    statements=({mig_data["sql"]!r},),
)
step2 = MigrationStep(
    domain={mig_data["domain"]!r},
    migration_id="002_core_state",
    checksum="chk_core_v1",
    statements=("CREATE TABLE core_placeholder (id INT PRIMARY KEY);",),
)
step3 = MigrationStep(
    domain={mig_data["domain"]!r},
    migration_id="003_v2_column",
    checksum="chk_v2_col",
    statements=("ALTER TABLE test_stateful_records ADD COLUMN notes TEXT DEFAULT '';",),
)
req3 = MigrationRequest(
    domain={mig_data["domain"]!r},
    steps=(step1, step2, step3),
    tombstones=(),
    request_id=generate_id("req"),
    complete_manifest=True,
)
res3 = _run_domain_migrations_raw(req3)
assert "003_v2_column" in res3.applied_ids

db_path = os.path.join(os.environ["DATA_DIR"], "migrations.sqlite3")
conn = sqlite3.connect(db_path)
try:
    cursor = conn.cursor()
    cursor.execute("SELECT record_id, value, notes FROM test_stateful_records WHERE record_id='record-1'")
    row = cursor.fetchone()
    assert row == ('record-1', 'preserved', '')
finally:
    conn.close()

print("STAGE_3_OK")
"""
    res3 = run_in_fresh_process(repository_root=_REPO_ROOT, script=p3_script)
    assert res3.returncode == 0, f"Stage 3 failed: {res3.stderr}"
    assert "STAGE_3_OK" in res3.stdout


def test_incompatible_state_schema_is_rejected(tmp_path: Path) -> None:
    """Verify stateful manifest with incompatible/invalid schema fields fails validation."""
    content = """
[provider]
id = "test.stateful.incompatible"
version = "2.0.0"
entry_point = "fake_module:factory"

[[provides]]
capability_id = "test.stateful.v2"
contract_version = "2.0.0"
cardinality = "exactly_one"

[runtime]
profiles = ["simulation"]
scopes = ["process"]
effect_classes = ["durable_compensatable"]
lifecycle = "scoped"
reload = "process_restart"

[state]
schema_id = "test_stateful"
schema_version = "2.0.0"
migration_manifest = "schema:test.stateful.v2"
compatible_prior_majors = [0]  # Invalid major
downgrade_policy = "reject"
uninstall_retention = "retain"
purge_requires_authorization = true
"""
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(content.strip(), encoding="utf-8")

    import pytest

    with pytest.raises(
        ManifestValidationError,
        match="compatible_prior_majors must contain positive integers",
    ):
        load_manifest(manifest_path)


def test_uninstall_does_not_expose_purge() -> None:
    """Verify that neither the data package root nor persistence subpackage exports any purge APIs."""
    import app.services.data as data_pkg
    import app.services.data.persistence as persist_pkg

    data_exports = getattr(data_pkg, "__all__", ())
    persist_exports = getattr(persist_pkg, "__all__", ())

    assert not any("purge" in exp.lower() for exp in data_exports)
    assert not any("purge" in exp.lower() for exp in persist_exports)
    assert not any("drop_all" in exp.lower() for exp in data_exports)

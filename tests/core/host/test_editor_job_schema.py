"""Verify host-owned additive job schema installation in isolated stores."""

import logging
import sqlite3
from contextlib import closing

from app.core.host.persistence import HostPersistence


def test_job_schema_is_idempotent_and_preserves_records(tmp_path, caplog):
    path = tmp_path / "host.db"
    path.touch()
    gateway = HostPersistence(path)
    caplog.set_level(logging.INFO)
    assert gateway.ensure_jobs_schema()["success"]
    assert gateway.create_records(
        "host_jobs", {"job_id": "keep", "status": "COMPLETED"}
    )["success"]
    assert gateway.ensure_jobs_schema()["success"]
    assert gateway.read_records("host_jobs")["data"]["records"][0]["job_id"] == "keep"
    assert "FR-host-job-schema: verified" in caplog.text


def test_incompatible_existing_job_table_is_not_migrated(tmp_path):
    path = tmp_path / "host.db"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE host_jobs (job_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO host_jobs VALUES ('keep')")
    gateway = HostPersistence(path)
    assert not gateway.ensure_jobs_schema()["success"]
    assert gateway.read_records("host_jobs")["data"]["records"] == [{"job_id": "keep"}]

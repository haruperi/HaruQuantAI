"""Schema-level evidence for the artifact catalog.

The catalog is internal support for Data's storage layer rather than a
registered feature, so this evidence lives in pytest. It indexes what the
dataset writer has written so a pinned read can select artifacts by recorded
time range without touching the filesystem.
"""

import re
import sqlite3

import pytest
from app.services.data.migrations.core import _CATALOG_SCHEMA_STATEMENTS

_NOW = "2026-08-03T00:00:00.000Z"
_DATASET = "ds-eurusd-m1"

_INSERT_DATASET = (
    "INSERT INTO data_datasets (dataset_id, dataset_kind, owner_domain, "
    "symbol_id, timeframe, provider_id, producer_ref, root_path, "
    "schema_version, normalization_version, timestamp_semantics, file_count, "
    "total_rows, total_bytes, min_ts_utc, max_ts_utc, state, request_id, "
    "correlation_id, created_at, updated_at) "
    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)

_INSERT_FILE = (
    "INSERT INTO data_partition_files (file_id, dataset_id, artifact_id, "
    "relative_path, format, content_hash, row_count, byte_size, min_ts_utc, "
    "max_ts_utc, schema_version, normalization_version, source_revision, "
    "provenance_json, license_json, verify_state, verified_at, request_id, "
    "correlation_id, created_at, updated_at) "
    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)


@pytest.fixture
def catalog():
    """Yield an in-memory catalog holding one dataset and one artifact."""
    con = sqlite3.connect(":memory:")
    for statement in _CATALOG_SCHEMA_STATEMENTS:
        con.execute(statement)
    con.execute(
        _INSERT_DATASET,
        (
            _DATASET,
            "candle",
            "data",
            "EURUSD",
            "M1",
            "mt5",
            None,
            "data/artifacts",
            "market.v1",
            "norm.v1",
            "bar_open",
            1,
            43_200,
            1_048_576,
            1_700_000_000,
            1_702_591_999,
            "ready",
            "req-1",
            "corr-1",
            _NOW,
            _NOW,
        ),
    )
    con.execute(
        _INSERT_FILE,
        (
            "file-1",
            _DATASET,
            "artifact-abc123",
            "eurusd/m1-2023-11.parquet",
            "parquet",
            "abc123",
            43_200,
            1_048_576,
            1_700_000_000,
            1_702_591_999,
            "market.v1",
            "norm.v1",
            "rev-7",
            "{}",
            "{}",
            "verified",
            _NOW,
            "req-1",
            "corr-1",
            _NOW,
            _NOW,
        ),
    )
    yield con
    con.close()


def test_overlap_predicate_keeps_what_between_would_drop(catalog):
    """Return an artifact that begins before the window and extends into it."""
    start, end = 1_701_000_000, 1_701_500_000
    overlapping = catalog.execute(
        "SELECT relative_path FROM data_partition_files "
        "WHERE dataset_id = ? AND max_ts_utc >= ? AND min_ts_utc <= ?",
        (_DATASET, start, end),
    ).fetchall()
    naive = catalog.execute(
        "SELECT relative_path FROM data_partition_files "
        "WHERE dataset_id = ? AND min_ts_utc BETWEEN ? AND ?",
        (_DATASET, start, end),
    ).fetchall()
    assert len(overlapping) == 1
    assert naive == [], "BETWEEN silently drops the artifact; that is the bug"


def test_a_failed_hash_is_visible_to_the_integrity_gate(catalog):
    """Let a pinned read fail closed on an unverifiable artifact."""
    unverifiable = (
        "SELECT COUNT(*) FROM data_partition_files WHERE dataset_id = ? "
        "AND verify_state IN ('hash_mismatch', 'missing')"
    )
    assert catalog.execute(unverifiable, (_DATASET,)).fetchone()[0] == 0
    catalog.execute(
        "UPDATE data_partition_files SET verify_state = 'hash_mismatch' "
        "WHERE file_id = ?",
        ("file-1",),
    )
    assert catalog.execute(unverifiable, (_DATASET,)).fetchone()[0] == 1


def test_a_fetch_cannot_claim_materialisation_without_a_dataset(catalog):
    """Reject an untraceable "we saved it somewhere" claim."""
    with pytest.raises(sqlite3.IntegrityError):
        catalog.execute(
            "INSERT INTO data_fetch_log (fetch_id, provider_id, symbol_id, "
            "data_kind, range_start_utc, range_end_utc, materialized, "
            "dataset_id, served_from, state, request_id, correlation_id, "
            "started_at, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "fetch-2",
                "mt5",
                "EURUSD",
                "candle",
                1,
                2,
                1,
                None,
                "broker",
                "succeeded",
                "req-2",
                "corr-2",
                _NOW,
                _NOW,
                _NOW,
            ),
        )


def test_a_dataset_declares_its_timestamp_semantics(catalog):
    """Make mixing bar-open and bar-close artifacts detectable at load."""
    semantics = catalog.execute(
        "SELECT timestamp_semantics FROM data_datasets WHERE dataset_id = ?",
        (_DATASET,),
    ).fetchone()[0]
    assert semantics == "bar_open"


def test_a_quality_event_names_the_artifact_it_concerns(catalog):
    """Attribute a finding to a specific content-addressed artifact."""
    catalog.execute(
        "INSERT INTO data_fetch_log (fetch_id, provider_id, symbol_id, "
        "data_kind, timeframe, range_start_utc, range_end_utc, rows_returned, "
        "materialized, dataset_id, served_from, fetch_latency_ms, state, "
        "error_code, request_id, correlation_id, started_at, finished_at, "
        "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "fetch-1",
            "mt5",
            "EURUSD",
            "candle",
            "M1",
            1_700_000_000,
            1_702_591_999,
            43_200,
            1,
            _DATASET,
            "broker",
            180,
            "succeeded",
            None,
            "req-1",
            "corr-1",
            _NOW,
            _NOW,
            _NOW,
            _NOW,
        ),
    )
    catalog.execute(
        "INSERT INTO data_quality_events (event_id, symbol_id, dataset_id, "
        "file_id, fetch_id, issue_type, severity, action_taken, ts_range_start, "
        "ts_range_end, affected_rows, detail_json, detected_at, request_id, "
        "correlation_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "qe-1",
            "EURUSD",
            _DATASET,
            "file-1",
            "fetch-1",
            "gap",
            "warning",
            "flagged",
            1_700_100_000,
            1_700_100_060,
            1,
            "{}",
            _NOW,
            "req-1",
            "corr-1",
            _NOW,
        ),
    )
    row = catalog.execute(
        "SELECT file_id, fetch_id FROM data_quality_events WHERE event_id = ?",
        ("qe-1",),
    ).fetchone()
    assert row == ("file-1", "fetch-1")


def test_coverage_is_answerable_without_touching_the_filesystem(catalog):
    """Answer "do I need to fetch?" from catalog rows alone."""
    row = catalog.execute(
        "SELECT MIN(min_ts_utc), MAX(max_ts_utc), SUM(row_count), COUNT(*) "
        "FROM data_partition_files "
        "WHERE dataset_id = ? AND verify_state <> 'missing'",
        (_DATASET,),
    ).fetchone()
    assert row == (1_700_000_000, 1_702_591_999, 43_200, 1)


def test_only_verification_state_is_not_manifest_derived():
    """Keep the catalog rebuildable by rescanning sidecar manifests."""
    joined = "\n".join(_CATALOG_SCHEMA_STATEMENTS)
    body = re.search(
        r"CREATE TABLE IF NOT EXISTS data_partition_files \((.*?)\n    \) STRICT",
        joined,
        re.DOTALL,
    )
    assert body is not None
    columns = {
        line.split()[0]
        for line in body.group(1).split("\n")
        if line.strip() and not line.strip().upper().startswith(("UNIQUE", "CHECK"))
    }
    index_local = {"verify_state", "verified_at"}
    assert index_local < columns
    assert len(columns - index_local) > 0

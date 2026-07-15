"""Unit tests for backfill key derivation, chunk execution, and recovery."""

import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import (
    BackfillChunkRequest,
    DataQualityReport,
    MarketDataset,
)
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.records import OHLCVRecord
from app.services.data.jobs.backfill import (
    derive_backfill_key,
    execute_backfill_chunk,
    recover_update_jobs,
)
from app.services.data.storage.database import execute_transaction
from app.services.data.storage.migrations import run_data_migrations


@pytest.fixture
def test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Setup test environment variables and database tables."""
    db_path = tmp_path / "data_jobs.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.name}")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    run_data_migrations(
        "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
    )
    return tmp_path


def test_backfill_key_is_canonical() -> None:
    """Test idempotency key derivation is deterministic and canonical."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    req1 = BackfillChunkRequest(
        job_id="job-1",
        source_id="binance",
        symbol="BTC/USD",
        data_kind="ohlcv",
        timeframe="M1",
        start=t,
        end=t + timedelta(hours=1),
        schema_version="v1",
        normalization_version="v1",
        max_records=100,
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )
    req2 = BackfillChunkRequest(
        job_id="job-2",  # Different job ID
        source_id="binance",
        symbol="BTC/USD",
        data_kind="ohlcv",
        timeframe="M1",
        start=t,
        end=t + timedelta(hours=1),
        schema_version="v1",
        normalization_version="v1",
        max_records=100,
        request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
    )
    # Checksum is identical because job_id is not in the key components list
    assert derive_backfill_key(req1) == derive_backfill_key(req2)


def test_chunk_execution_deduplication(
    test_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test duplicate backfill chunks return cached result without source fetch."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    req = BackfillChunkRequest(
        job_id="job-1",
        source_id="test",
        symbol="BTC/USD",
        data_kind="ohlcv",
        timeframe="M5",
        start=t,
        end=t + timedelta(hours=1),
        schema_version="v1",
        normalization_version="v1",
        max_records=100,
        request_id="req-9def222923677c46c532f127a566e618927942a9122451cf38f44a98a45cd6ee",
    )

    # Insert dummy job definition first
    insert_job_sql = (
        "INSERT INTO data_update_jobs ("
        "    job_id, source_id, symbols_json, timeframes_json, data_kinds_json, "
        "    start, enabled, created_at, request_id, state, recovery_state"
        ") VALUES ("
        "    ?, ?, '[\"BTC/USD\"]', '[\"M5\"]', '[\"ohlcv\"]', ?, 1, ?, ?, "
        "    'created', 'clean'"
        ")"
    )
    from app.services.data.contracts import StatementPlan, TransactionRequest

    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(insert_job_sql,),
                parameter_sets=(
                    (
                        "job-1",
                        "test",
                        t.isoformat(),
                        datetime.now(UTC).isoformat(),
                        "req-e1c98f93323acd1110614245c80be18779dae0d25a466e78f45c5502ad3617f4",
                    ),
                ),
                max_rows=1,
            ),
            request_id="req-e1c98f93323acd1110614245c80be18779dae0d25a466e78f45c5502ad3617f4",
        )
    )

    # Mock fetch_market_dataset and save_dataset
    mock_records = (
        OHLCVRecord(
            timestamp=t,
            source="test",
            source_symbol="BTC/USD",
            source_revision="v1",
            available_at=t,
            open=Decimal("100.0"),
            high=Decimal("101.0"),
            low=Decimal("99.0"),
            close=Decimal("100.5"),
            volume=Decimal("10.0"),
            price_unit="USD",
            volume_unit="Units",
        ),
    )
    mock_dataset = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="BTC/USD",
        timeframe="M5",
        records=mock_records,
        start=t,
        end=t,
        available_at=t,
        record_count=1,
        quality_report=DataQualityReport(
            quality_status="passed",
            quality_score=Decimal("1.0"),
            issues=(),
            warnings=(),
            record_count=1,
            checked_count=1,
            truncated=False,
            sample_limit=1000,
            schema_version="v1",
            generated_at=t,
        ),
        source_metadata={},
        license_metadata={},
        cache_status="miss",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-9def222923677c46c532f127a566e618927942a9122451cf38f44a98a45cd6ee",
    )

    monkeypatch.setattr(
        "app.services.data.jobs.backfill.fetch_market_dataset",
        lambda _: mock_dataset,
    )
    res1 = execute_backfill_chunk(req)
    assert res1.committed is True
    assert res1.record_count == 1

    # Second execution: should be deduplicated
    res2 = execute_backfill_chunk(req)
    assert res2.idempotency_key == res1.idempotency_key
    assert res2.chunk_id == res1.chunk_id


def test_chunk_execution_lease_locked(test_env: Path) -> None:
    """Test execute_backfill_chunk fails when job lease is locked by another request."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    req = BackfillChunkRequest(
        job_id="job-1",
        source_id="test",
        symbol="BTC/USD",
        data_kind="ohlcv",
        timeframe="M5",
        start=t,
        end=t + timedelta(hours=1),
        schema_version="v1",
        normalization_version="v1",
        max_records=100,
        request_id="req-f9268538b6e1c2ba98715a5eaa23c31bd74d6f6a1c924c1aedcf2eebe6f321b1",
    )

    # Insert job definition already locked by another request
    expires = (
        (datetime.now(UTC) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    )
    insert_job_sql = (
        "INSERT INTO data_update_jobs ("
        "    job_id, source_id, symbols_json, timeframes_json, data_kinds_json, "
        "    start, enabled, created_at, request_id, state, lease_owner, "
        "    lease_expires_at, recovery_state"
        ") VALUES ("
        "    ?, ?, '[\"BTC/USD\"]', '[\"M5\"]', '[\"ohlcv\"]', ?, 1, ?, ?, "
        "    'running', 'other-request', ?, 'clean'"
        ")"
    )
    from app.services.data.contracts import StatementPlan, TransactionRequest

    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(insert_job_sql,),
                parameter_sets=(
                    (
                        "job-1",
                        "test",
                        t.isoformat(),
                        datetime.now(UTC).isoformat(),
                        "req-e1c98f93323acd1110614245c80be18779dae0d25a466e78f45c5502ad3617f4",
                        expires,
                    ),
                ),
                max_rows=1,
            ),
            request_id="req-e1c98f93323acd1110614245c80be18779dae0d25a466e78f45c5502ad3617f4",
        )
    )

    with pytest.raises(DataError) as exc_info:
        execute_backfill_chunk(req)
    assert exc_info.value.args[0] == "CONCURRENT_WRITE_LOCKED"


def test_recovery_resumes_after_committed_chunk(test_env: Path) -> None:
    """Test recovery successfully processes active jobs and identifies corruption."""
    t = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    # Job 1 has a complete prepared data/manifest pair that can be published.
    pending_file = test_env / "job1.pending.parquet"
    pending_file.write_bytes(b"prepared-data")
    pending_file.with_suffix(".parquet.manifest.json").write_text("{}")
    clean_hash = hashlib.sha256(b"prepared-data").hexdigest()

    # Job 2: Running, last checkpoint points to file that doesn't exist (corrupted)
    # Insert both jobs
    insert_job_sql = (
        "INSERT INTO data_update_jobs ("
        "    job_id, source_id, symbols_json, timeframes_json, data_kinds_json, "
        "    start, enabled, created_at, request_id, state, last_checkpoint, "
        "    recovery_state"
        ") VALUES ("
        "    ?, ?, '[\"BTC/USD\"]', '[\"M5\"]', '[\"ohlcv\"]', ?, 1, ?, ?, "
        "    'running', ?, 'clean'"
        ")"
    )
    from app.services.data.contracts import StatementPlan, TransactionRequest

    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(insert_job_sql, insert_job_sql),
                parameter_sets=(
                    (
                        "job-clean",
                        "test",
                        t.isoformat(),
                        datetime.now(UTC).isoformat(),
                        "req-7dbf5afd61b2617f550fb1f9ad53d59b32b0006cca5c6062e61b5ecdc4fb5208",
                        "job1_chk.parquet",
                    ),
                    (
                        "job-corrupt",
                        "test",
                        t.isoformat(),
                        datetime.now(UTC).isoformat(),
                        "req-904920868f0ada429110c9717cd9246f74ed91b8f81acd08be2fb4042e17f208",
                        "missing.parquet",
                    ),
                ),
                max_rows=1,
            ),
            request_id="req-d5f4394607b72fcdb7c37a392c28de4c7cfa7ccd97ee49416eb7b22c4e5cc1fa",
        )
    )

    insert_checkpoint_sql = (
        "INSERT INTO data_backfill_checkpoints ("
        "idempotency_key, job_id, chunk_id, committed_start, committed_end, "
        "record_count, content_hash, checkpoint, artifact_temp, artifact_final, "
        "publication_state, request_id, created_at"
        ") VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, 'prepared', ?, ?)"
    )
    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(insert_checkpoint_sql, insert_checkpoint_sql),
                parameter_sets=(
                    (
                        "clean-key",
                        "job-clean",
                        "clean-chunk",
                        t.isoformat(),
                        (t + timedelta(hours=1)).isoformat(),
                        clean_hash,
                        "job1.pending.parquet",
                        "job1.pending.parquet",
                        "job1.parquet",
                        "req-7dbf5afd61b2617f550fb1f9ad53d59b32b0006cca5c6062e61b5ecdc4fb5208",
                        t.isoformat(),
                    ),
                    (
                        "corrupt-key",
                        "job-corrupt",
                        "corrupt-chunk",
                        t.isoformat(),
                        (t + timedelta(hours=1)).isoformat(),
                        clean_hash,
                        "missing.pending.parquet",
                        "missing.pending.parquet",
                        "missing.parquet",
                        "req-904920868f0ada429110c9717cd9246f74ed91b8f81acd08be2fb4042e17f208",
                        t.isoformat(),
                    ),
                ),
                max_rows=2,
            ),
            request_id="req-d5f4394607b72fcdb7c37a392c28de4c7cfa7ccd97ee49416eb7b22c4e5cc1fa",
        )
    )

    report = recover_update_jobs(
        "req-18ddccd09e275818a0371d15ba1dbd1487e11b4401e7d9e3b130cecc3448ba77"
    )
    assert "job-clean" in report.recovered_job_ids
    assert "job-corrupt" in report.blocked_job_ids

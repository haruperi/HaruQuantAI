"""Recoverably atomic historical backfill orchestration."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, cast

from app.services.data.access.historical import fetch_market_dataset
from app.services.data.config import get_data_settings
from app.services.data.contracts import (
    BackfillChunkRequest,
    BackfillChunkResult,
    DatasetSaveRequest,
    MarketDataRequest,
    RecoveryReport,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.contracts.errors import DataError
from app.services.data.storage.database import execute_transaction
from app.services.data.storage.datasets import save_dataset
from app.utils import Clock, generate_id, logger, utc_now

if TYPE_CHECKING:
    from app.services.data.contracts.market import MarketDataset

BACKFILL_MAX_RECORDS_PER_CHUNK: Final = 10_000
BACKFILL_MAX_SOURCE_SPAN: Final = timedelta(days=1)
JOB_LEASE_TIMEOUT_SECONDS: Final = 300


def derive_backfill_key(request: BackfillChunkRequest) -> str:
    """Derive a stable content-identity key for one bounded chunk request."""
    logger.info("Deriving backfill idempotency key")
    material = "|".join(
        (
            request.source_id,
            request.symbol,
            request.data_kind,
            request.timeframe or "none",
            request.start.astimezone(UTC).isoformat(),
            request.end.astimezone(UTC).isoformat(),
            request.schema_version,
            request.normalization_version,
        )
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _check_limits(request: BackfillChunkRequest) -> None:
    """Validate all chunk bounds before storage or source access."""
    logger.debug("Validating backfill chunk limits")
    if request.max_records > BACKFILL_MAX_RECORDS_PER_CHUNK:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={
                "max_records": request.max_records,
                "allowed": BACKFILL_MAX_RECORDS_PER_CHUNK,
            },
            request_id=request.request_id,
        )
    if request.end - request.start > BACKFILL_MAX_SOURCE_SPAN:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={"field": "source_span"},
            request_id=request.request_id,
        )


def _result_from_row(
    request: BackfillChunkRequest,
    row: Mapping[str, None | bool | int | float | str],
) -> BackfillChunkResult:
    """Build committed result evidence from one durable checkpoint row."""
    logger.debug("Building committed backfill result from durable evidence")
    return BackfillChunkResult(
        job_id=str(row["job_id"]),
        chunk_id=str(row["chunk_id"]),
        idempotency_key=str(row["idempotency_key"]),
        committed_start=datetime.fromisoformat(str(row["committed_start"])),
        committed_end=datetime.fromisoformat(str(row["committed_end"])),
        record_count=int(str(row["record_count"])),
        content_hash=str(row["content_hash"]),
        checkpoint=str(row["artifact_final"]),
        committed=True,
        request_id=request.request_id,
    )


def _committed_result(
    request: BackfillChunkRequest,
    key: str,
) -> BackfillChunkResult | None:
    """Return an existing committed idempotency result."""
    logger.debug("Checking committed backfill idempotency state")
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    """
                    SELECT job_id, chunk_id, idempotency_key, committed_start,
                           committed_end, record_count, content_hash,
                           artifact_final
                    FROM data_backfill_checkpoints
                    WHERE idempotency_key = ? AND publication_state = 'committed'
                    """.strip(),
                ),
                parameter_sets=((key,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )
    return _result_from_row(request, result.rows[0]) if result.rows else None


def _acquire_lease(request: BackfillChunkRequest, now: datetime) -> None:
    """Atomically acquire or renew the job lease with one conditional mutation."""
    logger.info("Acquiring atomic backfill lease for job %s", request.job_id)
    expires_at = now + timedelta(seconds=JOB_LEASE_TIMEOUT_SECONDS)
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    """
                    UPDATE data_update_jobs
                    SET state = 'running', lease_owner = ?, lease_expires_at = ?
                    WHERE job_id = ? AND (
                        state != 'running'
                        OR lease_owner = ?
                        OR lease_expires_at IS NULL
                        OR lease_expires_at <= ?
                    )
                    """.strip(),
                ),
                parameter_sets=(
                    (
                        request.request_id,
                        expires_at.isoformat(),
                        request.job_id,
                        request.request_id,
                        now.isoformat(),
                    ),
                ),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )
    if result.affected_rows > 0:
        return
    existing = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=("SELECT job_id FROM data_update_jobs WHERE job_id = ?",),
                parameter_sets=((request.job_id,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )
    code = "CONCURRENT_WRITE_LOCKED" if existing.rows else "JOB_NOT_FOUND"
    raise DataError(
        code, safe_details={"job_id": request.job_id}, request_id=request.request_id
    )


def _fetch_backfill_data(request: BackfillChunkRequest) -> MarketDataset:
    """Fetch one bounded canonical dataset and persist only safe failure state."""
    logger.info("Fetching canonical backfill observations")
    kind = cast(
        "Literal['bars', 'ticks', 'spreads']",
        {"ohlcv": "bars", "tick": "ticks", "spread": "spreads"}[request.data_kind],
    )
    market_request = MarketDataRequest(
        source_id=request.source_id,
        symbol=request.symbol,
        data_kind=kind,
        timeframe=request.timeframe,
        start=request.start,
        end=request.end,
        limit=request.max_records,
        use_cache=False,
        quality_failure_behavior="fail",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id=request.request_id,
    )
    try:
        return fetch_market_dataset(market_request)
    except DataError as error:
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        """
                        UPDATE data_update_jobs
                        SET last_run_status = 'failed', last_error = ?,
                            recovery_state = 'required'
                        WHERE job_id = ?
                        """.strip(),
                    ),
                    parameter_sets=((error.code, request.job_id),),
                    max_rows=1,
                ),
                request_id=request.request_id,
            )
        )
        raise


def _configured_data_dir(request_id: str) -> Path:
    """Resolve the required existing DATA_DIR without a working-directory fallback."""
    logger.debug("Resolving configured backfill storage root")
    try:
        data_dir = get_data_settings().data_dir
    except ValueError:
        data_dir = None
    if data_dir is None:
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"field": "DATA_DIR"},
            request_id=request_id,
        )
    root = data_dir.resolve()
    if not root.is_dir():
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details={"field": "DATA_DIR"},
            request_id=request_id,
        )
    return root


def _artifact_paths(
    request: BackfillChunkRequest,
    key: str,
) -> tuple[Path, Path, Path, Path]:
    """Create and verify deterministic paths under approved raw storage."""
    logger.debug("Resolving recoverable backfill artifact paths")
    root = _configured_data_dir(request.request_id)
    source_component = hashlib.sha256(request.source_id.encode()).hexdigest()[:16]
    symbol_component = hashlib.sha256(request.symbol.encode()).hexdigest()[:16]
    relative_base = Path("data/raw/backfill") / source_component / symbol_component
    pending_relative = relative_base / "pending" / f"{key}.parquet"
    final_relative = relative_base / f"{key}.parquet"
    pending = (root / pending_relative).resolve()
    final = (root / final_relative).resolve()
    approved_root = (root / "data/raw").resolve()
    if not pending.is_relative_to(approved_root) or not final.is_relative_to(
        approved_root
    ):
        raise DataError(
            "PERMISSION_DENIED",
            safe_details={"operation": "backfill_path"},
            request_id=request.request_id,
        )
    pending.parent.mkdir(parents=True, exist_ok=True)
    final.parent.mkdir(parents=True, exist_ok=True)
    return pending_relative, final_relative, pending, final


def _prepare_artifact(
    request: BackfillChunkRequest,
    dataset: MarketDataset,
    key: str,
    now: datetime,
) -> tuple[str, str, str, str]:
    """Write a pending artifact and durably record prepared publication state."""
    logger.info("Preparing recoverable backfill artifact")
    pending_relative, final_relative, _, _ = _artifact_paths(request, key)
    manifest = save_dataset(
        DatasetSaveRequest(
            dataset=dataset,
            relative_path=pending_relative,
            format="parquet",
            overwrite=False,
            request_id=request.request_id,
        )
    )
    chunk_id = f"chunk-{key}"
    execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    """
                    INSERT INTO data_backfill_checkpoints (
                        idempotency_key, job_id, chunk_id, committed_start,
                        committed_end, record_count, content_hash, checkpoint,
                        artifact_temp, artifact_final, publication_state,
                        request_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'prepared', ?, ?)
                    """.strip(),
                ),
                parameter_sets=(
                    (
                        key,
                        request.job_id,
                        chunk_id,
                        request.start.isoformat(),
                        request.end.isoformat(),
                        dataset.record_count,
                        manifest.content_hash,
                        str(pending_relative),
                        str(pending_relative),
                        str(final_relative),
                        request.request_id,
                        now.isoformat(),
                    ),
                ),
                max_rows=1,
            ),
            request_id=request.request_id,
        )
    )
    return chunk_id, manifest.content_hash, str(pending_relative), str(final_relative)


def _file_hash(path: Path) -> str:
    """Hash one bounded artifact without loading it into memory."""
    logger.debug("Hashing prepared backfill artifact")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _publish_artifact(
    request_id: str,
    pending_relative: str,
    final_relative: str,
    content_hash: str,
) -> None:
    """Atomically publish a verified prepared data/manifest pair."""
    logger.info("Publishing prepared backfill artifact")
    root = _configured_data_dir(request_id)
    pending = (root / pending_relative).resolve()
    final = (root / final_relative).resolve()
    pending_manifest = pending.with_suffix(pending.suffix + ".manifest.json")
    final_manifest = final.with_suffix(final.suffix + ".manifest.json")
    if final.exists():
        if _file_hash(final) != content_hash or not final_manifest.is_file():
            raise DataError(
                "CHECKPOINT_CORRUPTED",
                safe_details={"operation": "backfill_publish"},
                request_id=request_id,
            )
        return
    if not pending.is_file() or not pending_manifest.is_file():
        raise DataError(
            "CHECKPOINT_CORRUPTED",
            safe_details={"operation": "backfill_publish"},
            request_id=request_id,
        )
    if _file_hash(pending) != content_hash:
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={"operation": "backfill_publish"},
            request_id=request_id,
        )
    pending.replace(final)
    pending_manifest.replace(final_manifest)


def _finalize_checkpoint(
    request_id: str,
    job_id: str,
    key: str,
    final_relative: str,
) -> None:
    """Atomically finalize checkpoint and job evidence after publication."""
    logger.info("Finalizing committed backfill checkpoint")
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    """
                    UPDATE data_backfill_checkpoints
                    SET checkpoint = ?, publication_state = 'committed'
                    WHERE idempotency_key = ? AND publication_state = 'prepared'
                    """.strip(),
                    """
                    UPDATE data_update_jobs
                    SET last_run_status = 'succeeded', last_checkpoint = ?,
                        last_error = NULL, recovery_state = 'clean',
                        lease_owner = NULL, lease_expires_at = NULL
                    WHERE job_id = ?
                    """.strip(),
                ),
                parameter_sets=(
                    (final_relative, key),
                    (final_relative, job_id),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if not result.committed:
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={"operation": "backfill_finalize"},
            request_id=request_id,
        )


def execute_backfill_chunk(
    request: BackfillChunkRequest,
    *,
    clock: Clock | None = None,
) -> BackfillChunkResult:
    """Execute one bounded chunk through a recoverable publication protocol."""
    logger.info("Executing backfill chunk for job %s", request.job_id)
    _check_limits(request)
    key = derive_backfill_key(request)
    existing = _committed_result(request, key)
    if existing is not None:
        return existing
    now = utc_now(clock)
    _acquire_lease(request, now)
    dataset = _fetch_backfill_data(request)
    chunk_id, content_hash, pending_relative, final_relative = _prepare_artifact(
        request,
        dataset,
        key,
        now,
    )
    _publish_artifact(
        request.request_id,
        pending_relative,
        final_relative,
        content_hash,
    )
    _finalize_checkpoint(request.request_id, request.job_id, key, final_relative)
    return BackfillChunkResult(
        job_id=request.job_id,
        chunk_id=chunk_id,
        idempotency_key=key,
        committed_start=request.start,
        committed_end=request.end,
        record_count=dataset.record_count,
        content_hash=content_hash,
        checkpoint=final_relative,
        committed=True,
        request_id=request.request_id,
    )


def recover_update_jobs(
    request_id: str | None = None,
    *,
    clock: Clock | None = None,
) -> RecoveryReport:
    """Finish prepared publications and classify unrecoverable checkpoints."""
    rid = request_id or generate_id("req")
    logger.info("Recovering prepared DATA backfill publications")
    prepared = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    """
                    SELECT idempotency_key, job_id, content_hash,
                           artifact_temp, artifact_final
                    FROM data_backfill_checkpoints
                    WHERE publication_state = 'prepared'
                    ORDER BY created_at, idempotency_key
                    """.strip(),
                ),
                parameter_sets=((),),
                max_rows=1_000,
            ),
            request_id=rid,
        )
    )
    recovered: list[str] = []
    blocked: list[str] = []
    for row in prepared.rows:
        job_id = str(row["job_id"])
        try:
            _publish_artifact(
                rid,
                str(row["artifact_temp"]),
                str(row["artifact_final"]),
                str(row["content_hash"]),
            )
            _finalize_checkpoint(
                rid,
                job_id,
                str(row["idempotency_key"]),
                str(row["artifact_final"]),
            )
        except DataError:
            execute_transaction(
                TransactionRequest(
                    plan=StatementPlan(
                        statements=(
                            """
                            UPDATE data_update_jobs
                            SET state = 'blocked', recovery_state = 'blocked',
                                last_error = 'CHECKPOINT_CORRUPTED',
                                lease_owner = NULL, lease_expires_at = NULL
                            WHERE job_id = ?
                            """.strip(),
                        ),
                        parameter_sets=((job_id,),),
                        max_rows=1,
                    ),
                    request_id=rid,
                )
            )
            blocked.append(job_id)
        else:
            recovered.append(job_id)
    return RecoveryReport(
        recovered_job_ids=tuple(sorted(set(recovered))),
        blocked_job_ids=tuple(sorted(set(blocked))),
        recovered_at=utc_now(clock),
        request_id=rid,
    )


__all__ = ["derive_backfill_key", "execute_backfill_chunk", "recover_update_jobs"]

"""Explicit crash recovery for interrupted update jobs.

Recovery is **never** triggered at import time. It runs only when a caller asks, because
resuming ingestion is a governed action with side effects: it acquires leases, reads
checkpoints, and republishes work. A module that recovered on import would do all of
that as a side effect of someone typing ``import``.

Resumption starts after the last *committed* chunk. Partial work is never published, so
an interrupted run either completes its chunk or is replayed from the checkpoint before
it.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from app.services.data.contracts import DataError
from app.services.data.data_jobs.backfill import (
    _finalize_checkpoint,
    _publish_artifact,
)
from app.services.data.data_jobs.contracts import (
    RecoveryReport,
)
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.transactions import execute_transaction
from app.utils import Clock, generate_id, logger, utc_now

BACKFILL_MAX_RECORDS_PER_CHUNK: Final = 10_000
BACKFILL_MAX_SOURCE_SPAN: Final = timedelta(days=1)
JOB_LEASE_TIMEOUT_SECONDS: Final = 300


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


__all__ = [
    "recover_update_jobs",
]

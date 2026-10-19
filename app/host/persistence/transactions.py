"""Atomic batch persistence transactions and all-or-nothing multi-row operations.

Description:
    Provides transactional execution foundation for the host platform and data
    workspaces. Manages atomic multi-row batch writes (create, update, delete,
    upsert) under a single BEGIN IMMEDIATE transaction reservation in SQLite WAL
    mode. Guarantees all-or-nothing rollback semantics upon constraint
    violations, foreign key reference guard errors, or optimistic revision
    conflicts.

Purpose:
    FEAT-HOST-PERSISTENCE: Host platform and workspace isolated SQLite persistence.

Key Capabilities:
    - FR-HOST-PERSISTENCE-BATCH-TRANSACTIONS: Execute atomic multi-row batch writes.
      Associated: `apply_batch()`
      Logging: DEBUG emitted on transaction begin and operation execution;
      INFO on successful commit; ERROR and rollback on any failure.

Python API Usage:
    ```python
    from app.host.persistence.create import get_connection
    from app.host.persistence.transactions import BatchOperation, apply_batch

    conn = get_connection("data/database/haruquantai.db")
    operations = [
        BatchOperation(
            "create",
            "host_settings",
            data={"scope": "s", "key": "k", "value_json": "{}"},
        ),
        BatchOperation(
            "delete",
            "host_settings",
            pk_values={"scope": "s", "key": "old"},
        ),
    ]
    result = apply_batch(conn, operations)
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.persistence.transactions
    ```
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.create import (
    TABLE_PRIMARY_KEYS,
    PersistenceError,
    insert_row,
)
from app.host.persistence.delete import delete_record
from app.host.persistence.read import read_row_by_pk
from app.host.persistence.update import RevisionConflictError, update_record

__all__ = [
    "BatchOperation",
    "BatchResult",
    "TransactionsCLI",
    "apply_batch",
]

logger = get_logger(__name__)

BATCH_TRANSACTIONS_FR = "FR-HOST-PERSISTENCE-BATCH-TRANSACTIONS"


@dataclass(frozen=True)
class BatchOperation:
    """Specification of a single write operation within an atomic batch."""

    op_type: str  # "create" | "insert" | "update" | "delete" | "upsert"
    table: str
    data: Mapping[str, Any] | None = None
    pk_values: Mapping[str, Any] | None = None
    expected_revision: int | None = None
    revision_col: str = "revision"


@dataclass(frozen=True)
class BatchResult:
    """Summary of committed atomic batch transaction."""

    total_operations: int
    affected_rows: int
    details: Sequence[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert batch result to standard dictionary."""
        return {
            "total_operations": self.total_operations,
            "affected_rows": self.affected_rows,
            "details": list(self.details),
        }


def _execute_upsert(
    conn: sqlite3.Connection,
    idx: int,
    op: BatchOperation,
) -> tuple[int, dict[str, Any]]:
    """Execute an upsert operation by checking current row by primary key."""
    if not op.data:
        raise PersistenceError(
            f"Upsert operation at index {idx} on '{op.table}' requires non-empty data."
        )
    pk_cols = TABLE_PRIMARY_KEYS[op.table]
    target_pk = op.pk_values or {col: op.data[col] for col in pk_cols if col in op.data}
    if len(target_pk) != len(pk_cols):
        raise PersistenceError(
            f"Upsert operation at index {idx} on '{op.table}' requires "
            f"complete primary key specification."
        )
    existing = read_row_by_pk(conn, op.table, target_pk)
    if existing is not None:
        affected = update_record(
            conn,
            op.table,
            target_pk,
            op.data,
            expected_revision=op.expected_revision,
            revision_col=op.revision_col,
            commit=False,
        )
        return (
            affected,
            {
                "index": idx,
                "op": "upsert",
                "table": op.table,
                "status": "updated",
                "affected": affected,
            },
        )
    pk_res = insert_row(conn, op.table, op.data, commit=False)
    return (
        1,
        {
            "index": idx,
            "op": "upsert",
            "table": op.table,
            "status": "inserted",
            "key": pk_res,
        },
    )


def _execute_operation(
    conn: sqlite3.Connection,
    idx: int,
    op: BatchOperation,
) -> tuple[int, dict[str, Any]]:
    """Execute a single batch operation within an active transaction."""
    op_type = op.op_type.lower()
    table = op.table

    if table not in TABLE_PRIMARY_KEYS:
        raise PersistenceError(
            f"Table '{table}' at batch index {idx} is not in approved table set."
        )

    if op_type in ("create", "insert"):
        if not op.data:
            raise PersistenceError(
                f"Create operation at index {idx} on '{table}' requires non-empty data."
            )
        pk_res = insert_row(conn, table, op.data, commit=False)
        return (
            1,
            {
                "index": idx,
                "op": op_type,
                "table": table,
                "status": "created",
                "key": pk_res,
            },
        )

    if op_type == "update":
        if not op.pk_values or not op.data:
            raise PersistenceError(
                f"Update operation at index {idx} on '{table}' requires both "
                f"pk_values and data."
            )
        affected = update_record(
            conn,
            table,
            op.pk_values,
            op.data,
            expected_revision=op.expected_revision,
            revision_col=op.revision_col,
            commit=False,
        )
        return (
            affected,
            {
                "index": idx,
                "op": op_type,
                "table": table,
                "status": "updated",
                "affected": affected,
            },
        )

    if op_type == "delete":
        if not op.pk_values:
            raise PersistenceError(
                f"Delete operation at index {idx} on '{table}' requires pk_values."
            )
        affected = delete_record(conn, table, op.pk_values, commit=False)
        return (
            affected,
            {
                "index": idx,
                "op": op_type,
                "table": table,
                "status": "deleted",
                "affected": affected,
            },
        )

    if op_type == "upsert":
        return _execute_upsert(conn, idx, op)

    raise PersistenceError(
        f"Unsupported batch operation type '{op.op_type}' at index {idx}."
    )


def apply_batch(
    conn: sqlite3.Connection,
    operations: Sequence[BatchOperation],
) -> BatchResult:
    """Execute atomic multi-row batch writes with all-or-nothing rollback.

    Executes all operations inside a single BEGIN IMMEDIATE transaction.
    If any operation encounters a constraint violation, invalid table,
    foreign key reference guard, or optimistic revision conflict, the entire
    transaction rolls back completely and re-raises the failure.

    Args:
        conn: Open SQLite connection. Must be idle with no active transaction.
        operations: Ordered sequence of BatchOperation instances to apply.

    Returns:
        BatchResult summarizing total operations, affected rows, and details.

    Raises:
        PersistenceError: If connection is busy, table is invalid, or constraint fails.
        RevisionConflictError: If an optimistic revision expectation fails.
    """
    if conn.in_transaction:
        logger.error(
            "%s: caller transaction already active",
            BATCH_TRANSACTIONS_FR,
            extra={"fr_id": BATCH_TRANSACTIONS_FR},
        )
        raise PersistenceError(
            "Batch operations require an idle connection with no active transaction."
        )

    if not operations:
        logger.debug(
            "%s: empty operations sequence, returning no-op result",
            BATCH_TRANSACTIONS_FR,
            extra={"fr_id": BATCH_TRANSACTIONS_FR},
        )
        return BatchResult(total_operations=0, affected_rows=0, details=[])

    logger.debug(
        "%s: beginning atomic batch transaction with %d operations",
        BATCH_TRANSACTIONS_FR,
        len(operations),
        extra={"fr_id": BATCH_TRANSACTIONS_FR, "operations_count": len(operations)},
    )

    details: list[dict[str, Any]] = []
    total_affected = 0

    conn.execute("BEGIN IMMEDIATE")
    try:
        for idx, op in enumerate(operations):
            affected, detail = _execute_operation(conn, idx, op)
            total_affected += affected
            details.append(detail)
        conn.commit()
    except Exception as err:
        conn.rollback()
        logger.exception(
            "%s: batch transaction failed, rolled back completely",
            BATCH_TRANSACTIONS_FR,
            extra={"fr_id": BATCH_TRANSACTIONS_FR, "error": str(err)},
        )
        if isinstance(err, RevisionConflictError):
            raise
        raise PersistenceError(f"Batch transaction failed: {err}") from err

    logger.info(
        "%s: committed atomic batch transaction with %d operations (%d affected rows)",
        BATCH_TRANSACTIONS_FR,
        len(operations),
        total_affected,
        extra={
            "fr_id": BATCH_TRANSACTIONS_FR,
            "total_operations": len(operations),
            "affected_rows": total_affected,
        },
    )
    return BatchResult(
        total_operations=len(operations),
        affected_rows=total_affected,
        details=details,
    )


class TransactionsCLI:
    """Headless CLI formatter for transactions presentation."""

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format batch execution result into human-readable terminal output."""
        logger.debug(
            "%s: formatting CLI output",
            BATCH_TRANSACTIONS_FR,
            extra={"fr_id": BATCH_TRANSACTIONS_FR},
        )
        lines = [f"{k}: {v}" for k, v in data.items()]
        return "\n".join(lines)


if __name__ == "__main__":
    import tempfile

    from app.host.persistence.create import create_schema, get_connection

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_db = Path(tmp_dir) / "demo.db"
        demo_conn = get_connection(tmp_db)
        create_schema(demo_conn)
        demo_ops = [
            BatchOperation(
                op_type="create",
                table="host_settings",
                data={
                    "scope": "sys",
                    "key": "demo_key",
                    "value_json": '{"status": "ok"}',
                    "updated_at_utc": "2026-10-19T00:00:00Z",
                },
            ),
            BatchOperation(
                op_type="update",
                table="host_settings",
                pk_values={"scope": "sys", "key": "demo_key"},
                data={"value_json": '{"status": "updated"}'},
            ),
        ]
        batch_out = apply_batch(demo_conn, demo_ops)
        demo_conn.close()
        print(TransactionsCLI.format_output(batch_out.to_dict()))

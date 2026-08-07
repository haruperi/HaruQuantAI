"""Create operations for Research-owned artifact metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    run_domain_migrations,
)
from app.services.research.contracts.errors import ValidationError
from app.services.research.migrations import build_research_migration_request
from app.utils import get_logger

logger = get_logger(__name__)


def create_artifact_metadata(
    *,
    relative_path: str,
    format_name: str,
    size_bytes: int,
    sha256: str,
    atomic: bool,
    schema_version: str,
    audit_event_id: str,
    request_id: str,
    correlation_id: str,
) -> Mapping[str, object]:
    """Record one Research artifact manifest row through Data.

    Args:
        relative_path: Approved path relative to the Research artifact root.
        format_name: Serialized artifact format.
        size_bytes: Exact serialized byte count.
        sha256: Exact serialized content digest.
        atomic: Whether the file replacement was atomic.
        schema_version: Artifact schema version.
        audit_event_id: Authorizing audit event identifier.
        request_id: Request trace identifier.
        correlation_id: Cross-operation trace identifier.

    Returns:
        Detached normalized metadata row.

    Raises:
        ValidationError: If migration or insertion cannot be confirmed.
    """
    logger.info("Persisting Research artifact metadata")
    migration = run_domain_migrations(
        cast("Any", build_research_migration_request(request_id))
    )
    if migration.status != "success" or migration.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "MIGRATION_FAILED")
    statement = """INSERT INTO research_artifacts (
        relative_path, format, size_bytes, sha256, atomic, schema_version,
        audit_event_id, request_id, correlation_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(relative_path) DO UPDATE SET
        format = excluded.format,
        size_bytes = excluded.size_bytes,
        sha256 = excluded.sha256,
        atomic = excluded.atomic,
        schema_version = excluded.schema_version,
        audit_event_id = excluded.audit_event_id,
        request_id = excluded.request_id,
        correlation_id = excluded.correlation_id"""
    parameters = (
        relative_path,
        format_name,
        size_bytes,
        sha256,
        int(atomic),
        schema_version,
        audit_event_id,
        request_id,
        correlation_id,
    )
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(cast("tuple[Any, ...]", parameters),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "METADATA_WRITE_FAILED")
    result = cast("Any", response.data)
    if result.affected_rows != 1:
        raise ValidationError("RES_PERSISTENCE_FAILED", "METADATA_CONFLICT")
    return {
        "relative_path": relative_path,
        "format": format_name,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "atomic": atomic,
        "schema_version": schema_version,
        "audit_event_id": audit_event_id,
        "request_id": request_id,
        "correlation_id": correlation_id,
    }


__all__ = ("create_artifact_metadata",)

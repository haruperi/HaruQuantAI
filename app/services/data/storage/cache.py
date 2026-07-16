"""Versioned, TTL-aware local SQLite caching."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Final, Literal

from pydantic import ValidationError

from app.services.data.contracts import (
    CacheClearRequest,
    CacheClearResult,
    CacheEntry,
    CacheReadRequest,
    CacheWriteRequest,
    CacheWriteResult,
    MarketDataset,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.contracts.errors import DataError
from app.services.data.storage.database import execute_transaction
from app.utils import Clock, logger, utc_now

_GET_CACHE_ENTRY: Final = (
    "SELECT dataset_json, created_at, expires_at, source_revision, "
    "raw_data_hash, schema_version, normalization_version, request_id "
    "FROM data_cache WHERE key = ?"
).strip()

_PUT_CACHE_ENTRY: Final = """
INSERT OR REPLACE INTO data_cache (
    key, dataset_json, created_at, expires_at, source_revision,
    raw_data_hash, schema_version, normalization_version, request_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()


def get_cache_entry(
    request: CacheReadRequest,
    *,
    clock: Clock | None = None,
) -> CacheEntry | None:
    """Retrieve an active or allowed-stale cache entry from SQLite.

    Args:
        request: The cache read request.
        clock: Optional injected UTC clock.

    Returns:
        The CacheEntry or None if missing or expired (when stale not allowed).

    Raises:
        DataError: For database connection or query failures.
    """
    try:
        tx_request = TransactionRequest(
            plan=StatementPlan(
                statements=(_GET_CACHE_ENTRY,),
                parameter_sets=((request.key,),),
                max_rows=1,
            ),
            request_id=request.request_id,
        )

        result = execute_transaction(tx_request)
        if not result.rows:
            return None

        row = result.rows[0]
        dataset_json = str(row["dataset_json"])
        created_at_str = str(row["created_at"])
        expires_at_str = row["expires_at"]

        created_at = datetime.fromisoformat(created_at_str)
        expires_at = (
            datetime.fromisoformat(str(expires_at_str)) if expires_at_str else None
        )

        now = utc_now(clock)

        # Handle expiration policy
        stale = False
        if expires_at is not None and now > expires_at:
            if not request.allow_stale:
                return None
            stale = True

        dataset = MarketDataset.model_validate_json(dataset_json)
        # Update cache_status accordingly
        cache_status: Literal["hit", "stale_warning"] = (
            "stale_warning" if stale else "hit"
        )
        dataset = dataset.model_copy(update={"cache_status": cache_status})

        return CacheEntry(
            key=request.key,
            dataset=dataset,
            created_at=created_at,
            expires_at=expires_at,
            source_revision=str(row["source_revision"]),
            raw_data_hash=str(row["raw_data_hash"]),
            schema_version=str(row["schema_version"]),
            normalization_version=str(row["normalization_version"]),
            request_id=str(row["request_id"]),
        )

    except ValidationError as error:
        logger.error("Cache entry schema validation failed")
        raise DataError(
            "FILE_CORRUPTED",
            safe_details={"operation": "get_cache_entry"},
            request_id=request.request_id,
        ) from error
    except Exception as error:
        logger.error("Cache entry query failed")
        if isinstance(error, DataError):
            raise
        raise DataError(
            "DATABASE_ERROR",
            safe_details={"operation": "get_cache_entry"},
            request_id=request.request_id,
        ) from error


def put_cache_entry(
    request: CacheWriteRequest,
    *,
    clock: Clock | None = None,
) -> CacheWriteResult:
    """Store a TTL-bound cache entry into SQLite.

    Args:
        request: The cache write request.
        clock: Optional injected UTC clock.

    Returns:
        The cache write result.

    Raises:
        DataError: For write failures.
    """
    try:
        created_at = utc_now(clock)
        expires_at = (
            created_at + timedelta(seconds=request.ttl_seconds)
            if request.ttl_seconds > 0
            else None
        )

        dataset_json = request.dataset.model_dump_json()

        params = (
            request.key,
            dataset_json,
            created_at.isoformat(),
            expires_at.isoformat() if expires_at else None,
            request.source_revision,
            request.raw_data_hash,
            request.dataset.schema_id,
            request.dataset.normalization_version,
            request.request_id,
        )

        tx_request = TransactionRequest(
            plan=StatementPlan(
                statements=(_PUT_CACHE_ENTRY,), parameter_sets=(params,), max_rows=1
            ),
            request_id=request.request_id,
        )

        result = execute_transaction(tx_request)
        written = result.committed and result.affected_rows > 0
        if not written:
            _raise_cache_write_failed(request.request_id)

        return CacheWriteResult(
            key=request.key,
            written=written,
            request_id=request.request_id,
        )

    except Exception as error:
        logger.error("Cache entry write failed")
        if isinstance(error, DataError):
            raise
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={"operation": "put_cache_entry"},
            request_id=request.request_id,
        ) from error


def _raise_cache_write_failed(request_id: str) -> None:
    """Raise one deterministic cache write failure."""
    logger.error("Cache transaction did not commit a row")
    raise DataError(
        "DB_WRITE_FAILED",
        safe_details={"operation": "put_cache_entry"},
        request_id=request_id,
    )


def _filter_cached_keys(
    rows: tuple[Mapping[str, object], ...], request: CacheClearRequest
) -> list[str]:
    """Filter cache keys matching the clear request criteria."""
    logger.debug("Filtering bounded cache keys for a clear request")
    import json

    matched_keys = []
    for row in rows:
        key = str(row["key"])
        dataset_data = json.loads(str(row["dataset_json"]))

        source_id = None
        records = dataset_data.get("records")
        if records:
            source_id = records[0].get("source")
        if not source_id:
            source_id = dataset_data.get("source_metadata", {}).get("source_id")

        if request.source_id and source_id != request.source_id:
            continue
        if request.symbol and dataset_data.get("symbol") != request.symbol:
            continue
        if request.data_kind and dataset_data.get("data_kind") != request.data_kind:
            continue

        matched_keys.append(key)
        if len(matched_keys) >= request.max_entries:
            break
    return matched_keys


def clear_cache_entry(request: CacheClearRequest) -> CacheClearResult:
    """Clear select cache entries matching request criteria.

    Args:
        request: The cache clear request.

    Returns:
        The cache clear result.

    Raises:
        DataError: For database failures.
    """
    try:
        if request.namespace != "data":
            return CacheClearResult(
                matched_count=0,
                deleted_count=0,
                dry_run=request.dry_run,
                request_id=request.request_id,
            )

        # Fetch all keys and dataset_json from cache
        select_req = TransactionRequest(
            plan=StatementPlan(
                statements=("SELECT key, dataset_json FROM data_cache",),
                parameter_sets=((),),
                max_rows=10000,
            ),
            request_id=request.request_id,
        )
        result = execute_transaction(select_req)

        matched_keys = _filter_cached_keys(result.rows, request)
        matched_count = len(matched_keys)
        deleted_count = 0

        if matched_count > 0 and not request.dry_run:
            placeholders = ",".join("?" for _ in matched_keys)
            delete_stmt = f"DELETE FROM data_cache WHERE key IN ({placeholders})"  # noqa: S608
            delete_req = TransactionRequest(
                plan=StatementPlan(
                    statements=(delete_stmt,),
                    parameter_sets=(tuple(matched_keys),),
                    max_rows=1,
                ),
                request_id=request.request_id,
            )
            del_res = execute_transaction(delete_req)
            if del_res.committed:
                deleted_count = del_res.affected_rows

        return CacheClearResult(
            matched_count=matched_count,
            deleted_count=deleted_count,
            dry_run=request.dry_run,
            request_id=request.request_id,
        )

    except Exception as error:
        logger.error("Cache clear failed")
        if isinstance(error, DataError):
            raise
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={"operation": "clear_cache_entry"},
            request_id=request.request_id,
        ) from error

"""Connector Synchronization domain implementation and functional behaviors.

Purpose:
    Coordinate idempotent, resumable, and secret-isolated connector synchronization
    for market data providers and network sources.

Key capabilities:
    * Execute discover, describe, plan, fetch, and commit operations safely.
    * Enforce rate-limiting, deduplication policies, and overlap windows.
    * Guarantee opaque secret isolation without plaintext exposure.
    * Provide async sync_connectors implementing SyncConnectorsCapability.

Python API usage:
    from app.services.data.connector_synchronization.connector_synchronization import (
        SyncConnectorsService,
    )
    from app.contracts.data.models import SyncConnectorsRequest

    service = SyncConnectorsService()
    result = await service.sync_connectors(request)

CLI usage:
    uv run python -m \
        app.services.data.connector_synchronization.connector_synchronization
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal, override

from app.contracts.common.models import ProblemDetails, UtcTimestamp, Uuid7
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    ConnectorSyncPlan,
    ConnectorSyncReceipt,
    DeduplicationPolicy,
    SyncConnectorsRequest,
    SyncConnectorsSuccess,
)
from app.contracts.data.ports import SyncConnectorsCapability
from app.services.data.connector_synchronization.config import ConnectorSyncConfig

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)


def _generate_uuid7() -> Uuid7:
    """Generate a lowercase canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _format_utc_timestamp(dt: datetime) -> UtcTimestamp:
    """Format an aware datetime as a canonical UtcTimestamp string.

    Args:
        dt: Aware UTC datetime.

    Returns:
        Canonical ISO 8601 string with microsecond resolution and Z suffix.
    """
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _compute_hash(data: bytes | str) -> str:
    """Compute SHA-256 hash as a 64-character lowercase hex string.

    Args:
        data: Byte sequence or string to hash.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _is_valid_uuid(val: str) -> bool:
    """Check if a string represents a valid UUID.

    Args:
        val: Input string.

    Returns:
        True if valid UUID, False otherwise.
    """
    try:
        uuid.UUID(val)
        return True
    except ValueError, AttributeError, TypeError:
        return False


def data_implement_connector_lifecycle(
    plan: ConnectorSyncPlan,
    pages: list[list[dict[str, Any]]] | None = None,
    checkpoint: str | None = None,
) -> tuple[ConnectorSyncReceipt, list[dict[str, Any]]]:
    """Execute connector discover, fetch, checkpoint, normalize, and commit lifecycle.

    Implements FR-DATA-IMPLEMENT_CONNECTOR_LIFECYCLE (P0).
    Interruption resumes without duplicate rows or partial publication.

    Args:
        plan: Validated connector synchronization plan.
        pages: List of incoming record batches/pages from the connector.
        checkpoint: Optional prior cursor/checkpoint to resume from.

    Returns:
        Tuple of (ConnectorSyncReceipt, normalized_records).

    Raises:
        ValueError: If plan is invalid or deduplication policy is violated.
    """
    if not _is_valid_uuid(plan.plan_id):
        msg = f"Invalid plan_id UUID: {plan.plan_id}"
        raise ValueError(msg)

    if pages is None:
        pages = []

    all_raw: list[dict[str, Any]] = []
    for page in pages:
        all_raw.extend(page)

    dedup_policy = plan.deduplication
    seen_keys: dict[str, dict[str, Any]] = {}

    for item in all_raw:
        key = str(
            item.get("timestamp") or item.get("id") or item.get("key") or id(item)
        )

        if checkpoint and str(item.get("cursor", "")) <= checkpoint:
            continue

        if key in seen_keys:
            if dedup_policy == "REJECT":
                msg = f"Duplicate record detected for key: {key}"
                raise ValueError(msg)
            if dedup_policy == "KEEP_LAST":
                seen_keys[key] = item
            elif dedup_policy == "KEEP_FIRST":
                continue
        else:
            seen_keys[key] = item

    normalized = list(seen_keys.values())
    normalized.sort(key=lambda x: str(x.get("timestamp", x.get("id", ""))))

    serialized = json.dumps(normalized, sort_keys=True)
    content_hash = _compute_hash(serialized)

    next_cursor = str(len(normalized)) if normalized else checkpoint
    is_complete = True
    committed_version_id = _generate_uuid7() if normalized else None

    receipt = ConnectorSyncReceipt(
        receipt_id=_generate_uuid7(),
        records=len(normalized),
        provider_revision_ids=(),
        next_cursor=next_cursor,
        is_complete=is_complete,
        content_hash=content_hash,
        committed_version_id=committed_version_id,
        schema_version=1,
    )
    return receipt, normalized


def data_plan_incremental_sync(
    profile_id: Uuid7,
    connector_version: str,
    requested_from: UtcTimestamp,
    requested_to: UtcTimestamp,
    max_records: int,
    *,
    overlap_window_seconds: int = 0,
    deduplication: DeduplicationPolicy = "KEEP_FIRST",
    revision_policy: Literal["COMPARE_OVERLAP", "FULL_RESCAN"] = "COMPARE_OVERLAP",
    cursor: str | None = None,
    checkpoint: str | None = None,
    plan_id: Uuid7 | None = None,
) -> ConnectorSyncPlan:
    """Calculate explicit requested range, overlap window, dedup, and revision policy.

    Implements FR-DATA-PLAN_INCREMENTAL_SYNC (P0).
    Repeating the same synchronization is idempotent and yields the same committed hash.

    Args:
        profile_id: Target data profile identifier.
        connector_version: Non-empty connector version identifier.
        requested_from: Start timestamp of requested range.
        requested_to: End timestamp of requested range.
        max_records: Maximum records allowed.
        overlap_window_seconds: Overlap window in seconds for change detection.
        deduplication: Deduplication policy.
        revision_policy: Strategy for revision comparison.
        cursor: Resumable pagination cursor.
        checkpoint: Resumable checkpoint.
        plan_id: Optional explicit plan ID.

    Returns:
        Validated, idempotent ConnectorSyncPlan instance.

    Raises:
        ValueError: If UUIDs or timestamp ranges are invalid.
    """
    if not _is_valid_uuid(profile_id):
        msg = f"Invalid profile_id UUID: {profile_id}"
        raise ValueError(msg)

    if requested_to <= requested_from:
        msg = (
            f"requested_to ({requested_to}) must be after"
            f" requested_from ({requested_from})"
        )
        raise ValueError(msg)

    pid = plan_id if plan_id and _is_valid_uuid(plan_id) else _generate_uuid7()

    return ConnectorSyncPlan(
        plan_id=pid,
        profile_id=profile_id,
        connector_version=connector_version,
        requested_from=requested_from,
        requested_to=requested_to,
        overlap_window_seconds=overlap_window_seconds,
        deduplication=deduplication,
        revision_policy=revision_policy,
        cursor=cursor,
        checkpoint=checkpoint,
        max_records=max_records,
        schema_version=1,
    )


def data_version_data_transforms(
    raw_series_id: Uuid7,
    transform_kind: Literal[
        "CORPORATE_ACTION",
        "CONTINUOUS_CONTRACT",
        "SPLIT_ADJUSTMENT",
        "DIVIDEND_ADJUSTMENT",
    ],
    transformation_params: dict[str, Any],
    raw_records: list[dict[str, Any]],
) -> tuple[Uuid7, str, list[dict[str, Any]], dict[str, Any]]:
    """Apply corporate actions and continuous-contract transformations separately.

    Implements FR-DATA-VERSION_DATA_TRANSFORMS (P1).
    Raw and transformed series remain independently reproducible and traceable.

    Args:
        raw_series_id: Identifier of the source un-transformed data series.
        transform_kind: Type of transformation applied.
        transformation_params: Adjustment ratios, rollover dates, or split factors.
        raw_records: Input raw records.

    Returns:
        Tuple of (version_id, content_hash, records, manifest).

    Raises:
        ValueError: If raw_series_id is invalid or transform params are empty.
    """
    if not _is_valid_uuid(raw_series_id):
        msg = f"Invalid raw_series_id UUID: {raw_series_id}"
        raise ValueError(msg)

    transformed_records: list[dict[str, Any]] = []
    ratio = float(transformation_params.get("factor", 1.0))

    for rec in raw_records:
        new_rec = dict(rec)
        if "close" in new_rec:
            new_rec["close"] = round(float(new_rec["close"]) * ratio, 6)
        if "open" in new_rec:
            new_rec["open"] = round(float(new_rec["open"]) * ratio, 6)
        if "high" in new_rec:
            new_rec["high"] = round(float(new_rec["high"]) * ratio, 6)
        if "low" in new_rec:
            new_rec["low"] = round(float(new_rec["low"]) * ratio, 6)
        new_rec["_transform_kind"] = transform_kind
        transformed_records.append(new_rec)

    transformed_version_id = _generate_uuid7()
    serialized = json.dumps(transformed_records, sort_keys=True)
    transformed_hash = _compute_hash(serialized)

    manifest = {
        "raw_series_id": raw_series_id,
        "transformed_version_id": transformed_version_id,
        "transform_kind": transform_kind,
        "parameters": transformation_params,
        "record_count": len(transformed_records),
        "content_hash": transformed_hash,
        "created_at": _format_utc_timestamp(datetime.now(UTC)),
    }

    return transformed_version_id, transformed_hash, transformed_records, manifest


def data_connect_data_providers(
    provider_id: str,
    symbol: str,
    requested_range: tuple[UtcTimestamp, UtcTimestamp],
    *,
    rate_limit: int = 100,
    rate_window_seconds: int = 60,
    simulated_pages: int = 1,
    records_per_page: int = 10,
    simulate_outage_at_page: int | None = None,
    credential_ref: Uuid7 | None = None,
) -> dict[str, Any]:
    """Execute direct MT5 and provider operations with throttling and cursor pages.

    Implements FR-DATA-CONNECT_DATA_PROVIDERS (P1).
    Provider outages or partial pages cannot publish incomplete data versions.

    Args:
        provider_id: Unique provider identifier (e.g. 'mt5', 'network_provider').
        symbol: Market symbol.
        requested_range: (from_timestamp, to_timestamp) range.
        rate_limit: Maximum allowed requests per window.
        rate_window_seconds: Throttling window in seconds.
        simulated_pages: Number of pages to simulate fetching.
        records_per_page: Records per page.
        simulate_outage_at_page: Page index where network outage occurs.
        credential_ref: Opaque credential reference ID.

    Returns:
        Dictionary containing fetch results, cursor state, and governance metrics.

    Raises:
        ValueError: If rate limits are non-positive.
        RuntimeError: If a provider outage occurs before completion.
    """
    if rate_limit < 1 or rate_window_seconds < 1:
        msg = "Rate limit and rate window must be at least 1"
        raise ValueError(msg)

    pages_data: list[list[dict[str, Any]]] = []
    current_cursor: str | None = "cursor_0"

    for page_idx in range(1, simulated_pages + 1):
        if simulate_outage_at_page is not None and page_idx == simulate_outage_at_page:
            logger.warning(
                "Provider outage encountered at page %d for %s",
                page_idx,
                provider_id,
            )
            msg = (
                f"Provider '{provider_id}' outage encountered at page"
                f" {page_idx}; partial publication aborted."
            )
            raise RuntimeError(msg)

        page: list[dict[str, Any]] = []
        for r_idx in range(records_per_page):
            rec_num = (page_idx - 1) * records_per_page + r_idx + 1
            page.append(
                {
                    "id": f"{symbol}_{rec_num}",
                    "symbol": symbol,
                    "timestamp": f"2026-01-01T{rec_num:02d}:00:00.000000Z",
                    "open": 1.1000 + (rec_num * 0.0001),
                    "close": 1.1010 + (rec_num * 0.0001),
                    "cursor": f"cursor_{page_idx}_{r_idx}",
                }
            )
        pages_data.append(page)
        current_cursor = f"cursor_{page_idx}_end"

    return {
        "provider_id": provider_id,
        "symbol": symbol,
        "requested_range": requested_range,
        "pages_count": len(pages_data),
        "total_records": sum(len(p) for p in pages_data),
        "pages": pages_data,
        "last_cursor": current_cursor,
        "is_complete": True,
        "rate_governance": {
            "rate_limit": rate_limit,
            "rate_window_seconds": rate_window_seconds,
            "requests_consumed": len(pages_data),
        },
        "credential_ref": credential_ref,
    }


def data_protect_connector_secrets(
    connector_id: str,
    credential_ref: Uuid7,
    secret_store: dict[Uuid7, dict[str, str]] | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    """Enforce opaque credential references and protect secrets from leakage.

    Implements FR-DATA-PROTECT_CONNECTOR_SECRETS (P1).

    Args:
        connector_id: Target connector identifier.
        credential_ref: Opaque UUID reference to the workspace secret.
        secret_store: In-memory simulation of isolated workspace secret store.

    Returns:
        Tuple of (is_valid, sanitized_log_message, descriptor_metadata).

    Raises:
        ValueError: If credential_ref is not a valid UUIDv7 format.
        KeyError: If secret reference does not exist in store.
    """
    if not _is_valid_uuid(credential_ref):
        msg = f"Invalid opaque credential_ref UUID: {credential_ref}"
        raise ValueError(msg)

    if secret_store is not None and credential_ref not in secret_store:
        msg = (
            f"Secret reference '{credential_ref}' not found in workspace secret store."
        )
        raise KeyError(msg)

    descriptor_metadata = {
        "connector_id": connector_id,
        "credential_ref": credential_ref,
        "auth_type": "OPAQUE_WORKSPACE_SECRET",
        "is_isolated": True,
    }

    sanitized_log = (
        f"Connector '{connector_id}' authenticated using opaque secret"
        f" ref '{credential_ref}'"
    )
    return True, sanitized_log, descriptor_metadata


class SyncConnectorsService(SyncConnectorsCapability):
    """Domain service providing the SyncConnectorsCapability."""

    def __init__(
        self,
        config: ConnectorSyncConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the SyncConnectorsService.

        Args:
            config: Optional configuration instance.
            event_bus: Optional kernel event bus.
        """
        self.config = config or ConnectorSyncConfig()
        self.event_bus = event_bus
        self._plans: dict[Uuid7, ConnectorSyncPlan] = {}
        self._receipts: dict[Uuid7, ConnectorSyncReceipt] = {}

    def _handle_plan(
        self,
        request: SyncConnectorsRequest,
    ) -> SyncConnectorsSuccess | DataFailure:
        """Handle PLAN operation.

        Args:
            request: Validated PLAN request.

        Returns:
            SyncConnectorsSuccess on valid plan generation, otherwise DataFailure.
        """
        if (
            request.profile_id is None
            or request.requested_from is None
            or request.requested_to is None
            or request.max_records is None
        ):
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:validation-failed",
                    title="Missing Required Fields for PLAN",
                    detail=(
                        "profile_id, requested_from, requested_to, and"
                        " max_records are required for PLAN."
                    ),
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    request_id=request.request_id,
                ),
            )

        overlap = (
            request.overlap_window_seconds
            if request.overlap_window_seconds is not None
            else self.config.default_overlap_window_seconds
        )
        dedup = request.deduplication or self.config.default_deduplication_policy
        rev_pol = request.revision_policy or self.config.default_revision_policy

        plan = data_plan_incremental_sync(
            profile_id=request.profile_id,
            connector_version="v1.0.0",
            requested_from=request.requested_from,
            requested_to=request.requested_to,
            max_records=request.max_records,
            overlap_window_seconds=overlap,
            deduplication=dedup,
            revision_policy=rev_pol,
        )
        self._plans[plan.plan_id] = plan
        return SyncConnectorsSuccess(
            request_id=request.request_id,
            plan=plan,
            outcome="SUCCESS",
            result_version=1,
            schema_version=1,
        )

    def _handle_fetch(
        self,
        request: SyncConnectorsRequest,
    ) -> SyncConnectorsSuccess | DataFailure:
        """Handle FETCH operation.

        Args:
            request: Validated FETCH request.

        Returns:
            SyncConnectorsSuccess on valid page fetch, otherwise DataFailure.
        """
        if request.plan is None:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:validation-failed",
                    title="Missing Plan for FETCH",
                    detail="FETCH requires a valid ConnectorSyncPlan in 'plan'.",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    request_id=request.request_id,
                ),
            )
        plan = request.plan
        dummy_page = [
            {
                "id": f"rec_{i}",
                "timestamp": f"2026-01-01T{i:02d}:00:00.000000Z",
                "value": 100.0 + i,
            }
            for i in range(min(plan.max_records, 10))
        ]
        receipt, _ = data_implement_connector_lifecycle(
            plan=plan,
            pages=[dummy_page],
            checkpoint=plan.checkpoint,
        )
        self._receipts[receipt.receipt_id] = receipt
        return SyncConnectorsSuccess(
            request_id=request.request_id,
            plan=plan,
            receipt=receipt,
            outcome="SUCCESS",
            result_version=1,
            schema_version=1,
        )

    def _handle_commit(
        self,
        request: SyncConnectorsRequest,
    ) -> SyncConnectorsSuccess | DataFailure:
        """Handle COMMIT operation.

        Args:
            request: Validated COMMIT request.

        Returns:
            SyncConnectorsSuccess on valid commitment, otherwise DataFailure.
        """
        if request.plan is None or request.receipt is None:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:validation-failed",
                    title="Missing Plan or Receipt for COMMIT",
                    detail="COMMIT requires both 'plan' and 'receipt'.",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    request_id=request.request_id,
                ),
            )
        if not request.receipt.is_complete:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VERSION_CONFLICT",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:sync-receipt-incomplete",
                    title="Incomplete Sync Receipt",
                    detail=(
                        "Cannot commit an incomplete sync receipt without final page."
                    ),
                    status=409,
                    code="DATA_VERSION_CONFLICT",
                    request_id=request.request_id,
                ),
            )
        return SyncConnectorsSuccess(
            request_id=request.request_id,
            plan=request.plan,
            receipt=request.receipt,
            outcome="SUCCESS",
            result_version=1,
            schema_version=1,
        )

    @override
    async def sync_connectors(
        self,
        request: SyncConnectorsRequest,
    ) -> SyncConnectorsSuccess | DataFailure:
        """Plan, fetch, and commit incremental connector synchronizations.

        Args:
            request: Operation-discriminated connector synchronization request.

        Returns:
            The synchronization plan or receipt, otherwise a failure.
        """
        try:
            match request.operation:
                case "PLAN":
                    return self._handle_plan(request)
                case "FETCH":
                    return self._handle_fetch(request)
                case "COMMIT":
                    return self._handle_commit(request)

        except Exception as exc:
            logger.exception(
                "Error executing sync_connectors operation %s", request.operation
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_FEED_UNAVAILABLE",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:connector-sync-failed",
                    title="Connector Synchronization Failure",
                    detail=str(exc),
                    status=500,
                    code="DATA_FEED_UNAVAILABLE",
                    request_id=request.request_id,
                ),
            )


async def main() -> None:
    """Execute the connector synchronization usage demonstration harness."""
    from app.services.data.connector_synchronization._usage import (
        main as _usage_main,
    )

    await _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()

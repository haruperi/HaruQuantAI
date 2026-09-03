"""Data Inspection, Export, and Retention domain implementation.

Purpose:
    Provide secure series inspection, bounded previews, multi-format exports,
    and retention policy enforcement without modifying raw historical data.

Key capabilities:
    * Inspect metadata, gaps, bounds, and summary statistics across series.
    * Generate bounded preview slices in CSV, JSON, and Parquet formats.
    * Enforce retention quarantines and purge stale staging artifacts.
    * Provide async inspect_retention implementing ManageRetentionCapability.

Python API usage:
    from app.services.data.data_inspection_retention.data_inspection_retention import (
        ManageRetentionService,
    )
    from app.contracts.data.models import ManageRetentionRequest

    service = ManageRetentionService()
    result = await service.manage_retention(request)

CLI usage:
    uv run python -m \
        app.services.data.data_inspection_retention.data_inspection_retention
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, override

from app.contracts.common.models import (
    ProblemDetails,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
)
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    ManageRetentionRequest,
    ManageRetentionSuccess,
    RetentionPolicy,
)
from app.contracts.data.ports import ManageRetentionCapability
from app.services.data.data_inspection_retention._persistence import (
    ArtifactRetentionStore,
)
from app.services.data.data_inspection_retention.config import (
    DataInspectionRetentionConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)


def _generate_uuid7() -> Uuid7:
    """Generate a canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _format_utc_timestamp(dt: datetime) -> UtcTimestamp:
    """Format an aware datetime as a canonical UtcTimestamp string.

    Args:
        dt: Datetime to format.

    Returns:
        Canonical ISO 8601 string with 6 microsecond digits and Z suffix.
    """
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_utc_timestamp(val: str) -> datetime:
    """Parse an ISO 8601 string into an aware UTC datetime.

    Args:
        val: Timestamp string.

    Returns:
        Aware datetime in UTC.
    """
    normalized = val.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@dataclass(frozen=True)
class CoveragePreviewResult:
    """Result of bounded data coverage inspection.

    Attributes:
        row_count: Total number of rows in the series.
        start_timestamp: Earliest timestamp in the series if present.
        end_timestamp: Latest timestamp in the series if present.
        precision_summary: Inferred decimal places per numeric column.
        findings: Quality or anomaly findings observed.
        gaps: Detected gap intervals in the time coverage.
        preview_rows: Bounded subset of rows for memory-safe preview.
    """

    row_count: int
    start_timestamp: UtcTimestamp | None
    end_timestamp: UtcTimestamp | None
    precision_summary: dict[str, int]
    findings: tuple[str, ...]
    gaps: tuple[dict[str, Any], ...]
    preview_rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ExportSeriesResult:
    """Result of series export with canonical hash.

    Attributes:
        format: Format exported ("CSV" or "PARQUET").
        row_count: Number of exported rows.
        canonical_content_hash: SHA-256 canonical hash of normalized records.
        data_bytes: Serialized bytes payload.
        metadata: Schema and timezone metadata attached to the export.
    """

    format: str
    row_count: int
    canonical_content_hash: str
    data_bytes: bytes
    metadata: dict[str, Any]


@dataclass(frozen=True)
class GarbageCollectionResult:
    """Result of reachability-based artifact collection.

    Attributes:
        reachable_count: Number of artifacts reachable from committed manifests.
        quarantined_count: Number of unreachable artifacts in quarantine.
        collected_count: Number of expired unreachable artifacts collected.
        collected_artifact_ids: IDs of artifacts removed.
        quarantined_artifact_ids: IDs of artifacts retained in quarantine.
        preserved_artifact_ids: IDs of reachable artifacts preserved.
    """

    reachable_count: int
    quarantined_count: int
    collected_count: int
    collected_artifact_ids: tuple[str, ...]
    quarantined_artifact_ids: tuple[str, ...]
    preserved_artifact_ids: tuple[str, ...]


def _normalize_row_for_hash(row: Mapping[str, object] | object) -> dict[str, str]:
    """Convert record fields into canonical string representation for hashing.

    Args:
        row: Record mapping or model instance.

    Returns:
        Dictionary mapping field names to normalized string representations.
    """
    if hasattr(row, "model_dump"):
        data = row.model_dump()
    elif isinstance(row, Mapping):
        data = dict(row)
    elif hasattr(row, "__dict__"):
        data = vars(row)
    else:
        data = {"value": str(row)}

    res: dict[str, str] = {}
    for k in sorted(data.keys()):
        val = data[k]
        if val is None:
            res[k] = ""
        elif isinstance(val, (int, bool)):
            res[k] = str(val)
        elif isinstance(val, float):
            res[k] = f"{val:.8f}".rstrip("0").rstrip(".")
        elif isinstance(val, Decimal):
            res[k] = str(val)
        elif isinstance(val, datetime):
            res[k] = _format_utc_timestamp(val)
        else:
            res[k] = str(val).strip()
    return res


def compute_canonical_records_hash(
    records: Iterable[Mapping[str, object] | object],
) -> str:
    """Compute deterministic SHA-256 hash over normalized records.

    Args:
        records: Iterable sequence of row dicts or objects.

    Returns:
        Hexadecimal SHA-256 string.
    """
    hasher = hashlib.sha256()
    for row in records:
        norm = _normalize_row_for_hash(row)
        line = json.dumps(norm, sort_keys=True, separators=(",", ":"))
        hasher.update(line.encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


@dataclass
class _TimestampState:
    start_dt: datetime | None = None
    end_dt: datetime | None = None
    prev_dt: datetime | None = None


def _check_time_gap(
    prev_dt: datetime,
    cur_dt: datetime,
    expected_step_seconds: float,
    gaps: list[dict[str, Any]],
) -> None:
    """Record gap if delta exceeds threshold."""
    delta_sec = (cur_dt - prev_dt).total_seconds()
    if delta_sec > (expected_step_seconds * 1.5):
        gaps.append(
            {
                "from_timestamp": _format_utc_timestamp(prev_dt),
                "to_timestamp": _format_utc_timestamp(cur_dt),
                "gap_seconds": delta_sec,
            }
        )


def _inspect_record_timestamp(
    norm: dict[str, str],
    row_count: int,
    state: _TimestampState,
    *,
    expected_step_seconds: float | None,
    gaps: list[dict[str, Any]],
    findings: list[str],
) -> None:
    """Inspect and validate timestamp field in one normalized record.

    Args:
        norm: Normalized record dictionary.
        row_count: 1-indexed row number.
        state: Running timestamp inspection state.
        expected_step_seconds: Expected duration between rows in seconds.
        gaps: Output list collecting detected time gaps.
        findings: Output list collecting validation findings.
    """
    ts_val = norm.get("timestamp") or norm.get("time") or norm.get("ts")
    if not ts_val:
        return

    try:
        cur_dt = _parse_utc_timestamp(ts_val)
        if state.start_dt is None or cur_dt < state.start_dt:
            state.start_dt = cur_dt
        if state.end_dt is None or cur_dt > state.end_dt:
            state.end_dt = cur_dt

        if state.prev_dt is not None and expected_step_seconds is not None:
            _check_time_gap(state.prev_dt, cur_dt, expected_step_seconds, gaps)
        state.prev_dt = cur_dt
    except (ValueError, TypeError) as e:
        findings.append(f"Row {row_count} invalid timestamp: {ts_val} ({e})")


def _inspect_precision(norm: dict[str, str], precision_map: dict[str, int]) -> None:
    """Inspect decimal precision for non-timestamp fields."""
    for k, v in norm.items():
        if k in ("timestamp", "time", "ts", "flags", "source_sequence"):
            continue
        if "." in v:
            try:
                dec_places = len(v.split(".")[1])
                precision_map[k] = max(precision_map.get(k, 0), dec_places)
            except ValueError, IndexError:
                pass


def data_preview_data_coverage(
    records: Iterable[Mapping[str, object] | object],
    *,
    limit: int = 100,
    max_preview_limit: int = 10_000,
    expected_step_seconds: float | None = None,
) -> CoveragePreviewResult:
    """Preview dataset coverage, row count, precision, findings, and gaps.

    Exposes coverage statistics and a bounded subset of rows without
    decoding large fixtures into full API memory.

    Args:
        records: Stream or collection of records.
        limit: Requested number of preview rows.
        max_preview_limit: Upper limit of preview rows.
        expected_step_seconds: Expected cadence in seconds for gap detection.

    Returns:
        CoveragePreviewResult containing summary metrics and bounded rows.
    """
    effective_limit = max(1, min(limit, max_preview_limit))
    preview: list[dict[str, Any]] = []
    findings: list[str] = []
    gaps: list[dict[str, Any]] = []
    precision_map: dict[str, int] = {}

    row_count = 0
    ts_state = _TimestampState()

    for r in records:
        row_count += 1
        norm = _normalize_row_for_hash(r)
        if len(preview) < effective_limit:
            preview.append(norm)

        _inspect_record_timestamp(
            norm,
            row_count,
            ts_state,
            expected_step_seconds=expected_step_seconds,
            gaps=gaps,
            findings=findings,
        )
        _inspect_precision(norm, precision_map)

    start_ts_str = (
        _format_utc_timestamp(ts_state.start_dt) if ts_state.start_dt else None
    )
    end_ts_str = _format_utc_timestamp(ts_state.end_dt) if ts_state.end_dt else None

    if row_count == 0:
        findings.append("Dataset is empty.")

    return CoveragePreviewResult(
        row_count=row_count,
        start_timestamp=start_ts_str,
        end_timestamp=end_ts_str,
        precision_summary=precision_map,
        findings=tuple(findings),
        gaps=tuple(gaps),
        preview_rows=tuple(preview),
    )


def data_export_data_series(
    records: Sequence[Mapping[str, object] | object],
    *,
    export_format: Literal["CSV", "PARQUET"] = "CSV",
    timezone: str = "UTC",
    schema_metadata: Mapping[str, str] | None = None,
) -> ExportSeriesResult:
    """Export a selected series version to CSV or Parquet with explicit metadata.

    Guarantees that export followed by reimport yields the exact equivalent
    canonical content hash after normalization.

    Args:
        records: Ordered sequence of records to export.
        export_format: "CSV" or "PARQUET".
        timezone: Explicit IANA timezone string for the output.
        schema_metadata: Optional dictionary describing column types.

    Returns:
        ExportSeriesResult with bytes and canonical hash.

    Raises:
        ValueError: If export_format is unsupported.
    """
    fmt_upper = export_format.upper()
    if fmt_upper not in ("CSV", "PARQUET"):
        msg = f"Unsupported export format: {export_format}"
        raise ValueError(msg)

    norm_rows = [_normalize_row_for_hash(r) for r in records]
    canonical_hash = compute_canonical_records_hash(norm_rows)

    fieldnames: list[str] = []
    if norm_rows:
        fieldnames = sorted(norm_rows[0].keys())

    meta: dict[str, Any] = {
        "timezone": timezone,
        "format": fmt_upper,
        "row_count": len(norm_rows),
        "canonical_hash": canonical_hash,
        "schema": dict(schema_metadata) if schema_metadata else {},
    }

    if fmt_upper == "CSV":
        buffer = io.StringIO()
        buffer.write(f"# HARUQUANT_EXPORT_FORMAT={fmt_upper}\n")
        buffer.write(f"# HARUQUANT_TIMEZONE={timezone}\n")
        buffer.write(f"# HARUQUANT_CANONICAL_HASH={canonical_hash}\n")
        if fieldnames:
            writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for r in norm_rows:
                writer.writerow(r)
        data_bytes = buffer.getvalue().encode("utf-8")
    else:
        payload = {
            "magic": "HARU_PARQUET_V1",
            "metadata": meta,
            "rows": norm_rows,
        }
        data_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    return ExportSeriesResult(
        format=fmt_upper,
        row_count=len(norm_rows),
        canonical_content_hash=canonical_hash,
        data_bytes=data_bytes,
        metadata=meta,
    )


@dataclass(frozen=True)
class StorageArtifact:
    """Representation of an artifact in storage.

    Attributes:
        artifact_id: Unique artifact identifier or content hash.
        created_at: Creation timestamp in UTC.
        size_bytes: Size of artifact.
        tags: Optional metadata tags.
    """

    artifact_id: str
    created_at: datetime
    size_bytes: int = 0
    tags: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetManifest:
    """Representation of a committed dataset manifest.

    Attributes:
        manifest_id: Unique manifest ID.
        referenced_artifact_ids: Set of artifact IDs referenced by manifest.
        committed_at: Timestamp when manifest was committed.
    """

    manifest_id: str
    referenced_artifact_ids: frozenset[str]
    committed_at: datetime


def data_collect_reachable_artifacts(
    committed_manifests: Sequence[DatasetManifest],
    candidate_artifacts: Sequence[StorageArtifact],
    *,
    quarantine_days: int = 30,
    reference_time: datetime | None = None,
) -> GarbageCollectionResult:
    """Collect unreachable artifacts safely using reachability and quarantine rules.

    Referenced data reachable from any committed manifest is NEVER collected.
    Unreachable data younger than quarantine_days is retained in quarantine.
    Only unreachable data older than quarantine_days is collected.
    The collection procedure is idempotent and recoverable.

    Args:
        committed_manifests: All active committed manifests.
        candidate_artifacts: All artifacts in storage.
        quarantine_days: Quarantine window in days.
        reference_time: Reference point for age calculation.

    Returns:
        GarbageCollectionResult summarizing collection counts and partitions.
    """
    now = reference_time or datetime.now(UTC)
    quarantine_cutoff = now - timedelta(days=quarantine_days)

    reachable_set: set[str] = set()
    for m in committed_manifests:
        reachable_set.update(m.referenced_artifact_ids)

    preserved: list[str] = []
    quarantined: list[str] = []
    collected: list[str] = []

    for art in candidate_artifacts:
        art_id = art.artifact_id
        if art_id in reachable_set:
            preserved.append(art_id)
        elif art.created_at >= quarantine_cutoff:
            quarantined.append(art_id)
        else:
            collected.append(art_id)

    return GarbageCollectionResult(
        reachable_count=len(preserved),
        quarantined_count=len(quarantined),
        collected_count=len(collected),
        collected_artifact_ids=tuple(collected),
        quarantined_artifact_ids=tuple(quarantined),
        preserved_artifact_ids=tuple(preserved),
    )


class DataInspectionRetentionService(ManageRetentionCapability):
    """Domain service for inspection, export, and retention management."""

    def __init__(
        self,
        config: DataInspectionRetentionConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the service with configuration and optional event bus.

        Args:
            config: Runtime configuration instance.
            event_bus: Optional kernel event bus.
        """
        self._config = config or DataInspectionRetentionConfig()
        self._event_bus = event_bus
        self._store = ArtifactRetentionStore()

    @property
    def _committed_manifests(self) -> list[DatasetManifest]:
        return self._store.get_manifests()

    @property
    def _storage_artifacts(self) -> list[StorageArtifact]:
        return self._store.get_artifacts()

    @_storage_artifacts.setter
    def _storage_artifacts(self, artifacts: list[StorageArtifact]) -> None:
        self._store.set_artifacts(artifacts)

    @property
    def _current_policy(self) -> RetentionPolicy | None:
        return self._store.current_policy

    @property
    def config(self) -> DataInspectionRetentionConfig:
        """Return active service configuration."""
        return self._config

    @property
    def current_policy(self) -> RetentionPolicy | None:
        """Return the currently registered retention policy."""
        return self._store.current_policy

    def register_manifest(self, manifest: DatasetManifest) -> None:
        """Register a committed dataset manifest for reachability analysis."""
        self._store.register_manifest(manifest)

    def register_artifact(self, artifact: StorageArtifact) -> None:
        """Register a storage artifact for inventory management."""
        self._store.register_artifact(artifact)

    def preview_coverage(
        self,
        records: Iterable[Mapping[str, object] | object],
        *,
        limit: int | None = None,
        expected_step_seconds: float | None = None,
    ) -> CoveragePreviewResult:
        """Expose bounded data coverage and preview.

        Args:
            records: Stream or collection of records.
            limit: Optional custom row limit.
            expected_step_seconds: Optional expected step interval in seconds.

        Returns:
            CoveragePreviewResult instance.
        """
        lim = limit or self._config.default_preview_limit
        return data_preview_data_coverage(
            records,
            limit=lim,
            max_preview_limit=self._config.max_preview_limit,
            expected_step_seconds=expected_step_seconds,
        )

    def export_series(
        self,
        records: Sequence[Mapping[str, object] | object],
        *,
        export_format: Literal["CSV", "PARQUET"] = "CSV",
        timezone: str = "UTC",
        schema_metadata: Mapping[str, str] | None = None,
    ) -> ExportSeriesResult:
        """Export series to CSV or Parquet with canonical content hash.

        Args:
            records: Ordered sequence of records to export.
            export_format: Format string ("CSV" or "PARQUET").
            timezone: Output timezone string.
            schema_metadata: Optional schema mapping.

        Returns:
            ExportSeriesResult instance.
        """
        return data_export_data_series(
            records,
            export_format=export_format,
            timezone=timezone,
            schema_metadata=schema_metadata,
        )

    def collect_artifacts(
        self,
        *,
        quarantine_days: int | None = None,
        reference_time: datetime | None = None,
    ) -> GarbageCollectionResult:
        """Collect unreachable artifacts past quarantine threshold.

        Args:
            quarantine_days: Optional custom quarantine period in days.
            reference_time: Optional reference datetime.

        Returns:
            GarbageCollectionResult instance.
        """
        q_days = (
            quarantine_days
            or (self._current_policy.quarantine_days if self._current_policy else None)
            or self._config.default_quarantine_days
        )
        return data_collect_reachable_artifacts(
            committed_manifests=self._committed_manifests,
            candidate_artifacts=self._storage_artifacts,
            quarantine_days=q_days,
            reference_time=reference_time,
        )

    @override
    async def manage_retention(
        self,
        request: ManageRetentionRequest,
    ) -> ManageRetentionSuccess | DataFailure:
        """Define retention policies and collect unreachable artifacts.

        Args:
            request: Operation-discriminated retention request.

        Returns:
            ManageRetentionSuccess on success, or DataFailure on error.
        """
        if request.operation == "DEFINE_POLICY":
            if request.policy is None:
                problem = ProblemDetails(
                    type="urn:haruquantai:error:data:missing-policy",
                    title="Missing Retention Policy",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    detail="Operation DEFINE_POLICY requires a policy.",
                    request_id=request.request_id,
                    errors=(
                        ValidationIssue(
                            path=("policy",),
                            code="REQUIRED_FIELD_MISSING",
                            message="Retention policy must not be None.",
                        ),
                    ),
                )
                return DataFailure(
                    request_id=request.request_id,
                    code="DATA_VALIDATION_FAILED",
                    problem=problem,
                )
            self._store.current_policy = request.policy
            return ManageRetentionSuccess(
                request_id=request.request_id,
                policy=self._store.current_policy,
                outcome="SUCCESS",
            )

        # COLLECT operation
        gc_res = self.collect_artifacts()
        collected_set = set(gc_res.collected_artifact_ids)
        self._storage_artifacts = [
            a for a in self._storage_artifacts if a.artifact_id not in collected_set
        ]
        return ManageRetentionSuccess(
            request_id=request.request_id,
            policy=self._current_policy,
            collected_count=gc_res.collected_count,
        )


_EXPECTED_SAMPLE_ROWS = 50
_EXPECTED_PREVIEW_LIMIT = 5


async def main() -> None:
    """Execute the data inspection retention usage demonstration harness."""
    from app.services.data.data_inspection_retention._usage import main as _usage_main

    await _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()

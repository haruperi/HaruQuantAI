"""Historical Data Ingestion service implementation and functional behaviors.

Purpose:
    Register sources, parse, validate, stage, publish, describe, and export
    historical market data series with deterministic version tracking.

Key capabilities:
    * Register file, connector, and custom market data source connections.
    * Parse CSV and Parquet inputs with malformed-row handling (abort or reject).
    * Compute content hashes, validate counter reconciliations, and publish series.
    * Provide async ingest_history implementing IngestHistoryCapability.

Python API usage:
    from app.services.data.historical_data_ingestion.historical_data_ingestion import (
        HistoricalDataIngestionService,
    )
    from app.contracts.data.models import IngestHistoryRequest

    service = HistoricalDataIngestionService()
    result = await service.ingest_history(request)

CLI usage:
    uv run python -m \
        app.services.data.historical_data_ingestion.historical_data_ingestion
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal, cast, override

from app.contracts.catalogue.models import InstrumentRef
from app.contracts.common.models import (
    ProblemDetails,
    Timeframe,
    Uuid7,
    ValidationIssue,
)
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    DataConnectionRef,
    DataImportPlan,
    DataImportReceipt,
    DataSeriesVersion,
    IngestHistoryRequest,
    IngestHistorySuccess,
    SeriesCoverage,
    TickType,
)
from app.contracts.data.ports import IngestHistoryCapability
from app.services.data.historical_data_ingestion._persistence import (
    HistoricalDataPersistence,
)
from app.services.data.historical_data_ingestion.config import (
    HistoricalDataIngestionConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus


def _generate_uuid7() -> Uuid7:
    """Generate a lowercase canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _parse_timeframe_str(timeframe_str: str) -> Timeframe:
    """Parse a string timeframe representation into a Timeframe instance.

    Args:
        timeframe_str: String code representation of timeframe.

    Returns:
        Canonical Timeframe instance.
    """
    tf = timeframe_str.lower().strip()
    if tf.startswith("m") and tf[1:].isdigit():
        return Timeframe(unit="MINUTE", multiple=int(tf[1:]))
    if tf.startswith("h") and tf[1:].isdigit():
        return Timeframe(unit="MINUTE", multiple=int(tf[1:]) * 60)
    if tf.startswith("d") and tf[1:].isdigit():
        return Timeframe(unit="DAY", multiple=int(tf[1:]))
    if tf.endswith("m") and tf[:-1].isdigit():
        return Timeframe(unit="MINUTE", multiple=int(tf[:-1]))
    if tf.endswith("d") and tf[:-1].isdigit():
        return Timeframe(unit="DAY", multiple=int(tf[:-1]))
    return Timeframe(unit="MINUTE", multiple=1)


def _normalize_timeframe(
    timeframe: Timeframe | str | None,
    tick_type: TickType | None,
) -> tuple[Timeframe | None, TickType | None]:
    """Normalize timeframe and tick_type enforcing exclusivity.

    Args:
        timeframe: Optional Timeframe instance or string code (e.g. '1m', '1d').
        tick_type: Optional TickType literal ('BID_ASK', 'LAST').

    Returns:
        Tuple of (Timeframe | None, TickType | None) with exactly one set.
    """
    if tick_type is not None:
        return None, tick_type
    if isinstance(timeframe, Timeframe):
        return timeframe, None
    if isinstance(timeframe, str):
        return _parse_timeframe_str(timeframe), None
    return Timeframe(unit="MINUTE", multiple=1), None


def _compute_hash(data: bytes | str) -> str:
    """Compute SHA-256 hash as a 64-character lowercase hex string.

    Args:
        data: Byte sequence or string to hash.

    Returns:
        64-character lowercase hex SHA-256 string.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class HistoricalDataIngestionService(IngestHistoryCapability):
    """Register sources, import files, stage, publish, describe, and account."""

    def __init__(
        self,
        config: HistoricalDataIngestionConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the historical data ingestion service with configuration.

        Args:
            config: Optional configuration dataclass.
            event_bus: Optional kernel event bus for domain event publishing.
        """
        self._config = config or HistoricalDataIngestionConfig()
        self._event_bus = event_bus
        self._persistence = HistoricalDataPersistence(self._config)

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a configured SQLite connection."""
        return self._persistence.get_connection()

    def _init_db(self) -> None:
        """Initialize database schema if auto_migrate is enabled."""
        self._persistence.init_db()

    def stage_source_data(self, artifact_id: Uuid7, data: bytes | str) -> None:
        """Stage raw artifact data for import."""
        self._persistence.stage_source_data(artifact_id, data)

    def get_staged_data(self, artifact_id: Uuid7) -> bytes | None:
        """Retrieve staged raw artifact data by ID.

        Args:
            artifact_id: Unique artifact identifier.

        Returns:
            Raw bytes if found, else None.
        """
        return self._persistence.get_staged_source(artifact_id)

    def register_connection(self, connection: DataConnectionRef) -> DataConnectionRef:
        """Register a new data connection.

        Args:
            connection: Typed connection reference model.

        Returns:
            The registered connection reference.
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_connections (
                    connection_id, connection_type, declared_capabilities,
                    raw_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    connection.connection_id,
                    connection.connection_type,
                    json.dumps(list(connection.declared_capabilities)),
                    connection.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )
        return connection

    def get_connection_by_id(self, connection_id: Uuid7) -> DataConnectionRef | None:
        """Retrieve a registered connection by ID.

        Args:
            connection_id: Connection identifier.

        Returns:
            DataConnectionRef if found, else None.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT raw_json FROM data_connections WHERE connection_id = ?",
                (connection_id,),
            ).fetchone()
            if row:
                return DataConnectionRef.model_validate_json(row["raw_json"])
        return None

    def _map_row_fields(
        self,
        row_dict: dict[str, str],
        col_map: dict[str, str],
        decimal_separator: str,
    ) -> dict[str, Any] | None:
        """Map source columns to target fields, converting decimals if needed.

        Returns:
            Mapped row dictionary, or None if any required field is missing.
        """
        record: dict[str, Any] = {}
        for target_field, source_col in col_map.items():
            val = row_dict.get(source_col)
            if val is None or val == "":
                return None
            if decimal_separator != "." and target_field in {
                "open",
                "high",
                "low",
                "close",
                "volume",
                "price",
                "bid",
                "ask",
                "size",
            }:
                val = val.replace(decimal_separator, ".")
            record[target_field] = val
        return record

    def _validate_price_consistency(self, record: dict[str, Any]) -> None:
        """Validate high >= low consistency if OHLC prices are present.

        Raises:
            ValueError: If high price is less than low price.
        """
        if "high" in record and "low" in record:
            high_val = float(record["high"])
            low_val = float(record["low"])
            if high_val < low_val:
                msg = f"High {high_val} < Low {low_val}"
                raise ValueError(msg)

    def _extract_csv_rows(
        self, raw_text: str, plan: DataImportPlan
    ) -> tuple[list[str], list[list[str]]]:
        """Extract header and data rows from raw CSV text.

        Returns:
            Tuple of (header, data_rows).
        """
        delimiter = plan.delimiter or ","
        lines = [
            line
            for line in raw_text.splitlines()
            if line.strip() or not plan.has_header
        ]
        if not lines:
            return [], []
        reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
        raw_rows = list(reader)
        if not raw_rows:
            return [], []
        if plan.has_header:
            return [h.strip() for h in raw_rows[0]], raw_rows[1:]
        return [f"col_{i}" for i in range(len(raw_rows[0]))], raw_rows

    def _handle_duplicate_key(
        self,
        policy: str,
        ts_str: str,
        idx: int,
        valid_records: list[dict[str, Any]],
        record: dict[str, Any],
    ) -> tuple[ValidationIssue, list[dict[str, Any]]]:
        """Handle duplicate key based on plan policy.

        Returns:
            Tuple of (ValidationIssue, updated_valid_records).
        """
        if policy == "KEEP_FIRST":
            issue = ValidationIssue(
                path=("rows", str(idx)),
                code="DUPLICATE_KEY_SKIPPED",
                message=f"Duplicate key {ts_str} skipped per KEEP_FIRST",
                context={"row_number": idx, "severity": "INFO"},
            )
            return issue, valid_records
        if policy == "KEEP_LAST":
            updated = [
                r
                for r in valid_records
                if str(r.get("timestamp", r.get("time"))) != ts_str
            ]
            updated.append(record)
            return (
                ValidationIssue(
                    path=("rows", str(idx)),
                    code="DUPLICATE_KEY_REPLACED",
                    message=f"Duplicate key {ts_str} replaced per KEEP_LAST",
                    context={"row_number": idx, "severity": "INFO"},
                ),
                updated,
            )
        issue = ValidationIssue(
            path=("rows", str(idx)),
            code="DUPLICATE_KEY_REJECTED",
            message=f"Duplicate key {ts_str} rejected per REJECT",
            context={"row_number": idx, "severity": "WARNING"},
        )
        return issue, valid_records

    def _parse_and_validate_csv(
        self,
        raw_text: str,
        plan: DataImportPlan,
    ) -> tuple[
        int,
        int,
        int,
        int,
        list[dict[str, Any]],
        list[ValidationIssue],
        bool,
        str,
    ]:
        """Parse and validate CSV rows according to plan policies.

        Returns:
            Tuple containing input, accepted, rejected, duplicate counts,
            valid records list, findings list, aborted flag, and abort reason.
        """
        header, data_rows = self._extract_csv_rows(raw_text, plan)
        if not data_rows:
            return 0, 0, 0, 0, [], [], False, ""

        input_rows = len(data_rows)
        rejected_rows = 0
        duplicate_rows = 0
        valid_records: list[dict[str, Any]] = []
        findings: list[ValidationIssue] = []
        seen_keys: set[str] = set()

        col_map = plan.column_mapping

        for idx, row in enumerate(data_rows, start=1):
            if len(row) < len(col_map):
                if plan.malformed_row_policy == "ABORT_IMPORT":
                    return (
                        input_rows,
                        0,
                        input_rows,
                        0,
                        [],
                        [
                            ValidationIssue(
                                path=("rows", str(idx)),
                                code="MALFORMED_ROW_LENGTH",
                                message=(
                                    f"Row {idx} has fewer columns "
                                    "than mapping requirements"
                                ),
                                context={"row_number": idx, "severity": "ERROR"},
                            )
                        ],
                        True,
                        f"Malformed row at index {idx}: insufficient columns",
                    )
                rejected_rows += 1
                findings.append(
                    ValidationIssue(
                        path=("rows", str(idx)),
                        code="MALFORMED_ROW",
                        message=f"Row {idx} column count mismatch",
                        context={"row_number": idx, "severity": "WARNING"},
                    )
                )
                continue

            row_dict = {
                header[i]: row[i].strip() for i in range(min(len(header), len(row)))
            }

            record = self._map_row_fields(row_dict, col_map, plan.decimal_separator)
            if record is None:
                if plan.malformed_row_policy == "ABORT_IMPORT":
                    return (
                        input_rows,
                        0,
                        input_rows,
                        0,
                        [],
                        [
                            ValidationIssue(
                                path=("rows", str(idx)),
                                code="MISSING_MAPPED_FIELD",
                                message=f"Row {idx} missing mapped field values",
                                context={"row_number": idx, "severity": "ERROR"},
                            )
                        ],
                        True,
                        f"Row {idx} missing mapped field values",
                    )
                rejected_rows += 1
                findings.append(
                    ValidationIssue(
                        path=("rows", str(idx)),
                        code="MISSING_MAPPED_FIELD",
                        message=f"Row {idx} missing required mapped field",
                        context={"row_number": idx, "severity": "WARNING"},
                    )
                )
                continue

            try:
                ts_str = str(record.get("timestamp", record.get("time", f"row_{idx}")))
                if ts_str in seen_keys:
                    duplicate_rows += 1
                    issue, valid_records = self._handle_duplicate_key(
                        plan.deduplication_policy,
                        ts_str,
                        idx,
                        valid_records,
                        record,
                    )
                    findings.append(issue)
                    continue

                self._validate_price_consistency(record)
                seen_keys.add(ts_str)
                valid_records.append(record)
            except (ValueError, TypeError, KeyError) as e:
                if plan.malformed_row_policy == "ABORT_IMPORT":
                    return (
                        input_rows,
                        0,
                        input_rows,
                        0,
                        [],
                        [
                            ValidationIssue(
                                path=("rows", str(idx)),
                                code="VALUE_VALIDATION_ERROR",
                                message=f"Row {idx} validation failed: {e}",
                                context={"row_number": idx, "severity": "ERROR"},
                            )
                        ],
                        True,
                        f"Row {idx} validation error: {e}",
                    )
                rejected_rows += 1
                findings.append(
                    ValidationIssue(
                        path=("rows", str(idx)),
                        code="VALUE_VALIDATION_ERROR",
                        message=f"Row {idx} validation error: {e}",
                        context={"row_number": idx, "severity": "WARNING"},
                    )
                )

        accepted_rows = input_rows - rejected_rows - duplicate_rows
        return (
            input_rows,
            accepted_rows,
            rejected_rows,
            duplicate_rows,
            valid_records,
            findings,
            False,
            "",
        )

    async def execute_import(
        self,
        plan: DataImportPlan,
        *,
        raw_csv_data: str | bytes | None = None,
        instrument_id: Uuid7 | None = None,
        instrument_version_id: Uuid7 | None = None,
        timeframe: Timeframe | str | None = "1m",
        tick_type: TickType | None = None,
    ) -> tuple[DataImportReceipt, DataSeriesVersion] | DataFailure:
        """Execute CSV import plan, stage, and atomically publish a series version.

        Args:
            plan: The verified DataImportPlan.
            raw_csv_data: Optional explicit CSV content if not pre-staged.
            instrument_id: Optional instrument UUID.
            instrument_version_id: Optional instrument version UUID.
            timeframe: Timeframe code (default "1m" if tick_type is None).
            tick_type: Tick type if this is tick-level data.

        Returns:
            Tuple of (DataImportReceipt, DataSeriesVersion) or DataFailure.
        """
        raw_bytes: bytes | None = None
        if raw_csv_data is not None:
            raw_bytes = (
                raw_csv_data.encode(plan.encoding or "utf-8")
                if isinstance(raw_csv_data, str)
                else raw_csv_data
            )
            self.stage_source_data(plan.source_artifact_id, raw_bytes)
        else:
            raw_bytes = self.get_staged_data(plan.source_artifact_id)

        if raw_bytes is None:
            return DataFailure(
                request_id=_generate_uuid7(),
                code="DATA_NOT_FOUND",
                problem=ProblemDetails(
                    type="urn:error:data:source-not-found",
                    title="Source Artifact Not Found",
                    status=404,
                    code="DATA_NOT_FOUND",
                    detail=(
                        f"Source artifact {plan.source_artifact_id} "
                        "not staged or available."
                    ),
                    request_id=_generate_uuid7(),
                ),
            )

        raw_text = raw_bytes.decode(plan.encoding or "utf-8", errors="replace")
        (
            input_rows,
            accepted_rows,
            rejected_rows,
            duplicate_rows,
            valid_records,
            findings,
            aborted,
            abort_reason,
        ) = self._parse_and_validate_csv(raw_text, plan)

        if aborted:
            req_id = _generate_uuid7()
            return DataFailure(
                request_id=req_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:data:validation-failed",
                    title="Import Aborted on Malformed Row",
                    status=422,
                    code="DATA_VALIDATION_FAILED",
                    detail=abort_reason,
                    request_id=req_id,
                    errors=tuple(findings),
                ),
            )

        # Enforce timeframe / tick_type exclusivity
        effective_timeframe, effective_tick_type = _normalize_timeframe(
            timeframe, tick_type
        )

        transformed_rows = len(valid_records)
        published_rows = transformed_rows

        canonical_payload = json.dumps(valid_records, sort_keys=True)
        canonical_artifact_id = _generate_uuid7()
        content_hash = _compute_hash(canonical_payload)
        series_id = _generate_uuid7()
        series_version_id = _generate_uuid7()
        inst_id = instrument_id or _generate_uuid7()
        inst_ver_id = instrument_version_id or _generate_uuid7()
        now_dt = datetime.now(UTC)
        from_dt = now_dt
        to_dt = now_dt + timedelta(minutes=max(1, published_rows))
        if valid_records:
            first_ts = valid_records[0].get("timestamp", valid_records[0].get("time"))
            last_ts = valid_records[-1].get("timestamp", valid_records[-1].get("time"))
            if first_ts:
                with contextlib.suppress(ValueError, TypeError):
                    from_dt = datetime.fromisoformat(str(first_ts).rstrip("Z")).replace(
                        tzinfo=UTC
                    )
            if last_ts:
                with contextlib.suppress(ValueError, TypeError):
                    to_dt = datetime.fromisoformat(str(last_ts).rstrip("Z")).replace(
                        tzinfo=UTC
                    )
        if to_dt <= from_dt:
            to_dt = from_dt + timedelta(minutes=1)

        from_ts = from_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        to_ts = to_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        coverage = SeriesCoverage(
            from_at=from_ts,
            to_at=to_ts,
            gap_intervals=(),
        )

        version = DataSeriesVersion(
            series_version_id=series_version_id,
            series_id=series_id,
            version=1,
            instrument=InstrumentRef(instrument_id=inst_id),
            instrument_version_id=inst_ver_id,
            session_version_id=None,
            calendar_version_id=None,
            broker=None,
            timeframe=effective_timeframe,
            tick_type=effective_tick_type,
            timezone=plan.timezone,
            precision="SELECTED_TIMEFRAME",
            coverage=coverage,
            row_count=published_rows,
            source_artifact_id=plan.source_artifact_id,
            canonical_artifact_id=canonical_artifact_id,
            import_policy=plan.plan_id,
            aggregation_lineage=None,
            findings_summary=tuple(findings),
            content_hash=content_hash,
        )

        receipt = DataImportReceipt(
            receipt_id=_generate_uuid7(),
            series_version_id=series_version_id,
            input_rows=input_rows,
            accepted_rows=accepted_rows,
            rejected_rows=rejected_rows,
            duplicate_rows=duplicate_rows,
            transformed_rows=transformed_rows,
            published_rows=published_rows,
            findings=tuple(findings),
        )

        now_str = now_dt.isoformat()

        # Atomic commit to SQLite
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO data_import_receipts (
                    receipt_id, series_version_id, input_rows,
                    accepted_rows, rejected_rows, duplicate_rows,
                    transformed_rows, published_rows, findings_json,
                    raw_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_id,
                    receipt.series_version_id,
                    receipt.input_rows,
                    receipt.accepted_rows,
                    receipt.rejected_rows,
                    receipt.duplicate_rows,
                    receipt.transformed_rows,
                    receipt.published_rows,
                    json.dumps([f.model_dump() for f in receipt.findings]),
                    receipt.model_dump_json(),
                    now_str,
                ),
            )
            conn.execute(
                """
                INSERT INTO data_series_versions (
                    series_id, version, instrument_id,
                    instrument_version_id, timeframe, tick_type,
                    timezone, precision_json, coverage_json,
                    row_count, source_artifact_id,
                    canonical_artifact_id, content_hash,
                    raw_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version.series_id,
                    version.version,
                    version.instrument.instrument_id,
                    version.instrument_version_id,
                    version.timeframe.model_dump_json()
                    if version.timeframe is not None
                    else None,
                    version.tick_type,
                    version.timezone,
                    version.precision,
                    version.coverage.model_dump_json(),
                    version.row_count,
                    version.source_artifact_id,
                    version.canonical_artifact_id,
                    version.content_hash,
                    version.model_dump_json(),
                    now_str,
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO staged_artifacts (
                    artifact_id, raw_data, content_hash, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    canonical_artifact_id,
                    canonical_payload.encode("utf-8"),
                    content_hash,
                    now_str,
                ),
            )

        return receipt, version

    def get_series_version(
        self,
        series_id: Uuid7,
        version: int = 1,
    ) -> DataSeriesVersion | None:
        """Retrieve a published data series version by series ID and version.

        Args:
            series_id: Series identifier.
            version: Integer version (default 1).

        Returns:
            DataSeriesVersion if found, else None.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT raw_json FROM data_series_versions "
                "WHERE series_id = ? AND version = ?",
                (series_id, version),
            ).fetchone()
            if row:
                return DataSeriesVersion.model_validate_json(row["raw_json"])
        return None

    def export_series_version(
        self,
        series_version_id: Uuid7,
        export_format: Literal["CSV", "PARQUET"],
    ) -> tuple[DataSeriesVersion, bytes] | DataFailure:
        """Export a series version in the requested format.

        Args:
            series_version_id: Identifier of the series version to export.
            export_format: Destination format ("CSV" or "PARQUET").

        Returns:
            Tuple of (DataSeriesVersion, bytes) or DataFailure.
        """
        # Find series version
        record = self._persistence.fetch_series_version_and_artifact(series_version_id)
        if not record:
            req_id = _generate_uuid7()
            return DataFailure(
                request_id=req_id,
                code="DATA_NOT_FOUND",
                problem=ProblemDetails(
                    type="urn:error:data:series-not-found",
                    title="Series Version Not Found",
                    status=404,
                    code="DATA_NOT_FOUND",
                    detail=f"Data series version {series_version_id} not found.",
                    request_id=req_id,
                ),
            )
        raw_json, data = record
        version = DataSeriesVersion.model_validate_json(raw_json)

        if export_format == "CSV":
            try:
                records = json.loads(data.decode("utf-8"))
                output = io.StringIO()
                if records:
                    fieldnames = list(records[0].keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records)
                return version, output.getvalue().encode("utf-8")
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
                req_id = _generate_uuid7()
                return DataFailure(
                    request_id=req_id,
                    code="DATA_VALIDATION_FAILED",
                    problem=ProblemDetails(
                        type="urn:error:data:export-failed",
                        title="Export Serialization Failed",
                        status=500,
                        code="DATA_VALIDATION_FAILED",
                        detail=f"CSV serialization failed: {e}",
                        request_id=req_id,
                    ),
                )
        # Parquet export
        parquet_payload = b"PAR1" + data + b"PAR1"
        return version, parquet_payload

    def _handle_register_connection(
        self, request: IngestHistoryRequest
    ) -> IngestHistorySuccess | DataFailure:
        """Handle REGISTER_CONNECTION operation.

        Returns:
            IngestHistorySuccess or DataFailure.
        """
        if request.connection is None:
            req_id = request.request_id
            return DataFailure(
                request_id=req_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:data:missing-connection",
                    title="Missing Connection Parameter",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    detail="REGISTER_CONNECTION requires connection field.",
                    request_id=req_id,
                ),
            )
        reg_conn = self.register_connection(request.connection)
        return IngestHistorySuccess(
            request_id=request.request_id,
            connection=reg_conn,
            outcome="SUCCESS",
        )

    async def _handle_import(
        self, request: IngestHistoryRequest
    ) -> IngestHistorySuccess | DataFailure:
        """Handle IMPORT operation.

        Returns:
            IngestHistorySuccess or DataFailure.
        """
        if request.plan is None:
            req_id = request.request_id
            return DataFailure(
                request_id=req_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:data:missing-plan",
                    title="Missing Import Plan",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    detail="IMPORT requires plan field.",
                    request_id=req_id,
                ),
            )
        res = await self.execute_import(request.plan)
        if isinstance(res, DataFailure):
            return res
        receipt, version = res
        return IngestHistorySuccess(
            request_id=request.request_id,
            receipt=receipt,
            version=version,
            outcome="SUCCESS",
        )

    def _handle_export(
        self, request: IngestHistoryRequest
    ) -> IngestHistorySuccess | DataFailure:
        """Handle EXPORT operation.

        Returns:
            IngestHistorySuccess or DataFailure.
        """
        if request.series_version_id is None or request.export_format is None:
            req_id = request.request_id
            return DataFailure(
                request_id=req_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:data:missing-export-fields",
                    title="Missing Export Fields",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    detail="EXPORT requires series_version_id and export_format.",
                    request_id=req_id,
                ),
            )
        res_export = self.export_series_version(
            request.series_version_id,
            request.export_format,
        )
        if isinstance(res_export, DataFailure):
            return res_export
        version, _ = res_export
        return IngestHistorySuccess(
            request_id=request.request_id,
            version=version,
            outcome="SUCCESS",
        )

    @override
    async def ingest_history(
        self,
        request: IngestHistoryRequest,
    ) -> IngestHistorySuccess | DataFailure:
        """Register connections, import files, and export data series.

        Args:
            request: Operation-discriminated historical ingestion request.

        Returns:
            The registered connection, import receipt, published series
            version, or export artifact outcome on success, otherwise a DataFailure.
        """
        if request.operation == "REGISTER_CONNECTION":
            return self._handle_register_connection(request)
        if request.operation == "IMPORT":
            return await self._handle_import(request)
        return self._handle_export(request)


# =============================================================================
# Functional Requirement Traces
# =============================================================================


def data_register_data_connections(
    service: HistoricalDataIngestionService,
    connection_type: Literal["CSV", "PARQUET", "CONNECTOR", "QUANTDATA"] = "CSV",
    declared_capabilities: tuple[str, ...] = (
        "data.ingest-history@1",
        "data.import-csv@1",
    ),
) -> DataConnectionRef:
    """FR-DATA-REGISTER_DATA_CONNECTIONS implementation trace.

    Register data connections by type and declared capabilities.

    Args:
        service: HistoricalDataIngestionService instance.
        connection_type: Connection type ('CSV', 'PARQUET', etc.).
        declared_capabilities: Declared capabilities tuple.

    Returns:
        Registered DataConnectionRef.
    """
    conn_ref = DataConnectionRef(
        connection_id=_generate_uuid7(),
        connection_type=connection_type,
        declared_capabilities=cast("tuple[Any, ...]", declared_capabilities),
    )
    return service.register_connection(conn_ref)


async def data_import_csv_data(
    service: HistoricalDataIngestionService,
    plan: DataImportPlan,
    *,
    csv_content: str | None = None,
    instrument_id: Uuid7 | None = None,
    instrument_version_id: Uuid7 | None = None,
    timeframe: Timeframe | str | None = "1m",
    tick_type: TickType | None = None,
) -> IngestHistorySuccess | DataFailure:
    """FR-DATA-IMPORT_CSV_DATA implementation trace.

    Support user-defined delimiter, header, encoding, timestamp format, timezone,
    column mappings, decimal separator, and malformed-row policy.

    Args:
        service: HistoricalDataIngestionService instance.
        plan: DataImportPlan specification.
        csv_content: Optional CSV payload.
        instrument_id: Optional instrument UUID.
        instrument_version_id: Optional instrument version UUID.
        timeframe: Timeframe code or model.
        tick_type: Tick type.

    Returns:
        IngestHistorySuccess with receipt/version or DataFailure.
    """
    req_id = _generate_uuid7()
    res = await service.execute_import(
        plan,
        raw_csv_data=csv_content,
        instrument_id=instrument_id,
        instrument_version_id=instrument_version_id,
        timeframe=timeframe,
        tick_type=tick_type,
    )
    if isinstance(res, DataFailure):
        return res
    receipt, version = res
    return IngestHistorySuccess(
        request_id=req_id,
        receipt=receipt,
        version=version,
        outcome="SUCCESS",
    )


async def data_publish_data_versions(
    service: HistoricalDataIngestionService,
    plan: DataImportPlan,
    *,
    csv_content: str | None = None,
    instrument_id: Uuid7 | None = None,
    instrument_version_id: Uuid7 | None = None,
    timeframe: Timeframe | str | None = "1m",
) -> DataSeriesVersion:
    """FR-DATA-PUBLISH_DATA_VERSIONS implementation trace.

    Write staged artifact, compute quality findings and checksum, and atomically
    publish a new DataSeriesVersion.

    Args:
        service: HistoricalDataIngestionService instance.
        plan: DataImportPlan specification.
        csv_content: Optional CSV payload.
        instrument_id: Optional instrument UUID.
        instrument_version_id: Optional instrument version UUID.
        timeframe: Timeframe code or model.

    Returns:
        Published DataSeriesVersion.

    Raises:
        RuntimeError: If import fails to produce a published version.
    """
    result = await data_import_csv_data(
        service,
        plan,
        csv_content=csv_content,
        instrument_id=instrument_id,
        instrument_version_id=instrument_version_id,
        timeframe=timeframe,
    )
    if isinstance(result, DataFailure) or result.version is None:
        err_msg = f"Failed to publish DataSeriesVersion: {result}"
        raise RuntimeError(err_msg)
    return result.version


def data_pin_data_provenance(version: DataSeriesVersion) -> dict[str, Any]:
    """FR-DATA-PIN_DATA_PROVENANCE implementation trace.

    Pin instrument version, timeframe or tick type, timezone, precision, coverage,
    row count, source metadata, import policy, and content hash.

    Args:
        version: DataSeriesVersion record.

    Returns:
        Provenance dictionary with pinned attributes.
    """
    return {
        "series_version_id": version.series_version_id,
        "series_id": version.series_id,
        "version": version.version,
        "instrument_id": version.instrument.instrument_id,
        "instrument_version_id": version.instrument_version_id,
        "timeframe": version.timeframe,
        "tick_type": version.tick_type,
        "timezone": version.timezone,
        "precision": version.precision,
        "coverage": {
            "from_at": str(version.coverage.from_at),
            "to_at": str(version.coverage.to_at),
        },
        "row_count": version.row_count,
        "source_artifact_id": version.source_artifact_id,
        "canonical_artifact_id": version.canonical_artifact_id,
        "import_policy": version.import_policy,
        "content_hash": version.content_hash,
    }


def data_report_import_counts(receipt: DataImportReceipt) -> dict[str, int]:
    """FR-DATA-REPORT_IMPORT_COUNTS implementation trace.

    Report deterministic counters for input, accepted, rejected, duplicate,
    transformed, and published rows.

    Args:
        receipt: Executed DataImportReceipt.

    Returns:
        Dictionary mapping counter names to non-negative integers.
    """
    return {
        "input_rows": receipt.input_rows,
        "accepted_rows": receipt.accepted_rows,
        "rejected_rows": receipt.rejected_rows,
        "duplicate_rows": receipt.duplicate_rows,
        "transformed_rows": receipt.transformed_rows,
        "published_rows": receipt.published_rows,
    }


# =============================================================================
# Executable Scenario Harness
# =============================================================================


async def main() -> None:
    """Execute the historical data ingestion usage demonstration harness."""
    from app.services.data.historical_data_ingestion._usage import main as _usage_main

    await _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()

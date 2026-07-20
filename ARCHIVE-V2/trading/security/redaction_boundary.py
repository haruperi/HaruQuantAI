"""Recursive redaction boundary and durable dead-letter logging.

This module provides the trading runtime boundary for redacting outbound data
and writing failed critical events to a crash-resilient write-ahead dead-letter
log. It is filesystem-only, import-safe, and relies on injected clocks for all
timestamps.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from app.services.trading.contracts import JsonObject, JsonValue
from app.utils.logger import logger
from app.utils.security import redact_value
from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from app.services.trading.state import Clock

type DeadLetterProcessor = Callable[[JsonObject], bool]


class RedactionBoundaryResult(BaseModel):
    """Result of recursive trading redaction.

    Attributes:
        payload: Redacted JSON object.
        blocked_live_scopes: Scopes that must fail closed after boundary
            failure handling.
        alert: Redacted operator alert payload.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    payload: JsonObject
    blocked_live_scopes: tuple[str, ...] = Field(default_factory=tuple)
    alert: JsonObject | None = None

    @model_validator(mode="after")
    def validate_result(self) -> RedactionBoundaryResult:
        """Validate redaction boundary result.

        Returns:
            RedactionBoundaryResult: Validated result.
        """
        logger.info(
            "Validated redaction boundary result with {} blocked scopes.",
            len(self.blocked_live_scopes),
        )
        return self


class DeadLetterRecord(BaseModel):
    """Write-ahead dead-letter event record.

    Attributes:
        event_id: Deterministic event identifier derived from redacted payload.
        source: Source subsystem.
        reason: Redacted failure reason.
        payload: Redacted failed payload.
        retry_count: Number of recovery attempts.
        max_retries: Poison-pill retry threshold.
        written_at: Timestamp supplied by injected Clock.
        blocked_live_scopes: Live scopes blocked until recovery.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str
    source: str
    reason: str
    payload: JsonObject
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(ge=1)
    written_at: str
    blocked_live_scopes: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_record(self) -> DeadLetterRecord:
        """Validate a dead-letter record.

        Returns:
            DeadLetterRecord: Validated record.

        Raises:
            ValueError: If identifiers are blank.
        """
        logger.info("Validating dead-letter record {}.", self.event_id)
        if not self.event_id.strip():
            raise ValueError("event_id must be non-empty.")
        if not self.source.strip():
            raise ValueError("source must be non-empty.")
        if not self.reason.strip():
            raise ValueError("reason must be non-empty.")
        if not self.written_at.strip():
            raise ValueError("written_at must be non-empty.")
        return self

    def with_retry_count(self, retry_count: int) -> DeadLetterRecord:
        """Return a copy with an updated retry count.

        Args:
            retry_count: New retry count.

        Returns:
            DeadLetterRecord: Updated immutable record.
        """
        logger.info("Updating dead-letter retry count for {}.", self.event_id)
        return self.model_copy(update={"retry_count": retry_count})


class ManualReviewRecord(BaseModel):
    """Poison-pill DLQ event relocated for manual review.

    Attributes:
        record: Failed dead-letter record.
        alert: High-severity redacted operator alert payload.
        relocated_at: Timestamp supplied by injected Clock.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    record: DeadLetterRecord
    alert: JsonObject
    relocated_at: str

    @model_validator(mode="after")
    def validate_manual_review(self) -> ManualReviewRecord:
        """Validate manual-review record.

        Returns:
            ManualReviewRecord: Validated record.
        """
        logger.info(
            "Validated manual-review DLQ record {}.",
            self.record.event_id,
        )
        return self


class DeadLetterWriteResult(BaseModel):
    """Result of a write-ahead DLQ write.

    Attributes:
        record: Durable dead-letter record.
        alert: Redacted high-severity operator alert payload.
        blocked_live_scopes: Live scopes to block.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    record: DeadLetterRecord
    alert: JsonObject
    blocked_live_scopes: tuple[str, ...]

    @model_validator(mode="after")
    def validate_write_result(self) -> DeadLetterWriteResult:
        """Validate DLQ write result.

        Returns:
            DeadLetterWriteResult: Validated result.
        """
        logger.info("Validated DLQ write result for {}.", self.record.event_id)
        return self


class WriteAheadDeadLetterQueue:
    """Crash-resilient JSONL write-ahead dead-letter queue.

    Args:
        path: Primary write-ahead DLQ JSONL file.
        manual_review_path: Manual-review poison-pill JSONL file.
        clock: Injected clock used for timestamps.
        max_retries: Maximum recovery attempts before manual review.
    """

    def __init__(
        self,
        *,
        path: Path,
        manual_review_path: Path,
        clock: Clock,
        max_retries: int = 3,
    ) -> None:
        """Initialize a write-ahead dead-letter queue.

        Args:
            path: Primary write-ahead DLQ JSONL file.
            manual_review_path: Manual-review poison-pill JSONL file.
            clock: Injected clock used for timestamps.
            max_retries: Maximum recovery attempts before manual review.

        Raises:
            ValueError: If max_retries is less than one.
        """
        logger.info("Initializing write-ahead DLQ at {}.", path)
        if max_retries < 1:
            raise ValueError("max_retries must be at least one.")
        self._path = path
        self._manual_review_path = manual_review_path
        self._clock = clock
        self._max_retries = max_retries

    def write_failed_event(
        self,
        *,
        source: str,
        reason: str,
        payload: Mapping[str, object],
        affected_live_scopes: tuple[str, ...],
    ) -> DeadLetterWriteResult:
        """Write a failed critical event to the write-ahead DLQ.

        Args:
            source: Source subsystem.
            reason: Failure reason.
            payload: Raw event payload to redact before persistence.
            affected_live_scopes: Live scopes to block until recovery.

        Returns:
            DeadLetterWriteResult: Write result and alert instructions.

        Raises:
            ValueError: If source, reason, or affected scope values are blank.
            OSError: If the durable write fails.
        """
        logger.info("Writing failed event from {} to DLQ.", source)
        if not source.strip():
            raise ValueError("source must be non-empty.")
        if not reason.strip():
            raise ValueError("reason must be non-empty.")
        if any(not scope.strip() for scope in affected_live_scopes):
            raise ValueError("affected_live_scopes must not contain blank values.")

        redacted = _ensure_json_object(redact_value(payload))
        safe_reason = str(redact_value(reason))
        record = DeadLetterRecord(
            event_id=_event_id(source=source, payload=redacted),
            source=source,
            reason=safe_reason,
            payload=redacted,
            retry_count=0,
            max_retries=self._max_retries,
            written_at=self._clock.now_utc().isoformat(),
            blocked_live_scopes=affected_live_scopes,
        )
        self._append_jsonl(self._path, record.model_dump(mode="json"))
        alert = _build_alert(
            event_id=record.event_id,
            source=source,
            severity="high",
            message="Critical trading event routed to dead-letter queue.",
            blocked_live_scopes=affected_live_scopes,
        )
        logger.warning("Dead-letter event {} persisted.", record.event_id)
        return DeadLetterWriteResult(
            record=record,
            alert=alert,
            blocked_live_scopes=affected_live_scopes,
        )

    def recover_pending(self, *, processor: DeadLetterProcessor) -> tuple[str, ...]:
        """Replay pending DLQ records exactly once where processing succeeds.

        Records that process successfully are removed from the pending write
        ahead log. Records that fail are retained with incremented retry counts
        until the poison-pill threshold moves them to manual review.

        Args:
            processor: Callable that returns True when a record is reconciled.

        Returns:
            tuple[str, ...]: Event IDs successfully recovered.
        """
        logger.info("Recovering pending dead-letter records.")
        recovered: list[str] = []
        retained: list[DeadLetterRecord] = []
        for record in self.read_pending():
            logger.debug("Replaying DLQ record {}.", record.event_id)
            if processor(record.payload):
                recovered.append(record.event_id)
                continue
            retry_count = record.retry_count + 1
            if retry_count >= record.max_retries:
                self._relocate_to_manual_review(record.with_retry_count(retry_count))
                continue
            retained.append(record.with_retry_count(retry_count))
        self._rewrite_pending(retained)
        logger.info("Recovered {} dead-letter records.", len(recovered))
        return tuple(recovered)

    def read_pending(self) -> tuple[DeadLetterRecord, ...]:
        """Read all pending DLQ records.

        Returns:
            tuple[DeadLetterRecord, ...]: Pending records.

        Raises:
            ValueError: If a persisted line cannot be parsed.
        """
        logger.info("Reading pending dead-letter records.")
        if not self._path.exists():
            return ()
        records: list[DeadLetterRecord] = []
        lines = self._path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.error("DLQ parse failed at line {}.", line_number)
                raise ValueError("dead-letter log contains invalid JSON.") from exc
            if not isinstance(parsed, dict):
                raise TypeError("dead-letter log line must contain an object.")
            records.append(DeadLetterRecord.model_validate(parsed))
        return tuple(records)

    def read_manual_review(self) -> tuple[ManualReviewRecord, ...]:
        """Read all manual-review poison-pill records.

        Returns:
            tuple[ManualReviewRecord, ...]: Manual-review records.
        """
        logger.info("Reading manual-review dead-letter records.")
        if not self._manual_review_path.exists():
            return ()
        records: list[ManualReviewRecord] = []
        for line in self._manual_review_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(ManualReviewRecord.model_validate(json.loads(line)))
        return tuple(records)

    def _relocate_to_manual_review(self, record: DeadLetterRecord) -> None:
        """Relocate a poison-pill event to manual review.

        Args:
            record: Poison-pill record to relocate.
        """
        logger.warning("Relocating poison-pill DLQ record {}.", record.event_id)
        manual = ManualReviewRecord(
            record=record,
            alert=_build_alert(
                event_id=record.event_id,
                source=record.source,
                severity="high",
                message="DLQ event exceeded retry threshold and requires review.",
                blocked_live_scopes=record.blocked_live_scopes,
            ),
            relocated_at=self._clock.now_utc().isoformat(),
        )
        self._append_jsonl(self._manual_review_path, manual.model_dump(mode="json"))

    def _rewrite_pending(self, records: list[DeadLetterRecord]) -> None:
        """Rewrite the pending DLQ file with retained records.

        Args:
            records: Records to retain.
        """
        logger.info("Rewriting pending DLQ with {} records.", len(records))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record.model_dump(mode="json"), sort_keys=True))
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(self._path)

    def _append_jsonl(self, path: Path, payload: JsonObject) -> None:
        """Append a JSON object to a crash-resilient JSONL file.

        Args:
            path: JSONL file path.
            payload: JSON object to append.
        """
        logger.debug("Appending JSONL record to {}.", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())


def redact_for_boundary(
    payload: Mapping[str, object],
    *,
    blocked_live_scopes: tuple[str, ...] = (),
    alert_message: str | None = None,
) -> RedactionBoundaryResult:
    """Redact a payload before export to logs, notifications, events, or chat.

    Args:
        payload: Raw payload to recursively redact.
        blocked_live_scopes: Optional scopes blocked by the boundary decision.
        alert_message: Optional operator alert message.

    Returns:
        RedactionBoundaryResult: Redacted payload and optional alert.
    """
    logger.info("Redacting trading payload at security boundary.")
    redacted = _ensure_json_object(redact_value(payload))
    alert = None
    if alert_message is not None:
        alert = _build_alert(
            event_id=_event_id(source="redaction_boundary", payload=redacted),
            source="redaction_boundary",
            severity="high",
            message=alert_message,
            blocked_live_scopes=blocked_live_scopes,
        )
    return RedactionBoundaryResult(
        payload=redacted,
        blocked_live_scopes=blocked_live_scopes,
        alert=alert,
    )


def _build_alert(
    *,
    event_id: str,
    source: str,
    severity: str,
    message: str,
    blocked_live_scopes: tuple[str, ...],
) -> JsonObject:
    """Build a redacted operator alert payload.

    Args:
        event_id: Event identifier.
        source: Source subsystem.
        severity: Alert severity.
        message: Alert message.
        blocked_live_scopes: Blocked live scopes.

    Returns:
        JsonObject: Redacted alert payload.
    """
    logger.debug("Building redacted alert for event {}.", event_id)
    return {
        "event_id": event_id,
        "source": source,
        "severity": severity,
        "message": str(redact_value(message)),
        "blocked_live_scopes": list(blocked_live_scopes),
    }


def _event_id(*, source: str, payload: JsonObject) -> str:
    """Build a deterministic event ID from source and redacted payload.

    Args:
        source: Source subsystem.
        payload: Redacted payload.

    Returns:
        str: Deterministic event identifier.
    """
    logger.debug("Computing deterministic DLQ event ID for {}.", source)
    material = json.dumps({"source": source, "payload": payload}, sort_keys=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _ensure_json_object(value: object) -> JsonObject:
    """Return a redacted JSON object.

    Args:
        value: Value expected to be a JSON mapping.

    Returns:
        JsonObject: JSON-safe mapping.

    Raises:
        TypeError: If value is not a mapping.
    """
    logger.debug("Ensuring redacted payload is a JSON object.")
    if not isinstance(value, Mapping):
        raise TypeError("redacted payload must be a mapping.")
    result: JsonObject = {}
    for key, item in value.items():
        result[str(key)] = _ensure_json_value(item)
    return result


def _ensure_json_value(value: object) -> JsonValue:
    """Return a JSON-safe redacted value.

    Args:
        value: Redacted value.

    Returns:
        JsonValue: JSON-safe value.
    """
    logger.debug("Ensuring redacted value is JSON-safe.")
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, Mapping):
        return _ensure_json_object(value)
    if isinstance(value, list | tuple | set):
        return [_ensure_json_value(item) for item in value]
    return str(value)

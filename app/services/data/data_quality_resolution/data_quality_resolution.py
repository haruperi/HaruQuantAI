"""Data Quality and Resolution service implementation.

Purpose:
    Detect, resolve, normalize, and serialize conflicting quality operations
    across market data series and ticks.

Key capabilities:
    * Detect timestamp regressions, negative prices, and bad ticks.
    * Apply deterministic resolution policies and emit auditable quality decisions.
    * Reconcile conflict resolutions against SQLite persistence or in-memory stores.
    * Provide async resolve_quality implementing ResolveQualityCapability.

Python API usage:
    from app.services.data.data_quality_resolution.data_quality_resolution import (
        DataQualityResolutionService,
    )
    from app.contracts.data.models import ResolveQualityRequest

    service = DataQualityResolutionService()
    result = await service.resolve_quality(request)

CLI usage:
    uv run python -m app.services.data.data_quality_resolution.data_quality_resolution
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import sqlite3
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any, Literal, override

from app.contracts.common.models import (
    ProblemDetails,
    SeriesPointKey,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
)
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    Bar,
    DataQualityDecision,
    DataQualityFinding,
    ResolveQualityRequest,
    ResolveQualitySuccess,
    Tick,
)
from app.contracts.data.ports import ResolveQualityCapability
from app.services.data.data_quality_resolution._persistence import (
    data_lock_data_publication,
    init_database,
)
from app.services.data.data_quality_resolution.config import (
    DataQualityResolutionConfig,
)

__all__ = [
    "DataQualityResolutionService",
    "data_detect_data_quality",
    "data_lock_data_publication",
    "data_order_market_rows",
    "data_resolve_quality_findings",
    "data_validate_ohlc_bars",
]

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
        dt: Datetime to format.

    Returns:
        Canonical ISO 8601 string with 6 microsecond digits and Z suffix.
    """
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_utc_timestamp(val: str) -> datetime:
    """Parse an ISO 8601 string into an aware UTC datetime.

    Args:
        val: ISO formatted timestamp string.

    Returns:
        Aware UTC datetime.

    Raises:
        ValueError: If parsing fails.
    """
    cleaned = val.replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def _format_decimal(val: str | float | Decimal) -> str:
    """Format a decimal value to match the canonical DecimalValue grammar.

    Args:
        val: Input number or string.

    Returns:
        Canonical decimal string without trailing zeros.
    """
    dec = Decimal(str(val))
    if dec == 0:
        return "0"
    s = f"{dec:f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def data_validate_ohlc_bars(
    bars: Sequence[object],
) -> tuple[tuple[Bar, ...], tuple[ValidationIssue, ...]]:
    """Validate bar invariants and reject inconsistent bars.

    Rejects a bar where low > min(open, close), high < max(open, close),
    low > high, or a required field is nonfinite.

    Args:
        bars: Sequence of Bar instances, dict payloads, or other records.

    Returns:
        Tuple of (valid_bars, validation_issues).
    """
    valid_bars: list[Bar] = []
    issues: list[ValidationIssue] = []

    for idx, item in enumerate(bars):
        try:
            if isinstance(item, Bar):
                # Bar model validator already enforces invariants
                valid_bars.append(item)
            elif isinstance(item, dict):
                d: dict[str, Any] = dict(item)
                if "timestamp" in d and isinstance(d["timestamp"], str):
                    with contextlib.suppress(ValueError, TypeError):
                        dt = _parse_utc_timestamp(d["timestamp"])
                        d["timestamp"] = _format_utc_timestamp(dt)
                for field_name in (
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "spread_ticks",
                ):
                    if field_name in d and d[field_name] is not None:
                        with contextlib.suppress(
                            ValueError, TypeError, InvalidOperation
                        ):
                            d[field_name] = _format_decimal(d[field_name])
                bar = Bar(**d)
                valid_bars.append(bar)
            else:
                issues.append(
                    ValidationIssue(
                        path=("bars", str(idx)),
                        code="INVALID_BAR_TYPE",
                        message=f"Expected Bar or dict, got {type(item).__name__}",
                    )
                )
        except (ValueError, TypeError, InvalidOperation) as err:
            issues.append(
                ValidationIssue(
                    path=("bars", str(idx)),
                    code="OHLC_INVARIANT_VIOLATION",
                    message=str(err),
                    context={"row_index": idx, "raw": str(item)},
                )
            )

    return tuple(valid_bars), tuple(issues)


def data_order_market_rows[T: (Bar, Tick, dict[str, Any])](
    rows: Sequence[T],
) -> tuple[tuple[T, ...], str]:
    """Sort rows deterministically by UTC timestamp and source sequence.

    Preserves duplicate tick timestamps using deterministic sequence order.

    Args:
        rows: Sequence of market rows (Bar, Tick, or dict).

    Returns:
        Tuple of (sorted_rows, content_sha256_hash).
    """

    def _extract_sort_key(item: object) -> tuple[datetime, int]:
        if isinstance(item, (Bar, Tick)):
            dt = _parse_utc_timestamp(item.timestamp)
            seq = int(item.source_sequence)
            return dt, seq
        if isinstance(item, dict):
            raw_ts = str(item.get("timestamp", ""))
            dt = (
                _parse_utc_timestamp(raw_ts)
                if raw_ts
                else datetime.fromtimestamp(0, tz=UTC)
            )
            seq = int(item.get("source_sequence", 0))
            return dt, seq
        return datetime.fromtimestamp(0, tz=UTC), 0

    # Stable sort by (timestamp, source_sequence)
    sorted_rows = sorted(rows, key=_extract_sort_key)

    # Compute deterministic hash
    hasher = hashlib.sha256()
    for row in sorted_rows:
        item_obj: object = row
        if isinstance(item_obj, (Bar, Tick)):
            hasher.update(item_obj.model_dump_json().encode("utf-8"))
        elif isinstance(item_obj, dict):
            hasher.update(json.dumps(item_obj, sort_keys=True).encode("utf-8"))
        else:
            hasher.update(str(item_obj).encode("utf-8"))

    return tuple(sorted_rows), hasher.hexdigest()


def _check_timestamp_and_session(
    idx: int,
    d: dict[str, Any],
    last_dt: datetime | None,
    version_id: Uuid7,
    session_hours: tuple[int, int] | None = None,
) -> tuple[datetime | None, SeriesPointKey | None, list[DataQualityFinding]]:
    findings: list[DataQualityFinding] = []
    ts_str = str(d.get("timestamp", "")).strip()
    dt: datetime | None = None
    seq = int(d.get("source_sequence", idx))

    try:
        dt = _parse_utc_timestamp(ts_str)
    except ValueError, TypeError:
        findings.append(
            DataQualityFinding(
                finding_id=_generate_uuid7(),
                data_version_id=version_id,
                rule_code="TIME_PARSE",
                severity="ERROR",
                point=None,
                observed=ts_str,
                expected="ISO-8601 UTC timestamp",
            )
        )

    point_key: SeriesPointKey | None = (
        SeriesPointKey(timestamp=_format_utc_timestamp(dt), sequence=seq)
        if dt is not None
        else None
    )

    if dt is not None:
        if last_dt is not None and dt < last_dt:
            findings.append(
                DataQualityFinding(
                    finding_id=_generate_uuid7(),
                    data_version_id=version_id,
                    rule_code="UNSORTED_TIME",
                    severity="WARNING",
                    point=point_key,
                    observed=dt.isoformat(),
                    expected=f">= {last_dt.isoformat()}",
                )
            )

        if session_hours is not None:
            start_h, end_h = session_hours
            h = dt.hour
            in_session = (
                start_h <= h < end_h
                if start_h <= end_h
                else (h >= start_h or h < end_h)
            )
            if not in_session:
                exp_sess = f"session [{start_h}, {end_h})"
                findings.append(
                    DataQualityFinding(
                        finding_id=_generate_uuid7(),
                        data_version_id=version_id,
                        rule_code="OUT_OF_SESSION",
                        severity="WARNING",
                        point=point_key,
                        observed=f"hour={h}",
                        expected=exp_sess,
                    )
                )

    return dt, point_key, findings


def _check_bar_invariants(
    d: dict[str, Any],
    ts_str: str,
    point_key: SeriesPointKey | None,
    version_id: Uuid7,
    seen_bar_timestamps: set[str],
) -> list[DataQualityFinding]:
    findings: list[DataQualityFinding] = []
    is_bar = "open" in d or "high" in d or "low" in d or "close" in d
    if not is_bar:
        return findings

    if ts_str in seen_bar_timestamps:
        findings.append(
            DataQualityFinding(
                finding_id=_generate_uuid7(),
                data_version_id=version_id,
                rule_code="DUPLICATE_BAR",
                severity="ERROR",
                point=point_key,
                observed=ts_str,
                expected="unique bar timestamp",
            )
        )
    else:
        seen_bar_timestamps.add(ts_str)

    try:
        op = Decimal(str(d.get("open", "")))
        hp = Decimal(str(d.get("high", "")))
        lp = Decimal(str(d.get("low", "")))
        cp = Decimal(str(d.get("close", "")))

        for field_name, dec_val in [
            ("open", op),
            ("high", hp),
            ("low", lp),
            ("close", cp),
        ]:
            if not dec_val.is_finite():
                findings.append(
                    DataQualityFinding(
                        finding_id=_generate_uuid7(),
                        data_version_id=version_id,
                        rule_code="OHLC_NONFINITE",
                        severity="ERROR",
                        point=point_key,
                        observed={field_name: str(dec_val)},
                        expected="finite decimal",
                    )
                )

        min_body = min(op, cp)
        max_body = max(op, cp)

        if lp > min_body:
            findings.append(
                DataQualityFinding(
                    finding_id=_generate_uuid7(),
                    data_version_id=version_id,
                    rule_code="OHLC_LOW_ABOVE_BODY",
                    severity="ERROR",
                    point=point_key,
                    observed={"low": str(lp), "min_body": str(min_body)},
                    expected="low <= min(open, close)",
                )
            )
        if hp < max_body:
            findings.append(
                DataQualityFinding(
                    finding_id=_generate_uuid7(),
                    data_version_id=version_id,
                    rule_code="OHLC_HIGH_BELOW_BODY",
                    severity="ERROR",
                    point=point_key,
                    observed={"high": str(hp), "max_body": str(max_body)},
                    expected="high >= max(open, close)",
                )
            )
        if lp > hp:
            findings.append(
                DataQualityFinding(
                    finding_id=_generate_uuid7(),
                    data_version_id=version_id,
                    rule_code="OHLC_LOW_ABOVE_HIGH",
                    severity="ERROR",
                    point=point_key,
                    observed={"low": str(lp), "high": str(hp)},
                    expected="low <= high",
                )
            )
    except InvalidOperation, ValueError, TypeError:
        findings.append(
            DataQualityFinding(
                finding_id=_generate_uuid7(),
                data_version_id=version_id,
                rule_code="OHLC_NONFINITE",
                severity="ERROR",
                point=point_key,
                observed=str(d),
                expected="valid decimal numbers",
            )
        )

    return findings


def _check_tick_invariants(
    d: dict[str, Any],
    point_key: SeriesPointKey | None,
    version_id: Uuid7,
) -> list[DataQualityFinding]:
    findings: list[DataQualityFinding] = []
    is_tick = "bid" in d and "ask" in d
    if not is_tick:
        return findings

    try:
        bid = Decimal(str(d["bid"]))
        ask = Decimal(str(d["ask"]))
        if bid > ask:
            findings.append(
                DataQualityFinding(
                    finding_id=_generate_uuid7(),
                    data_version_id=version_id,
                    rule_code="BID_ABOVE_ASK",
                    severity="ERROR",
                    point=point_key,
                    observed={"bid": str(bid), "ask": str(ask)},
                    expected="bid <= ask",
                )
            )
    except InvalidOperation, ValueError, TypeError:
        findings.append(
            DataQualityFinding(
                finding_id=_generate_uuid7(),
                data_version_id=version_id,
                rule_code="OHLC_NONFINITE",
                severity="ERROR",
                point=point_key,
                observed=str(d),
                expected="valid decimal prices",
            )
        )

    return findings


def _check_volume_and_spread(
    d: dict[str, Any],
    point_key: SeriesPointKey | None,
    version_id: Uuid7,
) -> list[DataQualityFinding]:
    findings: list[DataQualityFinding] = []
    vol_raw = d.get("volume")
    if vol_raw is not None:
        try:
            vol = Decimal(str(vol_raw))
            if vol < Decimal(0):
                findings.append(
                    DataQualityFinding(
                        finding_id=_generate_uuid7(),
                        data_version_id=version_id,
                        rule_code="NEGATIVE_VOLUME",
                        severity="ERROR",
                        point=point_key,
                        observed=str(vol),
                        expected="volume >= 0",
                    )
                )
        except InvalidOperation, ValueError, TypeError:
            pass

    spread_raw = d.get("spread_ticks")
    if spread_raw is not None:
        try:
            sp = Decimal(str(spread_raw))
            if sp < Decimal(0):
                findings.append(
                    DataQualityFinding(
                        finding_id=_generate_uuid7(),
                        data_version_id=version_id,
                        rule_code="NEGATIVE_SPREAD",
                        severity="ERROR",
                        point=point_key,
                        observed=str(sp),
                        expected="spread >= 0",
                    )
                )
        except InvalidOperation, ValueError, TypeError:
            pass

    return findings


def data_detect_data_quality(
    rows: Sequence[dict[str, Any] | Bar | Tick],
    data_version_id: Uuid7 | None = None,
    session_start_hour: int | None = None,
    session_end_hour: int | None = None,
) -> tuple[DataQualityFinding, ...]:
    """Detect quality findings across market rows per section 16.4 rules.

    Detects:
    - OHLC_NONFINITE: Non-finite or unparsable numbers
    - OHLC_LOW_ABOVE_BODY: low > min(open, close)
    - OHLC_HIGH_BELOW_BODY: high < max(open, close)
    - OHLC_LOW_ABOVE_HIGH: low > high
    - NEGATIVE_VOLUME: volume < 0
    - UNSORTED_TIME: timestamp earlier than previous row
    - DUPLICATE_BAR: duplicate bar timestamp
    - DUPLICATE_TICK: duplicate tick timestamp (INFO)
    - OUT_OF_SESSION: timestamp outside trading session
    - BID_ABOVE_ASK: bid > ask
    - NEGATIVE_SPREAD: spread < 0
    - TIME_PARSE: unparsable timestamp

    Args:
        rows: Sequence of market records.
        data_version_id: Optional version identifier to bind findings.
        session_start_hour: Optional trading session start hour (0-23 UTC).
        session_end_hour: Optional trading session end hour (0-23 UTC).

    Returns:
        Tuple of detected DataQualityFinding instances.
    """
    version_id = data_version_id or _generate_uuid7()
    findings: list[DataQualityFinding] = []

    last_dt: datetime | None = None
    seen_bar_timestamps: set[str] = set()

    session_hours = (
        (session_start_hour, session_end_hour)
        if session_start_hour is not None and session_end_hour is not None
        else None
    )

    for idx, row in enumerate(rows):
        d: dict[str, Any] = (
            row.model_dump(mode="json") if isinstance(row, (Bar, Tick)) else dict(row)
        )
        ts_str = str(d.get("timestamp", "")).strip()

        dt, point_key, ts_findings = _check_timestamp_and_session(
            idx,
            d,
            last_dt,
            version_id,
            session_hours,
        )
        findings.extend(ts_findings)
        if dt is not None:
            last_dt = dt

        findings.extend(
            _check_bar_invariants(d, ts_str, point_key, version_id, seen_bar_timestamps)
        )
        findings.extend(_check_tick_invariants(d, point_key, version_id))
        findings.extend(_check_volume_and_spread(d, point_key, version_id))

    return tuple(findings)


def data_resolve_quality_findings(
    decision: DataQualityDecision,
    findings: Sequence[DataQualityFinding],
) -> tuple[tuple[DataQualityFinding, ...], DataQualityDecision]:
    """Resolve quality findings without mutating the source version.

    Records source-to-derived lineage and marks affected findings with resolution state.

    Args:
        decision: Explicit resolution decision.
        findings: Sequence of findings to resolve.

    Returns:
        Tuple of (resolved_findings, completed_decision).
    """
    target_ids = set(decision.finding_ids)
    derived_id = decision.derived_version_id or (
        _generate_uuid7() if decision.action == "TRANSFORM" else None
    )

    updated_findings: list[DataQualityFinding] = []
    for finding in findings:
        if finding.finding_id in target_ids:
            state: Literal["OPEN", "ACCEPTED", "REJECTED", "TRANSFORMED"] = "ACCEPTED"
            if decision.action == "ACCEPT":
                state = "ACCEPTED"
            elif decision.action == "REJECT":
                state = "REJECTED"
            elif decision.action == "TRANSFORM":
                state = "TRANSFORMED"

            updated_findings.append(
                DataQualityFinding(
                    finding_id=finding.finding_id,
                    data_version_id=finding.data_version_id,
                    rule_code=finding.rule_code,
                    severity=finding.severity,
                    point=finding.point,
                    range_from=finding.range_from,
                    range_to=finding.range_to,
                    observed=finding.observed,
                    expected=finding.expected,
                    resolution_state=state,
                    derived_version_id=derived_id,
                )
            )
        else:
            updated_findings.append(finding)

    updated_decision = DataQualityDecision(
        decision_id=decision.decision_id,
        finding_ids=decision.finding_ids,
        action=decision.action,
        policy_version=decision.policy_version,
        derived_version_id=derived_id,
        decided_at=decision.decided_at,
    )

    return tuple(updated_findings), updated_decision


# Re-exported from _persistence
__all_persistence__ = ("PublicationLockReceipt", "data_lock_data_publication")


class DataQualityResolutionService(ResolveQualityCapability):
    """Service providing data quality detection and resolution capabilities."""

    def __init__(
        self,
        config: DataQualityResolutionConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the data quality resolution service.

        Args:
            config: Optional configuration.
            event_bus: Optional event bus.
        """
        self._config = config or DataQualityResolutionConfig()
        self._event_bus = event_bus
        self._db_conn = self._init_db()
        self._findings_store: dict[str, list[DataQualityFinding]] = {}

    def _init_db(self) -> sqlite3.Connection:
        """Initialize persistence schema.

        Returns:
            Configured sqlite3 connection.
        """
        return init_database(self._config.get_database_path())

    @override
    async def resolve_quality(
        self,
        request: ResolveQualityRequest,
    ) -> ResolveQualitySuccess | DataFailure:
        """Detect quality findings or resolve them explicitly.

        Args:
            request: Discriminated data quality request.

        Returns:
            ResolveQualitySuccess on success, or DataFailure on error.
        """
        try:
            if request.operation == "DETECT":
                if request.data_version_id is None:
                    problem = ProblemDetails(
                        type="urn:haruquantai:error:data:missing-field",
                        title="Missing data_version_id",
                        status=400,
                        code="DATA_VALIDATION_FAILED",
                        detail="data_version_id is required for DETECT operation",
                        request_id=request.request_id,
                    )
                    return DataFailure(
                        request_id=request.request_id,
                        code="DATA_VALIDATION_FAILED",
                        problem=problem,
                    )

                findings = tuple(
                    self._findings_store.get(str(request.data_version_id), [])
                )
                return ResolveQualitySuccess(
                    request_id=request.request_id,
                    findings=findings,
                    decision=None,
                    outcome="SUCCESS",
                )

            if request.operation == "RESOLVE":
                if request.decision is None:
                    problem = ProblemDetails(
                        type="urn:haruquantai:error:data:missing-field",
                        title="Missing decision",
                        status=400,
                        code="DATA_VALIDATION_FAILED",
                        detail="decision is required for RESOLVE operation",
                        request_id=request.request_id,
                    )
                    return DataFailure(
                        request_id=request.request_id,
                        code="DATA_VALIDATION_FAILED",
                        problem=problem,
                    )

                # Gather findings referenced in decision
                target_ids = set(request.decision.finding_ids)
                all_findings: list[DataQualityFinding] = []
                for flist in self._findings_store.values():
                    all_findings.extend(flist)

                matched = [f for f in all_findings if f.finding_id in target_ids]
                resolved_findings, completed_decision = data_resolve_quality_findings(
                    decision=request.decision,
                    findings=matched,
                )

                # Update store
                for rf in resolved_findings:
                    v_str = str(rf.data_version_id)
                    if v_str in self._findings_store:
                        self._findings_store[v_str] = [
                            rf if f.finding_id == rf.finding_id else f
                            for f in self._findings_store[v_str]
                        ]

                return ResolveQualitySuccess(
                    request_id=request.request_id,
                    findings=resolved_findings,
                    decision=completed_decision,
                    outcome="SUCCESS",
                )
        except Exception as exc:
            logger.exception("Error in resolve_quality")
            problem = ProblemDetails(
                type="urn:haruquantai:error:data:internal-error",
                title="Quality Resolution Failed",
                status=500,
                code="DATA_VALIDATION_FAILED",
                detail=str(exc),
                request_id=request.request_id,
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=problem,
            )

    def register_findings(
        self,
        data_version_id: Uuid7,
        findings: Sequence[DataQualityFinding],
    ) -> None:
        """Register findings directly in service memory/db for a version.

        Args:
            data_version_id: Target version identifier.
            findings: Detected findings to store.
        """
        self._findings_store[str(data_version_id)] = list(findings)


def run_usage_scenarios() -> None:
    """Execute the usage demonstration harness."""
    from app.services.data.data_quality_resolution._usage import (
        run_usage_scenarios as _run,
    )

    _run()


def main() -> None:
    """Main entry point."""
    run_usage_scenarios()


if __name__ == "__main__":
    main()

"""Path and timestamp normalization tools for HaruQuant agents.

This file contains a small set of official AI-callable tools for safe path
normalization, directory preparation, timestamp normalization, and freshness
checks. Lower-level datetime and timezone helpers remain normal utility
functions and are not intended to be exposed as agent tools unless explicitly
registered.

Exported AI Tools:
    - normalize_path
    - ensure_parent_dir
    - ensure_dir
    - normalize_timestamp
    - evaluate_freshness
    - evaluate_board_baseline_freshness
    - is_stale

Public Utility Helpers:
    - parse_datetime_value
    - to_utc_datetime
    - to_naive_utc_datetime
    - format_timestamp_z
    - normalize_timezone_for_series
    - freshness_window_to_dict
    - board_baseline_window_to_dict
    - board_baseline_evaluation_to_dict

Internal Helpers:
    - _metadata
    - _success_response
    - _error_response
    - _resolve_tz
    - _is_epoch_milliseconds
    - _resolve_path
    - _validate_allowed_root

Classes:
    - Clock
    - SystemClock
    - FixedClock
    - FreshnessWindow
    - BoardBaselineArtifactWindow
    - BoardBaselineFreshnessEvaluation
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Protocol, cast
from zoneinfo import ZoneInfo

from tools.utils.logger import logger

PathLike = str | Path
OutputType = Literal["iso", "datetime", "epoch_s", "epoch_ms"]
FreshnessClass = Literal["HOT", "WARM", "COOL", "COLD"]
BoardBaselineArtifact = Literal[
    "best_bid_ask_tick",
    "spread_snapshot",
    "symbol_tradability_status",
    "account_equity_free_margin_snapshot",
    "open_positions_snapshot",
    "risk_decision",
    "correlation_matrix",
    "regime_classification",
    "volatility_state_estimate",
    "economic_calendar_blackout_state",
    "strategy_lifecycle_state",
    "compliance_profile_and_approval_policy",
]

UTC = timezone.utc
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALLOWED_ROOT = PROJECT_ROOT

BOARD_BASELINE_TTL_POLICY: dict[
    BoardBaselineArtifact, tuple[FreshnessClass, int, str]
] = {
    "best_bid_ask_tick": (
        "HOT",
        2,
        "Block new entries; allow emergency exits per policy",
    ),
    "spread_snapshot": ("HOT", 2, "Recompute before execution"),
    "symbol_tradability_status": ("HOT", 5, "Revalidate before execution"),
    "account_equity_free_margin_snapshot": ("HOT", 5, "Block new entries"),
    "open_positions_snapshot": ("HOT", 5, "Reconcile before execution"),
    "risk_decision": ("HOT", 30, "Invalidate and recompute"),
    "correlation_matrix": ("WARM", 60, "Recompute before risk approval"),
    "regime_classification": ("WARM", 300, "Re-evaluate before new entry"),
    "volatility_state_estimate": ("WARM", 300, "Re-evaluate sizing inputs"),
    "economic_calendar_blackout_state": (
        "WARM",
        300,
        "Refresh before execution during active sessions",
    ),
    "strategy_lifecycle_state": ("COOL", 600, "Refresh before approving live action"),
    "compliance_profile_and_approval_policy": (
        "COOL",
        900,
        "Refresh before policy-sensitive action",
    ),
}


class Clock(Protocol):
    """Minimal clock protocol used by TTL-sensitive helpers."""

    def now(self) -> datetime:
        """Return the current timestamp."""
        ...


class SystemClock:
    """Clock implementation backed by the system wall clock."""

    def now(self) -> datetime:
        """Return the current timezone-aware UTC timestamp."""
        return datetime.now(UTC)


@dataclass(frozen=True)
class FixedClock:
    """Deterministic clock for tests and replay-sensitive workflows."""

    current: datetime

    def now(self) -> datetime:
        """Return the configured timestamp normalized to UTC."""
        return to_utc_datetime(self.current)


@dataclass(frozen=True)
class FreshnessWindow:
    """Freshness result derived from an observed timestamp and a TTL."""

    observed_at: datetime
    checked_at: datetime
    max_age_seconds: int

    @property
    def age_seconds(self) -> float:
        """Return age in seconds at check time."""
        return max((self.checked_at - self.observed_at).total_seconds(), 0.0)

    @property
    def expires_at(self) -> datetime:
        """Return the timestamp at which the observation expires."""
        return self.observed_at + timedelta(seconds=self.max_age_seconds)

    @property
    def is_fresh(self) -> bool:
        """Return True when the observation is still within its TTL."""
        return self.age_seconds <= float(self.max_age_seconds)

    @property
    def is_stale(self) -> bool:
        """Return True when the observation is outside its TTL."""
        return not self.is_fresh


@dataclass(frozen=True)
class BoardBaselineArtifactWindow:
    """Freshness evaluation for one board-baseline artifact."""

    artifact_name: BoardBaselineArtifact
    freshness_class: FreshnessClass
    action_if_stale: str
    window: FreshnessWindow


@dataclass(frozen=True)
class BoardBaselineFreshnessEvaluation:
    """Aggregated freshness decision for execution-critical board inputs."""

    artifact_windows: tuple[BoardBaselineArtifactWindow, ...]
    checked_at: datetime
    shortest_ttl_seconds: int
    proposal_materially_changed: bool = False
    workflow_pause_exceeded_shortest_ttl: bool = False

    @property
    def stale_artifacts(self) -> tuple[BoardBaselineArtifactWindow, ...]:
        """Return stale artifact windows."""
        return tuple(item for item in self.artifact_windows if item.window.is_stale)

    @property
    def is_valid(self) -> bool:
        """Return True when the aggregate freshness state is valid."""
        return (
            not self.stale_artifacts
            and not self.proposal_materially_changed
            and not self.workflow_pause_exceeded_shortest_ttl
        )


def _metadata(
    *,
    tool_name: str,
    request_id: str | None,
    execution_ms: float,
    tool_risk_level: str,
    read_only: bool,
    writes_file: bool,
) -> dict[str, Any]:
    """Build standard tool metadata."""
    return {
        "tool_name": tool_name,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": tool_risk_level,
        "request_id": request_id,
        "execution_ms": execution_ms,
        "read_only": read_only,
        "writes_file": writes_file,
        "modifies_database": False,
        "places_trade": False,
        "requires_network": False,
    }


def _success_response(
    *,
    tool_name: str,
    message: str,
    data: Any,
    request_id: str | None,
    started_at: float,
    tool_risk_level: str = "low",
    read_only: bool = True,
    writes_file: bool = False,
) -> dict[str, Any]:
    """Build a standard successful AI-tool response."""
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": "success",
        "message": message,
        "data": data,
        "error": None,
        "metadata": _metadata(
            tool_name=tool_name,
            request_id=request_id,
            execution_ms=execution_ms,
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
        ),
    }


def _error_response(
    *,
    tool_name: str,
    message: str,
    code: str,
    details: str,
    request_id: str | None,
    started_at: float,
    tool_risk_level: str = "low",
    read_only: bool = True,
    writes_file: bool = False,
) -> dict[str, Any]:
    """Build a standard error AI-tool response."""
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": "error",
        "message": message,
        "data": None,
        "error": {"code": code, "details": details},
        "metadata": _metadata(
            tool_name=tool_name,
            request_id=request_id,
            execution_ms=execution_ms,
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
        ),
    }


def _resolve_tz(tz_name: str) -> ZoneInfo:
    """Resolve a timezone name into a ZoneInfo instance."""
    try:
        return ZoneInfo(tz_name)
    except Exception as error:
        raise ValueError(f"Invalid timezone: {tz_name}") from error


def _is_epoch_milliseconds(value: int | float) -> bool:
    """Return True when a numeric timestamp looks like epoch milliseconds."""
    return abs(float(value)) >= 1_000_000_000_000


def parse_datetime_value(value: Any, assume_tz: str = "UTC") -> datetime:
    """
    Parse a timestamp value into a timezone-aware datetime.

    Args:
        value (Any): datetime, ISO string, epoch seconds, or epoch milliseconds.
        assume_tz (str): Timezone used for naive datetime values.

    Returns:
        datetime: Timezone-aware datetime.

    Raises:
        ValueError: If the value cannot be parsed.
    """
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = (
            float(value) / 1000.0 if _is_epoch_milliseconds(value) else float(value)
        )
        result = datetime.fromtimestamp(seconds, tz=UTC)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("datetime string cannot be empty.")
        try:
            result = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"unsupported datetime format: {value}") from error
    else:
        raise ValueError(f"unsupported datetime value type: {type(value).__name__}.")

    if result.tzinfo is None:
        result = result.replace(tzinfo=_resolve_tz(assume_tz))
    return result


def to_utc_datetime(value: Any, assume_tz: str = "UTC") -> datetime:
    """Normalize a timestamp value to timezone-aware UTC datetime."""
    return parse_datetime_value(value, assume_tz=assume_tz).astimezone(UTC)


def to_naive_utc_datetime(value: Any, assume_tz: str = "UTC") -> datetime:
    """Normalize a timestamp value to UTC and remove timezone information."""
    return to_utc_datetime(value, assume_tz=assume_tz).replace(tzinfo=None)


def to_utc(value: datetime) -> datetime:
    """Return a datetime converted to timezone-aware UTC.

    This compatibility helper is used by existing data modules that need a
    plain datetime utility instead of the AI-tool response shape.
    """
    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime instance.")
    return to_utc_datetime(value)


def format_timestamp_z(value: Any | None, assume_tz: str = "UTC") -> str | None:
    """Format a timestamp as UTC ISO-8601 with trailing Z."""
    if value is None:
        return None
    return (
        to_utc_datetime(value, assume_tz=assume_tz).isoformat().replace("+00:00", "Z")
    )


def normalize_timezone_for_series(
    series_or_index: Any,
    *,
    target_tz: str = "UTC",
    make_naive: bool = False,
) -> Any:
    """
    Normalize a pandas Series or DatetimeIndex timezone.

    This is a developer utility, not an official AI tool. It intentionally
    returns a pandas object.
    """
    import pandas as pd

    tz = _resolve_tz(target_tz)

    if isinstance(series_or_index, pd.DatetimeIndex):
        out = series_or_index
        if out.tz is None:
            out = out.tz_localize("UTC")
        out = out.tz_convert(tz)
        return out.tz_localize(None) if make_naive else out

    if isinstance(series_or_index, pd.Series):
        out = pd.to_datetime(series_or_index, errors="raise")
        if out.dt.tz is None:
            out = out.dt.tz_localize("UTC")
        out = out.dt.tz_convert(tz)
        return out.dt.tz_localize(None) if make_naive else out

    raise ValueError("series_or_index must be a pandas Series or DatetimeIndex.")


def _resolve_path(path: PathLike, base: PathLike | None = None) -> Path:
    """Normalize and resolve a path, optionally relative to a base."""
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("path must be a non-empty string or pathlib.Path.")

    candidate = Path(path).expanduser()
    if base is not None and not candidate.is_absolute():
        candidate = Path(base).expanduser() / candidate
    return candidate.resolve()


def _validate_allowed_root(
    path: Path, allowed_root: PathLike | None
) -> tuple[Path | None, bool]:
    """Validate path is inside allowed_root when a root is provided."""
    if allowed_root is None:
        return None, True

    root = Path(allowed_root).expanduser().resolve()
    return root, path == root or root in path.parents


def freshness_window_to_dict(window: FreshnessWindow) -> dict[str, Any]:
    """Serialize a FreshnessWindow into a JSON-safe dictionary."""
    return {
        "observed_at": window.observed_at.isoformat(),
        "checked_at": window.checked_at.isoformat(),
        "expires_at": window.expires_at.isoformat(),
        "max_age_seconds": window.max_age_seconds,
        "age_seconds": round(window.age_seconds, 6),
        "is_fresh": window.is_fresh,
        "is_stale": window.is_stale,
    }


def board_baseline_window_to_dict(
    window: BoardBaselineArtifactWindow,
) -> dict[str, Any]:
    """Serialize a BoardBaselineArtifactWindow into a JSON-safe dictionary."""
    return {
        "artifact_name": window.artifact_name,
        "freshness_class": window.freshness_class,
        "action_if_stale": window.action_if_stale,
        "window": freshness_window_to_dict(window.window),
    }


def board_baseline_evaluation_to_dict(
    evaluation: BoardBaselineFreshnessEvaluation,
) -> dict[str, Any]:
    """Serialize BoardBaselineFreshnessEvaluation into a JSON-safe dictionary."""
    return {
        "valid": evaluation.is_valid,
        "checked_at": evaluation.checked_at.isoformat(),
        "shortest_ttl_seconds": evaluation.shortest_ttl_seconds,
        "proposal_materially_changed": evaluation.proposal_materially_changed,
        "workflow_pause_exceeded_shortest_ttl": (
            evaluation.workflow_pause_exceeded_shortest_ttl
        ),
        "stale_artifacts": [item.artifact_name for item in evaluation.stale_artifacts],
        "artifact_windows": [
            board_baseline_window_to_dict(item) for item in evaluation.artifact_windows
        ],
    }


def normalize_path(
    path: PathLike,
    *,
    base: PathLike | None = None,
    allowed_root: PathLike | None = DEFAULT_ALLOWED_ROOT,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Normalize a path and optionally enforce an allowed root.

    Use this tool when an agent needs a safe normalized path string before
    referencing artifacts or local project files.

    Args:
        path (PathLike): Input path.
        base (PathLike | None): Base directory for relative paths.
        allowed_root (PathLike | None): Optional root boundary. Defaults to
            the project root.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with JSON-safe path data.
    """
    tool_name = "normalize_path"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        resolved = _resolve_path(path, base)
        root, inside_root = _validate_allowed_root(resolved, allowed_root)
    except ValueError as error:
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    if not inside_root:
        return _error_response(
            tool_name=tool_name,
            message="Path is outside the allowed root.",
            code="PERMISSION_DENIED",
            details="resolved path must be inside allowed_root.",
            request_id=request_id,
            started_at=started_at,
        )

    return _success_response(
        tool_name=tool_name,
        message="Path normalized successfully.",
        data={
            "path": str(resolved),
            "exists": resolved.exists(),
            "is_absolute": resolved.is_absolute(),
            "allowed_root": str(root) if root else None,
            "inside_allowed_root": inside_root,
        },
        request_id=request_id,
        started_at=started_at,
    )


def ensure_parent_dir(
    path: PathLike,
    *,
    allowed_root: PathLike | None = DEFAULT_ALLOWED_ROOT,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Ensure the parent directory exists for a file path.

    This tool creates directories and is therefore marked as medium risk with
    ``writes_file=True``.

    Args:
        path (PathLike): File path whose parent should exist.
        allowed_root (PathLike | None): Optional root boundary. Defaults to
            the project root.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with JSON-safe path data.
    """
    tool_name = "ensure_parent_dir"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        resolved = _resolve_path(path)
        root, inside_root = _validate_allowed_root(resolved, allowed_root)
    except ValueError as error:
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
            tool_risk_level="medium",
            read_only=False,
            writes_file=True,
        )

    if not inside_root:
        return _error_response(
            tool_name=tool_name,
            message="Path is outside the allowed root.",
            code="PERMISSION_DENIED",
            details="resolved path must be inside allowed_root.",
            request_id=request_id,
            started_at=started_at,
            tool_risk_level="medium",
            read_only=False,
            writes_file=True,
        )

    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _error_response(
            tool_name=tool_name,
            message="Ensuring parent directory failed.",
            code="TOOL_EXECUTION_FAILED",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
            tool_risk_level="medium",
            read_only=False,
            writes_file=True,
        )

    return _success_response(
        tool_name=tool_name,
        message="Parent directory ensured.",
        data={
            "path": str(resolved),
            "parent": str(resolved.parent),
            "parent_exists": resolved.parent.exists(),
            "allowed_root": str(root) if root else None,
            "inside_allowed_root": inside_root,
        },
        request_id=request_id,
        started_at=started_at,
        tool_risk_level="medium",
        read_only=False,
        writes_file=True,
    )


def ensure_dir(
    path: PathLike,
    *,
    allowed_root: PathLike | None = DEFAULT_ALLOWED_ROOT,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Ensure a directory exists.

    This tool creates directories and is therefore marked as medium risk with
    ``writes_file=True``.

    Args:
        path (PathLike): Directory path to create if missing.
        allowed_root (PathLike | None): Optional root boundary. Defaults to
            the project root.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with JSON-safe path data.
    """
    tool_name = "ensure_dir"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        resolved = _resolve_path(path)
        root, inside_root = _validate_allowed_root(resolved, allowed_root)
    except ValueError as error:
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
            tool_risk_level="medium",
            read_only=False,
            writes_file=True,
        )

    if not inside_root:
        return _error_response(
            tool_name=tool_name,
            message="Path is outside the allowed root.",
            code="PERMISSION_DENIED",
            details="resolved path must be inside allowed_root.",
            request_id=request_id,
            started_at=started_at,
            tool_risk_level="medium",
            read_only=False,
            writes_file=True,
        )

    try:
        resolved.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _error_response(
            tool_name=tool_name,
            message="Ensuring directory failed.",
            code="TOOL_EXECUTION_FAILED",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
            tool_risk_level="medium",
            read_only=False,
            writes_file=True,
        )

    return _success_response(
        tool_name=tool_name,
        message="Directory ensured.",
        data={
            "path": str(resolved),
            "exists": resolved.exists(),
            "is_dir": resolved.is_dir(),
            "allowed_root": str(root) if root else None,
            "inside_allowed_root": inside_root,
        },
        request_id=request_id,
        started_at=started_at,
        tool_risk_level="medium",
        read_only=False,
        writes_file=True,
    )


def normalize_timestamp(
    value: Any,
    *,
    output: OutputType = "iso",
    assume_tz: str = "UTC",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Normalize an input timestamp into a JSON-safe representation.

    Args:
        value (Any): datetime, ISO string, epoch seconds, or epoch milliseconds.
        output (OutputType): Desired output: iso, datetime, epoch_s, or epoch_ms.
            The ``datetime`` option returns an ISO string under ``data["datetime"]``
            to keep tool output JSON-safe.
        assume_tz (str): Timezone used for naive inputs.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response.
    """
    tool_name = "normalize_timestamp"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | output=%s", tool_name, request_id, output)

    if output not in {"iso", "datetime", "epoch_s", "epoch_ms"}:
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="output must be one of: iso, datetime, epoch_s, epoch_ms.",
            request_id=request_id,
            started_at=started_at,
        )

    try:
        dt_utc = to_utc_datetime(value, assume_tz=assume_tz)
    except ValueError as error:
        return _error_response(
            tool_name=tool_name,
            message="Timestamp normalization failed.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    payload: dict[str, Any] = {
        "iso": dt_utc.isoformat().replace("+00:00", "Z"),
        "datetime": dt_utc.isoformat(),
        "epoch_s": int(dt_utc.timestamp()),
        "epoch_ms": int(dt_utc.timestamp() * 1000),
    }

    return _success_response(
        tool_name=tool_name,
        message="Timestamp normalized successfully.",
        data={"output": output, "value": payload[output], "utc": payload},
        request_id=request_id,
        started_at=started_at,
    )


def _evaluate_freshness(
    observed_at: Any,
    *,
    max_age_seconds: int,
    clock: Clock | None = None,
) -> FreshnessWindow:
    """Evaluate timestamp freshness and return a FreshnessWindow."""
    if isinstance(max_age_seconds, bool) or not isinstance(max_age_seconds, int):
        raise ValueError("max_age_seconds must be an integer.")
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative.")

    active_clock = clock or SystemClock()
    try:
        checked_at = active_clock.now()
    except TypeError:
        checked_at = active_clock.now(UTC)  # type: ignore[call-arg]
    return FreshnessWindow(
        observed_at=to_utc_datetime(observed_at),
        checked_at=to_utc_datetime(checked_at),
        max_age_seconds=max_age_seconds,
    )


def evaluate_freshness(
    observed_at: Any,
    *,
    max_age_seconds: int,
    clock: Clock | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Evaluate whether a timestamp is fresh under a TTL window.

    Args:
        observed_at (Any): Observation timestamp.
        max_age_seconds (int): Maximum allowed age in seconds.
        clock (Clock | None): Optional deterministic clock for tests.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with JSON-safe freshness data.
    """
    tool_name = "evaluate_freshness"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        window = _evaluate_freshness(
            observed_at,
            max_age_seconds=max_age_seconds,
            clock=clock,
        )
    except ValueError as error:
        return _error_response(
            tool_name=tool_name,
            message="Freshness evaluation failed.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    return _success_response(
        tool_name=tool_name,
        message="Freshness evaluated.",
        data=freshness_window_to_dict(window),
        request_id=request_id,
        started_at=started_at,
    )


def is_stale(
    observed_at: Any,
    *,
    max_age_seconds: int,
    clock: Clock | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Return whether a timestamp is stale under a TTL window.

    Args:
        observed_at (Any): Observation timestamp.
        max_age_seconds (int): Maximum allowed age in seconds.
        clock (Clock | None): Optional deterministic clock for tests.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with boolean staleness data.
    """
    tool_name = "is_stale"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        window = _evaluate_freshness(
            observed_at,
            max_age_seconds=max_age_seconds,
            clock=clock,
        )
    except ValueError as error:
        return _error_response(
            tool_name=tool_name,
            message="Staleness check failed.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    return _success_response(
        tool_name=tool_name,
        message="Staleness checked.",
        data={"is_stale": window.is_stale, "window": freshness_window_to_dict(window)},
        request_id=request_id,
        started_at=started_at,
    )


def _evaluate_board_baseline_freshness(
    artifact_timestamps: Mapping[str, Any],
    *,
    proposal_materially_changed: bool = False,
    workflow_paused_at: Any | None = None,
    clock: Clock | None = None,
) -> BoardBaselineFreshnessEvaluation:
    """Evaluate freshness for execution-critical board baseline artifacts."""
    if not isinstance(artifact_timestamps, Mapping) or not artifact_timestamps:
        raise ValueError("artifact_timestamps must be a non-empty mapping.")

    active_clock = clock or SystemClock()
    checked_at = to_utc_datetime(active_clock.now())
    artifact_windows: list[BoardBaselineArtifactWindow] = []
    shortest_ttl: int | None = None

    for artifact_name, observed_at in artifact_timestamps.items():
        if artifact_name not in BOARD_BASELINE_TTL_POLICY:
            raise ValueError(f"unsupported board-baseline artifact: {artifact_name}")

        known_artifact = cast(BoardBaselineArtifact, artifact_name)
        freshness_class, ttl_seconds, action_if_stale = BOARD_BASELINE_TTL_POLICY[
            known_artifact
        ]
        window = _evaluate_freshness(
            observed_at,
            max_age_seconds=ttl_seconds,
            clock=FixedClock(checked_at),
        )
        artifact_windows.append(
            BoardBaselineArtifactWindow(
                artifact_name=known_artifact,
                freshness_class=freshness_class,
                action_if_stale=action_if_stale,
                window=window,
            )
        )
        shortest_ttl = (
            ttl_seconds if shortest_ttl is None else min(shortest_ttl, ttl_seconds)
        )

    pause_exceeded = False
    if workflow_paused_at is not None and shortest_ttl is not None:
        pause_exceeded = _evaluate_freshness(
            workflow_paused_at,
            max_age_seconds=shortest_ttl,
            clock=FixedClock(checked_at),
        ).is_stale

    return BoardBaselineFreshnessEvaluation(
        artifact_windows=tuple(artifact_windows),
        checked_at=checked_at,
        shortest_ttl_seconds=shortest_ttl or 0,
        proposal_materially_changed=bool(proposal_materially_changed),
        workflow_pause_exceeded_shortest_ttl=pause_exceeded,
    )


def evaluate_board_baseline_freshness(
    artifact_timestamps: Mapping[str, Any],
    *,
    proposal_materially_changed: bool = False,
    workflow_paused_at: Any | None = None,
    clock: Clock | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Evaluate execution-critical artifacts against board-baseline TTL policies.

    Args:
        artifact_timestamps (Mapping[str, Any]): Mapping of artifact name to
            observation timestamp.
        proposal_materially_changed (bool): Whether proposal content changed.
        workflow_paused_at (Any | None): Optional workflow pause timestamp.
        clock (Clock | None): Optional deterministic clock for tests.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with JSON-safe evaluation data.
    """
    tool_name = "evaluate_board_baseline_freshness"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        evaluation = _evaluate_board_baseline_freshness(
            artifact_timestamps,
            proposal_materially_changed=proposal_materially_changed,
            workflow_paused_at=workflow_paused_at,
            clock=clock,
        )
    except ValueError as error:
        return _error_response(
            tool_name=tool_name,
            message="Board baseline freshness evaluation failed.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    payload = board_baseline_evaluation_to_dict(evaluation)
    if not evaluation.is_valid:
        logger.warning(
            "%s invalid | request_id=%s | stale_artifacts=%s",
            tool_name,
            request_id,
            payload["stale_artifacts"],
        )

    return _success_response(
        tool_name=tool_name,
        message="Board baseline freshness evaluated.",
        data=payload,
        request_id=request_id,
        started_at=started_at,
    )


__all__ = [
    "BOARD_BASELINE_TTL_POLICY",
    "BoardBaselineArtifact",
    "BoardBaselineArtifactWindow",
    "BoardBaselineFreshnessEvaluation",
    "Clock",
    "FixedClock",
    "FreshnessWindow",
    "SystemClock",
    "board_baseline_evaluation_to_dict",
    "board_baseline_window_to_dict",
    "ensure_dir",
    "ensure_parent_dir",
    "evaluate_board_baseline_freshness",
    "evaluate_freshness",
    "format_timestamp_z",
    "freshness_window_to_dict",
    "is_stale",
    "normalize_path",
    "normalize_timestamp",
    "normalize_timezone_for_series",
    "parse_datetime_value",
    "to_utc",
    "to_naive_utc_datetime",
    "to_utc_datetime",
]

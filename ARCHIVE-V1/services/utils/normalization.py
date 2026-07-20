"""
normalization.py

Provides path, date/time, and timezone normalization tools for HaruQuant agents.

This file contains AI-callable tools for normalizing file paths, handling
timezone-aware datetimes, and evaluating data freshness (TTL).

Exported AI Tools:
    - normalize_path: Normalizes to pathlib.Path and optionally resolves relative to a base.
    - ensure_parent_dir: Ensures the parent directory exists for a given file path.
    - ensure_dir: Ensures a directory path exists.
    - parse_datetime: Parses various datetime inputs into timezone-aware datetimes.
    - to_utc: Normalizes a datetime to timezone-aware UTC.
    - to_naive_utc: Normalizes a datetime to UTC and removes timezone information.
    - format_timestamp_z: Formats datetime as ISO-8601 with trailing 'Z'.
    - normalize_timestamp: Normalizes an input timestamp to a desired format.
    - normalize_timezone_for_series: Normalizes pandas DatetimeIndex/Series timezone.
    - evaluate_freshness: Evaluates whether a timestamp is still fresh under a TTL window.
    - evaluate_board_baseline_freshness: Evaluates execution-critical artifacts against baselines.
    - is_stale: Returns True if an observed timestamp is older than its TTL window.

Internal Helpers:
    - _normalize_path: Internal logic for path normalization.
    - _ensure_parent_dir: Internal logic for parent directory creation.
    - _ensure_dir: Internal logic for directory creation.
    - _parse_datetime: Internal logic for datetime parsing.
    - _to_utc: Internal logic for UTC normalization.
    - _to_naive_utc: Internal logic for naive UTC normalization.
    - _format_timestamp_z: Internal logic for 'Z' formatting.
    - _normalize_timezone_for_series: Internal logic for pandas TZ normalization.
    - _evaluate_freshness: Internal logic for freshness evaluation.
    - _evaluate_board_baseline_freshness: Internal logic for aggregate freshness.
    - _is_stale: Internal logic for staleness check.
    - _resolve_tz: Resolves timezone names.
    - _is_epoch_milliseconds: Checks for epoch MS.

Classes:
    Clock (Protocol): Minimal clock protocol for time-sensitive tools.
    SystemClock: Clock implementation backed by the system wall clock.
    FixedClock: Deterministic clock for tests and replay-sensitive code.
    FreshnessWindow: Result of a freshness evaluation for a single timestamp.
    BoardBaselineArtifactWindow: Freshness evaluation for a board-baseline artifact.
    BoardBaselineFreshnessEvaluation: Aggregated freshness decision for critical inputs.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal, Protocol, Union
from zoneinfo import ZoneInfo

from app.services.utils.logger import logger
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

PathLike = Union[str, Path]
OutputType = Literal["iso", "datetime", "epoch_s", "epoch_ms"]
UTC = UTC
DEFAULT_TIMEZONE = "UTC"
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

# Tool Metadata Constants
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

# TTL policies for critical execution artifacts
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
    """
    Minimal clock protocol used by workflow and TTL-sensitive tools.

    This protocol allows for decoupling time-dependent logic from the system clock,
    enabling deterministic testing and point-in-time evaluation.
    """

    def now(self) -> datetime:
        """
        Return the current UTC timestamp.

        Returns:
            datetime: Timezone-aware UTC datetime representing the 'current' moment.
        """


class SystemClock:
    """
    Clock implementation backed by the system wall clock.

    This is the default implementation for production use, providing the
    actual current system time in UTC.
    """

    def now(self) -> datetime:
        """
        Return the current UTC timestamp from the system clock.

        The logic uses `datetime.now(timezone.utc)` to ensure a timezone-aware
        object is returned, avoiding ambiguities with local system time.

        Returns:
            datetime: Timezone-aware UTC datetime.
        """
        return datetime.now(UTC)


@dataclass(frozen=True)
class FixedClock:
    """
    Deterministic clock for tests and replay-sensitive code.

    Args:
        current (datetime): The fixed timestamp to return. This can be any
            datetime object; it will be normalized to UTC upon access.
    """

    current: datetime

    def now(self) -> datetime:
        """
        Return the configured timestamp normalized to UTC.

        Internal logic ensures the stored `current` timestamp is converted to
        a timezone-aware UTC datetime using `_to_utc`.

        Returns:
            datetime: Timezone-aware UTC datetime.
        """
        res = _to_utc(self.current)
        logger.info("Implemented retrieving fixed clock time")
        return res


@dataclass(frozen=True)
class FreshnessWindow:
    """
    A freshness result derived from an observed timestamp and a TTL.

    This class encapsulates the comparison logic between an observation time
    and a check time, determining if the elapsed duration exceeds a defined
    maximum age.

    Args:
        observed_at (datetime): The timestamp when the data was originally recorded.
        checked_at (datetime): The timestamp when the freshness check was performed.
        max_age_seconds (int): The maximum duration (in seconds) the data is considered fresh.
    """

    observed_at: datetime
    checked_at: datetime
    max_age_seconds: int

    @property
    def age_seconds(self) -> float:
        """
        Return age in seconds at the check time.

        Logic: Calculates the difference between `checked_at` and `observed_at`.
        Returns 0.0 if `observed_at` is in the future relative to `checked_at`.

        Returns:
            float: Number of seconds elapsed since observation.
        """
        res = max((self.checked_at - self.observed_at).total_seconds(), 0.0)
        logger.info("Implemented calculating freshness window age in seconds")
        return res

    @property
    def expires_at(self) -> datetime:
        """
        Return the timestamp at which the observed value expires.

        Logic: Adds `max_age_seconds` to the `observed_at` timestamp.

        Returns:
            datetime: Expiration timestamp.
        """
        res = self.observed_at + timedelta(seconds=self.max_age_seconds)
        logger.info("Implemented calculating freshness expiration timestamp")
        return res

    @property
    def is_fresh(self) -> bool:
        """
        Return True when the observed value is still inside its TTL.

        Logic: Checks if `age_seconds` is less than or equal to `max_age_seconds`.

        Returns:
            bool: True if fresh, False otherwise.
        """
        res = self.age_seconds <= float(self.max_age_seconds)
        logger.info("Implemented freshness evaluation check")
        return res

    @property
    def is_stale(self) -> bool:
        """
        Return True when the observed value is outside its TTL.

        Logic: The inverse of `is_fresh`.

        Returns:
            bool: True if stale, False otherwise.
        """
        res = not self.is_fresh
        logger.info("Implemented staleness evaluation check")
        return res


@dataclass(frozen=True)
class BoardBaselineArtifactWindow:
    """
    Freshness evaluation for one board-baseline artifact.

    This combines the high-level policy (freshness class and recovery action)
    with the low-level window calculation for a specific artifact.

    Args:
        artifact_name (BoardBaselineArtifact): Name of the artifact being evaluated.
        freshness_class (FreshnessClass): Category of freshness (HOT, WARM, etc.).
        action_if_stale (str): Human-readable instruction on what to do if stale.
        window (FreshnessWindow): The underlying freshness window calculation.
    """

    artifact_name: BoardBaselineArtifact
    freshness_class: FreshnessClass
    action_if_stale: str
    window: FreshnessWindow


@dataclass(frozen=True)
class BoardBaselineFreshnessEvaluation:
    """
    Aggregated board-baseline freshness decision for execution-critical inputs.

    This class provides a comprehensive view of the freshness state of multiple
    artifacts, flagging if any are stale or if external conditions (like material
    proposal changes) invalidate the current state.

    Args:
        artifact_windows (tuple): Windows for each artifact evaluated.
        checked_at (datetime): Time the aggregate evaluation was performed.
        shortest_ttl_seconds (int): The smallest TTL among all evaluated artifacts.
        proposal_materially_changed (bool): Flag indicating if the underlying proposal
            has changed since the last evaluation.
        workflow_pause_exceeded_shortest_ttl (bool): Flag indicating if a workflow
            pause duration has exceeded the tightest TTL in the group.
    """

    artifact_windows: tuple[BoardBaselineArtifactWindow, ...]
    checked_at: datetime
    shortest_ttl_seconds: int
    proposal_materially_changed: bool = False
    workflow_pause_exceeded_shortest_ttl: bool = False

    @property
    def stale_artifacts(self) -> tuple[BoardBaselineArtifactWindow, ...]:
        """
        Return artifact windows that are stale.

        Logic: Filters `artifact_windows` for those where `window.is_stale` is True.

        Returns:
            tuple: Collection of stale artifact windows.
        """
        res = tuple(
            window for window in self.artifact_windows if window.window.is_stale
        )
        logger.info("Implemented retrieving stale artifacts tuple")
        return res

    @property
    def is_valid(self) -> bool:
        """
        Return True when the aggregate freshness decision is valid.

        Logic: Evaluates to True only if no artifacts are stale, the proposal
        hasn't changed, and no workflow pause limits were exceeded.

        Returns:
            bool: Overall validity status.
        """
        res = (
            not self.stale_artifacts
            and not self.proposal_materially_changed
            and not self.workflow_pause_exceeded_shortest_ttl
        )
        logger.info("Implemented freshness aggregate validation check")
        return res


def _normalize_path(path: PathLike, base: PathLike | None = None) -> Path:
    """Internal helper for path normalization."""
    p = Path(path).expanduser()
    if base is not None:
        base_path = Path(base).expanduser().resolve()
        if not p.is_absolute():
            p = base_path / p
        result = p.resolve()
        if result != base_path and base_path not in result.parents:
            raise ValueError("path escapes the supplied base directory")
    else:
        result = p.resolve()
    logger.debug(f"Normalized path: {path} -> {result}")
    return result


def normalize_path(
    path: PathLike,
    base: PathLike | None = None,
    base_dir: PathLike | None = None,
    request_id: str | None = None,
) -> Any:
    """
    Normalize to pathlib.Path and optionally resolve relative to a base directory.

    Use this tool when an agent needs to ensure a file or directory path is
    correctly formatted and resolved, especially when dealing with relative
    paths or home directory shortcuts.

    Args:
        path (PathLike): The input path (string or Path object).
        base (PathLike, optional): The base directory for relative paths.
        base_dir (PathLike, optional): Alias for base.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status, message, data (Path),
        error, and metadata.
    """
    active_base = base_dir if base_dir is not None else base
    tool_name = "normalize_path"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    logger.info("{} called | request_id={} | path={}", tool_name, request_id, path)

    if not path:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning("{} failed validation | request_id={}", tool_name, request_id)
        dict_data = standard_tool_response(
            spec,
            "error",
            "Path is required.",
            error={"code": "INVALID_INPUT", "details": "path cannot be empty."},
            request_id=request_id,
            execution_ms=execution_ms,
        )
        from app.services.utils.errors import ValidationError

        raise ValidationError("path cannot be empty.", code="INVALID_INPUT")

    try:
        result = _normalize_path(path, active_base)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        dict_data = standard_tool_response(
            spec,
            "success",
            "Path normalized successfully.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
        return PathResponse(result, dict_data)
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        dict_data = standard_tool_response(
            spec,
            "error",
            "Path normalization failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )
        from app.services.utils.errors import SecurityError

        if "escapes the supplied base directory" in str(e):
            raise SecurityError(str(e))
        raise e


def _ensure_parent_dir(path: PathLike) -> Path:
    """Internal helper for ensuring parent directory exists."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured parent directory for: {p}")
    return p


def ensure_parent_dir(
    path: PathLike,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Ensure parent directory exists for a file path.

    Use this tool before writing a file to ensure the target directory structure
    is created.

    Args:
        path (PathLike): The target file path.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (Path).
    """
    tool_name = "ensure_parent_dir"
    spec = ToolStandardSpec(
        tool_name=tool_name,
        tool_category=TOOL_CATEGORY,
        read_only=False,
        writes_file=True,
    )
    started_at = time.perf_counter()

    logger.info("{} called | request_id={} | path={}", tool_name, request_id, path)

    if not path:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Path is required.",
            error={"code": "INVALID_INPUT", "details": "path cannot be empty."},
            request_id=request_id,
            execution_ms=execution_ms,
        )

    try:
        result = _ensure_parent_dir(path)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "success",
            "Parent directory ensured.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "error",
            "Ensuring parent directory failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _ensure_dir(path: PathLike) -> Path:
    """Internal helper for ensuring directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {p}")
    return p


def ensure_dir(
    path: PathLike,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Ensure directory path exists.

    Use this tool to create a directory and any necessary parents recursively.

    Args:
        path (PathLike): The target directory path.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (Path).
    """
    tool_name = "ensure_dir"
    spec = ToolStandardSpec(
        tool_name=tool_name,
        tool_category=TOOL_CATEGORY,
        read_only=False,
        writes_file=True,
    )
    started_at = time.perf_counter()

    logger.info("{} called | request_id={} | path={}", tool_name, request_id, path)

    if not path:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Path is required.",
            error={"code": "INVALID_INPUT", "details": "path cannot be empty."},
            request_id=request_id,
            execution_ms=execution_ms,
        )

    try:
        result = _ensure_dir(path)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "success",
            "Directory ensured.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "error",
            "Ensuring directory failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _resolve_tz(tz_name: str) -> ZoneInfo:
    """Resolve a timezone name to a ZoneInfo instance."""
    try:
        return ZoneInfo(tz_name)
    except Exception as exc:
        raise ValueError(f"Invalid timezone: {tz_name}") from exc


def _is_epoch_milliseconds(value: float) -> bool:
    """Return True when a numeric timestamp looks like epoch milliseconds."""
    return abs(float(value)) >= 1_000_000_000_000


def _parse_datetime(value: Any, assume_tz: str = "UTC") -> datetime:
    """Internal helper for datetime parsing."""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        seconds = (
            float(value) / 1000.0 if _is_epoch_milliseconds(value) else float(value)
        )
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("Datetime string cannot be empty")
        text = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"Unsupported datetime format: {value}") from exc
    else:
        raise ValueError(f"Unsupported datetime value type: {type(value).__name__}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_resolve_tz(assume_tz))

    return dt


class DatetimeResponse(datetime):
    """Timezone-aware datetime representing a standard tool response value."""

    _dict_data: dict[str, Any]

    def __new__(cls, dt: datetime, dict_data: dict[str, Any]) -> DatetimeResponse:
        """Create a new DatetimeResponse instance.

        Args:
            dt: The datetime object.
            dict_data: Standard tool response envelope dictionary.

        Returns:
            A new DatetimeResponse instance.
        """
        self = datetime.__new__(
            cls,
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
            fold=dt.fold,
        )
        self._dict_data = dict_data
        logger.info("Implemented DatetimeResponse instantiation")
        return self

    def __getitem__(self, key: str) -> Any:
        """Access standard tool response fields using dictionary syntax."""
        logger.info("Implemented DatetimeResponse field access")
        return self._dict_data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a standard tool response field with a default value.

        Args:
            key: Field name to retrieve.
            default: Value to return if key is not found.

        Returns:
            Field value or default.
        """
        logger.debug("Implemented DatetimeResponse get method")
        return self._dict_data.get(key, default)


class StringResponse(str):
    """String representing a standard tool response value."""

    _dict_data: dict[str, Any]

    def __new__(cls, val: str, dict_data: dict[str, Any]) -> StringResponse:
        """Create a new StringResponse instance.

        Args:
            val: The string value.
            dict_data: Standard tool response envelope dictionary.

        Returns:
            A new StringResponse instance.
        """
        self = str.__new__(cls, val)
        self._dict_data = dict_data
        logger.info("Implemented StringResponse instantiation")
        return self

    def __getitem__(self, key: str) -> Any:  # type: ignore[override]
        """Access standard tool response fields using dictionary syntax."""
        logger.info("Implemented StringResponse field access")
        return self._dict_data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a standard tool response field with a default value.

        Args:
            key: Field name to retrieve.
            default: Value to return if key is not found.

        Returns:
            Field value or default.
        """
        logger.info("Implemented StringResponse get method")
        return self._dict_data.get(key, default)


class IntResponse(int):
    """Integer representing a standard tool response value."""

    _dict_data: dict[str, Any]

    def __new__(cls, val: int, dict_data: dict[str, Any]) -> IntResponse:
        """Create a new IntResponse instance.

        Args:
            val: The integer value.
            dict_data: Standard tool response envelope dictionary.

        Returns:
            A new IntResponse instance.
        """
        self = int.__new__(cls, val)
        self._dict_data = dict_data
        logger.info("Implemented IntResponse instantiation")
        return self

    def __getitem__(self, key: str) -> Any:
        """Access standard tool response fields using dictionary syntax."""
        logger.info("Implemented IntResponse field access")
        return self._dict_data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a standard tool response field with a default value.

        Args:
            key: Field name to retrieve.
            default: Value to return if key is not found.

        Returns:
            Field value or default.
        """
        logger.info("Implemented IntResponse get method")
        return self._dict_data.get(key, default)


class PathResponse(Path):
    """Path representing a standard tool response value."""

    _dict_data: dict[str, Any]

    def __new__(cls, path: PathLike, dict_data: dict[str, Any]) -> PathResponse:
        """Create a new PathResponse instance.

        Args:
            path: The file/directory path.
            dict_data: Standard tool response envelope dictionary.

        Returns:
            A new PathResponse instance.
        """
        self = super().__new__(cls, path)
        self._dict_data = dict_data
        logger.info("Implemented PathResponse instantiation")
        return self

    def __init__(self, path: PathLike, dict_data: dict[str, Any]) -> None:
        """Initialize a PathResponse instance.

        Args:
            path: The file/directory path.
            dict_data: Standard tool response envelope dictionary.
        """
        super().__init__(path)
        logger.info("Implemented PathResponse initialization")

    def __getitem__(self, key: str) -> Any:
        """Access standard tool response fields using dictionary syntax."""
        logger.info("Implemented PathResponse field access")
        return self._dict_data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a standard tool response field with a default value.

        Args:
            key: Field name to retrieve.
            default: Value to return if key is not found.

        Returns:
            Field value or default.
        """
        logger.info("Implemented PathResponse get method")
        return self._dict_data.get(key, default)


def parse_datetime(
    value: Any,
    assume_tz: str = "UTC",
    assumed_timezone: str | None = None,
    request_id: str | None = None,
) -> Any:
    """Parse datetime input into timezone-aware datetime."""
    from datetime import date

    from app.services.utils.errors import ValidationError

    tool_name = "parse_datetime"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    if value is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        raise ValidationError("value cannot be None.", code="INVALID_INPUT")

    try:
        active_tz = assumed_timezone if assumed_timezone is not None else assume_tz
        # Perform parsing
        if isinstance(value, (int, float)):
            if value > 2e11:  # ms
                dt = datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
            else:
                dt = datetime.fromtimestamp(value, tz=timezone.utc)
        elif isinstance(value, date) and not isinstance(value, datetime):
            dt = datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
        elif isinstance(value, datetime):
            if value.tzinfo is None:
                dt = value.replace(tzinfo=_resolve_tz(active_tz)).astimezone(
                    timezone.utc
                )
            else:
                dt = value.astimezone(timezone.utc)
        elif isinstance(value, str):
            text = value.strip()
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(text)
            except ValueError as exc:
                raise ValidationError(
                    f"Invalid ISO-8601 datetime: {value}", code="INVALID_INPUT"
                ) from exc
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_resolve_tz(active_tz))
        else:
            raise ValidationError(
                f"Unsupported datetime type: {type(value).__name__}",
                code="INVALID_INPUT",
            )

        # Standardize timezone to UTC
        dt = dt.astimezone(timezone.utc)

        # Build standard tool response
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        dict_data = standard_tool_response(
            spec,
            "success",
            "Datetime parsed successfully.",
            data=dt,
            request_id=request_id,
            execution_ms=execution_ms,
        )
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return DatetimeResponse(dt, dict_data)

    except Exception as exc:
        if not isinstance(exc, ValidationError):
            msg = str(exc)
            if "Invalid timezone" in msg:
                msg = f"unknown timezone: {active_tz}"
            exc = ValidationError(msg, code="INVALID_INPUT")
        raise exc


def _to_utc(dt: datetime | Any, assume_tz: str = "UTC") -> datetime:
    """Internal helper for UTC normalization."""
    parsed = _parse_datetime(dt, assume_tz=assume_tz)
    return parsed.astimezone(timezone.utc)


def to_utc(
    dt: datetime | Any,
    assume_tz: str = "UTC",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Normalize datetime to timezone-aware UTC.

    Use this tool to ensure a timestamp is converted to UTC.

    Args:
        dt (datetime | Any): Input datetime.
        assume_tz (str): Default timezone for naive inputs.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (datetime).
    """
    tool_name = "to_utc"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    try:
        result = _to_utc(dt, assume_tz)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "success",
            "Normalized to UTC.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "error",
            "UTC normalization failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _to_naive_utc(dt: datetime | Any, assume_tz: str = "UTC") -> datetime:
    """Internal helper for naive UTC normalization."""
    res = _to_utc(dt, assume_tz=assume_tz).replace(tzinfo=None)
    logger.debug("Implemented internal naive UTC conversion")
    return res


def to_naive_utc(
    dt: datetime | Any,
    assume_tz: str = "UTC",
    request_id: str | None = None,
) -> Any:
    """Normalize datetime to UTC and drop tzinfo."""
    tool_name = "to_naive_utc"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    try:
        result = _to_naive_utc(dt, assume_tz)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        dict_data = standard_tool_response(
            spec,
            "success",
            "Normalized to naive UTC.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return DatetimeResponse(result, dict_data)
    except Exception as exc:
        from app.services.utils.errors import ValidationError

        if not isinstance(exc, ValidationError):
            exc = ValidationError(str(exc), code="INVALID_INPUT")
        raise exc


def _format_timestamp_z(value: datetime | None, assume_tz: str = "UTC") -> str | None:
    """Internal helper for 'Z' formatting."""
    if value is None:
        return None
    res = _to_utc(value, assume_tz=assume_tz).isoformat().replace("+00:00", "Z")
    logger.debug("Implemented internal timestamp formatting")
    return res


def format_utc_timestamp(value: Any, assume_tz: str = "UTC") -> str | None:
    """Format a timestamp as UTC ISO-8601 string with a trailing Z."""
    res = _format_timestamp_z(value, assume_tz)
    logger.info("Implemented UTC timestamp formatting wrapper")
    return res


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    res = datetime.now(timezone.utc)
    logger.info("Implemented current UTC time retrieval")
    return res


def format_timestamp_z(
    value: datetime | Any | None,
    assume_tz: str = "UTC",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Format a timestamp as UTC ISO-8601 with a trailing Z.

    Use this tool to get a string representation of a timestamp in the
    standardized "YYYY-MM-DDTHH:MM:SS.mmmmmmZ" format.

    Args:
        value (datetime | Any | None): Input timestamp.
        assume_tz (str): Default timezone for naive inputs.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (str or None).
    """
    tool_name = "format_timestamp_z"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    try:
        result = _format_timestamp_z(value, assume_tz)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "success",
            "Timestamp formatted.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "error",
            "Formatting failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def normalize_timestamp(
    value: Any,
    *,
    output: OutputType = "datetime",
    assume_tz: str = "UTC",
    assumed_timezone: str | None = None,
    request_id: str | None = None,
) -> Any:
    """Normalize timestamp to desired format."""
    tool_name = "normalize_timestamp"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    active_tz = assumed_timezone if assumed_timezone is not None else assume_tz
    try:
        dt = parse_datetime(value, assume_tz=active_tz)

        # Format the output value
        if output == "iso":
            result_val: Any = format_utc_timestamp(dt)
        elif output == "epoch_s":
            result_val = int(dt.timestamp())
        elif output == "epoch_ms":
            result_val = int(dt.timestamp() * 1000)
        else:
            result_val = dt

        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        dict_data = standard_tool_response(
            spec,
            "success",
            "Timestamp normalized.",
            data=result_val,
            request_id=request_id,
            execution_ms=execution_ms,
        )
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        if isinstance(result_val, datetime):
            return DatetimeResponse(result_val, dict_data)
        if isinstance(result_val, str):
            return StringResponse(result_val, dict_data)
        if isinstance(result_val, int):
            return IntResponse(result_val, dict_data)
        return result_val

    except Exception as exc:
        from app.services.utils.errors import ValidationError

        if not isinstance(exc, ValidationError):
            exc = ValidationError(str(exc), code="INVALID_INPUT")
        raise exc


def _normalize_timezone_for_series(
    series_or_index: Any,
    *,
    target_tz: str = "UTC",
    make_naive: bool = False,
) -> Any:
    """Internal helper for pandas TZ normalization."""
    import pandas as pd

    tz = _resolve_tz(target_tz)

    if isinstance(series_or_index, pd.DatetimeIndex):
        out = series_or_index
        if out.tz is None:
            out = out.tz_localize("UTC")
        out = out.tz_convert(tz)
        result = out.tz_localize(None) if make_naive else out
        logger.debug(f"Normalized DatetimeIndex to {target_tz}")
        return result

    if isinstance(series_or_index, pd.Series):
        if not isinstance(series_or_index.dtype, pd.DatetimeTZDtype):
            out = pd.to_datetime(series_or_index, errors="raise")
            if out.dt.tz is None:
                out = out.dt.tz_localize("UTC")
        else:
            out = series_or_index
        out = out.dt.tz_convert(tz)
        result = out.dt.tz_localize(None) if make_naive else out
        logger.debug(f"Normalized Series to {target_tz}")
        return result

    raise ValueError(
        "normalize_timezone_for_series expects pandas Series or DatetimeIndex"
    )


def normalize_timezone_for_series(
    series_or_index: Any,
    *,
    target_tz: str = "UTC",
    make_naive: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Normalize pandas DatetimeIndex/Series timezone.

    Use this tool when you need to convert a pandas time series or index to a
    specific timezone.

    Args:
        series_or_index (Any): pandas Series or DatetimeIndex.
        target_tz (str): Target timezone name. Defaults to "UTC".
        make_naive (bool): Whether to drop tzinfo at the end. Defaults to False.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (pandas object).
    """
    tool_name = "normalize_timezone_for_series"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    logger.info(
        "{} called | request_id={} | target_tz={}", tool_name, request_id, target_tz
    )

    try:
        result = _normalize_timezone_for_series(
            series_or_index, target_tz=target_tz, make_naive=make_naive
        )
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "success",
            "Timezone normalized.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "error",
            "Timezone normalization failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _evaluate_freshness(
    observed_at: Any,
    *,
    max_age_seconds: int,
    clock: Clock | None = None,
) -> FreshnessWindow:
    """Internal helper for freshness evaluation."""
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")

    active_clock = clock or SystemClock()
    result = FreshnessWindow(
        observed_at=_to_utc(observed_at),
        checked_at=_to_utc(active_clock.now()),
        max_age_seconds=int(max_age_seconds),
    )
    logger.debug(
        f"Evaluated freshness: {result.is_fresh} (age={result.age_seconds}s, max={max_age_seconds}s)"
    )
    return result


def evaluate_freshness(
    observed_at: Any,
    *,
    max_age_seconds: int,
    clock: Clock | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Evaluate whether a timestamp is still fresh under a TTL window.

    Use this tool to check if data is too old based on its observation time
    and a defined TTL (Time-To-Live).

    Args:
        observed_at (Any): The timestamp to evaluate.
        max_age_seconds (int): Maximum allowed age in seconds.
        clock (Clock, optional): Custom clock for evaluation.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (FreshnessWindow).
    """
    tool_name = "evaluate_freshness"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    logger.info(
        "{} called | request_id={} | max_age={}", tool_name, request_id, max_age_seconds
    )

    try:
        result = _evaluate_freshness(
            observed_at, max_age_seconds=max_age_seconds, clock=clock
        )
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "success",
            "Freshness evaluated.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "error",
            "Freshness evaluation failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _evaluate_board_baseline_freshness(
    artifact_timestamps: Mapping[BoardBaselineArtifact, Any],
    *,
    proposal_materially_changed: bool = False,
    workflow_paused_at: Any | None = None,
    clock: Clock | None = None,
) -> BoardBaselineFreshnessEvaluation:
    """Internal helper for aggregate freshness evaluation."""
    if not artifact_timestamps:
        raise ValueError("artifact_timestamps must not be empty")

    active_clock = clock or SystemClock()
    checked_at = _to_utc(active_clock.now())
    artifact_windows: list[BoardBaselineArtifactWindow] = []
    shortest_ttl_seconds: int | None = None

    for artifact_name, observed_at in artifact_timestamps.items():
        if artifact_name not in BOARD_BASELINE_TTL_POLICY:
            raise ValueError(f"unsupported board-baseline artifact: {artifact_name}")

        freshness_class, max_age_seconds, action_if_stale = BOARD_BASELINE_TTL_POLICY[
            artifact_name
        ]
        artifact_windows.append(
            BoardBaselineArtifactWindow(
                artifact_name=artifact_name,
                freshness_class=freshness_class,
                action_if_stale=action_if_stale,
                window=_evaluate_freshness(
                    observed_at,
                    max_age_seconds=max_age_seconds,
                    clock=FixedClock(checked_at),
                ),
            )
        )
        shortest_ttl_seconds = (
            max_age_seconds
            if shortest_ttl_seconds is None
            else min(shortest_ttl_seconds, max_age_seconds)
        )

    workflow_pause_exceeded_shortest_ttl = False
    if workflow_paused_at is not None and shortest_ttl_seconds is not None:
        workflow_pause_exceeded_shortest_ttl = _is_stale(
            workflow_paused_at,
            max_age_seconds=shortest_ttl_seconds,
            clock=FixedClock(checked_at),
        )

    result = BoardBaselineFreshnessEvaluation(
        artifact_windows=tuple(artifact_windows),
        checked_at=checked_at,
        shortest_ttl_seconds=shortest_ttl_seconds or 0,
        proposal_materially_changed=proposal_materially_changed,
        workflow_pause_exceeded_shortest_ttl=workflow_pause_exceeded_shortest_ttl,
    )

    if not result.is_valid:
        logger.warning(
            f"Board baseline freshness check failed. Stale artifacts: {[w.artifact_name for w in result.stale_artifacts]}"
        )
    else:
        logger.info("Board baseline freshness check passed.")

    return result


def evaluate_board_baseline_freshness(
    artifact_timestamps: Mapping[BoardBaselineArtifact, Any],
    *,
    proposal_materially_changed: bool = False,
    workflow_paused_at: Any | None = None,
    clock: Clock | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Evaluate execution-critical artifacts against the board TTL baselines.

    Use this tool to perform a comprehensive freshness check on multiple
    execution artifacts at once.

    Args:
        artifact_timestamps (Mapping): Map of artifact names to timestamps.
        proposal_materially_changed (bool): External change flag from the workflow.
        workflow_paused_at (Any, optional): Workflow pause timestamp.
        clock (Clock, optional): Custom clock for evaluation.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (BoardBaselineFreshnessEvaluation).
    """
    tool_name = "evaluate_board_baseline_freshness"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    try:
        result = _evaluate_board_baseline_freshness(
            artifact_timestamps,
            proposal_materially_changed=proposal_materially_changed,
            workflow_paused_at=workflow_paused_at,
            clock=clock,
        )
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "success",
            "Board baseline freshness evaluated.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "error",
            "Board baseline evaluation failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _is_stale(
    observed_at: Any,
    *,
    max_age_seconds: int,
    clock: Clock | None = None,
) -> bool:
    """Internal helper for staleness check."""
    res = _evaluate_freshness(
        observed_at,
        max_age_seconds=max_age_seconds,
        clock=clock,
    ).is_stale
    logger.debug("Implemented internal staleness check")
    return res


def is_stale(
    observed_at: Any,
    *,
    max_age_seconds: int,
    now: Any = None,
    clock: Clock | None = None,
    request_id: str | None = None,
) -> bool:
    """Return True when the observed timestamp is older than TTL window."""
    from app.services.utils.errors import ValidationError

    if max_age_seconds < 0:
        raise ValidationError("max_age_seconds must not be negative.")
    obs = _to_utc(observed_at)
    if now is not None:
        ref_now = _to_utc(now)
    elif clock is not None:
        ref_now = clock.now()
    else:
        from datetime import datetime as dt_class

        ref_now = dt_class.now(timezone.utc)
    res = (ref_now - obs).total_seconds() > max_age_seconds
    logger.info("Implemented staleness check wrapper")
    return res


def normalize_timestamp_sequence(
    sequence: Iterable[Any],
) -> list[datetime]:
    """Normalize a sequence of timestamps to UTC datetime objects."""
    res = [_to_utc(item) for item in sequence]
    logger.info("Implemented sequence timestamp normalization")
    return res


def validate_timestamp_sequence(
    sequence: Iterable[Any],
    *,
    allow_duplicates: bool = False,
) -> list[dict[str, Any]]:
    """Validate sequence of timestamps is monotonic and unique."""
    issues = []
    parsed_sequence: list[datetime | None] = []

    for i, item in enumerate(sequence):
        try:
            parsed = _parse_datetime(item)
            parsed_utc = parsed.astimezone(timezone.utc)
            parsed_sequence.append(parsed_utc)
        except Exception:
            parsed_sequence.append(None)
            issues.append(
                {
                    "code": "INVALID_TIMESTAMP",
                    "index": i,
                    "message": f"Invalid timestamp at index {i}: {item}",
                }
            )
            continue

        # Find the last valid parsed timestamp
        last_valid = None
        for prev in reversed(parsed_sequence[:-1]):
            if prev is not None:
                last_valid = prev
                break

        if last_valid is not None:
            if parsed_utc == last_valid:
                if not allow_duplicates:
                    issues.append(
                        {
                            "code": "DUPLICATE_TIMESTAMP",
                            "index": i,
                            "message": f"Duplicate timestamp at index {i}: {item}",
                        }
                    )
            elif parsed_utc < last_valid:
                issues.append(
                    {
                        "code": "NON_MONOTONIC_TIMESTAMP",
                        "index": i,
                        "message": f"Non-monotonic timestamp at index {i}: {item}",
                    }
                )

    logger.info("Implemented sequence timestamp validation")
    return issues


def normalize_timestamp_column(
    rows: Iterable[Mapping[str, Any] | Any],
    column: str,
) -> list[dict[str, Any]]:
    """Normalize a timestamp column across a sequence of dict rows."""
    from app.services.utils.errors import ValidationError

    if not column or not isinstance(column, str):
        raise ValidationError("column must be a non-empty string.")

    result = []
    for i, row in enumerate(rows):
        if not isinstance(row, Mapping) or column not in row:
            raise ValidationError(f"Row {i} is missing timestamp column: {column}")
        val = row[column]
        try:
            parsed = _to_utc(val)
        except Exception as exc:
            raise ValidationError(
                f"Row {i} value for column {column} is not a valid datetime-like: {val}"
            ) from exc
        new_row = dict(row)
        new_row[column] = parsed
        result.append(new_row)
    logger.info("Implemented row timestamp column normalization")
    return result


def check_clock_drift(
    observed_at: Any,
    *,
    now: Any = None,
    max_drift_seconds: float = 30.0,
) -> dict[str, Any]:
    """Check if drift between observed_at and now exceeds limit."""
    from app.services.utils.errors import ValidationError

    if max_drift_seconds < 0:
        raise ValidationError("max_drift_seconds must not be negative.")

    observed_utc = _to_utc(observed_at)

    if now is None:
        from datetime import datetime as dt_class

        now_utc = dt_class.now(timezone.utc)
    else:
        now_utc = _to_utc(now)

    drift_seconds = abs((observed_utc - now_utc).total_seconds())
    drift_detected = drift_seconds > max_drift_seconds

    res = {
        "drift_detected": drift_detected,
        "drift_seconds": drift_seconds,
        "max_drift_seconds": float(max_drift_seconds),
        "checked_at": format_utc_timestamp(now_utc),
    }
    logger.info("Implemented check clock drift")
    return res


def to_utc_datetime(dt: Any, assume_tz: str = "UTC") -> datetime:
    """Normalize datetime to timezone-aware UTC datetime directly."""
    res = _to_utc(dt, assume_tz=assume_tz)
    logger.info("Implemented converting to UTC datetime")
    return res

"""Donor timeframe calculations and explicitly located custom timeframe lists.

Description:
    Owns TimeframeManager conversions, hashes, names, registry and comparator
    semantics. Keeps strict donor parsing distinct from retained Python aliases
    and the positive-duration guard applied by bar resampling consumers.
    TimeframeManager.java owns conversion/registry methods; TimeframesComparator
    owns ordering and its distinct seconds utility. TimeBar/Fx/FuturesIntradayBar
    own chart_period/can_compute_chart_from metadata rules. DomainError replaces
    Java TradingException; explicit paths replace singleton settings lookup.
    Atomic UTF-8 registry replacement is a host safety adaptation. No import-time
    file writes or second enum are introduced. Evidence is in test_timeframes.py.
Purpose:
    FEAT-DATA-TIMEFRAMES: One source of timeframe metadata and calculations.
Key Capabilities:
    - FR-data-timeframe-conversion: DEBUG records donor conversions and alias
      resolution; Java fixtures verify values, overflow and exceptions.
    - FR-data-timeframe-registry: INFO records registry load/add operations;
      isolated-file tests verify persistence and failed-write behavior.
    - FR-data-timeframe-ordering: DEBUG records comparator keys and legacy
      translations; tests verify ordering and sentinel behavior.
Python API Usage:
    timeframe_to_seconds("H7")  # 25200
    TimeframeManager(custom_timeframes_path).add_timeframe("H7")
CLI Usage:
    uv run pytest tests/core/data/test_timeframes.py --no-cov
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from app.core.enums import Timeframe
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError

logger = get_logger(__name__)
_INT_MAX = (1 << 31) - 1
_JAVA_CHAR_MAX = (1 << 16) - 1
_JAVA_TRIM = "".join(chr(code) for code in range(33))
_UNITS = {"S": 1000, "M": 60000, "H": 3600000, "D": 86400000}
_SPECIAL_MILLIS = {"TICK": 0, "Intraday": 0, "Weekly": 604800000, "Monthly": 2419200000}
_SPECIAL_HASHES = {
    "TICK": 0,
    "Intraday": -10,
    "Weekly": 604800700,
    "Monthly": 2419200800,
}
_DEFAULTS = ("TICK", "M1", "M5", "M15", "M30", "H1", "H4", "D1", "Weekly", "Monthly")
_PREDEFINED = (
    "TICK",
    "M1",
    "M3",
    "M5",
    "M15",
    "M30",
    "H1",
    "H2",
    "H3",
    "H4",
    "H6",
    "H8",
    "H12",
    "D1",
    "Weekly",
    "Monthly",
)
_LEGACY = {
    0: "TICK",
    1: "M1",
    5: "M5",
    14: "M14",
    15: "M15",
    30: "M30",
    53: "M53",
    60: "H1",
    120: "H2",
    240: "H4",
    1440: "D1",
    10080: "Weekly",
    43200: "Monthly",
    -2: "unknown",
    -10: "Intraday",
}


def _int32(value: int) -> int:
    """Apply the donor's signed integer arithmetic at overflow boundaries."""
    return (value + (1 << 31)) % (1 << 32) - (1 << 31)


def _count(value: str) -> int:
    """Parse the donor's signed, untrimmed Java integer count syntax."""
    if not re.fullmatch(r"[+-]?\d+", value) or any(
        ord(char) > _JAVA_CHAR_MAX for char in value
    ):
        raise ValueError("Invalid Java integer")
    result = int(value)
    if not -(1 << 31) <= result <= _INT_MAX:
        raise ValueError("Java integer overflow")
    return result


def _parts(timeframe: str) -> tuple[str, int]:
    """Validate a donor unit/count pair without adding host aliases."""
    try:
        count = _count(timeframe[1:])
    except (ValueError, TypeError) as error:
        logger.debug("FR-data-timeframe-conversion: invalid donor timeframe")
        raise DomainError(
            code="INVALID_TIMEFRAME", message="Invalid donor timeframe format"
        ) from error
    if timeframe[:1] not in _UNITS:
        raise DomainError(code="INVALID_TIMEFRAME", message="Unknown timeframe unit")
    return timeframe[0], count


def get_millis(timeframe: str) -> int:
    """Match TimeframeManager.getMillis, including seconds int overflow."""
    logger.debug("FR-data-timeframe-conversion: get milliseconds")
    if timeframe in _SPECIAL_MILLIS:
        return _SPECIAL_MILLIS[timeframe]
    unit, count = _parts(timeframe)
    result = count * _UNITS[unit]
    return _int32(result) if unit == "S" else result


def get_tf_hash(timeframe: str) -> int:
    """Match donor timeframe identity; this is not a chart or string hash."""
    logger.debug("FR-data-timeframe-conversion: get timeframe hash")
    if timeframe in _SPECIAL_HASHES:
        return _SPECIAL_HASHES[timeframe]
    unit, count = _parts(timeframe)
    result = count * _UNITS[unit] + {"S": 300, "M": 400, "H": 500, "D": 600}[unit]
    return _int32(result) if unit == "S" else result


def get_tf_name(milliseconds: int) -> str:
    """Match donor duration naming thresholds (not an inverse hash decoder)."""
    logger.debug("FR-data-timeframe-conversion: get timeframe name")
    if milliseconds < 0:
        return "Intraday"
    if milliseconds == 0:
        return "TICK"
    if milliseconds >= _SPECIAL_MILLIS["Weekly"]:
        return "Weekly" if milliseconds < _SPECIAL_MILLIS["Monthly"] else "Monthly"
    unit = "S" if milliseconds < _UNITS["M"] else "M"
    if milliseconds >= _UNITS["H"]:
        unit = (
            "M"
            if milliseconds % _UNITS["H"] and not milliseconds % _UNITS["M"]
            else "H"
        )
    if milliseconds >= _UNITS["D"]:
        unit = "D"
    return f"{unit}{milliseconds // _UNITS[unit]}"


def normalize_timeframe(timeframe: str | Timeframe) -> str:
    """Resolve host/broker aliases at one boundary, preserving donor unit text."""
    name = str(timeframe).strip().upper()
    special = {
        "TICKS": "TICK",
        "INTRADAY": "Intraday",
        "CURRENT": "Intraday",
        "WEEKLY": "Weekly",
        "MONTHLY": "Monthly",
        "W1": "Weekly",
        "MN1": "Monthly",
    }
    try:
        name = Timeframe.from_string(name).value
    except ValueError:
        logger.debug("FR-data-timeframe-conversion: resolving non-enum timeframe")
    logger.debug("FR-data-timeframe-conversion: resolved host aliases")
    return special.get(name, name)


def timeframe_to_seconds(timeframe: str | Timeframe) -> int:
    """Resolve retained Python aliases, then use the donor duration owner."""
    milliseconds = get_millis(normalize_timeframe(timeframe))
    # Java arithmetic permits negative counts; consumers decide resampling safety.
    return -(abs(milliseconds) // 1000) if milliseconds < 0 else milliseconds // 1000


def minute_timeframe(count: int) -> str:
    """Match TimeframeManager.M(int) without adding a second enum."""
    logger.debug("FR-data-timeframe-conversion: formatting minute timeframe")
    if not -(1 << 31) <= count <= _INT_MAX:
        raise ValueError("Minute count exceeds a Java integer")
    return f"M{count}"


def is_timeframe_less_than(first: str, second: str) -> bool:
    """Match TimeframeManager.isTimeFrameLessThen using donor milliseconds."""
    return get_millis(first) < get_millis(second)


def chart_period(timeframe: str | Timeframe) -> tuple[int, int, bool]:
    """Map TimeBar period/basePeriodInMs and Intraday's non-TimeBar identity.

    TimeBar.getPeriodInMS returns its base unit, not its multiplied duration.
    TICK/Weekly/Monthly return before setting that unit, leaving it zero.
    Seconds periods use long multiplication here, unlike getMillis' int overflow.
    This is chart metadata eligibility only; aggregation remains owned by DataIO.
    """
    name = normalize_timeframe(timeframe)
    logger.debug("FR-data-timeframe-conversion: resolving chart bar period")
    if name in _SPECIAL_MILLIS:
        return _SPECIAL_MILLIS[name] // 1000, 0, name == "Intraday"
    unit, count = _parts(name)
    return count * (_UNITS[unit] // 1000), _UNITS[unit], False


def can_compute_chart_from(target: str | Timeframe, source: str | Timeframe) -> bool:
    """Match TimeBar/IntradayBar.checkCanBeComputedFrom's exact eligibility."""
    period, _, intraday = chart_period(target)
    if intraday or normalize_timeframe(target) == normalize_timeframe(source):
        return True
    source_period, _, source_intraday = chart_period(source)
    if source_period == 0 or source_intraday:
        return True
    remainder = abs(period) % abs(source_period) * (-1 if period < 0 else 1)
    day_remainder = abs(period) % 86400 * (-1 if period < 0 else 1)
    return not (period < source_period or (remainder > 0 and day_remainder > 0))


def timeframe_sort_key(timeframe: str) -> int:
    """Match TimeframesComparator.compare, including its signed-int error key."""
    logger.debug("FR-data-timeframe-ordering: computing sort key")
    try:
        return get_tf_hash(timeframe)
    except DomainError:
        return _INT_MAX


def comparator_seconds_count(timeframe: str | None) -> int:
    """Match the donor comparator's distinct permissive seconds utility."""
    logger.debug("FR-data-timeframe-ordering: comparator seconds count")
    if not timeframe:
        return _INT_MAX
    if timeframe == "TICK":
        return 0
    try:
        count = _count(timeframe[1:].strip(_JAVA_TRIM))
    except ValueError:
        return _INT_MAX
    multiplier = {"S": 1, "M": 60, "H": 3600}.get(timeframe[0], 86400)
    return _int32(count * multiplier)


def translate_sq3_tf_to_string(value: int) -> str:
    """Translate the donor's finite legacy SQ3 minute constants."""
    logger.debug("FR-data-timeframe-ordering: translating SQ3 constant")
    return _LEGACY.get(value, "unknown")


def translate_to_mt_constant(timeframe: str) -> int:
    """Match donor legacy MT constants; these are not MT5 enum encodings."""
    logger.debug("FR-data-timeframe-ordering: translating MT constant")
    return next((key for key, name in _LEGACY.items() if name == timeframe), -2)


class TimeframeManager:
    """Own custom timeframe lists at an explicit host-supplied file path.

    An omitted path is a read-only default registry. No host settings or active
    store is inferred. Failed writes do not modify the in-memory list.
    """

    def __init__(self, custom_timeframes_path: Path | None = None) -> None:
        self._path = custom_timeframes_path
        self._custom: list[str] = []
        if self._path is not None and self._path.exists():
            with self._path.open(encoding="utf-8", newline="") as stream:
                self._custom = list(
                    dict.fromkeys(
                        value for value in stream.read().split("\r\n") if value
                    )
                )
        logger.info("FR-data-timeframe-registry: loaded explicit/default registry")

    @staticmethod
    def is_valid(timeframe: str | None) -> bool:
        """Match donor registration validation, which excludes TICK/Intraday."""
        logger.debug("FR-data-timeframe-registry: validating registration")
        if timeframe in ("Weekly", "Monthly"):
            return True
        if not timeframe or timeframe[0] not in _UNITS:
            return False
        try:
            _count(timeframe[1:])
        except ValueError:
            return False
        return True

    @staticmethod
    def get_predefined_timeframes() -> list[str]:
        """Return a detached donor predefined list, distinct from defaults."""
        logger.debug("FR-data-timeframe-registry: reading predefined list")
        return list(_PREDEFINED)

    def get_timeframes(self) -> list[str]:
        """Return sorted defaults plus registered custom entries."""
        logger.debug("FR-data-timeframe-registry: reading registered list")
        return sorted([*_DEFAULTS, *self._custom], key=timeframe_sort_key)

    def tf_exists(self, timeframe: str) -> bool:
        """Test exact donor membership, without aliases or case folding."""
        logger.debug("FR-data-timeframe-registry: testing membership")
        return timeframe in _DEFAULTS or timeframe in self._custom

    def add_timeframe(self, timeframe: str) -> None:
        """Validate and persist a custom entry; reject implicit file targets."""
        if self.tf_exists(timeframe) or not self.is_valid(timeframe):
            raise ValueError("Timeframe already exists or has invalid format")
        if self._path is None:
            raise ValueError("An explicit custom timeframes file is required")
        updated = [*self._custom, timeframe]
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=self._path.parent,
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write("\r\n".join(updated))
            temporary.replace(self._path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        self._custom = updated
        logger.info("FR-data-timeframe-registry: added custom timeframe")

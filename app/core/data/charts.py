"""Canonical donor chart definition, initialization and cache identity.

Description:
    Owns datalib/ChartDef.java constructors, state, XML, getClone overloads,
    isSameConnectionSymbol, canBeComputedFrom, isSmallerThan and getChartsHash.
    DataCatalog resolves data; factories receive resolved instrument metadata.
    Cache identity receives an explicit session snapshot instead of importing a
    workspace/global SessionManager. No catalog or calendar logic is duplicated.
Purpose:
    FEAT-DATA-CHART-IDENTITY: Complete donor chart contracts and dependencies.
Key Capabilities:
    - FR-data-chart-initialize: DEBUG records live/backtest/copy construction;
      catalog integration tests verify state, errors and day-end correction.
    - FR-data-chart-identity: DEBUG records Java hashes, comparisons and cache
      keys; tests cover UTF-16, donor base-unit comparison, and session changes.
    - FR-data-chart-clone: DEBUG records nested detached clones; tests verify all
      copied fields, positive-only range overrides and symbol replacement.
    - FR-data-chart-xml: DEBUG records full nested XML and recovery; tests verify
      states 0/1/2, nullable strings, numeric defaults and emitted logs.
Python API Usage:
    chart = ChartDef.for_backtest(data_info, instrument_info, timeframe="H7",
        history_from=0, history_to=0, spread=0.0, session="No Session", timezone="UTC")
CLI Usage:
    uv run pytest tests/core/data/test_chart_contracts.py --no-cov

    Donor get/set methods map to typed attributes, except getSpread (real-spread
    sentinel), isBacktestDataDef and getBarTimeType (derived properties). The
    Python finite Timeframe enum and explicit dependency/timezone inputs are
    retained host adaptations. Original custom session/history eligibility and
    descriptive cache hash are replaced by donor rules in approved S15 iteration 2.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timedelta
from typing import Any
from xml.etree.ElementTree import Element
from zoneinfo import ZoneInfo

from app.core.data.contracts import DataInfo, SessionWindow
from app.core.data.instruments import InstrumentInfo, _scalar_xml, _xml_values
from app.core.data.timeframes import (
    can_compute_chart_from,
    chart_period,
    normalize_timeframe,
    timeframe_to_seconds,
)
from app.core.enums import Timeframe
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError

logger = get_logger(__name__)
_BACKTEST = 2
_HOURS_PER_DAY = 24
_MINUTES_PER_HOUR = 60
_BAR_TYPES = (1, 2)
_XML_FIELDS = {
    "connectionName": "connection_name",
    "symbol": "symbol",
    "instrument": "instrument",
    "timeframe": "timeframe",
    "historyFrom": "history_from",
    "historyTo": "history_to",
    "loadedHistoryFrom": "loaded_history_from",
    "spread": "spread",
    "registered": "registered",
    "session": "session",
    "type": "chart_type",
    "backloadType": "backload_type",
    "backloadNumber": "backload_number",
}
_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _java_string_hash(value: str | None) -> int:
    """Map Java UTF-16 String.hashCode; a default object's unset hash is zero."""
    result = 0
    encoded = (value or "").encode("utf-16-be", errors="surrogatepass")
    for offset in range(0, len(encoded), 2):
        result = (
            31 * result + int.from_bytes(encoded[offset : offset + 2])
        ) & 0xFFFFFFFF
    return result if result < (1 << 31) else result - (1 << 32)


def _day_end(milliseconds: int, timezone: str) -> int:
    """Map SQTime.correctDayEnd in an explicit zone; use integer milliseconds.

    Python datetime's representable range bounds the host API; Java long values
    outside it raise instead of wrapping or guessing a date. DST uses ZoneInfo.
    """
    epoch = datetime(1970, 1, 1, tzinfo=ZoneInfo("UTC"))
    value = (epoch + timedelta(milliseconds=milliseconds)).astimezone(
        ZoneInfo(timezone)
    )
    end = value.replace(hour=23, minute=59, second=59, microsecond=999000)
    delta = end.astimezone(ZoneInfo("UTC")) - epoch
    return delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000


def _session_time(value: str) -> str:
    """Map SessionElement time formatting and getSessionStr's N/A recovery."""
    try:
        hour, minute = (int(part) for part in value.split(":"))
        if not 0 <= hour < _HOURS_PER_DAY or not 0 <= minute < _MINUTES_PER_HOUR:
            return "N/A"
    except ValueError, TypeError:
        logger.debug("FR-data-chart-identity: invalid session time recovered")
        return "N/A"
    return f"{hour:02d}:{minute:02d}"


@dataclass
class ChartDef:
    """Donor chart state; constructor-specific behavior lives in typed factories."""

    symbol: str | None = None
    timeframe: str | Timeframe | None = None
    instrument: str | None = None
    session: str | None = None
    connection_name: str | None = None
    connection_hash: int = 0
    symbol_hash: int = 0
    history_from: int = 0
    history_to: int = 0
    loaded_history_from: int = 0
    spread: float = 0.0
    real_spread: bool = False
    min_distance: float = 0.0
    chart_type: int = 0
    backload_type: int = 0
    backload_number: int = 0
    registered: bool = False
    data_info: DataInfo | None = None
    instrument_info: InstrumentInfo | None = None

    def __post_init__(self) -> None:
        """Initialize cached donor identity without an implicit catalog lookup."""
        if isinstance(self.timeframe, Timeframe):
            self.timeframe = normalize_timeframe(self.timeframe)
        self.connection_hash = _java_string_hash(self.connection_name)
        self.symbol_hash = _java_string_hash(self.symbol)
        logger.debug("FR-data-chart-identity: initialized Java string hashes")

    @classmethod
    def for_live(
        cls,
        data_info: DataInfo,
        instrument_info: InstrumentInfo | None,
        *,
        timeframe: str | Timeframe,
        backload_type: int,
        backload_number: int,
        session: str,
    ) -> ChartDef:
        """Map live construction with resolved data and instrument inputs."""
        if data_info.connection is None or data_info.symbol is None:
            raise ValueError("Chart construction requires connection and symbol")
        logger.debug("FR-data-chart-initialize: initialized live chart")
        return cls(
            symbol=data_info.symbol,
            connection_name=data_info.connection,
            timeframe=normalize_timeframe(timeframe),
            data_info=data_info,
            instrument_info=instrument_info,
            chart_type=1,
            session=session,
            backload_type=backload_type,
            backload_number=backload_number,
        )

    @classmethod
    def for_backtest(
        cls,
        data_info: DataInfo,
        instrument_info: InstrumentInfo | None,
        *,
        timeframe: str | Timeframe,
        history_from: int,
        history_to: int,
        spread: float,
        session: str,
        timezone: str,
    ) -> ChartDef:
        """Map backtest state, zero-start sentinel and daily session override."""
        if data_info.connection is None or data_info.symbol is None:
            raise ValueError("Chart construction requires connection and symbol")
        name = normalize_timeframe(timeframe)
        chart_period(name)
        start = history_from if history_from != 0 else -(1 << 63)
        if data_info.bar_time_type == 1 and name.startswith("D"):
            session = "No Session"
        logger.debug("FR-data-chart-initialize: initialized backtest chart")
        return cls(
            symbol=data_info.symbol,
            connection_name=data_info.connection,
            timeframe=name,
            data_info=data_info,
            instrument_info=instrument_info,
            chart_type=_BACKTEST,
            history_from=start,
            history_to=_day_end(history_to, timezone),
            loaded_history_from=start,
            spread=spread,
            session=session,
        )

    def copy_for_backtest(
        self,
        data_info: DataInfo,
        instrument_info: InstrumentInfo | None,
        *,
        timezone: str,
        timeframe: str | Timeframe | None = None,
    ) -> ChartDef:
        """Map copy constructors using newly resolved catalog/instrument inputs.

        As in the donor constructor, metadata is supplied by the lookup owner
        rather than cloned from a potentially stale original chart cache.
        """
        if self.symbol is None or self.timeframe is None or self.session is None:
            raise ValueError("Copy construction requires resolved dataset metadata")
        if (
            data_info.symbol != self.symbol
            or data_info.connection != self.connection_name
        ):
            raise ValueError(
                "Copy metadata does not match the requested connection/symbol"
            )
        result = self.for_backtest(
            data_info,
            instrument_info,
            timeframe=self.timeframe if timeframe is None else timeframe,
            history_from=self.history_from,
            history_to=self.history_to,
            spread=self.get_spread(),
            session=self.session,
            timezone=timezone,
        )
        result.loaded_history_from = self.loaded_history_from
        return result

    @property
    def is_backtest_data_def(self) -> bool:
        """Map isBacktestDataDef without duplicating the chart type flag."""
        return self.chart_type == _BACKTEST

    @property
    def bar_time_type(self) -> int:
        """Map getBarTimeType; absent catalog data is an explicit error."""
        if self.data_info is None:
            raise ValueError("Chart requires resolved dataset metadata")
        return self.data_info.bar_time_type

    @property
    def symbol_info(self) -> InstrumentInfo | None:
        """Map getSymbolInfo/getInstrumentInfo to the same resolved instrument."""
        return self.instrument_info

    def get_spread(self) -> float:
        """Map real-spread sentinel; spread assignments retain donor raw state."""
        logger.debug("FR-data-chart-identity: reading effective spread")
        return -1.0 if self.real_spread else self.spread

    def timeframe_seconds(self) -> int:
        """Read the shared duration owner for a recognized timeframe."""
        if self.timeframe is None:
            raise ValueError("Chart timeframe is unset")
        return timeframe_to_seconds(self.timeframe)

    def is_symbol_recognized(self) -> bool:
        """Map donor recognition, which distinguishes null from an empty string."""
        return self.symbol is not None

    def is_same_connection_symbol(self, other: ChartDef) -> bool:
        """Map cached Java hash equality, including source hash collisions."""
        logger.debug("FR-data-chart-identity: comparing connection/symbol")
        return (
            self.symbol_hash == other.symbol_hash
            and self.connection_hash == other.connection_hash
        )

    def _require_period(self) -> tuple[int, int, bool]:
        if self.bar_time_type not in _BAR_TYPES or self.timeframe is None:
            raise DomainError(
                code="INVALID_TIMEFRAME", message="No matching donor bar type"
            )
        return chart_period(self.timeframe)

    def is_smaller_than(self, other: ChartDef) -> bool:
        """Map donor base-unit comparison using this chart's barTimeType for both."""
        if not self.is_same_connection_symbol(other):
            return False
        _, base, _ = self._require_period()
        if other.timeframe is None:
            raise ValueError("Other chart timeframe is unset")
        return base < chart_period(other.timeframe)[1]

    def can_be_computed_from(self, other: ChartDef) -> bool:
        """Map TimeBar/Intraday eligibility; session/history are not extra filters."""
        if not self.is_same_connection_symbol(other):
            return False
        self._require_period()
        if self.timeframe is None or other.timeframe is None:
            raise ValueError("Chart timeframe is unset")
        return can_compute_chart_from(self.timeframe, other.timeframe)

    def get_charts_hash(
        self,
        *,
        session_name: str | None,
        session_elements: Sequence[SessionWindow] | None,
    ) -> str:
        """Map getChartsHash/getSessionStr/getDataFileHash from explicit snapshots.

        None session_name represents failed SessionManager lookup (NULL).
        A present name with None elements represents its null element list
        (name_NONE), distinct from an empty list (name_). Callers resolve sessions.
        """
        if self.data_info is None or self.symbol is None:
            raise ValueError("Cache identity requires recognized dataset metadata")
        session_text = "NULL" if session_name is None else session_name + "_"
        if session_name is not None and session_elements is None:
            session_text += "NONE"
        elif session_name is not None and session_elements is not None:
            for window in session_elements:
                first = window.day_from if window.day_from in _DAYS else "N/A"
                last = window.day_to if window.day_to in _DAYS else "N/A"
                end_time = _session_time(window.end_time)
                if first == last and last in _DAYS and end_time == "00:00":
                    last = _DAYS[(_DAYS.index(last) + 1) % len(_DAYS)]
                session_text += (
                    first
                    + _session_time(window.start_time)
                    + last
                    + end_time
                    + ("Y" if window.eod else "N")
                )
        logger.debug("FR-data-chart-identity: computed donor cache identity")
        connection = (
            self.connection_name if self.connection_name is not None else "null"
        )
        timeframe = str(self.timeframe) if self.timeframe is not None else "null"
        return (
            f"{self.symbol}{connection}{self.history_from}{self.history_to}"
            f"{session_text}{timeframe}{self.data_info.file_hash}"
        )

    def clone(
        self,
        symbol: str | None = None,
        history_from: int | None = None,
        history_to: int | None = None,
    ) -> ChartDef:
        """Map getClone with detached children and positive-only date overrides."""
        result = replace(
            self,
            symbol=self.symbol if symbol is None else symbol,
            history_from=history_from
            if history_from is not None and history_from > 0
            else self.history_from,
            history_to=history_to
            if history_to is not None and history_to > 0
            else self.history_to,
            data_info=self.data_info.clone() if self.data_info is not None else None,
            instrument_info=self.instrument_info.clone()
            if self.instrument_info is not None
            else None,
        )
        result.connection_hash = self.connection_hash
        result.symbol_hash = (
            self.symbol_hash if symbol is None else _java_string_hash(symbol)
        )
        logger.debug("FR-data-chart-clone: cloned complete chart metadata")
        return result

    def to_xml(self) -> Element:
        """Map getXML, which includes DataInfo but not the separate instrument cache."""
        result = _scalar_xml("ChartDef", self.to_dict(), _XML_FIELDS)
        if self.data_info is not None:
            result.append(self.data_info.to_xml())
        logger.debug("FR-data-chart-xml: serialized chart")
        return result

    @classmethod
    def from_xml(cls, element: Element, *, timezone: str) -> ChartDef:
        """Map setFromXML defaults/recovery, type preservation and nested DataInfo."""
        if element.tag != "ChartDef" or any(
            element.get(key) is None for key in ("connectionName", "symbol")
        ):
            raise ValueError("ChartDef XML requires connectionName and symbol")
        values = _xml_values(element, _XML_FIELDS, asdict(cls()))
        values["history_to"] = _day_end(values["history_to"], timezone)
        child = element.find("DataInfo")
        values["data_info"] = DataInfo.from_xml(child) if child is not None else None
        logger.debug("FR-data-chart-xml: parsed chart")
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        """Serialize canonical chart state, including nested metadata."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChartDef:
        """Restore nested canonical values without an old-path compatibility owner."""
        values = {
            field.name: data[field.name] for field in fields(cls) if field.name in data
        }
        if isinstance(values.get("data_info"), dict):
            values["data_info"] = DataInfo.from_dict(values["data_info"])
        if isinstance(values.get("instrument_info"), dict):
            values["instrument_info"] = InstrumentInfo.from_dict(
                values["instrument_info"]
            )
        return cls(**values)

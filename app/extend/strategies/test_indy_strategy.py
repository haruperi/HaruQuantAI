# ruff: noqa: N802
"""Indicator logging and verification strategy.

Description:
    Computes custom indicator values on bar updates and records timestamp, Close,
    Volume, and indicator values formatted as semicolon-separated CSV records.
    Conforms to StrategyQuant SQ.Strategies.TestIndyStrategy.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful TestIndyStrategy strategy.

Key Capabilities:
    - FR-STRAT-TESTINDY: Indicator evaluation and structured CSV stream output.

Python API Usage:
    from app.extend.strategies.test_indy_strategy import TestIndyStrategy
    strat = TestIndyStrategy()
    strat.Initialize()
    strat.OnBarUpdate()
    strat.Deinitialize()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import IO, override

from app.core.host.logging import get_logger
from app.extend.strategies.base import Strategy, UpdateEventTypes

logger = get_logger(__name__)


class TestIndyStrategy(Strategy):
    """Logs indicator values and bar metrics to CSV output stream."""

    __test__ = False

    def __init__(
        self,
        event_type: int = UpdateEventTypes.BarOpen,
        data_index: int = 1,
    ) -> None:
        super().__init__()
        self._event_type: int = event_type
        self._data_index: int = data_index
        self._file_name: str = "test_indy"
        self._writer: IO[str] | None = None
        self._records: list[str] = []

    def getIndyValue(self) -> float:
        """Return indicator value for current bar (overrideable in subclasses)."""
        return 0.0

    def setLogName(self, log_file_name: str) -> None:
        """Set output log identifier."""
        self._file_name = log_file_name

    def get_records(self) -> list[str]:
        """Return captured CSV records."""
        return list(self._records)

    @override
    def Initialize(self) -> None:
        """Configure update event frequency."""
        self.setUpdateEventType(self._event_type)
        logger.info(
            "FR-STRAT-TESTINDY: Initialize configured for log=%s", self._file_name
        )

    @override
    def OnBarUpdate(self) -> None:
        """Write formatted timestamp, Close, Volume, and indicator value."""
        ts_ms = self.Time.get(self._data_index)
        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        time_str = dt.strftime("%Y.%m.%d;%H:%M")

        close_val = self.Close.get(self._data_index)
        volume_val = self.Volume.get(self._data_index)
        indy_val = self.getIndyValue()

        record = f"{time_str};{close_val};{volume_val};{indy_val}"
        self._records.append(record)
        if self._writer is not None:
            self._writer.write(record + "\n")

        logger.debug("FR-STRAT-TESTINDY: recorded bar %s", record)

    @override
    def Deinitialize(self) -> None:
        """Flush and close output writer if open."""
        if self._writer is not None:
            self._writer.close()
            self._writer = None
        logger.info("FR-STRAT-TESTINDY: Deinitialize completed")

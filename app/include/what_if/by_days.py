"""Trade only on selected weekdays."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, ClassVar, override

from pydantic import Field, field_validator

from .base import BaseWhatIf, WhatIfRecord, local_open, validate_timezone


class ByDays(BaseWhatIf):
    """Trade only on selected weekdays."""

    name: ClassVar[str] = "Trade only on selected weekdays"
    days: tuple[Annotated[int, Field(ge=1, le=7)], ...] = (1, 2, 3, 4, 5, 6, 7)
    timezone: str = "UTC"

    _timezone = field_validator("timezone")(validate_timezone)

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        return [
            t for t in trades if local_open(t, self.timezone).isoweekday() in self.days
        ]

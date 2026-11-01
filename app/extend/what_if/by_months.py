"""Trade only during selected months."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, ClassVar, override

from pydantic import Field, field_validator

from .base import BaseWhatIf, WhatIfRecord, local_open, validate_timezone


class ByMonths(BaseWhatIf):
    """Trade only during selected months."""

    name: ClassVar[str] = "Trade only during selected months"
    months: tuple[Annotated[int, Field(ge=1, le=12)], ...] = tuple(range(1, 13))
    timezone: str = "UTC"

    _timezone = field_validator("timezone")(validate_timezone)

    @override
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Return the scenario result without mutating history."""
        return [t for t in trades if local_open(t, self.timezone).month in self.months]

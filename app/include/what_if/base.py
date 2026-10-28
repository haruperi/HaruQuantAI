"""Immutable historical analysis records and the WhatIf extension contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from typing import Any, ClassVar, Literal, Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WhatIfRecord(BaseModel):
    """Analysis snapshot; milliseconds since Unix epoch, signed monetary costs.

    Closed trades, unfilled pending orders and balance entries stay distinguishable.
    Profit excludes commission, swap and fee; net_profit includes all four.
    """

    model_config = ConfigDict(
        frozen=True, extra="forbid", strict=True, allow_inf_nan=False
    )
    record_id: int
    kind: Literal["trade", "pending", "balance"] = "trade"
    symbol: str = ""
    direction: Literal[-1, 0, 1] = 1
    time_open_msc: int
    time_close_msc: int
    volume: float = Field(default=1.0, ge=0)
    profit: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    fee: float = 0.0

    @model_validator(mode="after")
    def validate_trade(self) -> Self:
        """Require valid completed trade intervals, directions and sizes."""
        if self.time_close_msc < self.time_open_msc:
            raise ValueError("Close time precedes open time")
        if self.kind == "trade" and (self.volume <= 0 or self.direction == 0):
            raise ValueError("Trades require positive volume and a direction")
        return self

    @property
    def net_profit(self) -> float:
        """Profit including signed costs and financing."""
        return self.profit + self.commission + self.swap + self.fee

    @classmethod
    def from_closed_trade(cls, trade: Any) -> Self:
        """Adapt a ClosedTrade snapshot without importing the workspace layer."""
        return cls(
            record_id=trade.position_id,
            symbol=trade.symbol,
            direction=trade.direction,
            time_open_msc=trade.time_open_msc,
            time_close_msc=trade.time_close_msc,
            volume=trade.volume,
            profit=trade.profit,
            commission=trade.commission,
            swap=trade.swap,
            fee=trade.fee,
        )


class BaseWhatIf(BaseModel, ABC):
    """Validated scenario returning a new list without changing source records."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        allow_inf_nan=False,
    )
    name: ClassVar[str] = "WhatIf"

    @abstractmethod
    def filter_trades(self, trades: Sequence[WhatIfRecord]) -> list[WhatIfRecord]:
        """Apply this scenario to immutable analysis snapshots."""

    @classmethod
    def get_parameter_schema(cls) -> dict[str, Any]:
        """Expose configurable fields for editor controls."""
        return cls.model_json_schema()


def local_open(record: WhatIfRecord, timezone: str) -> datetime:
    """Interpret an epoch timestamp in the explicit analysis timezone."""
    return datetime.fromtimestamp(record.time_open_msc / 1000, ZoneInfo(timezone))


def validate_timezone(value: str) -> str:
    """Fail during configuration rather than when processing the first trade."""
    try:
        ZoneInfo(value)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Unknown timezone: {value}") from exc
    return value


def exclude_ranked(
    trades: Sequence[WhatIfRecord],
    count: int,
    *,
    lowest: bool,
    include_pending: bool = False,
) -> list[WhatIfRecord]:
    """Rank gross profit stably; lowest removal traverses from the end."""
    ranked = sorted(enumerate(trades), key=lambda pair: pair[1].profit, reverse=True)
    candidates = reversed(ranked) if lowest else iter(ranked)
    removed: set[int] = set()
    for index, trade in candidates:
        eligible = trade.kind != "balance" if include_pending else trade.kind == "trade"
        if eligible and len(removed) < count:
            removed.add(index)
    return [trade for index, trade in ranked if index not in removed]


def replace_record(record: WhatIfRecord, **changes: Any) -> WhatIfRecord:
    """Revalidate derived money values, including overflow, on replacement."""
    return WhatIfRecord.model_validate(record.model_dump() | changes)

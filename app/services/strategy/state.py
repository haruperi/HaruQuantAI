"""Serializable strategy-local state; it is not the broker ledger."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class StrategyState:
    """Minimal restart-safe state shared by standard and custom strategies."""

    last_processed_signal_bar: str | None = None
    daily_trade_count: dict[str, int] = field(default_factory=dict)
    open_signal_order_identifiers: dict[str, str] = field(default_factory=dict)
    cooldown_until: datetime | None = None
    emitted_intent_ids: set[str] = field(default_factory=set)
    processed_event_ids: set[str] = field(default_factory=set)
    custom: dict[str, Any] = field(default_factory=dict)

    def entry_count_for(self, trading_day: str) -> int:
        return self.daily_trade_count.get(trading_day, 0)

    def increment_entry_count(self, trading_day: str) -> None:
        self.daily_trade_count[trading_day] = self.entry_count_for(trading_day) + 1

    def get_custom(self, key: str, default: Any = None) -> Any:
        return self.custom.get(key, default)

    def set_custom(self, key: str, value: Any) -> None:
        self.custom[key] = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_processed_signal_bar": self.last_processed_signal_bar,
            "daily_trade_count": dict(self.daily_trade_count),
            "open_signal_order_identifiers": dict(self.open_signal_order_identifiers),
            "cooldown_until": self.cooldown_until.isoformat()
            if self.cooldown_until
            else None,
            "emitted_intent_ids": sorted(self.emitted_intent_ids),
            "processed_event_ids": sorted(self.processed_event_ids),
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> StrategyState:
        cooldown_raw = value.get("cooldown_until")
        cooldown = (
            datetime.fromisoformat(cooldown_raw)
            if isinstance(cooldown_raw, str)
            else None
        )
        return cls(
            last_processed_signal_bar=value.get("last_processed_signal_bar"),
            daily_trade_count=dict(value.get("daily_trade_count", {})),
            open_signal_order_identifiers=dict(
                value.get("open_signal_order_identifiers", {})
            ),
            cooldown_until=cooldown,
            emitted_intent_ids=set(value.get("emitted_intent_ids", [])),
            processed_event_ids=set(value.get("processed_event_ids", [])),
            custom=dict(value.get("custom", {})),
        )

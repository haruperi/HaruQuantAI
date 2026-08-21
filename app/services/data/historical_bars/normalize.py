"""Normalization of raw broker price bars into canonical Bar DTOs."""

from collections.abc import Sequence
from typing import TYPE_CHECKING

from app.contracts.data.historical_bars import Bar

if TYPE_CHECKING:
    from app.contracts.broker.market_data import BrokerRawBar


def normalize_raw_bar(raw: BrokerRawBar) -> Bar:
    """Transform single raw broker bar into canonical normalized Bar.

    Satisfies:
        FR-DATA-NORMALIZE_BARS: Converts broker-specific fields into standard
        immutable Bar DTO.

    Args:
        raw: Raw broker bar.

    Returns:
        Canonical Bar instance.
    """
    return Bar(
        datetime=raw.timestamp,
        open=raw.open_price,
        high=raw.high_price,
        low=raw.low_price,
        close=raw.close_price,
        volume=raw.volume,
    )


def normalize_bars(raw_bars: Sequence[BrokerRawBar]) -> Sequence[Bar]:
    """Transform sequence of raw broker bars into normalized Bar DTOs.

    Satisfies:
        FR-DATA-NORMALIZE_BARS: Batch normalizes broker raw bars.

    Args:
        raw_bars: Collection of raw price bars.

    Returns:
        Tuple of normalized Bar instances.
    """
    return tuple(normalize_raw_bar(b) for b in raw_bars)

"""Market trading hours and session window calculations.

Provides timezone-aware market hours lookup and normalized trading session
windows across the major global sessions.
"""

from datetime import UTC, datetime
from typing import Any

from app.services.utils.logger import logger

# --- Session Constants ---
SYDNEY_START: int = 22
SYDNEY_END: int = 7
TOKYO_START: int = 0
TOKYO_END: int = 9
LONDON_START: int = 8
LONDON_END: int = 17
NY_START: int = 13
NY_END: int = 22
HOURS_IN_DAY: int = 24
SECONDS_IN_HOUR: int = 3600


def get_market_hours(symbol: str, request_id: str | None = None) -> dict[str, Any]:
    """Description.
        Get timezone-aware market hours for a given symbol.
    
    Args:
        symbol: str.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    logger.info(
        f"Retrieving market hours for {symbol}",
        extra={"request_id": request_id},
    )
    return {
        "symbol": symbol,
        "timezone": "UTC",
        "trading_days": {
            "Monday": {"start": "00:00", "end": "24:00"},
            "Tuesday": {"start": "00:00", "end": "24:00"},
            "Wednesday": {"start": "00:00", "end": "24:00"},
            "Thursday": {"start": "00:00", "end": "24:00"},
            "Friday": {"start": "00:00", "end": "24:00"},
        },
        "historical_hours_supported": False,
    }


def get_trading_sessions(
    start_time: datetime, end_time: datetime, request_id: str | None = None
) -> list[dict[str, Any]]:
    """Description.
        Return normalized trading session windows and labels.
    
    Args:
        start_time: datetime.
        end_time: datetime.
        request_id: str | None.
    
    Returns:
        list[dict[str, Any]].
    """
    logger.info(
        f"Generating session windows between {start_time} and {end_time}",
        extra={"request_id": request_id},
    )
    sessions = []
    current = start_time.replace(minute=0, second=0, microsecond=0)
    while current < end_time:
        hour = current.hour
        active = []
        if hour >= SYDNEY_START or hour < SYDNEY_END:
            active.append("Sydney")
        if TOKYO_START <= hour < TOKYO_END:
            active.append("Tokyo")
        if LONDON_START <= hour < LONDON_END:
            active.append("London")
        if NY_START <= hour < NY_END:
            active.append("New York")

        for session in active:
            next_hour = (current.hour + 1) % HOURS_IN_DAY
            sessions.append(
                {
                    "session_name": session,
                    "start": current.isoformat(),
                    "end": (current.replace(hour=next_hour)).isoformat(),
                }
            )
        current = datetime.fromtimestamp(current.timestamp() + SECONDS_IN_HOUR, tz=UTC)

    return sessions


__all__ = [
    "get_market_hours",
    "get_trading_sessions",
]

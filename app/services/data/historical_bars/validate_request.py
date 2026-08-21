"""Request parameter validation for historical bars retrieval."""

from typing import TYPE_CHECKING

from app.services.data.historical_bars.config import VALID_TIMEFRAMES

if TYPE_CHECKING:
    from app.contracts.data.historical_bars import HistoricalBarsRequest


def validate_historical_request(request: HistoricalBarsRequest) -> None:
    """Validate historical bar request specifications.

    Satisfies:
        FR-DATA-VALIDATE_REQUEST: Validates symbol presence, date ordering,
        and supported timeframe format.

    Args:
        request: Historical bar query specifications.

    Raises:
        ValueError: If query specifications are invalid.
    """
    if not request.symbol or not request.symbol.strip():
        msg = "Symbol must not be empty"
        raise ValueError(msg)

    if request.end <= request.start:
        msg = (
            f"End datetime ({request.end}) must be strictly after "
            f"start datetime ({request.start})"
        )
        raise ValueError(msg)

    tf = request.timeframe.upper()
    if tf not in VALID_TIMEFRAMES:
        allowed = sorted(VALID_TIMEFRAMES)
        msg = f"Invalid timeframe '{request.timeframe}'. Must be one of {allowed}"
        raise ValueError(msg)

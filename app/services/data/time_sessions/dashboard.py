"""Owner-authored unavailable market-hours dashboard snapshot."""

from app.utils import utc_now


def get_market_hours_dashboard_snapshot() -> dict[str, object]:
    """Return explicit unavailable evidence until a market scope is selected.

    Returns:
        Timestamped market-context requirement.
    """
    return {
        "view": "market_hours",
        "owner": "data",
        "status": "unavailable",
        "reason": "MARKET_SCOPE_REQUIRED",
        "observed_at": utc_now(),
    }


__all__ = ("get_market_hours_dashboard_snapshot",)

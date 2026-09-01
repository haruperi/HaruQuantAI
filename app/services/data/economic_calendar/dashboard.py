"""Owner-authored unavailable economic-calendar dashboard snapshot."""

from app.kernel.time import utc_now


def get_calendar_dashboard_snapshot() -> dict[str, object]:
    """Return explicit unavailable evidence until a calendar scope is selected.

    Returns:
        Timestamped calendar-context requirement.
    """
    return {
        "view": "calendar",
        "owner": "data",
        "status": "unavailable",
        "reason": "CALENDAR_SCOPE_REQUIRED",
        "observed_at": utc_now(),
    }


__all__ = ("get_calendar_dashboard_snapshot",)

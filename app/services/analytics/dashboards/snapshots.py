"""Owner-authored unavailable Analytics dashboard snapshots."""

from app.kernel.time import utc_now


def get_analytics_dashboard_snapshot(view: str) -> dict[str, object]:
    """Return explicit unavailable evidence until a report context is selected.

    Args:
        view: Approved Analytics dashboard view.

    Returns:
        Timestamped, non-invented unavailable snapshot.

    Raises:
        ValueError: If the view is not owned by Analytics.
    """
    if view not in {"equity_curve", "summary"}:
        raise ValueError("unsupported Analytics dashboard view")
    return {
        "view": view,
        "owner": "analytics",
        "status": "unavailable",
        "reason": "REPORT_CONTEXT_REQUIRED",
        "observed_at": utc_now(),
    }


__all__ = ("get_analytics_dashboard_snapshot",)

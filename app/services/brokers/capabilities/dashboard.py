"""Owner-authored Broker capability dashboard snapshot."""

from app.utils import utc_now


def get_broker_dashboard_snapshot() -> dict[str, object]:
    """Return explicit unavailable evidence without opening a broker socket.

    Returns:
        Timestamped broker-context requirement.
    """
    return {
        "view": "broker",
        "owner": "brokers",
        "status": "unavailable",
        "reason": "BROKER_SESSION_CONTEXT_REQUIRED",
        "observed_at": utc_now(),
    }


__all__ = ("get_broker_dashboard_snapshot",)

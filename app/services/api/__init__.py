"""Approved package-root boundary for the UI/API domain."""

from app.services.api.alerts import (
    CriticalAlertDeliveryResult,
    CriticalAlertError,
    CriticalAlertSink,
    CriticalAlertTrigger,
    CriticalOperationalAlert,
    build_kill_switch_activation_alert,
    build_unknown_broker_state_alert,
    deliver_critical_alert,
)
from app.services.api.contracts import ResearchRunRequest

__all__ = (
    "CriticalAlertDeliveryResult",
    "CriticalAlertError",
    "CriticalAlertSink",
    "CriticalAlertTrigger",
    "CriticalOperationalAlert",
    "ResearchRunRequest",
    "build_kill_switch_activation_alert",
    "build_unknown_broker_state_alert",
    "deliver_critical_alert",
)

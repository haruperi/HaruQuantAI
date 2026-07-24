"""Public critical operational alert boundary."""

from app.services.api.alerts.builders import (
    build_kill_switch_activation_alert,
    build_unknown_broker_state_alert,
)
from app.services.api.alerts.delivery import deliver_critical_alert
from app.services.api.alerts.models import (
    CriticalAlertDeliveryResult,
    CriticalAlertError,
    CriticalAlertSink,
    CriticalAlertTrigger,
    CriticalOperationalAlert,
)

__all__ = (
    "CriticalAlertDeliveryResult",
    "CriticalAlertError",
    "CriticalAlertSink",
    "CriticalAlertTrigger",
    "CriticalOperationalAlert",
    "build_kill_switch_activation_alert",
    "build_unknown_broker_state_alert",
    "deliver_critical_alert",
)

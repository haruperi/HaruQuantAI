"""Trading Monitoring and Health submodule.

Exports:
    LatencyTracker: Bounded latency history tracking.
    LostOrderWatchdog: Flag stale/lost orders.
    IncidentSignal: Represents alert messages with runbook bindings.
    OperationalSignalsManager: Incidents dispatcher, rate limiter and escalations.
    HeartbeatEmitter: Emits dead man's switch heartbeats.
    ToolHealthMonitor: Consecutive failure tracker.
    MonitoringService: Root monitoring orchestrator and circuit breakers.
"""

from app.services.trading.monitoring.heartbeat_watchdog import HeartbeatEmitter
from app.services.trading.monitoring.operational_signals import (
    IncidentSignal,
    OperationalSignalsManager,
)
from app.services.trading.monitoring.service import MonitoringService
from app.services.trading.monitoring.timeouts_and_staleness import (
    LatencyTracker,
    LostOrderWatchdog,
)
from app.services.trading.monitoring.tool_health import ToolHealthMonitor

__all__ = [
    "HeartbeatEmitter",
    "IncidentSignal",
    "LatencyTracker",
    "LostOrderWatchdog",
    "MonitoringService",
    "OperationalSignalsManager",
    "ToolHealthMonitor",
]

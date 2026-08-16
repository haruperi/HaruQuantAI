"""Execution realism feature API."""

from app.services.simulator.realism.contracts import (
    LatencyProfile,
    QueueFillResult,
    QueueModel,
    RealisticExecutionResult,
    build_latency_profile,
    build_queue_model,
)
from app.services.simulator.realism.crash_points import (
    create_state,
    get_points,
    recover,
)
from app.services.simulator.realism.latency import project_latency_timestamps
from app.services.simulator.realism.pricing import price_realistic_execution
from app.services.simulator.realism.providers import (
    admit_calibrated_realism,
    build_fill_model_provider,
    sample_calibrated_realism,
)
from app.services.simulator.realism.queue import simulate_queue_fill
from app.services.simulator.realism.races import resolve_cancel_replace_race
from app.services.simulator.realism.random_streams import (
    create,
    get_identity,
    get_performance_budgets,
    restore,
    sample,
    serialize,
)
from app.services.simulator.realism.views import project_execution_views

__all__ = [
    "LatencyProfile",
    "QueueFillResult",
    "QueueModel",
    "RealisticExecutionResult",
    "admit_calibrated_realism",
    "build_fill_model_provider",
    "build_latency_profile",
    "build_queue_model",
    "create_realism_stream",
    "create_recovery_state",
    "get_realism_performance_budgets",
    "get_realism_stream_identity",
    "get_simulation_crash_points",
    "price_realistic_execution",
    "project_execution_views",
    "project_latency_timestamps",
    "recover_unknown_outcome",
    "resolve_cancel_replace_race",
    "restore_realism_stream",
    "sample_calibrated_realism",
    "sample_realism_stream",
    "serialize_realism_stream",
    "simulate_queue_fill",
]

create_realism_stream = create
sample_realism_stream = sample
serialize_realism_stream = serialize
restore_realism_stream = restore
get_realism_stream_identity = get_identity
get_realism_performance_budgets = get_performance_budgets
get_simulation_crash_points = get_points
create_recovery_state = create_state
recover_unknown_outcome = recover

"""Execution realism feature API."""

from app.services.simulator.realism.contracts import (
    LatencyProfile,
    QueueFillResult,
    QueueModel,
    RealisticExecutionResult,
    build_latency_profile,
    build_queue_model,
)
from app.services.simulator.realism.latency import project_latency_timestamps
from app.services.simulator.realism.pricing import price_realistic_execution
from app.services.simulator.realism.providers import build_fill_model_provider
from app.services.simulator.realism.queue import simulate_queue_fill
from app.services.simulator.realism.races import resolve_cancel_replace_race
from app.services.simulator.realism.views import project_execution_views

__all__ = [
    "LatencyProfile",
    "QueueFillResult",
    "QueueModel",
    "RealisticExecutionResult",
    "build_fill_model_provider",
    "build_latency_profile",
    "build_queue_model",
    "price_realistic_execution",
    "project_execution_views",
    "project_latency_timestamps",
    "resolve_cancel_replace_race",
    "simulate_queue_fill",
]

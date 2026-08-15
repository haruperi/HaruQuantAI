"""Supported Simulation execution API."""

from app.services.simulator.execution.engine import EventDrivenExecutionEngine
from app.services.simulator.execution.lifecycle import (
    build_lifecycle_deal,
    build_protection_projection,
    describe_lifecycle_race,
    deterministic_lifecycle_ticket,
    resolve_fill_remainder,
    resolve_order_expiration,
)
from app.services.simulator.execution.matching import (
    SAME_TICK_PRIORITY,
    SUPPORTED_FILL_POLICIES,
    MatchResult,
    evaluate_protective_exit,
    match_order,
)
from app.services.simulator.execution.pricing import (
    ExecutionProfile,
    SessionInterval,
    price_order,
)
from app.services.simulator.execution.provider_semantics import (
    is_provider_session_open,
    validate_provider_order,
)
from app.services.simulator.execution.trader import SimTrader

__all__ = [
    "SAME_TICK_PRIORITY",
    "SUPPORTED_FILL_POLICIES",
    "EventDrivenExecutionEngine",
    "ExecutionProfile",
    "MatchResult",
    "SessionInterval",
    "SimTrader",
    "build_lifecycle_deal",
    "build_protection_projection",
    "describe_lifecycle_race",
    "deterministic_lifecycle_ticket",
    "evaluate_protective_exit",
    "is_provider_session_open",
    "match_order",
    "price_order",
    "resolve_fill_remainder",
    "resolve_order_expiration",
    "validate_provider_order",
]

"""Compensation registry mapping action classes to plans.

Classes and functions:
    CompensationRegistry: Class. Provides CompensationRegistry behavior for execution workflows.
"""

from __future__ import annotations

from app.services.execution.compensation.base import CompensationPlan
from app.services.utils.logger import logger


class CompensationRegistry:
    """Registry mapping action classes (A-E) to compensation plans."""

    def __init__(self) -> None:
        self._registry: dict[str, type[CompensationPlan]] = {}

    def register(self, action_class: str, plan_class: type[CompensationPlan]) -> None:
        """Register a compensation plan for an action class."""
        self._registry[action_class] = plan_class
        logger.info(
            f"CompensationRegistry: registered {plan_class.__name__} "
            f"for action class {action_class}"
        )

    def get_plan(self, action_class: str, action_id: str) -> CompensationPlan | None:
        """Get a compensation plan instance for an action class."""
        plan_cls = self._registry.get(action_class)
        if plan_cls is None:
            return None
        return plan_cls(action_id)

    def has_plan(self, action_class: str) -> bool:
        """Perform the has_plan execution service operation."""
        return action_class in self._registry

    @property
    def registered_classes(self) -> list[str]:
        """Perform the registered_classes execution service operation."""
        return list(self._registry.keys())


# Default registry with standard mappings
default_registry = CompensationRegistry()

# Register default compensation plans
from app.services.execution.compensation.order_compensation import (
    OrderCompensationPlan,
)
from app.services.execution.compensation.position_compensation import (
    PositionCompensationPlan,
)

default_registry.register("C", OrderCompensationPlan)
default_registry.register("D", OrderCompensationPlan)
default_registry.register("C", PositionCompensationPlan)
default_registry.register("D", PositionCompensationPlan)
default_registry.register("E", PositionCompensationPlan)

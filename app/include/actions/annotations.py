"""Chart annotation action blocks."""

from __future__ import annotations

from app.host.logging import get_logger
from app.include.actions.base import ActionRecord

logger = get_logger(__name__)


class DrawDownArrowAction:
    """Action block to record a down arrow chart annotation."""

    def __init__(self, shift: int = 0) -> None:
        """Initialize down arrow action.

        Args:
            shift: Relative bar shift (default: 0).
        """
        self.shift = shift

    def execute(self) -> ActionRecord:
        """Execute down arrow annotation action."""
        logger.debug(
            "FR-SERVICES-ACTION-DRAW: DrawDownArrow(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_down_arrow",
            params={"shift": self.shift},
        )


class DrawUpArrowAction:
    """Action block to record an up arrow chart annotation."""

    def __init__(self, shift: int = 0) -> None:
        """Initialize up arrow action.

        Args:
            shift: Relative bar shift (default: 0).
        """
        self.shift = shift

    def execute(self) -> ActionRecord:
        """Execute up arrow annotation action."""
        logger.debug(
            "FR-SERVICES-ACTION-DRAW: DrawUpArrow(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_up_arrow",
            params={"shift": self.shift},
        )


class DrawVerticalLineAction:
    """Action block to record a vertical line chart annotation."""

    def __init__(self, shift: int = 0) -> None:
        """Initialize vertical line action.

        Args:
            shift: Relative bar shift (default: 0).
        """
        self.shift = shift

    def execute(self) -> ActionRecord:
        """Execute vertical line annotation action."""
        logger.debug(
            "FR-SERVICES-ACTION-DRAW: DrawVerticalLine(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_vertical_line",
            params={"shift": self.shift},
        )


def draw_down_arrow(shift: int = 0) -> ActionRecord:
    """Record a down arrow annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing down arrow.
    """
    action = DrawDownArrowAction(shift)
    return action.execute()


def draw_up_arrow(shift: int = 0) -> ActionRecord:
    """Record an up arrow annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing up arrow.
    """
    action = DrawUpArrowAction(shift)
    return action.execute()


def draw_vertical_line(shift: int = 0) -> ActionRecord:
    """Record a vertical line annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing vertical line.
    """
    action = DrawVerticalLineAction(shift)
    return action.execute()


__all__ = [
    "DrawDownArrowAction",
    "DrawUpArrowAction",
    "DrawVerticalLineAction",
    "draw_down_arrow",
    "draw_up_arrow",
    "draw_vertical_line",
]

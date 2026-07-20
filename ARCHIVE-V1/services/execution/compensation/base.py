"""Compensation plan base class (Playbook §13).

Classes and functions:
    CompensationPlan: Class. Provides CompensationPlan behavior for execution workflows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.services.utils.logger import logger


class CompensationPlan(ABC):
    """Abstract base for compensation plans."""

    def __init__(self, action_id: str, description: str = "") -> None:
        self.action_id = action_id
        self.description = description
        self._log_entries: list[dict[str, Any]] = []

    @abstractmethod
    def execute(self, context: dict[str, Any]) -> bool:
        """Execute the compensation action. Returns True on success."""

    @abstractmethod
    def validate(self, context: dict[str, Any]) -> bool:
        """Validate that compensation is applicable. Returns True if valid."""

    def log(self, entry: dict[str, Any]) -> None:
        """Log a compensation step entry."""
        self._log_entries.append(entry)
        logger.info(f"CompensationPlan[{self.action_id}]: {entry}")

    @property
    def log_entries(self) -> list[dict[str, Any]]:
        """Perform the log_entries execution service operation."""
        return list(self._log_entries)

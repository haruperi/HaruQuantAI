"""Degrade tool health status dynamically after consecutive timeouts.

This module implements:
- Dynamic tool health status degradation (TRD-FR-170)
"""

from typing import Literal

from loguru import logger

ToolStatus = Literal["HEALTHY", "DEGRADED", "FAILED"]


class ToolHealthMonitor:
    """Tracks and degrades tool/adapter health dynamically.

    Status is updated based on consecutive failures.
    """

    def __init__(self, failure_threshold: int = 3) -> None:
        """Initialize the tool health monitor.

        Args:
            failure_threshold: Consecutive failures before status becomes FAILED.
        """
        self._failure_threshold = max(1, failure_threshold)
        self._consecutive_failures = 0
        self._status: ToolStatus = "HEALTHY"

    def record_success(self) -> None:
        """Record a successful tool execution.

        Resets consecutive failure counter and restores status to HEALTHY.
        """
        if self._status != "HEALTHY":
            logger.info("Tool health restored to HEALTHY.")
        self._consecutive_failures = 0
        self._status = "HEALTHY"

    def record_failure(self, error_message: str = "") -> None:
        """Record a tool execution timeout or adapter failure.

        Increments consecutive failures and degrades status accordingly.

        Args:
            error_message: Optional error context detail.
        """
        self._consecutive_failures += 1
        previous_status = self._status

        if self._consecutive_failures >= self._failure_threshold:
            self._status = "FAILED"
        else:
            self._status = "DEGRADED"

        if self._status != previous_status:
            logger.warning(
                "Tool health status transitioned from {} to {} due to consecutive "
                "failures (count: {}). Error: {}",
                previous_status,
                self._status,
                self._consecutive_failures,
                error_message,
            )

    @property
    def status(self) -> ToolStatus:
        """Get the current tool health status.

        Returns:
            ToolStatus: "HEALTHY", "DEGRADED", or "FAILED".
        """
        return self._status

    @property
    def consecutive_failures(self) -> int:
        """Get the current count of consecutive failures.

        Returns:
            int: Failure count.
        """
        return self._consecutive_failures

    @property
    def is_healthy(self) -> bool:
        """Check if the tool is healthy.

        Returns:
            bool: True if HEALTHY.
        """
        return self._status == "HEALTHY"

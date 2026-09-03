"""Configuration for Tick Normalization feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TickNormalizationConfig:
    """Runtime configuration for the tick normalization feature.

    Attributes:
        max_batch_size: Maximum allowed number of ticks in a single batch.
    """

    max_batch_size: int = 1_000_000

    def __post_init__(self) -> None:
        """Validate configuration limits.

        Raises:
            ValueError: If max_batch_size is not a positive integer.
        """
        if self.max_batch_size <= 0:
            msg = "max_batch_size must be a positive integer"
            raise ValueError(msg)

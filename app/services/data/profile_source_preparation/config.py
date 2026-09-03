"""Configuration for Volume Profile Source Preparation feature."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ProfileSourcePreparationConfig:
    """Runtime configuration for Volume Profile Source Preparation feature.

    Attributes:
        default_price_step: Default price step increment if unspecified.
        default_bin_count: Default target number of price bins.
        min_price_step: Minimum allowable price step.
        max_bin_count: Maximum allowable number of price bins.
        require_session_alignment: Whether session boundary alignment is required.
    """

    default_price_step: Decimal = Decimal("0.01")
    default_bin_count: int | None = None
    min_price_step: Decimal = Decimal("0.00000001")
    max_bin_count: int = 10_000
    require_session_alignment: bool = True

    def __post_init__(self) -> None:
        """Validate configuration settings.

        Raises:
            ValueError: If settings are out of valid bounds.
        """
        if self.default_price_step <= Decimal(0):
            msg = "default_price_step must be a positive decimal"
            raise ValueError(msg)
        if self.min_price_step <= Decimal(0):
            msg = "min_price_step must be a positive decimal"
            raise ValueError(msg)
        if self.default_bin_count is not None and self.default_bin_count <= 0:
            msg = "default_bin_count must be a positive integer if provided"
            raise ValueError(msg)
        if self.max_bin_count <= 0:
            msg = "max_bin_count must be a positive integer"
            raise ValueError(msg)
        if (
            self.default_bin_count is not None
            and self.default_bin_count > self.max_bin_count
        ):
            msg = "default_bin_count cannot exceed max_bin_count"
            raise ValueError(msg)

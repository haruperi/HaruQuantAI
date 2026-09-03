"""Configuration for Run Data Binding feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunDataBindingConfig:
    """Runtime configuration for Run Data Binding feature.

    Attributes:
        strict_precision_check: Whether precision requirements are strictly enforced.
        allow_synthetic_sources: Whether synthetic/scenario data versions can be bound.
        require_committed_status: Whether only committed versions may be bound.
        supported_precisions: Tuple of supported simulation precision identifiers.
    """

    strict_precision_check: bool = True
    allow_synthetic_sources: bool = True
    require_committed_status: bool = True
    supported_precisions: tuple[str, ...] = (
        "SELECTED_TIMEFRAME",
        "M1_SIMULATION",
        "REAL_TICK_CUSTOM_SPREAD",
        "REAL_TICK_RECORDED_SPREAD",
    )

    def __post_init__(self) -> None:
        """Validate configuration settings.

        Raises:
            ValueError: If settings are out of valid bounds.
        """
        if not self.supported_precisions:
            msg = "supported_precisions cannot be empty"
            raise ValueError(msg)

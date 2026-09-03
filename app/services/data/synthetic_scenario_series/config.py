"""Configuration for Synthetic and Scenario Series feature."""

from __future__ import annotations

from dataclasses import dataclass, field

_VALID_MODELS: frozenset[str] = frozenset({"gbm", "constant", "random_walk"})
_VALID_TRANSFORMS: frozenset[str] = frozenset(
    {"SHOCK", "GAP", "VOLATILITY", "LIQUIDITY", "OUTAGE", "MISSINGNESS"}
)


@dataclass(frozen=True)
class SyntheticScenarioSeriesConfig:
    """Runtime configuration for Synthetic and Scenario Series feature.

    Attributes:
        max_records: Maximum allowable records generated per request.
        default_model: Default synthetic model algorithm identifier.
        default_rounding: Rounding mode applied to generated prices/volumes.
        supported_transform_types: Set of supported scenario transformation
            types.
    """

    max_records: int = 250_000
    default_model: str = "gbm"
    default_rounding: str = "ROUND_HALF_EVEN"
    supported_transform_types: frozenset[str] = field(
        default_factory=lambda: _VALID_TRANSFORMS
    )

    def __post_init__(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If configuration values are out of bounds or invalid.
        """
        if self.max_records <= 0:
            msg = "max_records must be a positive integer"
            raise ValueError(msg)

        if self.default_model not in _VALID_MODELS:
            valid = sorted(_VALID_MODELS)
            msg = f"default_model must be one of {valid}"
            raise ValueError(msg)

        if not self.supported_transform_types.issubset(_VALID_TRANSFORMS):
            invalid = self.supported_transform_types - _VALID_TRANSFORMS
            msg = f"supported_transform_types contains invalid transforms: {invalid}"
            raise ValueError(msg)

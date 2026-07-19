"""Bounded immutable registry for Research metric-family calculators."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
import pandas as pd

from app.utils import logger
from app.utils.errors import ValidationError

_FAMILIES = (
    "returns",
    "roc",
    "candles",
    "ranges",
    "volatility",
    "spread",
    "activity",
)


@dataclass(frozen=True, slots=True)
class MetricContext:
    """Internal immutable view of one prepared analytical frame."""

    data: pd.DataFrame

    def __post_init__(self) -> None:
        """Detach metric input from caller mutation."""
        logger.debug("Detaching Research metric context")
        object.__setattr__(self, "data", self.data.copy(deep=True))


@dataclass(frozen=True, slots=True)
class MetricValue:
    """Internal normalized value for one metric family."""

    name: str
    value: float | None
    unit: str
    sample_size: int
    undefined_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate normalized metric evidence.

        Raises:
            ValidationError: If metric metadata is contradictory.
        """
        logger.debug("Validating normalized Research metric value")
        if not self.name or not self.unit or self.sample_size < 0:
            raise ValidationError("RES_INPUT_INVALID", "INVALID_METRIC_VALUE")
        if self.value is None and self.undefined_reason is None:
            raise ValidationError("RES_INPUT_INVALID", "UNDEFINED_REASON_REQUIRED")
        if self.value is not None and not np.isfinite(self.value):
            raise ValidationError("RES_NONFINITE_DATA", "METRIC_VALUE_NONFINITE")


@runtime_checkable
class MetricCalculator(Protocol):
    """Read-only calculator contract for one named metric family."""

    @property
    def family(self) -> str:
        """Return the exact metric family name.

        Raises:
            NotImplementedError: Protocol declaration has no implementation.
        """
        logger.debug("Reading Research metric calculator family")
        raise NotImplementedError

    def compute(self, context: MetricContext) -> tuple[MetricValue, ...]:
        """Compute normalized values from an immutable metric context.

        Args:
            context: Detached metric inputs.

        Raises:
            NotImplementedError: Protocol declaration has no implementation.
        """
        logger.debug(
            "Declaring Research metric computation for %d rows", len(context.data)
        )
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class _FamilyCalculator:
    """Focused calculator for one approved descriptive family."""

    family: str

    def compute(self, context: MetricContext) -> tuple[MetricValue, ...]:
        """Compute the configured descriptive family.

        Args:
            context: Detached metric inputs.

        Returns:
            One normalized family value.

        Raises:
            ValidationError: If required columns are missing.
        """
        logger.info("Computing Research metric family %s", self.family)
        data = context.data
        required = {"open", "high", "low", "close", "volume", "spread"}
        if not required <= set(data.columns):
            raise ValidationError("RES_INPUT_INVALID", "OHLCVS_COLUMNS_REQUIRED")
        close = data["close"].astype("float64")
        returns = np.log(close / close.shift(1)).dropna()
        calculations = {
            "returns": (
                float(returns.mean()) if not returns.empty else None,
                "ratio",
                len(returns),
            ),
            "roc": (
                float(close.iloc[-1] / close.iloc[0] - 1.0) if len(close) > 1 else None,
                "ratio",
                len(close),
            ),
            "candles": (
                float((data["close"] > data["open"]).mean()),
                "ratio",
                len(data),
            ),
            "ranges": (float((data["high"] - data["low"]).mean()), "price", len(data)),
            "volatility": (
                float(returns.std(ddof=1)) if len(returns) > 1 else None,
                "ratio",
                len(returns),
            ),
            "spread": (
                float(data["spread"].mean()),
                str(data.attrs.get("spread_unit", "price")),
                len(data),
            ),
            "activity": (float(data["volume"].mean()), "volume", len(data)),
        }
        value, unit, count = calculations[self.family]
        reason = None if value is not None else "insufficient_sample"
        return (MetricValue(self.family, value, unit, count, reason),)


@dataclass(frozen=True, slots=True)
class MetricRegistry:
    """Immutable ordered membership of unique metric calculators."""

    _calculators: tuple[MetricCalculator, ...]

    def __post_init__(self) -> None:
        """Validate bounded unique membership.

        Raises:
            ValidationError: If membership is empty, invalid, or duplicated.
        """
        logger.debug("Validating Research metric registry")
        if not self._calculators or any(
            not isinstance(item, MetricCalculator) for item in self._calculators
        ):
            raise ValidationError("RES_INPUT_INVALID", "INVALID_METRIC_CALCULATOR")
        families = tuple(item.family for item in self._calculators)
        if len(set(families)) != len(families):
            raise ValidationError("RES_INPUT_INVALID", "DUPLICATE_METRIC_FAMILY")

    @classmethod
    def from_calculators(
        cls, calculators: Iterable[MetricCalculator]
    ) -> MetricRegistry:
        """Construct one isolated registry from a bounded iterable.

        Args:
            calculators: Ordered calculator iterable.

        Returns:
            New immutable registry.

        Raises:
            ValidationError: If membership is invalid.
        """
        logger.info("Building isolated Research metric registry")
        return cls(tuple(calculators))

    def resolve(self, family: str) -> MetricCalculator:
        """Resolve a calculator by exact family.

        Args:
            family: Exact registered family.

        Returns:
            Matching calculator.

        Raises:
            ValidationError: If the family is absent.
        """
        logger.debug("Resolving Research metric family %s", family)
        for calculator in self._calculators:
            if calculator.family == family:
                return calculator
        raise ValidationError("RES_INPUT_INVALID", "METRIC_FAMILY_NOT_FOUND")

    def all(self) -> tuple[MetricCalculator, ...]:
        """Return calculators in deterministic registration order.

        Returns:
            Immutable calculator tuple.
        """
        logger.debug("Listing Research metric calculators")
        return self._calculators


def build_default_registry() -> MetricRegistry:
    """Build a fresh registry containing the exact seven metric families.

    Returns:
        Isolated default registry.
    """
    logger.info("Building default Research metric registry")
    return MetricRegistry.from_calculators(
        _FamilyCalculator(name) for name in _FAMILIES
    )


__all__ = ("MetricCalculator", "MetricRegistry", "build_default_registry")

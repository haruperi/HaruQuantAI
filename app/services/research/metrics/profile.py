"""Assembly of the versioned seven-family Research metric profile."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from app.services.research.contracts import CoreMetricProfile, ResearchWarning
from app.services.research.metrics.registry import MetricContext
from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from app.services.research.contracts import PreparedDataset, ResearchResourceLimits
    from app.services.research.metrics.registry import MetricRegistry

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
)


def build_core_metric_profile(
    prepared: PreparedDataset,
    *,
    registry: MetricRegistry,
    limits: ResearchResourceLimits,
) -> CoreMetricProfile:
    """Execute a registry and assemble complete seven-family evidence.

    Args:
        prepared: Prepared Research dataset.
        registry: Isolated metric registry.
        limits: Approved resource ceilings.

    Returns:
        Versioned metric profile with explicit undefined values and warnings.

    Raises:
        ValidationError: If resources or family membership are invalid.
    """
    logger.info("Building Research core metric profile")
    if len(prepared.data) > limits.max_rows:
        raise ValidationError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    metrics: dict[str, JSONValue] = {}
    warnings: list[ResearchWarning] = []
    context = MetricContext(prepared.data)
    for calculator in registry.all():
        values = calculator.compute(context)
        if len(values) != 1:
            raise ValidationError("RES_INPUT_INVALID", "ONE_VALUE_PER_FAMILY_REQUIRED")
        value = values[0]
        metrics[calculator.family] = cast(
            "JSONValue",
            {
                "value": value.value,
                "unit": value.unit,
                "sample_size": value.sample_size,
                "undefined_reason": value.undefined_reason,
            },
        )
        if value.value is None:
            warnings.append(
                ResearchWarning(
                    "METRIC_UNDEFINED",
                    "Metric could not be computed",
                    "warning",
                    calculator.family,
                    {"reason": value.undefined_reason},
                )
            )
    return CoreMetricProfile(
        "v1",
        cast("dict[str, Any]", metrics),
        prepared.quality,
        prepared.dataset_hash,
        prepared.configuration_hash,
        tuple(warnings),
    )


__all__ = ("build_core_metric_profile",)

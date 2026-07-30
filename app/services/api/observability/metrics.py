"""Metric naming, validation, and write helpers for API observability."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.api.observability.errors import SecurityError, ValidationError
from app.utils import is_sensitive_key

if TYPE_CHECKING:
    from app.services.api.observability.sinks import MetricSink

_METRIC_NAME_PATTERN = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
_TRUE_VALUES = frozenset({"1", "true", "t", "yes", "on", "enabled"})
_FALSE_VALUES = frozenset({"0", "false", "f", "no", "off", "disabled"})


def _to_bool_env(value: str, *, env_name: str) -> bool:
    """Parse one canonical boolean environment value.

    Args:
        value: Raw candidate value.
        env_name: Environment name for deterministic failure output.

    Returns:
        Parsed boolean.

    Raises:
        ValidationError: If the value is unsupported.
    """
    normalized = value.strip().casefold()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    msg = f"{env_name}_INVALID"
    raise ValidationError(msg)


def _metrics_enabled() -> bool:
    """Return whether metrics recording and exposition is enabled."""
    return _to_bool_env(
        os.getenv("METRICS_ENABLED", "false"),
        env_name="METRICS_ENABLED",
    )


def _validate_metric_name(name: str) -> str:
    """Validate one metric name.

    Args:
        name: Raw metric name.

    Returns:
        Validated metric name.

    Raises:
        ValidationError: If malformed.
    """
    if not isinstance(name, str):
        raise ValidationError("METRICS_NAME_MISSING")
    if not name.strip() or not _METRIC_NAME_PATTERN.fullmatch(name):
        raise ValidationError("METRICS_NAME_INVALID")
    return name


def _validate_metric_value(value: object) -> Decimal:
    """Validate one finite metric value.

    Args:
        value: Raw decimal value.

    Returns:
        Validated `Decimal` value.

    Raises:
        ValidationError: If non-finite or malformed.
    """
    if not isinstance(value, Decimal):
        raise ValidationError("METRICS_VALUE_INVALID")
    if not value.is_finite():
        raise ValidationError("METRICS_VALUE_INVALID")
    return value


def validate_metric_labels(labels: Mapping[str, str]) -> None:
    """Reject sensitive or malformed metric labels before sink mutation.

    Raises:
        SecurityError: If the declared validation fails.
        ValidationError: If the declared validation fails.
    """
    if not isinstance(labels, Mapping):
        raise ValidationError("METRICS_LABELS_MALFORMED")
    for key, value in labels.items():
        if not isinstance(key, str):
            raise ValidationError("METRICS_LABEL_KEY_INVALID")
        normalized_key = key.strip()
        if not normalized_key:
            raise ValidationError("METRICS_LABEL_KEY_INVALID")
        if is_sensitive_key(normalized_key):
            raise SecurityError(
                "METRICS_LABEL_INVALID",
                "SENSITIVE_LABEL_KEY",
            )
        if not isinstance(value, str):
            raise ValidationError("METRICS_LABEL_VALUE_INVALID")
        if not str(value).strip():
            raise ValidationError("METRICS_LABEL_VALUE_INVALID")


def record_metric(
    name: str,
    value: Decimal,
    *,
    labels: Mapping[str, str],
    sink: MetricSink,
) -> None:
    """Record one validated observation through an explicitly injected sink."""
    if not _metrics_enabled():
        return
    validated_name = _validate_metric_name(name)
    validated_value = _validate_metric_value(value)
    validate_metric_labels(labels)
    normalized_labels = {
        str(key).strip(): str(val).strip() for key, val in labels.items()
    }
    sink.validate_labels(normalized_labels)
    sink.record(
        validated_name,
        validated_value,
        labels=normalized_labels,
    )


__all__ = (
    "record_metric",
    "validate_metric_labels",
)

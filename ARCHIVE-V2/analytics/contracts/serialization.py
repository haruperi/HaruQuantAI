"""Serialization helpers for canonical JSON formatting and safe float validation.

This module owns helpers to convert arbitrarily nested structures into standard,
JSON-serializable types and generate canonical sorted JSON strings.
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.analytics.contracts.models import PrecisionPolicy

# JSON serializable value type alias
type JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


def to_json_safe(  # noqa: C901, PLR0911, PLR0912
    value: Any,  # noqa: ANN401
    precision: PrecisionPolicy,
) -> JsonValue:
    """Recursively convert any python object to a JSON-safe format (ANL-NFR-433).

    Args:
        value (Any): Input parameter `value`.
        precision (PrecisionPolicy): Input parameter `precision`.

    Returns:
        Calculated JsonValue value.
    """
    logger.debug("to_json_safe: executed.")
    if value is None:
        return None

    # Handle pandas structures
    if pd is not None:
        if isinstance(value, pd.DataFrame):
            return to_json_safe(value.to_dict(orient="records"), precision)
        if isinstance(value, pd.Series):
            return to_json_safe(value.tolist(), precision)

    # Handle numpy structures
    if np is not None:
        if isinstance(value, np.ndarray):
            return to_json_safe(value.tolist(), precision)
        if isinstance(value, np.generic):
            return to_json_safe(value.item(), precision)

    # Handle Decimal
    if isinstance(value, Decimal):
        if precision.monetary_precision_mode == "decimal_precise":
            return str(value)
        # Default/float64_with_tolerance conversion
        val_float = float(value)
        if not math.isfinite(val_float):
            msg = "Non-finite Decimal encountered during serialization."
            raise ValidationError(msg)
        return val_float

    # Handle float
    if isinstance(value, float):
        if not math.isfinite(value):
            msg = "Non-finite float (NaN/inf) encountered during serialization."
            raise ValidationError(msg)
        return value

    # Handle other primitives
    if isinstance(value, (bool, int, str)):
        return value

    # Handle dataclasses
    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict

        return to_json_safe(asdict(value), precision)

    # Handle dict / mappings
    if isinstance(value, dict) or hasattr(value, "keys"):
        new_dict = {}
        for k, v in value.items():
            new_dict[str(k)] = to_json_safe(v, precision)
        return new_dict

    # Handle lists, tuples, sets, sequences
    if isinstance(value, (list, tuple, set)) or hasattr(value, "__iter__"):
        return [to_json_safe(item, precision) for item in value]

    try:
        return str(value)
    except Exception as e:
        msg = f"Unserializable object of type {type(value).__name__}: {value!r}"
        raise ValidationError(msg) from e


def canonical_json(value: JsonValue) -> str:
    """Generate sorted, whitespace-free canonical JSON representation (ANL-NFR-433).

    Args:
        value (JsonValue): Input parameter `value`.

    Returns:
        Calculated str value.
    """
    logger.debug("canonical_json: executed.")
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

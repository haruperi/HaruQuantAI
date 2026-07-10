"""Risk governance contracts serialization.

Provides canonical serialization helpers, payload validation,
and round-trip verification for risk contracts crossing system boundaries.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, TypeVar

from app.utils.contract import Contract
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.utils.validations import ValidationResult

RiskModelT = TypeVar("RiskModelT", bound=Contract)


def to_canonical_risk_payload(model: Contract) -> dict[str, object]:
    """Emit stable, JSON-safe fields for a canonical risk model.

    Converts Decimal values to float, datetime values to ISO 8601 strings,
    and returns a clean Python dictionary.

    Args:
        model: The risk contract model instance to serialize.

    Returns:
        dict[str, object]: A JSON-safe dictionary representation of the model.
    """
    logger.debug("Serializing canonical payload for model: %s", type(model).__name__)
    data = model.model_dump()
    payload = _coerce_types(data)
    logger.info(
        "Successfully serialized model: %s to canonical payload.", type(model).__name__
    )
    return payload  # type: ignore[return-value]


def from_canonical_risk_payload(
    payload: Mapping[str, object], model_type: type[RiskModelT]
) -> RiskModelT:
    """Validate and restore a known model type.

    Args:
        payload: The JSON-safe dictionary representation of the model.
        model_type: The Pydantic contract class type to instantiate.

    Returns:
        RiskModelT: The validated and restored model instance.
    """
    logger.debug("Restoring model %s from canonical payload.", model_type.__name__)
    model = model_type.model_validate(payload)
    logger.info("Successfully restored model %s from payload.", model_type.__name__)
    return model


def validate_risk_model_round_trip(model: Contract) -> ValidationResult:
    """Verifies canonicalization and round-trip integrity for a risk model.

    Converts the model to a payload, restores it, and asserts equality.

    Args:
        model: The risk contract model instance to verify.

    Returns:
        ValidationResult: The validation result dictionary.
    """
    logger.debug("Starting round-trip validation for %s", type(model).__name__)
    try:
        payload = to_canonical_risk_payload(model)
        restored = from_canonical_risk_payload(payload, type(model))

        if restored == model:
            logger.info("Round-trip validation passed for %s.", type(model).__name__)
            return {
                "valid": True,
                "message": f"Round-trip validation passed for {type(model).__name__}.",
                "code": "OK",
                "details": {},
            }
        logger.warning(
            "Round-trip mismatch for %s. Original and restored differ.",
            type(model).__name__,
        )
        return {
            "valid": False,
            "message": f"Round-trip validation failed for {type(model).__name__}.",
            "code": "ROUND_TRIP_MISMATCH",
            "details": {
                "original": model.model_dump_json(),
                "restored": restored.model_dump_json(),
            },
        }
    except Exception as e:  # noqa: BLE001
        logger.error(
            "Round-trip validation error for %s: %s",
            type(model).__name__,
            str(e),
            exc_info=True,
        )
        return {
            "valid": False,
            "message": f"Round-trip validation error: {e!s}",
            "code": "ROUND_TRIP_ERROR",
            "details": {"exception": str(e)},
        }


def _coerce_types(v: object) -> object:
    """Recursively convert datetime to ISO string and Decimal to float.

    Args:
        v: Value to coerce.

    Returns:
        object: Coerced value.
    """
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _coerce_types(val) for k, val in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_coerce_types(val) for val in v]
    return v

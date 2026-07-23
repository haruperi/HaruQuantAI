"""Private validation helpers shared by canonical DATA request boundaries."""

from app.services.data.contracts.errors import DataError
from app.utils import ValidationError as UtilsValidationError
from app.utils import generate_id, logger, validate_id

_LEGACY_REQ_ID_LEN = 68


def validate_request_id(value: str | None) -> None:
    """Validate a DATA request identifier against the shared trace policy.

    Args:
        value: Request identifier, or ``None`` when no trace identity is carried.

    Raises:
        ValueError: If the identifier is neither a prefixed UUID4 nor stable ID.
    """
    logger.debug("Validating DATA request identifier")
    if value is None:
        return
    try:
        validate_id(value, expected_prefix="req")
    except UtilsValidationError as error:
        if value.startswith("req-") and len(value) == _LEGACY_REQ_ID_LEN:
            return
        raise ValueError("request_id must be a prefixed UUID4 or stable ID") from error


def resolve_request_id(value: str | None) -> str:
    """Return an explicit request identifier or generate one.

    Args:
        value: Caller-supplied identifier, or ``None``.

    Returns:
        The supplied identifier or a newly generated identifier.
    """
    return value if value is not None else generate_id("req")


def reject_mixed_call_styles(
    request: object | None,
    values: tuple[object | None, ...],
    request_id: str,
) -> None:
    """Reject combining a typed request with direct keyword arguments.

    Args:
        request: Typed request contract, or ``None``.
        values: Direct keyword values supplied beside the request.
        request_id: Trace identifier for a failure.

    Raises:
        DataError: If both supported call styles are mixed.
    """
    if request is not None and any(value is not None for value in values):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "request objects cannot be mixed with keywords"},
            request_id=request_id,
        )


def require_direct_value(value: str | None, field: str, request_id: str) -> str:
    """Return a value required by the direct keyword call style.

    Args:
        value: Supplied value, or ``None``.
        field: Field name reported in safe error details.
        request_id: Trace identifier for a failure.

    Returns:
        The supplied value.

    Raises:
        DataError: If the required value is absent.
    """
    if value is None:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": field},
            request_id=request_id,
        )
    return value


__all__: list[str] = []

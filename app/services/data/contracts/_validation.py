"""Private shared DATA contract-boundary validation helpers."""

from app.utils import ValidationError as UtilsValidationError
from app.utils import logger, validate_id


def validate_request_id(value: str | None) -> None:
    """Validate a DATA request identifier against the shared trace policy."""
    logger.debug("Validating DATA request identifier")
    if value is None:
        return
    try:
        validate_id(value, expected_prefix="req")
    except UtilsValidationError as error:
        raise ValueError("request_id must be a prefixed UUID4 or stable ID") from error


__all__: list[str] = []

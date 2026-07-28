"""Private shared identity checks for Trading action modules."""

from typing import TYPE_CHECKING, cast

from pydantic import BaseModel

from app.services.trading.contracts import TradingError, TradingRequest
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.trading.contracts.models import JsonValue


def authority_id(request: TradingRequest) -> str:
    """Return the exact selected authority identity.

    Args:
        request: Canonical Trading request.

    Returns:
        Provider identity or the Simulation authority name.
    """
    logger.debug("Resolving Trading request authority identity")
    return request.provider_id or "simulation"


def require_action(request: TradingRequest, action: str) -> None:
    """Require one exact public action identity.

    Args:
        request: Canonical request.
        action: Required action value.

    Raises:
        TradingError: If action identity differs.
    """
    logger.debug("Checking Trading action identity %s", action)
    if request.action != action:
        raise TradingError("INVALID_REQUEST", "Trading action mismatches verb")


def response_data_json(value: object) -> JsonValue:
    """Convert a standard response's raw DTO data to JSON-safe evidence.

    Args:
        value: Raw response data, optionally a Pydantic DTO.

    Returns:
        JSON-safe raw result evidence.
    """
    if isinstance(value, BaseModel):
        return cast("JsonValue", value.model_dump(mode="json"))
    return cast("JsonValue", value)


__all__: tuple[str, ...] = ()

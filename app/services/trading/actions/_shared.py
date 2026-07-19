"""Private shared identity checks for Trading action modules."""

from app.services.trading.contracts import TradingError, TradingRequest
from app.utils import logger


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


__all__: tuple[str, ...] = ()

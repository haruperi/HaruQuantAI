"""Point-in-time OperatingEnvelope evaluation."""

from collections.abc import Mapping
from decimal import Decimal

from app.services.strategy.operating_envelope.models import parse_operating_envelope
from app.utils import get_logger

logger = get_logger(__name__)


def evaluate_operating_envelope(
    envelope: Mapping[str, object],
    *,
    volatility: Decimal | None,
    spread: Decimal | None,
    liquidity: Decimal | None,
    regime: str | None,
    session: str | None,
    active_event_types: tuple[str, ...] | None,
) -> str:
    """Return PERMITTED only when all required current evidence passes."""
    parsed = parse_operating_envelope(envelope)
    if None in (volatility, spread, liquidity, regime, session, active_event_types):
        logger.warning("Operating-envelope evidence incomplete")
        return "RESTRICTED"
    if (
        volatility is None
        or spread is None
        or liquidity is None
        or regime is None
        or session is None
        or active_event_types is None
    ):
        return "RESTRICTED"
    permitted = (
        volatility <= Decimal(str(parsed["max_volatility"]))
        and spread <= Decimal(str(parsed["max_spread"]))
        and liquidity >= Decimal(str(parsed["min_liquidity"]))
        and regime in parsed["permitted_regimes"]
        and session in parsed["permitted_sessions"]
        and not set(active_event_types).intersection(parsed["blocked_event_types"])
    )
    return "PERMITTED" if permitted else "RESTRICTED"


__all__ = ["evaluate_operating_envelope"]

"""Shadow-routing execution comparison primitives.

Shadow mode execution records order intents and compares expected fills
against live market quotes and account balances without ever dispatching a
broker mutation (TRD-FR-125). This module performs no broker calls; it is
pure comparison logic driven entirely by caller-supplied evidence.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.trading.contracts import JsonObject, TradingContract
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger
from pydantic import Field, model_validator

BPS_DENOMINATOR = Decimal(10_000)


class ShadowIntentRecord(TradingContract):
    """Recorded shadow-route order intent.

    Attributes:
        request_id: Unique request identifier.
        symbol: Instrument symbol.
        side: Trade direction (e.g. ``buy``/``sell``).
        volume: Requested order volume.
        expected_price: Price the intent expected to fill at.
        recorded_at: UTC timestamp supplied by an injected Clock.
        payload: JSON-safe original intent payload.
    """

    request_id: str
    symbol: str
    side: str
    volume: Decimal = Field(gt=0)
    expected_price: Decimal = Field(gt=0)
    recorded_at: str
    payload: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self) -> ShadowIntentRecord:
        """Validate shadow intent record identifiers.

        Returns:
            ShadowIntentRecord: Validated shadow intent record.

        Raises:
            ValueError: If any required identifier field is blank.
        """
        logger.info("Validating shadow intent record for {}.", self.symbol)
        for field_name in ("request_id", "symbol", "side", "recorded_at"):
            if not getattr(self, field_name).strip():
                message = f"{field_name} must be non-empty."
                raise ValueError(message)
        return self


class ShadowFillComparison(TradingContract):
    """Comparison of a shadow intent against live market/account evidence.

    Attributes:
        request_id: Unique request identifier.
        symbol: Instrument symbol.
        expected_price: Price the intent expected to fill at.
        live_reference_price: Current live market reference price.
        price_drift: Signed live-minus-expected price difference.
        price_drift_bps: Price drift expressed in basis points.
        expected_balance_after: Account balance the intent expected after
            fill.
        live_balance: Current live account balance.
        balance_drift: Signed live-minus-expected balance difference.
    """

    request_id: str
    symbol: str
    expected_price: Decimal
    live_reference_price: Decimal
    price_drift: Decimal
    price_drift_bps: Decimal
    expected_balance_after: Decimal
    live_balance: Decimal
    balance_drift: Decimal


def record_shadow_intent(
    *,
    request_id: str,
    symbol: str,
    side: str,
    volume: Decimal,
    expected_price: Decimal,
    recorded_at: str,
    payload: JsonObject | None = None,
) -> ShadowIntentRecord:
    """Record a shadow-route order intent without dispatching to a broker.

    Args:
        request_id: Unique request identifier.
        symbol: Instrument symbol.
        side: Trade direction.
        volume: Requested order volume.
        expected_price: Price the intent expected to fill at.
        recorded_at: UTC timestamp supplied by an injected Clock.
        payload: Optional JSON-safe original intent payload.

    Returns:
        ShadowIntentRecord: Recorded shadow intent.
    """
    logger.info("Recording shadow intent {} for {}.", request_id, symbol)
    return ShadowIntentRecord(
        request_id=request_id,
        symbol=symbol,
        side=side,
        volume=volume,
        expected_price=expected_price,
        recorded_at=recorded_at,
        payload=payload or {},
    )


def compare_shadow_fill(
    *,
    intent: ShadowIntentRecord,
    live_reference_price: Decimal,
    expected_balance_after: Decimal,
    live_balance: Decimal,
) -> ShadowFillComparison:
    """Compare a recorded shadow intent against live quote/balance evidence.

    Args:
        intent: Previously recorded shadow intent.
        live_reference_price: Current live market reference price.
        expected_balance_after: Account balance the intent expected after
            fill.
        live_balance: Current live account balance.

    Returns:
        ShadowFillComparison: Price and balance drift comparison.

    Raises:
        TradingMappedError: If ``live_reference_price`` is not positive.
    """
    logger.info("Comparing shadow fill for {}.", intent.request_id)
    if live_reference_price <= 0:
        raise TradingMappedError(
            "live_reference_price must be positive.",
            code="INVALID_INPUT",
        )
    price_drift = live_reference_price - intent.expected_price
    price_drift_bps = (price_drift / intent.expected_price) * BPS_DENOMINATOR
    balance_drift = live_balance - expected_balance_after
    logger.debug(
        "Shadow fill drift for {}: price={} bps={} balance={}.",
        intent.request_id,
        price_drift,
        price_drift_bps,
        balance_drift,
    )
    return ShadowFillComparison(
        request_id=intent.request_id,
        symbol=intent.symbol,
        expected_price=intent.expected_price,
        live_reference_price=live_reference_price,
        price_drift=price_drift,
        price_drift_bps=price_drift_bps,
        expected_balance_after=expected_balance_after,
        live_balance=live_balance,
        balance_drift=balance_drift,
    )

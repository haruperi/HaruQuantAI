"""Function-only constructors for Strategy intent values."""

from app.services.strategy.intents.intent import TradeIntent


def create_trade_intent_value(**kwargs: object) -> TradeIntent:
    """Create one canonical immutable TradeIntent value.

    Args:
        **kwargs: Validated TradeIntent field values.

    Returns:
        Canonical immutable TradeIntent.
    """
    return TradeIntent.model_validate(kwargs)


__all__ = ["create_trade_intent_value"]

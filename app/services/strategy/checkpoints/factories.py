"""Function-only constructors for checkpoint contract values."""

from app.services.strategy.checkpoints.models import StrategyCheckpoint


def create_strategy_checkpoint_value(**kwargs: object) -> StrategyCheckpoint:
    """Create one immutable Strategy checkpoint value.

    Args:
        **kwargs: Validated Strategy checkpoint field values.

    Returns:
        Immutable Strategy checkpoint.
    """
    return StrategyCheckpoint.model_validate(kwargs)


__all__ = ["create_strategy_checkpoint_value"]

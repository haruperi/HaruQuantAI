"""Function-only constructors for replay contract values."""

from app.services.strategy.replay.models import StrategyReplayManifest


def create_strategy_replay_manifest_value(
    **kwargs: object,
) -> StrategyReplayManifest:
    """Create one immutable Strategy replay manifest value.

    Args:
        **kwargs: Validated replay-manifest field values.

    Returns:
        Immutable Strategy replay manifest.
    """
    return StrategyReplayManifest.model_validate(kwargs)


__all__ = ["create_strategy_replay_manifest_value"]

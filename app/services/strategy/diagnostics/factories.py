"""Function-only constructors for Strategy diagnostics values."""

from app.services.strategy.diagnostics.models import StrategyDiagnostics


def create_strategy_diagnostics(**kwargs: object) -> StrategyDiagnostics:
    """Create one immutable structured Strategy diagnostics value.

    Args:
        **kwargs: Validated Strategy diagnostics field values.

    Returns:
        Immutable structured Strategy diagnostics.
    """
    return StrategyDiagnostics.model_validate(kwargs)


__all__ = ["create_strategy_diagnostics"]

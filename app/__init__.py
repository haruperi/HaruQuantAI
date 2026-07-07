"""App module package for HaruQuantAI.

The root package keeps analytics helpers lazy so importing subpackages such as
``app.services.analytics.contracts`` does not recursively initialize the full
analytics public facade during test collection.
"""

from __future__ import annotations

from app.utils.logger import setup_logging

setup_logging()

__all__ = [
    "MetricDefinitionCatalog",
    "return_on_initial_capital",
    "total_return",
]


def __getattr__(name: str) -> object:
    """Lazily expose approved root compatibility exports.

    Args:
        name: Attribute requested from the root package.

    Returns:
        The requested public compatibility export.

    Raises:
        AttributeError: If ``name`` is not an approved root export.
    """
    if name in {"return_on_initial_capital", "total_return"}:
        from app.services.analytics.metrics.pnl import (
            return_on_initial_capital,
            total_return,
        )

        value = {
            "return_on_initial_capital": return_on_initial_capital,
            "total_return": total_return,
        }[name]
        globals()[name] = value
        return value
    if name == "MetricDefinitionCatalog":
        from app.services.analytics.contracts import MetricDefinitionCatalog

        globals()[name] = MetricDefinitionCatalog
        return MetricDefinitionCatalog
    message = f"module 'app' has no attribute {name!r}"
    raise AttributeError(message)

"""App module package for HaruQuantAI."""

from app.services.analytics import (
    return_on_initial_capital,
    total_return,
)
from app.services.analytics.contracts import MetricDefinitionCatalog
from app.utils.logger import setup_logging

setup_logging()

__all__ = [
    "return_on_initial_capital",
    "total_return",
    "MetricDefinitionCatalog",
]

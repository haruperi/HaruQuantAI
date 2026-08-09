"""Analytics record persistence statement builders."""

from app.services.analytics.persistence.create import build_analytics_insert
from app.services.analytics.persistence.read import build_analytics_select

__all__ = ("build_analytics_insert", "build_analytics_select")

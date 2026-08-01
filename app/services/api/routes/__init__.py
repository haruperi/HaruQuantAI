"""Documented UI/API HTTP routers for canonical composition."""

from app.services.api.routes.auth import router as auth_router
from app.services.api.routes.dashboards import router as dashboards_router
from app.services.api.routes.data import router as data_router
from app.services.api.routes.health import router as health_router
from app.services.api.routes.observability import router as observability_router
from app.services.api.routes.operator import router as operator_router
from app.services.api.routes.research import router as research_router
from app.services.api.routes.settings import router as settings_router
from app.services.api.routes.strategies import router as strategies_router

__all__ = (
    "auth_router",
    "dashboards_router",
    "data_router",
    "health_router",
    "observability_router",
    "operator_router",
    "research_router",
    "settings_router",
    "strategies_router",
)

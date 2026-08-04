"""Documented UI/API HTTP routers for canonical composition."""

from app.services.api.routes.agentic import router as agentic_router
from app.services.api.routes.auth import router as auth_router
from app.services.api.routes.dashboards import router as dashboards_router
from app.services.api.routes.data import router as data_router
from app.services.api.routes.data_stream import router as data_stream_router
from app.services.api.routes.health import router as health_router
from app.services.api.routes.observability import router as observability_router
from app.services.api.routes.operator import router as operator_router
from app.services.api.routes.optimization import router as optimization_router
from app.services.api.routes.portfolio import router as portfolio_router
from app.services.api.routes.research import router as research_router
from app.services.api.routes.risk import router as risk_router
from app.services.api.routes.settings import router as settings_router
from app.services.api.routes.simulation import router as simulation_router
from app.services.api.routes.simulation_sessions import (
    router as simulation_sessions_router,
)
from app.services.api.routes.strategies import router as strategies_router
from app.services.api.routes.trading import router as trading_router

__all__ = (
    "agentic_router",
    "auth_router",
    "dashboards_router",
    "data_router",
    "data_stream_router",
    "health_router",
    "observability_router",
    "operator_router",
    "optimization_router",
    "portfolio_router",
    "research_router",
    "risk_router",
    "settings_router",
    "simulation_router",
    "simulation_sessions_router",
    "strategies_router",
    "trading_router",
)

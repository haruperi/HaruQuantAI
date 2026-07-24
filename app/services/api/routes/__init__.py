"""Documented UI/API HTTP routers."""

from app.services.api.routes.research import router as research_router
from app.services.api.routes.strategies import router as strategies_router

__all__ = ("research_router", "strategies_router")

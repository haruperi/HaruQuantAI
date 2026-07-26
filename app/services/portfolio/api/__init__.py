"""Public Portfolio application boundary package."""

from app.services.portfolio.api.service import PortfolioService

__all__: tuple[str, ...] = ("PortfolioService",)

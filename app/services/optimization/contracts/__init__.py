"""Shared non-feature contracts for the Optimization domain."""

from app.services.optimization.contracts.errors import (
    OPTIMIZATION_ERROR_CATALOG,
    OptimizationError,
)

__all__ = ["OPTIMIZATION_ERROR_CATALOG", "OptimizationError"]

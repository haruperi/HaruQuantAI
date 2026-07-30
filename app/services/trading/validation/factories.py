"""Function-only construction for Trading validation evidence."""

from __future__ import annotations

from app.services.trading.validation.readiness import ReadinessAssessment
from app.services.trading.validation.snapshots import RouteSnapshot


def create_readiness_assessment(**values: object) -> ReadinessAssessment:
    """Construct one validated readiness assessment.

    Args:
        **values: Assessment field values.

    Returns:
        Validated internal assessment.
    """
    return ReadinessAssessment.model_validate(values)


def create_route_snapshot(**values: object) -> RouteSnapshot:
    """Construct one validated route snapshot.

    Args:
        **values: Snapshot field values.

    Returns:
        Validated internal snapshot.
    """
    return RouteSnapshot.model_validate(values)


__all__ = ["create_readiness_assessment", "create_route_snapshot"]

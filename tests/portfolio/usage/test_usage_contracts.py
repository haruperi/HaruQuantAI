"""Runnable Portfolio contract usage example."""

from __future__ import annotations

from typing import Any

from app.services.portfolio.contracts import PortfolioConstructionRequest
from app.utils import logger


def test_build_strict_construction_request(
    construction_request_data: dict[str, Any],
) -> None:
    """Build and serialize a public versioned construction request.

    Args:
        construction_request_data: Complete explicit request data.
    """
    logger.info("Running Portfolio construction request usage example")
    request = PortfolioConstructionRequest(**construction_request_data)
    wire_value = request.model_dump(mode="json")

    assert wire_value["contract_version"] == "v1"
    assert wire_value["schema_id"] == "portfolio.construction_request.v1"
    assert wire_value["components"][0]["strategy_id"] == "strategy-a"

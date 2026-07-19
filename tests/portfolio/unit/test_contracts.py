"""Unit tests for strict Portfolio boundary contracts."""

# ruff: noqa: INP001

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest
from app.services.portfolio.contracts import (
    FixedWeightInput,
    PortfolioComponentWeight,
    PortfolioConstructionRequest,
    PortfolioConstructionResult,
    PortfolioOutcome,
)
from app.services.portfolio.exceptions import PortfolioError, PortfolioErrorPayload
from app.utils import logger


def test_request_rejects_unknown_fields_and_unsafe_numbers(
    construction_request_data: dict[str, Any],
) -> None:
    """Verify strict input rejects unknown fields and binary floats.

    Args:
        construction_request_data: Complete request constructor data.
    """
    logger.info("Testing Portfolio strict unknown-field and numeric rejection")
    unknown = deepcopy(construction_request_data)
    unknown["unknown"] = object()
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioConstructionRequest(**unknown)

    fixed = deepcopy(construction_request_data)
    fixed["method"] = "fixed"
    fixed["fixed_weights"] = (
        {
            "component_id": "component-a",
            "capital_weight": 0.5,
            "proposed_risk_budget_weight": Decimal("0.5"),
        },
        {
            "component_id": "component-b",
            "capital_weight": Decimal("0.5"),
            "proposed_risk_budget_weight": Decimal("0.5"),
        },
    )
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioConstructionRequest(**fixed)


def test_request_serializes_version_schema_and_immutable_references(
    construction_request_data: dict[str, Any],
) -> None:
    """Verify version/schema separation and immutable owner references.

    Args:
        construction_request_data: Complete request constructor data.
    """
    logger.info("Testing Portfolio versioned immutable request serialization")
    request = PortfolioConstructionRequest(**construction_request_data)

    assert request.contract_version == "v1"
    assert request.schema_id == "portfolio.construction_request.v1"
    assert request.model_dump(mode="json")["scope"] == {
        "environment": "simulation",
        "tenant": "owner",
    }
    with pytest.raises(TypeError):
        request.scope["tenant"] = "changed"  # type: ignore[index]
    with pytest.raises(Exception, match="frozen"):
        request.portfolio_id = "changed"  # type: ignore[misc]


def test_request_requires_utc_ordering_and_compatible_route(
    construction_request_data: dict[str, Any],
) -> None:
    """Verify timestamps, ordering, and runtime route fail closed.

    Args:
        construction_request_data: Complete request constructor data.
    """
    logger.info("Testing Portfolio UTC, ordering, and route invariants")
    naive = deepcopy(construction_request_data)
    naive["requested_at"] = construction_request_data["requested_at"].replace(
        tzinfo=None
    )
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioConstructionRequest(**naive)

    unordered = deepcopy(construction_request_data)
    unordered["components"] = tuple(reversed(unordered["components"]))
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioConstructionRequest(**unordered)

    incompatible = deepcopy(construction_request_data)
    incompatible["execution_route"] = "live"
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioConstructionRequest(**incompatible)


def test_fixed_method_requires_complete_separate_weight_fields(
    construction_request_data: dict[str, Any],
) -> None:
    """Verify fixed capital and proposed Risk weights stay separate.

    Args:
        construction_request_data: Complete request constructor data.
    """
    logger.info("Testing separate Portfolio capital and proposed Risk weights")
    data = deepcopy(construction_request_data)
    data["method"] = "fixed"
    data["fixed_weights"] = tuple(
        FixedWeightInput(
            component_id=component,
            capital_weight=Decimal("0.5"),
            proposed_risk_budget_weight=Decimal("0.5"),
        )
        for component in ("component-a", "component-b")
    )

    request = PortfolioConstructionRequest(**data)

    assert request.fixed_weights[0].capital_weight == Decimal("0.5")
    assert request.fixed_weights[0].proposed_risk_budget_weight == Decimal("0.5")
    missing = deepcopy(data)
    missing["fixed_weights"] = data["fixed_weights"][:1]
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioConstructionRequest(**missing)


def test_result_requires_ordered_exact_weight_totals(
    construction_request_data: dict[str, Any],
) -> None:
    """Verify published results require deterministic exact totals.

    Args:
        construction_request_data: Complete request constructor data.
    """
    logger.info("Testing Portfolio result exact weight invariants")
    request = PortfolioConstructionRequest(**construction_request_data)
    weights = tuple(
        PortfolioComponentWeight(
            component_id=component.component_id,
            strategy_id=component.strategy_id,
            strategy_version=component.strategy_version,
            capital_weight=Decimal("0.5"),
            proposed_risk_budget_weight=Decimal("0.5"),
        )
        for component in request.components
    )
    result = PortfolioConstructionResult(
        result_id="result-1",
        portfolio_id=request.portfolio_id,
        portfolio_version=request.portfolio_version,
        scope=request.scope,
        status="constructed",
        component_weights=weights,
        method=request.method,
        config_hash="a" * 64,
        evidence_hash="b" * 64,
        strategy_lineage_hash="c" * 64,
        canonical_hash="d" * 64,
        created_at=request.requested_at,
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
    )

    assert result.status == "constructed"
    assert "risk_budget_projection_ref" not in type(result).model_fields
    invalid_weights = (
        weights[0].model_copy(update={"capital_weight": Decimal("0.6")}),
        weights[1],
    )
    invalid_result = result.model_dump(mode="json")
    invalid_result["scope"] = dict(result.scope)
    invalid_result["component_weights"] = invalid_weights
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioConstructionResult(**invalid_result)


def test_outcome_contains_exactly_one_value_or_error() -> None:
    """Verify public envelopes never represent ambiguous outcomes."""
    logger.info("Testing Portfolio operation envelope exclusivity")
    success = PortfolioOutcome[str](
        ok=True,
        request_id="req-1",
        correlation_id="corr-1",
        value="done",
    )
    failure = PortfolioOutcome[str](
        ok=False,
        request_id="req-1",
        correlation_id="corr-1",
        error=PortfolioErrorPayload("PORT_NOT_FOUND", "ALLOCATION"),
    )

    assert success.value == "done"
    assert failure.error is not None
    with pytest.raises(ValueError, match="exactly one"):
        PortfolioOutcome[str](
            ok=True,
            request_id="req-1",
            correlation_id="corr-1",
        )

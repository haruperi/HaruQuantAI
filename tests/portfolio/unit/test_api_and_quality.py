"""Unit tests for the typed public Portfolio service and quality boundary."""

# ruff: noqa: INP001

from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

import pytest
from app.services.portfolio.api import PortfolioService
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioConstructionRequest,
    PortfolioOutcome,
)
from app.services.portfolio.orchestration import PortfolioWorkflowService
from app.services.portfolio.state import PortfolioRepository, scope_key
from app.utils import AuthContext, logger
from tests.portfolio.unit.test_repository import FakePortfolioStore
from tests.portfolio.unit.test_workflows import _plan, _service


def _auth(now: datetime) -> AuthContext:
    """Build one already authenticated Utils context.

    Args:
        now: Stable UTC issuance time.

    Returns:
        Valid immutable authentication context.
    """
    logger.debug("Building Portfolio API authentication context")
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="owner-1",
        principal_type="USER",
        roles=("portfolio_owner",),
        permissions=("portfolio.manage",),
        scopes=("portfolio-alpha",),
        tenant_or_environment="simulation",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=now,
    )


class FailingWorkflow:
    """Workflow fake that raises an unexpected construction exception."""

    @staticmethod
    def construct(request: PortfolioConstructionRequest):
        """Raise one unexpected workflow error.

        Args:
            request: Construction request that triggered the failure.

        Raises:
            RuntimeError: Always, to verify the public exception boundary.
        """
        logger.error("Raising unexpected Portfolio API workflow failure")
        del request
        raise RuntimeError("private failure detail")


def test_public_methods_have_auth_context_and_optional_request_id() -> None:
    """Every governed public method carries the required context signature."""
    logger.info("Testing Portfolio public governed method signatures")
    for method_name in (
        "construct",
        "status",
        "activate",
        "assess_drift",
        "submit_rebalance",
        "recompute_measurement",
        "rollback",
        "history",
    ):
        signature = inspect.signature(getattr(PortfolioService, method_name))
        assert "auth_context" in signature.parameters
        assert signature.parameters["request_id"].default is None


def test_status_and_history_return_structured_non_null_outcomes(
    active_allocation: ActivePortfolioAllocation,
    portfolio_now: datetime,
) -> None:
    """Read operations return typed values and never nullable success."""
    logger.info("Testing Portfolio public read operation envelopes")
    store = FakePortfolioStore()
    store.allocations[
        (active_allocation.portfolio_id, active_allocation.allocation_version)
    ] = active_allocation
    store.histories[active_allocation.portfolio_id] = [active_allocation]
    store.active_scopes[scope_key(active_allocation.scope)] = (active_allocation, 1)
    repository = PortfolioRepository(store)
    service = PortfolioService(cast("PortfolioWorkflowService", object()), repository)
    auth = _auth(portfolio_now)
    status = service.status(
        active_allocation.portfolio_id,
        active_allocation.scope,
        auth,
    )
    history = service.history(active_allocation.portfolio_id, auth)
    assert status.ok is True
    assert status.value is active_allocation
    assert history.ok is True
    assert history.value == (active_allocation,)


def test_public_boundary_maps_unexpected_exception_without_detail_leak(
    construction_request_data: dict[str, object],
    portfolio_now: datetime,
) -> None:
    """Unexpected failures become the closed internal-error payload."""
    logger.info("Testing Portfolio public unexpected-failure mapping")
    auth = _auth(portfolio_now)
    construction_request_data.update(
        {
            "request_id": auth.request_id,
            "workflow_id": auth.workflow_id,
            "correlation_id": auth.correlation_id,
        }
    )
    request = PortfolioConstructionRequest(**construction_request_data)
    service = PortfolioService(
        cast("PortfolioWorkflowService", FailingWorkflow()),
        PortfolioRepository(FakePortfolioStore()),
    )
    outcome = service.construct(request, auth)
    assert isinstance(outcome, PortfolioOutcome)
    assert outcome.ok is False
    assert outcome.error is not None
    assert outcome.error.code == "PORT_INTERNAL_ERROR"
    assert "private" not in outcome.error.detail.lower()


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend.

    Returns:
        AnyIO backend name.
    """
    logger.debug("Selecting asyncio for Portfolio API tests")
    return "asyncio"


@pytest.mark.anyio
async def test_submit_rebalance_returns_structured_measured_outcome(
    active_allocation: ActivePortfolioAllocation,
    portfolio_now: datetime,
    portfolio_settings: PortfolioSettings,
) -> None:
    """The public async mutation returns measured truth in one envelope."""
    logger.info("Testing Portfolio public rebalance operation")
    workflows, _recorder, store = _service(
        active_allocation,
        portfolio_now,
        portfolio_settings,
    )
    service = PortfolioService(workflows, PortfolioRepository(store))
    auth = _auth(portfolio_now)
    plan = _plan(active_allocation, portfolio_now, portfolio_settings)
    outcome = await service.submit_rebalance(
        plan,
        account_evidence_ref="account-1",
        market_evidence_ref="market-1",
        fx_evidence_refs=(),
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        approval_token_ref="approval-token-ref-1",
        trading_request_id="trading-request-1",
        valid_until=portfolio_now + timedelta(minutes=5),
        auth_context=auth,
    )
    assert outcome.ok is True
    assert outcome.value is not None
    assert outcome.value.status == "measured"


def test_api_has_no_authentication_or_presentation_framework_imports() -> None:
    """Portfolio API remains independent of HTTP and authentication engines."""
    logger.info("Testing Portfolio API ownership import boundary")
    source = Path("app/services/portfolio/api.py").read_text(encoding="utf-8")
    for forbidden in ("fastapi", "flask", "django", "jwt", "oauth", "httpx"):
        assert forbidden not in source.lower()

"""Unit tests for the typed public Portfolio service and quality boundary."""

from __future__ import annotations

import ast
import inspect
from asyncio import run
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.composition.logging import get_logger
from app.contracts.common.models import create_auth_context, get_standard_response_type
from app.kernel.serialization import canonical_digest
from app.services.portfolio import (
    activate_portfolio,
    assess_portfolio_drift,
    construct_portfolio,
    create_portfolio_handle,
    create_portfolio_value,
    dump_portfolio_value,
    execute_portfolio_handle_operation,
    get_portfolio_definition,
    get_portfolio_error_catalog,
    get_portfolio_history,
    get_portfolio_status,
    get_portfolio_value_field,
    is_portfolio_handle,
    is_portfolio_value,
    persistence,
    recompute_portfolio_measurement,
    register_portfolio_definition,
    rollback_portfolio,
    submit_portfolio_rebalance,
    to_portfolio_error_payload,
)
from app.services.portfolio._settings import PortfolioSettings
from app.services.portfolio.api.service import PortfolioService
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioConstructionRequest,
)
from app.services.portfolio.orchestration import PortfolioWorkflowService
from app.services.portfolio.persistence import delete
from app.services.portfolio.state import PortfolioRepository, scope_key

from tests.portfolio.unit.test_repository import FakePortfolioStore
from tests.portfolio.unit.test_workflows import _plan, _service

AuthContext = Any
StandardResponse = get_standard_response_type()
logger = get_logger(__name__)

_PORTFOLIO_ROOT = Path(__file__).parents[3] / "app" / "services" / "portfolio"
_PERSISTENCE_ROOT = _PORTFOLIO_ROOT / "persistence"
_EXPECTED_PERSISTENCE_FILES = {
    "__init__.py",
    "create.py",
    "read.py",
    "update.py",
    "delete.py",
}
_EXPECTED_PERSISTENCE_EXPORTS = {
    "create_construction_record",
    "create_definition_record",
    "create_ledger_account_record",
    "create_ledger_batch_record",
    "create_plan_record",
    "create_portfolio_runtime_store",
    "read_active_allocation_record",
    "read_allocation_history_records",
    "read_allocation_record",
    "read_construction_record",
    "read_definition_record",
    "read_idempotency_record",
    "read_ledger_account_record",
    "read_ledger_batch_record",
    "read_ledger_entries_for_account",
    "read_plan_record",
    "read_plan_version_records",
    "update_active_allocation_record",
}
_DATA_RUNTIME_CALLS = {
    "build_portfolio_runtime_store",
    "execute_runtime_store_operation",
    "execute_runtime_store_transition",
}


def test_private_persistence_package_has_exact_crud_layout() -> None:
    """Enforce the documented private Portfolio persistence boundary."""
    logger.info("Testing Portfolio persistence package structure")
    assert {path.name for path in _PERSISTENCE_ROOT.glob("*.py")} == (
        _EXPECTED_PERSISTENCE_FILES
    )
    assert set(persistence.__all__) == _EXPECTED_PERSISTENCE_EXPORTS
    assert all(
        inspect.isfunction(getattr(persistence, name)) for name in persistence.__all__
    )
    assert delete.__all__ == []


def test_active_allocation_update_retains_one_atomic_transition() -> None:
    """Keep active-state CAS and immutable history in one Data transaction."""
    logger.info("Testing Portfolio atomic allocation persistence transition")
    source = inspect.getsource(persistence.update_active_allocation_record)
    assert source.count("_execute(") == 1
    assert "portfolio_allocation_versions" in source
    assert "portfolio_active_scopes" in source
    assert "portfolio_idempotency" in source
    assert "portfolio_audit_outbox" in source


def test_data_runtime_calls_are_confined_to_portfolio_persistence() -> None:
    """Prevent direct Data runtime-store access from Portfolio feature modules."""
    logger.info("Testing Portfolio runtime-store call ownership")
    violations: list[str] = []
    for path in _PORTFOLIO_ROOT.rglob("*.py"):
        if _PERSISTENCE_ROOT in path.parents:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name in _DATA_RUNTIME_CALLS:
                violations.append(f"{path}: {name}")
    assert not violations, violations


def test_portfolio_persistence_no_longer_uses_generic_runtime_records() -> None:
    """Require direct relational statements through Data transactions only."""
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in _PERSISTENCE_ROOT.glob("*.py")
    )
    assert "data_runtime_records" not in source
    assert "build_portfolio_runtime_store" not in source
    assert "execute_runtime_store_operation" not in source
    assert "execute_runtime_store_transition" not in source
    assert "execute_transaction" in source


def test_function_only_factories_and_opaque_handles(
    construction_result: object,
    portfolio_settings: PortfolioSettings,
) -> None:
    """Exercise every function-only value and handle boundary."""
    dumped = dump_portfolio_value(construction_result)
    assert dumped["portfolio_id"] == "portfolio-alpha"
    assert get_portfolio_value_field(construction_result, "portfolio_id") == (
        "portfolio-alpha"
    )
    assert is_portfolio_value(construction_result)
    assert is_portfolio_value(construction_result, "PortfolioConstructionResult")
    assert not is_portfolio_value(construction_result, "Unknown")
    with pytest.raises(ValueError, match="Unknown Portfolio value type"):
        create_portfolio_value("Unknown")
    with pytest.raises(ValueError, match="registered Portfolio value"):
        dump_portfolio_value(object())
    with pytest.raises(ValueError, match="registered Portfolio value"):
        get_portfolio_value_field(object(), "field")
    with pytest.raises(ValueError, match="Unknown Portfolio value field"):
        get_portfolio_value_field(construction_result, "_private")

    store = FakePortfolioStore()
    repository = create_portfolio_handle("PortfolioRepository", store)
    assert is_portfolio_handle(repository)
    assert is_portfolio_handle(repository, "PortfolioRepository")
    assert not is_portfolio_handle(repository, "Unknown")
    assert (
        execute_portfolio_handle_operation(
            repository,
            "history",
            "portfolio-alpha",
        )
        == ()
    )
    with pytest.raises(ValueError, match="Unknown Portfolio handle type"):
        create_portfolio_handle("Unknown")
    with pytest.raises(ValueError, match="registered Portfolio handle"):
        execute_portfolio_handle_operation(object(), "history")
    with pytest.raises(ValueError, match="Unsupported Portfolio handle operation"):
        execute_portfolio_handle_operation(repository, "activate_unknown")

    schedule = create_portfolio_value(
        "RebalanceSchedule",
        anchor_at=datetime(
            2026,
            7,
            19,
            12,
            0,
            tzinfo=portfolio_settings.portfolio_rebalance_schedule.anchor_at.tzinfo,
        ),
        interval_seconds=3600,
    )
    schedule_dump = dump_portfolio_value(schedule)
    assert schedule_dump["interval_seconds"] == 3600
    assert get_portfolio_error_catalog()["PORT_NOT_FOUND"].code == "PORT_NOT_FOUND"
    assert to_portfolio_error_payload("PORT_NOT_FOUND").data is not None


def test_standalone_public_operations_delegate_to_internal_service(
    portfolio_now: datetime,
) -> None:
    """Verify all standalone operations delegate without exporting a class."""
    service = PortfolioService(MagicMock(), MagicMock())
    marker = object()
    service.construct = MagicMock(return_value=marker)
    service.status = MagicMock(return_value=marker)
    service.activate = MagicMock(return_value=marker)
    service.assess_drift = MagicMock(return_value=marker)
    service.submit_rebalance = AsyncMock(return_value=marker)
    service.recompute_measurement = MagicMock(return_value=marker)
    service.rollback = MagicMock(return_value=marker)
    service.history = MagicMock(return_value=marker)
    auth = _auth(portfolio_now)

    assert construct_portfolio(service, marker, auth) is marker
    assert get_portfolio_status(service, "portfolio-alpha", {}, auth) is marker
    assert (
        activate_portfolio(
            service,
            marker,
            marker,
            marker,
            approval_attestation=None,
            approval_validation=None,
            expires_at=portfolio_now,
            idempotency_key="key",
            expected_predecessor=None,
            expected_revision=0,
            auth_context=auth,
        )
        is marker
    )
    assert (
        assess_portfolio_drift(
            service,
            marker,
            actual_exposures={},
            evidence_as_of=portfolio_now,
            risk_decision=marker,
            eligibility_decisions={},
            auth_context=auth,
        )
        is marker
    )
    assert (
        run(
            submit_portfolio_rebalance(
                service,
                marker,
                account_evidence_ref="account",
                market_evidence_ref="market",
                fx_evidence_refs=(),
                runtime_profile="simulation",
                execution_route="sim",
                approval_refs=(),
                approval_token_ref="token",
                trading_request_id="request",
                valid_until=portfolio_now,
                auth_context=auth,
            )
        )
        is marker
    )
    assert (
        recompute_portfolio_measurement(
            service,
            "plan",
            trading_request_id="request",
            auth_context=auth,
        )
        is marker
    )
    assert (
        rollback_portfolio(
            service,
            marker,
            marker,
            marker,
            rollback_of_version="v1",
            approval_attestation=None,
            approval_validation=None,
            expires_at=portfolio_now,
            idempotency_key="key",
            expected_predecessor=None,
            expected_revision=0,
            auth_context=auth,
        )
        is marker
    )
    assert get_portfolio_history(service, "portfolio-alpha", auth) is marker
    with pytest.raises(TypeError, match="PortfolioService handle"):
        construct_portfolio(object(), marker, auth)


def _auth(now: datetime) -> AuthContext:
    """Build one already authenticated Utils context.

    Args:
        now: Stable UTC issuance time.

    Returns:
        Valid immutable authentication context.
    """
    logger.debug("Building Portfolio API authentication context")
    return create_auth_context(
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
    assert isinstance(status, StandardResponse)
    assert status.status == "success"
    assert status.data is active_allocation
    assert history.status == "success"
    assert history.data == (active_allocation,)


def test_definition_registration_and_read_are_structured(
    portfolio_now: datetime,
) -> None:
    """Definition registration validates material and reaches the repository."""
    auth = _auth(portfolio_now)
    material = {
        "definition": {"objective": "balanced"},
        "scope": {"environment": "simulation"},
    }
    definition = create_portfolio_value(
        "PortfolioDefinition",
        portfolio_id="portfolio-alpha",
        portfolio_version="v1",
        scope=material["scope"],
        definition=material["definition"],
        canonical_hash=canonical_digest(material),
        request_id=auth.request_id,
        workflow_id=auth.workflow_id,
        correlation_id=auth.correlation_id,
        created_at=portfolio_now,
    )
    service = create_portfolio_handle(
        "PortfolioService",
        cast("PortfolioWorkflowService", MagicMock()),
        PortfolioRepository(FakePortfolioStore()),
    )
    registered = register_portfolio_definition(service, definition, auth)
    loaded = get_portfolio_definition(service, "portfolio-alpha", "v1", auth)
    assert registered.status == "success"
    assert registered.data == definition
    assert loaded.status == "success"
    assert loaded.data == definition

    conflicting = definition.model_copy(update={"canonical_hash": "f" * 64})
    rejected = register_portfolio_definition(service, conflicting, auth)
    assert rejected.status == "error"
    assert rejected.metadata.request_id == auth.request_id
    assert rejected.metadata.correlation_id == auth.correlation_id
    assert rejected.metadata.modifies_database is True


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
    assert isinstance(outcome, StandardResponse)
    assert outcome.status == "error"
    assert outcome.data is None
    assert outcome.error is not None
    assert outcome.error.code == "PORT_INTERNAL_ERROR"
    assert outcome.error.details["detail"] == "UNEXPECTED"
    assert "private" not in str(outcome.error.details).lower()


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
        trading_request_id="req-44444444-4444-4444-8444-444444444444",
        valid_until=portfolio_now + timedelta(minutes=5),
        auth_context=auth,
    )
    assert outcome.status == "success"
    assert outcome.data is not None
    assert outcome.data.status == "measured"
    assert outcome.metadata.places_trade is True


def test_api_has_no_authentication_or_presentation_framework_imports() -> None:
    """Portfolio API remains independent of HTTP and authentication engines."""
    logger.info("Testing Portfolio API ownership import boundary")
    source = Path("app/services/portfolio/api/service.py").read_text(encoding="utf-8")
    for forbidden in ("fastapi", "flask", "django", "jwt", "oauth", "httpx"):
        assert forbidden not in source.lower()

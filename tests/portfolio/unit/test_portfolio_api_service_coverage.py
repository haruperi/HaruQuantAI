"""Coverage expansion tests for Portfolio public API service."""

import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.portfolio.api.service import PortfolioService
from app.services.portfolio.exceptions import PortfolioError
from app.utils import AuthContext, generate_id


def _auth() -> AuthContext:
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="usr-1",
        principal_type="USER",
        roles=("portfolio_owner",),
        permissions=("portfolio.manage",),
        scopes=("portfolio-alpha",),
        tenant_or_environment="simulation",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=datetime.now(UTC),
    )


def test_portfolio_service_trace_validation() -> None:
    """Verify _trace checks auth context type and trace identity consistency."""
    auth = _auth()

    # Invalid AuthContext object -> PORT_INVALID_INPUT / AUTH_CONTEXT
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioService._trace("not-auth-context", None)  # type: ignore[arg-type]

    # Valid matching trace -> returns (request_id, correlation_id)
    req_id, cor_id = PortfolioService._trace(auth, None)
    assert req_id == auth.request_id
    assert cor_id == auth.correlation_id

    # Request ID mismatch -> PORT_INVALID_INPUT / TRACE_MISMATCH
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioService._trace(auth, generate_id("req"))

    # Command request_id mismatch
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioService._trace(auth, None, command_request_id=generate_id("req"))

    # Command workflow_id mismatch
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioService._trace(auth, None, command_workflow_id=generate_id("wf"))

    # Command correlation_id mismatch
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        PortfolioService._trace(auth, None, command_correlation_id=generate_id("cor"))


def test_portfolio_service_fallback_trace() -> None:
    """Verify _fallback_trace produces fallback trace identities."""
    req_id, cor_id = PortfolioService._fallback_trace(object(), None)
    assert isinstance(req_id, str)
    assert isinstance(cor_id, str)

    auth = _auth()
    req_id2, cor_id2 = PortfolioService._fallback_trace(auth, "caller-req-id")
    assert req_id2.startswith("req-")
    assert cor_id2 == auth.correlation_id


def test_portfolio_service_construct_and_status_outcomes() -> None:
    """
    Verify construct and status operations
    return success or failure envelopes.
    """
    mock_workflows = MagicMock()
    mock_repo = MagicMock()
    service = PortfolioService(mock_workflows, mock_repo)

    auth = _auth()
    req = MagicMock(
        request_id=auth.request_id,
        workflow_id=auth.workflow_id,
        correlation_id=auth.correlation_id,
    )

    # 1. construct success
    mock_workflows.construct.return_value = ("result-obj", "evidence-obj")
    outcome = service.construct(req, auth)
    assert outcome.status == "success"
    assert outcome.data == "result-obj"

    # 2. construct failure handling (exception)
    mock_workflows.construct.side_effect = PortfolioError(
        "PORT_INVALID_INPUT", "TEST_ERR"
    )
    err_outcome = service.construct(req, auth)
    assert err_outcome.status == "error"
    assert err_outcome.error is not None
    assert err_outcome.error.code == "PORT_INVALID_INPUT"

    # 3. status when no active allocation -> PORT_NOT_FOUND
    mock_repo.active.return_value = None
    status_err = service.status("port-1", {"scope": "test"}, auth)
    assert status_err.status == "error"
    assert status_err.error is not None
    assert status_err.error.code == "PORT_NOT_FOUND"

    # 4. status success
    mock_repo.active.return_value = ("alloc-obj", 1)
    status_ok = service.status("port-1", {"scope": "test"}, auth)
    assert status_ok.status == "success"
    assert status_ok.data == "alloc-obj"

    # 5. generic exception in _failure
    generic_err_outcome = PortfolioService._failure(
        ValueError("unexpected"),
        operation="portfolio.api.service.construct",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        start_time=time.perf_counter_ns(),
    )
    assert generic_err_outcome.status == "error"
    assert generic_err_outcome.error is not None
    assert generic_err_outcome.error.code == "PORT_INTERNAL_ERROR"


def test_portfolio_service_remaining_methods() -> None:
    """Verify remaining public operations on PortfolioService."""
    mock_workflows = MagicMock()
    mock_repo = MagicMock()
    service = PortfolioService(mock_workflows, mock_repo)
    auth = _auth()

    async def run_test() -> None:
        # assess_drift success
        mock_workflows.assess_drift.return_value = "drift-res"
        drift_ok = service.assess_drift(
            MagicMock(),
            actual_exposures={},
            evidence_as_of=datetime.now(UTC),
            risk_decision=MagicMock(),
            eligibility_decisions={},
            auth_context=auth,
        )
        assert drift_ok.status == "success"

        # submit_rebalance success
        plan_mock = MagicMock(
            request_id=auth.request_id,
            workflow_id=auth.workflow_id,
            correlation_id=auth.correlation_id,
        )
        mock_workflows.submit_rebalance = AsyncMock(return_value="submit-res")
        sub_ok = await service.submit_rebalance(
            plan_mock,
            account_evidence_ref="acc-ref",
            market_evidence_ref="mkt-ref",
            fx_evidence_refs=(),
            runtime_profile="simulation",
            execution_route="sim",
            approval_refs=(),
            approval_token_ref="tok-ref",
            trading_request_id="trd-1",
            valid_until=datetime.now(UTC),
            auth_context=auth,
        )
        assert sub_ok.status == "success"

        # recompute_measurement success
        mock_workflows.recompute_measurement.return_value = "recompute-res"
        recomp_ok = service.recompute_measurement(
            "plan-1", trading_request_id="trd-1", auth_context=auth
        )
        assert recomp_ok.status == "success"

        # rollback success
        candidate = MagicMock(
            request_id=auth.request_id,
            workflow_id=auth.workflow_id,
            correlation_id=auth.correlation_id,
        )
        mock_rollback_alloc = MagicMock(audit_ref="audit-rb-1")
        mock_workflows.rollback.return_value = mock_rollback_alloc
        rb_ok = service.rollback(
            candidate,
            MagicMock(),
            MagicMock(),
            rollback_of_version="v1",
            approval_attestation=None,
            approval_validation=None,
            expires_at=datetime.now(UTC),
            idempotency_key="idemp-1",
            expected_predecessor=None,
            expected_revision=0,
            auth_context=auth,
        )
        assert rb_ok.status == "success"

        # history success
        mock_repo.history.return_value = ("alloc-1", "alloc-2")
        hist_ok = service.history("port-1", auth)
        assert hist_ok.status == "success"

    import asyncio

    asyncio.run(run_test())

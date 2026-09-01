"""Integration evidence for durable Risk runtime state."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    data_settings_context,
    unwrap_data_response,
)
from app.services.risk import (
    build_risk_approval_state_store,
    build_risk_state_store,
    create_allocation_risk_decision,
    create_kill_switch_state,
    create_risk_approval_token,
    create_risk_audit_record,
    create_risk_decision_package,
    create_strategy_operational_eligibility_decision,
    execute_risk_state_store_operation,
    get_decision_state,
    run_risk_migrations,
)


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///risk-runtime.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _decision(version: str, predecessor: str | None) -> object:
    """Build one valid active allocation decision.

    Returns:
        Opaque Risk decision.
    """
    now = datetime(2026, 8, 1, tzinfo=UTC)
    return create_allocation_risk_decision(
        decision_id=f"decision-{version}",
        portfolio_id="portfolio-one",
        reviewed_version=version,
        state=get_decision_state("approve"),
        capped_weights={"strategy-one": Decimal("0.5")},
        risk_budget_projection={"max_drawdown": Decimal("0.05")},
        conditions=(),
        policy_version="v1",
        evidence_refs={"market": "evidence-one"},
        issued_at=now,
        expires_at=now + timedelta(days=1),
        active=True,
        predecessor_version=predecessor,
        audit_ref="audit-one",
    )


def _run_risk_migrations() -> None:
    """Apply the isolated Risk-owned schema through Data."""
    request_id = generate_id("req")
    unwrap_data_response(
        run_risk_migrations(request_id),
        operation="tests.risk.migrations",
        request_id=request_id,
    )


def test_risk_allocation_state_is_durable_and_guarded(tmp_path: Path) -> None:
    """Allocation activation survives reconstruction and checks predecessors."""
    with data_settings_context(_settings(tmp_path)):
        _run_risk_migrations()
        store = build_risk_state_store()
        first = _decision("v1", None)
        assert execute_risk_state_store_operation(
            store,
            "save_review_if_absent",
            first,
            timeout_seconds=None,
        )
        assert execute_risk_state_store_operation(
            store,
            "activate_compare_and_swap",
            first,
            expected_predecessor_version=None,
            timeout_seconds=None,
        )
        reconstructed = build_risk_state_store()
        active = execute_risk_state_store_operation(
            reconstructed,
            "get_active",
            "portfolio-one",
            timeout_seconds=None,
        )
        assert active == first
        second = _decision("v2", "v1")
        assert not execute_risk_state_store_operation(
            reconstructed,
            "activate_compare_and_swap",
            second,
            expected_predecessor_version="wrong",
            timeout_seconds=None,
        )
        assert execute_risk_state_store_operation(
            reconstructed,
            "activate_compare_and_swap",
            second,
            expected_predecessor_version="v1",
            timeout_seconds=None,
        )


def test_risk_decision_audit_eligibility_and_kill_state_are_relational(
    tmp_path: Path,
) -> None:
    """Persist Risk evidence through its owned relational tables."""
    with data_settings_context(_settings(tmp_path)):
        _run_risk_migrations()
        now = datetime(2026, 8, 1, tzinfo=UTC)
        store = build_risk_state_store()
        eligibility = create_strategy_operational_eligibility_decision(
            decision_id="eligibility-one",
            strategy_id="strategy-one",
            strategy_version="v1",
            scope={"symbol": "EURUSD"},
            state=get_decision_state("approve"),
            conditions=(),
            policy_version="v1",
            evidence_refs={"market": "market-one"},
            issued_at=now,
            expires_at=now + timedelta(hours=1),
            suspended=False,
            audit_ref="audit-eligibility",
        )
        assert execute_risk_state_store_operation(
            store,
            "save_if_absent",
            eligibility,
            timeout_seconds=None,
        )
        decision = create_risk_decision_package(
            decision_id="decision-abcdef",
            intent_id=None,
            state=get_decision_state("approve"),
            requested_size=None,
            approved_size=None,
            ordered_checks=(),
            primary_failure_limit=None,
            composite_breach_flags=(),
            evidence_refs={"market": "market-one"},
            config_hash="a" * 64,
            concurrency_disclosure="single relational transaction",
            recommendations=(),
            issued_at=now,
            expires_at=now + timedelta(hours=1),
            token=None,
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
        )
        execute_risk_state_store_operation(store, "save_decision", decision)
        first_audit = create_risk_audit_record(
            record_id="audit-one",
            event_type="risk_decision",
            payload={"decision_id": decision.decision_id},
            evidence_refs={"market": "market-one"},
            config_hash="a" * 64,
            decision_id=decision.decision_id,
            occurred_at=now,
            sequence=0,
            previous_hash="0" * 64,
            record_hash="b" * 64,
            sealed=True,
            request_id="req-11111111-1111-4111-8111-111111111111",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
        )
        assert (
            execute_risk_state_store_operation(
                store,
                "append_atomic",
                first_audit,
                expected_sequence=0,
                expected_previous_hash="0" * 64,
                timeout_seconds=None,
            )
            == "appended"
        )
        state = create_kill_switch_state(
            state_id="state-global",
            scope_level="global",
            scope={},
            state="active",
            reason="operator safety stop",
            version=1,
            updated_at=now + timedelta(seconds=1),
        )
        state_audit = create_risk_audit_record(
            record_id="audit-two",
            event_type="kill_switch",
            payload={"state": "active"},
            evidence_refs={"operator": "operator-one"},
            config_hash="a" * 64,
            decision_id=None,
            occurred_at=now + timedelta(seconds=1),
            sequence=1,
            previous_hash="b" * 64,
            record_hash="c" * 64,
            sealed=True,
            request_id="req-11111111-1111-4111-8111-111111111111",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
        )
        assert (
            execute_risk_state_store_operation(
                store,
                "compare_and_swap_with_audit",
                state,
                state_audit,
                expected_version=0,
                expected_sequence=1,
                expected_previous_hash="b" * 64,
                timeout_seconds=None,
            )
            == "committed"
        )

        reconstructed = build_risk_state_store()
        assert execute_risk_state_store_operation(
            reconstructed, "list_decisions", 10
        ) == (decision,)
        assert (
            execute_risk_state_store_operation(
                reconstructed,
                "load_kill_switch",
                "global",
                {},
            )
            == state
        )
        assert execute_risk_state_store_operation(
            reconstructed,
            "read_all",
            timeout_seconds=None,
        ) == (first_audit, state_audit)


def test_risk_approval_lifecycle_is_relational_and_guarded(tmp_path: Path) -> None:
    """Persist issuance and consumption through Risk approval-token rows."""
    with data_settings_context(_settings(tmp_path)):
        _run_risk_migrations()
        now = datetime(2026, 8, 1, tzinfo=UTC)
        token = create_risk_approval_token(
            token_id="token-one",
            decision_id="decision-one",
            config_hash="a" * 64,
            action="trade",
            scope={"account_id": "account-one"},
            approver_id="risk-governor",
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
            nonce="nonce-one",
            signature="signature-one",
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
        )
        store = cast("Any", build_risk_approval_state_store())
        assert store.save_issued(token, timeout_seconds=None) == "saved"
        reconstructed = cast("Any", build_risk_approval_state_store())
        assert (
            reconstructed.consume_if_active(
                token.token_id,
                expected_signature=token.signature,
                reservation_id="reservation-one",
                workflow_id=token.workflow_id,
                action=token.action,
                scope=token.scope,
                now=now + timedelta(seconds=1),
                timeout_seconds=None,
            )
            == "consumed"
        )
        assert (
            reconstructed.consume_if_active(
                token.token_id,
                expected_signature=token.signature,
                reservation_id="reservation-two",
                workflow_id=token.workflow_id,
                action=token.action,
                scope=token.scope,
                now=now + timedelta(seconds=2),
                timeout_seconds=None,
            )
            == "already_consumed"
        )

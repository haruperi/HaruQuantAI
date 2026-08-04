"""Integration evidence for durable Trading runtime state."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from app.services.data import (
    build_data_settings,
    build_migration_request,
    build_statement_plan,
    build_transaction_request,
    data_settings_context,
    execute_transaction,
    run_domain_migrations,
    unwrap_data_response,
)
from app.services.trading import (
    apply_execution_event,
    build_trading_state_store,
    create_trading_event,
    create_trading_projection,
    execute_trading_state_store_operation,
    get_trading_migrations,
)
from app.utils import generate_id


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///trading-runtime.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _run_trading_migrations() -> None:
    """Apply the isolated Trading-owned schema through Data."""
    definition_response = get_trading_migrations()
    assert definition_response.status == "success"
    assert definition_response.data is not None
    request_id = generate_id("req")
    unwrap_data_response(
        run_domain_migrations(
            build_migration_request(
                domain="trading",
                steps=definition_response.data,
                request_id=request_id,
            )
        ),
        operation="tests.trading.migrations",
        request_id=request_id,
    )


def _read_rows(statement: str) -> tuple[dict[str, object], ...]:
    """Read bounded relational evidence through Data's public boundary.

    Returns:
        Normalized rows.
    """
    request_id = generate_id("req")
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=((),),
                max_rows=10,
            ),
            request_id=request_id,
        )
    )
    result = unwrap_data_response(
        response,
        operation="tests.trading.read_materializations",
        request_id=request_id,
    )
    return tuple(dict(row) for row in result.rows)


def test_trading_idempotency_state_survives_reconstruction(tmp_path: Path) -> None:
    """Trading returns duplicate and conflict results from durable state."""
    with data_settings_context(_settings(tmp_path)):
        _run_trading_migrations()
        now = datetime(2026, 8, 1, tzinfo=UTC)
        store = build_trading_state_store()
        first = cast(
            "Any",
            execute_trading_state_store_operation(
                store,
                "reserve_idempotency",
                "order-one",
                "a" * 64,
                "v1",
                now,
                now + timedelta(hours=1),
            ),
        )
        assert first.status == "new"

        reconstructed = build_trading_state_store()
        duplicate = cast(
            "Any",
            execute_trading_state_store_operation(
                reconstructed,
                "reserve_idempotency",
                "order-one",
                "a" * 64,
                "v1",
                now,
                now + timedelta(hours=1),
            ),
        )
        conflict = cast(
            "Any",
            execute_trading_state_store_operation(
                reconstructed,
                "reserve_idempotency",
                "order-one",
                "b" * 64,
                "v1",
                now,
                now + timedelta(hours=1),
            ),
        )
        assert duplicate.status == "duplicate_active"
        assert conflict.status == "conflict"


def test_trading_events_and_projection_survive_reconstruction(tmp_path: Path) -> None:
    """Persist event, reconciliation, projection, and unresolved evidence."""
    with data_settings_context(_settings(tmp_path)):
        _run_trading_migrations()
        now = datetime(2026, 8, 1, tzinfo=UTC)
        store = build_trading_state_store()
        attempted = create_trading_event(
            event_id="attempt-one",
            event_type="send_attempted",
            aggregate_version=0,
            route="sim",
            tenant_id="account-one",
            authority_id="simulation",
            occurred_at=now,
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
            payload={"client_order_id": "client-one"},
        )
        reconciled = create_trading_event(
            event_id="reconciliation-one",
            event_type="reconciliation_transitioned",
            aggregate_version=1,
            route="sim",
            tenant_id="account-one",
            authority_id="simulation",
            occurred_at=now,
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
            payload={"state": "unresolved"},
        )
        for event in (attempted, reconciled):
            execute_trading_state_store_operation(store, "append_event", event)
        projection = create_trading_projection(
            route="sim",
            tenant_id="account-one",
            authority_id="simulation",
            version=2,
            event_ids=(attempted.event_id, reconciled.event_id),
            orders={},
            positions={},
            fills={},
            receipts={},
            authority_state={"reconciliation": "unresolved"},
            unresolved_attempt_ids=(attempted.event_id,),
            updated_at=now,
        )
        execute_trading_state_store_operation(
            store,
            "save_projection",
            projection,
            0,
        )
        updated = projection.model_copy(update={"version": 3})
        execute_trading_state_store_operation(
            store,
            "save_projection",
            updated,
            2,
        )

        reconstructed = build_trading_state_store()
        scope = (attempted.route, attempted.tenant_id, attempted.authority_id)
        assert (
            execute_trading_state_store_operation(
                reconstructed, "load_projection", scope
            )
            == updated
        )
        unresolved = cast(
            "tuple[Any, ...]",
            execute_trading_state_store_operation(
                reconstructed, "load_unresolved_attempts", scope
            ),
        )
        assert tuple(event.event_id for event in unresolved) == (attempted.event_id,)
        all_unresolved = cast(
            "tuple[Any, ...]",
            execute_trading_state_store_operation(
                reconstructed, "load_all_unresolved_attempts", 10
            ),
        )
        assert tuple(event.event_id for event in all_unresolved) == (
            attempted.event_id,
        )
        evidence = cast(
            "dict[str, object]",
            execute_trading_state_store_operation(
                reconstructed, "load_report_evidence", scope
            ),
        )
        assert evidence["version"] == 3
        assert evidence["unresolved_attempt_ids"] == [attempted.event_id]


def test_atomic_event_application_materializes_trading_tables(tmp_path: Path) -> None:
    """Persist an order, authority transition, fill, and position atomically."""
    with data_settings_context(_settings(tmp_path)):
        _run_trading_migrations()
        now = datetime(2026, 8, 1, tzinfo=UTC)
        store = build_trading_state_store()
        intent = {
            "action": "submit_order",
            "client_order_id": "client-materialized",
            "account_id": "account-one",
            "symbol": "EURUSD",
            "source_intent_id": "signal-one",
            "risk_decision_id": "risk-one",
            "side": "BUY",
            "order_type": "MARKET",
            "time_in_force": None,
            "approved_volume": "1.25",
            "price": None,
            "stop_price": None,
            "stop_loss": None,
            "take_profit": None,
            "route": "sim",
        }
        attempted = create_trading_event(
            event_id="event-attempt",
            event_type="send_attempted",
            aggregate_version=0,
            route="sim",
            tenant_id="account-one",
            authority_id="simulation",
            occurred_at=now,
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
            payload={"intent": intent},
        )
        receipt = {
            "receipt_id": "receipt-one",
            "provider_order_id": "broker-order-one",
            "provider_deal_ids": ["deal-one"],
            "status": "filled",
            "filled_quantity": "1.25",
            "average_price": "1.1005",
            "authority_timestamp": now.isoformat(),
            "received_at": (now + timedelta(milliseconds=5)).isoformat(),
            "response_classification": "accepted",
        }
        received = create_trading_event(
            event_id="event-receipt",
            event_type="receipt_recorded",
            aggregate_version=1,
            route="sim",
            tenant_id="account-one",
            authority_id="simulation",
            occurred_at=now + timedelta(milliseconds=5),
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
            payload={
                "receipt": receipt,
                "attempt_event_id": attempted.event_id,
            },
        )
        position = {
            "account_id": "account-one",
            "symbol_id": "EURUSD",
            "direction": "long",
            "quantity_decimal": "1.25",
            "avg_entry_price_decimal": "1.1005",
            "current_price_decimal": "1.1005",
            "unrealized_pnl_decimal": "0",
            "realized_pnl_decimal": "0",
            "commission_total_decimal": "0",
            "swap_total_decimal": "0",
            "stop_loss_decimal": None,
            "take_profit_decimal": None,
            "strategy_version_id": None,
            "state": "open",
            "opened_at": now.isoformat(),
            "closed_at": None,
            "position_version": 1,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        filled = create_trading_event(
            event_id="event-fill",
            event_type="fill_recorded",
            aggregate_version=2,
            route="sim",
            tenant_id="account-one",
            authority_id="simulation",
            occurred_at=now + timedelta(milliseconds=5),
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
            payload={
                "provider_deal_id": "deal-one",
                "receipt_id": "receipt-one",
                "filled_quantity": "1.25",
                "average_price": "1.1005",
                "position_id": "position-one",
                "position": position,
            },
        )

        for event in (attempted, received, filled):
            response = apply_execution_event(event, store)
            assert response.status == "success"

        orders = _read_rows("SELECT order_id, time_in_force, state FROM trading_orders")
        fills = _read_rows(
            "SELECT order_id, broker_fill_id, executed_at FROM trading_fills"
        )
        positions = _read_rows("SELECT position_id, state FROM trading_positions")
        transitions = _read_rows(
            "SELECT order_id, from_state, to_state FROM trading_order_transitions"
        )
        assert orders == (
            {
                "order_id": "client-materialized",
                "time_in_force": None,
                "state": "filled",
            },
        )
        assert fills == (
            {
                "order_id": "client-materialized",
                "broker_fill_id": "deal-one",
                "executed_at": now.isoformat(),
            },
        )
        assert positions == ({"position_id": "position-one", "state": "open"},)
        assert transitions == (
            {
                "order_id": "client-materialized",
                "from_state": "pending_new",
                "to_state": "filled",
            },
        )


def test_materialization_failure_writes_no_event_or_projection(tmp_path: Path) -> None:
    """Reject incomplete business evidence before opening the transaction."""
    with data_settings_context(_settings(tmp_path)):
        _run_trading_migrations()
        event = create_trading_event(
            event_id="event-incomplete",
            event_type="send_attempted",
            aggregate_version=0,
            route="sim",
            tenant_id="account-one",
            authority_id="simulation",
            occurred_at=datetime(2026, 8, 1, tzinfo=UTC),
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
            payload={"client_order_id": "missing-governed-intent"},
        )

        response = apply_execution_event(event, build_trading_state_store())

        assert response.status == "error"
        assert response.error is not None
        assert response.error.code == "PERSISTENCE_FAILED"
        assert _read_rows("SELECT COUNT(*) AS count FROM trading_events") == (
            {"count": 0},
        )
        assert _read_rows("SELECT COUNT(*) AS count FROM trading_projections") == (
            {"count": 0},
        )

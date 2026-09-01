"""Integration evidence for durable Trading runtime state."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from app.kernel.identity import generate_id
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
    build_trade_ownership,
    build_trading_state_store,
    create_closed_position_record,
    create_protective_order_plan,
    create_trading_event,
    create_trading_projection,
    execute_trading_state_store_operation,
    get_trading_migrations,
    parse_trade_ownership,
    persist_closed_position,
    persist_protective_order_plan,
    persist_trade_ownership,
    run_trading_migrations,
)


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
    request_id = generate_id("req")
    unwrap_data_response(
        run_trading_migrations(request_id=request_id),
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


def test_atomic_event_application_materializes_orders_only(tmp_path: Path) -> None:
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
        positions = _read_rows("SELECT ticket FROM trading_positions")
        lifecycle_tables = _read_rows(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name IN ('trading_fills', 'trading_order_transitions')"
        )
        assert orders == (
            {
                "order_id": "client-materialized",
                "time_in_force": None,
                "state": "FILLED",
            },
        )
        assert positions == ()
        assert lifecycle_tables == (
            {"name": "trading_order_transitions"},
            {"name": "trading_fills"},
        )


def test_closed_position_is_inserted_once_as_exact_evidence(tmp_path: Path) -> None:
    """Persist only a complete closed position with slippage measured in points."""
    with data_settings_context(_settings(tmp_path)):
        _run_trading_migrations()
        now = datetime(2026, 8, 1, tzinfo=UTC)
        record = create_closed_position_record(
            ticket="123456",
            symbol="EURUSD",
            type="buy",
            volume=Decimal("0.10"),
            entry_time=now,
            entry_price=Decimal("1.10000"),
            stop_loss=Decimal("1.09500"),
            take_profit=Decimal("1.11000"),
            exit_time=now + timedelta(hours=1),
            exit_price=Decimal("1.10500"),
            exit_reason="take_profit",
            commission=Decimal("-0.70"),
            swap=Decimal(0),
            profit=Decimal("49.30"),
            mae_points=12,
            mfe_points=55,
            slippage_points=1,
            magic="10001",
            strategy="trend_following",
            account="90001",
            environment="demo",
            request_id="req-11111111-1111-4111-8111-111111111111",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
            created_at=now + timedelta(hours=1),
            updated_at=now + timedelta(hours=1),
        )

        persist_closed_position(record)

        rows = _read_rows(
            "SELECT ticket, volume, slippage_points, environment FROM trading_positions"
        )
        assert rows == (
            {
                "ticket": "123456",
                "volume": "0.10",
                "slippage_points": 1,
                "environment": "demo",
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


def test_protection_and_ownership_have_reachable_append_only_writes(
    tmp_path: Path,
) -> None:
    """Persist exact protection and ownership evidence without position bodies."""
    with data_settings_context(_settings(tmp_path)):
        _run_trading_migrations()
        now = datetime(2026, 8, 7, tzinfo=UTC)
        plan = create_protective_order_plan(
            plan_id="protect-001",
            position_id="position-001",
            order_id="order-001",
            risk_decision_id="risk-001",
            quantity=Decimal(1),
            stop_price=Decimal(9),
            target_price=Decimal(12),
            oco_group_id="oco-001",
            source_sequence=1,
        )
        ownership = parse_trade_ownership(
            build_trade_ownership(
                ownership_id="ownership-001",
                owner_type="player",
                owner_id="player-001",
                account_id="account-001",
                position_id="position-001",
                trade_plan_id="plan-001",
                strategy_version="v1",
                session_id="session-001",
                source_sequence=1,
            )
        )
        persist_protective_order_plan(
            plan, correlation_id="correlation-001", occurred_at=now
        )
        persist_trade_ownership(
            ownership, correlation_id="correlation-001", occurred_at=now
        )
        assert _read_rows(
            "SELECT COUNT(*) AS count FROM trading_protective_orders"
        ) == ({"count": 2},)
        assert _read_rows("SELECT COUNT(*) AS count FROM trading_trade_ownership") == (
            {"count": 1},
        )
        assert _read_rows("SELECT COUNT(*) AS count FROM trading_positions") == (
            {"count": 0},
        )


def test_migration_004_preserves_existing_order_and_is_idempotent(
    tmp_path: Path,
) -> None:
    """Upgrade a populated migration-003 database without losing order evidence."""
    with data_settings_context(_settings(tmp_path)):
        response = get_trading_migrations()
        assert response.status == "success"
        assert response.data is not None
        steps = response.data
        request_id = "req-44444444-4444-4444-8444-444444444444"
        unwrap_data_response(
            run_domain_migrations(
                build_migration_request(
                    domain="trading",
                    steps=steps[:3],
                    request_id=request_id,
                    complete_manifest=False,
                )
            ),
            operation="tests.trading.migration_003",
            request_id=request_id,
        )
        now = datetime(2026, 8, 7, tzinfo=UTC)
        insert_response = execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT INTO trading_orders "
                        "(order_id, client_order_id, account_id, symbol_id, "
                        "risk_decision_id, side, order_type, quantity_decimal, "
                        "state, runtime_profile, correlation_id, created_at, "
                        "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ),
                    parameter_sets=(
                        (
                            "client-upgrade",
                            "client-upgrade",
                            "account-one",
                            "EURUSD",
                            "risk-one",
                            "buy",
                            "market",
                            "1",
                            "pending_new",
                            "paper",
                            "cor-33333333-3333-4333-8333-333333333333",
                            now.isoformat(),
                            now.isoformat(),
                        ),
                    ),
                    max_rows=1,
                ),
                request_id="req-55555555-5555-4555-8555-555555555555",
            )
        )
        assert insert_response.status == "success"
        _run_trading_migrations()
        _run_trading_migrations()
        assert _read_rows(
            "SELECT order_id, state, runtime_profile FROM trading_orders "
            "WHERE order_id = 'client-upgrade'"
        ) == (
            {
                "order_id": "client-upgrade",
                "state": "STAGED",
                "runtime_profile": "demo",
            },
        )
        assert _read_rows(
            "SELECT COUNT(*) AS count FROM data_migration_ledger "
            "WHERE domain = 'trading'"
        ) == ({"count": len(steps)},)

"""Credential-gated real MT5 demo validation through the Trading dispatcher."""

from __future__ import annotations

# ruff: noqa: INP001
import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers import BrokerId, create_broker_adapter
from app.services.trading import OrderIntent, dispatch_order_intent
from app.utils import generate_id, logger
from tests.brokers.integration.test_mt5_demo_mutations import (
    _authority_state,
    _cleanup_created_state,
    _connection_config,
    _minimum_pending_order,
    _require_demo_settings,
    _verify_demo_session,
)


async def _exercise_trading_demo_dispatch() -> None:
    """Dispatch one minimum-size MT5 demo order and reconcile exact cleanup."""
    settings = _require_demo_settings()
    connection = _connection_config(settings)
    created = create_broker_adapter(BrokerId.MT5, connection)
    assert created.is_success, created.error
    adapter = created.data
    assert adapter is not None

    connected = await adapter.connect()
    assert connected.is_success, connected.error
    original_orders: set[str] | None = None
    original_positions: set[str] | None = None
    try:
        await _verify_demo_session(adapter)
        original_orders, original_positions = await _authority_state(adapter)
        minimum = await _minimum_pending_order(adapter, settings)
        now = datetime.now(UTC)
        request_id = minimum.client_request_id or generate_id("req")
        correlation_id = minimum.client_order_id or generate_id("cor")
        intent = OrderIntent(
            client_order_id=correlation_id,
            request_id=request_id,
            workflow_id=generate_id("wf"),
            correlation_id=correlation_id,
            route="paper",
            provider_id="mt5",
            account_id="verified-mt5-demo-account",
            strategy_id="trading-demo-validation",
            strategy_version="v1",
            source_intent_id=f"intent-{correlation_id}",
            symbol=minimum.symbol,
            action="submit_order",
            side=minimum.side,
            order_type=minimum.order_type,
            quantity_unit=minimum.quantity_unit,
            approved_volume=minimum.quantity,
            risk_approved_volume=minimum.quantity,
            price=minimum.limit_price,
            time_in_force=minimum.time_in_force,
            idempotency_hash="a" * 64,
            canonical_material_version="v1",
            risk_decision_id="verified-demo-risk-decision",
            action_policy_verdict_id="verified-demo-action-policy",
            approval_token_ref="verified-demo-approval",
            created_at=now,
            valid_until=now + timedelta(minutes=5),
        )
        logger.info(
            "Trading real-provider validation authorized | environment=dev "
            "provider_environment=demo selected_adapter=mt5 "
            "account_classification=demo permission=trade_write "
            "operation=minimum_pending_order cleanup=cancel_and_reconcile"
        )

        receipt = await dispatch_order_intent(
            intent,
            connection,
            adapter,
            None,
            operation_timeout_seconds=Decimal(15),
            clock=lambda: datetime.now(UTC),
        )

        assert receipt.status == "accepted"
        assert receipt.provider_order_id is not None
        assert not receipt.reconciliation_required
    finally:
        if original_orders is not None and original_positions is not None:
            await _cleanup_created_state(
                adapter,
                original_orders=original_orders,
                original_positions=original_positions,
            )
        await adapter.disconnect()


def test_trading_dispatches_and_cleans_real_mt5_demo_order() -> None:
    """Use Trading's public boundary for one verified demo mutation and cleanup."""
    asyncio.run(_exercise_trading_demo_dispatch())

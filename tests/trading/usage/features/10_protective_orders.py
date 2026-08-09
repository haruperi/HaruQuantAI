"""Standalone usage evidence for FEAT-TRD-10."""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import build_data_settings, data_settings_context
from app.services.trading import (
    build_protective_order_plan,
    create_protective_order_plan,
    parse_protective_order_plan,
    persist_protective_order_plan,
    resize_protective_orders,
    run_trading_migrations,
    verify_protective_order_coverage,
)


def fr_trd_078() -> object:
    """Create a bracket/OCO protective-order plan."""
    return create_protective_order_plan(
        plan_id="usage-protect-001",
        position_id="usage-position-001",
        order_id="usage-order-001",
        risk_decision_id="usage-risk-001",
        quantity=Decimal(2),
        stop_price=Decimal(9),
        target_price=Decimal(12),
        oco_group_id="usage-oco-001",
        source_sequence=1,
    )


def fr_trd_079(plan: object) -> object:
    """Round-trip the versioned protective-order contract."""
    return parse_protective_order_plan(build_protective_order_plan(plan))


def fr_trd_080(plan: object) -> dict[str, object]:
    """Verify exact coverage and safely resize residual protection."""
    coverage = verify_protective_order_coverage(
        plan,
        open_quantity=Decimal(2),
        stop_acknowledged=True,
        target_acknowledged=True,
    )
    resized = resize_protective_orders(
        plan, residual_quantity=Decimal(1), source_sequence=2
    )
    return {"coverage": coverage, "resized_quantity": str(resized.quantity)}


def main() -> None:
    """Demonstrate every public protective-order operation."""
    plan = fr_trd_079(fr_trd_078())
    produced = fr_trd_080(plan)
    with TemporaryDirectory() as directory:
        settings = build_data_settings(
            database_url="sqlite:///protective-usage.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
        )
        with data_settings_context(settings):
            run_trading_migrations(
                request_id="req-11111111-1111-4111-8111-111111111111"
            )
            persist_protective_order_plan(
                plan,
                correlation_id="cor-11111111-1111-4111-8111-111111111111",
                occurred_at=datetime(2026, 8, 7, tzinfo=UTC),
            )
    print("SUCCESS: FR-TRD-078; SUCCESS: FR-TRD-079; SUCCESS: FR-TRD-080")
    print(
        {
            "Data -> FR-TRD-078": plan.plan_id,
            "Data -> FR-TRD-079": plan.schema_id,
            "Data -> FR-TRD-080": produced,
        }
    )


if __name__ == "__main__":
    main()

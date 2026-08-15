"""Approved public state API for the Trading domain."""

from app.services.trading.migrations import (
    TRADING_SCHEMA_VERSION as TRADING_SCHEMA_VERSION,
)
from app.services.trading.migrations import (
    get_trading_migrations,
    run_trading_migrations,
)
from app.services.trading.state.events import TradingEvent as TradingEvent
from app.services.trading.state.execution_positions import (
    create_execution_position,
    create_execution_position_store,
    get_execution_position,
    get_execution_position_snapshot,
    reconcile_execution_position_receipt,
    restore_execution_position_store,
    serialize_execution_position_store,
    set_execution_position,
    transition_execution_position,
)
from app.services.trading.state.factories import (
    create_idempotency_reservation,
    create_trading_event,
    create_trading_projection,
    get_trading_schema_version,
)
from app.services.trading.state.fills import (
    apply_order_fill,
    create_fill_aggregate,
    get_fill_residual,
)
from app.services.trading.state.idempotency import (
    IdempotencyReservation as IdempotencyReservation,
)
from app.services.trading.state.idempotency import (
    reserve_idempotency,
)
from app.services.trading.state.order_lifecycle import (
    create_order_lifecycle,
    transition_order_lifecycle,
)
from app.services.trading.state.projections import (
    TradingProjection as TradingProjection,
)
from app.services.trading.state.projections import (
    apply_execution_event,
)
from app.services.trading.state.runtime import (
    build_trading_state_store,
    execute_trading_state_store_operation,
    get_trading_projection,
)
from app.services.trading.state.stores import TradingStateStore as TradingStateStore

__all__ = [
    "apply_execution_event",
    "apply_order_fill",
    "build_trading_state_store",
    "create_execution_position",
    "create_execution_position_store",
    "create_fill_aggregate",
    "create_idempotency_reservation",
    "create_order_lifecycle",
    "create_trading_event",
    "create_trading_projection",
    "execute_trading_state_store_operation",
    "get_execution_position",
    "get_execution_position_snapshot",
    "get_fill_residual",
    "get_trading_migrations",
    "get_trading_projection",
    "get_trading_schema_version",
    "reconcile_execution_position_receipt",
    "reserve_idempotency",
    "restore_execution_position_store",
    "run_trading_migrations",
    "serialize_execution_position_store",
    "set_execution_position",
    "transition_execution_position",
    "transition_order_lifecycle",
]

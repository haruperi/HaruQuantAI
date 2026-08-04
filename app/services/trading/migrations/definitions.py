"""Additive Trading-owned schema definitions executed by Data.

Conformed to the authoritative schema model in ``docs/schema`` (Domain 7). The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-TRD-070`` through
``FR-TRD-073``.
"""

from hashlib import sha256
from typing import Any, Literal

from app.services.data import build_migration_step
from app.services.trading.contracts.responses import success_trading_response
from app.utils import get_logger

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

TRADING_SCHEMA_VERSION = "v1"

_TRADING_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS trading_events (
        event_seq INTEGER PRIMARY KEY,
        event_id TEXT NOT NULL UNIQUE,
        event_type TEXT NOT NULL,
        event_version TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        aggregate_version INTEGER NOT NULL,
        occurred_at TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        causation_id TEXT,
        bucket_year TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (scope_key, aggregate_version)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_events_scope "
        "ON trading_events(scope_key, aggregate_version)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_events_time "
        "ON trading_events(occurred_at DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_events_corr "
        "ON trading_events(correlation_id)"
    ),
    """
    CREATE TABLE IF NOT EXISTS trading_idempotency (
        idempotency_key TEXT PRIMARY KEY,
        material_hash TEXT NOT NULL,
        material_version TEXT NOT NULL,
        status TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        receipt_id TEXT,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_idem_expiry "
        "ON trading_idempotency(expires_at)"
    ),
    """
    CREATE TABLE IF NOT EXISTS trading_projections (
        scope_key TEXT PRIMARY KEY,
        projection_version INTEGER NOT NULL CHECK (projection_version >= 0),
        last_event_seq INTEGER NOT NULL,
        projection_json TEXT NOT NULL CHECK (json_valid(projection_json)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS trading_orders (
        order_id TEXT PRIMARY KEY,
        client_order_id TEXT NOT NULL UNIQUE,
        broker_order_id TEXT,
        account_id TEXT NOT NULL,
        symbol_id TEXT NOT NULL,
        strategy_version_id TEXT,
        config_id TEXT,
        signal_id TEXT,
        risk_decision_id TEXT NOT NULL,
        side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
        order_type TEXT NOT NULL CHECK (
            order_type IN ('market', 'limit', 'stop', 'stop_limit', 'trailing_stop')
        ),
        time_in_force TEXT CHECK (time_in_force IN ('gtc', 'ioc', 'fok', 'day', 'gtd')),
        quantity_decimal TEXT NOT NULL,
        filled_qty_decimal TEXT NOT NULL DEFAULT '0',
        limit_price_decimal TEXT,
        stop_price_decimal TEXT,
        avg_fill_price_decimal TEXT,
        stop_loss_decimal TEXT,
        take_profit_decimal TEXT,
        state TEXT NOT NULL CHECK (state IN (
            'pending_new', 'new', 'partially_filled', 'filled',
            'pending_cancel', 'cancelled', 'rejected', 'expired'
        )),
        reject_reason TEXT,
        runtime_profile TEXT NOT NULL CHECK (
            runtime_profile IN ('research', 'simulation', 'paper', 'live')
        ),
        submitted_at TEXT,
        terminal_at TEXT,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (
            order_type NOT IN ('limit', 'stop_limit')
            OR limit_price_decimal IS NOT NULL
        ),
        CHECK (
            order_type NOT IN ('stop', 'stop_limit', 'trailing_stop')
            OR stop_price_decimal IS NOT NULL
        ),
        CHECK (state <> 'rejected' OR reject_reason IS NOT NULL)
    ) STRICT
    """.strip(),
    """
    CREATE INDEX IF NOT EXISTS idx_trading_orders_open
    ON trading_orders(account_id, symbol_id)
    WHERE state IN ('pending_new', 'new', 'partially_filled', 'pending_cancel')
    """.strip(),
    """
    CREATE INDEX IF NOT EXISTS idx_trading_orders_broker
    ON trading_orders(broker_order_id) WHERE broker_order_id IS NOT NULL
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_orders_history "
        "ON trading_orders(account_id, created_at DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_orders_risk "
        "ON trading_orders(risk_decision_id)"
    ),
    """
    CREATE TABLE IF NOT EXISTS trading_fills (
        fill_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL REFERENCES trading_orders(order_id) ON DELETE RESTRICT,
        broker_fill_id TEXT,
        sequence INTEGER NOT NULL,
        quantity_decimal TEXT NOT NULL,
        price_decimal TEXT NOT NULL,
        commission_decimal TEXT NOT NULL DEFAULT '0',
        swap_decimal TEXT NOT NULL DEFAULT '0',
        slippage_bps TEXT,
        liquidity_flag TEXT CHECK (liquidity_flag IN ('maker', 'taker', 'unknown')),
        executed_at TEXT NOT NULL,
        reported_at TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (order_id, sequence),
        UNIQUE (broker_fill_id)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_fills_order "
        "ON trading_fills(order_id, sequence)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_fills_time "
        "ON trading_fills(executed_at DESC)"
    ),
    """
    CREATE TABLE IF NOT EXISTS trading_order_transitions (
        transition_seq INTEGER PRIMARY KEY,
        order_id TEXT NOT NULL CHECK (order_id <> '')
            REFERENCES trading_orders(order_id) ON DELETE RESTRICT,
        from_state TEXT,
        to_state TEXT NOT NULL,
        reason_code TEXT NOT NULL,
        detail_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(detail_json)),
        occurred_at TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_trading_transitions_order "
        "ON trading_order_transitions(order_id, transition_seq)"
    ),
    """
    CREATE TABLE IF NOT EXISTS trading_positions (
        position_id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        symbol_id TEXT NOT NULL,
        direction TEXT NOT NULL CHECK (direction IN ('long', 'short')),
        quantity_decimal TEXT NOT NULL,
        avg_entry_price_decimal TEXT NOT NULL,
        current_price_decimal TEXT,
        unrealized_pnl_decimal TEXT NOT NULL DEFAULT '0',
        realized_pnl_decimal TEXT NOT NULL DEFAULT '0',
        commission_total_decimal TEXT NOT NULL DEFAULT '0',
        swap_total_decimal TEXT NOT NULL DEFAULT '0',
        stop_loss_decimal TEXT,
        take_profit_decimal TEXT,
        strategy_version_id TEXT,
        state TEXT NOT NULL CHECK (state IN ('open', 'closing', 'closed')),
        opened_at TEXT NOT NULL,
        closed_at TEXT,
        position_version INTEGER NOT NULL DEFAULT 0 CHECK (position_version >= 0),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_trading_pos_open
    ON trading_positions(account_id, symbol_id, direction) WHERE state = 'open'
    """.strip(),
    """
    CREATE INDEX IF NOT EXISTS idx_trading_pos_history
    ON trading_positions(account_id, closed_at DESC) WHERE state = 'closed'
    """.strip(),
)


def _migration_checksum(statements: tuple[str, ...]) -> str:
    """Return a stable checksum for ordered Trading schema statements.

    Args:
        statements: Ordered additive SQL definitions.

    Returns:
        Lowercase SHA-256 checksum.
    """
    logger.debug("Calculating Trading migration checksum")
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return sha256(material).hexdigest()


def _get_trading_migrations_value() -> tuple[Any, ...]:
    """Return additive Trading migration definitions without opening storage.

    Returns:
        Ordered immutable Data-owned migration contracts.
    """
    logger.debug("Returning Trading-owned migration definitions")
    return (
        build_migration_step(
            domain="trading",
            migration_id="001_initial_trading_schema",
            checksum=_migration_checksum(_TRADING_SCHEMA_STATEMENTS),
            statements=_TRADING_SCHEMA_STATEMENTS,
        ),
    )


def get_trading_migrations() -> StandardResponse[tuple[Any, ...]]:
    """Return Trading migration definitions in a standard response.

    Returns:
        Canonical response containing immutable additive migration contracts.
    """
    return success_trading_response(
        _get_trading_migrations_value(),
        risk_level="low",
        legacy_status="available",
    )


__all__ = ["TRADING_SCHEMA_VERSION", "get_trading_migrations"]

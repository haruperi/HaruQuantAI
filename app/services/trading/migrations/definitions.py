"""Immutable Trading-owned schema definitions executed by Data."""

from hashlib import sha256
from typing import Any, Literal

from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_domain_migrations,
)
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

_CLOSED_POSITION_LEDGER_STATEMENTS = (
    """
    CREATE TABLE trading_closed_position_migration_guard (
        is_empty INTEGER NOT NULL CHECK (is_empty = 1)
    ) STRICT
    """.strip(),
    """
    INSERT INTO trading_closed_position_migration_guard (is_empty)
    SELECT CASE WHEN
        (SELECT COUNT(*) FROM trading_positions) = 0 AND
        (SELECT COUNT(*) FROM trading_fills) = 0 AND
        (SELECT COUNT(*) FROM trading_order_transitions) = 0
    THEN 1 ELSE 0 END
    """.strip(),
    """
    CREATE TABLE trading_positions__new (
        ticket TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('buy', 'sell')),
        volume TEXT NOT NULL,
        entry_time TEXT NOT NULL,
        entry_price TEXT NOT NULL,
        stop_loss TEXT,
        take_profit TEXT,
        exit_time TEXT NOT NULL,
        exit_price TEXT NOT NULL,
        exit_reason TEXT NOT NULL,
        commission TEXT NOT NULL,
        swap TEXT NOT NULL,
        profit TEXT NOT NULL,
        mae_points INTEGER NOT NULL CHECK (mae_points >= 0),
        mfe_points INTEGER NOT NULL CHECK (mfe_points >= 0),
        slippage_points INTEGER NOT NULL CHECK (slippage_points >= 0),
        magic TEXT NOT NULL,
        strategy TEXT NOT NULL,
        account TEXT NOT NULL,
        environment TEXT NOT NULL CHECK (
            environment IN ('demo', 'paper', 'sim', 'live')
        ),
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        evidence_hash TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (exit_time >= entry_time)
    ) STRICT
    """.strip(),
    "DROP TABLE trading_order_transitions",
    "DROP TABLE trading_fills",
    "DROP TABLE trading_positions",
    "ALTER TABLE trading_positions__new RENAME TO trading_positions",
    (
        "CREATE INDEX idx_trading_positions_account_exit "
        "ON trading_positions(account, exit_time DESC)"
    ),
    (
        "CREATE INDEX idx_trading_positions_strategy_exit "
        "ON trading_positions(account, strategy, exit_time DESC)"
    ),
    (
        "CREATE INDEX idx_trading_positions_symbol_exit "
        "ON trading_positions(account, symbol, exit_time DESC)"
    ),
    (
        "CREATE INDEX idx_trading_positions_magic_exit "
        "ON trading_positions(account, magic, exit_time DESC)"
    ),
    "DROP TABLE trading_closed_position_migration_guard",
)

_EXECUTION_LIFECYCLE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS trading_order_transitions (
        transition_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL REFERENCES trading_orders(order_id) ON DELETE RESTRICT,
        from_state TEXT,
        to_state TEXT NOT NULL,
        source_sequence INTEGER NOT NULL,
        reason_code TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        causation_id TEXT,
        created_at TEXT NOT NULL,
        UNIQUE (order_id, source_sequence)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS trading_fills (
        fill_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL REFERENCES trading_orders(order_id) ON DELETE RESTRICT,
        broker_fill_id TEXT,
        source_sequence INTEGER NOT NULL,
        quantity_decimal TEXT NOT NULL,
        price_decimal TEXT NOT NULL,
        fee_estimate_decimal TEXT,
        executed_at TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (order_id, source_sequence),
        UNIQUE (broker_fill_id)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS trading_protective_orders (
        protective_order_id TEXT PRIMARY KEY,
        position_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        protection_type TEXT NOT NULL CHECK (protection_type IN ('stop', 'target')),
        quantity_decimal TEXT NOT NULL,
        price_decimal TEXT NOT NULL,
        state TEXT NOT NULL CHECK (
            state IN ('pending', 'acknowledged', 'unknown', 'cancelled')
        ),
        oco_group_id TEXT NOT NULL,
        source_sequence INTEGER NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (position_id, protection_type, source_sequence)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS trading_trade_ownership (
        ownership_id TEXT PRIMARY KEY,
        position_id TEXT NOT NULL,
        owner_type TEXT NOT NULL CHECK (
            owner_type IN ('player', 'supervised_automation', 'automated')
        ),
        owner_id TEXT NOT NULL,
        trade_plan_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        source_sequence INTEGER NOT NULL,
        released INTEGER NOT NULL DEFAULT 0 CHECK (released IN (0, 1)),
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (position_id, source_sequence)
    ) STRICT
    """.strip(),
)

_ORDER_LIFECYCLE_STATE_STATEMENTS = (
    """
    CREATE TABLE trading_orders__lifecycle (
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
            'CREATED', 'STAGED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_FILLED',
            'FILLED', 'CANCEL_PENDING', 'CANCELLED', 'REPLACE_PENDING',
            'REPLACED', 'REJECTED', 'EXPIRED', 'UNKNOWN', 'RECONCILED'
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
        CHECK (state <> 'REJECTED' OR reject_reason IS NOT NULL)
    ) STRICT
    """.strip(),
    """
    INSERT INTO trading_orders__lifecycle
    SELECT
        order_id, client_order_id, broker_order_id, account_id, symbol_id,
        strategy_version_id, config_id, signal_id, risk_decision_id, side,
        order_type, time_in_force, quantity_decimal, filled_qty_decimal,
        limit_price_decimal, stop_price_decimal, avg_fill_price_decimal,
        stop_loss_decimal, take_profit_decimal,
        CASE state
            WHEN 'pending_new' THEN 'STAGED'
            WHEN 'new' THEN 'ACKNOWLEDGED'
            WHEN 'partially_filled' THEN 'PARTIALLY_FILLED'
            WHEN 'filled' THEN 'FILLED'
            WHEN 'pending_cancel' THEN 'CANCEL_PENDING'
            WHEN 'cancelled' THEN 'CANCELLED'
            WHEN 'rejected' THEN 'REJECTED'
            WHEN 'expired' THEN 'EXPIRED'
        END,
        reject_reason, runtime_profile, submitted_at, terminal_at,
        correlation_id, created_at, updated_at
    FROM trading_orders
    """.strip(),
    """
    CREATE TABLE trading_order_transitions__lifecycle (
        transition_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL
            REFERENCES trading_orders__lifecycle(order_id) ON DELETE RESTRICT,
        from_state TEXT,
        to_state TEXT NOT NULL,
        source_sequence INTEGER NOT NULL,
        reason_code TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        causation_id TEXT,
        created_at TEXT NOT NULL,
        UNIQUE (order_id, source_sequence)
    ) STRICT
    """.strip(),
    """
    INSERT INTO trading_order_transitions__lifecycle
    SELECT * FROM trading_order_transitions
    """.strip(),
    """
    CREATE TABLE trading_fills__lifecycle (
        fill_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL
            REFERENCES trading_orders__lifecycle(order_id) ON DELETE RESTRICT,
        broker_fill_id TEXT,
        source_sequence INTEGER NOT NULL,
        quantity_decimal TEXT NOT NULL,
        price_decimal TEXT NOT NULL,
        fee_estimate_decimal TEXT,
        executed_at TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (order_id, source_sequence),
        UNIQUE (broker_fill_id)
    ) STRICT
    """.strip(),
    "INSERT INTO trading_fills__lifecycle SELECT * FROM trading_fills",
    """
    CREATE TABLE trading_order_lifecycle_migration_guard (
        preserved INTEGER NOT NULL CHECK (preserved = 1)
    ) STRICT
    """.strip(),
    """
    INSERT INTO trading_order_lifecycle_migration_guard (preserved)
    SELECT CASE WHEN
        (SELECT COUNT(*) FROM trading_orders) =
            (SELECT COUNT(*) FROM trading_orders__lifecycle) AND
        (SELECT COUNT(*) FROM trading_order_transitions) =
            (SELECT COUNT(*) FROM trading_order_transitions__lifecycle) AND
        (SELECT COUNT(*) FROM trading_fills) =
            (SELECT COUNT(*) FROM trading_fills__lifecycle)
    THEN 1 ELSE 0 END
    """.strip(),
    "DROP TABLE trading_order_transitions",
    "DROP TABLE trading_fills",
    "DROP TABLE trading_orders",
    "ALTER TABLE trading_orders__lifecycle RENAME TO trading_orders",
    "ALTER TABLE trading_order_transitions__lifecycle RENAME TO trading_order_transitions",  # noqa: E501
    "ALTER TABLE trading_fills__lifecycle RENAME TO trading_fills",
    """
    CREATE INDEX idx_trading_orders_open
    ON trading_orders(account_id, symbol_id)
    WHERE state IN (
        'CREATED', 'STAGED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_FILLED',
        'CANCEL_PENDING', 'REPLACE_PENDING', 'UNKNOWN', 'RECONCILED'
    )
    """.strip(),
    """
    CREATE INDEX idx_trading_orders_broker
    ON trading_orders(broker_order_id) WHERE broker_order_id IS NOT NULL
    """.strip(),
    (
        "CREATE INDEX idx_trading_orders_history "
        "ON trading_orders(account_id, created_at DESC)"
    ),
    ("CREATE INDEX idx_trading_orders_risk ON trading_orders(risk_decision_id)"),
    "DROP TABLE trading_order_lifecycle_migration_guard",
)

_ROUTE_VOCABULARY_STATEMENTS = (
    """CREATE TABLE trading_orders__route_vocabulary (
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
            'CREATED', 'STAGED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_FILLED',
            'FILLED', 'CANCEL_PENDING', 'CANCELLED', 'REPLACE_PENDING',
            'REPLACED', 'REJECTED', 'EXPIRED', 'UNKNOWN', 'RECONCILED'
        )),
        reject_reason TEXT,
        runtime_profile TEXT NOT NULL CHECK (
            runtime_profile IN ('research', 'simulation', 'demo', 'live')
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
        CHECK (state <> 'REJECTED' OR reject_reason IS NOT NULL)
    ) STRICT""",
    """INSERT INTO trading_orders__route_vocabulary
    SELECT order_id, client_order_id, broker_order_id, account_id, symbol_id,
        strategy_version_id, config_id, signal_id, risk_decision_id, side,
        order_type, time_in_force, quantity_decimal, filled_qty_decimal,
        limit_price_decimal, stop_price_decimal, avg_fill_price_decimal,
        stop_loss_decimal, take_profit_decimal, state, reject_reason,
        CASE runtime_profile WHEN 'paper' THEN 'demo' ELSE runtime_profile END,
        submitted_at, terminal_at, correlation_id, created_at, updated_at
    FROM trading_orders""",
    "DROP TABLE trading_orders",
    "ALTER TABLE trading_orders__route_vocabulary RENAME TO trading_orders",
    """CREATE INDEX idx_trading_orders_open
    ON trading_orders(account_id, symbol_id)
    WHERE state IN (
        'CREATED', 'STAGED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_FILLED',
        'CANCEL_PENDING', 'REPLACE_PENDING', 'UNKNOWN', 'RECONCILED'
    )""",
    """CREATE INDEX idx_trading_orders_broker
    ON trading_orders(broker_order_id) WHERE broker_order_id IS NOT NULL""",
    (
        "CREATE INDEX idx_trading_orders_history "
        "ON trading_orders(account_id, created_at DESC)"
    ),
    "CREATE INDEX idx_trading_orders_risk ON trading_orders(risk_decision_id)",
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
        build_migration_step(
            domain="trading",
            migration_id="002_closed_position_ledger",
            checksum=_migration_checksum(_CLOSED_POSITION_LEDGER_STATEMENTS),
            statements=_CLOSED_POSITION_LEDGER_STATEMENTS,
        ),
        build_migration_step(
            domain="trading",
            migration_id="003_execution_lifecycle",
            checksum=_migration_checksum(_EXECUTION_LIFECYCLE_STATEMENTS),
            statements=_EXECUTION_LIFECYCLE_STATEMENTS,
        ),
        build_migration_step(
            domain="trading",
            migration_id="004_order_lifecycle_states",
            checksum=_migration_checksum(_ORDER_LIFECYCLE_STATE_STATEMENTS),
            statements=_ORDER_LIFECYCLE_STATE_STATEMENTS,
        ),
        build_migration_step(
            domain="trading",
            migration_id="005_route_vocabulary",
            checksum=_migration_checksum(_ROUTE_VOCABULARY_STATEMENTS),
            statements=_ROUTE_VOCABULARY_STATEMENTS,
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


def run_trading_migrations(*, request_id: str) -> object:
    """Apply the complete authoritative Trading migration manifest.

    Args:
        request_id: Non-empty audit correlation identifier.

    Returns:
        Data-owned standard response carrying the migration result.

    Raises:
        ValueError: If ``request_id`` is empty.
    """
    normalized_request_id = request_id.strip()
    if not normalized_request_id:
        raise ValueError("request_id must not be empty")
    logger.info("Running the authoritative Trading schema migration manifest")
    return run_domain_migrations(
        build_migration_request(
            domain="trading",
            steps=_get_trading_migrations_value(),
            request_id=normalized_request_id,
            complete_manifest=True,
        )
    )


__all__ = ["TRADING_SCHEMA_VERSION", "get_trading_migrations", "run_trading_migrations"]

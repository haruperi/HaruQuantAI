"""Database-backed trading execution sessions and account profile for D-IFACE.

Interacts with 'trading_sessions' and 'instruments' in haruquantai.db.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final
from uuid import uuid4

_DEFAULT_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)
_DEFAULT_BALANCE: Final[float] = 100000.0
_DEFAULT_LEVERAGE: Final[int] = 100


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 string representation.

    Returns:
        ISO-8601 formatted datetime string.
    """
    return datetime.now(UTC).isoformat()


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection configured with Row factory.

    Args:
        db_path: Optional explicit database path.

    Returns:
        Configured SQLite connection.
    """
    target = Path(db_path) if db_path is not None else _DEFAULT_DB_PATH
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_session_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a database row from trading_sessions into an API dictionary.

    Args:
        row: SQLite database row.

    Returns:
        Structured dictionary conforming to executionSessionSchema.
    """
    raw_meta = row["metadata_json"]
    meta: dict[str, Any] = {}
    if raw_meta:
        try:
            meta = json.loads(str(raw_meta))
        except json.JSONDecodeError, TypeError:
            meta = {}

    sim_seq = int(row["sim_sequence"]) if row["sim_sequence"] is not None else None
    sim_bal = (
        float(row["sim_initial_balance_decimal"])
        if row["sim_initial_balance_decimal"] is not None
        else _DEFAULT_BALANCE
    )
    sim_lev = (
        int(row["sim_leverage"])
        if row["sim_leverage"] is not None
        else _DEFAULT_LEVERAGE
    )

    return {
        "session_id": str(row["session_id"]),
        "principal_id": str(row["principal_id"]),
        "environment_id": str(row["environment_id"]),
        "name": str(row["name"]),
        "description": str(row["description"] or ""),
        "mode": str(row["mode"]),
        "provider": str(row["provider"]),
        "provider_account_ref": row["provider_account_ref"],
        "credential_ref": row["credential_ref"],
        "simulation_session_id": row["simulation_session_id"],
        "sim_sequence": sim_seq,
        "simulation_runtime_ref": row["simulation_runtime_ref"],
        "dataset_ref": row["dataset_ref"],
        "dataset_revision": row["dataset_revision"],
        "dataset_hash": row["dataset_hash"],
        "sim_initial_balance": sim_bal,
        "sim_leverage": sim_lev,
        "sim_account_currency": str(row["sim_account_currency"] or "USD"),
        "lifecycle_state": str(row["lifecycle_state"]),
        "recovery_state": str(row["recovery_state"]),
        "is_default": bool(row["is_default"]),
        "is_active": bool(row["is_active"]),
        "auto_start": bool(row["auto_start"]),
        "metadata": meta,
        "last_error_code": row["last_error_code"],
        "last_reconciled_at": row["last_reconciled_at"],
        "started_at": row["started_at"],
        "stopped_at": row["stopped_at"],
        "archived_at": row["archived_at"],
        "version": int(row["version"]),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


def list_execution_sessions(
    principal_id: str | None = None,
    mode: str | None = None,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List execution sessions matching principal and mode.

    Args:
        principal_id: Calling principal identity.
        mode: Trading mode filter ("sim", "paper", "live").
        db_path: Optional explicit database path.

    Returns:
        List of execution session records.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM trading_sessions WHERE archived_at IS NULL"
        params: list[Any] = []
        if principal_id:
            sql += " AND (principal_id = ? OR principal_id = 'usr_haruquantai')"
            params.append(principal_id)
        if mode:
            sql += " AND mode = ?"
            params.append(mode)
        sql += " ORDER BY is_default DESC, created_at DESC"

        cur.execute(sql, params)
        rows = cur.fetchall()

        if not rows:
            now = _utc_now_iso()
            sid = f"id-{uuid4().hex}"
            pid = principal_id or "usr_haruquantai"
            cur.execute(
                """
                INSERT INTO trading_sessions (
                    session_id, principal_id, environment_id, name, description,
                    mode, provider, provider_account_ref, credential_ref,
                    simulation_session_id, dataset_ref, dataset_revision,
                    dataset_hash, lifecycle_state, recovery_state,
                    is_default, is_active, auto_start, metadata_json,
                    last_error_code, last_reconciled_at, started_at, stopped_at,
                    archived_at, version, created_at, updated_at,
                    sim_initial_balance_decimal, sim_leverage,
                    sim_account_currency, sim_sequence, simulation_runtime_ref
                ) VALUES (
                    ?, ?, 'development', 'Default Simulation',
                    'Default seeded SIM session', 'sim', 'simulation',
                    'haruquantai_sim', 'cred-sim', 'sim-default-01',
                    'dataset-default', 'rev-1', 'hash-default', 'stopped',
                    'not_required', 1, 0, 1, '{}', NULL, NULL, NULL, NULL,
                    NULL, 1, ?, ?, '100000', 100, 'USD', 1,
                    'sim_runtime_default'
                )
                """,
                (sid, pid, now, now),
            )
            conn.commit()

            cur.execute(sql, params)
            rows = cur.fetchall()

        return [_row_to_session_dict(r) for r in rows]
    finally:
        conn.close()


def get_active_or_default_session(
    principal_id: str | None = None,
    mode: str = "sim",
    db_path: Path | str | None = None,
) -> dict[str, Any] | None:
    """Return the active session for mode, falling back to per-mode default.

    Args:
        principal_id: Calling principal identity.
        mode: Trading mode filter.
        db_path: Optional explicit database path.

    Returns:
        Active or default session dictionary if available, None otherwise.
    """
    sessions = list_execution_sessions(
        principal_id=principal_id, mode=mode, db_path=db_path
    )
    if not sessions:
        return None
    active = next((s for s in sessions if s.get("is_active")), None)
    if active:
        return active
    default_session = next((s for s in sessions if s.get("is_default")), None)
    if default_session:
        return default_session
    return sessions[0]


def get_account_profile(
    principal_id: str | None = None,
    username: str = "haruquantai",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Return provider-authored or simulated account profile for the Header.

    Args:
        principal_id: Calling principal identity.
        username: Username for account profile display.
        db_path: Optional explicit database path.

    Returns:
        Structured trading account profile dictionary.
    """
    session = get_active_or_default_session(
        principal_id=principal_id, mode="sim", db_path=db_path
    )
    balance = float(session["sim_initial_balance"]) if session else _DEFAULT_BALANCE
    leverage = (
        float(session["sim_leverage"])
        if session and session["sim_leverage"]
        else float(_DEFAULT_LEVERAGE)
    )
    currency = (
        str(session["sim_account_currency"])
        if session and session["sim_account_currency"]
        else "USD"
    )
    session_name = str(session["name"]) if session else "Default Simulation"

    return {
        "contract_version": "v1",
        "schema_id": "api.trading.account_profile.v1",
        "account_name": username or "haruquantai",
        "session_name": session_name,
        "trade_mode": "SIMULATION",
        "selected_mode": "sim",
        "mode_compatible": True,
        "environment_label": "Simulation Environment",
        "source": "simulator",
        "currency": currency,
        "balance": balance,
        "equity": balance,
        "profit": 0.0,
        "margin": 0.0,
        "free_margin": balance,
        "margin_level": None,
        "leverage": leverage,
        "retrieved_at": _utc_now_iso(),
    }


def get_instrument_constraints(
    symbol: str,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Return constraints for one trading symbol from instruments table.

    Args:
        symbol: Market symbol identifier.
        db_path: Optional explicit database path.

    Returns:
        Trading constraints dictionary.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                canonical_symbol, digits, tick_size_decimal, min_volume_decimal,
                max_volume_decimal, volume_step_decimal, contract_size_decimal,
                quote_currency
            FROM instruments
            WHERE canonical_symbol = ? OR symbol_id = ?
            """,
            (symbol, symbol),
        )
        row = cur.fetchone()
        if row is None:
            return {
                "contract_version": "v1",
                "schema_id": "api.trading.instrument_constraints.v1",
                "symbol": symbol,
                "source_id": "mt5",
                "quantity_unit": "lots",
                "min_quantity": "0.01",
                "max_quantity": "100.0",
                "quantity_step": "0.01",
                "price_tick": "0.00001",
                "digits": 5,
                "pip_size": 0.0001,
                "trade_tick_size": 0.00001,
                "trade_tick_value_profit": 1.0,
                "trade_tick_value_loss": 1.0,
                "trade_contract_size": _DEFAULT_BALANCE,
                "profit_currency": "USD",
                "supported_order_types": [
                    "MARKET",
                    "LIMIT",
                    "STOP",
                    "STOP_LIMIT",
                ],
                "supported_time_in_force": ["IOC", "FOK"],
                "supports_stop_loss": True,
                "supports_take_profit": True,
                "retrieved_at": _utc_now_iso(),
            }

        digits = int(row["digits"]) if row["digits"] is not None else 5
        point = 10 ** (-digits)
        pip_size = point * 10.0 if digits in (3, 5) else point
        contract_size = (
            float(row["contract_size_decimal"])
            if row["contract_size_decimal"]
            else _DEFAULT_BALANCE
        )

        return {
            "contract_version": "v1",
            "schema_id": "api.trading.instrument_constraints.v1",
            "symbol": str(row["canonical_symbol"]),
            "source_id": "mt5",
            "quantity_unit": "lots",
            "min_quantity": str(row["min_volume_decimal"] or "0.01"),
            "max_quantity": str(row["max_volume_decimal"] or "100.0"),
            "quantity_step": str(row["volume_step_decimal"] or "0.01"),
            "price_tick": str(row["tick_size_decimal"] or point),
            "digits": digits,
            "pip_size": pip_size,
            "trade_tick_size": float(row["tick_size_decimal"] or point),
            "trade_tick_value_profit": 1.0,
            "trade_tick_value_loss": 1.0,
            "trade_contract_size": contract_size,
            "profit_currency": str(row["quote_currency"] or "USD"),
            "supported_order_types": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
            "supported_time_in_force": ["IOC", "FOK"],
            "supports_stop_loss": True,
            "supports_take_profit": True,
            "retrieved_at": _utc_now_iso(),
        }
    finally:
        conn.close()


def set_default_session(
    session_id: str,
    principal_id: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Set one session as the default for its mode and principal.

    Args:
        session_id: Session unique identifier.
        principal_id: Optional principal identifier.
        db_path: Optional explicit database path.

    Returns:
        Updated session record dictionary.

    Raises:
        LookupError: If session_id does not exist.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT mode, principal_id FROM trading_sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError("SESSION_NOT_FOUND")

        mode = str(row["mode"])
        actual_principal = principal_id or str(row["principal_id"])
        now = _utc_now_iso()

        cur.execute(
            """
            UPDATE trading_sessions
            SET is_default = 0, updated_at = ?
            WHERE mode = ? AND principal_id = ?
            """,
            (now, mode, actual_principal),
        )
        cur.execute(
            """
            UPDATE trading_sessions
            SET is_default = 1, updated_at = ?
            WHERE session_id = ?
            """,
            (now, session_id),
        )
        conn.commit()

        cur.execute(
            "SELECT * FROM trading_sessions WHERE session_id = ?",
            (session_id,),
        )
        return _row_to_session_dict(cur.fetchone())
    finally:
        conn.close()


def start_session(
    session_id: str,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Mark session as started and active.

    Args:
        session_id: Session unique identifier.
        db_path: Optional explicit database path.

    Returns:
        Updated session record dictionary.

    Raises:
        LookupError: If session_id does not exist.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        now = _utc_now_iso()
        cur.execute(
            """
            UPDATE trading_sessions
            SET lifecycle_state = 'running', is_active = 1,
                started_at = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (now, now, session_id),
        )
        conn.commit()
        cur.execute(
            "SELECT * FROM trading_sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError("SESSION_NOT_FOUND")
        return _row_to_session_dict(row)
    finally:
        conn.close()


def stop_session(
    session_id: str,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Mark session as stopped and inactive.

    Args:
        session_id: Session unique identifier.
        db_path: Optional explicit database path.

    Returns:
        Updated session record dictionary.

    Raises:
        LookupError: If session_id does not exist.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        now = _utc_now_iso()
        cur.execute(
            """
            UPDATE trading_sessions
            SET lifecycle_state = 'stopped', is_active = 0,
                stopped_at = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (now, now, session_id),
        )
        conn.commit()
        cur.execute(
            "SELECT * FROM trading_sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError("SESSION_NOT_FOUND")
        return _row_to_session_dict(row)
    finally:
        conn.close()

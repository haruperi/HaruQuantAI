"""Trading execution sessions and account profile service.

Purpose:
    Own the workstation's trading execution sessions, default session
    selection, lifecycle state transitions, account profile projections,
    and instrument constraints behind the
    ``trading.manage-execution-sessions@1`` capability.

Key capabilities:
    * List execution sessions matching principal and mode, seeding the
      default SIM session when no records exist.
    * Select active or default sessions.
    * Trigger state transitions (default, start, stop).
    * Project account balance and leverage for trading headers.
    * Project symbol trading constraints.

Python API usage:
    service = ExecutionSessionsService(ManageExecutionSessionsConfig())
    result = await service.manage_execution_sessions(request)

CLI usage:
    uv run python -m app.services.trading.manage_execution_sessions.execution_sessions
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast
from uuid import uuid4

from app.contracts.common.models import ProblemDetails
from app.contracts.trading.errors import TradingFailure
from app.contracts.trading.models import (
    AccountProfileRecord,
    ExecutionSessionRecord,
    InstrumentConstraintsRecord,
    ManageExecutionSessionsRequest,
    ManageExecutionSessionsSuccess,
)
from app.services.trading.manage_execution_sessions.config import (
    ManageExecutionSessionsConfig,
)

if TYPE_CHECKING:
    from app.contracts.common.models import JsonObject

_DEFAULT_BALANCE: Final[float] = 100000.0
_DEFAULT_LEVERAGE: Final[int] = 100
_SUBPATH_PARTS: Final[int] = 2


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 string representation.

    Returns:
        ISO-8601 formatted datetime string.
    """
    return datetime.now(UTC).isoformat()


def _row_to_session_record(row: sqlite3.Row) -> ExecutionSessionRecord:
    """Convert a database row from trading_profiles into an ExecutionSessionRecord.

    Args:
        row: SQLite database row.

    Returns:
        Structured ExecutionSessionRecord model.
    """
    raw_meta = row["metadata_json"]
    meta: dict[str, object] = {}
    if raw_meta:
        try:
            parsed = json.loads(str(raw_meta))
            if isinstance(parsed, dict):
                meta = parsed
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

    return ExecutionSessionRecord(
        session_id=str(row["session_id"]),
        principal_id=str(row["principal_id"]),
        environment_id=str(row["environment_id"]),
        name=str(row["name"]),
        description=str(row["description"] or ""),
        mode=str(row["mode"]),
        provider=str(row["provider"]),
        provider_account_ref=(
            str(row["provider_account_ref"])
            if row["provider_account_ref"] is not None
            else None
        ),
        credential_ref=(
            str(row["credential_ref"]) if row["credential_ref"] is not None else None
        ),
        simulation_session_id=(
            str(row["simulation_session_id"])
            if row["simulation_session_id"] is not None
            else None
        ),
        sim_sequence=sim_seq,
        simulation_runtime_ref=(
            str(row["simulation_runtime_ref"])
            if row["simulation_runtime_ref"] is not None
            else None
        ),
        dataset_ref=(
            str(row["dataset_ref"]) if row["dataset_ref"] is not None else None
        ),
        dataset_revision=(
            str(row["dataset_revision"])
            if row["dataset_revision"] is not None
            else None
        ),
        dataset_hash=(
            str(row["dataset_hash"]) if row["dataset_hash"] is not None else None
        ),
        sim_initial_balance=sim_bal,
        sim_leverage=sim_lev,
        sim_account_currency=str(row["sim_account_currency"] or "USD"),
        lifecycle_state=str(row["lifecycle_state"]),
        recovery_state=str(row["recovery_state"]),
        is_default=bool(row["is_default"]),
        is_active=bool(row["is_active"]),
        auto_start=bool(row["auto_start"]),
        metadata=cast("JsonObject", meta),
        last_error_code=(
            str(row["last_error_code"]) if row["last_error_code"] is not None else None
        ),
        last_reconciled_at=(
            str(row["last_reconciled_at"])
            if row["last_reconciled_at"] is not None
            else None
        ),
        started_at=(str(row["started_at"]) if row["started_at"] is not None else None),
        stopped_at=(str(row["stopped_at"]) if row["stopped_at"] is not None else None),
        archived_at=(
            str(row["archived_at"]) if row["archived_at"] is not None else None
        ),
        version=int(row["version"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


class ExecutionSessionsService:
    """Execution sessions store and management service."""

    def __init__(self, config: ManageExecutionSessionsConfig | None = None) -> None:
        """Open the trading database and ensure required schemas exist.

        Args:
            config: Service configuration carrying the database path.
        """
        self._config = config or ManageExecutionSessionsConfig()
        target = Path(self._config.database_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(target), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._closed = False
        self._init_db()

    @property
    def closed(self) -> bool:
        """Return True if the service connection is closed."""
        return self._closed

    def close(self) -> None:
        """Close SQLite database connection cleanly."""
        self._closed = True
        self._conn.close()

    def _init_db(self) -> None:
        """Create trading_profiles and instruments tables when missing."""
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_profiles (
                    session_id TEXT PRIMARY KEY,
                    principal_id TEXT NOT NULL,
                    environment_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    mode TEXT NOT NULL CHECK(mode IN ('sim','demo','live')),
                    provider TEXT NOT NULL,
                    provider_account_ref TEXT,
                    credential_ref TEXT,
                    simulation_session_id TEXT,
                    dataset_ref TEXT,
                    dataset_revision TEXT,
                    dataset_hash TEXT,
                    lifecycle_state TEXT NOT NULL,
                    recovery_state TEXT NOT NULL,
                    is_default INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    auto_start INTEGER NOT NULL DEFAULT 1,
                    metadata_json TEXT NOT NULL,
                    last_error_code TEXT,
                    last_reconciled_at TEXT,
                    started_at TEXT,
                    stopped_at TEXT,
                    archived_at TEXT,
                    version INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    sim_initial_balance_decimal TEXT,
                    sim_leverage INTEGER,
                    sim_account_currency TEXT,
                    sim_sequence INTEGER,
                    simulation_runtime_ref TEXT
                );
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS instruments (
                    name TEXT PRIMARY KEY,
                    digits INTEGER,
                    point REAL,
                    spread REAL,
                    trade_contract_size REAL,
                    trade_tick_size REAL,
                    trade_tick_value_profit REAL,
                    trade_tick_value_loss REAL,
                    volume_min REAL,
                    volume_max REAL,
                    volume_step REAL,
                    currency_profit TEXT
                );
                """
            )

    def list_execution_sessions(
        self,
        principal_id: str | None = None,
        mode: str | None = None,
    ) -> list[ExecutionSessionRecord]:
        """List execution sessions matching principal and mode.

        Args:
            principal_id: Calling principal identity.
            mode: Trading mode filter.

        Returns:
            List of execution session records.
        """
        cur = self._conn.cursor()
        sql = "SELECT * FROM trading_profiles WHERE archived_at IS NULL"
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
            with self._conn:
                self._conn.execute(
                    """
                    INSERT INTO trading_profiles (
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

            cur.execute(sql, params)
            rows = cur.fetchall()

        return [_row_to_session_record(r) for r in rows]

    def get_active_or_default_session(
        self,
        principal_id: str | None = None,
        mode: str = "sim",
    ) -> ExecutionSessionRecord | None:
        """Return the active session for mode, falling back to per-mode default.

        Args:
            principal_id: Calling principal identity.
            mode: Trading mode filter.

        Returns:
            Active or default session record if available, None otherwise.
        """
        sessions = self.list_execution_sessions(principal_id=principal_id, mode=mode)
        if not sessions:
            return None
        active = next((s for s in sessions if s.is_active), None)
        if active is not None:
            return active
        default_session = next((s for s in sessions if s.is_default), None)
        if default_session is not None:
            return default_session
        return sessions[0]

    def set_default_session(
        self,
        session_id: str,
        principal_id: str | None = None,
    ) -> ExecutionSessionRecord:
        """Set one session as the default for its mode and principal.

        Args:
            session_id: Session unique identifier.
            principal_id: Optional principal identifier.

        Returns:
            Updated session record.

        Raises:
            LookupError: If session_id does not exist.
        """
        cur = self._conn.cursor()
        cur.execute(
            "SELECT mode, principal_id FROM trading_profiles WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        if row is None:
            message = f"Session '{session_id}' was not found."
            raise LookupError(message)

        mode = str(row["mode"])
        actual_principal = principal_id or str(row["principal_id"])
        now = _utc_now_iso()

        with self._conn:
            self._conn.execute(
                """
                UPDATE trading_profiles
                SET is_default = 0, updated_at = ?
                WHERE mode = ? AND principal_id = ?
                """,
                (now, mode, actual_principal),
            )
            self._conn.execute(
                """
                UPDATE trading_profiles
                SET is_default = 1, updated_at = ?
                WHERE session_id = ?
                """,
                (now, session_id),
            )

        cur.execute(
            "SELECT * FROM trading_profiles WHERE session_id = ?",
            (session_id,),
        )
        updated_row = cur.fetchone()
        return _row_to_session_record(updated_row)

    def start_session(self, session_id: str) -> ExecutionSessionRecord:
        """Mark session as started and active.

        Args:
            session_id: Session unique identifier.

        Returns:
            Updated session record.

        Raises:
            LookupError: If session_id does not exist.
        """
        now = _utc_now_iso()
        with self._conn:
            cur = self._conn.execute(
                """
                UPDATE trading_profiles
                SET lifecycle_state = 'running', is_active = 1,
                    started_at = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (now, now, session_id),
            )
            if cur.rowcount == 0:
                message = f"Session '{session_id}' was not found."
                raise LookupError(message)

        row = self._conn.execute(
            "SELECT * FROM trading_profiles WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return _row_to_session_record(row)

    def stop_session(self, session_id: str) -> ExecutionSessionRecord:
        """Mark session as stopped and inactive.

        Args:
            session_id: Session unique identifier.

        Returns:
            Updated session record.

        Raises:
            LookupError: If session_id does not exist.
        """
        now = _utc_now_iso()
        with self._conn:
            cur = self._conn.execute(
                """
                UPDATE trading_profiles
                SET lifecycle_state = 'stopped', is_active = 0,
                    stopped_at = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (now, now, session_id),
            )
            if cur.rowcount == 0:
                message = f"Session '{session_id}' was not found."
                raise LookupError(message)

        row = self._conn.execute(
            "SELECT * FROM trading_profiles WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return _row_to_session_record(row)

    def get_account_profile(
        self,
        principal_id: str | None = None,
        username: str = "haruquantai",
    ) -> AccountProfileRecord:
        """Return provider-authored or simulated account profile for Header.

        Args:
            principal_id: Calling principal identity.
            username: Username for account profile display.

        Returns:
            Structured AccountProfileRecord.
        """
        session = self.get_active_or_default_session(
            principal_id=principal_id, mode="sim"
        )
        balance = session.sim_initial_balance if session else _DEFAULT_BALANCE
        leverage = (
            float(session.sim_leverage)
            if session and session.sim_leverage
            else float(_DEFAULT_LEVERAGE)
        )
        currency = (
            session.sim_account_currency
            if session and session.sim_account_currency
            else "USD"
        )
        session_name = session.name if session else "Default Simulation"

        return AccountProfileRecord(
            account_name=username or "haruquantai",
            session_name=session_name,
            trade_mode="SIMULATION",
            selected_mode="sim",
            mode_compatible=True,
            environment_label="Simulation Environment",
            source="simulator",
            currency=currency,
            balance=balance,
            equity=balance,
            profit=0.0,
            margin=0.0,
            free_margin=balance,
            margin_level=None,
            leverage=leverage,
            retrieved_at=_utc_now_iso(),
        )

    def get_instrument_constraints(
        self,
        symbol: str,
    ) -> InstrumentConstraintsRecord:
        """Return constraints for one trading symbol from instruments table.

        Args:
            symbol: Market symbol identifier.

        Returns:
            InstrumentConstraintsRecord.
        """
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT
                name AS canonical_symbol,
                digits,
                point,
                spread,
                trade_contract_size,
                trade_tick_size,
                trade_tick_value_profit,
                trade_tick_value_loss,
                volume_min,
                volume_max,
                volume_step,
                currency_profit
            FROM instruments
            WHERE name = ?
            """,
            (symbol,),
        )
        row = cur.fetchone()
        if row is None:
            return InstrumentConstraintsRecord(
                symbol=symbol,
                source_id="mt5",
                quantity_unit="lots",
                min_quantity="0.01",
                max_quantity="100.0",
                quantity_step="0.01",
                price_tick="0.00001",
                digits=5,
                pip_size=0.0001,
                trade_tick_size=0.00001,
                trade_tick_value_profit=1.0,
                trade_tick_value_loss=1.0,
                trade_contract_size=_DEFAULT_BALANCE,
                profit_currency="USD",
                supported_order_types=("MARKET", "LIMIT", "STOP", "STOP_LIMIT"),
                supported_time_in_force=("IOC", "FOK"),
                supports_stop_loss=True,
                supports_take_profit=True,
                retrieved_at=_utc_now_iso(),
            )

        digits = int(row["digits"]) if row["digits"] is not None else 5
        point = float(row["point"]) if row["point"] is not None else 10 ** (-digits)
        pip_size = point * 10.0 if digits in (3, 5) else point
        contract_size = (
            float(row["trade_contract_size"])
            if row["trade_contract_size"]
            else _DEFAULT_BALANCE
        )
        tick_size = float(row["trade_tick_size"]) if row["trade_tick_size"] else point

        return InstrumentConstraintsRecord(
            symbol=str(row["canonical_symbol"]),
            source_id="mt5",
            quantity_unit="lots",
            min_quantity=str(row["volume_min"] or "0.01"),
            max_quantity=str(row["volume_max"] or "100.0"),
            quantity_step=str(row["volume_step"] or "0.01"),
            price_tick=str(tick_size),
            digits=digits,
            pip_size=pip_size,
            trade_tick_size=tick_size,
            trade_tick_value_profit=(
                float(row["trade_tick_value_profit"])
                if row["trade_tick_value_profit"] is not None
                else 1.0
            ),
            trade_tick_value_loss=(
                float(row["trade_tick_value_loss"])
                if row["trade_tick_value_loss"] is not None
                else 1.0
            ),
            trade_contract_size=contract_size,
            profit_currency=str(row["currency_profit"] or "USD"),
            supported_order_types=("MARKET", "LIMIT", "STOP", "STOP_LIMIT"),
            supported_time_in_force=("IOC", "FOK"),
            supports_stop_loss=True,
            supports_take_profit=True,
            retrieved_at=_utc_now_iso(),
        )

    async def manage_execution_sessions(  # noqa: C901, PLR0911, PLR0912
        self,
        request: ManageExecutionSessionsRequest,
    ) -> ManageExecutionSessionsSuccess | TradingFailure:
        """Handle execution session operations.

        Args:
            request: Operation-discriminated request.

        Returns:
            Success envelope or structured trading failure.
        """
        match request.operation:
            case "LIST_SESSIONS":
                sessions = self.list_execution_sessions(
                    principal_id=request.principal_id,
                    mode=request.mode,
                )
                return ManageExecutionSessionsSuccess(
                    request_id=request.request_id,
                    sessions=tuple(sessions),
                )

            case "GET_ACTIVE_OR_DEFAULT":
                session = self.get_active_or_default_session(
                    principal_id=request.principal_id,
                    mode=request.mode or "sim",
                )
                return ManageExecutionSessionsSuccess(
                    request_id=request.request_id,
                    session=session,
                )

            case "SET_DEFAULT":
                if not request.session_id:
                    return TradingFailure(
                        request_id=request.request_id,
                        code="TRADING_VALIDATION_FAILED",
                        problem=ProblemDetails(
                            title="Validation failed",
                            status=400,
                            code="TRADING_VALIDATION_FAILED",
                            detail="session_id is required for SET_DEFAULT",
                        ),
                    )
                try:
                    updated = self.set_default_session(
                        request.session_id, principal_id=request.principal_id
                    )
                    return ManageExecutionSessionsSuccess(
                        request_id=request.request_id,
                        session=updated,
                    )
                except LookupError:
                    return TradingFailure(
                        request_id=request.request_id,
                        code="TRADING_STATE_CONFLICT",
                        problem=ProblemDetails(
                            title="Session not found",
                            status=404,
                            code="SESSION_NOT_FOUND",
                            detail="Session not found",
                        ),
                    )

            case "START_SESSION":
                if not request.session_id:
                    return TradingFailure(
                        request_id=request.request_id,
                        code="TRADING_VALIDATION_FAILED",
                        problem=ProblemDetails(
                            title="Validation failed",
                            status=400,
                            code="TRADING_VALIDATION_FAILED",
                            detail="session_id is required for START_SESSION",
                        ),
                    )
                try:
                    started = self.start_session(request.session_id)
                    return ManageExecutionSessionsSuccess(
                        request_id=request.request_id,
                        session=started,
                    )
                except LookupError:
                    return TradingFailure(
                        request_id=request.request_id,
                        code="TRADING_STATE_CONFLICT",
                        problem=ProblemDetails(
                            title="Session not found",
                            status=404,
                            code="SESSION_NOT_FOUND",
                            detail="Session not found",
                        ),
                    )

            case "STOP_SESSION":
                if not request.session_id:
                    return TradingFailure(
                        request_id=request.request_id,
                        code="TRADING_VALIDATION_FAILED",
                        problem=ProblemDetails(
                            title="Validation failed",
                            status=400,
                            code="TRADING_VALIDATION_FAILED",
                            detail="session_id is required for STOP_SESSION",
                        ),
                    )
                try:
                    stopped = self.stop_session(request.session_id)
                    return ManageExecutionSessionsSuccess(
                        request_id=request.request_id,
                        session=stopped,
                    )
                except LookupError:
                    return TradingFailure(
                        request_id=request.request_id,
                        code="TRADING_STATE_CONFLICT",
                        problem=ProblemDetails(
                            title="Session not found",
                            status=404,
                            code="SESSION_NOT_FOUND",
                            detail="Session not found",
                        ),
                    )

            case "GET_ACCOUNT_PROFILE":
                profile = self.get_account_profile(
                    principal_id=request.principal_id,
                    username=request.username or "haruquantai",
                )
                return ManageExecutionSessionsSuccess(
                    request_id=request.request_id,
                    profile=profile,
                )

            case "GET_INSTRUMENT_CONSTRAINTS":
                constraints = self.get_instrument_constraints(
                    symbol=request.symbol or "EURUSD",
                )
                return ManageExecutionSessionsSuccess(
                    request_id=request.request_id,
                    constraints=constraints,
                )

            case _:
                return TradingFailure(  # type: ignore[unreachable]
                    request_id=request.request_id,
                    code="TRADING_QUERY_INVALID",
                    problem=ProblemDetails(
                        title="Invalid operation",
                        status=400,
                        code="TRADING_QUERY_INVALID",
                        detail=f"Unsupported operation: {request.operation}",
                    ),
                )


def run_demonstration() -> None:
    """Execute bounded usage demonstration of ExecutionSessionsService."""
    import asyncio
    from uuid import uuid7

    async def _demo() -> None:
        service = ExecutionSessionsService(ManageExecutionSessionsConfig())
        req = ManageExecutionSessionsRequest(
            request_id=str(uuid7()),
            capability_snapshot_id=str(uuid7()),
            operation="LIST_SESSIONS",
        )
        res = await service.manage_execution_sessions(req)
        count = (
            len(res.sessions) if isinstance(res, ManageExecutionSessionsSuccess) else 0
        )
        print("Execution sessions count:", count)
        service.close()

    asyncio.run(_demo())


if __name__ == "__main__":
    run_demonstration()

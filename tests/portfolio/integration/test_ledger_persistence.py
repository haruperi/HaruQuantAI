"""Integration evidence for durable Portfolio ledger state (``FEAT-PORT-09``).

Verifies the migration step ``002_portfolio_ledger_schema`` applies through
Data's ledger-verified, write-locked, transactional runner, and that ledger
accounts, balanced batches, and their legs are durably persisted and rebuilt
identically (``feature``, ``feature``, ``feature``,
``feature``; REACH gate).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from app.services.data import (
    build_data_settings,
    build_statement_plan,
    build_transaction_request,
    data_settings_context,
    execute_transaction,
    unwrap_data_response,
)
from app.services.portfolio import (
    build_ledger_account,
    build_portfolio_state_store,
    build_posting_batch,
    execute_portfolio_state_store_operation,
    run_portfolio_migrations,
)
from app.utils import generate_id

_LEDGER_TABLES = {
    "portfolio_ledger_accounts": (
        "SELECT COUNT(*) AS row_count FROM portfolio_ledger_accounts"
    ),
    "portfolio_ledger_posting_batches": (
        "SELECT COUNT(*) AS row_count FROM portfolio_ledger_posting_batches"
    ),
    "portfolio_ledger_entries": (
        "SELECT COUNT(*) AS row_count FROM portfolio_ledger_entries"
    ),
    "portfolio_ledger_balances": (
        "SELECT COUNT(*) AS row_count FROM portfolio_ledger_balances"
    ),
    "portfolio_ledger_snapshots": (
        "SELECT COUNT(*) AS row_count FROM portfolio_ledger_snapshots"
    ),
}

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///portfolio-ledger.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _run_portfolio_migrations() -> None:
    """Apply the Portfolio manifest through Data's public executor."""
    request_id = generate_id("req")
    unwrap_data_response(
        run_portfolio_migrations(request_id),
        operation="tests.portfolio.ledger.migrations",
        request_id=request_id,
    )


def _row_count(table: str) -> int:
    """Return one bounded table row count through Data's public executor."""
    request_id = generate_id("req")
    result = unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(_LEDGER_TABLES[table],),
                    parameter_sets=((),),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="tests.portfolio.ledger.row_count",
        request_id=request_id,
    )
    return int(result.rows[0]["row_count"])


def _ledger_account_mapping() -> dict[str, object]:
    """Return one complete ledger account mapping."""
    return build_ledger_account(
        account_id="cash-usd",
        portfolio_id="portfolio-alpha",
        currency="USD",
        normal_balance="debit",
        category="asset",
        registered_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-22222222-2222-4222-8222-222222222222",
    )


def _posting_batch_mapping() -> dict[str, object]:
    """Return one balanced posting-batch mapping with normalized legs."""
    return build_posting_batch(
        batch_id="batch-deposit-1",
        source_event_id="event-deposit-1",
        source_sequence=1,
        entry_sequence=1,
        entries=(
            {
                "entry_id": "leg-cash-debit",
                "account_id": "cash-usd",
                "side": "debit",
                "amount": Decimal(1000),
                "currency": "USD",
                "posting_type": "deposit",
            },
            {
                "entry_id": "leg-equity-credit",
                "account_id": "owner-equity",
                "side": "credit",
                "amount": Decimal(1000),
                "currency": "USD",
                "posting_type": "deposit",
            },
        ),
        posted_at=NOW,
        canonical_hash="a" * 64,
        request_id="req-33333333-3333-4333-8333-333333333333",
        correlation_id="cor-44444444-4444-4444-8444-444444444444",
    )


def test_ledger_migration_creates_all_five_ledger_tables(tmp_path: Path) -> None:
    """The 002 ledger step applies through Data and creates all five tables."""
    with data_settings_context(_settings(tmp_path)):
        _run_portfolio_migrations()
        for table in _LEDGER_TABLES:
            assert _row_count(table) == 0, f"{table} should exist and be empty"


def test_ledger_account_is_durable_and_rebuildable(tmp_path: Path) -> None:
    """A registered account survives adapter reconstruction."""
    with data_settings_context(_settings(tmp_path)):
        _run_portfolio_migrations()
        store = build_portfolio_state_store()
        account = _ledger_account_mapping()
        execute_portfolio_state_store_operation(
            store,
            "save_ledger_account",
            account,
            {"event": "portfolio.ledger.account.registered"},
        )
        assert _row_count("portfolio_ledger_accounts") == 1
        reconstructed = build_portfolio_state_store()
        loaded: Any = execute_portfolio_state_store_operation(
            reconstructed,
            "load_ledger_account",
            "cash-usd",
        )
        assert loaded is not None
        assert loaded["account_id"] == "cash-usd"
        assert loaded["currency"] == "USD"


def test_ledger_batch_and_entries_persist_atomically(tmp_path: Path) -> None:
    """A balanced batch and its legs commit atomically and rebuild identically."""
    with data_settings_context(_settings(tmp_path)):
        _run_portfolio_migrations()
        store = build_portfolio_state_store()
        account = _ledger_account_mapping()
        execute_portfolio_state_store_operation(
            store,
            "save_ledger_account",
            account,
            {"event": "portfolio.ledger.account.registered"},
        )
        batch = _posting_batch_mapping()
        entry_rows = tuple(
            (
                str(leg["entry_id"]),
                str(batch["batch_id"]),
                int(batch["entry_sequence"]),
                str(leg["account_id"]),
                str(leg["side"]),
                str(leg["amount"]),
                str(leg["currency"]),
                str(leg["posting_type"]),
                NOW.isoformat(),
                str(batch["request_id"]),
                str(batch["correlation_id"]),
                NOW.isoformat(),
            )
            for leg in batch["entries"]
        )
        execute_portfolio_state_store_operation(
            store,
            "save_ledger_batch",
            batch,
            entry_rows,
            {"event": "portfolio.ledger.batch.posted"},
        )
        assert _row_count("portfolio_ledger_posting_batches") == 1
        assert _row_count("portfolio_ledger_entries") == 2
        reconstructed = build_portfolio_state_store()
        loaded_batch: Any = execute_portfolio_state_store_operation(
            reconstructed,
            "load_ledger_batch",
            "event-deposit-1",
            1,
        )
        assert loaded_batch is not None
        assert loaded_batch["batch_id"] == "batch-deposit-1"
        legs: Any = execute_portfolio_state_store_operation(
            reconstructed,
            "load_ledger_entries",
            "cash-usd",
        )
        assert len(legs) == 1
        assert legs[0]["side"] == "debit"
        assert Decimal(str(legs[0]["amount"])) == Decimal(1000)


def test_ledger_batch_replay_with_identical_material_is_idempotent(
    tmp_path: Path,
) -> None:
    """Replaying a batch with identical material is a no-op (exactly-once)."""
    with data_settings_context(_settings(tmp_path)):
        _run_portfolio_migrations()
        store = build_portfolio_state_store()
        account = _ledger_account_mapping()
        execute_portfolio_state_store_operation(
            store,
            "save_ledger_account",
            account,
            {"event": "portfolio.ledger.account.registered"},
        )
        batch = _posting_batch_mapping()
        entry_rows = tuple(
            (
                str(leg["entry_id"]),
                str(batch["batch_id"]),
                int(batch["entry_sequence"]),
                str(leg["account_id"]),
                str(leg["side"]),
                str(leg["amount"]),
                str(leg["currency"]),
                str(leg["posting_type"]),
                NOW.isoformat(),
                str(batch["request_id"]),
                str(batch["correlation_id"]),
                NOW.isoformat(),
            )
            for leg in batch["entries"]
        )
        execute_portfolio_state_store_operation(
            store,
            "save_ledger_batch",
            batch,
            entry_rows,
            {"event": "portfolio.ledger.batch.posted"},
        )
        # Replay identical batch -> idempotent, no new rows.
        execute_portfolio_state_store_operation(
            store,
            "save_ledger_batch",
            batch,
            entry_rows,
            {"event": "portfolio.ledger.batch.posted"},
        )
        assert _row_count("portfolio_ledger_posting_batches") == 1
        assert _row_count("portfolio_ledger_entries") == 2


def test_ledger_batch_conflict_on_differing_material_is_rejected(
    tmp_path: Path,
) -> None:
    """A conflicting batch under the same event identity fails closed."""
    with data_settings_context(_settings(tmp_path)):
        _run_portfolio_migrations()
        store = build_portfolio_state_store()
        account = _ledger_account_mapping()
        execute_portfolio_state_store_operation(
            store,
            "save_ledger_account",
            account,
            {"event": "portfolio.ledger.account.registered"},
        )
        batch = _posting_batch_mapping()
        entry_rows = tuple(
            (
                str(leg["entry_id"]),
                str(batch["batch_id"]),
                int(batch["entry_sequence"]),
                str(leg["account_id"]),
                str(leg["side"]),
                str(leg["amount"]),
                str(leg["currency"]),
                str(leg["posting_type"]),
                NOW.isoformat(),
                str(batch["request_id"]),
                str(batch["correlation_id"]),
                NOW.isoformat(),
            )
            for leg in batch["entries"]
        )
        execute_portfolio_state_store_operation(
            store,
            "save_ledger_batch",
            batch,
            entry_rows,
            {"event": "portfolio.ledger.batch.posted"},
        )
        conflicting = dict(batch)
        conflicting["canonical_hash"] = "b" * 64
        with pytest.raises(ValueError, match="conflict"):
            execute_portfolio_state_store_operation(
                store,
                "save_ledger_batch",
                conflicting,
                entry_rows,
                {"event": "portfolio.ledger.batch.posted"},
            )

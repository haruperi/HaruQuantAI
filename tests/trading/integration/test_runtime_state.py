"""Integration evidence for durable Trading runtime state."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_runtime_store_migrations,
    unwrap_data_response,
)
from app.services.trading import (
    build_trading_state_store,
    execute_trading_state_store_operation,
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


def test_trading_idempotency_state_survives_reconstruction(tmp_path: Path) -> None:
    """Trading returns duplicate and conflict results from durable state."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_runtime_store_migrations(request_id),
            operation="tests.trading.runtime.migrations",
            request_id=request_id,
        )
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

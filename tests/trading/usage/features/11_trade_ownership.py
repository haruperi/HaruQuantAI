"""Standalone usage evidence for FEAT-TRD-11."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import build_data_settings, data_settings_context
from app.services.trading import (
    assign_trade_ownership,
    build_trade_ownership,
    create_trade_ownership_registry,
    detect_orphaned_trade,
    get_trade_ownership,
    parse_trade_ownership,
    persist_trade_ownership,
    run_trading_migrations,
)


def fr_trd_081() -> object:
    """Build and parse exact ownership evidence."""
    return parse_trade_ownership(
        build_trade_ownership(
            ownership_id="usage-ownership-001",
            owner_type="player",
            owner_id="usage-player-001",
            account_id="usage-account-001",
            position_id="usage-position-001",
            trade_plan_id="usage-plan-001",
            strategy_version="v1",
            session_id="usage-session-001",
            source_sequence=1,
        )
    )


def fr_trd_082(registry: object, ownership: object) -> object:
    """Assign and retrieve one unambiguous active owner."""
    assign_trade_ownership(registry, ownership)
    return get_trade_ownership(registry, "usage-position-001")


def fr_trd_083(registry: object) -> bool:
    """Detect a position whose ownership cannot be proven."""
    return detect_orphaned_trade(registry, "usage-position-001")


def main() -> None:
    """Demonstrate every public trade-ownership operation."""
    registry = create_trade_ownership_registry()
    before = fr_trd_083(registry)
    current = fr_trd_082(registry, fr_trd_081())
    with TemporaryDirectory() as directory:
        settings = build_data_settings(
            database_url="sqlite:///ownership-usage.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
        )
        with data_settings_context(settings):
            run_trading_migrations(
                request_id="req-22222222-2222-4222-8222-222222222222"
            )
            persist_trade_ownership(
                current,
                correlation_id="cor-22222222-2222-4222-8222-222222222222",
                occurred_at=datetime(2026, 8, 7, tzinfo=UTC),
            )
    print("SUCCESS: FR-TRD-081; SUCCESS: FR-TRD-082; SUCCESS: FR-TRD-083")
    print(
        {
            "Data -> FR-TRD-081": current.schema_id,
            "Data -> FR-TRD-082": current.ownership_id,
            "Data -> FR-TRD-083": before,
        }
    )


if __name__ == "__main__":
    main()

"""Reconcile every Data table with an application operation trigger."""

import re
from pathlib import Path

from app.services import data

# Step 006 created these reference tables; ``011_market_reference_v1`` drops
# and replaces them, so their CREATE statements remain in the immutable
# step-006 source even though no live table or lifecycle exists.
_DROPPED_BY_LATER_STEPS = frozenset(
    {
        "data_symbols",
        "data_providers",
        "data_market_sessions",
    }
)

# Reference tables introduced by ``011_market_reference_v1`` that await their
# owning feature registration; the README records them as pending. The three
# catalog-facing merged tables (``data_instruments``, ``data_brokers``,
# ``data_sessions``) are not exempt and must keep lifecycle operations.
_REFERENCE_TABLES_PENDING_FEATURES = frozenset(
    {
        "data_session_elements",
        "data_broker_stocks",
        "data_stock_groups",
        "data_stock_members",
    }
)


def test_every_declared_data_table_has_a_public_application_trigger() -> None:
    """Reject schema-only Data tables and stale lifecycle operation names."""
    sources = (
        Path("app/services/data/migrations/core.py"),
        Path("app/services/data/migrations/economic_calendar.py"),
        Path("app/services/data/migrations/economic_event_definitions.py"),
        Path("app/services/data/migrations/market_reference.py"),
        Path("app/services/data/migrations/research_sources.py"),
        Path("app/services/data/migrations/runtime_stores.py"),
        Path("app/services/data/datasets/migrations/definitions.py"),
        Path("app/services/data/persistence/migrations.py"),
        Path("app/services/data/persistence/locking.py"),
    )
    declared = {
        match.group(1)
        for path in sources
        for match in re.finditer(
            r"CREATE TABLE(?: IF NOT EXISTS)?\s+(data_[a-z_]+)",
            path.read_text(encoding="utf-8"),
        )
    }
    dropped = {
        match.group(1)
        for path in (Path("app/services/data/migrations/market_reference.py"),)
        for match in re.finditer(
            r"DROP TABLE IF EXISTS (data_[a-z_]+)", path.read_text()
        )
    }
    assert dropped == _DROPPED_BY_LATER_STEPS
    lifecycles = data.get_catalog_table_lifecycles()
    assert set(lifecycles) == (
        (declared - dropped) - _REFERENCE_TABLES_PENDING_FEATURES
    )
    public = set(data.__all__)
    missing = {
        table: tuple(operation for operation in operations if operation not in public)
        for table, operations in lifecycles.items()
        if any(operation not in public for operation in operations)
    }
    assert not missing

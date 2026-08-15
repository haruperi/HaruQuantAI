"""Reconcile every Data table with an application operation trigger."""

import re
from pathlib import Path

from app.services import data


def test_every_declared_data_table_has_a_public_application_trigger() -> None:
    """Reject schema-only Data tables and stale lifecycle operation names."""
    sources = (
        Path("app/services/data/migrations/core.py"),
        Path("app/services/data/migrations/economic_calendar.py"),
        Path("app/services/data/migrations/economic_event_definitions.py"),
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
    lifecycles = data.get_catalog_table_lifecycles()
    assert set(lifecycles) == declared
    public = set(data.__all__)
    missing = {
        table: tuple(operation for operation in operations if operation not in public)
        for table, operations in lifecycles.items()
        if any(operation not in public for operation in operations)
    }
    assert not missing

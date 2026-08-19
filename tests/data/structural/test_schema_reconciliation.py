"""Reconcile the authoritative Data schema model with executable definitions."""

from __future__ import annotations

import re
from pathlib import Path


def test_readme_declares_every_live_data_table() -> None:
    """Require every migration-defined Data table in the owning README model."""
    sources = (
        *Path("app/services/data/migrations").glob("*.py"),
        Path("app/services/data/persistence/migrations.py"),
        Path("app/services/data/persistence/locking.py"),
    )
    pattern = re.compile(r"CREATE TABLE(?: IF NOT EXISTS)?\s+(data_[a-z_]+)")
    declared = {
        match.group(1)
        for path in sources
        for match in pattern.finditer(path.read_text(encoding="utf-8"))
    }
    # Later steps may drop tables created by immutable earlier steps; the
    # README documents the live target model, so dropped tables are excluded.
    dropped = {
        match.group(1)
        for path in sources
        for match in re.finditer(
            r"DROP TABLE IF EXISTS (data_[a-z_]+)", path.read_text()
        )
    }
    declared -= dropped
    readme = Path("app/services/data/README.md").read_text(encoding="utf-8")
    documented = set(pattern.findall(readme))

    assert documented == declared
    assert "docs/schema" not in readme or "no duplicate" in readme.lower()

"""Global pytest fixtures and test-isolation configuration."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_test_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None]:
    """Force all tests to execute against an isolated temporary database.

    Ensures that active workspace databases (data/database/haruquantai.db)
    are never opened, created, or mutated by test suites (FIP-14, ARCH:274).
    """
    test_db = str(tmp_path / "test_isolated_workspace.db")
    monkeypatch.setenv("HARUQUANTAI_DB_PATH", test_db)
    yield

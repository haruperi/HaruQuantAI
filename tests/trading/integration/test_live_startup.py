"""Workflow integration for fail-closed live startup."""

# ruff: noqa: INP001

import pytest
from tests.trading.conftest import live_config, live_evidence, live_session


@pytest.mark.anyio
async def test_live_startup_requires_reconciliation() -> None:
    """Mutation admission never opens before startup reconciliation succeeds."""

    async def incomplete() -> bool:
        """Return incomplete authority reconciliation."""
        return False

    session = live_session(startup_reconcile=incomplete)
    assert (await session.start(live_config(), live_evidence())).status == "blocked"
    assert not session.admission_enabled

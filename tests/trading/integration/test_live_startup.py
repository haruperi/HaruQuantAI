"""Workflow integration for fail-closed live startup."""

import pytest
from app.services.trading import (
    is_live_session_admission_enabled,
    start_live_session,
)

from tests.trading.conftest import live_config, live_evidence, live_session


@pytest.mark.anyio
async def test_live_startup_requires_reconciliation() -> None:
    """Mutation admission never opens before startup reconciliation succeeds."""

    async def incomplete() -> bool:
        """Return incomplete authority reconciliation."""
        return False

    session = live_session(startup_reconcile=incomplete)
    result = await start_live_session(session, live_config(), live_evidence())
    assert result.status == "success"
    assert result.metadata.extensions["legacy_status"] == "blocked"
    assert not is_live_session_admission_enabled(session)

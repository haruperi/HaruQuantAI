"""Workflow integration for bounded live shutdown reporting."""

import pytest
from app.services.trading import start_live_session, stop_live_session

from tests.trading.conftest import live_config, live_evidence, live_session


@pytest.mark.anyio
async def test_shutdown_reports_unresolved_work() -> None:
    """A failed flush remains visible in the final shutdown result."""

    async def failed() -> bool:
        """Return an incomplete shutdown step."""
        return False

    session = live_session(flush_evidence=failed)
    await start_live_session(session, live_config(), live_evidence())
    outcome = await stop_live_session(session)
    assert outcome.status == "success"
    assert outcome.metadata.extensions["legacy_status"] == "partial"
    assert outcome.data is not None
    assert "flush_evidence" in outcome.data["unresolved_steps"]

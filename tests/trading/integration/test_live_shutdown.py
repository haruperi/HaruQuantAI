"""Workflow integration for bounded live shutdown reporting."""

# ruff: noqa: INP001

import pytest
from tests.trading.conftest import live_config, live_evidence, live_session


@pytest.mark.anyio
async def test_shutdown_reports_unresolved_work() -> None:
    """A failed flush remains visible in the final shutdown result."""

    async def failed() -> bool:
        """Return an incomplete shutdown step."""
        return False

    session = live_session(flush_evidence=failed)
    await session.start(live_config(), live_evidence())
    outcome = await session.stop()
    assert outcome.status == "partial"
    assert "flush_evidence" in outcome.data["unresolved_steps"]

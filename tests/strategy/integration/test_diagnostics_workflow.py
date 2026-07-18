"""WF-STR-006 bounded diagnostics integration."""

# ruff: noqa: PT018

from app.services.strategy import export_strategy_diagnostics
from app.utils import logger

from tests.strategy.unit.test_models import make_context


def test_diagnostics_workflow() -> None:
    """Export redacted diagnostics without leaking supplied secrets."""
    logger.debug("Testing WF-STR-006 diagnostics workflow")
    outcome = export_strategy_diagnostics(
        make_context(),
        {"strategy_id": "s", "strategy_version": "1", "password": "secret"},
    )
    assert (
        outcome.data is not None
        and outcome.data.safe_details["password"] == "[REDACTED]"
    )

"""Strategy diagnostics export tests."""

# ruff: noqa: PT018
from app.composition.logging import get_logger
from app.services.strategy import export_strategy_diagnostics

from tests.strategy.unit.test_models import make_context

logger = get_logger(__name__)


def test_export_diagnostics_redacts_and_bounds() -> None:
    """Verify recursive redaction is represented in bounded diagnostics."""
    logger.debug("Testing Strategy diagnostic export")
    outcome = export_strategy_diagnostics(
        make_context(), {"strategy_id": "s", "strategy_version": "1", "token": "secret"}
    )
    assert outcome.status == "success"
    assert outcome.data is not None and outcome.data.redacted_paths == ("token",)

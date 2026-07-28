"""Strategy accepted error catalogue tests."""

from app.services.strategy import StrategyErrorCode
from app.services.strategy.diagnostics.errors import STRATEGY_ERROR_CATALOG
from app.utils import logger


def test_error_catalogue_excludes_deferred_codes() -> None:
    """Verify only accepted Strategy error names are exposed."""
    logger.debug("Testing Strategy error catalogue")
    values = {item.value for item in StrategyErrorCode}
    assert "STRATEGY_ARBITRARY_CODE_REJECTED" in values
    assert not any(value.startswith("SIM_") for value in values)
    assert set(STRATEGY_ERROR_CATALOG) == values
    assert all(
        definition.domain == "strategy"
        for definition in STRATEGY_ERROR_CATALOG.values()
    )

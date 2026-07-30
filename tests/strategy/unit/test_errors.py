"""Strategy accepted error catalogue tests."""

from app.services.strategy import get_strategy_error_catalog
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.utils import get_logger

logger = get_logger(__name__)


def test_error_catalogue_excludes_deferred_codes() -> None:
    """Verify only accepted Strategy error names are exposed."""
    logger.debug("Testing Strategy error catalogue")
    values = {item.value for item in StrategyErrorCode}
    assert "STRATEGY_ARBITRARY_CODE_REJECTED" in values
    assert not any(value.startswith("SIM_") for value in values)
    catalog = get_strategy_error_catalog()
    assert set(catalog) == values
    assert all(definition.domain == "strategy" for definition in catalog.values())

"""Unit tests for Analytics reproducibility hashes."""

from decimal import Decimal

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.reports.hashes import compute_reproducibility_hashes
from app.utils import get_logger

logger = get_logger(__name__)

from tests.analytics.component.test_results_adapter import (  # noqa: E402
    _config,
    _source,
)


def test_hashes_change_only_for_material_input() -> None:
    """Identical canonical evidence hashes equally and material balances differ."""
    logger.debug("Testing Analytics reproducibility hash materiality")
    first = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    second = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(2000),
        account_currency="USD",
        config=_config(),
    )
    first_hashes = compute_reproducibility_hashes(first)
    assert first_hashes == compute_reproducibility_hashes(first)
    assert first_hashes.input_hash != compute_reproducibility_hashes(second).input_hash

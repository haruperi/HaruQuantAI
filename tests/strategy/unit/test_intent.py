"""Canonical TradeIntent contract tests."""

from decimal import Decimal

import pytest
from app.services.strategy import TradeIntent
from app.utils import logger
from pydantic import ValidationError

from tests.strategy.unit.test_models import HASH, NOW


def test_trade_intent_rejects_invalid_partial_fill_contract() -> None:
    """Verify minimum fills require an explicit partial-fill preference."""
    logger.debug("Testing TradeIntent partial-fill invariant")
    with pytest.raises(ValidationError):
        TradeIntent(
            intent_id="intent-1",
            decision_id="decision-1",
            idempotency_key=HASH,
            strategy_id="s",
            strategy_version="1",
            strategy_sequence=0,
            symbol="EURUSD",
            side="BUY",
            intent_type="OPEN",
            requested_sizing_mode="quantity",
            quantity_hint=Decimal(1),
            notional_hint=None,
            signal_timestamp=NOW,
            decision_timestamp=NOW,
            parent_intent_id=None,
            stop_loss=None,
            take_profit=None,
            expiration=None,
            allow_partial_fills=False,
            min_fill_size=Decimal("0.1"),
            rationale_ref=None,
            lineage={"config_hash": HASH},
        )

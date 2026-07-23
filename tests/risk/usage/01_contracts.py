"""Executable Risk contracts usage example.

Demonstrates creating and inspecting TradeIntent, PortfolioState, and Risk
contract instances.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.evidence.account_contracts import (
    AccountBalance,
    AccountStateSnapshot,
)
from app.services.data.evidence.market_context_contracts import MarketContextEvidence
from app.services.risk.contracts import (
    PortfolioState,
    validate_market_context_evidence,
)
from app.services.strategy import TradeIntent

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def example_contracts() -> None:
    """Demonstrate Risk contract models."""
    print("=" * 80)
    print("Risk Example 1: Boundary Contracts and Evidence")
    print("=" * 80)

    # 1. TradeIntent
    intent = TradeIntent(
        intent_id="intent-1",
        decision_id="strategy-decision-1",
        idempotency_key="intent-key-1",
        strategy_id="strategy-1",
        strategy_version="1.0.0",
        strategy_sequence=1,
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        limit_price=None,
        stop_price=None,
        time_in_force=None,
        requested_sizing_mode="fixed_risk",
        quantity_hint=Decimal(1),
        notional_hint=None,
        signal_timestamp=NOW,
        decision_timestamp=NOW,
        parent_intent_id=None,
        stop_loss=Decimal("1.09"),
        take_profit=None,
        expiration=NOW + timedelta(minutes=1),
        allow_partial_fills=False,
        min_fill_size=None,
        rationale_ref=None,
        lineage={"config_hash": "a" * 64},
    )
    print(
        f"TradeIntent ID: {intent.intent_id}, symbol: {intent.symbol}, "
        f"side: {intent.side}"
    )

    # 2. PortfolioState
    account = AccountStateSnapshot(
        account_id="account-1",
        currency="USD",
        balances=(
            AccountBalance(asset="USD", total=Decimal(10000), available=Decimal(9500)),
        ),
        equity=Decimal(10000),
        margin_used=Decimal(500),
        margin_available=Decimal(9500),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-1",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    portfolio = PortfolioState(
        account_snapshot=account,
        peak_equity=Decimal(10000),
        day_start_equity=Decimal(10000),
        inception_equity=Decimal(10000),
        symbol_prices={},
        symbol_contract_sizes={},
        symbol_quote_currencies={},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations={},
        exposure_dimensions={},
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("returns",),
        request_id="request-1",
        workflow_id="workflow-1",
    )
    print(
        f"PortfolioState account ID: {portfolio.account_snapshot.account_id}, "
        f"equity: {portfolio.account_snapshot.equity}"
    )

    market = MarketContextEvidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state="clear",
        spread=Decimal(1),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "example"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )
    validate_market_context_evidence(market, now=NOW)
    print(f"Validated consumed market-context evidence for symbol: {market.symbol}")


def main() -> None:
    """Run Risk contracts usage example."""
    example_contracts()


if __name__ == "__main__":
    main()

"""Representative non-gating Risk workload baseline tests."""

from datetime import timedelta
from decimal import Decimal

from app.services.data.evidence.account_contracts import (
    AccountBalance,
    AccountPosition,
    AccountStateSnapshot,
)
from app.services.risk.contracts import PortfolioState, ScenarioDefinition
from app.services.risk.portfolio import build_portfolio_risk_snapshot
from app.services.risk.scenarios import run_risk_scenario_analysis

from tests.risk import _support as examples


def test_supported_scenario_and_position_workload_completes() -> None:
    """Exercise 500 positions, 100 strategies, 5,000 returns, and 100 scenarios."""
    config = examples._config()
    symbols = tuple(f"S{index:03d}" for index in range(500))
    account = AccountStateSnapshot(
        account_id="account-performance",
        currency="USD",
        balances=(
            AccountBalance(
                asset="USD",
                total=Decimal(1_000_000),
                available=Decimal(1_000_000),
            ),
        ),
        equity=Decimal(1_000_000),
        margin_used=Decimal(0),
        margin_available=Decimal(1_000_000),
        positions=tuple(
            AccountPosition(
                position_id=f"position-{index:03d}",
                symbol=symbol,
                side="LONG",
                quantity=Decimal(1),
                entry_price=Decimal(1),
            )
            for index, symbol in enumerate(symbols)
        ),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="performance-fixture",
        snapshot_at=examples.NOW,
        expires_at=examples.NOW + timedelta(minutes=1),
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    return_timestamps = tuple(
        examples.NOW - timedelta(seconds=5_000 - index) for index in range(5_000)
    )
    state = PortfolioState(
        account_snapshot=account,
        peak_equity=Decimal(1_000_000),
        day_start_equity=Decimal(1_000_000),
        inception_equity=Decimal(1_000_000),
        symbol_prices={symbol: Decimal(1) for symbol in symbols},
        symbol_contract_sizes={symbol: Decimal(1) for symbol in symbols},
        symbol_quote_currencies=dict.fromkeys(symbols, "USD"),
        fx_conversions=(),
        return_timestamps=return_timestamps,
        return_history={"S000": tuple(Decimal(0) for _ in return_timestamps)},
        correlations={},
        exposure_dimensions={
            symbol: (f"strategy:strategy-{index % 100:03d}",)
            for index, symbol in enumerate(symbols)
        },
        as_of=examples.NOW,
        expires_at=examples.NOW + timedelta(minutes=1),
        provenance={"source": "performance-fixture"},
        missing_fields=(),
        request_id="request-performance",
        workflow_id="workflow-performance",
    )
    snapshot = build_portfolio_risk_snapshot(state, config, now=examples.NOW)
    scenarios = tuple(
        ScenarioDefinition(
            scenario_id=f"scenario-{index:03d}",
            shocks={"drawdown": Decimal("0.001")},
            randomized=False,
            seed=None,
            assumptions=("representative bounded workload",),
        )
        for index in range(100)
    )
    results = run_risk_scenario_analysis(snapshot, scenarios, config, now=examples.NOW)
    assert len(account.positions) == 500
    assert len(return_timestamps) == 5_000
    assert (
        len(
            {
                dimension
                for dimensions in state.exposure_dimensions.values()
                for dimension in dimensions
            }
        )
        == 100
    )
    assert len(results) == 100
    assert all(result.advisory_only for result in results)

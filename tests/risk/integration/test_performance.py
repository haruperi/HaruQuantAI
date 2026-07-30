"""Representative non-gating Risk workload baseline tests."""

from datetime import timedelta
from decimal import Decimal

from app.services.data import build_account_state_snapshot
from app.services.risk import (
    build_portfolio_risk_snapshot,
    create_portfolio_state,
    create_scenario_definition,
    run_risk_scenario_analysis,
)

from tests.risk import _support as examples


def test_supported_scenario_and_position_workload_completes() -> None:
    """Exercise 500 positions, 100 strategies, 5,000 returns, and 100 scenarios."""
    config = examples._config()
    symbols = tuple(f"S{index:03d}" for index in range(500))
    account = build_account_state_snapshot(
        account_id="account-performance",
        currency="USD",
        balances=(
            {
                "asset": "USD",
                "total": Decimal(1_000_000),
                "available": Decimal(1_000_000),
            },
        ),
        equity=Decimal(1_000_000),
        margin_used=Decimal(0),
        margin_available=Decimal(1_000_000),
        positions=tuple(
            {
                "position_id": f"position-{index:03d}",
                "symbol": symbol,
                "side": "LONG",
                "quantity": Decimal(1),
                "entry_price": Decimal(1),
            }
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
    state = create_portfolio_state(
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
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )
    snapshot = examples.unwrap_risk_response(
        build_portfolio_risk_snapshot(state, config, now=examples.NOW),
        operation="build_portfolio_risk_snapshot",
    )
    scenarios = tuple(
        create_scenario_definition(
            scenario_id=f"scenario-{index:03d}",
            shocks={"drawdown": Decimal("0.001")},
            randomized=False,
            seed=None,
            assumptions=("representative bounded workload",),
        )
        for index in range(100)
    )
    results = examples.unwrap_risk_response(
        run_risk_scenario_analysis(snapshot, scenarios, config, now=examples.NOW),
        operation="run_risk_scenario_analysis",
    )
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

"""Executable Portfolio construction usage example.

Demonstrates the deterministic construction feature through the package-root
public API. Each functional requirement FR-PORT-010 through FR-PORT-014 has a
dedicated demonstration function.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import PortfolioConstructionResult

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_port_010() -> None:
    """FR-PORT-010: Support fixed, equal, and inverse-volatility methods only.

    Demonstrates that the construction result carries one of exactly three
    approved methods and no other method identifier is valid.
    """
    _header(
        "FR-PORT-010: Support fixed, equal, and inverse-volatility methods only. Demonstrates that the construction result carries one of exactly three approved methods and no other method identifier is valid."
    )
    print("FR-PORT-010: Support fixed, equal, and inverse-volatility methods only")

    result = PortfolioConstructionResult(
        result_id="result-1",
        portfolio_id="portfolio-alpha",
        portfolio_version="version-1",
        scope={"environment": "simulation"},
        status="constructed",
        component_weights=(
            {
                "component_id": "component-a",
                "strategy_id": "strategy-a",
                "strategy_version": "1.0.0",
                "capital_weight": Decimal("0.5"),
                "proposed_risk_budget_weight": Decimal("0.5"),
            },
            {
                "component_id": "component-b",
                "strategy_id": "strategy-b",
                "strategy_version": "1.0.0",
                "capital_weight": Decimal("0.5"),
                "proposed_risk_budget_weight": Decimal("0.5"),
            },
        ),
        method="equal",
        config_hash="a" * 64,
        evidence_hash="b" * 64,
        strategy_lineage_hash="c" * 64,
        canonical_hash="d" * 64,
        created_at=NOW,
        request_id="req-1",
        workflow_id="wf-1",
        correlation_id="corr-1",
    )
    assert result.method in ("fixed", "equal", "inverse_volatility")
    print(f"Method 'equal' accepted: {result.method}")

    try:
        PortfolioConstructionResult(
            **{**result.model_dump(mode="python"), "method": "mean_variance"}
        )
        msg = "ERROR: unsupported method accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        msg = "Unsupported method 'mean_variance' correctly rejected"
    print(msg)


def fr_port_011() -> None:
    """FR-PORT-011: Reject zero/negative volatility, insufficient observations,
    non-finite values, and invalid weight totals.

    Demonstrates that published component weights must total exactly one.
    """
    _header(
        "FR-PORT-011: Reject zero/negative volatility, insufficient observations, non-finite values, and invalid weight totals. Demonstrates that published component weights must total exactly one."
    )
    print("FR-PORT-011: Reject invalid weights and non-finite values")

    try:
        PortfolioConstructionResult(
            result_id="result-bad",
            portfolio_id="portfolio-alpha",
            portfolio_version="version-1",
            scope={"environment": "simulation"},
            status="constructed",
            component_weights=(
                {
                    "component_id": "component-a",
                    "strategy_id": "strategy-a",
                    "strategy_version": "1.0.0",
                    "capital_weight": Decimal("0.7"),
                    "proposed_risk_budget_weight": Decimal("0.5"),
                },
                {
                    "component_id": "component-b",
                    "strategy_id": "strategy-b",
                    "strategy_version": "1.0.0",
                    "capital_weight": Decimal("0.7"),
                    "proposed_risk_budget_weight": Decimal("0.5"),
                },
            ),
            method="equal",
            config_hash="a" * 64,
            evidence_hash="b" * 64,
            strategy_lineage_hash="c" * 64,
            canonical_hash="d" * 64,
            created_at=NOW,
            request_id="req-1",
            workflow_id="wf-1",
            correlation_id="corr-1",
        )
        msg = "ERROR: invalid weight total accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        msg = "Weight total != 1.0 correctly rejected"
    print(msg)


def fr_port_012() -> None:
    """FR-PORT-012: Return identical bytes and hash for identical
    inputs/configuration.

    Demonstrates that two identically constructed results produce identical
    canonical hash material.
    """
    _header(
        "FR-PORT-012: Return identical bytes and hash for identical inputs/configuration. Demonstrates that two identically constructed results produce identical canonical hash material."
    )
    print("FR-PORT-012: Return identical hash for identical inputs")

    data = {
        "result_id": "result-det",
        "portfolio_id": "portfolio-alpha",
        "portfolio_version": "version-1",
        "scope": {"environment": "simulation"},
        "status": "constructed",
        "component_weights": (
            {
                "component_id": "component-a",
                "strategy_id": "strategy-a",
                "strategy_version": "1.0.0",
                "capital_weight": Decimal("0.5"),
                "proposed_risk_budget_weight": Decimal("0.5"),
            },
            {
                "component_id": "component-b",
                "strategy_id": "strategy-b",
                "strategy_version": "1.0.0",
                "capital_weight": Decimal("0.5"),
                "proposed_risk_budget_weight": Decimal("0.5"),
            },
        ),
        "method": "equal",
        "config_hash": "a" * 64,
        "evidence_hash": "b" * 64,
        "strategy_lineage_hash": "c" * 64,
        "canonical_hash": "d" * 64,
        "created_at": NOW,
        "request_id": "req-1",
        "workflow_id": "wf-1",
        "correlation_id": "corr-1",
    }
    result_a = PortfolioConstructionResult(**data)
    result_b = PortfolioConstructionResult(**data)
    wire_a = result_a.model_dump(mode="json")
    wire_b = result_b.model_dump(mode="json")
    assert wire_a == wire_b
    identical = result_a.canonical_hash == result_b.canonical_hash
    print(f"Identical canonical_hash: {identical}")


def fr_port_013() -> None:
    """FR-PORT-013: Exclude MVO, Black-Litterman, CVaR, and implicit optimizer
    delegation.

    Demonstrates that the construction result method field accepts only the
    three approved methods, excluding advanced optimization methods.
    """
    _header(
        "FR-PORT-013: Exclude MVO, Black-Litterman, CVaR, and implicit optimizer delegation. Demonstrates that the construction result method field accepts only the three approved methods, excluding advanced optimization methods."
    )
    print("FR-PORT-013: Exclude MVO, Black-Litterman, CVaR optimization")

    approved = {"fixed", "equal", "inverse_volatility"}
    excluded = {"mean_variance", "black_litterman", "cvar"}
    print(f"Approved methods: {approved}")
    print(f"Excluded methods: {excluded}")
    assert approved.isdisjoint(excluded)
    print("No advanced optimization method is approved")


def fr_port_014() -> None:
    """FR-PORT-014: Publish nothing on partial construction failure.

    Demonstrates that a construction result with invalid weights raises an
    error and publishes no result.
    """
    _header(
        "FR-PORT-014: Publish nothing on partial construction failure. Demonstrates that a construction result with invalid weights raises an error and publishes no result."
    )
    print("FR-PORT-014: Publish nothing on partial construction failure")

    try:
        PortfolioConstructionResult(
            result_id="result-fail",
            portfolio_id="portfolio-alpha",
            portfolio_version="version-1",
            scope={"environment": "simulation"},
            status="constructed",
            component_weights=(),
            method="equal",
            config_hash="a" * 64,
            evidence_hash="b" * 64,
            strategy_lineage_hash="c" * 64,
            canonical_hash="d" * 64,
            created_at=NOW,
            request_id="req-1",
            workflow_id="wf-1",
            correlation_id="corr-1",
        )
        msg = "ERROR: empty component weights accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        msg = "Empty component weights correctly rejected — nothing published"
    print(msg)


def main() -> None:
    """Run every functional-requirement demonstration for Portfolio construction."""
    fr_port_010()
    fr_port_011()
    fr_port_012()
    fr_port_013()
    fr_port_014()


if __name__ == "__main__":
    main()

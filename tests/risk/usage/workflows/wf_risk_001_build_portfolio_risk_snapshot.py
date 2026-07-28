"""WF-RISK-001: build a complete immutable portfolio Risk snapshot."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import build_portfolio_risk_snapshot
from tests.risk._support import unwrap_risk_response
from tests.risk.unit.test_snapshot import NOW, _config, _state

WORKFLOW_ID = "WF-RISK-001"
STAGES = (
    "Accept account, position, order, symbol, return, FX, and provenance evidence.",
    "Validate versions, UTC timestamps, finite numerics, profile, and config hash.",
    "Normalize without inventing missing values or mutating source evidence.",
    "Calculate exposure, drawdown, leverage, distribution, and contribution evidence.",
    "Return immutable PortfolioRiskSnapshot with coverage and missing-evidence markers.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Owning domains supply typed portfolio evidence.
    _stage(1)
    state, config = _state(), _config()
    print("Input:", state.account_snapshot.account_id, state.as_of)
    # Stage 2: Public builder validates all boundary invariants.
    _stage(2)
    print("Config:", config.profile, config.policy_version)
    # Stage 3: Preserve the immutable caller input.
    _stage(3)
    before = state.model_dump(mode="python")
    # Stage 4: Build all supported portfolio calculations.
    _stage(4)
    snapshot = unwrap_risk_response(
        build_portfolio_risk_snapshot(state, config, now=NOW),
        operation="build_portfolio_risk_snapshot",
    )
    print("Coverage:", dict(snapshot.coverage))
    # Stage 5 — OUTPUT BOUNDARY: Return Risk-owned immutable snapshot or RiskDomainError.
    _stage(5)
    print(
        "Output:",
        type(snapshot).__name__,
        snapshot.snapshot_id,
        "input unchanged:",
        before == state.model_dump(mode="python"),
    )


if __name__ == "__main__":
    main()

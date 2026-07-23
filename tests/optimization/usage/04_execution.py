"""Executable Optimization execution usage example.

Demonstrates backtest execution adapter interface, execution request, error handling,
and candidate execution.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization.errors import OptimizationError
from app.services.optimization.execution import (
    EngineOptimizationResult,
    execute_candidate,
)
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_execution_contracts import execution_request


def example_execution() -> None:
    """Demonstrate candidate execution engine integration."""
    print("=" * 80)
    print("Optimization Example 4: Candidate Execution")
    print("=" * 80)

    req = execution_request()
    print(f"Execution request contract version: {req.contract_version}")

    # Optimization Error construction
    err = OptimizationError("OPT_EXECUTION_FAILED")
    payload = err.to_payload()
    print(f"OptimizationError payload code: {payload['code']}")

    # Adapter verification
    adapter = FakeAdapter()
    print(f"Adapter is callable: {callable(getattr(adapter, 'execute', None))}")

    # Execute candidate
    res = adapter.execute(req)
    print(
        f"Adapter execution returned EngineOptimizationResult: {isinstance(res, EngineOptimizationResult)}"
    )

    exec_res = execute_candidate(req, adapter, deterministic_only=True)
    print(f"execute_candidate hash: {exec_res.candidate_hash[:8]}...")


def main() -> None:
    """Run Optimization execution usage example."""
    example_execution()


if __name__ == "__main__":
    main()

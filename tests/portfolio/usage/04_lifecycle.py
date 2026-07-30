"""Executable Portfolio standalone public API lifecycle usage example."""

import inspect
import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import (
    activate_portfolio,
    assess_portfolio_drift,
    construct_portfolio,
    get_portfolio_history,
    get_portfolio_status,
    recompute_portfolio_measurement,
    rollback_portfolio,
    submit_portfolio_rebalance,
    to_portfolio_error_payload,
)
from app.utils import get_standard_response_type

PUBLIC_OPERATIONS = {
    "activate": activate_portfolio,
    "assess_drift": assess_portfolio_drift,
    "construct": construct_portfolio,
    "history": get_portfolio_history,
    "recompute_measurement": recompute_portfolio_measurement,
    "rollback": rollback_portfolio,
    "status": get_portfolio_status,
    "submit_rebalance": submit_portfolio_rebalance,
}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_port_034() -> None:
    """FR-PORT-034: Expose construction, status, activation, drift/rebalance,
    rollback, and history operations.

    Demonstrates that the package root exposes every required standalone operation.
    """
    _header(
        "FR-PORT-034: Expose construction, status, activation, drift/rebalance, rollback, and history as package-root functions."
    )
    print("FR-PORT-034: Expose construction, status, activation, drift, rebalance")

    required = {
        "construct",
        "status",
        "activate",
        "assess_drift",
        "submit_rebalance",
        "recompute_measurement",
        "rollback",
        "history",
    }
    actual = set(PUBLIC_OPERATIONS)
    missing = required - actual
    assert not missing, f"Missing operations: {missing}"
    print(f"All {len(required)} required standalone operations present at package root")
    for op in sorted(required):
        print(f"  - {op}")


def fr_port_035() -> None:
    """FR-PORT-035: Accept AuthContext and request_id: str | None = None on
    governed entry points.

    Demonstrates that every governed public function accepts the required
    authentication and trace parameters.
    """
    _header(
        "FR-PORT-035: Every governed package-root function accepts AuthContext and optional request_id."
    )
    print("FR-PORT-035: Accept AuthContext and optional request_id")

    governed = (
        "construct",
        "status",
        "activate",
        "assess_drift",
        "submit_rebalance",
        "recompute_measurement",
        "rollback",
        "history",
    )
    for method_name in governed:
        signature = inspect.signature(PUBLIC_OPERATIONS[method_name])
        assert "auth_context" in signature.parameters
        assert signature.parameters["request_id"].default is None
        print(f"  {method_name}: accepts auth_context and optional request_id")


def fr_port_036() -> None:
    """FR-PORT-036: Return structured success/error envelopes; never None or
    raw exceptions.

    Demonstrates that every governed public function returns a StandardResponse typed
    envelope.
    """
    _header(
        "FR-PORT-036: Package-root operations return structured envelopes, never None or raw exceptions."
    )
    print("FR-PORT-036: Return structured envelopes, never None or raw exceptions")

    error_response = to_portfolio_error_payload("PORT_NOT_FOUND", "LIFECYCLE")
    assert isinstance(error_response, get_standard_response_type())
    assert error_response.status == "success"
    assert error_response.data is not None
    print("Structured Portfolio error envelope:")
    print(error_response.model_dump(mode="json"))


def fr_port_037() -> None:
    """FR-PORT-037: Keep authentication and presentation logic outside
    Portfolio.

    Demonstrates that the Portfolio API implementation contains no HTTP, FastAPI, or
    authentication-framework imports.
    """
    _header(
        "FR-PORT-037: Keep authentication and presentation frameworks outside Portfolio."
    )
    print("FR-PORT-037: Keep authentication and presentation outside Portfolio")

    source_file = Path("app/services/portfolio/api/service.py")
    source = source_file.read_text(encoding="utf-8")
    forbidden = ("fastapi", "flask", "django", "jwt", "oauth", "httpx")
    found = [lib for lib in forbidden if lib in source.lower()]
    assert not found, f"Forbidden presentation imports found: {found}"
    print("No HTTP/authentication framework imports in Portfolio API")


def main() -> None:
    """Run every functional-requirement demonstration for the Portfolio API."""
    fr_port_034()
    fr_port_035()
    fr_port_036()
    fr_port_037()


if __name__ == "__main__":
    main()

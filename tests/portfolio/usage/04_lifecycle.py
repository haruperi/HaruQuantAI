"""Executable Portfolio public API lifecycle usage example.

Demonstrates the PortfolioService public boundary through the package-root
public API. Each functional requirement FR-PORT-034 through FR-PORT-037 has a
dedicated demonstration function.
"""

import inspect
import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import PortfolioError, PortfolioService


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_port_034() -> None:
    """FR-PORT-034: Expose construction, status, activation, drift/rebalance,
    rollback, and history operations.

    Demonstrates that PortfolioService exposes every required operation.
    """
    _header(
        "FR-PORT-034: Expose construction, status, activation, drift/rebalance, rollback, and history operations. Demonstrates that PortfolioService exposes every required operation."
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
    actual = {
        name
        for name, _member in inspect.getmembers(
            PortfolioService, predicate=inspect.isfunction
        )
    }
    missing = required - actual
    assert not missing, f"Missing operations: {missing}"
    print(f"All {len(required)} required operations present on PortfolioService")
    for op in sorted(required):
        print(f"  - {op}")


def fr_port_035() -> None:
    """FR-PORT-035: Accept AuthContext and request_id: str | None = None on
    governed entry points.

    Demonstrates that every governed public method accepts the required
    authentication and trace parameters.
    """
    _header(
        "FR-PORT-035: Accept AuthContext and request_id: str | None = None on governed entry points. Demonstrates that every governed public method accepts the required authentication and trace parameters."
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
        signature = inspect.signature(getattr(PortfolioService, method_name))
        assert "auth_context" in signature.parameters
        assert signature.parameters["request_id"].default is None
        print(f"  {method_name}: auth_context + request_id OK")


def fr_port_036() -> None:
    """FR-PORT-036: Return structured success/error envelopes; never None or
    raw exceptions.

    Demonstrates that every public method returns a StandardResponse typed
    envelope.
    """
    _header(
        "FR-PORT-036: Return structured success/error envelopes; never None or raw exceptions. Demonstrates that every public method returns a StandardResponse typed envelope."
    )
    print("FR-PORT-036: Return structured envelopes, never None or raw exceptions")

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
        signature = inspect.signature(getattr(PortfolioService, method_name))
        return_annotation = str(signature.return_annotation)
        assert "StandardResponse" in return_annotation
        print(f"  {method_name} -> {return_annotation.split('[', maxsplit=1)[0]}")

    error_response = PortfolioError("PORT_NOT_FOUND", "LIFECYCLE").to_payload()
    assert error_response.status == "success"
    assert error_response.data is not None
    print("  PortfolioError.to_payload -> StandardResponse")


def fr_port_037() -> None:
    """FR-PORT-037: Keep authentication and presentation logic outside
    Portfolio.

    Demonstrates that the PortfolioService module contains no HTTP, FastAPI, or
    authentication-framework imports.
    """
    _header(
        "FR-PORT-037: Keep authentication and presentation logic outside Portfolio. Demonstrates that the PortfolioService module contains no HTTP, FastAPI, or authentication-framework imports."
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

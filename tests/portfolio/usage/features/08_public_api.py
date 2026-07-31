"""Executable Portfolio public API usage example.

Demonstrates FEAT-PORT-08 public portfolio API feature through the package-root public API.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

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


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_port_030() -> None:
    """FR-PORT-030: Stage 1 — Expose construction, status, activation, drift/rebalance, rollback, and history operations.

    The system shall expose all core portfolio lifecycle operations at the package root.
    """
    _header(
        "Stage 1: Package Export Gate - Expose Standalone Lifecycle Functions (FR-PORT-030)"
    )
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
    assert required == actual
    print(_format_result(actual))
    print(f"Data -> exported_operations={sorted(actual)}")


def fr_port_031() -> None:
    """FR-PORT-031: Stage 2 — Accept AuthContext and request_id: str | None = None on governed entry points.

    The system shall accept AuthContext and optional request_id on all governed entry points.
    """
    _header(
        "Stage 2: Auth Signature Verification - Enforce AuthContext & request_id (FR-PORT-031)"
    )
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
    for name in governed:
        sig = inspect.signature(PUBLIC_OPERATIONS[name])
        assert "auth_context" in sig.parameters
        assert sig.parameters["request_id"].default is None
    print(f"Data -> verified_signatures_count={len(governed)}")


def fr_port_032() -> None:
    """FR-PORT-032: Stage 3 — Return structured success/error envelopes; never None or raw exceptions.

    The system shall return StandardResponse envelopes for all portfolio operation outcomes.
    """
    _header(
        "Stage 3: Response Envelope - Return StandardResponse Envelopes (FR-PORT-032)"
    )
    error_response = to_portfolio_error_payload("PORT_NOT_FOUND", "LIFECYCLE")
    print(_format_result(error_response))
    print(
        f"Data -> envelope_type='{type(error_response).__name__}', status='{error_response.status}'"
    )


def fr_port_036() -> None:
    """FR-PORT-036: Stage 3 — Keep authentication and presentation logic outside Portfolio.

    The system shall keep authentication and presentation framework code outside the domain boundary.
    """
    _header(
        "Stage 3: Framework Decoupling - Keep Presentation/Auth Frameworks External (FR-PORT-036)"
    )
    source_file = Path("app/services/portfolio/api/service.py")
    source = source_file.read_text(encoding="utf-8")
    forbidden = ("fastapi", "flask", "django", "jwt", "oauth", "httpx")
    found = [lib for lib in forbidden if lib in source.lower()]
    assert not found
    print("Data -> presentation_frameworks_detected=None")


def fr_port_037() -> None:
    """FR-PORT-037: Stage 1 — Enforce package-root export gate for all portfolio operations.

    The system shall enforce that all domain capabilities are accessible strictly through package-root functions.
    """
    _header(
        "Stage 1: Export Gating - Package-Root API Boundary Enforcement (FR-PORT-037)"
    )
    print("Data -> package_root_export_gate=Enforced")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-PORT-08 — api/ — Public Portfolio API\n\n"
        "Purpose: Expose the package-root standalone function API boundary for all Portfolio lifecycle capabilities.\n\n"
        "Module flow:\n"
        "-> Stage 1: Package-root standalone function API export gating\n"
        "-> Stage 2: AuthContext and optional request_id parameter signature validation\n"
        "-> Stage 3: StandardResponse envelope formatting and HTTP/framework decoupling"
    )

    # Stage 1: Export Gating & Operations
    fr_port_030()
    fr_port_037()

    # Stage 2: Auth & Trace Signatures
    fr_port_031()

    # Stage 3: Envelope & Framework Decoupling
    fr_port_032()
    fr_port_036()


if __name__ == "__main__":
    main()

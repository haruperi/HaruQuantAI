"""Executable Simulation errors usage example.

Demonstrates FEAT-SIM-08 error catalog inspection, controlled SimulationError handling, and public error payload formatting.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    get_simulation_error_catalog,
    to_simulation_error_payload,
    unwrap_simulation_response,
    validate_phase_one_scope,
)


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


def fr_sim_036() -> None:
    """
    FR-SIM-036: Stage 1 — Inspect authoritative closed catalog of Simulation error codes.

    The system shall expose the authoritative closed catalog of Simulation error codes with group, meaning, and fail-closed effect. Every code raised by any `FR-SIM-*` appears here, and no code appears that no requirement raises.
    """
    _header("Stage 1: Error Catalog - Inspect Simulation Error Catalog (FR-SIM-036)")
    catalog = get_simulation_error_catalog()
    catalog_entry = catalog.get("SIM_MARKET_CLOSED")
    print(_format_result(catalog))
    print(
        f"Data -> total_error_codes={len(catalog)}, SIM_MARKET_CLOSED_category='{catalog_entry.category if catalog_entry else None}'"
    )


def fr_sim_035() -> None:
    """
    FR-SIM-035: Stage 2 — Catch controlled domain exception on boundary failure.

    The system shall expose one base exception carrying a cataloged `code`, bounded redacted message/details, and optional request/correlation identifiers. Every controlled Simulation boundary failure surfaces through it; no uncontrolled exception crosses the run boundary.
    """
    _header(
        "Stage 2: Exception Handling - Catch Controlled Simulation Failure (FR-SIM-035)"
    )
    try:
        unwrap_simulation_response(
            validate_phase_one_scope(
                {
                    "asset_class": "CRYPTO",
                    "runtime_profile": "simulation",
                    "execution_route": "sim",
                }
            ),
            operation="usage.errors.validate_phase_one_scope",
        )
    except Exception as error:  # noqa: BLE001
        print(_format_result(error))
        print(f"Data -> code='{getattr(error, 'code', None)}', message='{error!s}'")


def fr_sim_037() -> None:
    """
    FR-SIM-037: Stage 2 — Convert exception into bounded redacted public error payload.

    The system shall convert a controlled exception into a bounded, redacted payload exposing no provider exception, path, credential, or raw payload.
    """
    _header("Stage 2: Error Payload - Format Public Error Payload (FR-SIM-037)")
    try:
        unwrap_simulation_response(
            validate_phase_one_scope(
                {
                    "asset_class": "CRYPTO",
                    "runtime_profile": "simulation",
                    "execution_route": "sim",
                }
            ),
            operation="usage.errors.validate_phase_one_scope",
        )
    except Exception as error:  # noqa: BLE001
        resp = to_simulation_error_payload(error)
        payload = resp.data if hasattr(resp, "data") else resp
        print(_format_result(resp))
        print(
            f"Data -> error_code='{payload.get('code') if isinstance(payload, dict) else getattr(payload, 'code', None)}'"
        )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-08 — errors/ — Domain Error Taxonomy\n\n"
        "Purpose: Expose closed Simulation error taxonomy, handle controlled domain exceptions, and format bounded redacted error payloads.\n\n"
        "Module flow:\n"
        "-> Stage 1: Authoritative closed error catalog lookup\n"
        "-> Stage 2: Controlled exception catching and boundary fail-closed verification\n"
        "-> Stage 3: Public error payload formatting with secret/path redaction"
    )

    # Stage 1: Error catalog lookup
    fr_sim_036()

    # Stage 2: Exception handling & Error payload formatting
    fr_sim_035()
    fr_sim_037()


if __name__ == "__main__":
    main()

"""Executable Simulation errors usage example.

Demonstrates simulation error construction, error catalog inspection, and error
payload formatting.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator import (
    SIM_ERROR_CATALOG,
    SimulationError,
    to_simulation_error_payload,
    unwrap_simulation_response,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_sim_035() -> None:
    """Demonstrate FR-SIM-035.

    Responsibility:
        The system shall expose one base exception carrying a cataloged `code`, bounded
        redacted message/details, and optional request/correlation identifiers. Every
        controlled Simulation boundary failure surfaces through it; no uncontrolled
        exception crosses the run boundary.
    """
    _header(
        "Demonstrate FR-SIM-035. Responsibility: The system shall expose one base exception carrying a cataloged `code`, bounded redacted message/details, and optional request/correlation identifiers. Every controlled Simulation boundary failure surfaces through it; no uncontrolled exception crosses the run boundary."
    )
    error = SimulationError("SIM_MARKET_CLOSED", "Configured market is closed")
    print(f"SimulationError code: {error.code}, message: {error.message}")


def fr_sim_036() -> None:
    """Demonstrate FR-SIM-036.

    Responsibility:
        The system shall expose the authoritative closed catalog of Simulation error
        codes with group, meaning, and fail-closed effect. Every code raised by any
        `FR-SIM-*` appears here, and no code appears that no requirement raises.
    """
    _header(
        "Demonstrate FR-SIM-036. Responsibility: The system shall expose the authoritative closed catalog of Simulation error codes with group, meaning, and fail-closed effect. Every code raised by any `FR-SIM-*` appears here, and no code appears that no requirement raises."
    )
    catalog_entry = SIM_ERROR_CATALOG.get("SIM_MARKET_CLOSED")
    print(
        "Catalog entry for SIM_MARKET_CLOSED group: "
        f"{catalog_entry.category if catalog_entry else None}"
    )


def fr_sim_037() -> None:
    """Demonstrate FR-SIM-037.

    Responsibility:
        The system shall convert a controlled exception into a bounded, redacted payload
        exposing no provider exception, path, credential, or raw payload.
    """
    _header(
        "Demonstrate FR-SIM-037. Responsibility: The system shall convert a controlled exception into a bounded, redacted payload exposing no provider exception, path, credential, or raw payload."
    )
    payload = unwrap_simulation_response(
        to_simulation_error_payload(
            SimulationError("SIM_INVALID_CONFIG", "Invalid configuration")
        ),
        operation="usage.errors.to_simulation_error_payload",
    )
    print(f"Converted error payload code: {payload['code']}")


def main() -> None:
    """Run Simulator errors usage example."""
    fr_sim_035()
    fr_sim_036()
    fr_sim_037()


if __name__ == "__main__":
    main()

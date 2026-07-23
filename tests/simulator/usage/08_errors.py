"""Executable Simulation errors usage example.

Demonstrates simulation error construction, error catalog inspection, and error payload formatting.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator.errors import (
    SIM_ERROR_CATALOG,
    SimulationError,
    to_simulation_error_payload,
)


def example_errors() -> None:
    """Demonstrate Simulation error handling and catalog."""
    print("=" * 80)
    print("Simulator Example 8: Error Catalog and Payload Serialization")
    print("=" * 80)

    # 1. Construct SimulationError
    error = SimulationError("SIM_MARKET_CLOSED", "Configured market is closed")
    print(f"SimulationError code: {error.code}, message: {error.message}")

    # 2. Inspect Error Catalog
    catalog_entry = SIM_ERROR_CATALOG.get("SIM_MARKET_CLOSED")
    print(
        f"Catalog entry for SIM_MARKET_CLOSED group: {catalog_entry['group'] if catalog_entry else None}"
    )

    # 3. Payload conversion
    payload = to_simulation_error_payload(
        SimulationError("SIM_INVALID_CONFIG", "Invalid configuration")
    )
    print(f"Converted error payload code: {payload['code']}")


def main() -> None:
    """Run Simulator errors usage example."""
    example_errors()


if __name__ == "__main__":
    main()

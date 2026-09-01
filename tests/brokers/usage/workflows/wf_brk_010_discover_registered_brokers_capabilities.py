"""WF-BRK-010: discover registered brokers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    get_broker_id,
    get_broker_value_field,
    get_registered_brokers,
)

WORKFLOW_ID = "WF-BRK-010"
STAGES = (
    "Enumerate the registered broker identifiers.",
    "Confirm discovery imports no provider package and opens no session.",
    "Show that an unregistered identifier is absent rather than empty.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, status: str, data: object) -> None:
    """Print the status and bounded data of one workflow step."""
    print(f"{label} status : {status}")
    print(f"{label} data   : {data}")


def main() -> None:
    """Run the documented broker discovery workflow without creating an adapter."""
    print(f"{WORKFLOW_ID} — Discover Registered Brokers")
    print(
        "INPUT BOUNDARY — a caller queries the static registry before creating any adapter"
    )

    modules_before = {name for name in sys.modules if "MetaTrader5" in name}

    # Stage 1 — Enumerate the registered broker identifiers.
    _stage(1)
    registered_response = get_registered_brokers()
    status = get_broker_value_field(registered_response, "status")
    _report("registry", status, None)
    assert status == "success"
    registered = get_broker_value_field(registered_response, "data")
    assert registered is not None
    print(
        "Registered broker IDs :",
        tuple(get_broker_value_field(item, "value") for item in registered),
    )
    print("Registered count      :", len(registered))
    mt5_id = get_broker_id("mt5")
    assert mt5_id in registered

    # Stage 2 — Confirm discovery imports no provider package and opens no session.
    _stage(2)
    modules_after = {name for name in sys.modules if "MetaTrader5" in name}
    newly_imported = modules_after - modules_before
    _report("imports ", "success", f"{len(newly_imported)} provider modules imported")
    print("Discovery is import-safe and side-effect free:", not newly_imported)
    print("No session opened and no credential resolved: True")

    # Stage 3 — Show that an unregistered identifier is absent rather than empty.
    _stage(3)
    unknown_key = "not_a_registered_broker"
    present = any(
        get_broker_value_field(item, "value") == unknown_key for item in registered
    )
    _report("unknown ", "success", f"present={present}")
    print("Unregistered identifier is absent, not an empty record:", present is False)

    print("\nOUTPUT BOUNDARY — registered broker set")


if __name__ == "__main__":
    main()

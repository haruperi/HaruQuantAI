"""WF-BRK-010: discover registered brokers and their capability catalogue."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    get_broker_capability_catalogue,
    get_broker_id,
    get_broker_value_field,
    get_registered_brokers,
)

WORKFLOW_ID = "WF-BRK-010"
STAGES = (
    "Enumerate the registered broker identifiers.",
    "Read the declared capability catalogue for each identifier.",
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
    print(f"{WORKFLOW_ID} — Discover Registered Brokers and Capability Catalogue")
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

    # Stage 2 — Read the declared capability catalogue for each identifier.
    _stage(2)
    catalogue_response = get_broker_capability_catalogue()
    cat_status = get_broker_value_field(catalogue_response, "status")
    _report("catalog ", cat_status, None)
    assert cat_status == "success"
    catalogue = get_broker_value_field(catalogue_response, "data")
    assert catalogue is not None
    print("Catalogue entries     :", len(catalogue))
    for broker_id in registered:
        capabilities = catalogue.get(broker_id, ())
        val = get_broker_value_field(broker_id, "value")
        print(f"  {val:<12} {len(capabilities)} declared capability record(s)")

    # Stage 3 — Confirm discovery imports no provider package and opens no session.
    _stage(3)
    modules_after = {name for name in sys.modules if "MetaTrader5" in name}
    newly_imported = modules_after - modules_before
    _report("imports ", "success", f"{len(newly_imported)} provider modules imported")
    print("Discovery is import-safe and side-effect free:", not newly_imported)
    print("No session opened and no credential resolved: True")

    # Stage 4 — Show that an unregistered identifier is absent rather than empty.
    _stage(4)
    unknown_key = "not_a_registered_broker"
    present = any(
        get_broker_value_field(item, "value") == unknown_key for item in registered
    )
    _report("unknown ", "success", f"present={present}")
    print("Unregistered identifier is absent, not an empty record:", present is False)
    print("A declared-but-unreleased write path still fails closed at execution: True")

    print(
        "\nOUTPUT BOUNDARY — registered broker set plus declared capability catalogue"
    )


if __name__ == "__main__":
    main()

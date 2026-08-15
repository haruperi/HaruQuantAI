"""Simulation mutation capability and architecture conformance tests."""

from __future__ import annotations

import ast
from pathlib import Path

from app.services.brokers import (
    get_broker_capability_catalogue,
    get_broker_capability_id,
    get_broker_id,
)


def test_exact_mutation_intersection_is_available() -> None:
    """Only the seven Phase-12 mutations join the simulation intersection."""
    catalogue = get_broker_capability_catalogue().data
    assert catalogue is not None
    by_id = {item.capability: item for item in catalogue[get_broker_id("sim")]}
    admitted = {
        "check_order",
        "place_order",
        "modify_order",
        "cancel_order",
        "modify_position",
        "reduce_position",
        "close_position",
    }
    for name in admitted:
        assert by_id[get_broker_capability_id(name)].availability == "AVAILABLE"
    assert by_id[get_broker_capability_id("replace_order")].availability == (
        "UNAVAILABLE"
    )


def test_adapter_owns_no_matching_accounting_or_simulation_import() -> None:
    """Brokers contains delegation and mapping but no business-state engine."""
    path = Path("app/services/brokers/simulation/adapter.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(module.startswith("app.services.simulation") for module in imports)
    lowered = source.lower()
    for forbidden in ("matching_engine", "position_accounting", "fill_ledger"):
        assert forbidden not in lowered

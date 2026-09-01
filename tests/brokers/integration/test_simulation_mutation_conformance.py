"""Simulation mutation capability and architecture conformance tests."""

from __future__ import annotations

import ast
from pathlib import Path


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

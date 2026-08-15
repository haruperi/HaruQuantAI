"""Isolation tests for FEAT-BRK-17."""

import ast
from pathlib import Path

from app.services.brokers import build_broker_connection_config


def test_simulation_adapter_import_graph_is_acyclic() -> None:
    """Brokers production code never imports the Simulator domain."""
    root = Path("app/services/brokers")
    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "app.services.simulator" not in source
        ast.parse(source)


def test_simulation_config_requires_no_credentials_or_endpoint() -> None:
    """The in-process channel is configured without transport material."""
    config = build_broker_connection_config("sim", "simulation")
    assert config.credentials is None
    assert config.endpoint is None

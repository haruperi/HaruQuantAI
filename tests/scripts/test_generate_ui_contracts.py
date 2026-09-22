"""Tests for UI contracts generation script."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType


def _load_generator() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "generate_ui_contracts.py"
    )
    module_name = "_generate_ui_contracts_under_test"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        msg = f"Unable to load generator from {script_path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_generator()
generate_typescript_contracts = _GENERATOR.generate_typescript_contracts


def test_contracts_content_structure() -> None:
    """Generated contracts contain all required wire types and interfaces."""
    code = generate_typescript_contracts()
    assert "export type ValueKind =" in code
    assert "export interface PluginRef" in code
    assert "export interface ParameterSpec" in code
    assert "export interface PortSpec" in code
    assert "export interface WorkspaceSpec" in code
    assert "export interface CatalogEntryView" in code
    assert "export interface GraphDocument" in code
    assert "export interface SingleExecutionRequest" in code
    assert "export interface SingleExecutionResult" in code
    assert "export interface BatchExecutionRequest" in code
    assert "export interface ExportRequest" in code
    assert "export interface ApiResponse<T = unknown>" in code


def test_contracts_check_cli() -> None:
    """CLI --check succeeds when file is up to date."""
    root = Path(__file__).resolve().parent.parent.parent
    cmd = [sys.executable, "-m", "scripts.generate_ui_contracts", "--check"]
    res = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert "up to date" in res.stdout


def test_contracts_source_matches_live_backend() -> None:
    """The checked-in JSON descriptions cannot drift from the live backend."""
    import json
    from pathlib import Path

    from app.plugins.schema import (
        Alignment,
        OptimizationDistribution,
        OptimizationScale,
        Unit,
        ValueKind,
        WidgetKind,
    )

    source_path = (
        Path(__file__).resolve().parent.parent.parent
        / "scripts"
        / "ui_contracts_source.json"
    )
    source = json.loads(source_path.read_text(encoding="utf-8"))

    live = {
        "ValueKind": [v.value for v in ValueKind],
        "Unit": [v.value for v in Unit],
        "Alignment": [v.value for v in Alignment],
        "WidgetKind": [v.value for v in WidgetKind],
        "OptimizationScale": [v.value for v in OptimizationScale],
        "OptimizationDistribution": [v.value for v in OptimizationDistribution],
    }
    for name, expected in live.items():
        assert source["enums"][name] == expected, (
            f"{name} drifted: source={source['enums'][name]} live={expected}"
        )

    # envelope shape matches the gateway's actual envelopes
    from app.host.gateway import GATEWAY_API_VERSION, _error_envelope, _success_envelope

    assert source["api_version"] == GATEWAY_API_VERSION
    success = _success_envelope({"k": 1}, "req_1")
    assert sorted(source["envelope"]["top_level_keys"]) == sorted(success)
    assert success["status"] == source["envelope"]["success_status"]
    error = _error_envelope("CODE", "message", "req_1")
    assert error["status"] == source["envelope"]["error_status"]
    assert sorted(source["envelope"]["error_object_keys"]) == sorted(error["error"])

    # route list matches the gateway's registered routes
    from app.host.gateway import GatewayConfig, _GatewayProvider

    provider = _GatewayProvider(GatewayConfig())
    provider.set_dependencies(None, None)
    app = provider.create_asgi_app()
    routes = sorted(
        f"{sorted(r.methods)[0]} {r.path}" for r in app.routes if hasattr(r, "methods")
    )
    assert sorted(source["routes"]) == routes

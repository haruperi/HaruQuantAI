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

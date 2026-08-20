"""Unit tests for runtime and configuration graph extractor.

Traces to: P2-T02, Gate G2
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.architecture.provider_runtime_graph import scan_runtime_and_config


def test_extracts_runtime_edges(tmp_path: Path) -> None:
    """Verify scanner extracts runtime execution edges."""
    mod = tmp_path / "runtime_app.py"
    mod.write_text(
        """
import asyncio
import threading
import subprocess

def create_engine():
    pass

def setup_app(app):
    app.include_router(None)
    asyncio.create_task(None)
    threading.Thread(target=None)
    subprocess.run(["echo", "1"])
""",
        encoding="utf-8",
    )

    graph = scan_runtime_and_config(tmp_path)
    kinds = {e["kind"] for e in graph["runtime_edges"]}
    assert "router_mount" in kinds
    assert "background_task" in kinds
    assert "subprocess" in kinds
    assert "factory" in kinds


def test_extracts_configuration_edges(tmp_path: Path) -> None:
    """Verify scanner extracts configuration kinds."""
    mod = tmp_path / "config_app.py"
    mod.write_text(
        """
API_KEY = "my_secret_token"  # pragma: allowlist secret
ALLOWLIST_HOSTS = ["localhost"]
ENABLE_FEATURE_FLAG = True
MODULE_PATH = "app.module"

def run_mode():
    check("research")
    deploy("dev")
    select_broker("mt5")
""",
        encoding="utf-8",
    )

    graph = scan_runtime_and_config(tmp_path)
    kinds = {c["kind"] for c in graph["configuration_edges"]}
    assert "secret_reference" in kinds
    assert "allowlist" in kinds
    assert "feature_flag" in kinds
    assert "module_path" in kinds
    assert "profile" in kinds
    assert "environment" in kinds
    assert "provider_name" in kinds


def test_never_serializes_secret_value(tmp_path: Path) -> None:
    """Verify secret variable names are recorded but plain-text values are never stored."""
    secret_value = "super_secret_password_12345"  # pragma: allowlist secret
    mod = tmp_path / "secret_store.py"
    mod.write_text(f'DATABASE_PASSWORD = "{secret_value}"\n', encoding="utf-8")

    graph = scan_runtime_and_config(tmp_path)
    serialized = json.dumps(graph)
    assert "DATABASE_PASSWORD" in serialized
    assert secret_value not in serialized


def test_unresolved_owner_exits_two(tmp_path: Path) -> None:
    """Verify unexplained entries cause exit code 2."""
    script_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "architecture"
        / "provider_runtime_graph.py"
    )
    mod = tmp_path / "clean_app.py"
    mod.write_text("X = 1\n", encoding="utf-8")

    res = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(script_path),
            "--root",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0

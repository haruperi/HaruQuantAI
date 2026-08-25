"""Determinism and artifact-shape tests for the contract generator.

Runs ``scripts/generate_contracts.py --check`` as the single subprocess
gate, then verifies byte-determinism of ``render_artifacts()`` and the
on-disk artifact tree (16 wire schemas plus 17 generated TypeScript
modules).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATOR_SCRIPT = REPO_ROOT / "scripts" / "generate_contracts.py"
CONTRACTS_ROOT = REPO_ROOT / "app" / "contracts"
UI_GENERATED_DIR = REPO_ROOT / "app" / "ui" / "src" / "contracts" / "generated"

OWNERS: tuple[str, ...] = (
    "common",
    "workspace",
    "catalogue",
    "data",
    "strategy",
    "simulator",
    "analytics",
    "research",
    "portfolio",
    "orchestration",
    "interfaces",
    "ui",
    "plugins",
    "broker",
    "risk",
    "trading",
)

EXPECTED_ARTIFACT_COUNT = 33
FORBIDDEN_TS_NAMES = frozenset({"ui_contracts.ts", "client.ts"})

# Module-level caches: rendering every namespace is expensive, so the
# generator module and one render result are computed at most once and
# reused by every test in this module. A mutable holder avoids global
# statements while keeping the cache shared across tests.
_CACHE: dict[str, Any] = {}


def _load_generator_module() -> ModuleType:
    """Import scripts/generate_contracts.py as an isolated module."""
    if "module" not in _CACHE:
        spec = importlib.util.spec_from_file_location(
            "generate_contracts", GENERATOR_SCRIPT
        )
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _CACHE["module"] = module
    result = _CACHE["module"]
    assert isinstance(result, ModuleType)
    return result


def _cached_artifacts() -> dict[Path, str]:
    """Return the cached render_artifacts() result for test assertions."""
    artifacts = _CACHE.get("artifacts")
    if artifacts is None:
        artifacts = _load_generator_module().render_artifacts()
        _CACHE["artifacts"] = artifacts
    assert isinstance(artifacts, dict)
    return artifacts


def test_generator_check_mode_exits_zero() -> None:
    """Verify the --check mode reports a fully up-to-date artifact tree."""
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT))
    completed = subprocess.run(  # noqa: S603 - fixed argv of trusted constants
        [sys.executable, str(GENERATOR_SCRIPT), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, (
        "generate_contracts.py --check failed:\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )


def test_generator_check_mode_handles_crlf_line_endings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify check_mode succeeds when disk files contain CRLF line endings."""
    generator = _load_generator_module()
    artifacts = _cached_artifacts()
    sample_path = next(iter(artifacts.keys()))
    crlf_content: str = artifacts[sample_path].replace("\n", "\r\n")

    original_read_text = Path.read_text

    def mock_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        if self == sample_path:
            return crlf_content
        return str(original_read_text(self, *args, **kwargs))

    monkeypatch.setattr(Path, "read_text", mock_read_text)
    assert generator.check_mode() == 0


def test_render_artifacts_is_deterministic_and_complete() -> None:
    """Verify two fresh renders produce identical 33-artifact mappings."""
    generator = _load_generator_module()
    first = generator.render_artifacts()
    second = generator.render_artifacts()
    assert first == second
    assert len(first) == EXPECTED_ARTIFACT_COUNT
    schema_paths = [path for path in first if path.name == "schema.json"]
    ts_paths = [path for path in first if path.suffix == ".ts"]
    assert len(schema_paths) == 16
    assert len(ts_paths) == 17
    # Reuse the verified render for the remaining artifact-shape tests.
    _CACHE["artifacts"] = second


def test_render_artifacts_match_check_mode_inventory() -> None:
    """Verify the rendered artifact set covers every owner plus the barrel."""
    artifacts = _cached_artifacts()
    expected_schema_paths = {
        CONTRACTS_ROOT / owner / "wire" / "schema.json" for owner in OWNERS
    }
    expected_ts_paths = {UI_GENERATED_DIR / f"{owner}.ts" for owner in OWNERS} | {
        UI_GENERATED_DIR / "index.ts"
    }
    assert set(artifacts) == expected_schema_paths | expected_ts_paths


def test_wire_schema_json_parses_and_declares_namespace() -> None:
    """Verify each on-disk schema.json parses and matches its directory."""
    wire_files = sorted(CONTRACTS_ROOT.glob("*/wire/schema.json"))
    assert len(wire_files) == 16
    for path in wire_files:
        document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        namespace = document.get("namespace")
        assert isinstance(namespace, str)
        assert namespace == path.parent.parent.name
        assert document.get("schema_version") == 1
        assert "$defs" in document


def test_generated_typescript_directory_shape() -> None:
    """Verify exactly 17 generated TS files with no legacy names."""
    generated_files = sorted(UI_GENERATED_DIR.iterdir())
    assert len(generated_files) == 17
    names = {path.name for path in generated_files}
    assert all(path.suffix == ".ts" for path in generated_files)
    assert "index.ts" in names
    for owner in OWNERS:
        assert f"{owner}.ts" in names
    assert not names & FORBIDDEN_TS_NAMES

"""Unit tests for static provider dependency graph extractor.

Traces to: P2-T01, Gate G2
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.architecture.provider_static_graph import scan_repository


def test_extracts_import_kinds(tmp_path: Path) -> None:
    """Verify scanner extracts import, from_import, dynamic_import, and lazy_export."""
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        """
import math
from os import path
import importlib

_EXPORTS = {
    "my_func": "mypkg.submodule",
}

def load_dyn():
    return importlib.import_module("mypkg.dynamic_mod")
""",
        encoding="utf-8",
    )
    (pkg / "submodule.py").write_text("def my_func(): pass\n", encoding="utf-8")
    (pkg / "dynamic_mod.py").write_text("VAR = 1\n", encoding="utf-8")

    graph = scan_repository(tmp_path)
    kinds = {edge["kind"] for edge in graph["edges"]}
    assert "import" in kinds
    assert "from_import" in kinds
    assert "lazy_export" in kinds
    assert "dynamic_import" in kinds


def test_marks_type_checking_edge(tmp_path: Path) -> None:
    """Verify guarded imports are marked with type_checking=True."""
    mod = tmp_path / "typed_mod.py"
    mod.write_text(
        """
from typing import TYPE_CHECKING
import sys

if TYPE_CHECKING:
    import typing_extensions
""",
        encoding="utf-8",
    )

    graph = scan_repository(tmp_path)
    tc_edges = [e for e in graph["edges"] if e["type_checking"]]
    assert len(tc_edges) >= 1
    assert any(e["target"] == "typing_extensions" for e in tc_edges)


def test_rejects_dynamic_expression(tmp_path: Path) -> None:
    """Verify non-literal dynamic imports cause exit code 2."""
    script_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "architecture"
        / "provider_static_graph.py"
    )
    bad_mod = tmp_path / "bad.py"
    bad_mod.write_text(
        """
import importlib
def dyn(name):
    return importlib.import_module(name)
""",
        encoding="utf-8",
    )

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
    assert res.returncode == 2
    assert "UNEXPLAINED_DYNAMIC_IMPORT" in res.stderr


def test_output_is_deterministic(tmp_path: Path) -> None:
    """Verify running scan twice produces identical JSON structure and bytes."""
    mod = tmp_path / "mod.py"
    mod.write_text("import json\nimport os\n", encoding="utf-8")

    graph1 = scan_repository(tmp_path)
    graph2 = scan_repository(tmp_path)

    bytes1 = json.dumps(graph1, sort_keys=True, indent=2)
    bytes2 = json.dumps(graph2, sort_keys=True, indent=2)
    assert bytes1 == bytes2

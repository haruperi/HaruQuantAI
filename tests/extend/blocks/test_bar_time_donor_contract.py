"""Guard SQX BarAndTime donor-to-Python structural contracts.

The historical donor inventory is NOT evidence of behavioral parity. This suite
checks that all donor block names, registered APIs and Python signatures remain
covered. With HARU_SQX_BAR_AND_TIME_DONOR pointing at the actual Java directory,
it also verifies that the input donor snapshot matches the audited SHA-256s.
Output/parameter/edge-case parity requires donor-executed fixtures separately.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import re
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_INVENTORY_PATH = (
    _PROJECT_ROOT / "docs/dev/fixtures/blocks-donor-coverage-inventory.json"
)
_PACKAGE_PATH = _PROJECT_ROOT / "app/extend/blocks/bar_time"
_PACKAGE = "app.extend.blocks.bar_time"
_SUPPORT_MODULES = {"__init__", "_common", "facade"}


def _donor_rows() -> list[dict[str, object]]:
    payload = json.loads(_INVENTORY_PATH.read_text(encoding="utf-8"))
    return [
        row
        for row in payload["inventory"]
        if str(row["donor"]).startswith("BarAndTime/")
    ]


def _python_name(java_filename: str) -> str:
    stem = Path(java_filename).stem
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", stem).lower()


def test_every_donor_class_has_one_registered_python_block() -> None:
    """Require a one-to-one module/API/metadata mapping for all donor classes."""
    rows = _donor_rows()
    assert len(rows) == 37, "Audited SQX donor snapshot changed"

    expected_names = {_python_name(str(row["donor"])) for row in rows}
    assert len(expected_names) == len(rows), "Duplicate donor Python names"

    actual_names = {
        path.stem
        for path in _PACKAGE_PATH.glob("*.py")
        if path.stem not in _SUPPORT_MODULES
    }
    assert actual_names == expected_names, {
        "missing": sorted(expected_names - actual_names),
        "unexpected": sorted(actual_names - expected_names),
    }

    package = importlib.import_module(_PACKAGE)
    for row in rows:
        name = _python_name(str(row["donor"]))
        module = importlib.import_module(f"{_PACKAGE}.{name}")
        implementation = getattr(module, name)
        spec = getattr(module, f"{name}_spec")

        assert callable(implementation), name
        assert getattr(implementation, "_block_spec", None) is spec, name
        assert spec.id == row["direct_catalog_id"], name
        assert spec.category == "bar_time", name
        assert len(spec.outputs) == 1, name
        assert getattr(package, name) is implementation, name
        assert getattr(package, f"{name}_spec") is spec, name

        # The editor/compiler must be able to bind every declared input by name.
        parameter_names = tuple(inspect.signature(implementation).parameters)
        port_names = tuple(port.name for port in spec.inputs)
        assert parameter_names == port_names, {
            "block": name,
            "parameters": parameter_names,
            "declared_inputs": port_names,
        }


def test_checked_donor_sources_match_inventory_when_provided() -> None:
    """Reject a different donor build rather than falsely certifying parity."""
    value = os.environ.get("HARU_SQX_BAR_AND_TIME_DONOR")
    if not value:
        pytest.skip(
            "Actual SQX Java donor not available: set "
            "HARU_SQX_BAR_AND_TIME_DONOR to the BarAndTime directory"
        )

    donor_root = Path(value)
    assert donor_root.is_dir(), f"Donor directory not found: {donor_root}"
    rows = _donor_rows()
    expected = {Path(str(row["donor"])).name for row in rows}
    actual = {path.name for path in donor_root.glob("*.java")}
    assert actual == expected, {
        "missing_java": sorted(expected - actual),
        "unexpected_java": sorted(actual - expected),
    }

    for row in rows:
        name = Path(str(row["donor"])).name
        digest = hashlib.sha256((donor_root / name).read_bytes()).hexdigest()
        assert digest == row["sha256"], (
            f"{name} differs from audited SQX donor snapshot. "
            "Re-inventory the donor before making behavioral parity claims."
        )

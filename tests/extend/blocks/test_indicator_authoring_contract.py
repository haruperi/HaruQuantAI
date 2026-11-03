"""Enforce the canonical layout across the complete indicator package.

Description:
    Discovers indicator modules independently of hand-maintained class lists,
    checks their authoring structure, and verifies rejection logging before
    calculations can consume missing market feeds.
Purpose:
    FEAT-INDICATORS-BLOCKS: Retain a consistent, discoverable indicator contract.
Key Capabilities:
    - FR-indicator-authoring-layout: Verify compact headers and explicit sections.
    - FR-indicator-authoring-inputs: Verify missing feeds fail before calculation.
    - FR-indicator-authoring-logging: Capture actual calculation request records.
Python API Usage:
    Run the tests with pytest.
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_authoring_contract.py --no-cov
"""

from __future__ import annotations

import ast
import importlib
import logging
from dataclasses import replace
from pathlib import Path
from typing import cast

import numpy as np
import pytest
from app.core.trading.blocks.registry import BlockRegistry
from app.core.trading.blocks.series import BarData
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.template import IndicatorTemplate
from app.workspace.code_editor._indicator_resolver import resolve_indicator

ROOT = Path("app/extend/blocks/indicators")
PATHS = sorted(ROOT.rglob("*.py"))


def _indicator_node(tree: ast.Module) -> ast.ClassDef | None:
    """Find the module's own indicator without counting imported classes."""
    return next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and any(
                isinstance(base, ast.Name) and base.id == "BaseIndicator"
                for base in node.bases
            )
        ),
        None,
    )


def _indicator_type(path: Path, node: ast.ClassDef) -> type[BaseIndicator]:
    """Import a discovered module's public indicator class."""
    module = importlib.import_module(".".join(path.with_suffix("").parts))
    return cast("type[BaseIndicator]", getattr(module, node.name))


@pytest.mark.parametrize("path", PATHS, ids=lambda path: path.relative_to(ROOT))
def test_module_header_and_indicator_layout(path: Path) -> None:
    """Keep files easy to scan while retaining each indicator's optional methods."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assert ast.get_docstring(tree)
    header = tree.body[0]
    assert header.end_lineno is not None
    assert header.end_lineno - header.lineno + 1 <= 20
    node = _indicator_node(tree)
    if node is None:
        return  # Package exports and the base re-export are support modules.
    methods = {
        member.name: member
        for member in node.body
        if isinstance(member, ast.FunctionDef)
    }
    spec = next(
        member
        for member in node.body
        if isinstance(member, ast.AnnAssign)
        and isinstance(member.target, ast.Name)
        and member.target.id == "spec"
    )
    assert isinstance(spec.value, ast.Call)
    assert [keyword.arg for keyword in spec.value.keywords] == [
        "id",
        "version",
        "name",
        "description",
        "category",
        "tags",
        "execution_kind",
        "chart_pane",
        "inputs",
        "outputs",
        "required_market_inputs",
        "required_history_lookback",
        "dependencies",
        "is_generation_eligible",
        "parameter_search_space",
        "is_deterministic",
        "is_causal",
        "supports_incremental",
    ]
    assert (
        spec.lineno
        < methods["required_inputs"].lineno
        < methods["required_history"].lineno
        < methods["calculate"].lineno
    )
    for member in node.body:
        if (
            isinstance(member, ast.AnnAssign)
            and isinstance(member.target, ast.Name)
            and member.target.id != "spec"
            and not member.target.id.startswith("_")
        ):
            assert spec.lineno < member.lineno < methods["required_inputs"].lineno
    assert node.end_lineno is not None
    for member in tree.body:
        if isinstance(member, (ast.ClassDef, ast.FunctionDef)) and member is not node:
            assert member.lineno > node.end_lineno
    module = importlib.import_module(".".join(path.with_suffix("").parts))
    assert module.__all__ == [node.name]
    cls = _indicator_type(path, node)
    assert cls.spec.description and cls.spec.tags
    assert all(port.description for port in cls.spec.inputs)
    assert all(port.description for port in cls.spec.outputs)
    assert all(field.title and field.description for field in cls.model_fields.values())
    assert cls().required_history() >= 1


@pytest.mark.parametrize("path", PATHS, ids=lambda path: path.relative_to(ROOT))
def test_missing_inputs_are_logged_before_calculation(
    path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Reject unavailable feeds before algorithms run, including early returns."""
    node = _indicator_node(ast.parse(path.read_text(encoding="utf-8")))
    if node is None:
        return
    cls = _indicator_type(path, node)
    indicator = cls()
    bars = replace(
        BarData.from_arrays(close=np.array([1.0, 2.0, 3.0])),
        available_inputs=frozenset(),
    )
    assert indicator.required_inputs(), "A market indicator must declare its feeds"
    with (
        caplog.at_level(logging.DEBUG, logger=cls.__module__),
        pytest.raises(ValueError, match="Missing indicator inputs"),
    ):
        indicator.calculate(bars)
    records = [record for record in caplog.records if record.name == cls.__module__]
    assert records
    assert "requested" in records[0].getMessage()
    assert "bars=3" in records[0].getMessage()


@pytest.mark.parametrize("path", PATHS, ids=lambda path: path.relative_to(ROOT))
def test_search_ranges_fit_declared_parameter_bounds(path: Path) -> None:
    """Keep generator ranges within field bounds without inventing new ranges."""
    node = _indicator_node(ast.parse(path.read_text(encoding="utf-8")))
    if node is None:
        return
    cls = _indicator_type(path, node)
    properties = cls.model_json_schema()["properties"]
    for name, search in cls.spec.parameter_search_space.items():
        assert name in properties
        field = properties[name]
        if "min" in search and "minimum" in field:
            assert search["min"] >= field["minimum"]
        if "max" in search and "maximum" in field:
            assert search["max"] <= field["maximum"]
        choices = search.get("choices", search.get("values", ()))
        if choices and "enum" in field:
            assert set(choices).issubset(field["enum"])


def test_template_is_discoverable_and_excluded_from_generation() -> None:
    """Manual users can find and run the example without generating strategies."""
    registry = BlockRegistry()
    registry.discover(ROOT, authorized_root="app/extend")
    assert registry.diagnostics == []
    indicators = [
        item for item in registry.snapshot() if item.spec.id.startswith("indicator.")
    ]
    assert len(indicators) == 129
    descriptor = registry.require(IndicatorTemplate.spec.id)
    assert not descriptor.spec.is_generation_eligible
    cls = resolve_indicator(str(ROOT / "template.py"))
    bars = BarData.from_arrays(close=np.array([1.0, 2.0, 3.0, 4.0]))
    result = cls.model_validate({"period": 3}).calculate(bars)
    assert set(result) == {port.name for port in cls.spec.outputs}
    np.testing.assert_allclose(
        result["value"].values, [np.nan, np.nan, 2.0, 3.0], equal_nan=True
    )

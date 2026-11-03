"""Shared compiler and native-export regression tests.

Description:
    Verify exact AST preservation, causal simulation, and native export parity.
Purpose:
    FEAT-WIZARD-COMPILER: Executable compiler acceptance evidence.
Key Capabilities:
    - FR-test-hsl-compiler: Verify complete rules survive compilation and export.
Python API Usage:
    Run pytest against this module.
CLI Usage:
    uv run pytest tests/workspace/algo_wizard --no-cov
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from app.core.data.contracts import MarketBar
from app.core.enums import Timeframe
from app.core.lib.errors import DomainError
from app.core.trading.strategy.contracts import BarUpdateEvent, StrategyContext
from app.core.trading.strategy.hsl.compiler import StrategyCompiler
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.core.trading.strategy.runtime import StrategyRuntime
from app.core.wizard.template_helpers import render_jinja_template
from app.core.wizard.transform import MQL5_TEMPLATE, PYTHON_TEMPLATE


def _document(**changes: Any) -> HSLStrategyDocument:
    return HSLStrategyDocument.model_validate(
        {
            "strategy": {
                "id": "cross",
                "name": "Cross Strategy",
                "parameters": {"level": {"type": "float", "default": 1.1}},
                "rules": [
                    {
                        "id": "cross",
                        "when": {
                            "type": "comparison",
                            "operator": "crosses_above",
                            "left": {"type": "price", "field": "close"},
                            "right": {"type": "parameter", "name": "level"},
                        },
                        "then": [{"action": "enter_market", "side": "long"}],
                        "else_then": [
                            {"action": "emit_alert", "message": "no crossing"}
                        ],
                    }
                ],
                **changes,
            }
        }
    )


def test_compilation_preserves_complete_ast() -> None:
    """Compiled inventory cannot discard else branches or expression definitions."""
    document = _document()
    compiler = StrategyCompiler()
    plan = compiler.compile_to_runtime(document)
    assert json.loads(plan.hsl_json or "") == document.model_dump(mode="json")
    assert all(not rule.conditions and not rule.actions for rule in plan.rules)
    normalized = compiler.compile_to_normalized(document)
    assert normalized.hsl_json == plan.hsl_json


def test_inclusive_crossing_uses_real_backtest_runtime() -> None:
    """Equality on the previous bar permits a cross on the next closed bar."""
    bars = tuple(
        MarketBar(1704110400 + i * 3600, p, p + 0.001, p - 0.001, p, 100)
        for i, p in enumerate((1.09, 1.1, 1.11, 1.12))
    )
    effects = StrategyCompiler().evaluate_hsl_on_bars(_document(), bars)
    assert [len(effect.orders_to_open) for effect in effects] == [0, 0, 1, 0]
    assert effects[2].orders_to_open[0].price == 1.11
    assert effects[1].alerts[0]["message"] == "no crossing"


def test_native_export_executes_the_identical_plan() -> None:
    """Generated Python retains semantics and delegates to the shared evaluator."""
    document = _document(
        rules=[
            {
                "id": "entry",
                "when": {"type": "state", "state": "always_true"},
                "then": [{"action": "enter_market", "side": "long", "size": 0.25}],
            }
        ]
    )
    compiler = StrategyCompiler()
    normalized = compiler.compile_to_normalized(document)
    source = render_jinja_template(PYTHON_TEMPLATE, normalized)
    namespace: dict[str, Any] = {}
    exec(compile(source, "<native-hsl-export>", "exec"), namespace)
    exported = namespace[normalized.class_name]()
    event = BarUpdateEvent(
        "EURUSD",
        Timeframe.PERIOD_H1,
        MarketBar(1704110400, 1.1, 1.101, 1.099, 1.1, 100),
    )
    expected = StrategyRuntime().evaluate(
        compiler.compile_to_runtime(document), StrategyContext(), event
    )
    assert exported.evaluate(event, StrategyContext()) == expected
    with pytest.raises(DomainError) as error:
        render_jinja_template(MQL5_TEMPLATE, normalized)
    assert error.value.code == "HSL_EXPORT_UNSUPPORTED"


def test_unsupported_timeframe_and_lifecycle_are_explicit() -> None:
    """Historical hosts reject event streams they cannot actually provide."""
    bar = MarketBar(1704110400, 1.1, 1.101, 1.099, 1.1, 100)
    with pytest.raises(DomainError) as error:
        StrategyCompiler().evaluate_hsl_on_bars(
            _document(timeframe={"primary": "CUSTOM_TF"}), [bar]
        )
    assert error.value.code == "HSL_UNSUPPORTED_TIMEFRAME"
    document = _document(
        rules=[
            {
                "id": "timer",
                "event": "on_timer",
                "when": {"type": "state", "state": "always_true"},
                "then": [{"action": "emit_alert", "message": "timer"}],
            }
        ]
    )
    with pytest.raises(DomainError) as error:
        StrategyCompiler().evaluate_hsl_on_bars(document, [bar])
    assert error.value.code == "HSL_BACKTEST_EVENT_UNSUPPORTED"


def test_compiler_rejects_unknown_parameter() -> None:
    """Validation runs before compiling or exporting an invalid document."""
    compiler = StrategyCompiler()
    for compile_document in (
        compiler.compile_to_runtime,
        compiler.compile_to_normalized,
    ):
        with pytest.raises(DomainError) as error:
            compile_document(_document(parameters={}))
        assert error.value.code == "WIZARD_UNKNOWN_PARAMETER_REF"


def test_browser_default_document_compiles_without_wire_repair() -> None:
    """The actual TypeScript authoring payload parses through the backend contract."""
    import subprocess
    from pathlib import Path

    script = """
const fs = require('fs'); const ts = require('typescript'); const vm = require('vm');
const source = fs.readFileSync('workspaces/algo_wizard/algoWizardModel.ts', 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const sandbox = { exports: {} }; vm.runInNewContext(compiled, sandbox);
console.log(JSON.stringify(sandbox.exports.DEFAULT_HSL_STRATEGY_DOCUMENT));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[3] / "app" / "web",
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    document = HSLStrategyDocument.model_validate_json(result.stdout)
    assert StrategyCompiler().compile_to_runtime(document).hsl_json

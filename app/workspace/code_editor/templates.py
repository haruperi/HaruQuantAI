"""Snippet templates catalog and code generators for AppCodeEditor.

Key Capabilities:
- Catalog of all 12 StrategyQuant X snippet template definitions.
- Generates clean Python boilerplate conforming to HaruQuantAI architecture.
- Maps template types to canonical output paths in app/include/.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._template_generators import (
    _gen_ai_tools,
    _gen_custom_analysis,
    _gen_databank_column,
    _gen_indicator,
    _gen_money_management,
    _gen_monte_carlo_manipulation,
    _gen_monte_carlo_retest,
    _gen_order,
    _gen_other_actions,
    _gen_signal,
    _gen_trade_column,
    _gen_what_if,
    _to_snake_case,
)


@dataclass(frozen=True)
class SnippetTemplate:
    """Definition for a code snippet template."""

    template_id: str
    name: str
    description: str
    category: str
    default_filename: str
    target_subdir: str
    generator_func_name: str


_TEMPLATES: dict[str, SnippetTemplate] = {
    "BlocksIndicators": SnippetTemplate(
        template_id="BlocksIndicators",
        name="Technical Indicator",
        description="Custom indicator inheriting BaseIndicator with calculate(bars)",
        category="building_blocks",
        default_filename="custom_indicator.py",
        target_subdir="app/include/indicators/custom",
        generator_func_name="_gen_indicator",
    ),
    "BlocksSignal": SnippetTemplate(
        template_id="BlocksSignal",
        name="Signal Condition",
        description="Entry/exit condition rule evaluating indicator series",
        category="building_blocks",
        default_filename="custom_signal.py",
        target_subdir="app/include/signals",
        generator_func_name="_gen_signal",
    ),
    "BlocksOrder": SnippetTemplate(
        template_id="BlocksOrder",
        name="Order Action",
        description="Custom order action rule (Open, Modify, Close order)",
        category="building_blocks",
        default_filename="custom_order.py",
        target_subdir="app/include/orders",
        generator_func_name="_gen_order",
    ),
    "BlocksOtherActions": SnippetTemplate(
        template_id="BlocksOtherActions",
        name="Side-Effect Action",
        description="Side-effects: variable assignment, alert, logger, chart mark",
        category="building_blocks",
        default_filename="custom_action.py",
        target_subdir="app/include/actions",
        generator_func_name="_gen_other_actions",
    ),
    "ColumnsDatabanks": SnippetTemplate(
        template_id="ColumnsDatabanks",
        name="Databank Metric Column",
        description="Custom strategy performance metric / Databank column",
        category="databanks",
        default_filename="custom_metric.py",
        target_subdir="app/include/metrics",
        generator_func_name="_gen_databank_column",
    ),
    "ColumnsTrades": SnippetTemplate(
        template_id="ColumnsTrades",
        name="Trade Column",
        description="Custom per-trade metric computed over trade execution records",
        category="databanks",
        default_filename="custom_trade_column.py",
        target_subdir="app/include/trade_columns",
        generator_func_name="_gen_trade_column",
    ),
    "MoneyManagement": SnippetTemplate(
        template_id="MoneyManagement",
        name="Money Management",
        description="Position sizing algorithm computing trade order volume",
        category="money_management",
        default_filename="custom_position_sizer.py",
        target_subdir="app/include/money_management",
        generator_func_name="_gen_money_management",
    ),
    "MonteCarloManipulation": SnippetTemplate(
        template_id="MonteCarloManipulation",
        name="Monte Carlo Manipulation",
        description="Trade list manipulation (resample, reshuffle, skip, slippage)",
        category="robustness",
        default_filename="custom_mc_manipulation.py",
        target_subdir="app/include/monte_carlo/manipulation",
        generator_func_name="_gen_monte_carlo_manipulation",
    ),
    "MonteCarloRetest": SnippetTemplate(
        template_id="MonteCarloRetest",
        name="Monte Carlo Retest",
        description="Simulation parameter perturbation to test robustness",
        category="robustness",
        default_filename="custom_mc_retest.py",
        target_subdir="app/include/monte_carlo/retest",
        generator_func_name="_gen_monte_carlo_retest",
    ),
    "WhatIf": SnippetTemplate(
        template_id="WhatIf",
        name="What-If Scenario",
        description="Scenario filtering rule (e.g. drop worst N trades)",
        category="robustness",
        default_filename="custom_what_if.py",
        target_subdir="app/include/what_if",
        generator_func_name="_gen_what_if",
    ),
    "CustomAnalysis": SnippetTemplate(
        template_id="CustomAnalysis",
        name="Custom Analysis Script",
        description="Standalone analytical script running over projects/databanks",
        category="analysis",
        default_filename="custom_analysis.py",
        target_subdir="app/include/analysis",
        generator_func_name="_gen_custom_analysis",
    ),
    "AITools": SnippetTemplate(
        template_id="AITools",
        name="AI Assistant Tool",
        description="Dynamically registered tool callable by AI agents",
        category="ai_tools",
        default_filename="custom_ai_tool.py",
        target_subdir="app/include/ai_tools",
        generator_func_name="_gen_ai_tools",
    ),
}

_GENERATORS = {
    "_gen_indicator": _gen_indicator,
    "_gen_signal": _gen_signal,
    "_gen_order": _gen_order,
    "_gen_other_actions": _gen_other_actions,
    "_gen_databank_column": _gen_databank_column,
    "_gen_trade_column": _gen_trade_column,
    "_gen_money_management": _gen_money_management,
    "_gen_monte_carlo_manipulation": _gen_monte_carlo_manipulation,
    "_gen_monte_carlo_retest": _gen_monte_carlo_retest,
    "_gen_what_if": _gen_what_if,
    "_gen_custom_analysis": _gen_custom_analysis,
    "_gen_ai_tools": _gen_ai_tools,
}


def list_templates() -> list[dict[str, Any]]:
    """Return catalog of all available snippet templates."""
    return [
        {
            "template_id": t.template_id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "default_filename": t.default_filename,
            "target_subdir": t.target_subdir,
        }
        for t in _TEMPLATES.values()
    ]


def get_template(template_id: str) -> SnippetTemplate:
    """Retrieve template definition by ID."""
    if template_id not in _TEMPLATES:
        raise CodeEditorError(f"Unknown template ID: '{template_id}'.")
    return _TEMPLATES[template_id]


def render_template(
    template_id: str, name: str, category: str | None = None
) -> tuple[str, str]:
    """Generate Python boilerplate code and target relative file path.

    Args:
        template_id: Template category identifier.
        name: User-provided name for the new snippet.
        category: Optional subcategory folder (e.g. for indicators).

    Returns:
        Tuple of (rendered_code, relative_file_path).
    """
    if not name.isidentifier() or name.startswith("_"):
        raise CodeEditorError("Snippet name must be a public Python identifier")
    tmpl = get_template(template_id)
    gen_func = _GENERATORS[tmpl.generator_func_name]
    content = gen_func(name)

    snake_name = _to_snake_case(name) or "snippet"
    if template_id == "BlocksIndicators" and category is not None:
        if not category.isidentifier() or category.startswith("_"):
            raise CodeEditorError(
                "Indicator category must be a public Python identifier"
            )
        cat = _to_snake_case(category).strip("_") or "custom"
        target_dir = f"app/include/indicators/{cat}"
    else:
        target_dir = tmpl.target_subdir
    file_path = f"{target_dir}/{snake_name}.py"
    return content, file_path

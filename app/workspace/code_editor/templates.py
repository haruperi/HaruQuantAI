"""Templates editor contracts and workflows.

Description:
    Lists and renders existing Python templates without changing generated computation
    or publication paths.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-templates-get-template: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-templates-list-templates: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-templates-render-template: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor.templates
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

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
    _to_pascal_case,
    _to_snake_case,
)
from app.workspace.code_editor.results import (
    TemplateInfo,
)

logger = logging.getLogger(__name__)


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
        target_subdir="app/extend/blocks/indicators/custom",
        generator_func_name="_gen_indicator",
    ),
    "BlocksSignal": SnippetTemplate(
        template_id="BlocksSignal",
        name="Signal Condition",
        description="Entry/exit condition rule evaluating indicator series",
        category="building_blocks",
        default_filename="custom_signal.py",
        target_subdir="app/extend/signals",
        generator_func_name="_gen_signal",
    ),
    "BlocksOrder": SnippetTemplate(
        template_id="BlocksOrder",
        name="Order Action",
        description="Custom order action rule (Open, Modify, Close order)",
        category="building_blocks",
        default_filename="custom_order.py",
        target_subdir="app/extend/orders",
        generator_func_name="_gen_order",
    ),
    "BlocksOtherActions": SnippetTemplate(
        template_id="BlocksOtherActions",
        name="Side-Effect Action",
        description="Side-effects: variable assignment, alert, logger, chart mark",
        category="building_blocks",
        default_filename="custom_action.py",
        target_subdir="app/extend/actions",
        generator_func_name="_gen_other_actions",
    ),
    "ColumnsDatabanks": SnippetTemplate(
        template_id="ColumnsDatabanks",
        name="Databank Metric Column",
        description="Custom strategy performance metric / Databank column",
        category="databanks",
        default_filename="custom_metric.py",
        target_subdir="app/extend/metrics",
        generator_func_name="_gen_databank_column",
    ),
    "ColumnsTrades": SnippetTemplate(
        template_id="ColumnsTrades",
        name="Trade Column",
        description="Custom per-trade metric computed over trade execution records",
        category="databanks",
        default_filename="custom_trade_column.py",
        target_subdir="app/extend/trade_columns",
        generator_func_name="_gen_trade_column",
    ),
    "MoneyManagement": SnippetTemplate(
        template_id="MoneyManagement",
        name="Money Management",
        description="Position sizing algorithm computing trade order volume",
        category="money_management",
        default_filename="custom_position_sizer.py",
        target_subdir="app/extend/money_management",
        generator_func_name="_gen_money_management",
    ),
    "MonteCarloManipulation": SnippetTemplate(
        template_id="MonteCarloManipulation",
        name="Monte Carlo Manipulation",
        description="Trade list manipulation (resample, reshuffle, skip, slippage)",
        category="robustness",
        default_filename="custom_mc_manipulation.py",
        target_subdir="app/extend/monte_carlo/manipulation",
        generator_func_name="_gen_monte_carlo_manipulation",
    ),
    "MonteCarloRetest": SnippetTemplate(
        template_id="MonteCarloRetest",
        name="Monte Carlo Retest",
        description="Simulation parameter perturbation to test robustness",
        category="robustness",
        default_filename="custom_mc_retest.py",
        target_subdir="app/extend/monte_carlo/retest",
        generator_func_name="_gen_monte_carlo_retest",
    ),
    "WhatIf": SnippetTemplate(
        template_id="WhatIf",
        name="What-If Scenario",
        description="Scenario filtering rule (e.g. drop worst N trades)",
        category="robustness",
        default_filename="custom_what_if.py",
        target_subdir="app/extend/what_if",
        generator_func_name="_gen_what_if",
    ),
    "CustomAnalysis": SnippetTemplate(
        template_id="CustomAnalysis",
        name="Custom Analysis Script",
        description="Standalone analytical script running over projects/databanks",
        category="analysis",
        default_filename="custom_analysis.py",
        target_subdir="app/extend/analysis",
        generator_func_name="_gen_custom_analysis",
    ),
    "AITools": SnippetTemplate(
        template_id="AITools",
        name="AI Assistant Tool",
        description="Dynamically registered tool callable by AI agents",
        category="ai_tools",
        default_filename="custom_ai_tool.py",
        target_subdir="app/extend/ai_tools",
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


def list_templates(file_path: str | None = None) -> list[TemplateInfo]:
    """Return catalog of all available snippet templates."""
    logger.debug("FR-code-editor-templates-list-templates: invoked")
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
        if file_path is None or _template_matches_path(t, file_path)
    ]


def _template_matches_path(template: SnippetTemplate, file_path: str) -> bool:
    from app.workspace.code_editor._common import EXTEND_DIR, resolve_safe_path

    path = resolve_safe_path(file_path)
    if path == EXTEND_DIR.resolve() or path.name == "user":
        return True
    user_root = EXTEND_DIR / "user"
    if path.is_relative_to(user_root):
        path = EXTEND_DIR / path.relative_to(user_root)
    target = resolve_safe_path(template.target_subdir)
    if template.template_id == "BlocksIndicators":
        target = EXTEND_DIR / "blocks" / "indicators"
    if "code_templates" in path.parts:
        return False
    return path.is_relative_to(target) or target.is_relative_to(path)


def get_template(template_id: str) -> SnippetTemplate:
    """Retrieve template definition by ID."""
    logger.debug("FR-code-editor-templates-get-template: invoked")
    if template_id not in _TEMPLATES:
        raise CodeEditorError(f"Unknown template ID: '{template_id}'.")
    return _TEMPLATES[template_id]


def render_template(
    template_id: str,
    name: str,
    category: str | None = None,
    indicator: str | None = None,
    order_action_type: str | None = None,
    mc_type: str | None = None,
) -> tuple[str, str]:
    """Generate Python boilerplate code and target relative file path.

    Args:
        template_id: Template category identifier.
        name: User-provided name for the new snippet.
        category: Optional subcategory folder (e.g. for indicators).
        indicator: Optional canonical indicator for a derived signal.
        order_action_type: Optional Open, Modify or Close subtype.
        mc_type: Manipulation or Retest for the MonteCarlo alias.

    Returns:
        Tuple of (rendered_code, relative_file_path).
    """
    logger.debug("FR-code-editor-templates-render-template: invoked")
    if not name.isidentifier() or name.startswith("_"):
        raise CodeEditorError("Snippet name must be a public Python identifier")
    if template_id == "MonteCarlo":
        if mc_type not in ("Manipulation", "Retest"):
            raise CodeEditorError("Select Manipulation or Retest")
        template_id += mc_type
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
        target_dir = f"app/extend/blocks/indicators/{cat}"
        content = content.replace('category="custom"', f'category="{cat}"').replace(
            'id="indicator.custom.', f'id="indicator.{cat}.'
        )
    else:
        target_dir = tmpl.target_subdir
    if template_id == "BlocksOrder" and order_action_type is not None:
        if order_action_type not in ("Open", "Modify", "Close"):
            raise CodeEditorError("Select Open, Modify or Close order action")
        target_dir += "/" + order_action_type.lower()
        content += f"\nACTION_KIND = {order_action_type.lower()!r}\n"
        content = content.replace(
            '"symbol": symbol,', '"action": ACTION_KIND,\n            "symbol": symbol,'
        )
    if template_id == "BlocksSignal" and indicator:
        from app.workspace.code_editor._indicator_resolver import resolve_indicator

        cls = resolve_indicator(indicator)
        target_dir += "/" + _to_snake_case(cls.__name__)
        content += f"\n# Canonical indicator identity used by this signal.\nINDICATOR = {indicator!r}\nOUTPUT = {cls.spec.outputs[0].name!r}\n"
        from app.workspace.code_editor._common import EXTEND_DIR, INCLUDE_DIR
        from app.workspace.code_editor.catalogue import symbol_catalogue

        indicator_root = EXTEND_DIR / "blocks" / "indicators"
        if not any(indicator_root.rglob("*.py")):
            indicator_root = INCLUDE_DIR / "blocks" / "indicators"
        candidates = [
            s for s in symbol_catalogue(indicator_root) if s.name == cls.__name__
        ]
        if "/" in indicator:
            candidates = [
                s for s in candidates if s.file_path == indicator.split("::", 1)[0]
            ]
        if len(candidates) != 1:
            raise CodeEditorError("Select an unambiguous indicator file")
        class_name = _to_pascal_case(name)
        content += f'''
from {candidates[0].module} import {cls.__name__} as SourceIndicator
from app.include.blocks.series import BarData


def evaluate_indicator(bars: BarData, bar_idx: int, threshold: float = 0.0) -> bool:
    """Calculate the selected indicator output and evaluate this signal."""
    output = SourceIndicator().calculate(bars)[OUTPUT]
    return {class_name}(threshold=threshold).evaluate(output, bars, bar_idx)
'''
    file_path = f"{target_dir}/{snake_name}.py"
    return content, file_path

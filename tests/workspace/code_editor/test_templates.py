"""Unit tests for the 12 Code Editor snippet templates."""

import ast

import pytest
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor.templates import (
    _TEMPLATES,
    get_template,
    list_templates,
    render_template,
)


def test_list_templates_returns_12_templates():
    """Verify that all 12 templates are registered."""
    templates = list_templates()
    assert len(templates) == 12
    ids = {t["template_id"] for t in templates}
    expected = {
        "BlocksIndicators",
        "BlocksSignal",
        "BlocksOrder",
        "BlocksOtherActions",
        "ColumnsDatabanks",
        "ColumnsTrades",
        "MoneyManagement",
        "MonteCarloManipulation",
        "MonteCarloRetest",
        "WhatIf",
        "CustomAnalysis",
        "AITools",
    }
    assert ids == expected


@pytest.mark.parametrize("tmpl_id", list(_TEMPLATES.keys()))
def test_each_template_renders_valid_python(tmpl_id: str):
    """Verify that rendering each template produces syntactically valid Python code."""
    content, file_path = render_template(tmpl_id, "SampleSnippet")
    assert file_path.startswith("app/include/")
    assert file_path.endswith(".py")
    assert len(content) > 50

    # Ensure code compiles without syntax errors
    parsed = ast.parse(content)
    assert parsed is not None


def test_get_template_unknown_raises():
    """Verify unknown template ID raises CodeEditorError."""
    with pytest.raises(CodeEditorError):
        get_template("NonExistentTemplate")


def test_render_indicator_with_custom_category():
    """Verify indicator template targets selected domain subfolder."""
    content, path_vol = render_template(
        "BlocksIndicators", "CustomVol", category="volatility"
    )
    assert path_vol == "app/include/blocks/indicators/volatility/custom_vol.py"
    assert 'id="indicator.volatility.custom_vol"' in content
    assert 'category="volatility"' in content

    _, path_custom = render_template("BlocksIndicators", "CustomAlpha")
    assert path_custom == "app/include/blocks/indicators/custom/custom_alpha.py"

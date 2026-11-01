"""Regression coverage for unified indicator and building block ownership."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from app.include.blocks.indicators.base import BaseIndicator
from app.workspace.code_editor._common import INCLUDE_DIR, CodeEditorError
from app.workspace.code_editor.indicator_tester import IndicatorTester
from app.workspace.code_editor.registry import registry, unresolved_symbols
from app.workspace.code_editor.routes import CodeEditor
from app.workspace.code_editor.templates import render_template


@pytest.fixture
def indicator_folder():
    with TemporaryDirectory(
        dir=INCLUDE_DIR / "blocks/indicators/custom", prefix="regression_"
    ) as folder:
        yield Path(folder)


def test_external_and_traversing_paths_are_rejected_before_execution(tmp_path):
    path = tmp_path / "outside.py"
    marker = tmp_path / "executed.txt"
    path.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8"
    )
    tester = IndicatorTester()
    for candidate in (str(path), "../contracts.py", "../../../app/main.py"):
        with pytest.raises(CodeEditorError):
            tester._resolve_indicator_class(candidate)
    assert not marker.exists()


def test_direct_path_ignores_imported_indicator_dependencies():
    cls = IndicatorTester()._resolve_indicator_class("trend/supertrend.py")
    assert cls.__name__ == "SuperTrend"
    assert issubclass(cls, BaseIndicator)


def test_builtin_resolution_uses_current_compiled_buffer():
    path = INCLUDE_DIR / "blocks/indicators/trend/sma.py"
    source = (
        "from typing import ClassVar\n"
        "from app.include.blocks.indicators.base import BaseIndicator\n"
        "class SMA(BaseIndicator):\n"
        "    revision: ClassVar[int] = 42\n"
        "    def calculate(self, bars): return {}\n"
    )
    result = CodeEditor().compile_file(str(path), source)
    assert result["success"], result
    tester = IndicatorTester()
    cls = tester._resolve_indicator_class("SMA")
    assert cls is registry.blocks[str(path)]["SMA"]
    assert cls.revision == 42
    assert tester._resolve_indicator_class(str(path)) is cls


def test_new_category_and_nonmatching_filename_resolve_uniformly(indicator_folder):
    path = indicator_folder / "different_filename.py"
    source, _ = render_template("BlocksIndicators", "UnifiedProbe")
    path.write_text(source, encoding="utf-8")
    tester = IndicatorTester()
    cls = tester._resolve_indicator_class("UnifiedProbe")
    assert cls.__name__ == "UnifiedProbe"
    result = tester.indicator_tester("UnifiedProbe", bar_count=5)
    assert result["status"] == "success", result


def test_duplicate_names_require_explicit_path(indicator_folder):
    source, _ = render_template("BlocksIndicators", "DuplicateProbe")
    for filename in ("first.py", "second.py"):
        (indicator_folder / filename).write_text(source, encoding="utf-8")
    tester = IndicatorTester()
    with pytest.raises(CodeEditorError, match="Multiple indicators"):
        tester._resolve_indicator_class("DuplicateProbe")
    assert (
        tester._resolve_indicator_class(str(indicator_folder / "first.py")).__name__
        == "DuplicateProbe"
    )


def test_unrelated_syntax_error_does_not_block_indicator_resolution(indicator_folder):
    (indicator_folder / "broken.py").write_text("class Broken(", encoding="utf-8")
    assert IndicatorTester()._resolve_indicator_class("RSI").__name__ == "RSI"


def test_python_314_annotation_symbols_do_not_hide_real_unresolved_globals():
    source = (
        "from dataclasses import dataclass\n@dataclass\nclass Sample:\n    value: int\n"
    )
    assert not unresolved_symbols(source, "sample.py")
    errors = unresolved_symbols(
        source + "\ndef broken(): return missing_value\n", "sample.py"
    )
    assert any("missing_value" in error["message"] for error in errors)


def test_compile_all_accepts_the_real_unified_library():
    result = CodeEditor().compile_all()
    failures = [item for item in result["results"] if not item["success"]]
    assert not failures, failures
    assert result["total_files"] >= 87
    assert not registry.blocks[str(INCLUDE_DIR / "blocks/indicators/base.py")]


def test_dynamic_modules_keep_relative_import_context():
    result = CodeEditor().compile_file(str(INCLUDE_DIR / "contracts.py"))
    assert result["success"], result


def test_nested_ai_tools_register_and_enforce_contract():
    with TemporaryDirectory(
        dir=INCLUDE_DIR / "ai_tools", prefix="regression_"
    ) as folder:
        path = Path(folder) / "probe.py"
        service = CodeEditor()
        invalid = service.compile_file(str(path), "class Invalid: pass")
        assert not invalid["success"]
        source, _ = render_template("AITools", "NestedProbe")
        valid = service.compile_file(str(path), source)
        assert valid["success"], valid
        assert (
            "EURUSD"
            in registry.call_tool("ext_nested_probe", {"target_symbol": "EURUSD"})[
                "result"
            ]
        )


@pytest.mark.parametrize(
    "category", ["", "../trend", "_private", "nested/other", ".hidden"]
)
def test_invalid_indicator_category_is_rejected(category):
    with pytest.raises(CodeEditorError, match="public Python identifier"):
        render_template("BlocksIndicators", "Probe", category)


def test_modular_actions_preserve_the_public_facade():
    from app.include.blocks import actions
    from app.include.blocks.actions.annotations import DrawUpArrowAction
    from app.include.blocks.actions.base import ActionRecord
    from app.include.blocks.actions.facade import Actions

    assert len(actions.__all__) == 19
    assert all(hasattr(actions, name) for name in actions.__all__)
    assert actions.ActionRecord is ActionRecord
    assert actions.Actions is Actions
    assert actions.DrawUpArrowAction is DrawUpArrowAction
    record = Actions.draw_up_arrow(shift=3)
    assert record.action_type == "draw_up_arrow"
    assert record.params["shift"] == 3


def test_validator_accepts_either_base_what_if_and_rejects_unrelated_or_abstract() -> (
    None
):
    import types
    from collections.abc import Sequence

    from app.extend.what_if.base import BaseWhatIf as ExtBaseWhatIf
    from app.extend.what_if.base import WhatIfRecord as ExtRecord
    from app.include.what_if.base import BaseWhatIf as IncBaseWhatIf
    from app.include.what_if.base import WhatIfRecord as IncRecord
    from app.workspace.code_editor.registry import SnippetRegistry

    reg = SnippetRegistry()

    class ConcreteIncludeWhatIf(IncBaseWhatIf):
        def filter_trades(self, trades: Sequence[IncRecord]) -> list[IncRecord]:
            return list(trades)

    mod_inc = types.ModuleType("custom_inc_mod")
    mod_inc.ConcreteIncludeWhatIf = ConcreteIncludeWhatIf  # type: ignore[attr-defined]
    ConcreteIncludeWhatIf.__module__ = "custom_inc_mod"
    res_inc = reg.register(Path("app/include/what_if/inc.py"), mod_inc)
    assert "ConcreteIncludeWhatIf" in res_inc

    class ConcreteExtendWhatIf(ExtBaseWhatIf):
        def filter_trades(self, trades: Sequence[ExtRecord]) -> list[ExtRecord]:
            return list(trades)

    mod_ext = types.ModuleType("custom_ext_mod")
    mod_ext.ConcreteExtendWhatIf = ConcreteExtendWhatIf  # type: ignore[attr-defined]
    ConcreteExtendWhatIf.__module__ = "custom_ext_mod"
    res_ext = reg.register(Path("app/include/what_if/ext.py"), mod_ext)
    assert "ConcreteExtendWhatIf" in res_ext

    class UnrelatedClass:
        pass

    mod_unrelated = types.ModuleType("custom_unrelated_mod")
    mod_unrelated.UnrelatedClass = UnrelatedClass  # type: ignore[attr-defined]
    UnrelatedClass.__module__ = "custom_unrelated_mod"
    with pytest.raises(CodeEditorError, match="must implement BaseWhatIf"):
        reg.register(Path("app/include/what_if/unrelated.py"), mod_unrelated)

    class AbstractWhatIf(IncBaseWhatIf):
        pass

    mod_abstract = types.ModuleType("custom_abstract_mod")
    mod_abstract.AbstractWhatIf = AbstractWhatIf  # type: ignore[attr-defined]
    AbstractWhatIf.__module__ = "custom_abstract_mod"
    with pytest.raises(CodeEditorError, match="must implement BaseWhatIf"):
        reg.register(Path("app/include/what_if/abstract.py"), mod_abstract)

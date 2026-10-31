"""End-to-end Gate G10 acceptance tests for AlgoWizard and platform descriptors."""

from __future__ import annotations

from app.core.wizard.template_helpers import (
    format_class_identifier,
    format_parameter_value,
    format_variable_value,
    sanitize_identifier,
)
from app.core.wizard.transform import NormalizedParam, NormalizedVar
from app.extend.code.easylanguage.descriptor import (
    EASYLANGUAGE_DESCRIPTOR,
    render_easylanguage,
)
from app.extend.code.jforex.descriptor import JFOREX_DESCRIPTOR, render_jforex
from app.extend.code.mql4.descriptor import MQL4_DESCRIPTOR, render_mql4
from app.extend.code.mql5.descriptor import MQL5_DESCRIPTOR, render_mql5
from app.extend.code.ninjatrader.descriptor import (
    NINJATRADER_DESCRIPTOR,
    render_ninjatrader,
)
from app.extend.code.pseudo_code.descriptor import (
    PSEUDO_CODE_DESCRIPTOR,
    render_pseudo_code,
)
from app.workspace.algo_wizard import (
    AddStrategyRequest,
    CheckResourcesRequest,
    CloudExportService,
    CloudImportRequest,
    ExportStrategyRequest,
    ExportTargetPlatform,
    GetCatalogueRequest,
    ListWizardExamplesRequest,
    LoadStrategyFileRequest,
    LoadWizardExampleRequest,
    NegateConditionRequest,
    RemoveStrategyRequest,
    SaveStrategyFileRequest,
    SaveToRetesterRequest,
    StartStrategyRequest,
    StopStrategyRequest,
    StrategyCompiler,
    StrategyDocumentService,
    StrategyValidator,
    VisualBlockService,
    WizardBacktestRequest,
    WizardBarInput,
    WizardBlockLibrary,
    WizardCatalogueService,
    WizardService,
)


def test_template_helpers_and_six_platform_descriptors() -> None:
    """Verify template_helpers and all 6 app.extend.code.* descriptors."""
    assert sanitize_identifier("123 Strategy/Name") == "s_123_Strategy_Name"
    assert sanitize_identifier("///", fallback="default_strat") == "default_strat"
    assert format_class_identifier("ema_crossover_v1") == "EmaCrossoverV1"

    bool_param = NormalizedParam(
        name="use_filter",
        type_name="bool",
        type_mql="bool",
        type_cs="bool",
        type_py="bool",
        value=True,
    )
    bool_var = NormalizedVar(
        name="in_session",
        type_name="bool",
        type_mql="bool",
        type_py="bool",
        value=False,
    )
    assert format_parameter_value(bool_param) == "true"
    assert format_variable_value(bool_var) == "false"

    descriptors = (
        (EASYLANGUAGE_DESCRIPTOR, "easylanguage", ".eld"),
        (JFOREX_DESCRIPTOR, "jforex", ".java"),
        (MQL4_DESCRIPTOR, "mql4", ".mq4"),
        (MQL5_DESCRIPTOR, "mql5", ".mq5"),
        (NINJATRADER_DESCRIPTOR, "ninjatrader", ".cs"),
        (PSEUDO_CODE_DESCRIPTOR, "pseudo_code", ".txt"),
    )
    for spec, expected_id, expected_ext in descriptors:
        assert spec.platform_id == expected_id
        assert spec.extension == expected_ext
        assert spec.supports_stop_loss is True
        assert spec.supports_take_profit is True

    wizard = WizardService()
    example_doc = wizard.load_example(
        LoadWizardExampleRequest(example_id="ema_crossover")
    ).data.document
    compiler = StrategyCompiler()
    normalized = compiler.compile_to_normalized(example_doc)

    el_code = render_easylanguage(normalized)
    assert "[LegacyColorValue = TRUE];" in el_code

    jf_code = render_jforex(normalized)
    assert "implements IStrategy" in jf_code

    mql4_code = render_mql4(normalized)
    assert "#property strict" in mql4_code

    mql5_code = render_mql5(normalized)
    assert "CTrade trade;" in mql5_code

    nt_code = render_ninjatrader(normalized)
    assert "namespace NinjaTrader.NinjaScript.Strategies" in nt_code

    pseudo_code = render_pseudo_code(
        normalized,
        display_name=example_doc.strategy.name,
        symbols=example_doc.strategy.universe.symbols,
        primary_timeframe=example_doc.strategy.timeframe.primary,
    )
    assert "STRATEGY: EMA Crossover" in pseudo_code


def test_end_to_end_workspace_qualification_pipeline() -> None:
    """Verify full BlockRegistry -> HSL -> Validator -> Runtime -> Export pipeline."""
    library = WizardBlockLibrary()
    validator = StrategyValidator(library=library)
    compiler = StrategyCompiler(library=library, validator=validator)
    catalogue_service = WizardCatalogueService(library=library)
    strategy_service = StrategyDocumentService(
        validator=validator,
        compiler=compiler,
    )
    visual_service = VisualBlockService(
        library=library,
        validator=validator,
        compiler=compiler,
    )
    wizard_service = WizardService(
        library=library,
        validator=validator,
        compiler=compiler,
        strategy_service=strategy_service,
    )
    cloud_service = CloudExportService(
        library=library,
        validator=validator,
        compiler=compiler,
        wizard_service=wizard_service,
        strategy_service=strategy_service,
    )

    # 1. Catalogue projection from BlockRegistry
    catalogue = catalogue_service.get_all(GetCatalogueRequest()).data
    assert any(b.semantic_id == "indicator.rsi" for b in catalogue.blocks)

    # 2. Load built-in canonical HSL example
    examples = wizard_service.list_examples(ListWizardExamplesRequest()).data
    assert len(examples) >= 4
    loaded_example = wizard_service.load_example(
        LoadWizardExampleRequest(example_id="rsi_mean_reversion")
    ).data
    hsl_doc = loaded_example.document

    # 3. Validate, negate condition, check resources, and run wizard backtest
    validation = validator.validate(hsl_doc)
    assert validation.valid is True

    negated = visual_service.negate_condition(
        NegateConditionRequest(condition=hsl_doc.strategy.rules[0].when)
    ).data
    assert negated.type in ("comparison", "not", "logical")

    resources = visual_service.check_resources(
        CheckResourcesRequest(
            document=hsl_doc,
            available_symbols=("EURUSD",),
            available_timeframes=("H1", "D1"),
        )
    ).data
    assert resources.ready is True

    bars = tuple(
        WizardBarInput(
            time=1700000000 + (hour * 3600),
            open=1.1000 - (hour * 0.0010),
            high=1.1010 - (hour * 0.0010),
            low=1.0990 - (hour * 0.0010),
            close=1.0995 - (hour * 0.0010),
            volume=1000.0,
        )
        for hour in range(25)
    )
    bt_result = visual_service.run_backtest(
        WizardBacktestRequest(document=hsl_doc, bars=bars)
    ).data
    assert bt_result.status == "COMPLETED"
    assert bt_result.bars_evaluated == 25

    # 4. Save file, load file, and handoff to Retester
    saved_file = wizard_service.save_file(
        SaveStrategyFileRequest(filename="rsi_reversion.json", document=hsl_doc)
    ).data
    reloaded_doc = wizard_service.load_file(
        LoadStrategyFileRequest(file_id=saved_file.file_id)
    ).data
    assert reloaded_doc.strategy.id == hsl_doc.strategy.id

    handoff = wizard_service.save_to_retester(
        SaveToRetesterRequest(document=hsl_doc)
    ).data
    assert handoff.document_hash == saved_file.document_hash

    # 5. Strategy lifecycle: add -> start -> stop -> remove
    added = strategy_service.add_strategy(AddStrategyRequest(document=hsl_doc)).data
    assert added.status == "IDLE"
    started = strategy_service.start_strategy(
        StartStrategyRequest(strategy_id=added.strategy_id)
    ).data
    assert started.status == "RUNNING"
    stopped = strategy_service.stop_strategy(
        StopStrategyRequest(strategy_id=added.strategy_id)
    ).data
    assert stopped.status == "STOPPED"

    # 6. Cloud import from file and export across all 8 target platforms
    imported = cloud_service.import_strategy(
        CloudImportRequest(source="file", file_id=saved_file.file_id)
    ).data
    assert imported.validation.valid is True

    all_platforms: tuple[ExportTargetPlatform, ...] = (
        "python",
        "mql4",
        "mql5",
        "easylanguage",
        "ninjatrader",
        "jforex",
        "pseudo_code",
        "hsl_json",
    )
    for platform in all_platforms:
        exported = cloud_service.export_strategy(
            ExportStrategyRequest(
                document=imported.document,
                target_platform=platform,
            )
        ).data
        assert exported.target_platform == platform
        assert len(exported.content.strip()) > 0
        assert len(exported.sha256) == 64

    removed = strategy_service.remove_strategy(
        RemoveStrategyRequest(strategy_id=added.strategy_id)
    ).data
    assert removed.removed is True

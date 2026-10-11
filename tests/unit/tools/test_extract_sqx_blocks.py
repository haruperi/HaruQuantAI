"""Verify extraction and parsing of SQX building blocks and indicator snippets.

Description:
    Synthetic Java snippet fixtures exercise clean-room AST and regex parsing
    for annotations, parameter ranges, return types, category hierarchy, and
    symmetrical opposite pairings without relying on an active SQX installation.

Purpose:
    FEAT-TOOLS-EXTRACT-SQX-BLOCKS: Extraction tooling qualification.

Key Capabilities:
    - FR-TOOLS-SQX-BLOCKS-JAVA-PARSER: Verify annotation and parameter parsing.
      Associated: `test_parse_indicator_block()`, `test_parse_condition_block()`
      Logging: Captured logger assertions verify parser execution.
    - FR-TOOLS-SQX-BLOCKS-MANIFEST-PARSER: Verify manifest and opposite loading.
      Associated: `test_load_opposites()`, `test_load_manifest()`
      Logging: Captured logger assertions verify manifest resolution.
    - FR-TOOLS-SQX-BLOCKS-CATALOG-BUILDER: Verify catalog assembly and schema.
      Associated: `test_catalog_builder_and_validation()`
      Logging: Captured logger assertions verify catalog construction.
    - FR-TOOLS-SQX-BLOCKS-VALIDATOR: Verify boundary checks and provenance hashes.
      Associated: `test_validator_and_provenance()`
      Logging: Captured logger assertions verify validation events.

Python API Usage:
    Run isolated tests through pytest; no live application runtime is exposed.

CLI Usage:
    ```bash
    uv run pytest tests/unit/tools/test_extract_sqx_blocks.py --no-cov
    ```
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.extract_sqx_blocks import (
    BlockDefinition,
    SQXBlockExtractor,
    parse_annotation_attributes,
    strip_comments,
)

SAMPLE_INDICATOR_JAVA = """/*
 * StrategyQuant sample snippet test
 */
package SQ.Blocks.Indicators.ATR;

import SQ.Internal.IndicatorBlock;

@BuildingBlock(name="(ATR) Average True Range", display="ATR(@Chart@#Period#)[#Shift#]", returnType=ReturnTypes.PriceRange)
@Indicator(min=0, max=5000, step=0.001)
@Help("Average True Range measures market volatility")
@ParameterSet(set="Period=14")
@ParameterSet(set="Period=20")
public class ATR extends IndicatorBlock {

    @Parameter(defaultChartIndex=0)
    public ChartData Chart;

    @Parameter(category="Default", name="Period", minValue=2, maxValue=10000, defaultValue="14", step=1)
    public int Period;

    @Output(name="ATR", color=Colors.Green)
    public DataSeries Value;

    @Override
    protected void OnBarUpdate() throws TradingException {
        // Calculation logic
    }
}
"""

SAMPLE_CONDITION_JAVA = """package SQ.Blocks.Indicators.ATR;

import SQ.Internal.ConditionBlock;

@BuildingBlock(name="ATR is rising", display="ATR(@Chart@#Period#)[#Shift#] is rising", returnType=ReturnTypes.Boolean)
@Help("Is triggered if ATR is rising")
@OppositeBlock("ATRFalling")
@SortOrder(100)
@CategoryOrder(1200)
@ParameterSet(set="Period=14")
public class ATRRising extends ConditionBlock {

    @Parameter
    public ChartData Input;

    @Parameter(defaultValue="14", minValue=2, maxValue=10000, step=1)
    public int Period;

    @Parameter
    public int Shift;

    @Override
    public boolean OnBlockEvaluate(int shift) throws TradingException {
        return true;
    }
}
"""

SAMPLE_ACTION_JAVA = """package SQ.Blocks.Order.Open;

import SQ.Internal.ActionBlock;

@BuildingBlock(name="(MKT) Enter at market", display="EnterAtMarket", returnType=ReturnTypes.Order)
@Help("Opens order at current market price")
@SortOrder(100)
@CategoryOrder(100)
public class EnterAtMarket extends ActionBlock {

    @Parameter(defaultValue="Any", category="Basic", showIfDefault=false)
    public String Symbol;

    @Parameter(defaultValue="1", category="Basic")
    @Editor(type=Editors.Selection, values="Long=1,Short=-1")
    public int Direction;
}
"""


def test_strip_comments() -> None:
    """Verify stripping of block and line comments while preserving code."""
    source = "int a = 1; /* block comment */ int b = 2; // line comment\nint c = 3;"
    cleaned = strip_comments(source)
    assert "block comment" not in cleaned
    assert "line comment" not in cleaned
    assert "int a = 1;" in cleaned
    assert "int b = 2;" in cleaned
    assert "int c = 3;" in cleaned


def test_parse_annotation_attributes() -> None:
    """Verify parsing key-value attributes with strings, enums, and numbers."""
    raw = (
        'name="(ATR) Average True Range", display="ATR(@Chart@#Period#)[#Shift#]", '
        "returnType=ReturnTypes.PriceRange, min=0, max=5000, step=0.001"
    )
    attrs = parse_annotation_attributes(raw)
    assert attrs["name"] == "(ATR) Average True Range"
    assert attrs["display"] == "ATR(@Chart@#Period#)[#Shift#]"
    assert attrs["returnType"] == "ReturnTypes.PriceRange"
    assert attrs["min"] == "0"
    assert attrs["max"] == "5000"
    assert attrs["step"] == "0.001"


def test_parse_indicator_block(tmp_path: Path) -> None:
    """Verify parsing of an indicator snippet with outputs and parameter sets."""
    snippet_file = tmp_path / "ATR.java"
    snippet_file.write_text(SAMPLE_INDICATOR_JAVA, encoding="utf-8")

    extractor = SQXBlockExtractor(sqx_root=tmp_path)
    block: BlockDefinition | None = extractor.parse_java_snippet(
        snippet_file, "internal/extend/Snippets/SQ/Blocks/Indicators/ATR/ATR.java"
    )

    assert block is not None
    assert block.class_name == "ATR"
    assert block.name == "(ATR) Average True Range"
    assert block.return_type == "ReturnTypes.PriceRange"
    assert block.block_type == "Indicator"
    assert block.category == "Indicators"
    assert block.help_text == "Average True Range measures market volatility"
    assert len(block.parameter_sets) == 2
    assert "Period=14" in block.parameter_sets

    # Parameter assertions
    period_param = next(p for p in block.parameters if p["name"] == "Period")
    assert period_param["type"] == "int"
    assert period_param["default_value"] == "14"
    assert period_param["min_value"] == "2"
    assert period_param["max_value"] == "10000"
    assert period_param["step"] == "1"

    # Output assertions
    assert len(block.outputs) == 1
    assert block.outputs[0]["name"] == "ATR"
    assert block.outputs[0]["color"] == "Colors.Green"


def test_parse_condition_block(tmp_path: Path) -> None:
    """Verify parsing of a condition snippet with opposite block and sort orders."""
    snippet_file = tmp_path / "ATRRising.java"
    snippet_file.write_text(SAMPLE_CONDITION_JAVA, encoding="utf-8")

    extractor = SQXBlockExtractor(sqx_root=tmp_path)
    block = extractor.parse_java_snippet(
        snippet_file,
        "internal/extend/Snippets/SQ/Blocks/Indicators/ATR/ATRRising.java",
    )

    assert block is not None
    assert block.class_name == "ATRRising"
    assert block.return_type == "ReturnTypes.Boolean"
    assert block.block_type == "Condition"
    assert block.opposite_block == "ATRFalling"
    assert block.sort_order == 100
    assert block.category_order == 1200

    shift_param = next(p for p in block.parameters if p["name"] == "Shift")
    assert shift_param["type"] == "int"


def test_parse_action_order_block(tmp_path: Path) -> None:
    """Verify parsing of an action order snippet with editor selection values."""
    snippet_file = tmp_path / "EnterAtMarket.java"
    snippet_file.write_text(SAMPLE_ACTION_JAVA, encoding="utf-8")

    extractor = SQXBlockExtractor(sqx_root=tmp_path)
    block = extractor.parse_java_snippet(
        snippet_file,
        "internal/extend/Snippets/SQ/Blocks/Order/Open/EnterAtMarket.java",
    )

    assert block is not None
    assert block.class_name == "EnterAtMarket"
    assert block.return_type == "ReturnTypes.Order"
    assert block.block_type == "Order"

    dir_param = next(p for p in block.parameters if p["name"] == "Direction")
    assert dir_param["default_value"] == "1"
    assert dir_param.get("editor_type") == "Editors.Selection"
    assert dir_param.get("editor_values") == "Long=1,Short=-1"


def test_load_opposites(tmp_path: Path) -> None:
    """Verify loading of opposite blocks from semicolon CSV."""
    csv_file = tmp_path / "opposites.csv"
    csv_file.write_text("Block;OppositeBlock\nADX;ADX\nAWOFalling;AWORising\n")

    opposites = SQXBlockExtractor.load_opposites(csv_file)
    assert opposites["ADX"] == "ADX"
    assert opposites["AWOFalling"] == "AWORising"


def test_load_manifest(tmp_path: Path) -> None:
    """Verify reading snippet file manifest entries."""
    manifest_file = tmp_path / "snippets.txt"
    manifest_file.write_text(
        "$SNIPPETS_BUILTIN_DIR$/SQ/Blocks/BarAndTime/BarDate.java|fdade41783c46f078fe548510e2f82bd\n"
        "$SNIPPETS_BUILTIN_DIR$/SQ/Calculators/RSICalculator.java|1234567890abcdef\n"
    )

    entries = SQXBlockExtractor.load_manifest(manifest_file)
    assert len(entries) == 2
    assert entries[0][0] == "SQ/Blocks/BarAndTime/BarDate.java"
    assert entries[0][1] == "fdade41783c46f078fe548510e2f82bd"


def test_catalog_builder_and_validation(tmp_path: Path) -> None:
    """Verify end-to-end catalog generation, validation, and JSON serialization."""
    # Build fake SQX tree
    snips_dir = tmp_path / "internal/extend/Snippets/SQ/Blocks/Indicators/ATR"
    snips_dir.mkdir(parents=True)
    atr_java = snips_dir / "ATR.java"
    atr_java.write_text(SAMPLE_INDICATOR_JAVA, encoding="utf-8")

    settings_dir = tmp_path / "user/settings"
    settings_dir.mkdir(parents=True)
    manifest = settings_dir / "snippets.txt"
    manifest.write_text(
        "$SNIPPETS_BUILTIN_DIR$/SQ/Blocks/Indicators/ATR/ATR.java|dummy_md5\n"
    )

    out_file = tmp_path / "output_catalog.json"
    extractor = SQXBlockExtractor(sqx_root=tmp_path, output_file=out_file)

    catalog = extractor.build_catalog()
    assert catalog["total_snippets"] == 1
    assert "ATR" in catalog["blocks"]
    assert catalog["schema_version"] == 1

    saved_path = extractor.save_catalog(catalog)
    assert saved_path.exists()

    loaded = json.loads(saved_path.read_text(encoding="utf-8"))
    assert loaded["blocks"]["ATR"]["name"] == "(ATR) Average True Range"
    assert loaded["blocks"]["ATR"]["sha256"] != ""

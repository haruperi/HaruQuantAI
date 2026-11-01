"""Donor XML serialization and reference CSV parsing for indicator test suite.

Description:
    Provides XML parser/serializer for StrategyQuant IndicatorTester XML configuration
    files, parameter string decoders, and 7-column semicolon CSV reference data loaders.
Purpose:
    FEAT-CODE-EDITOR-INDICATOR-SUITE: Batch indicator suite I/O contracts.
Key Capabilities:
    - FR-code-editor-suite-io: Serialize and deserialize IndicatorTester XML configs and
      parse multi-format reference time series CSV files safely.
Python API Usage:
    from app.workspace.code_editor._indicator_suite_io import (
        suite_config_to_xml,
        suite_config_from_xml,
        parse_reference_csv,
    )
CLI Usage:
    uv run pytest tests/workspace/code_editor/test_indicator_suite.py --no-cov
"""

from __future__ import annotations

import logging
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core.lib.errors import JSONValue
from app.extend.blocks.indicators.base import BaseIndicator
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._indicator_data import indicator_defaults
from app.workspace.code_editor.command_models import (
    SuiteConfigModel,
    SuiteTestCaseModel,
)

logger = logging.getLogger(__name__)

SUPPORTED_SUITE_ENGINES: tuple[str, ...] = (
    "MetaTrader4",
    "MetaTrader5",
    "TradeStation",
    "MultiCharts",
    "JForex",
    "HaruQuantAI",
)
MAX_INVALID_LINES = 50


@dataclass(frozen=True, slots=True)
class ReferenceBarRow:
    """Parsed 7-column semicolon-separated reference bar and expected indicator value."""

    raw_time: str
    timestamp: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    reference_value: float


def format_default_parameters(parameters: dict[str, JSONValue]) -> str:
    """Format default parameter dictionary as a donor-style comma-separated string."""
    if not parameters:
        return ""
    parts: list[str] = []
    for value in parameters.values():
        if isinstance(value, bool):
            parts.append("true" if value else "false")
        elif isinstance(value, (int, float, str)):
            parts.append(str(value))
    return ",".join(parts)


def _coerce_scalar(raw_token: str, default_val: JSONValue) -> JSONValue:
    """Coerce a string parameter token to match the canonical field default type."""
    token = raw_token.strip()
    if isinstance(default_val, bool):
        lowered = token.lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
        raise CodeEditorError(f"Invalid boolean parameter value: {token}")
    if isinstance(default_val, int) and not isinstance(default_val, bool):
        try:
            return int(float(token)) if "." in token else int(token)
        except ValueError:
            raise CodeEditorError(f"Invalid integer parameter value: {token}") from None
    if isinstance(default_val, float):
        try:
            parsed = float(token)
        except ValueError:
            raise CodeEditorError(f"Invalid float parameter value: {token}") from None
        if not math.isfinite(parsed):
            raise CodeEditorError("Indicator parameter must be finite")
        return parsed
    try:
        if token.lower() in {"true", "false"}:
            return token.lower() == "true"
        if "." in token:
            parsed_f = float(token)
            if math.isfinite(parsed_f):
                return parsed_f
        return int(token)
    except ValueError:
        return token


def parse_suite_parameters(
    cls: type[BaseIndicator], raw_parameters: str
) -> dict[str, JSONValue]:
    """Parse donor comma-separated positional or key=value parameter strings."""
    defaults = indicator_defaults(cls)
    cleaned = raw_parameters.strip()
    if not cleaned:
        return defaults
    tokens = [part.strip() for part in cleaned.split(",") if part.strip()]
    field_names = list(defaults.keys())
    effective = dict(defaults)
    positional_idx = 0
    for token in tokens:
        if "=" in token:
            key, raw_val = token.split("=", 1)
            k = key.strip()
            if k not in effective:
                raise CodeEditorError(f"Unknown indicator parameter '{k}'")
            effective[k] = _coerce_scalar(raw_val, effective[k])
        else:
            if positional_idx >= len(field_names):
                raise CodeEditorError(
                    f"Too many positional parameters for {cls.__name__}"
                )
            field_name = field_names[positional_idx]
            effective[field_name] = _coerce_scalar(token, effective[field_name])
            positional_idx += 1
    return effective


def default_reference_filename(indicator_label: str, parameters: str) -> str:
    """Build deterministic reference CSV filename matching donor conventions."""
    safe_indy = indicator_label.rsplit("::", maxsplit=1)[-1].replace("/", "_")
    cleaned_params = "_".join(
        part.strip().replace("=", "_") for part in parameters.split(",") if part.strip()
    )
    if cleaned_params:
        return f"{safe_indy}_{cleaned_params}.csv"
    return f"{safe_indy}.csv"


def suite_config_to_xml(config: SuiteConfigModel) -> str:
    """Serialize a SuiteConfigModel to donor-compatible <IndicatorTester> XML."""
    root = ET.Element("IndicatorTester")
    engine_el = ET.SubElement(root, "Engine")
    engine_el.text = config.engine
    bars_el = ET.SubElement(root, "BarsToReserve")
    bars_el.text = str(config.bars_to_reserve)
    tests_el = ET.SubElement(root, "Tests")
    for test in config.tests:
        attrs = {
            "use": "true" if test.use else "false",
            "indicator": test.indicator,
            "parameters": test.parameters,
            "decimals": str(test.decimals),
            "result": test.result,
            "shift": str(test.shift),
            "fileName": test.file_name,
            "exists": "yes" if test.exists else "no",
        }
        test_el = ET.SubElement(tests_el, "Test", attrib=attrs)
        if test.errors or test.show_grid:
            errors_el = ET.SubElement(
                test_el,
                "Errors",
                attrib={"showGrid": "true" if test.show_grid else "false"},
            )
            for err_line in test.errors:
                err_el = ET.SubElement(errors_el, "Error")
                err_el.text = err_line
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode") + "\n"


def suite_config_from_xml(
    xml_text: str, tests_dir: Path | None = None
) -> SuiteConfigModel:
    """Parse donor <IndicatorTester> XML into a validated SuiteConfigModel."""
    cleaned = xml_text.strip()
    if not cleaned:
        raise CodeEditorError("Suite XML configuration must not be empty")
    if "<!DOCTYPE" in cleaned.upper() or "<!ENTITY" in cleaned.upper():
        raise CodeEditorError("XML DTD and entity declarations are forbidden")
    try:
        root = ET.fromstring(cleaned)  # noqa: S314
    except ET.ParseError as exc:
        raise CodeEditorError("Invalid IndicatorTester XML syntax") from exc
    if root.tag != "IndicatorTester":
        raise CodeEditorError("Root XML element must be <IndicatorTester>")
    engine = (root.findtext("Engine") or "MetaTrader4").strip()
    if engine not in SUPPORTED_SUITE_ENGINES:
        raise CodeEditorError(f"Unsupported indicator suite engine: {engine}")
    bars_raw = (root.findtext("BarsToReserve") or "300").strip()
    try:
        bars_to_reserve = int(bars_raw)
    except ValueError:
        raise CodeEditorError("BarsToReserve must be an integer") from None
    if not 0 <= bars_to_reserve <= 10000:
        raise CodeEditorError("BarsToReserve must be between 0 and 10000")

    tests: list[SuiteTestCaseModel] = []
    tests_node = root.find("Tests")
    if tests_node is not None:
        for idx, node in enumerate(tests_node.findall("Test")):
            indicator = node.attrib.get("indicator", "").strip()
            if not indicator:
                raise CodeEditorError("Each <Test> element requires an indicator name")
            params_str = node.attrib.get("parameters", "").strip()
            try:
                decimals = int(node.attrib.get("decimals", "6"))
                shift = int(node.attrib.get("shift", "0"))
            except ValueError:
                raise CodeEditorError(
                    "Test decimals and shift attributes must be integers"
                ) from None
            file_name = node.attrib.get("fileName", "").strip() or (
                default_reference_filename(indicator, params_str)
            )
            exists_attr = node.attrib.get("exists", "no").strip().lower() in {
                "yes",
                "true",
                "1",
            }
            if tests_dir is not None:
                exists_attr = _resolve_reference_file(
                    tests_dir, engine, file_name
                ).is_file()
            errors_node = node.find("Errors")
            show_grid = False
            errors: list[str] = []
            if errors_node is not None:
                show_grid = (
                    errors_node.attrib.get("showGrid", "false").lower() == "true"
                )
                errors = [
                    (err.text or "").strip()
                    for err in errors_node.findall("Error")
                    if (err.text or "").strip()
                ]
            tests.append(
                SuiteTestCaseModel(
                    test_id=node.attrib.get("id", f"test-{idx + 1}"),
                    use=node.attrib.get("use", "true").lower() == "true",
                    indicator=indicator,
                    parameters=params_str,
                    decimals=decimals,
                    result=node.attrib.get("result", ""),
                    shift=shift,
                    file_name=file_name,
                    exists=exists_attr,
                    show_grid=show_grid,
                    errors=errors,
                )
            )
    return SuiteConfigModel(engine=engine, bars_to_reserve=bars_to_reserve, tests=tests)


def _resolve_reference_file(tests_dir: Path, engine: str, file_name: str) -> Path:
    """Resolve a reference CSV file path safely inside the indicator tests root."""
    if not file_name or "/" in file_name or "\\" in file_name or ".." in file_name:
        raise CodeEditorError("Reference fileName must be a simple file name")
    base = tests_dir.resolve()
    engine_candidate = (base / engine / file_name).resolve()
    if not engine_candidate.is_relative_to(base):
        raise CodeEditorError("Reference file path escapes indicator tests directory")
    if engine_candidate.is_file():
        return engine_candidate
    direct_candidate = (base / file_name).resolve()
    if not direct_candidate.is_relative_to(base):
        raise CodeEditorError("Reference file path escapes indicator tests directory")
    return direct_candidate if direct_candidate.is_file() else engine_candidate


def _parse_reference_datetime(raw_time: str, fallback_index: int) -> int:
    """Parse donor reference timestamp formats into UTC epoch seconds."""
    text = raw_time.strip()
    for fmt in (
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(text, fmt).replace(tzinfo=UTC)
            return int(dt.timestamp())
        except ValueError:
            continue
    raise ValueError(
        f"Unrecognized reference timestamp: {raw_time} at {fallback_index}"
    )


def parse_reference_csv(
    csv_path: Path,
) -> tuple[list[ReferenceBarRow], list[str]]:
    """Parse semicolon-delimited 7-column donor reference CSV with invalid line cap."""
    try:
        lines = csv_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CodeEditorError("Reference CSV file could not be read") from exc
    valid_rows: list[ReferenceBarRow] = []
    invalid_lines: list[str] = []
    for line_no, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [p.strip() for p in stripped.split(";")]
        if line_no == 1 and parts and parts[0].lower() in {"date", "datetime", "time"}:
            continue
        if len(parts) < 7:
            if len(invalid_lines) < MAX_INVALID_LINES:
                invalid_lines.append(
                    f"Line {line_no}: expected 7 semicolon columns, got {len(parts)}"
                )
            continue
        try:
            ts = _parse_reference_datetime(parts[0], line_no)
            open_p = float(parts[1])
            high_p = float(parts[2])
            low_p = float(parts[3])
            close_p = float(parts[4])
            vol = float(parts[5])
            ref_val = float(parts[6])
            if not all(
                math.isfinite(v) for v in (open_p, high_p, low_p, close_p, vol, ref_val)
            ):
                raise ValueError("Non-finite numeric value in reference row")
            valid_rows.append(
                ReferenceBarRow(
                    raw_time=parts[0],
                    timestamp=ts,
                    open_price=open_p,
                    high_price=high_p,
                    low_price=low_p,
                    close_price=close_p,
                    volume=vol,
                    reference_value=ref_val,
                )
            )
        except ValueError as exc:
            if len(invalid_lines) < MAX_INVALID_LINES:
                invalid_lines.append(f"Line {line_no}: {exc}")
    return valid_rows, invalid_lines

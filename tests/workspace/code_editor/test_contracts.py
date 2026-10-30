"""Compatibility and rejection cases for editor domain records."""

import math

import pytest
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor import http, requests, results
from app.workspace.code_editor.errors import CodeEditorError
from pydantic import TypeAdapter, ValidationError


@pytest.mark.parametrize("params", [None, {}, {"period": 20}, {"fast_period": 12}])
def test_indicator_request_preserves_parameters_and_defaults(params):
    request = requests.IndicatorTestRunRequest(indicator_name="MACD", params=params)
    assert request.params == params
    assert (request.symbol, request.timeframe) == ("EURUSD", "H1")
    assert (request.bars_to_reserve, request.bar_count) == (50, 150)
    assert (
        requests.IndicatorTestRunRequest(
            indicator_name="SMA", bars_to_reserve=0
        ).bars_to_reserve
        == 0
    )
    assert requests.IndicatorTestRunRequest(indicator_name="SMA").params is None


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("field", ["params", "reference_values"])
def test_nonfinite_indicator_inputs_are_rejected(value, field):
    payload = {
        "indicator_name": "SMA",
        field: {"nested": [value]} if field == "params" else [value],
    }
    with pytest.raises(ValidationError):
        requests.IndicatorTestRunRequest.model_validate(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"files": [{}]},
        {"files": [{"file_path": "x.py"}]},
        {"tabs": [{"file_path": "x.py"}]},
    ],
)
def test_nested_buffers_require_content(payload):
    model = requests.SaveAllRequest if "files" in payload else requests.SessionRequest
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_empty_buffers_optional_lists_and_extra_session_fields_remain_compatible():
    assert requests.SaveAllRequest().files is None
    assert requests.SaveAllRequest(files=[]).files == []
    buffer = requests.SaveFileRequest(file_path="x.py", content="")
    assert requests.SaveAllRequest(files=[buffer]).files[0].content == ""
    session = requests.SessionRequest.model_validate(
        {
            "tabs": [
                {
                    "file_path": "x.py",
                    "content": "",
                    "title": "x.py",
                    "is_dirty": True,
                    "cursor_position": {"line": 2, "column": 3},
                }
            ],
            "layout": {},
        }
    )
    assert session.tabs[0].model_dump() == {
        "file_path": "x.py",
        "content": "",
        "mode": "python",
    }
    assert requests.CompileRequest(file_path="x.py", content="").content == ""
    assert requests.CompileRequest(file_path="x.py").content is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("bars_to_reserve", -1),
        ("bars_to_reserve", 10001),
        ("bar_count", 0),
        ("bar_count", 10001),
    ],
)
def test_indicator_window_bounds(field, value):
    with pytest.raises(ValidationError):
        requests.IndicatorTestRunRequest.model_validate(
            {"indicator_name": "SMA", field: value}
        )


def test_existing_request_import_locations_remain_available():
    for name in http.__all__:
        if name != "router":
            assert getattr(http, name) is getattr(requests, name)


@pytest.mark.parametrize("rule", ["skip", "overwrite", "rename"])
def test_existing_package_conflict_rules(rule):
    request = requests.ImportPackRequest(
        archive_path="test.zip", resolution_rules={"a.py": rule}
    )
    assert request.resolution_rules == {"a.py": rule}


def test_invalid_package_rule_and_nonfinite_metadata_are_rejected():
    with pytest.raises(ValidationError):
        requests.ImportPackRequest(
            archive_path="test.zip", resolution_rules={"a.py": "unknown"}
        )
    with pytest.raises(ValidationError):
        requests.ExportPackRequest(
            file_paths=[], archive_path="test.zip", metadata={"nested": [math.nan]}
        )


@pytest.mark.parametrize(
    "record",
    [
        {"bar": 0, "time": 1, "calc": 2.0, "ref": 1.0, "diff": 1.0},
        {
            "bar": 0,
            "time": 1,
            "series": "value",
            "type": "NonFiniteValue",
            "message": "gap",
        },
        {"bar": 0, "type": "CodeEditorError", "message": "missing history"},
    ],
)
def test_diagnostic_variants_retain_exact_fields(record):
    assert (
        results.validate_result(TypeAdapter(results.IndicatorDiagnostic), record)
        == record
    )


def test_result_validation_does_not_add_optional_fields_or_drop_extras():
    record = {"status": "not_open", "active_file": None}
    assert (
        results.validate_result(TypeAdapter(results.CloseTabResult), record) == record
    )
    for malformed in [
        {**record, "surprise": True},
        {"status": "unknown", "active_file": None},
    ]:
        with pytest.raises(CodeEditorError) as rejected:
            results.validate_result(TypeAdapter(results.CloseTabResult), malformed)
        assert rejected.value.category is ErrorCode.INTERNAL


def test_error_message_constructor_is_compatible_and_categorized():
    error = CodeEditorError("Expected validation failure")
    assert str(error) == "Expected validation failure"
    assert error.code == "validation"
    assert error.details == {}

"""Unit tests for report generation, comparisons, and packaging tools in Analytics."""

from __future__ import annotations

from typing import Any

import pytest
from app.services.analytics.reports import (
    build_analytics_report,
    build_backtest_report,
    build_portfolio_analytics_report,
    calculate_prop_firm_compliance,
    calculate_statistical_validation,
    compare_analytics_reports,
    format_summary_as_rows,
    print_statistical_validation_report,
)
from app.utils.errors import ValidationError


@pytest.fixture
def valid_trading_result() -> dict[str, Any]:
    return {
        "schema_version": "1.3.1",
        "result_id": "bt_run_test",
        "phase": "backtest",
        "strategy_id": "strategy_test",
        "strategy_version": "v1",
        "account_base_currency": "USD",
        "trades": [
            {
                "trade_id": "t1",
                "open_time": "2026-01-01T00:00:00Z",
                "close_time": "2026-01-01T04:00:00Z",
                "direction": "long",
                "profit_loss": 100.0,
                "initial_risk": 50.0,
            }
        ],
        "equity_curve": [
            {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0},
            {"timestamp": "2026-01-01T04:00:00Z", "equity": 10100.0},
        ],
    }


def test_build_report_success(valid_trading_result):
    resp = build_analytics_report(valid_trading_result, request_id="req_test")
    assert resp["status"] == "success"
    data = resp["data"]
    assert data["report_status"] == "partial"  # because benchmark is skipped/missing
    assert data["strategy_id"] == "strategy_test"
    assert "trade_metrics" in data["sections"]
    assert "equity_metrics" in data["sections"]


def test_build_report_with_benchmark(valid_trading_result):
    valid_trading_result["benchmark_curve"] = [
        {"timestamp": "2026-01-01T00:00:00Z", "equity": 5000.0},
        {"timestamp": "2026-01-01T04:00:00Z", "equity": 5050.0},
    ]
    resp = build_analytics_report(valid_trading_result, request_id="req_test")
    assert resp["status"] == "success"
    data = resp["data"]
    assert data["report_status"] == "completed"
    assert data["sections"]["benchmark_metrics"]["status"] == "completed"


def test_build_report_validation_errors():
    # Invalid request_id
    with pytest.raises(ValidationError):
        build_analytics_report({}, request_id=" ")

    # Missing required fields
    resp = build_analytics_report(
        {"schema_version": "1.3.1", "result_id": "missing_fields"},
        request_id="req_test",
    )
    assert resp["status"] == "error"
    assert resp["error"]["code"] == "VALIDATION_FAILED"


def test_portfolio_report():
    port_result = {
        "portfolio_run_id": "port_run_1",
        "account_base_currency": "USD",
        "component_results": [],
    }
    resp = build_portfolio_analytics_report(port_result, request_id="req_test")
    assert resp["status"] == "success"
    assert resp["data"]["portfolio_run_id"] == "port_run_1"

    with pytest.raises(ValidationError):
        build_portfolio_analytics_report(None, request_id=" ")

    resp_err = build_portfolio_analytics_report(None, request_id="req_test")
    assert resp_err["status"] == "error"


def test_portfolio_report_fails_closed_without_fx_conversion():
    port_result = {
        "portfolio_run_id": "port_run_fx",
        "account_base_currency": "USD",
        "component_results": [
            {"strategy_id": "s1", "profit_currency": "USD"},
            {"strategy_id": "s2", "profit_currency": "EUR"},
        ],
    }

    resp = build_portfolio_analytics_report(port_result, request_id="req_test")

    assert resp["status"] == "error"
    assert resp["error"]["code"] == "VALIDATION_FAILED"


def test_compare_reports():
    ref = {"report_id": "ref_report"}
    cand = {"report_id": "cand_report"}
    resp = compare_analytics_reports(ref, cand, request_id="req_test")
    assert resp["status"] == "success"
    assert resp["data"]["reference_report_id"] == "ref_report"

    with pytest.raises(ValidationError):
        compare_analytics_reports(ref, cand, request_id=" ")

    resp_err = compare_analytics_reports(None, None, request_id="req_test")
    assert resp_err["status"] == "error"


def test_format_and_helpers(valid_trading_result):
    assert format_summary_as_rows({}) == []
    report_dict = build_backtest_report(valid_trading_result)
    assert report_dict["report_status"] == "partial"

    assert print_statistical_validation_report([0.01, -0.02]) == ""


def test_calculate_statistical_validation():
    # Success
    resp = calculate_statistical_validation(
        [0.01, -0.005, 0.012], request_id="req_test"
    )
    assert resp["status"] == "success"
    assert resp["data"]["mean"] > 0.0

    # Validation errors
    with pytest.raises(ValidationError):
        calculate_statistical_validation([], request_id=" ")

    resp_err = calculate_statistical_validation([], request_id="req_test")
    assert resp_err["status"] == "error"


def test_calculate_prop_firm_compliance():
    # Success
    resp = calculate_prop_firm_compliance({"report_id": "rep_1"}, request_id="req_test")
    assert resp["status"] == "success"
    assert resp["data"]["compliant"] is True

    # Validation errors
    with pytest.raises(ValidationError):
        calculate_prop_firm_compliance({}, request_id=" ")

    resp_none = calculate_prop_firm_compliance(None, request_id="req_test")
    assert resp_none["status"] == "success"


def test_report_serialization_and_hashing():
    from app.services.analytics.reports import (
        serialize_report,
        compute_report_hash,
        ReportFormat,
        HashPolicy,
    )
    report_dict = {
        "report_id": "rep_test_01",
        "report_status": "completed",
        "sections": {"trade_metrics": {"status": "completed"}},
        "metadata": {"created_at": "2026-01-01"},
    }

    # Serialization JSON
    ser_json = serialize_report(report_dict, ReportFormat.JSON)
    assert ser_json.format == ReportFormat.JSON
    assert "rep_test_01" in ser_json.content

    # Serialization Markdown
    ser_md = serialize_report(report_dict, ReportFormat.MARKDOWN)
    assert ser_md.format == ReportFormat.MARKDOWN
    assert "# Performance Report: rep_test_01" in ser_md.content

    # Hashing (Deterministic and excludes metadata)
    hash_sha = compute_report_hash(report_dict, HashPolicy.SHA256)
    hash_md5 = compute_report_hash(report_dict, HashPolicy.MD5)
    assert len(hash_sha) == 64
    assert len(hash_md5) == 32

    # Verify metadata exclusion: altering metadata does not change hash
    report_dict_alt = dict(report_dict)
    report_dict_alt["metadata"] = {"created_at": "2026-12-31", "request_id": "req_xyz"}
    assert compute_report_hash(report_dict_alt, HashPolicy.SHA256) == hash_sha


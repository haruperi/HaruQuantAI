"""Batch indicator suite, test distribution, and calibration verification tests."""

from __future__ import annotations

import hashlib
import time
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from app.core.host.resources import ResourceMonitor
from app.core.jobs.manager import JobManager
from app.include.blocks.price import BarPrice
from app.main import create_app
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._indicator_data import (
    calculate_indicator,
    output_series,
)
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.command_models import (
    CalibrationRequest,
    SuiteAddTestsRequest,
    SuiteConfigModel,
    SuiteCreateConfigRequest,
    SuiteLoadConfigRequest,
    SuiteStartRequest,
    SuiteTestCaseModel,
    TestDistributionRequest,
)
from app.workspace.code_editor.indicator_calibration import (
    IndicatorCalibrationService,
    beautify_calibration_range,
    parse_calibration_ranges_config,
)
from app.workspace.code_editor.indicator_suite import (
    IndicatorSuiteService,
    list_suite_indicators,
    parse_suite_parameters,
    resolve_suite_indicator,
    run_single_suite_test,
    suite_config_from_xml,
    suite_config_to_xml,
)
from app.workspace.code_editor.indicator_test_distribution import (
    IndicatorTestDistributionService,
)
from fastapi.testclient import TestClient


@pytest.fixture
def suite_env(isolated_editor, tmp_path: Path):
    manager = JobManager(
        max_workers=1,
        persistence=isolated_editor,
        resource_mgr=ResourceMonitor(scratch_root=tmp_path / "scratch"),
        min_available_ram_pct=0,
    )
    store = StateStore(isolated_editor)
    tests_dir = tmp_path / "indicator_tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    suite = IndicatorSuiteService(manager, store, tests_dir=tests_dir)
    dist = IndicatorTestDistributionService(manager, store, suite)
    yield suite, dist, store, tests_dir, manager
    manager.shutdown(wait=True, cancel_futures=True)


def _generate_exact_reference_csv(
    dest: Path,
    *,
    indicator_name: str = "ATR",
    params_str: str = "14",
    count: int = 40,
    shift: int = 0,
    corrupt_index: int | None = None,
    delta_at_end: float = 0.0,
) -> None:
    cls, out_name = resolve_suite_indicator(indicator_name)
    params = parse_suite_parameters(cls, params_str)
    rng = np.random.default_rng(42)
    closes = 1.1000 + np.cumsum(rng.normal(0.0, 0.001, count))
    opens = closes - 0.0002
    highs = closes + 0.0015
    lows = closes - 0.0015
    volumes = np.full(count, 1000.0)
    timestamps = [1704067200 + i * 3600 for i in range(count)]
    bars = BarPrice(
        open_data=opens,
        high_data=highs,
        low_data=lows,
        close_data=closes,
        volume_data=volumes,
    )
    series_map = output_series(
        calculate_indicator(cls, bars, params, timestamps), count
    )
    target = (
        series_map[out_name]
        if out_name and out_name in series_map
        else next(iter(series_map.values()))
    )
    lines: list[str] = []
    for i in range(count):
        if corrupt_index is not None and i == corrupt_index:
            lines.append("corrupted;line;with;too;few;cols")
            continue
        src_idx = max(0, i - shift)
        val = float(target[src_idx])
        if not np.isfinite(val):
            val = 0.0
        if i == count - 1:
            val += delta_at_end
        day = 1 + (i // 24)
        hour = i % 24
        dt_str = f"2024.01.{day:02d} {hour:02d}:00:00"
        lines.append(
            f"{dt_str};{opens[i]:.5f};{highs[i]:.5f};{lows[i]:.5f};"
            f"{closes[i]:.5f};{volumes[i]:.1f};{val:.8f}"
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_list_suite_indicators_expands_multi_output_buffers():
    options = list_suite_indicators()
    assert len(options) > 50
    names = {opt.indicator for opt in options}
    assert "ATR" in names
    assert any("." in opt.indicator for opt in options)


def test_suite_xml_roundtrip_and_duplicate_policy(suite_env):
    suite, _, _, tests_dir, _ = suite_env
    snap = suite.create_new_config(
        SuiteCreateConfigRequest(
            indicators=["ATR"],
            engine="MetaTrader4",
            bars_to_reserve=300,
        )
    )
    assert snap.config.engine == "MetaTrader4"
    assert snap.config.bars_to_reserve == 300
    assert len(snap.config.tests) == 1
    assert snap.config.tests[0].indicator == "ATR"
    assert "<Engine>MetaTrader4</Engine>" in snap.xml_content
    assert "<BarsToReserve>300</BarsToReserve>" in snap.xml_content

    with pytest.raises(CodeEditorError, match="Duplicate indicator test row"):
        suite.add_tests(
            SuiteAddTestsRequest(indicators=["ATR"], allow_duplicates=False)
        )

    added = suite.add_tests(
        SuiteAddTestsRequest(indicators=["ATR"], allow_duplicates=True)
    )
    assert len(added.config.tests) == 2

    parsed = suite_config_from_xml(added.xml_content, tests_dir=tests_dir)
    assert parsed.engine == "MetaTrader4"
    assert parsed.bars_to_reserve == 300
    assert len(parsed.tests) == 2

    with pytest.raises(CodeEditorError, match="DTD"):
        suite_config_from_xml("<!DOCTYPE foo><IndicatorTester></IndicatorTester>")


def test_reference_csv_comparator_passed_failed_skipped_and_shifts(tmp_path: Path):
    tests_dir = tmp_path / "refs"
    csv_pass = tests_dir / "MetaTrader4" / "ATR_14.csv"
    _generate_exact_reference_csv(
        csv_pass, indicator_name="ATR", params_str="14", count=40
    )

    row_pass = SuiteTestCaseModel(
        test_id="t1",
        indicator="ATR",
        parameters="14",
        decimals=6,
        shift=0,
        file_name="ATR_14.csv",
    )
    res_pass = run_single_suite_test(
        row_pass, engine="MetaTrader4", bars_to_reserve=20, tests_dir=tests_dir
    )
    assert res_pass.result == "Passed"
    assert res_pass.exists is True
    assert res_pass.errors == []

    csv_fail = tests_dir / "MetaTrader4" / "ATR_fail.csv"
    _generate_exact_reference_csv(
        csv_fail,
        indicator_name="ATR",
        params_str="14",
        count=40,
        delta_at_end=0.01,
    )
    row_fail = row_pass.model_copy(update={"file_name": "ATR_fail.csv"})
    res_fail = run_single_suite_test(
        row_fail, engine="MetaTrader4", bars_to_reserve=20, tests_dir=tests_dir
    )
    assert res_fail.result == "Failed - 1 differences"
    assert res_fail.show_grid is True
    assert len(res_fail.errors) == 1

    csv_shift = tests_dir / "MetaTrader4" / "ATR_shift.csv"
    _generate_exact_reference_csv(
        csv_shift,
        indicator_name="ATR",
        params_str="14",
        count=40,
        shift=2,
    )
    row_shift = row_pass.model_copy(update={"file_name": "ATR_shift.csv", "shift": 2})
    res_shift = run_single_suite_test(
        row_shift, engine="MetaTrader4", bars_to_reserve=20, tests_dir=tests_dir
    )
    assert res_shift.result == "Passed"

    csv_bad = tests_dir / "MetaTrader4" / "ATR_bad.csv"
    _generate_exact_reference_csv(
        csv_bad,
        indicator_name="ATR",
        params_str="14",
        count=40,
        corrupt_index=10,
    )
    row_bad = row_pass.model_copy(update={"file_name": "ATR_bad.csv"})
    res_bad = run_single_suite_test(
        row_bad, engine="MetaTrader4", bars_to_reserve=20, tests_dir=tests_dir
    )
    assert res_bad.result == "Skipped - File contains invalid lines (1)"

    row_missing = row_pass.model_copy(update={"file_name": "nonexistent.csv"})
    res_missing = run_single_suite_test(
        row_missing, engine="MetaTrader4", bars_to_reserve=20, tests_dir=tests_dir
    )
    assert res_missing.result == "Skipped - File not found."
    assert res_missing.exists is False


def test_suite_background_execution_and_stop(suite_env):
    suite, _, _, tests_dir, _ = suite_env
    _generate_exact_reference_csv(
        tests_dir / "MetaTrader4" / "ATR_14.csv",
        indicator_name="ATR",
        params_str="14",
        count=45,
    )
    cfg = SuiteConfigModel(
        engine="MetaTrader4",
        bars_to_reserve=20,
        tests=[
            SuiteTestCaseModel(
                test_id="t1",
                use=True,
                indicator="ATR",
                parameters="14",
                decimals=6,
                shift=0,
                file_name="ATR_14.csv",
            )
        ],
    )
    started = suite.start_testing(SuiteStartRequest(config=cfg))
    for _ in range(50):
        current = suite.get_snapshot(started.job_id)
        if current.status == "COMPLETED":
            break
        time.sleep(0.05)
    final = suite.get_snapshot(started.job_id)
    assert final.status == "COMPLETED"
    assert final.status_code == 3
    assert final.passed_tests == 1
    assert final.config.tests[0].result == "Passed"


def test_test_distribution_rejects_donor_url_and_verifies_sha256(
    suite_env, tmp_path: Path
):
    suite, dist, _, tests_dir, _ = suite_env

    with pytest.raises(CodeEditorError, match="Legacy donor URL"):
        dist.download_tests(
            TestDistributionRequest(
                source_url="http://autoupdate.strategyquant.com/indicator_data/indicator_tests.zip",
                expected_sha256="a" * 64,
            )
        )

    csv_path = tmp_path / "sample_ATR.csv"
    _generate_exact_reference_csv(
        csv_path, indicator_name="ATR", params_str="14", count=35
    )
    xml_cfg = suite_config_to_xml(
        SuiteConfigModel(
            engine="MetaTrader4",
            bars_to_reserve=20,
            tests=[
                SuiteTestCaseModel(
                    test_id="t1",
                    use=True,
                    indicator="ATR",
                    parameters="14",
                    decimals=6,
                    shift=0,
                    file_name="ATR_14.csv",
                )
            ],
        )
    )
    bundle_buf = BytesIO()
    with zipfile.ZipFile(bundle_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("IndicatorTester.xml", xml_cfg)
        zf.writestr("MetaTrader4/ATR_14.csv", csv_path.read_bytes())
    bundle_bytes = bundle_buf.getvalue()
    bundle_file = tmp_path / "verified_bundle.zip"
    bundle_file.write_bytes(bundle_bytes)
    digest = hashlib.sha256(bundle_bytes).hexdigest()

    with pytest.raises(CodeEditorError, match="SHA-256 digest mismatch"):
        dist.download_tests(
            TestDistributionRequest(
                archive_path=str(bundle_file),
                expected_sha256="0" * 64,
            )
        )

    snap = dist.download_tests(
        TestDistributionRequest(
            archive_path=str(bundle_file),
            expected_sha256=digest,
        )
    )
    assert snap.status == "COMPLETED"
    assert snap.completed is True
    assert snap.config_updated is True
    assert (tests_dir / "MetaTrader4" / "ATR_14.csv").is_file()
    loaded = suite.load_config(SuiteLoadConfigRequest())
    assert loaded.config.tests[0].exists is True


def test_indicator_calibration_engine_gate_and_population_stats(isolated_editor):
    store = StateStore(isolated_editor)

    def _fake_loader(symbol: str, timeframe: str, count: int):
        rng = np.random.default_rng(123)
        closes = 100.0 + np.cumsum(rng.normal(0.0, 1.0, count))
        bars = BarPrice(
            open_data=closes - 0.5,
            high_data=closes + 1.5,
            low_data=closes - 1.5,
            close_data=closes,
            volume_data=np.full(count, 500.0),
        )
        stamps = [1704067200 + i * 3600 for i in range(count)]
        return bars, stamps

    calibrator = IndicatorCalibrationService(store=store, history_loader=_fake_loader)

    with pytest.raises(CodeEditorError, match="Stockpicker"):
        calibrator.calibrate(
            CalibrationRequest(
                symbols=["EURUSD"],
                timeframes=["H1"],
                engine="Stockpicker",
            )
        )

    res = calibrator.calibrate(
        CalibrationRequest(
            project_name="BuilderProj",
            task_name="Task1",
            symbols=["EURUSD"],
            timeframes=["H1"],
            engine="MetaTrader4",
            max_steps=20,
            indicators=["ATR", "RSI", "DataLoggingIndy"],
            ranges_config_text="RSI.period=10,14,20\n",
            bars_count=120,
        )
    )
    assert res.calibrated_count >= 2
    keys = {entry.key for entry in res.ranges}
    assert "ATR" in keys
    assert "RSI" in keys
    for entry in res.ranges:
        assert entry.max_value >= entry.min_value
        assert entry.step > 0
        assert entry.samples > 0

    f_min, f_max, f_step = beautify_calibration_range(12.34, 87.65, max_steps=-1)
    assert f_min == 12.0
    assert f_max == 88.0
    assert f_step == 0.5
    parsed_cfg = parse_calibration_ranges_config(
        "rounding=disabled\nQQE.Value1=disabled\nQQE.RSIPeriod=10,20\n"
    )
    assert parsed_cfg.rounding_disabled is True
    assert ("qqe", "value1") in parsed_cfg.disabled_outputs
    assert parsed_cfg.parameter_variations[("qqe", "rsiperiod")] == ["10", "20"]


def test_indicator_suite_http_endpoints(isolated_editor, tmp_path: Path):
    app = create_app()
    app.state.persistence = isolated_editor
    app.state.code_editor_tests_dir = tmp_path / "http_tests"
    (tmp_path / "http_tests").mkdir(parents=True, exist_ok=True)

    def _fake_loader(symbol: str, timeframe: str, count: int):
        closes = np.linspace(1.1, 1.2, count)
        bars = BarPrice(
            open_data=closes,
            high_data=closes + 0.002,
            low_data=closes - 0.002,
            close_data=closes,
            volume_data=np.full(count, 100.0),
        )
        return bars, [1704067200 + i * 60 for i in range(count)]

    app.state.code_editor_history_loader = _fake_loader

    with TestClient(app) as client:
        r_ind = client.get("/api/v1/code-editor/indicator-suite/indicators")
        assert r_ind.status_code == 200
        assert len(r_ind.json()["data"]) > 50

        r_new = client.post(
            "/api/v1/code-editor/indicator-suite/config/new",
            json={
                "indicators": ["ATR"],
                "engine": "MetaTrader4",
                "bars_to_reserve": 300,
            },
        )
        assert r_new.status_code == 200
        assert r_new.json()["data"]["config"]["engine"] == "MetaTrader4"

        r_cal = client.post(
            "/api/v1/code-editor/indicator-suite/calibrate",
            json={
                "project_name": "P1",
                "symbols": ["EURUSD"],
                "timeframes": ["H1"],
                "engine": "MetaTrader4",
                "indicators": ["ATR"],
                "bars_count": 80,
            },
        )
        assert r_cal.status_code == 200
        assert r_cal.json()["data"]["calibrated_count"] == 1

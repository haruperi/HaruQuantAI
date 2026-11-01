"""Unit tests for ResultsSourceCodeService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_source_code import (
    MTPathsConfig,
    ResultsSourceCodeService,
    SourceCodeProjection,
)


def _create_source_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="SourceStrategy",
        parameters={
            "wf_schedule": [
                {
                    "start_date": "2023-01-01",
                    "end_date": "2023-06-30",
                    "net_profit": 500.0,
                    "params": "p=14",
                }
            ]
        },
    )


class TestResultsSourceCodeService:
    """Test suite for ResultsSourceCodeService."""

    def test_golden_fixture_render_metatrader5(self) -> None:
        """Verify rendering MetaTrader 5 source containing OnTick()."""
        service = ResultsSourceCodeService()
        sample = _create_source_result("Strat_01")
        service.register_in_memory_result(sample)

        resp = service.render_source_code(
            "p1", "Results", "Strat_01", target_id="MetaTrader5"
        )
        proj = resp.data
        assert proj.target_id == "MetaTrader5"
        assert proj.file_extension == ".mq5"
        assert "OnTick()" in proj.code

    def test_unknown_target_raises_error(self) -> None:
        """Verify unknown source target raises DomainError."""
        service = ResultsSourceCodeService()
        sample = _create_source_result("Strat_01")
        service.register_in_memory_result(sample)

        with pytest.raises(DomainError) as exc_info:
            service.render_source_code(
                "p1", "Results", "Strat_01", target_id="NonExistentTarget"
            )
        assert exc_info.value.code == "RESULTS_UNKNOWN_SOURCE_TARGET"

    def test_mt_paths_configuration(self) -> None:
        """Verify get and save MT paths."""
        service = ResultsSourceCodeService()
        cfg = MTPathsConfig(mt5_terminal_dir="C:/MT5")
        save_resp = service.save_mt_paths(cfg)
        assert save_resp.data.mt5_terminal_dir == "C:/MT5"

        get_resp = service.get_mt_paths()
        assert get_resp.data.mt5_terminal_dir == "C:/MT5"

    def test_export_wf_calendar(self) -> None:
        """Verify exporting WF calendar CSV."""
        service = ResultsSourceCodeService()
        sample = _create_source_result("Strat_01")
        service.register_in_memory_result(sample)

        cal_resp = service.export_wf_calendar("p1", "Results", "Strat_01")
        csv_text = cal_resp.data
        assert "RunIndex,StartDate,EndDate,NetProfit,Parameters" in csv_text
        assert "1,2023-01-01,2023-06-30,500.0,p=14" in csv_text

    def test_export_wf_calendar_missing(self) -> None:
        """Verify missing WF schedule raises DomainError."""
        service = ResultsSourceCodeService()
        empty_res = RunResult(
            result_id="res_empty",
            databank_id="Results",
            strategy_id="EmptyStrat",
            strategy_name="Empty",
        )
        service.register_in_memory_result(empty_res)

        with pytest.raises(DomainError) as exc_info:
            service.export_wf_calendar("p1", "Results", "EmptyStrat")
        assert exc_info.value.code == "RESULTS_WF_RESULT_REQUIRED"

    def test_projection_and_config_to_dict(self) -> None:
        """Verify to_dict serialization."""
        proj = SourceCodeProjection(
            strategy_id="s1",
            target_id="t1",
            title="T1",
            file_extension=".ext",
            param_style="PARAM_NAMES",
            code="code",
        )
        assert proj.to_dict()["target_id"] == "t1"

        cfg = MTPathsConfig(mt5_terminal_dir="b")
        assert cfg.to_dict()["mt5_terminal_dir"] == "b"

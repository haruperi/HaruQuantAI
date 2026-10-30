"""Tests for task execution coordinators.

Description:
    Tests execution, logging, protocol injection, error boundaries, and return
    contracts for all 15 Task Manager task coordinators.
"""

from __future__ import annotations

from typing import Any

from app.workspace.task_manager.tasks import (
    ApplyMassConfigTask,
    AutomaticPortfolioBuilderTask,
    AutomaticRetestTask,
    CallExternalScriptTask,
    CreatePortfolioTask,
    CustomAnalysisTask,
    FilteringTask,
    GoToTaskCoordinator,
    LoadFromFilesTask,
    LogDatabankStatsTask,
    NotificationTask,
    SaveToFilesTask,
    StopAndStartTaskCoordinator,
    UpdateDataTask,
    WaitForTaskCoordinator,
)


class MockProgress:
    """Mock progress tracker."""

    def __init__(self) -> None:
        self.logs: list[str] = []
        self.progress_values: list[float] = []

    def log(self, message: str) -> None:
        self.logs.append(message)

    def set_progress(self, percent: float) -> None:
        self.progress_values.append(percent)


class MockMassConfigStore:
    def __init__(self, count: int = 5) -> None:
        self.count = count

    def apply_config(
        self, databank: str, config_type: str, parameters: dict[str, Any]
    ) -> int:
        if databank == "fail":
            raise RuntimeError("Database error")
        return self.count


class MockPortfolioStore:
    def build_portfolio(
        self,
        source: str,
        target: str,
        size: int,
        corr: float,
        rank: str,
    ) -> int:
        if source == "fail":
            raise RuntimeError("Build error")
        return size

    def create_portfolio_strategy(
        self,
        source: str,
        name: str,
        mode: str,
        top_n: int,
    ) -> int:
        if source == "fail":
            raise RuntimeError("Create error")
        return top_n


class MockRetestEngine:
    def retest_strategies(
        self,
        databank: str,
        profile: str,
        filter_results: bool,
        target_databank: str,
    ) -> tuple[int, int]:
        if databank == "fail":
            raise RuntimeError("Retest crash")
        return 10, 8


class MockScriptExecutor:
    def execute(
        self,
        path: str,
        args: Any,
        cwd: str,
        timeout: int,
    ) -> tuple[int, str]:
        if path == "error.sh":
            return 1, "failed"
        if path == "crash.sh":
            raise TimeoutError("Timed out")
        return 0, "success"


class MockAnalysisRunner:
    def run_analysis(
        self, snippet: str, databank: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if snippet == "fail":
            raise RuntimeError("Analysis fail")
        return {"metric": 42.0}


class MockFilteringStore:
    def filter_strategies(
        self,
        source: str,
        target: str,
        conds: Any,
    ) -> tuple[int, int]:
        if source == "fail":
            raise RuntimeError("Filter error")
        return 20, 15


class MockFileLoadStore:
    def load_files_into_databank(
        self, directory: str, pattern: str, databank: str, clear: bool
    ) -> int:
        if directory == "fail":
            raise RuntimeError("Load fail")
        return 7


class MockStatsReporter:
    def compute_stats(self, bank: str, metrics: Any) -> dict[str, Any]:
        if bank == "fail":
            raise RuntimeError("Stats fail")
        return {"count": 10, "netProfit": 1500.0}


class MockNotificationSender:
    def send(self, ch: str, rec: str, subj: str, msg: str) -> bool:
        if rec == "fail":
            raise RuntimeError("Delivery fail")
        return True


class MockFileSaveStore:
    def save_databank_to_directory(
        self, bank: str, out_dir: str, fmt: str, save_all: bool
    ) -> int:
        if bank == "fail":
            raise RuntimeError("Save fail")
        return 5


class MockProjectController:
    def perform_action(self, proj: str, action: str) -> bool:
        if proj == "fail":
            raise RuntimeError("Controller fail")
        return True


class MockDataFeedProvider:
    def update_market_data(self, sym: str, tf: str, prov: str, clean: bool) -> int:
        if sym == "FAIL":
            raise RuntimeError("Data update fail")
        return 500


class MockChecker:
    def exists(self, path: str) -> bool:
        if path == "fail":
            raise RuntimeError("Checker error")
        return path == "present.csv"


class TestTaskCoordinators:
    """Test suite for all 15 task execution coordinators."""

    def test_apply_mass_config_task(self) -> None:
        p = MockProgress()
        s = MockMassConfigStore(3)
        res = ApplyMassConfigTask.run("Results", "def", {"a": 1}, store=s, progress=p)
        assert res.success
        assert res.modified_count == 3

        # Empty target
        fail_empty = ApplyMassConfigTask.run("", "def", {}, progress=p)
        assert not fail_empty.success

        # Error
        fail_err = ApplyMassConfigTask.run("fail", "def", {}, store=s, progress=p)
        assert not fail_err.success

    def test_automatic_portfolio_builder_task(self) -> None:
        p = MockProgress()
        s = MockPortfolioStore()
        res = AutomaticPortfolioBuilderTask.run(
            "Src", "Dst", 5, 0.7, "Sharpe", store=s, progress=p
        )
        assert res.success
        assert res.strategies_included == 5

        # Empty
        assert not AutomaticPortfolioBuilderTask.run(
            "", "Dst", 5, 0.7, "Sharpe"
        ).success

        # Error
        assert not AutomaticPortfolioBuilderTask.run(
            "fail", "Dst", 5, 0.7, "Sharpe", store=s
        ).success

    def test_automatic_retest_task(self) -> None:
        p = MockProgress()
        eng = MockRetestEngine()
        res = AutomaticRetestTask.run(
            "Results", "Stress", True, False, "", engine=eng, progress=p
        )
        assert res.success
        assert res.retested_count == 10
        assert res.passed_count == 8

        # Empty
        assert not AutomaticRetestTask.run("", "Stress", True, False, "").success

        # Error
        assert not AutomaticRetestTask.run(
            "fail", "Stress", True, False, "", engine=eng
        ).success

    def test_call_external_script_task(self) -> None:
        p = MockProgress()
        ex = MockScriptExecutor()
        res = CallExternalScriptTask.run(
            "ok.sh", [], "", 60, True, executor=ex, progress=p
        )
        assert res.success
        assert res.exit_code == 0

        # Empty
        assert not CallExternalScriptTask.run("", [], "", 60, True).success

        # Nonzero exit code
        fail_exit = CallExternalScriptTask.run(
            "error.sh", [], "", 60, True, executor=ex
        )
        assert not fail_exit.success

        # Nonzero exit code but fail_on_error=False
        soft_exit = CallExternalScriptTask.run(
            "error.sh", [], "", 60, False, executor=ex
        )
        assert soft_exit.success

        # Exception
        assert not CallExternalScriptTask.run(
            "crash.sh", [], "", 60, True, executor=ex
        ).success
        soft_crash = CallExternalScriptTask.run(
            "crash.sh", [], "", 60, False, executor=ex
        )
        assert soft_crash.success

    def test_create_portfolio_task(self) -> None:
        p = MockProgress()
        s = MockPortfolioStore()
        res = CreatePortfolioTask.run("Src", "Port", "top_n", 4, store=s, progress=p)
        assert res.success
        assert res.components_count == 4

        # Empty
        assert not CreatePortfolioTask.run("", "Port", "all", 0).success

        # Error
        assert not CreatePortfolioTask.run("fail", "Port", "all", 0, store=s).success

    def test_custom_analysis_task(self) -> None:
        p = MockProgress()
        runner = MockAnalysisRunner()
        res = CustomAnalysisTask.run("audit", "Results", {}, runner=runner, progress=p)
        assert res.success
        assert res.output_metrics["metric"] == 42.0

        # Empty
        assert not CustomAnalysisTask.run("", "Results", {}).success

        # Error
        assert not CustomAnalysisTask.run("fail", "Results", {}, runner=runner).success

    def test_filtering_task(self) -> None:
        p = MockProgress()
        s = MockFilteringStore()
        res = FilteringTask.run("Src", "Dst", [{"m": 1}], store=s, progress=p)
        assert res.success
        assert res.evaluated_count == 20
        assert res.passed_count == 15

        # Empty
        assert not FilteringTask.run("", "Dst", []).success

        # Error
        assert not FilteringTask.run("fail", "Dst", [], store=s).success

    def test_go_to_task_coordinator(self) -> None:
        tasks = [{"name": "A"}, {"name": "B"}, {"name": "Loop"}]
        # Met conditions
        res = GoToTaskCoordinator.evaluate_jump("Loop", "A", True, 2, tasks)
        assert res.jump_occurred
        assert res.next_index == 0

        # Unmet conditions
        res_unmet = GoToTaskCoordinator.evaluate_jump("Loop", "A", False, 2, tasks)
        assert not res_unmet.jump_occurred
        assert res_unmet.next_index == 3

        # Target not found
        res_missing = GoToTaskCoordinator.evaluate_jump(
            "Loop", "Missing", True, 2, tasks
        )
        assert not res_missing.jump_occurred
        assert res_missing.next_index == 3

    def test_load_from_files_task(self) -> None:
        p = MockProgress()
        s = MockFileLoadStore()
        res = LoadFromFilesTask.run(
            "dir", "*.sqx", "Results", False, store=s, progress=p
        )
        assert res.success
        assert res.loaded_count == 7

        # Empty
        assert not LoadFromFilesTask.run("", "*.sqx", "Results", False).success

        # Error
        assert not LoadFromFilesTask.run(
            "fail", "*.sqx", "Results", False, store=s
        ).success

    def test_log_databank_stats_task(self) -> None:
        rep = MockStatsReporter()
        res = LogDatabankStatsTask.run("Results", ["count"], "DEBUG", reporter=rep)
        assert res.success
        assert res.stats["count"] == 10

        # Empty
        assert not LogDatabankStatsTask.run("", ["count"]).success

        # Error
        assert not LogDatabankStatsTask.run("fail", ["count"], reporter=rep).success

    def test_notification_task(self) -> None:
        sender = MockNotificationSender()
        res = NotificationTask.run(
            "email",
            "test@example.com",
            "Done",
            "Project {p}",
            {"p": "Alfa"},
            sender=sender,
        )
        assert res.success
        assert res.formatted_message == "Project Alfa"

        # Invalid template placeholder fallback
        res_bad_fmt = NotificationTask.run(
            "email", "test@example.com", "Sub", "{missing}", {}
        )
        assert res_bad_fmt.success

        # Error
        assert not NotificationTask.run(
            "email", "fail", "Sub", "msg", {}, sender=sender
        ).success

    def test_save_to_files_task(self) -> None:
        p = MockProgress()
        s = MockFileSaveStore()
        res = SaveToFilesTask.run("Results", "out", "json", True, store=s, progress=p)
        assert res.success
        assert res.saved_count == 5

        # Empty
        assert not SaveToFilesTask.run("", "out", "json", True).success

        # Error
        assert not SaveToFilesTask.run("fail", "out", "json", True, store=s).success

    def test_stop_and_start_task_coordinator(self) -> None:
        ctrl = MockProjectController()
        # Conditions met
        res = StopAndStartTaskCoordinator.run("restart", "Proj2", True, controller=ctrl)
        assert res.action_executed

        # Conditions not met
        res_unmet = StopAndStartTaskCoordinator.run(
            "restart", "Proj2", False, controller=ctrl
        )
        assert not res_unmet.action_executed

        # Error
        assert not StopAndStartTaskCoordinator.run(
            "restart", "fail", True, controller=ctrl
        ).action_executed

    def test_update_data_task(self) -> None:
        p = MockProgress()
        prov = MockDataFeedProvider()
        res = UpdateDataTask.run(
            "EURUSD", "M1", "def", False, provider=prov, progress=p
        )
        assert res.success
        assert res.bars_updated == 500

        # Empty
        assert not UpdateDataTask.run("", "M1", "def", False).success

        # Error
        assert not UpdateDataTask.run("FAIL", "M1", "def", False, provider=prov).success

    def test_wait_for_task_coordinator(self) -> None:
        checker = MockChecker()
        # User wait
        res_user = WaitForTaskCoordinator.run("user", "")
        assert res_user.should_pause
        assert not res_user.condition_satisfied

        # File wait - present
        res_file_ok = WaitForTaskCoordinator.run("file", "present.csv", checker=checker)
        assert not res_file_ok.should_pause
        assert res_file_ok.condition_satisfied

        # File wait - missing
        res_file_miss = WaitForTaskCoordinator.run(
            "file", "missing.csv", checker=checker
        )
        assert res_file_miss.should_pause
        assert not res_file_miss.condition_satisfied

        # File wait - error
        res_file_err = WaitForTaskCoordinator.run("file", "fail", checker=checker)
        assert res_file_err.should_pause

        # Unknown action
        res_unknown = WaitForTaskCoordinator.run("custom", "")
        assert not res_unknown.should_pause

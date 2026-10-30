"""Tests for task manager settings serializers and parsers.

Description:
    Tests defaults, round-trip serialization, payload parsing, null-safety, and
    non-destructive target dictionary writing for all 17 Task Manager settings modules.
"""

from __future__ import annotations

from app.workspace.task_manager.settings import (
    AdvancedTMSettings,
    ApplyMassConfigSettings,
    AutoPortfolioBuilderSettings,
    AutoRetestSettings,
    CallExternalScriptSettings,
    ClearDatabanksSettings,
    CreatePortfolioSettings,
    CustomAnalysisSettings,
    DeleteFileSettings,
    FilteringSettings,
    GoToTaskSettings,
    LoadFromFilesSettings,
    LogDatabankStatsSettings,
    NotificationSettings,
    SaveToFilesSettings,
    StopAndStartSettings,
    UpdateDataSettings,
)


class TestSettingsSerializers:
    """Test suite for all settings serializers and parsers."""

    def test_advanced_tm_settings(self) -> None:
        """Test AdvancedTMSettings defaults, load, and write."""
        cfg = AdvancedTMSettings.load(None)
        assert cfg.max_runtime_minutes == 0
        assert not cfg.stop_on_error

        loaded = AdvancedTMSettings.load(
            {
                "maxRuntimeMinutes": 180,
                "stopOnError": True,
                "maxConsecutiveErrors": 5,
                "emailOnCompletion": True,
                "notificationEmail": "admin@haruquant.ai",
                "exitOnCondition": True,
            }
        )
        assert loaded.max_runtime_minutes == 180
        assert loaded.stop_on_error
        assert loaded.max_consecutive_errors == 5
        assert loaded.notification_email == "admin@haruquant.ai"

        target: dict[str, object] = {"preserve": "yes"}
        AdvancedTMSettings.write(target, loaded)
        assert target["maxRuntimeMinutes"] == 180
        assert target["preserve"] == "yes"

        d = AdvancedTMSettings.to_dict(loaded)
        assert d["max_runtime_minutes"] == 180

    def test_apply_mass_config_settings(self) -> None:
        """Test ApplyMassConfigSettings."""
        cfg = ApplyMassConfigSettings.load(None)
        assert cfg.target_databank == "Results"

        loaded = ApplyMassConfigSettings.load(
            {
                "targetDatabank": "Top10",
                "configType": "aggressive",
                "parameters": {"risk": 0.02},
            }
        )
        assert loaded.target_databank == "Top10"
        assert loaded.config_type == "aggressive"
        assert loaded.parameters["risk"] == 0.02

        target: dict[str, object] = {}
        ApplyMassConfigSettings.write(target, loaded)
        assert target["targetDatabank"] == "Top10"

    def test_auto_portfolio_builder_settings(self) -> None:
        """Test AutoPortfolioBuilderSettings."""
        cfg = AutoPortfolioBuilderSettings.load(None)
        assert cfg.portfolio_size == 5

        loaded = AutoPortfolioBuilderSettings.load(
            {
                "sourceDatabank": "BankA",
                "targetDatabank": "BankB",
                "portfolioSize": 12,
                "correlationThreshold": 0.5,
                "rankingMethod": "NetProfit",
            }
        )
        assert loaded.portfolio_size == 12
        assert loaded.correlation_threshold == 0.5

        target: dict[str, object] = {}
        AutoPortfolioBuilderSettings.write(target, loaded)
        assert target["portfolioSize"] == 12

    def test_auto_retest_settings(self) -> None:
        """Test AutoRetestSettings."""
        cfg = AutoRetestSettings.load(None)
        assert cfg.databank == "Results"

        loaded = AutoRetestSettings.load(
            {
                "databank": "Candidates",
                "retestProfile": "StressTest",
                "filterResults": False,
                "saveToTargetDatabank": True,
                "targetDatabank": "Passed",
            }
        )
        assert loaded.databank == "Candidates"
        assert loaded.retest_profile == "StressTest"
        assert not loaded.filter_results
        assert loaded.save_to_target_databank

        target: dict[str, object] = {}
        AutoRetestSettings.write(target, loaded)
        assert target["retestProfile"] == "StressTest"

    def test_call_external_script_settings(self) -> None:
        """Test CallExternalScriptSettings."""
        cfg = CallExternalScriptSettings.load(None)
        assert cfg.timeout_seconds == 300

        loaded = CallExternalScriptSettings.load(
            {
                "scriptPath": "/opt/script.py",
                "arguments": ["--verbose", "--runs", "10"],
                "workingDirectory": "/opt",
                "timeoutSeconds": 60,
                "failOnError": False,
            }
        )
        assert loaded.script_path == "/opt/script.py"
        assert len(loaded.arguments) == 3
        assert not loaded.fail_on_error

        # String arguments splitting
        loaded_str = CallExternalScriptSettings.load({"arguments": "--dry-run --fast"})
        assert loaded_str.arguments == ["--dry-run", "--fast"]

        target: dict[str, object] = {}
        CallExternalScriptSettings.write(target, loaded)
        assert target["scriptPath"] == "/opt/script.py"

    def test_clear_databanks_settings(self) -> None:
        """Test ClearDatabanksSettings."""
        cfg = ClearDatabanksSettings.load(None)
        assert cfg.databanks == ["Results"]

        loaded = ClearDatabanksSettings.load(
            {"databanks": ["A", "B"], "resetView": False}
        )
        assert loaded.databanks == ["A", "B"]
        assert not loaded.reset_view

        loaded_single = ClearDatabanksSettings.load({"databanks": "All"})
        assert loaded_single.databanks == ["All"]

        target: dict[str, object] = {}
        ClearDatabanksSettings.write(target, loaded)
        assert target["databanks"] == ["A", "B"]

    def test_create_portfolio_settings(self) -> None:
        """Test CreatePortfolioSettings."""
        cfg = CreatePortfolioSettings.load(None)
        assert cfg.source_databank == "Results"

        loaded = CreatePortfolioSettings.load(
            {
                "sourceDatabank": "Top",
                "portfolioName": "Best10",
                "selectionMode": "top_n",
                "topN": 10,
            }
        )
        assert loaded.portfolio_name == "Best10"
        assert loaded.top_n == 10

        target: dict[str, object] = {}
        CreatePortfolioSettings.write(target, loaded)
        assert target["portfolioName"] == "Best10"

    def test_custom_analysis_settings(self) -> None:
        """Test CustomAnalysisSettings."""
        cfg = CustomAnalysisSettings.load(None)
        assert cfg.target_databank == "Results"

        loaded = CustomAnalysisSettings.load(
            {
                "snippetName": "drawdown_audit",
                "targetDatabank": "Filtered",
                "parameters": {"k": 1},
            }
        )
        assert loaded.snippet_name == "drawdown_audit"
        assert loaded.parameters == {"k": 1}

        target: dict[str, object] = {}
        CustomAnalysisSettings.write(target, loaded)
        assert target["snippetName"] == "drawdown_audit"

    def test_delete_file_settings(self) -> None:
        """Test DeleteFileSettings."""
        cfg = DeleteFileSettings.load(None)
        assert not cfg.fail_if_missing

        loaded = DeleteFileSettings.load(
            {"filePath": "/tmp/out.csv", "failIfMissing": True}
        )
        assert loaded.file_path == "/tmp/out.csv"
        assert loaded.fail_if_missing

        target: dict[str, object] = {}
        DeleteFileSettings.write(target, loaded)
        assert target["filePath"] == "/tmp/out.csv"

    def test_filtering_settings(self) -> None:
        """Test FilteringSettings."""
        cfg = FilteringSettings.load(None)
        assert cfg.source_databank == "Results"

        loaded = FilteringSettings.load(
            {
                "sourceDatabank": "Gen",
                "targetDatabank": "Passed",
                "filterConditions": [
                    {"metric": "SharpeRatio", "comparator": ">", "value": 1.5},
                    {"metric": "Drawdown", "comparator": "<", "value": 20.0},
                ],
            }
        )
        assert len(loaded.filter_conditions) == 2
        assert loaded.filter_conditions[0].metric == "SharpeRatio"
        assert loaded.filter_conditions[0].value == 1.5

        target: dict[str, object] = {}
        FilteringSettings.write(target, loaded)
        assert target["sourceDatabank"] == "Gen"
        raw_conds = target["filterConditions"]
        assert isinstance(raw_conds, list)
        assert len(raw_conds) == 2

    def test_go_to_task_settings(self) -> None:
        """Test GoToTaskSettings."""
        cfg = GoToTaskSettings.load(None)
        assert cfg.target_task == ""

        loaded = GoToTaskSettings.load(
            {
                "task": "Step2",
                "conditions": [
                    {"type": "CyclesCount", "comparator": "<", "number": 10}
                ],
            }
        )
        assert loaded.target_task == "Step2"
        assert len(loaded.conditions) == 1

        target: dict[str, object] = {}
        GoToTaskSettings.write(target, loaded)
        assert target["task"] == "Step2"

    def test_load_from_files_settings(self) -> None:
        """Test LoadFromFilesSettings."""
        cfg = LoadFromFilesSettings.load(None)
        assert cfg.file_pattern == "*.sqx"

        loaded = LoadFromFilesSettings.load(
            {
                "directoryPath": "data/strats",
                "filePattern": "*.json",
                "targetDatabank": "Loaded",
                "clearBeforeLoad": True,
            }
        )
        assert loaded.directory_path == "data/strats"
        assert loaded.file_pattern == "*.json"
        assert loaded.clear_before_load

        target: dict[str, object] = {}
        LoadFromFilesSettings.write(target, loaded)
        assert target["clearBeforeLoad"] is True

    def test_log_databank_stats_settings(self) -> None:
        """Test LogDatabankStatsSettings."""
        cfg = LogDatabankStatsSettings.load(None)
        assert cfg.databank == "Results"

        loaded = LogDatabankStatsSettings.load(
            {"databank": "Main", "metrics": ["profit", "drawdown"], "logLevel": "DEBUG"}
        )
        assert loaded.databank == "Main"
        assert loaded.metrics == ["profit", "drawdown"]
        assert loaded.log_level == "DEBUG"

        loaded_single = LogDatabankStatsSettings.load({"metrics": "profit"})
        assert loaded_single.metrics == ["profit"]

        target: dict[str, object] = {}
        LogDatabankStatsSettings.write(target, loaded)
        assert target["logLevel"] == "DEBUG"

    def test_notification_settings(self) -> None:
        """Test NotificationSettings."""
        cfg = NotificationSettings.load(None)
        assert cfg.channel == "email"

        loaded = NotificationSettings.load(
            {
                "channel": "webhook",
                "recipient": "https://hooks.slack.com/services/xyz",
                "subject": "Build finished",
                "message": "Done with {projectName}",
            }
        )
        assert loaded.channel == "webhook"
        assert loaded.recipient == "https://hooks.slack.com/services/xyz"
        assert loaded.message_template == "Done with {projectName}"

        target: dict[str, object] = {}
        NotificationSettings.write(target, loaded)
        assert target["channel"] == "webhook"

    def test_save_to_files_settings(self) -> None:
        """Test SaveToFilesSettings."""
        cfg = SaveToFilesSettings.load(None)
        assert cfg.file_format == "sqx"

        loaded = SaveToFilesSettings.load(
            {
                "sourceDatabank": "Top",
                "outputDirectory": "exports/best",
                "fileFormat": "json",
                "saveAll": False,
            }
        )
        assert loaded.output_directory == "exports/best"
        assert loaded.file_format == "json"
        assert not loaded.save_all

        target: dict[str, object] = {}
        SaveToFilesSettings.write(target, loaded)
        assert target["outputDirectory"] == "exports/best"

    def test_stop_and_start_settings(self) -> None:
        """Test StopAndStartSettings."""
        cfg = StopAndStartSettings.load(None)
        assert cfg.action == "stop"

        loaded = StopAndStartSettings.load(
            {
                "action": "restart",
                "targetProject": "Worker2",
                "conditions": [{"type": "Runtime"}],
            }
        )
        assert loaded.action == "restart"
        assert loaded.target_project == "Worker2"
        assert len(loaded.conditions) == 1

        target: dict[str, object] = {}
        StopAndStartSettings.write(target, loaded)
        assert target["action"] == "restart"

    def test_update_data_settings(self) -> None:
        """Test UpdateDataSettings."""
        cfg = UpdateDataSettings.load(None)
        assert cfg.symbol == "EURUSD"

        loaded = UpdateDataSettings.load(
            {
                "symbol": "GBPUSD",
                "timeframe": "M5",
                "dataProvider": "Dukascopy",
                "cleanHistory": True,
            }
        )
        assert loaded.symbol == "GBPUSD"
        assert loaded.timeframe == "M5"
        assert loaded.data_provider == "Dukascopy"
        assert loaded.clean_history

        target: dict[str, object] = {}
        UpdateDataSettings.write(target, loaded)
        assert target["symbol"] == "GBPUSD"

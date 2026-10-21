"""Unit tests for Data Manager contextual help service and CLI adapter."""

from __future__ import annotations

import logging
import runpy
import sys
from typing import Any

import pytest
from app.workspace.data_manager.help import GUIDE_FR, DMHelp, DMHelpCLI, main


class TestDMHelp:
    """Verify DMHelp.help() behavior, validation, and telemetry."""

    def test_help_default_overview_topic_and_telemetry(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Default topic returns overview documentation and logs FR-DATAMGR-HELP-GUIDE."""
        service = DMHelp()
        with caplog.at_level(logging.INFO):
            guide = service.help()

        assert guide["topic"] == "overview"
        assert guide["title"] == "Data Manager Overview"
        assert "Download, import, and export market data." in guide["summary"]
        assert "overview" in guide["available_topics"]
        assert "export" in guide["available_topics"]
        assert len(guide["tutorials"]) == 3
        test_ids = [item["test_id"] for item in guide["tutorials"]]
        assert test_ids == [
            "dm-help-openlink-btn",
            "dm-help-openlink-btn-2",
            "dm-help-openlink-btn-3",
        ]
        assert all(len(item["steps"]) == 3 for item in guide["tutorials"])
        assert any(
            GUIDE_FR in rec.message and rec.levelname == "INFO"
            for rec in caplog.records
        )

    @pytest.mark.parametrize(
        "raw_topic,expected_key",
        [
            ("data", "data"),
            ("  IMPORT  ", "import"),
            ("export", "export"),
            ("instruments", "instruments"),
            ("sessions", "sessions"),
            ("brokers", "brokers"),
            ("custom-data", "custom-data"),
            ("stock-groups", "stock-groups"),
            ("log", "log"),
            ("chart", "chart"),
        ],
    )
    def test_help_resolves_all_registered_topics(
        self, raw_topic: str, expected_key: str
    ) -> None:
        """Every registered topic resolves case-insensitively with trimmed whitespace."""
        service = DMHelp()
        guide = service.help(raw_topic)
        assert guide["topic"] == expected_key
        assert isinstance(guide["title"], str) and guide["title"]
        assert isinstance(guide["summary"], str) and guide["summary"]

    def test_help_returns_defensive_copy_of_tutorials(self) -> None:
        """Mutating returned tutorial steps does not corrupt subsequent calls."""
        service = DMHelp()
        first = service.help("overview")
        first["tutorials"][0]["steps"].append("Mutated step")

        second = service.help("overview")
        assert "Mutated step" not in second["tutorials"][0]["steps"]

    @pytest.mark.parametrize("invalid_topic", ["unknown-topic", "", "   ", 123])
    def test_help_rejects_unsupported_topic_with_warning(
        self, invalid_topic: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Unsupported or non-string topics log WARNING and raise ValueError."""
        service = DMHelp()
        with (
            caplog.at_level(logging.WARNING),
            pytest.raises(ValueError, match="Unsupported Data Manager help topic"),
        ):
            service.help(invalid_topic)

        assert any(
            GUIDE_FR in rec.message and rec.levelname == "WARNING"
            for rec in caplog.records
        )


class TestDMHelpCLI:
    """Verify DMHelpCLI formatting and module entrypoints."""

    def test_format_help_guide_renders_header_summary_and_tutorials(self) -> None:
        """CLI formatter outputs structured heading, summary, and tutorial bullets."""
        guide = DMHelp().help("export")
        formatted = DMHelpCLI.format_help_guide(guide)
        assert "=== Multi-Format Data Export (export) ===" in formatted
        assert "Export selected datasets to target files." in formatted
        assert "- Test strategies with tick precision:" in formatted
        assert (
            "- Export data from Data Manager to external trading platforms:"
            in formatted
        )
        assert "- Import historical bar and tick data from files:" in formatted

    def test_main_and_dunder_main_execution(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Standalone main() and python -m execution complete without error."""
        with caplog.at_level(logging.INFO):
            main()
        assert any("Data Manager Overview" in rec.message for rec in caplog.records)

        sys.modules.pop("app.workspace.data_manager.help", None)
        runpy.run_module("app.workspace.data_manager.help", run_name="__main__")

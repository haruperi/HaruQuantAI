"""Unit tests for Custom Data indicators CLI registration and commands."""

import argparse
from unittest.mock import patch

from app.workspace.data_manager.cli import (
    CustomDataCLI,
    format_custom_table,
    format_review_table,
    register_commands,
    run_command,
)
from app.workspace.data_manager.custom import CustomData


def _setup_parser():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    register_commands(commands)
    return parser


def test_cli_format_custom_table():
    items = [
        {
            "name": "Sentiment",
            "values": [{"name": "Score"}, {"name": "Rank"}],
            "data_type": "custom",
            "timeframe": "D1",
            "date_from": "2026-01-01",
            "date_to": "2026-01-10",
            "total_days": 10,
            "total_records": 100,
        },
        {
            "name": "COT_Legacy",
            "values": [
                {"name": "Long"},
                {"name": "Short"},
                {"name": "Net"},
                {"name": "OI"},
            ],
            "data_type": "cot",
            "timeframe": "W1",
            "date_from": "2026-01-01",
            "date_to": "2026-01-10",
            "total_days": 10,
            "total_records": 50,
        },
    ]
    table = format_custom_table(items)
    assert "Sentiment" in table
    assert "Score, Rank" in table
    assert "4 outputs" in table
    assert CustomDataCLI.format_custom_table(items) == table

    empty_table = format_custom_table([])
    assert "=== External Indicators Catalog (0 items) ===" in empty_table


def test_cli_format_review_table():
    records = [
        {"timestamp": "2026-01-01", "values": {"Score": 10, "Rank": 1}},
        {"timestamp": "2026-01-02", "values": {"Score": 20, "Rank": 2}},
    ]
    table = format_review_table(records, ["Score", "Rank"])
    assert "Timestamp" in table
    assert "Score" in table
    assert "Rank" in table
    assert "2026-01-01" in table
    assert "10" in table
    assert CustomDataCLI.format_review_table(records, ["Score", "Rank"]) == table

    empty_table = format_review_table([], ["Score"])
    assert "No observations recorded." in empty_table


def test_custom_cli_list_command(capsys):
    parser = _setup_parser()
    args = parser.parse_args(["data-manager", "custom", "list"])

    with patch.object(
        CustomData,
        "list",
        return_value={
            "success": True,
            "data": [
                {
                    "name": "Test",
                    "values": [{"name": "V"}],
                    "data_type": "custom",
                    "timeframe": "D1",
                    "date_from": None,
                    "date_to": None,
                    "total_days": 0,
                    "total_records": 0,
                }
            ],
        },
    ):
        code = run_command(args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Page 1 of 1" in out
        assert "Test" in out


def test_custom_cli_add_and_edit_command(capsys):
    parser = _setup_parser()
    add_args = parser.parse_args(
        [
            "data-manager",
            "custom",
            "add",
            "--name",
            "Sentiment",
            "--values",
            "Score,Rank",
            "--timeframe",
            "D1",
        ]
    )

    with patch.object(
        CustomData,
        "add",
        return_value={
            "success": True,
            "message": "Indicator added.",
            "data": {
                "name": "Sentiment",
                "values": [{"name": "Score"}, {"name": "Rank"}],
                "data_type": "custom",
                "timeframe": "D1",
                "total_records": 0,
            },
        },
    ):
        code = run_command(add_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Indicator added." in out
        assert "Sentiment" in out

    edit_args = parser.parse_args(
        [
            "data-manager",
            "custom",
            "edit",
            "Sentiment",
            "--timeframe",
            "W1",
        ]
    )

    with patch.object(
        CustomData,
        "edit",
        return_value={
            "success": True,
            "message": "Indicator updated.",
            "data": {
                "name": "Sentiment",
                "values": [{"name": "Score"}],
                "data_type": "custom",
                "timeframe": "W1",
                "total_records": 0,
            },
        },
    ):
        code = run_command(edit_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Indicator updated." in out


def test_custom_cli_delete_and_clear_command(capsys):
    parser = _setup_parser()
    del_args = parser.parse_args(
        ["data-manager", "custom", "delete", "Sentiment", "Test"]
    )

    with patch.object(
        CustomData,
        "delete",
        return_value={
            "success": True,
            "message": "Indicators deleted.",
            "data": {"names": ["Sentiment", "Test"], "cleared_records": 5},
        },
    ):
        code = run_command(del_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Indicators deleted." in out
        assert "Sentiment" in out

    clr_args = parser.parse_args(["data-manager", "custom", "clear", "Sentiment"])

    with patch.object(
        CustomData,
        "clear",
        return_value={
            "success": True,
            "data": {"names": ["Sentiment"], "cleared_records": 10},
        },
    ):
        code = run_command(clr_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Cleared 10 observations" in out


def test_custom_cli_review_and_recognize_command(capsys):
    parser = _setup_parser()
    rev_args = parser.parse_args(
        ["data-manager", "custom", "review-data", "Sentiment", "--limit", "10"]
    )

    with patch.object(
        CustomData,
        "review_data",
        return_value={
            "success": True,
            "data": {
                "name": "Sentiment",
                "columns": ["Score"],
                "records": [{"timestamp": "2026-01-01", "values": {"Score": 1.5}}],
            },
        },
    ):
        code = run_command(rev_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Review observations for Sentiment:" in out
        assert "2026-01-01" in out

    rec_args = parser.parse_args(["data-manager", "custom", "recognize", "test.mq4"])

    with patch.object(
        CustomData,
        "recognize_from_file",
        return_value={
            "success": True,
            "message": "Recognized indicator.",
            "data": {
                "name": "test",
                "values": [{"name": "Score"}],
                "data_type": "custom",
                "timeframe": "D1",
                "total_records": 0,
            },
        },
    ):
        code = run_command(rec_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Recognized indicator." in out


def test_custom_cli_import_and_preview_command(capsys):
    parser = _setup_parser()
    imp_args = parser.parse_args(
        [
            "data-manager",
            "custom",
            "import-data",
            "Sentiment",
            "data.csv",
            "--columns",
            "date,Score",
        ]
    )

    with patch.object(
        CustomData,
        "import_data",
        return_value={
            "success": True,
            "data": {
                "name": "Sentiment",
                "imported_count": 50,
                "skipped_rows": 2,
            },
        },
    ):
        code = run_command(imp_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Imported 50 observations (2 skipped)" in out

    prev_args = parser.parse_args(
        [
            "data-manager",
            "custom",
            "import-preview",
            "Sentiment",
            "data.csv",
        ]
    )

    with patch.object(
        CustomData,
        "import_preview",
        return_value={
            "success": True,
            "data": {
                "total_records": 1,
                "format": {"columns": ["date", "Score"]},
                "records": [{"timestamp": "2026-01-01", "values": {"Score": 10}}],
            },
        },
    ):
        code = run_command(prev_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Preview for Sentiment (1 records found):" in out


def test_custom_cli_format_commands(capsys):
    parser = _setup_parser()
    add_fmt = parser.parse_args(
        [
            "data-manager",
            "custom",
            "add-format",
            "MyFormat",
            "--config",
            '{"separator": ",", "date_format": "%Y-%m-%d"}',
        ]
    )

    with patch.object(
        CustomData,
        "add_import_format",
        return_value={
            "success": True,
            "message": "Format added.",
            "data": {"name": "MyFormat", "separator": ","},
        },
    ):
        code = run_command(add_fmt, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Format added." in out

    del_fmt = parser.parse_args(["data-manager", "custom", "delete-format", "MyFormat"])

    with patch.object(
        CustomData,
        "delete_import_format",
        return_value={"success": True, "message": "Format deleted."},
    ):
        code = run_command(del_fmt, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Format deleted." in out


def test_custom_cli_transfer_commands(capsys):
    parser = _setup_parser()
    exp_args = parser.parse_args(
        ["data-manager", "custom", "export-values", "Sentiment", "out.csv"]
    )

    with patch.object(
        CustomData,
        "export_values",
        return_value={"success": True, "data": {"path": "out.csv", "count": 25}},
    ):
        code = run_command(exp_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Exported 25 rows to out.csv" in out

    cot_args = parser.parse_args(["data-manager", "custom", "update-cot"])

    with patch.object(
        CustomData,
        "update_cot",
        return_value={
            "success": True,
            "data": {"updated_count": 5, "records": 250},
        },
    ):
        code = run_command(cot_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Updated 5 COT indicators (250 records)" in out

    act_args = parser.parse_args(
        ["data-manager", "custom", "import-action", "job-1", "pause"]
    )

    with patch.object(
        CustomData,
        "import_action",
        return_value={"success": True, "message": "Import paused."},
    ):
        code = run_command(act_args, parser=parser)
        assert code == 0
        out = capsys.readouterr().out
        assert "Import paused." in out

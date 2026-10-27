"""Unit tests for Data Manager Help CLI commands."""

import argparse

from app.workspace.data_manager.cli import register_commands
from app.workspace.data_manager.help import run_help_command


def _setup_parser():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    register_commands(commands)
    return parser


def test_cli_help_topic_overview():
    parser = _setup_parser()
    args = parser.parse_args(["data-manager", "help", "topic", "overview"])
    res = run_help_command(args, parser)
    assert res["success"] is True
    assert res["data"]["topic"] == "overview"
    assert res["data"]["title"] == "Data Manager Overview"


def test_cli_help_list_topics():
    parser = _setup_parser()
    args = parser.parse_args(["data-manager", "help", "list-topics"])
    res = run_help_command(args, parser)
    assert res["success"] is True
    assert len(res["data"]["topics"]) == 11


def test_cli_help_list_tutorials():
    parser = _setup_parser()
    args = parser.parse_args(
        ["data-manager", "help", "list-tutorials", "--topic", "export"]
    )
    res = run_help_command(args, parser)
    assert res["success"] is True
    assert len(res["data"]["tutorials"]) == 2


def test_cli_help_get_tutorial():
    parser = _setup_parser()
    args = parser.parse_args(
        ["data-manager", "help", "get-tutorial", "tick-precision-testing"]
    )
    res = run_help_command(args, parser)
    assert res["success"] is True
    assert res["data"]["id"] == "tick-precision-testing"


def test_cli_help_list_articles():
    parser = _setup_parser()
    args = parser.parse_args(["data-manager", "help", "list-articles"])
    res = run_help_command(args, parser)
    assert res["success"] is True
    assert len(res["data"]["articles"]) == 3


def test_cli_help_search():
    parser = _setup_parser()
    args = parser.parse_args(["data-manager", "help", "search", "MetaTrader"])
    res = run_help_command(args, parser)
    assert res["success"] is True
    assert res["data"]["total_matches"] > 0

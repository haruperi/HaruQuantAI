"""Unit tests for Data Manager Dukascopy CLI commands."""

import argparse
import sqlite3

import pytest
from app.workspace.data_manager import register_commands
from app.workspace.data_manager.sources import run_dukascopy_command


@pytest.fixture(autouse=True)
def isolated_service(tmp_path, monkeypatch):
    from app.host.persistence import HostPersistence
    from app.workspace.data_manager import sources
    from app.workspace.data_manager.sources import Dukascopy

    database = tmp_path / "cli.db"
    sqlite3.connect(database).close()
    service = Dukascopy(HostPersistence(database), storage_root=tmp_path / "market")
    monkeypatch.setattr(sources, "Dukascopy", lambda: service)


def _setup_parser():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    register_commands(commands)
    return parser


def test_cli_dukascopy_disclaimer():
    parser = _setup_parser()
    args = parser.parse_args(["data-manager", "dukascopy", "disclaimer"])
    res = run_dukascopy_command(args, parser)
    assert res["success"] is True
    assert res["data"]["title"] == "Dukascopy data disclaimer"


def test_cli_dukascopy_catalog():
    parser = _setup_parser()
    args = parser.parse_args(
        ["data-manager", "dukascopy", "catalog", "--search", "EURUSD"]
    )
    res = run_dukascopy_command(args, parser)
    assert res["success"] is True
    assert res["data"]["count"] == 1
    assert res["data"]["symbols"][0]["symbol"] == "EURUSD"


def test_cli_dukascopy_add():
    parser = _setup_parser()
    args = parser.parse_args(
        [
            "data-manager",
            "dukascopy",
            "add",
            "EURUSD",
            "--data-type",
            "M1",
            "--postfix",
            "_CLITEST",
        ]
    )
    res = run_dukascopy_command(args, parser)
    # If first time, success
    if res["success"]:
        assert res["data"]["count"] == 1
        assert res["data"]["records"][0]["id"] == "dukascopy:EURUSD_CLITEST:M1"
    else:
        assert res["error"]["code"] == "conflict"

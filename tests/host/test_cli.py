"""Headless command output and failure behavior."""

import json
import sqlite3
from contextlib import closing
from unittest.mock import Mock

import pytest
from app import cli
from app.core.host.session import SessionManager
from app.host.persistence import HostPersistence


def test_main_routes_registered_domain_handler(monkeypatch, capsys):
    from app.workspace import data_manager as domain_cli

    handler = Mock(return_value=7)

    def register(commands):
        commands.add_parser("example-domain").set_defaults(handler=handler)

    monkeypatch.setattr(domain_cli, "register_commands", register)
    shutdown = Mock()
    monkeypatch.setattr(cli, "shutdown_logging", shutdown)
    assert cli.main(["example-domain"]) == 7
    assert handler.call_args.args[0].command == "example-domain"
    assert capsys.readouterr().out == ""
    shutdown.assert_called_once_with()


def test_health_checks_services_without_exposing_rows(monkeypatch):
    gateway = Mock()
    gateway.read_records.return_value = {
        "success": True,
        "data": {"records": [{"session_id": "private-session"}]},
    }
    settings = Mock()
    constructor = Mock(return_value=settings)
    monkeypatch.setattr(cli, "SettingsManager", constructor)
    response = cli.health(gateway)
    constructor.assert_called_once_with(gateway)
    settings.reload.assert_called_once_with()
    gateway.read_records.assert_called_once_with(
        "host_session", columns=["session_id"], limit=1
    )
    assert response["success"]
    assert response["data"]["status"] == "ok"
    assert "private-session" not in json.dumps(response)


@pytest.mark.parametrize("stage", ["settings", "session_storage"])
def test_health_reports_safe_failures(monkeypatch, stage):
    gateway = Mock()
    gateway.read_records.return_value = {"success": False}
    settings = Mock()
    if stage == "settings":
        settings.reload.side_effect = RuntimeError("private-credential")
    monkeypatch.setattr(cli, "SettingsManager", Mock(return_value=settings))
    response = cli.health(gateway)
    assert not response["success"]
    assert response["error"]["details"]["check"] == stage
    assert "private-credential" not in json.dumps(response)


@pytest.mark.parametrize("success", [True, False])
def test_command_json_and_exit_status(monkeypatch, capsys, success):
    monkeypatch.delenv("HARUQUANTAI_SESSION_TOKEN", raising=False)
    result = {"success": success}
    monkeypatch.setattr(cli, "health", Mock(return_value=result))
    shutdown = Mock()
    monkeypatch.setattr(cli, "shutdown_logging", shutdown)
    assert cli.main(["health"]) == (0 if success else 1)
    assert json.loads(capsys.readouterr().out) == result
    shutdown.assert_called_once_with()


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["unknown"],
        ["data-manager"],
        ["data-manager", "symbol"],
        ["data-manager", "symbol", "unknown"],
    ],
)
def test_invalid_commands_do_not_run_health(monkeypatch, arguments):
    health = Mock()
    monkeypatch.setattr(cli, "health", health)
    monkeypatch.setattr(cli, "shutdown_logging", Mock())
    with pytest.raises(SystemExit) as error:
        cli.main(arguments)
    assert error.value.code == 2
    health.assert_not_called()


@pytest.mark.parametrize(
    "result",
    [
        {"success": True, "data": [{"name": "EURUSD"}]},
        {"success": True, "data": []},
        {"success": False, "error": {"code": "internal"}},
    ],
)
def test_symbol_list_command(monkeypatch, capsys, result):
    from app.workspace.data_manager.symbols import Symbols, SymbolsCLI

    list_symbols = Mock(return_value=result)
    monkeypatch.setattr(Symbols, "list", list_symbols)
    health = Mock()
    monkeypatch.setattr(cli, "health", health)
    shutdown = Mock()
    monkeypatch.setattr(cli, "shutdown_logging", shutdown)

    assert cli.main(["data-manager", "symbol", "list"]) == (
        0 if result["success"] else 1
    )
    output = capsys.readouterr().out
    if result["success"]:
        assert "Page 1 of 1" in output
        assert SymbolsCLI.format_symbol_table(result, limit=None) + "\n" in output
    else:
        assert json.loads(output) == result
    list_symbols.assert_called_once_with()
    health.assert_not_called()
    shutdown.assert_called_once_with()


@pytest.mark.parametrize(
    "page,size,first,last",
    [(1, 50, 0, 49), (2, 50, 50, 99), (3, 50, 100, 104), (2, 10, 10, 19)],
)
def test_symbol_list_pagination(monkeypatch, capsys, *, page, size, first, last):
    from app.workspace.data_manager.symbols import Symbols

    symbols = [{"name": f"TEST{i:03d}"} for i in range(105)]
    monkeypatch.setattr(
        Symbols, "list", Mock(return_value={"success": True, "data": symbols})
    )
    monkeypatch.setattr(cli, "shutdown_logging", Mock())
    assert (
        cli.main(
            [
                "data-manager",
                "symbol",
                "list",
                "--page",
                str(page),
                "--page-size",
                str(size),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert f"Symbols {first + 1}-{last + 1} of 105" in output
    for index in range(105):
        assert (f"TEST{index:03d}" in output) == (first <= index <= last)


@pytest.mark.parametrize(
    "option,value",
    [("--page", "0"), ("--page-size", "-1"), ("--page", "abc"), ("--page", "2")],
)
def test_symbol_list_invalid_page(monkeypatch, capsys, option, value):
    from app.workspace.data_manager.symbols import Symbols

    monkeypatch.setattr(
        Symbols, "list", Mock(return_value={"success": True, "data": []})
    )
    monkeypatch.setattr(cli, "shutdown_logging", Mock())
    with pytest.raises(SystemExit) as error:
        cli.main(["data-manager", "symbol", "list", option, value])
    assert error.value.code == 2
    assert capsys.readouterr().out == ""


@pytest.fixture
def session_gateway(tmp_path, monkeypatch):
    path = tmp_path / "cli.db"
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("""
            CREATE TABLE host_session (
                session_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL, peer_id TEXT NOT NULL,
                created_at_utc TEXT NOT NULL, expires_at_utc TEXT NOT NULL,
                revoked_at_utc TEXT, status TEXT NOT NULL
            )
        """)
    settings = Mock()
    settings.get_scope.return_value = {
        "username": "tester",
        "password_hash": SessionManager.hash_password("password"),
    }
    monkeypatch.setattr(cli, "SettingsManager", Mock(return_value=settings))
    return HostPersistence(path)


def test_cli_session_lifecycle_and_channel_binding(session_gateway):
    gateway = session_gateway
    response = cli.login("tester", "password", gateway)
    assert response["success"]
    token = response["data"]["token"]
    row = gateway.read_records("host_session")["data"]["records"][0]
    assert row["peer_id"] == "cli"
    assert token not in str(row)
    assert cli.health(gateway, token=token)["success"]
    ui_token = SessionManager(gateway).create_session("tester", "ui:browser")
    assert not cli.health(gateway, token=ui_token)["success"]
    assert not cli.logout(ui_token, gateway)["success"]
    assert cli.logout(token, gateway)["success"]
    assert not cli.health(gateway, token=token)["success"]
    assert SessionManager(gateway).validate_session(ui_token, "ui:browser") is not None


def test_invalid_credentials_do_not_create_session(session_gateway):
    response = cli.login("tester", "wrong", session_gateway)
    assert response["error"]["code"] == "unauthorized"
    assert session_gateway.read_records("host_session")["data"]["records"] == []


def test_login_prompts_and_logout_uses_environment(monkeypatch, capsys):
    monkeypatch.setattr(cli, "shutdown_logging", Mock())
    prompt = Mock(return_value="password")
    monkeypatch.setattr(cli.getpass, "getpass", prompt)
    login = Mock(return_value={"success": True})
    monkeypatch.setattr(cli, "login", login)
    assert cli.main(["login", "--username", "tester"]) == 0
    prompt.assert_called_once_with("Password: ")
    login.assert_called_once_with("tester", "password")
    monkeypatch.setenv("HARUQUANTAI_SESSION_TOKEN", "test-token")
    logout = Mock(return_value={"success": True})
    monkeypatch.setattr(cli, "logout", logout)
    assert cli.main(["logout"]) == 0
    logout.assert_called_once_with("test-token")
    assert "password" not in capsys.readouterr().out

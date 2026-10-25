"""Headless command output and failure behavior."""

import json
import sqlite3
from contextlib import closing
from unittest.mock import Mock

import pytest
from app import cli
from app.host.persistence import HostPersistence
from app.host.session import SessionManager


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


@pytest.mark.parametrize("arguments", [[], ["unknown"]])
def test_invalid_commands_do_not_run_health(monkeypatch, arguments):
    health = Mock()
    monkeypatch.setattr(cli, "health", health)
    monkeypatch.setattr(cli, "shutdown_logging", Mock())
    with pytest.raises(SystemExit) as error:
        cli.main(arguments)
    assert error.value.code == 2
    health.assert_not_called()


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

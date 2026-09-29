"""Unit checks for CLI transport policy and safe result handling.

HTTP and initialization calls are replaced by explicit doubles. These tests
exercise rejected URLs, absent workspace providers, output shape, and response
bounds without connecting to a live host or opening the shared database.
"""

import json
from unittest.mock import MagicMock

import pytest
from app.cli import Client, ClientError, main


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp",
        "http://example.com",
        "http://user:password@localhost",  # pragma: allowlist secret -- dummy rejection fixture
    ],
)
def test_client_rejects_unsafe_transport(url):
    """Reject unsupported schemes, remote plaintext HTTP, and embedded credentials."""
    with pytest.raises(ClientError):
        Client(url)


def test_cli_unavailable_workspace_fails(monkeypatch):
    """Return failure when initialization finds no available requested workspace."""
    monkeypatch.setattr(
        Client, "initialize", lambda *args, **kwargs: {"catalog": {"domains": []}}
    )
    assert main(["--page=builder"]) == 1


def test_cli_login_output(monkeypatch, capsys):
    """Emit a machine-readable ready result for successful login-only initialization."""
    monkeypatch.setattr(
        Client, "initialize", lambda *args, **kwargs: {"catalog": {"domains": []}}
    )
    assert main(["--json"]) == 0
    assert json.loads(capsys.readouterr().out)["ready"]


def test_http_client_bounds_and_errors(monkeypatch):
    """Unwrap successful data and reject error envelopes or oversized responses."""
    mock = MagicMock()
    mock.__enter__.return_value = mock
    monkeypatch.setattr("app.cli.urlopen", lambda *args, **kwargs: mock)
    client = Client("http://127.0.0.1")
    mock.read.return_value = b'{"status":"success","data":{"ok":true}}'
    assert client.request("/status") == {"ok": True}
    mock.read.return_value = b'{"status":"error"}'
    with pytest.raises(ClientError):
        client.request("/status")
    mock.read.return_value = b"x" * 1048577
    with pytest.raises(ClientError):
        client.request("/status")


@pytest.mark.parametrize("version", [None, 1, 3, "2"])
def test_cli_rejects_incompatible_boot_versions(version):
    with pytest.raises(ClientError, match="Incompatible host boot schema"):
        Client._boot({"schema_version": version, "state": "SERVER_READY"})


def test_cli_rejects_malformed_version_two_snapshot():
    with pytest.raises(ClientError, match="Invalid host boot snapshot"):
        Client._boot({"schema_version": 2, "state": "STANDBY"})


def test_cli_initialization_has_no_restoration_wait(monkeypatch):
    from io import StringIO

    from app.host.events import EventBus
    from app.host.startup import Startup

    startup = Startup(EventBus())
    startup.listening()
    boot = startup.snapshot().model_dump(mode="json")
    transport = MagicMock()
    transport.__enter__.return_value = transport
    transport.recv.return_value = json.dumps({"type": "snapshot", "boot": boot})
    monkeypatch.setattr("app.cli.connect", lambda *args, **kwargs: transport)
    client = Client("http://127.0.0.1")
    request = MagicMock(
        side_effect=[
            {"token": "test-session"},
            {"boot": boot, "catalog": {}},
            {"acknowledged": True},
            {"boot": boot},
        ]
    )
    monkeypatch.setattr(client, "request", request)
    result = client.initialize("operator", None, output=StringIO())
    assert result["boot"]["state"] == "SERVER_READY"
    assert [call.args[0] for call in request.call_args_list] == [
        "/auth/login",
        "/init-data",
        "/app-loaded",
        "/status",
    ]
    assert transport.recv.call_count == 1
    transport.__exit__.assert_called_once()

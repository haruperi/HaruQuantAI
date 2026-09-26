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

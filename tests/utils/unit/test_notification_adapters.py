"""Mocked unit coverage for notification transport adapters."""

from __future__ import annotations

import smtplib
import subprocess
from typing import Any, ClassVar, Self

import pytest
from app.utils.errors.exceptions import ConfigurationError
from app.utils.notifications.desktop import (
    DesktopNotifier,
    _desktop_command,
    build_desktop_notification_config,
)
from app.utils.notifications.email import (
    EmailNotifier,
    build_email_notification_config,
)
from app.utils.notifications.sms import SMSNotifier, build_sms_notification_config
from app.utils.notifications.telegram import (
    TelegramNotifier,
    build_telegram_notification_config,
)


class _Response:
    """Context-managed fake HTTP response."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class _SMTP:
    """Context-managed fake SMTP client."""

    refused: ClassVar[dict[str, object]] = {}
    failure: ClassVar[Exception | None] = None
    started_tls: ClassVar[bool] = False
    logged_in: ClassVar[bool] = False

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        if self.failure is not None:
            raise self.failure

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def starttls(self, **_kwargs: object) -> None:
        type(self).started_tls = True

    def login(self, *_args: object) -> None:
        type(self).logged_in = True

    def send_message(self, _message: object) -> dict[str, object]:
        return self.refused


@pytest.mark.parametrize("system", ["Windows", "Darwin", "Linux"])
def test_desktop_commands_and_success(
    monkeypatch: pytest.MonkeyPatch, system: str
) -> None:
    """Cover every supported OS command and successful subprocess delivery."""
    monkeypatch.setattr(
        "app.utils.notifications.desktop.platform.system", lambda: system
    )
    observed: list[list[str]] = []

    def runner(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.append(args)
        return subprocess.CompletedProcess(args, 0)

    config = build_desktop_notification_config(enabled=True)
    result = DesktopNotifier(config, runner).send("Title", "Message")  # type: ignore[arg-type]

    assert result["status"] == "accepted"
    assert observed[0] == _desktop_command(system, "Title", "Message")


def test_desktop_rejects_invalid_and_failed_delivery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover desktop validation, unsupported OS, and process failure."""
    with pytest.raises(ConfigurationError):
        build_desktop_notification_config(timeout_seconds=0)
    with pytest.raises(ConfigurationError):
        _desktop_command("Linux", "", "message")
    with pytest.raises(ConfigurationError):
        _desktop_command("Other", "title", "message")
    monkeypatch.setattr(
        "app.utils.notifications.desktop.platform.system", lambda: "Linux"
    )
    config = build_desktop_notification_config(enabled=True)
    notifier = DesktopNotifier(
        config,
        lambda args, **_kwargs: subprocess.CompletedProcess(args, 1),  # type: ignore[arg-type]
    )
    with pytest.raises(ConfigurationError):
        notifier.send("title", "message")


def test_email_starttls_auth_success_and_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover SMTP assembly, TLS, authentication, refusal, and connection error."""
    monkeypatch.setattr(smtplib, "SMTP", _SMTP)
    config = build_email_notification_config(
        host="smtp.example.test",
        port=587,
        sender="sender@example.test",
        recipients=("team@example.test",),
        username="user",
        password="secret",  # pragma: allowlist secret
        enabled=True,
    )
    assert EmailNotifier(config).send("Title", "Text", "<p>Text</p>")["recipients"] == 1  # type: ignore[arg-type]
    assert _SMTP.started_tls
    assert _SMTP.logged_in
    _SMTP.refused = {"team@example.test": object()}
    with pytest.raises(ConfigurationError):
        EmailNotifier(config).send("Title", "Text")  # type: ignore[arg-type]
    _SMTP.refused = {}
    _SMTP.failure = smtplib.SMTPException("offline")
    with pytest.raises(ConfigurationError):
        EmailNotifier(config).send("Title", "Text")  # type: ignore[arg-type]
    _SMTP.failure = None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"host": "", "port": 25, "sender": "a@b", "recipients": ("c@d",)},
        {"host": "smtp", "port": 0, "sender": "a@b", "recipients": ("c@d",)},
        {"host": "smtp", "port": 25, "sender": "a@b", "recipients": ()},
    ],
)
def test_email_rejects_invalid_config(kwargs: dict[str, Any]) -> None:
    """Cover malformed SMTP configuration rejection."""
    with pytest.raises(ConfigurationError):
        build_email_notification_config(**kwargs)


def test_telegram_success_provider_failure_and_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover Telegram success, negative acknowledgement, and unknown outcome."""
    config = build_telegram_notification_config(
        bot_token="token", chat_ids=("1", "2"), enabled=True
    )
    requests: list[object] = []

    def successful_urlopen(request: object, **_kwargs: object) -> _Response:
        requests.append(request)
        return _Response(b'{"ok": true}')

    monkeypatch.setattr(
        "app.utils.notifications.telegram.urllib.request.urlopen",
        successful_urlopen,
    )
    assert (
        TelegramNotifier(config).send("A < B", "Text & value", "<p>bad</p>")[
            "recipients"
        ]
        == 2
    )  # type: ignore[arg-type]
    payload = requests[0].data.decode()  # type: ignore[union-attr]
    assert "&lt;" in payload
    assert "&amp;" in payload
    assert "<p>" not in payload
    monkeypatch.setattr(
        "app.utils.notifications.telegram.urllib.request.urlopen",
        lambda *_args, **_kwargs: _Response(b'{"ok": false}'),
    )
    with pytest.raises(ConfigurationError):
        TelegramNotifier(config).send("Title", "Text")  # type: ignore[arg-type]
    monkeypatch.setattr(
        "app.utils.notifications.telegram.urllib.request.urlopen",
        lambda *_args, **_kwargs: _Response(b"not-json"),
    )
    with pytest.raises(ConfigurationError):
        TelegramNotifier(config).send("Title", "Text")  # type: ignore[arg-type]


def test_sms_success_provider_failure_and_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover Twilio success, invalid response, and malformed configuration."""
    config = build_sms_notification_config(
        account_sid="AC123",
        auth_token="secret",
        from_phone="+10000000000",
        recipients=("+12222222222",),
        enabled=True,
    )
    monkeypatch.setattr(
        "app.utils.notifications.sms.urllib.request.urlopen",
        lambda *_args, **_kwargs: _Response(b'{"sid": "SM123"}'),
    )
    assert SMSNotifier(config).send("Title", "Text")["recipients"] == 1  # type: ignore[arg-type]
    monkeypatch.setattr(
        "app.utils.notifications.sms.urllib.request.urlopen",
        lambda *_args, **_kwargs: _Response(b'{"sid": "bad"}'),
    )
    with pytest.raises(ConfigurationError):
        SMSNotifier(config).send("Title", "Text")  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError):
        build_sms_notification_config(
            account_sid="bad",
            auth_token="",
            from_phone="bad",
            recipients=("bad",),
        )

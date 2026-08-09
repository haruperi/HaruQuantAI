"""Real non-production notification usage composition."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from app.services.api import (  # noqa: E402
    get_api_settings,
    get_system_settings,
    resolve_system_credential_slot,
)
from app.utils import (  # noqa: E402
    build_desktop_notification_config,
    build_email_notification_config,
    build_notification_manager_config,
    build_sms_notification_config,
    build_telegram_notification_config,
    create_notification_manager,
    generate_id,
    render_notification_template,
    send_notification,
)
from pydantic import SecretStr  # noqa: E402

_TRUE = frozenset({"1", "true", "yes", "on"})
_SAFE_ENVIRONMENTS = frozenset({"dev", "development", "test", "sandbox", "paper"})


def run_real_notification_evidence(evidence_name: str) -> Mapping[str, object]:
    """Send one bounded real test message through every enabled channel.

    Args:
        evidence_name: Secret-safe label identifying the evidence program.

    Returns:
        Secret-safe aggregate delivery result.

    Raises:
        RuntimeError: If environment, settings, credentials, or destinations are unsafe.
    """
    bootstrap = get_api_settings()
    environment = str(bootstrap.environment).strip().lower()
    if environment not in _SAFE_ENVIRONMENTS:
        raise RuntimeError(
            "real notification evidence requires a non-production environment"
        )
    request_id = generate_id("req")
    record = get_system_settings(request_id=request_id)
    settings = record.settings
    if not _enabled(settings, "NOTIFICATIONS_ENABLED"):
        raise RuntimeError("NOTIFICATIONS_ENABLED is not active")
    channels = tuple(
        channel
        for channel in ("desktop", "email", "telegram", "sms")
        if _enabled(settings, f"{channel.upper()}_NOTIFICATIONS_ENABLED")
    )
    if not channels:
        raise RuntimeError("no notification channel is enabled")
    timeout = float(settings.get("NOTIFICATION_TIMEOUT_SECONDS", "10"))
    channel_configs: dict[str, object] = {}
    if "desktop" in channels:
        channel_configs["desktop_config"] = build_desktop_notification_config(
            enabled=True, timeout_seconds=min(timeout, 30.0)
        )
    if "email" in channels:
        credential = _credential("smtp", request_id)
        recipients = _split(_secret(credential, "recipient_emails"))
        channel_configs["email_config"] = build_email_notification_config(
            host=_required(settings, "SMTP_HOST"),
            port=int(_required(settings, "SMTP_PORT")),
            tls_mode=settings.get("SMTP_TLS_MODE", "starttls"),
            username=_optional_secret(credential, "username"),
            password=_optional_secret(credential, "password"),
            sender=_secret(credential, "sender_email"),
            recipients=recipients,
            enabled=True,
            timeout_seconds=timeout,
        )
    if "telegram" in channels:
        credential = _credential("telegram", request_id)
        chat_ids = _split(
            _optional_secret(credential, "chat_ids") or _secret(credential, "chat_id")
        )
        channel_configs["telegram_config"] = build_telegram_notification_config(
            bot_token=_secret(credential, "bot_token"),
            chat_ids=chat_ids,
            enabled=True,
            timeout_seconds=timeout,
        )
    if "sms" in channels:
        credential = _credential("twilio", request_id)
        channel_configs["sms_config"] = build_sms_notification_config(
            account_sid=_secret(credential, "account_sid"),
            auth_token=_secret(credential, "auth_token"),
            from_phone=_secret(credential, "from_phone"),
            recipients=_split(_secret(credential, "recipient_phones")),
            enabled=True,
            timeout_seconds=timeout,
        )
    manager = create_notification_manager(
        build_notification_manager_config(
            enabled=True,
            default_channels=channels,
            rate_limit=int(settings.get("NOTIFICATION_RATE_LIMIT", "10")),
            rate_window_seconds=float(
                settings.get("NOTIFICATION_RATE_WINDOW_SECONDS", "60")
            ),
        ),
        **channel_configs,
    )
    rendered = render_notification_template(
        manager,
        "test_message",
        {
            "service": evidence_name,
            "timestamp": "runtime-generated",
            "status": "non-production delivery test",
        },
    )
    return send_notification(
        manager,
        rendered["title"],
        rendered["text"],
        html_body=rendered["html"],
    )


def _enabled(settings: Mapping[str, str], key: str) -> bool:
    """Return whether one persisted boolean setting is explicitly true."""
    return settings.get(key, "false").strip().lower() in _TRUE


def _required(settings: Mapping[str, str], key: str) -> str:
    """Return one required non-secret setting."""
    value = settings.get(key, "").strip()
    if not value:
        raise RuntimeError(f"required notification setting is missing: {key}")
    return value


def _credential(slot: str, request_id: str) -> Mapping[str, SecretStr]:
    """Resolve one encrypted credential without exposing its values."""
    value = resolve_system_credential_slot(slot, request_id=request_id)
    if not isinstance(value, Mapping):
        raise TypeError("credential resolution returned an invalid contract")
    return value  # type: ignore[return-value]


def _secret(values: Mapping[str, SecretStr], key: str) -> str:
    """Return one required in-memory secret for immediate composition."""
    value = values.get(key)
    if value is None or not value.get_secret_value().strip():
        raise RuntimeError(f"required credential field is missing: {key}")
    return value.get_secret_value()


def _optional_secret(values: Mapping[str, SecretStr], key: str) -> str | None:
    """Return one optional in-memory secret."""
    value = values.get(key)
    return value.get_secret_value() if value is not None else None


def _split(value: str) -> tuple[str, ...]:
    """Split a comma-delimited destination list without displaying it."""
    result = tuple(item.strip() for item in value.split(",") if item.strip())
    if not result:
        raise RuntimeError("notification destination list is empty")
    return result


__all__ = ("run_real_notification_evidence",)

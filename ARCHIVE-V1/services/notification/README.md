# Notification Service (`app/services/notification`)

## Overview
The Notification Service is a unified orchestration system for sending alerts and messages to developers, administrators, and trading teams. It supports Desktop, Telegram, Email, and SMS notifications. The service is fully integrated with `app.services.utils.settings.settings` and standardizes AI tool interfaces to return correct standard response envelopes.

## Design Philosophy & Non-Negotiable Rules
* **Rule 1 (Fallback to Settings):** When no configuration is explicitly provided, the system automatically falls back to settings loaded via `get_settings()` to initialize SMTP and Telegram bot configurations.
* **Rule 2 (Thread-safe Managers):** All notifier engines are initialized once in a thread-safe `NotificationManager` session.
* **Rule 3 (Unified Entry Point):** External callers must only import from the package root `app.services.notification`. Bypassing the entry point is strictly prohibited.

## Features

### `desktop.py` — Desktop Notifier
Triggers OS-native alerts using PowerShell BalloonTips on Windows, AppleScript on macOS, or `notify-send` on Linux.
**Key exports:** `DesktopNotifier`, `DesktopConfig`

### `email.py` — SMTP Email Notifier
Dispatches HTML and plain text emails using standard Python `smtplib` configurations.
**Key exports:** `EmailNotifier`, `EmailConfig`

### `telegram.py` — Telegram Bot Notifier
Routes formatted HTML notifications to one or more user/channel chat IDs via the Telegram API.
**Key exports:** `TelegramNotifier`, `TelegramConfig`

### `sms.py` — Twilio SMS Notifier
Queues short warning alerts to recipient mobile numbers via the Twilio SMS Gateway.
**Key exports:** `SMSNotifier`, `SMSConfig`

### `manager.py` — Notification Manager
A unified wrapper orchestrating notifier registration, active status checks, and rate-limiting limits.
**Key exports:** `NotificationManager`, `NotificationManagerConfig`

### `tools.py` — AI Tools Wrapper
Agent-facing tools returning standard envelope schemas.
**Key exports:** `build_notification_message`, `send_custom_notification`, `send_trading_notification`, `send_system_notification`, `send_position_notification`, `send_error_notification`, `validate_notification_config`, `build_notification_manager_config`, `create_notification_manager`, `get_notification_service_status`, `render_notification_template`

## Installation
### Prerequisites
* `uv` installed and available globally.

### Dependencies
* **Standard Library:** `subprocess`, `smtplib`, `ssl`, `urllib`, `dataclasses`, `time`, `sys`
* **Required Third-Party:** `requests`, `pydantic`

## Usage Examples

### Basic Usage
```python
from app.services.notification import send_custom_notification

result = send_custom_notification(
    title="Health Check",
    body="Notification service is up.",
    level="INFO"
)
print(result["status"])  # "success"
```

### Sending Trading Alerts
```python
from app.services.notification import send_trading_notification

result = send_trading_notification(
    symbol="EURUSD",
    action="BUY",
    price=1.1045,
    reason="RSI Oversold"
)
```

## API Reference

### `send_custom_notification(title: str, body: str, level: str = "INFO", request_id: str | None = None) -> dict`
Sends an ad hoc alert through all enabled channels.

**Parameters:**
* `title` (str): Non-empty title header.
* `body` (str): Alert details text.
* `level` (str): Priority tier ("INFO", "WARNING", "ERROR", etc.)
* `request_id` (str | None): Workflow tracking trace ID.

**Returns:**
* `dict`: Standard response envelope.

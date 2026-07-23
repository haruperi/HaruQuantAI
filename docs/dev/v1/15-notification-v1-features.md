## FEAT-NOTI-01: Base classes and interfaces for notification tools (app.services.notification.base)

| Function | Purpose |
|----------|---------|
| `NotificationLevel` (model) | Notification priority levels. |
| `NotificationError.__init__(*args, **kwargs) -> None` | Initialize the exception. |
| `NotificationMessage` (model) | Represents a notification message with metadata. |
| `NotificationResult` (model) | Result of a notification attempt. |
| `RateLimiter.__init__(max_requests: int = 10, time_window: int = 60) -> None` | Initialize rate limiter. |
| `RateLimiter.can_send() -> bool` | Check if a notification can be sent based on rate limits. |
| `RateLimiter.get_wait_time() -> int` | Get the number of seconds to wait before next request. |
| `BaseNotifier.__init__(name: str, rate_limit: RateLimiter \| None = None) -> None` | Initialize base notifier. |
| `BaseNotifier.send(message: NotificationMessage) -> NotificationResult` | Send a notification message. |
| `BaseNotifier.test_connection() -> bool` | Test the connection to the notification service. |
| `BaseNotifier.send_message(message: NotificationMessage) -> NotificationResult` | Public method to send a message with retry logic. |
| `BaseNotifier.enable() -> None` | Enable the notifier. |
| `BaseNotifier.disable() -> None` | Disable the notifier. |
| `BaseNotifier.is_enabled() -> bool` | Check if notifier is enabled. |
| `NotificationTemplate.__init__() -> None` | Initialize the notification template system. |
| `NotificationTemplate.get_template(template_name: str) -> dict[str, str]` | Get a template by name. |
| `NotificationTemplate.render(template_name: str, **kwargs) -> NotificationMessage` | Render a template with provided variables. |
| `NotificationTemplate.add_template(name: str, title_template: str, body_template: str) -> None` | Add a new template. |
| `NotificationTemplate.list_templates() -> list[str]` | List all available template names. |


## FEAT-NOTI-02: Configuration management for notification tools (app.services.notification.config)

| Function | Purpose |
|----------|---------|
| `NotificationConfig.from_ini(config_file: str = 'config.ini') -> 'NotificationConfig'` | Create configuration from INI file. |
| `NotificationConfig.from_env() -> 'NotificationConfig'` | Create configuration from environment variables (fallback method). |
| `NotificationConfig.from_file(file_path: str) -> 'NotificationConfig'` | Create configuration from JSON file. |
| `NotificationConfig.from_settings(settings: Any = None) -> 'NotificationConfig'` | Create configuration from a Settings instance or lazy-loaded settings. |
| `NotificationConfig.save_to_file(file_path: str) -> None` | Save configuration to JSON file. |
| `NotificationConfig.validate() -> list[str]` | Validate configuration and return list of errors. |
| `NotificationConfig.get_email_config() -> EmailConfig \| None` | Get email configuration if enabled. |
| `NotificationConfig.get_telegram_config() -> TelegramConfig \| None` | Get Telegram configuration if enabled. |
| `NotificationConfig.get_sms_config() -> SMSConfig \| None` | Get SMS configuration if enabled. |
| `NotificationConfig.get_desktop_config() -> DesktopConfig \| None` | Get desktop configuration if enabled. |
| `NotificationConfig.get_default_levels() -> list[NotificationLevel]` | Get default notification levels. |
| `NotificationConfig.is_any_service_enabled() -> bool` | Check if any notification service is enabled. |
| `NotificationConfig.get_enabled_services() -> list[str]` | Get list of enabled service names. |
| `NotificationConfig.print_configuration(show_passwords: bool = False) -> None` | Print current configuration (for debugging). |
| `NotificationPresets.development() -> NotificationConfig` | Development configuration with minimal notifications. |
| `NotificationPresets.production() -> NotificationConfig` | Production configuration with all services enabled. |
| `NotificationPresets.gmail_setup(email: str, password: str, recipients: list[str]) -> NotificationConfig` | Create configuration with Gmail setup. |
| `NotificationPresets.telegram_setup(bot_token: str, chat_ids: list[str]) -> NotificationConfig` | Create configuration with Telegram setup. |
| `NotificationPresets.twilio_setup(account_sid: str, auth_token: str, from_number: str, recipients: list[str]) -> NotificationConfig` | Create configuration with Twilio SMS setup. |


## FEAT-NOTI-03: Desktop notification service using powershell, osascript, or notify-send (app.services.notification.desktop)

| Function | Purpose |
|----------|---------|
| `DesktopConfig` (model) | Configuration for Desktop notification service. |
| `DesktopNotifier.__init__(config: DesktopConfig, rate_limit: RateLimiter \| None = None) -> None` | Initialize Desktop notifier. |
| `DesktopNotifier.send(message: NotificationMessage) -> NotificationResult` | Send a native desktop notification to the host operating system. |
| `DesktopNotifier.test_connection() -> bool` | Test desktop notification connection. |


## FEAT-NOTI-04: Email notification service using SMTP (app.services.notification.email)

| Function | Purpose |
|----------|---------|
| `EmailConfig` (model) | Configuration for email notification service. |
| `EmailNotifier.__init__(config: EmailConfig, rate_limit=None) -> None` | Initialize email notifier. |
| `EmailNotifier.send(message: NotificationMessage) -> NotificationResult` | Send email notification. |
| `EmailNotifier.test_connection() -> bool` | Test SMTP connection. |
| `EmailNotifier.send_test_email(recipient: str) -> NotificationResult` | Send a test email to verify configuration. |
| `EmailProviders.gmail(username: str, password: str, app_password: str \| None = None) -> EmailConfig` | Gmail configuration. |
| `EmailProviders.outlook(username: str, password: str) -> EmailConfig` | Outlook/Hotmail configuration. |
| `EmailProviders.yahoo(username: str, password: str, app_password: str \| None = None) -> EmailConfig` | Yahoo Mail configuration. |
| `EmailProviders.custom(smtp_server: str, smtp_port: int, username: str, password: str, use_tls: bool = True, use_ssl: bool = False) -> EmailConfig` | Create custom SMTP server configuration. |


## FEAT-NOTI-05: Notification Manager (app.services.notification.manager)

| Function | Purpose |
|----------|---------|
| `NotificationManagerConfig` (model) | Configuration for notification manager. |
| `NotificationManager.__init__(config: NotificationManagerConfig \| None = None) -> None` | Initialize notification manager. |
| `NotificationManager.send_notification(message: NotificationMessage, services: list[str] \| None = None) -> dict[str, NotificationResult]` | Send notification through specified tools. |
| `NotificationManager.send_trading_alert(symbol: str, action: str, price: float, reason: str, account: str = 'Demo', strategy: str = 'Unknown', risk_level: str = 'Medium', services: list[str] \| None = None) -> dict[str, NotificationResult]` | Send trading alert notification. |
| `NotificationManager.send_system_alert(level: str \| NotificationLevel, message: str, details: str = '', component: str = 'System', status: str = 'Active', services: list[str] \| None = None) -> dict[str, NotificationResult]` | Send system alert notification. |
| `NotificationManager.send_position_update(symbol: str, position_type: str, size: float, entry_price: float, current_price: float, pnl: float, pnl_percent: float, services: list[str] \| None = None) -> dict[str, NotificationResult]` | Send position update notification. |
| `NotificationManager.send_error_alert(error_type: str, message: str, component: str = 'Unknown', stack_trace: str = '', services: list[str] \| None = None) -> dict[str, NotificationResult]` | Send error alert notification. |
| `NotificationManager.send_custom_message(title: str, body: str, level: str \| NotificationLevel = 'INFO', metadata: dict[str, Any] \| None = None, recipients: list[str] \| None = None, services: list[str] \| None = None) -> dict[str, NotificationResult]` | Send custom notification message. |
| `NotificationManager.test_all_services() -> dict[str, bool]` | Test all notification tools. |
| `NotificationManager.enable_service(service_name: str) -> None` | Enable a specific notification service. |
| `NotificationManager.disable_service(service_name: str) -> None` | Disable a specific notification service. |
| `NotificationManager.get_service_status() -> dict[str, dict[str, Any]]` | Get status of all notification tools. |
| `NotificationManager.get_statistics() -> dict[str, Any]` | Get notification statistics. |
| `NotificationManager.reset_statistics() -> None` | Reset notification statistics. |
| `NotificationManager.add_template(name: str, title_template: str, body_template: str) -> None` | Add a new notification template. |
| `NotificationManager.list_templates() -> list[str]` | List all available templates. |
| `NotificationManager.list_services() -> list[str]` | List all available notification tools. |
| `NotificationManager.get_notifier(service_name: str) -> BaseNotifier \| None` | Get a specific notifier by name. |


## FEAT-NOTI-06: SMS notification service using Twilio (app.services.notification.sms)

| Function | Purpose |
|----------|---------|
| `SMSConfig` (model) | Configuration for SMS notification service. |
| `SMSNotifier.__init__(config: SMSConfig, rate_limit=None) -> None` | Initialize SMS notifier. |
| `SMSNotifier.send(message: NotificationMessage) -> NotificationResult` | Send SMS notification. |
| `SMSNotifier.test_connection() -> bool` | Test Twilio connection. |
| `SMSNotifier.get_account_info() -> dict[str, Any] \| None` | Get Twilio account information. |
| `SMSNotifier.send_test_sms(phone_number: str) -> NotificationResult` | Send a test SMS to verify configuration. |
| `SMSNotifier.get_message_status(message_sid: str) -> dict[str, Any] \| None` | Get the status of a sent message. |
| `SMSNotifier.get_message_history(limit: int = 50) -> list[dict[str, Any]]` | Get recent message history. |
| `SMSNotifier.validate_phone_number(phone_number: str) -> dict[str, Any] \| None` | Validate a phone number using Twilio's Lookup API. |


## FEAT-NOTI-07: Telegram bot notification service (app.services.notification.telegram)

| Function | Purpose |
|----------|---------|
| `TelegramConfig` (model) | Configuration for Telegram notification service. |
| `TelegramNotifier.__init__(config: TelegramConfig, rate_limit=None) -> None` | Initialize Telegram notifier. |
| `TelegramNotifier.send(message: NotificationMessage) -> NotificationResult` | Send Telegram notification. |
| `TelegramNotifier.test_connection() -> bool` | Test Telegram bot connection. |
| `TelegramNotifier.get_chat_info(chat_id: str) -> dict[str, Any] \| None` | Get information about a chat. |
| `TelegramNotifier.send_test_message(chat_id: str) -> NotificationResult` | Send a test message to verify configuration. |
| `TelegramNotifier.send_photo(chat_id: str, photo_path: str, caption: str = '') -> NotificationResult` | Send a photo with optional caption. |
| `TelegramNotifier.send_document(chat_id: str, document_path: str, caption: str = '') -> NotificationResult` | Send a document with optional caption. |
| `TelegramNotifier.get_updates(offset: int \| None = None, limit: int = 100) -> list[dict[str, Any]]` | Get updates from Telegram (useful for getting chat IDs). |


## FEAT-NOTI-08: Notification templates for different types of alerts and messages (app.services.notification.templates)

| Function | Purpose |
|----------|---------|
| `NotificationTemplate.__init__() -> None` | Initialize with default templates. |
| `NotificationTemplate.get_template(template_name: str) -> dict[str, str]` | Get a template by name. |
| `NotificationTemplate.render(template_name: str, **kwargs) -> NotificationMessage` | Render a template with provided variables. |
| `NotificationTemplate.add_template(name: str, title_template: str, body_template: str) -> None` | Add a new template. |
| `NotificationTemplate.update_template(name: str, title_template: str \| None = None, body_template: str \| None = None) -> None` | Update an existing template. |
| `NotificationTemplate.remove_template(name: str) -> None` | Remove a template. |
| `NotificationTemplate.list_templates() -> list[str]` | List all available template names. |
| `NotificationTemplate.get_template_variables(template_name: str) -> list[str]` | Get list of variables required by a template. |
| `NotificationTemplate.validate_template(template_name: str, **kwargs) -> list[str]` | Validate that all required variables are provided. |
| `NotificationTemplate.preview_template(template_name: str, **kwargs) -> str` | Preview a template without creating a NotificationMessage. |
| `NotificationTemplate.export_templates() -> dict[str, dict[str, str]]` | Export all templates for backup or sharing. |
| `NotificationTemplate.import_templates(templates: dict[str, dict[str, str]], overwrite: bool = False) -> None` | Import templates from a dictionary. |
| `NotificationTemplate.get_template_info(template_name: str) -> dict[str, Any]` | Get detailed information about a template. |


## FEAT-NOTI-09: Agent-facing notification tools (app.services.notification.tools)

| Function | Purpose |
|----------|---------|
| `build_notification_message(*, title: str, body: str, level: str = 'INFO', metadata: dict[str, Any] \| None = None, recipients: list[str] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Build a notification message payload without sending it. |
| `render_notification_template(*, template_name: str, variables: dict[str, Any] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Render a named notification template into a message payload. |
| `validate_notification_config(*, config: dict[str, Any] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Validate notification service configuration without contacting providers. |
| `build_notification_manager_config(*, config: dict[str, Any] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Build manager-level notification configuration from service settings. |
| `create_notification_manager(*, config: dict[str, Any] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Create a notification manager from manager configuration. |
| `get_notification_service_status(*, manager: Any \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Read notification service status from a manager. |
| `send_custom_notification(*, title: str, body: str, level: str = 'INFO', manager: Any \| None = None, services: list[str] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Send a custom notification through configured services. |
| `send_trading_notification(*, symbol: str, action: str, price: float, reason: str, manager: Any \| None = None, services: list[str] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Send a trading alert notification through configured services. |
| `send_system_notification(*, level: str, message: str, details: str = '', component: str = 'System', status: str = 'Active', manager: Any \| None = None, services: list[str] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Send a system alert notification through configured services. |
| `send_position_notification(*, symbol: str, position_type: str, size: float, entry_price: float, current_price: float, pnl: float, pnl_percent: float, manager: Any \| None = None, services: list[str] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Send a position update notification through configured services. |
| `send_error_notification(*, error_type: str, message: str, component: str = 'Unknown', stack_trace: str = '', manager: Any \| None = None, services: list[str] \| None = None, request_id: str \| None = None) -> dict[str, Any]` | Send an error alert notification through configured services. |


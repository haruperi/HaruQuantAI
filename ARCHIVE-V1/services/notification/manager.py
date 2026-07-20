"""Notification Manager.

This module provides a unified interface for all notification tools.
It manages multiple notification channels and provides high-level methods for common notification types.

Classes and functions:
    NotificationManagerConfig: Class. Provides NotificationManagerConfig behavior for notification workflows.
    NotificationManager: Class. Provides NotificationManager behavior for notification workflows.
"""

import threading
from dataclasses import dataclass, field
from typing import Any

from app.services.utils.logger import logger

from .base import (
    BaseNotifier,
    NotificationLevel,
    NotificationMessage,
    NotificationResult,
    RateLimiter,
)
from .desktop import DesktopConfig, DesktopNotifier
from .email import EmailConfig, EmailNotifier
from .sms import SMSConfig, SMSNotifier
from .telegram import TelegramConfig, TelegramNotifier
from .templates import NotificationTemplate


@dataclass
class NotificationManagerConfig:
    """Configuration for notification manager."""

    email_config: EmailConfig | None = None
    telegram_config: TelegramConfig | None = None
    sms_config: SMSConfig | None = None
    desktop_config: DesktopConfig | None = None
    default_levels: list[NotificationLevel] = field(default_factory=list)
    enable_all: bool = True

    def __post_init__(self):
        """Set default values after initialization."""
        if not self.default_levels:  # Check if empty, populate default
            self.default_levels = [
                NotificationLevel.WARNING,
                NotificationLevel.ERROR,
                NotificationLevel.CRITICAL,
            ]


class NotificationManager:
    """Unified notification manager for all notification tools."""

    def __init__(self, config: NotificationManagerConfig | None = None):
        """
        Initialize notification manager.

        Args:
            config: Notification manager configuration
        """
        self.config = config or NotificationManagerConfig()
        self.logger = logger.bind(name=__name__)
        self.template = NotificationTemplate()

        # Initialize notifiers
        self.notifiers: dict[str, BaseNotifier] = {}
        self._initialize_notifiers()

        # Statistics
        self.stats: dict[str, Any] = {
            "total_sent": 0,
            "total_failed": 0,
            "by_service": {},
            "by_level": {},
        }
        self._stats_lock = threading.Lock()

    def _initialize_notifiers(self):
        """Initialize all configured notifiers."""
        self._init_email_notifier()
        self._init_telegram_notifier()
        self._init_sms_notifier()
        self._init_desktop_notifier()

        if not self.notifiers:
            self.logger.warning("No notification services configured")

    def _init_email_notifier(self):
        """Initialize email notifier."""
        if self.config.email_config:
            try:
                email_rate_limit = RateLimiter(
                    max_requests=5, time_window=60
                )  # 5 emails per minute
                self.notifiers["email"] = EmailNotifier(
                    self.config.email_config, email_rate_limit
                )
                self.logger.info("Email notifier initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize email notifier: {e!s}")

    def _init_telegram_notifier(self):
        """Initialize Telegram notifier."""
        if self.config.telegram_config:
            try:
                telegram_rate_limit = RateLimiter(
                    max_requests=20, time_window=60
                )  # 20 messages per minute
                self.notifiers["telegram"] = TelegramNotifier(
                    self.config.telegram_config, telegram_rate_limit
                )
                self.logger.info("Telegram notifier initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize telegram notifier: {e!s}")

    def _init_sms_notifier(self):
        """Initialize SMS notifier."""
        if self.config.sms_config:
            try:
                sms_rate_limit = RateLimiter(
                    max_requests=3, time_window=60
                )  # 3 SMS per minute
                self.notifiers["sms"] = SMSNotifier(
                    self.config.sms_config, sms_rate_limit
                )
                self.logger.info("SMS notifier initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize SMS notifier: {e!s}")

    def _init_desktop_notifier(self):
        """Initialize desktop notifier."""
        if self.config.desktop_config:
            try:
                desktop_rate_limit = RateLimiter(
                    max_requests=60, time_window=60
                )  # 60 desktop notifications per minute
                self.notifiers["desktop"] = DesktopNotifier(
                    self.config.desktop_config, desktop_rate_limit
                )
                self.logger.info("Desktop notifier initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize desktop notifier: {e!s}")

    def send_notification(
        self, message: NotificationMessage, services: list[str] | None = None
    ) -> dict[str, NotificationResult]:
        """
        Send notification through specified tools.

        Args:
            message: The notification message to send
            services: List of services to use (email, telegram, sms). If None, uses all enabled tools.

        Returns:
            Dictionary mapping service names to notification results
        """
        if not self.config.enable_all:
            return {}

        # Determine which services to use
        if services is None:
            services = list(self.notifiers.keys())
        else:
            services = [s for s in services if s in self.notifiers]

        if not services:
            self.logger.warning("No valid notification services specified")
            return {}

        # Check if notification level is enabled
        if message.level not in self.config.default_levels:
            self.logger.debug(
                f"Notification level {message.level.value} not in default levels, skipping"
            )
            return {}

        results = {}

        # Send through each service
        for service_name in services:
            if service_name in self.notifiers:
                notifier = self.notifiers[service_name]
                if notifier.is_enabled():
                    try:
                        result = notifier.send_message(message)
                        results[service_name] = result

                        # Update statistics
                        self._update_stats(service_name, message.level, result.success)

                    except Exception as e:
                        self.logger.error(
                            f"Exception sending via {service_name}: {e!s}",
                            exc_info=True,
                        )
                        results[service_name] = NotificationResult(
                            success=False, error_message=str(e)
                        )
                        self._update_stats(service_name, message.level, False)
                else:
                    results[service_name] = NotificationResult(
                        success=False, error_message="Service disabled"
                    )

        return results

    def send_trading_alert(
        self,
        symbol: str,
        action: str,
        price: float,
        reason: str,
        account: str = "Demo",
        strategy: str = "Unknown",
        risk_level: str = "Medium",
        services: list[str] | None = None,
    ) -> dict[str, NotificationResult]:
        """
        Send trading alert notification.

        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            action: Trading action ("BUY", "SELL", "CLOSE")
            price: Entry/exit price
            reason: Reason for the trade
            account: Account name
            strategy: Strategy name
            risk_level: Risk level
            services: List of services to use

        Returns:
            Dictionary mapping service names to notification results
        """
        message = self.template.render(
            "trading_alert",
            symbol=symbol,
            action=action,
            price=f"{price:.5f}",
            reason=reason,
            account=account,
            strategy=strategy,
            risk_level=risk_level,
        )

        return self.send_notification(message, services)

    def send_system_alert(
        self,
        level: str | NotificationLevel,
        message: str,
        details: str = "",
        component: str = "System",
        status: str = "Active",
        services: list[str] | None = None,
    ) -> dict[str, NotificationResult]:
        """
        Send system alert notification.

        Args:
            level: Alert level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Alert message
            details: Additional details
            component: System component
            status: Component status
            services: List of services to use

        Returns:
            Dictionary mapping service names to notification results
        """
        if isinstance(level, str):
            level = NotificationLevel(level)

        notification_message = self.template.render(
            "system_alert",
            level=level.value,
            message=message,
            details=details,
            component=component,
            status=status,
        )
        notification_message.level = level

        return self.send_notification(notification_message, services)

    def send_position_update(
        self,
        symbol: str,
        position_type: str,
        size: float,
        entry_price: float,
        current_price: float,
        pnl: float,
        pnl_percent: float,
        services: list[str] | None = None,
    ) -> dict[str, NotificationResult]:
        """
        Send position update notification.

        Args:
            symbol: Trading symbol
            position_type: Position type ("BUY", "SELL")
            size: Position size
            entry_price: Entry price
            current_price: Current price
            pnl: Profit/Loss
            pnl_percent: Profit/Loss percentage
            services: List of services to use

        Returns:
            Dictionary mapping service names to notification results
        """
        message = self.template.render(
            "position_update",
            symbol=symbol,
            position_type=position_type,
            size=f"{size:.2f}",
            entry_price=f"{entry_price:.5f}",
            current_price=f"{current_price:.5f}",
            pnl=f"{pnl:.2f}",
            pnl_percent=f"{pnl_percent:.2f}%",
        )

        return self.send_notification(message, services)

    def send_error_alert(
        self,
        error_type: str,
        message: str,
        component: str = "Unknown",
        stack_trace: str = "",
        services: list[str] | None = None,
    ) -> dict[str, NotificationResult]:
        """
        Send error alert notification.

        Args:
            error_type: Type of error
            message: Error message
            component: Component where error occurred
            stack_trace: Stack trace (optional)
            services: List of services to use

        Returns:
            Dictionary mapping service names to notification results
        """
        notification_message = self.template.render(
            "error_alert",
            error_type=error_type,
            message=message,
            component=component,
            stack_trace=(
                stack_trace[:500] if stack_trace else "N/A"
            ),  # Limit stack trace length
        )
        notification_message.level = NotificationLevel.ERROR

        return self.send_notification(notification_message, services)

    def send_custom_message(
        self,
        title: str,
        body: str,
        level: str | NotificationLevel = "INFO",
        metadata: dict[str, Any] | None = None,
        recipients: list[str] | None = None,
        services: list[str] | None = None,
    ) -> dict[str, NotificationResult]:
        """
        Send custom notification message.

        Args:
            title: Message title
            body: Message body
            level: Notification level
            metadata: Additional metadata
            recipients: Specific recipients (for services that support it)
            services: List of services to use

        Returns:
            Dictionary mapping service names to notification results
        """
        if isinstance(level, str):
            level = NotificationLevel(level)

        message = NotificationMessage(
            title=title,
            body=body,
            level=level,
            metadata=metadata or {},
            recipients=recipients or [],
        )

        return self.send_notification(message, services)

    def test_all_services(self) -> dict[str, bool]:
        """Test all notification tools."""
        results = {}

        for service_name, notifier in self.notifiers.items():
            try:
                results[service_name] = notifier.test_connection()
                self.logger.info(
                    f"Service {service_name} test: {'PASS' if results[service_name] else 'FAIL'}"
                )
            except Exception as e:
                results[service_name] = False
                self.logger.error(f"Service {service_name} test exception: {e!s}")

        return results

    def enable_service(self, service_name: str):
        """Enable a specific notification service."""
        if service_name in self.notifiers:
            self.notifiers[service_name].enable()
            self.logger.info("Service %s enabled", service_name)
        else:
            self.logger.warning("Service %s not found", service_name)

    def disable_service(self, service_name: str):
        """Disable a specific notification service."""
        if service_name in self.notifiers:
            self.notifiers[service_name].disable()
            self.logger.info("Service %s disabled", service_name)
        else:
            self.logger.warning("Service %s not found", service_name)

    def get_service_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all notification tools."""
        status = {}

        for service_name, notifier in self.notifiers.items():
            status[service_name] = {
                "enabled": notifier.is_enabled(),
                "name": notifier.name,
                "rate_limit": {
                    "max_requests": notifier.rate_limit.max_requests,
                    "time_window": notifier.rate_limit.time_window,
                },
            }

        return status

    def get_statistics(self) -> dict[str, Any]:
        """Get notification statistics."""
        with self._stats_lock:
            return self.stats.copy()

    def _update_stats(self, service: str, level: NotificationLevel, success: bool):
        """Update notification statistics."""
        with self._stats_lock:
            # Update total counts
            if success:
                self.stats["total_sent"] = int(self.stats.get("total_sent", 0)) + 1
            else:
                self.stats["total_failed"] = int(self.stats.get("total_failed", 0)) + 1

            # Update by service
            by_service: dict[str, dict[str, int]] = self.stats.setdefault(
                "by_service", {}
            )
            if service not in by_service:
                by_service[service] = {"sent": 0, "failed": 0}

            if success:
                by_service[service]["sent"] += 1
            else:
                by_service[service]["failed"] += 1

            # Update by level
            level_str = level.value
            by_level: dict[str, dict[str, int]] = self.stats.setdefault("by_level", {})
            if level_str not in by_level:
                by_level[level_str] = {"sent": 0, "failed": 0}

            if success:
                by_level[level_str]["sent"] += 1
            else:
                by_level[level_str]["failed"] += 1

    def reset_statistics(self):
        """Reset notification statistics."""
        with self._stats_lock:
            self.stats = {
                "total_sent": 0,
                "total_failed": 0,
                "by_service": {},
                "by_level": {},
            }
        self.logger.info("Notification statistics reset")

    def add_template(self, name: str, title_template: str, body_template: str):
        """Add a new notification template."""
        self.template.add_template(name, title_template, body_template)

    def list_templates(self) -> list[str]:
        """List all available templates."""
        return self.template.list_templates()

    def list_services(self) -> list[str]:
        """List all available notification tools."""
        return list(self.notifiers.keys())

    def get_notifier(self, service_name: str) -> BaseNotifier | None:
        """Get a specific notifier by name."""
        return self.notifiers.get(service_name)

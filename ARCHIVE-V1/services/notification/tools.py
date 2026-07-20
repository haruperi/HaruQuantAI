"""Agent-facing notification tools.

Purpose:
    Provide deterministic notification helper tools for constructing messages,
    rendering templates, validating configuration, building disabled managers,
    inspecting service status, and exercising dry-run alert flows without
    touching external notification providers.

Members:
    - build_notification_message: AI Tool. Build a NotificationMessage object.
    - render_notification_template: AI Tool. Render a named notification template.
    - validate_notification_config: AI Tool. Validate a NotificationConfig object.
    - build_notification_manager_config: AI Tool. Build manager config.
    - create_notification_manager: AI Tool. Create a NotificationManager instance.
    - get_notification_service_status: AI Tool. Read manager service status.
    - send_custom_notification: AI Tool. Send a custom message.
    - send_trading_notification: AI Tool. Send a trading alert.
    - send_system_notification: AI Tool. Send a system alert.
    - send_position_notification: AI Tool. Send a position update.
    - send_error_notification: AI Tool. Send an error alert through configured services.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from app.services.utils.logger import logger

from .base import NotificationLevel, NotificationMessage, NotificationResult
from .config import NotificationConfig
from .manager import NotificationManager, NotificationManagerConfig
from .templates import NotificationTemplate

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "notification"
TOOL_RISK_LEVEL = "medium"
REQUIRES_APPROVAL = False
READ_ONLY = False
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


def _standard_tool_response(
    *,
    tool_name: str,
    status: str,
    message: str,
    data: Any = None,
    error: dict[str, str] | None = None,
    request_id: str | None = None,
    execution_ms: float = 0.0,
) -> dict[str, Any]:
    """Build the standard HaruQuant AI tool response envelope."""
    from app.services.utils.standard import ToolStandardSpec, standard_tool_response

    spec = ToolStandardSpec(tool_name=tool_name)
    spec.tool_name = tool_name
    spec.tool_version = TOOL_VERSION
    spec.tool_category = TOOL_CATEGORY
    spec.tool_risk_level = TOOL_RISK_LEVEL
    spec.read_only = READ_ONLY
    spec.writes_file = WRITES_FILE
    spec.modifies_database = MODIFIES_DATABASE
    spec.places_trade = PLACES_TRADE
    spec.requires_network = REQUIRES_NETWORK

    return standard_tool_response(
        spec=spec,
        status=status,
        message=message,
        data=data,
        error=error,
        request_id=request_id,
        execution_ms=execution_ms,
    )


def _invalid_response(
    *,
    tool_name: str,
    request_id: str | None,
    started_at: float,
    details: str,
) -> dict[str, Any]:
    """Return a standard invalid-input response."""
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    logger.warning(
        "%s validation failed | request_id=%s | details=%s",
        tool_name,
        request_id,
        details,
    )
    return _standard_tool_response(
        tool_name=tool_name,
        status="error",
        message="Invalid input.",
        data=None,
        error={"code": "INVALID_INPUT", "details": details},
        request_id=request_id,
        execution_ms=execution_ms,
    )


def _run_tool(
    *,
    tool_name: str,
    request_id: str | None,
    operation: Callable[[], dict[str, Any]],
    success_message: str,
    validation_error: str | None = None,
) -> dict[str, Any]:
    """Run a notification tool with standard logging, timing, and errors."""
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    if validation_error:
        return _invalid_response(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            details=validation_error,
        )

    try:
        data = operation()
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info(
            "%s completed successfully | request_id=%s | execution_ms=%s",
            tool_name,
            request_id,
            execution_ms,
        )
        return _standard_tool_response(
            tool_name=tool_name,
            status="success",
            message=success_message,
            data=data,
            error=None,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception(
            "%s failed | request_id=%s | execution_ms=%s",
            tool_name,
            request_id,
            execution_ms,
        )
        return _standard_tool_response(
            tool_name=tool_name,
            status="error",
            message="Tool execution failed.",
            data=None,
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _required_text_error(*values: tuple[str, str | None]) -> str | None:
    """Return an input error for the first missing required text value."""
    for field_name, value in values:
        if not isinstance(value, str) or not value.strip():
            return f"{field_name} must be a non-empty string."
    return None


def _numeric_error(*values: tuple[str, Any]) -> str | None:
    """Return an input error for the first non-numeric value."""
    for field_name, value in values:
        if not isinstance(value, (int, float)):
            return f"{field_name} must be numeric."
    return None


def _serialize_result(result: NotificationResult) -> dict[str, Any]:
    """Convert a NotificationResult into deterministic serializable data."""
    return {
        "success": result.success,
        "message_id": result.message_id,
        "error_message": result.error_message,
        "timestamp": result.timestamp.isoformat(),
        "retry_count": result.retry_count,
        "delivery_time_ms": result.delivery_time_ms,
    }


def _serialize_results(results: dict[str, NotificationResult]) -> dict[str, Any]:
    """Convert notification result mappings into serializable dictionaries."""
    return {service: _serialize_result(result) for service, result in results.items()}


def _serialize_message(message: NotificationMessage) -> dict[str, Any]:
    """Convert a NotificationMessage into deterministic serializable data."""
    return {
        "title": message.title,
        "body": message.body,
        "level": message.level.value,
        "timestamp": message.timestamp.isoformat(),
        "metadata": message.metadata,
        "recipients": message.recipients,
        "template_name": message.template_name,
    }


def _serialize_manager_config(config: NotificationManagerConfig) -> dict[str, Any]:
    """Convert a NotificationManagerConfig into deterministic serializable data."""
    return {
        "email_enabled": config.email_config is not None,
        "telegram_enabled": config.telegram_config is not None,
        "sms_enabled": config.sms_config is not None,
        "desktop_enabled": config.desktop_config is not None,
        "default_levels": [level.value for level in config.default_levels],
        "enable_all": config.enable_all,
    }


def _build_notification_message_impl(
    *,
    title: str,
    body: str,
    level: str = "INFO",
    metadata: dict[str, Any] | None = None,
    recipients: list[str] | None = None,
) -> NotificationMessage:
    """Build a notification message object.

    Args:
        title: Message title.
        body: Message body.
        level: Notification level name.
        metadata: Optional metadata dictionary.
        recipients: Optional recipient list.

    Returns:
        NotificationMessage object.
    """
    return NotificationMessage(
        title=title,
        body=body,
        level=NotificationLevel(level),
        metadata=metadata or {},
        recipients=recipients or [],
    )


def _render_notification_template_impl(
    *,
    template_name: str,
    variables: dict[str, Any] | None = None,
) -> NotificationMessage:
    """Render a notification template into a message object.

    Args:
        template_name: Name of the template to render.
        variables: Template variables.

    Returns:
        NotificationMessage object.
    """
    return NotificationTemplate().render(template_name, **(variables or {}))


def _validate_notification_config_impl(
    *,
    config: NotificationConfig | None = None,
) -> list[str]:
    """Validate notification service configuration.

    Args:
        config: Optional NotificationConfig. Defaults to settings.

    Returns:
        List of validation error strings.
    """
    return (config or NotificationConfig.from_settings()).validate()


def _build_notification_manager_config_impl(
    *,
    config: NotificationConfig | None = None,
) -> NotificationManagerConfig:
    """Build a NotificationManagerConfig from service configuration.

    Args:
        config: Optional NotificationConfig. Defaults to settings.

    Returns:
        NotificationManagerConfig object.
    """
    source = config or NotificationConfig.from_settings()
    return NotificationManagerConfig(
        email_config=source.get_email_config(),
        telegram_config=source.get_telegram_config(),
        sms_config=source.get_sms_config(),
        desktop_config=source.get_desktop_config(),
        default_levels=source.get_default_levels(),
        enable_all=source.enable_all,
    )


def _create_notification_manager_impl(
    *,
    config: NotificationManagerConfig | None = None,
) -> NotificationManager:
    """Create a notification manager.

    Args:
        config: Optional manager configuration. Defaults to settings.

    Returns:
        NotificationManager instance.
    """
    if config is None:
        config = _build_notification_manager_config_impl()
    return NotificationManager(config)


def _get_notification_service_status_impl(
    *,
    manager: NotificationManager | None = None,
) -> dict[str, dict[str, Any]]:
    """Read notification service status from a manager.

    Args:
        manager: Optional manager. Defaults to an empty manager.

    Returns:
        Service status dictionary.
    """
    return (manager or _create_notification_manager_impl()).get_service_status()


def _send_custom_notification_impl(
    *,
    title: str,
    body: str,
    level: str = "INFO",
    manager: NotificationManager | None = None,
    services: list[str] | None = None,
) -> dict[str, Any]:
    """Send a custom notification through configured services.

    Args:
        title: Message title.
        body: Message body.
        level: Notification level.
        manager: Optional configured manager.
        services: Optional service filter.

    Returns:
        Serializable mapping of service names to delivery results.
    """
    active_manager = manager or _create_notification_manager_impl()
    return _serialize_results(
        active_manager.send_custom_message(
            title=title,
            body=body,
            level=level,
            services=services,
        )
    )


def _send_trading_notification_impl(
    *,
    symbol: str,
    action: str,
    price: float,
    reason: str,
    manager: NotificationManager | None = None,
    services: list[str] | None = None,
) -> dict[str, Any]:
    """Send a trading alert notification through configured services.

    Args:
        symbol: Trading symbol.
        action: Trading action.
        price: Alert price.
        reason: Alert reason.
        manager: Optional configured manager.
        services: Optional service filter.

    Returns:
        Serializable mapping of service names to delivery results.
    """
    active_manager = manager or _create_notification_manager_impl()
    return _serialize_results(
        active_manager.send_trading_alert(
            symbol=symbol,
            action=action,
            price=price,
            reason=reason,
            services=services,
        )
    )


def _send_system_notification_impl(
    *,
    level: str,
    message: str,
    details: str = "",
    component: str = "System",
    status: str = "Active",
    manager: NotificationManager | None = None,
    services: list[str] | None = None,
) -> dict[str, Any]:
    """Send a system alert notification through configured services.

    Args:
        level: Notification level.
        message: Alert message.
        details: Optional details.
        component: Component name.
        status: Component status.
        manager: Optional configured manager.
        services: Optional service filter.

    Returns:
        Serializable mapping of service names to delivery results.
    """
    active_manager = manager or _create_notification_manager_impl()
    return _serialize_results(
        active_manager.send_system_alert(
            level=level,
            message=message,
            details=details,
            component=component,
            status=status,
            services=services,
        )
    )


def _send_position_notification_impl(
    *,
    symbol: str,
    position_type: str,
    size: float,
    entry_price: float,
    current_price: float,
    pnl: float,
    pnl_percent: float,
    manager: NotificationManager | None = None,
    services: list[str] | None = None,
) -> dict[str, Any]:
    """Send a position update notification through configured services.

    Args:
        symbol: Trading symbol.
        position_type: Position direction/type.
        size: Position size.
        entry_price: Entry price.
        current_price: Current price.
        pnl: Profit/loss value.
        pnl_percent: Profit/loss percent.
        manager: Optional configured manager.
        services: Optional service filter.

    Returns:
        Serializable mapping of service names to delivery results.
    """
    active_manager = manager or _create_notification_manager_impl()
    return _serialize_results(
        active_manager.send_position_update(
            symbol=symbol,
            position_type=position_type,
            size=size,
            entry_price=entry_price,
            current_price=current_price,
            pnl=pnl,
            pnl_percent=pnl_percent,
            services=services,
        )
    )


def _send_error_notification_impl(
    *,
    error_type: str,
    message: str,
    component: str = "Unknown",
    stack_trace: str = "",
    manager: NotificationManager | None = None,
    services: list[str] | None = None,
) -> dict[str, Any]:
    """Send an error alert notification through configured services.

    Args:
        error_type: Error category.
        message: Error message.
        component: Component name.
        stack_trace: Optional stack trace.
        manager: Optional configured manager.
        services: Optional service filter.

    Returns:
        Serializable mapping of service names to delivery results.
    """
    active_manager = manager or _create_notification_manager_impl()
    return _serialize_results(
        active_manager.send_error_alert(
            error_type=error_type,
            message=message,
            component=component,
            stack_trace=stack_trace,
            services=services,
        )
    )


# --- AI Tool Wrappers ---


def build_notification_message(
    *,
    title: str,
    body: str,
    level: str = "INFO",
    metadata: dict[str, Any] | None = None,
    recipients: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Build a notification message payload without sending it.

    Use this tool when an agent needs to validate and serialize a notification
    message before rendering, routing, or sending it.

    Args:
        title: Non-empty message title.
        body: Non-empty message body.
        level: Notification level name, for example "INFO" or "ERROR".
        metadata: Optional metadata to attach to the message.
        recipients: Optional recipient override list.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing the serialized notification message.
    """
    validation_error = _required_text_error(
        ("title", title),
        ("body", body),
        ("level", level),
    )
    return _run_tool(
        tool_name="build_notification_message",
        request_id=request_id,
        validation_error=validation_error,
        success_message="Notification message built successfully.",
        operation=lambda: _serialize_message(
            _build_notification_message_impl(
                title=title,
                body=body,
                level=level,
                metadata=metadata,
                recipients=recipients,
            )
        ),
    )


def render_notification_template(
    *,
    template_name: str,
    variables: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Render a named notification template into a message payload.

    Use this tool when an agent needs a standard trading, system, position, or
    error alert body generated from template variables before delivery.

    Args:
        template_name: Name of the notification template to render.
        variables: Template variable mapping.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing the serialized rendered message.
    """
    validation_error = _required_text_error(("template_name", template_name))
    return _run_tool(
        tool_name="render_notification_template",
        request_id=request_id,
        validation_error=validation_error,
        success_message=f"Template '{template_name}' rendered successfully.",
        operation=lambda: _serialize_message(
            _render_notification_template_impl(
                template_name=template_name,
                variables=variables,
            )
        ),
    )


def validate_notification_config(
    *,
    config: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Validate notification service configuration without contacting providers.

    Use this tool before creating a manager or enabling notification channels.

    Args:
        config: Optional NotificationConfig-compatible dictionary.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing validation errors, if any.
    """

    def _operation() -> dict[str, Any]:
        config_obj = NotificationConfig(**config) if config else None
        errors = _validate_notification_config_impl(config=config_obj)
        return {"valid": not errors, "errors": errors}

    return _run_tool(
        tool_name="validate_notification_config",
        request_id=request_id,
        success_message="Configuration validated.",
        operation=_operation,
    )


def build_notification_manager_config(
    *,
    config: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Build manager-level notification configuration from service settings.

    Use this tool when an agent needs to inspect which channels would be active
    before creating a NotificationManager.

    Args:
        config: Optional NotificationConfig-compatible dictionary.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing serialized manager configuration.
    """
    return _run_tool(
        tool_name="build_notification_manager_config",
        request_id=request_id,
        success_message="Manager configuration built.",
        operation=lambda: _serialize_manager_config(
            _build_notification_manager_config_impl(
                config=NotificationConfig(**config) if config else None
            )
        ),
    )


def create_notification_manager(
    *,
    config: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a notification manager from manager configuration.

    Use this tool to verify that manager construction succeeds. It returns a
    serializable status instead of the live manager object.

    Args:
        config: Optional NotificationManagerConfig-compatible dictionary.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response indicating manager creation status.
    """

    def _operation() -> dict[str, Any]:
        mgr_config = NotificationManagerConfig(**config) if config else None
        _create_notification_manager_impl(config=mgr_config)
        return {"manager_status": "created"}

    return _run_tool(
        tool_name="create_notification_manager",
        request_id=request_id,
        success_message="Notification manager created successfully.",
        operation=_operation,
    )


def get_notification_service_status(
    *,
    manager: Any | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Read notification service status from a manager.

    Use this tool when an agent needs to know which notification services are
    configured and enabled.

    Args:
        manager: Optional NotificationManager instance.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing service status data.
    """
    return _run_tool(
        tool_name="get_notification_service_status",
        request_id=request_id,
        success_message="Service status retrieved successfully.",
        operation=lambda: _get_notification_service_status_impl(manager=manager),
    )


def send_custom_notification(
    *,
    title: str,
    body: str,
    level: str = "INFO",
    manager: Any | None = None,
    services: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Send a custom notification through configured services.

    Use this tool for ad hoc notification delivery. With no configured services,
    the result is a successful empty delivery map.

    Args:
        title: Non-empty notification title.
        body: Non-empty notification body.
        level: Notification level name.
        manager: Optional NotificationManager instance.
        services: Optional service names to target.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing per-service delivery results.
    """
    validation_error = _required_text_error(
        ("title", title),
        ("body", body),
        ("level", level),
    )
    return _run_tool(
        tool_name="send_custom_notification",
        request_id=request_id,
        validation_error=validation_error,
        success_message="Custom notification processed.",
        operation=lambda: _send_custom_notification_impl(
            title=title,
            body=body,
            level=level,
            manager=manager,
            services=services,
        ),
    )


def send_trading_notification(
    *,
    symbol: str,
    action: str,
    price: float,
    reason: str,
    manager: Any | None = None,
    services: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Send a trading alert notification through configured services.

    Use this tool when an agent needs to alert on a trading signal, order
    intent, or market event without placing a trade.

    Args:
        symbol: Non-empty trading symbol.
        action: Non-empty trading action.
        price: Numeric alert price.
        reason: Non-empty alert reason.
        manager: Optional NotificationManager instance.
        services: Optional service names to target.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing per-service delivery results.
    """
    validation_error = _required_text_error(
        ("symbol", symbol), ("action", action), ("reason", reason)
    ) or _numeric_error(("price", price))
    return _run_tool(
        tool_name="send_trading_notification",
        request_id=request_id,
        validation_error=validation_error,
        success_message="Trading notification processed.",
        operation=lambda: _send_trading_notification_impl(
            symbol=symbol,
            action=action,
            price=price,
            reason=reason,
            manager=manager,
            services=services,
        ),
    )


def send_system_notification(
    *,
    level: str,
    message: str,
    details: str = "",
    component: str = "System",
    status: str = "Active",
    manager: Any | None = None,
    services: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Send a system alert notification through configured services.

    Use this tool for health, deployment, component, or operational alerts.

    Args:
        level: Notification level name.
        message: Non-empty alert message.
        details: Optional alert details.
        component: Component name.
        status: Component status.
        manager: Optional NotificationManager instance.
        services: Optional service names to target.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing per-service delivery results.
    """
    validation_error = _required_text_error(("level", level), ("message", message))
    return _run_tool(
        tool_name="send_system_notification",
        request_id=request_id,
        validation_error=validation_error,
        success_message="System notification processed.",
        operation=lambda: _send_system_notification_impl(
            level=level,
            message=message,
            details=details,
            component=component,
            status=status,
            manager=manager,
            services=services,
        ),
    )


def send_position_notification(
    *,
    symbol: str,
    position_type: str,
    size: float,
    entry_price: float,
    current_price: float,
    pnl: float,
    pnl_percent: float,
    manager: Any | None = None,
    services: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Send a position update notification through configured services.

    Use this tool to notify about open-position state, current price, and PnL.

    Args:
        symbol: Non-empty trading symbol.
        position_type: Non-empty position direction/type.
        size: Numeric position size.
        entry_price: Numeric entry price.
        current_price: Numeric current price.
        pnl: Numeric profit/loss value.
        pnl_percent: Numeric profit/loss percent.
        manager: Optional NotificationManager instance.
        services: Optional service names to target.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing per-service delivery results.
    """
    validation_error = _required_text_error(
        ("symbol", symbol), ("position_type", position_type)
    ) or _numeric_error(
        ("size", size),
        ("entry_price", entry_price),
        ("current_price", current_price),
        ("pnl", pnl),
        ("pnl_percent", pnl_percent),
    )
    return _run_tool(
        tool_name="send_position_notification",
        request_id=request_id,
        validation_error=validation_error,
        success_message="Position notification processed.",
        operation=lambda: _send_position_notification_impl(
            symbol=symbol,
            position_type=position_type,
            size=size,
            entry_price=entry_price,
            current_price=current_price,
            pnl=pnl,
            pnl_percent=pnl_percent,
            manager=manager,
            services=services,
        ),
    )


def send_error_notification(
    *,
    error_type: str,
    message: str,
    component: str = "Unknown",
    stack_trace: str = "",
    manager: Any | None = None,
    services: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Send an error alert notification through configured services.

    Use this tool to notify operators about exceptions or component failures.

    Args:
        error_type: Non-empty error category.
        message: Non-empty error message.
        component: Component name.
        stack_trace: Optional stack trace. It is truncated by the manager.
        manager: Optional NotificationManager instance.
        services: Optional service names to target.
        request_id: Optional workflow trace ID.

    Returns:
        Standard tool response containing per-service delivery results.
    """
    validation_error = _required_text_error(
        ("error_type", error_type),
        ("message", message),
    )
    return _run_tool(
        tool_name="send_error_notification",
        request_id=request_id,
        validation_error=validation_error,
        success_message="Error notification processed.",
        operation=lambda: _send_error_notification_impl(
            error_type=error_type,
            message=message,
            component=component,
            stack_trace=stack_trace,
            manager=manager,
            services=services,
        ),
    )


__all__ = [
    "build_notification_manager_config",
    "build_notification_message",
    "create_notification_manager",
    "get_notification_service_status",
    "render_notification_template",
    "send_custom_notification",
    "send_error_notification",
    "send_position_notification",
    "send_system_notification",
    "send_trading_notification",
    "validate_notification_config",
]

# ruff: noqa: E501
"""Analytics Registry module.

This module houses the registry for official tools, metric kernel visibility,
stability, agent/API eligibility, aliases, deprecation status, and traceability.
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from app.services.analytics.contracts.metric_catalog import (
    OFFICIAL_ANALYTICS_TOOL_CATALOG,
)
from app.services.analytics.contracts.models import (
    MetricConfig,
    MetricResult,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger

# Active request IDs cache/registry (observability/traceability)
_ACTIVE_REQUESTS: set[str] = set()

# Central registry mapping unique names/aliases to tool entry configurations
TOOL_REGISTRY: dict[str, RegisteredToolEntry] = {}
OFFICIAL_TOOL_NAMES: frozenset[str] = frozenset(OFFICIAL_ANALYTICS_TOOL_CATALOG)


@dataclass(frozen=True, slots=True)
class RegisteredToolEntry:
    """Registry entry configuration for an analytics public capability or tool.

    Attributes:
        name: The canonical registered name of the tool.
        callable_obj: The actual callable target object.
        stability: Stability state: stable/approved_experimental/deprecated/
            internal_support_only (ANL-NFR-010).
        safe_for_agent_api: True if safe for agentic/API execution (ANL-NFR-011).
        category: Capability classification (ANL-NFR-012).
        description: Extracted docstring details.
        aliases: Registered alternate names (ANL-NFR-008).
    """

    name: str
    callable_obj: Any
    stability: Literal[
        "stable",
        "approved_experimental",
        "deprecated",
        "internal_support_only",
    ]
    safe_for_agent_api: bool
    category: Literal[
        "official_tool",
        "internal_metric_kernel",
        "compatibility_alias",
        "deprecated_export",
    ]
    description: str
    aliases: tuple[str, ...] = field(default_factory=tuple)


def register_tool(
    name: str,
    stability: Literal[
        "stable",
        "approved_experimental",
        "deprecated",
        "internal_support_only",
    ],
    safe_for_agent_api: bool,
    category: Literal[
        "official_tool",
        "internal_metric_kernel",
        "compatibility_alias",
        "deprecated_export",
    ],
    aliases: tuple[str, ...] = (),
) -> Callable[[Any], Any]:
    """Decorator to register a capability in the central registry (ANL-NFR-008).

    Args:
        name (str): Input parameter `name`.
        stability (Literal['stable', 'approved_experimental', 'deprecated', 'internal_support_only']): Input parameter `stability`.
        safe_for_agent_api (bool): Input parameter `safe_for_agent_api`.
        category (Literal['official_tool', 'internal_metric_kernel', 'compatibility_alias', 'deprecated_export']): Input parameter `category`.
        aliases (tuple[str, ...]): Input parameter `aliases`.

    Returns:
        Calculated Callable[[Any], Any] value.
    """
    logger.debug("register_tool: executed.")

    def decorator(func: Any) -> Any:  # noqa: ANN401
        # Validate name collision
        """Expose behavior for `decorator`.

        Args:
            func (Any): Input parameter `func`.

        Returns:
            Calculated Any value.
        """
        logger.debug("decorator: executed.")
        if name in TOOL_REGISTRY:
            msg = f"Duplicate registry name collision: {name!r}."
            raise ValidationError(msg)

        # Validate aliases collision
        for alias in aliases:
            if alias in TOOL_REGISTRY:
                msg = f"Duplicate registry alias collision: {alias!r}."
                raise ValidationError(msg)

        entry = RegisteredToolEntry(
            name=name,
            callable_obj=func,
            stability=stability,
            safe_for_agent_api=safe_for_agent_api,
            category=category,
            description=func.__doc__ or "",
            aliases=aliases,
        )

        TOOL_REGISTRY[name] = entry
        for alias in aliases:
            TOOL_REGISTRY[alias] = entry

        return func

    return decorator


def get_active_requests() -> set[str]:
    """Retrieve active requests registered in the local observability log.

    Returns:
        Calculated set[str] value.
    """
    logger.debug("get_active_requests: executed.")
    return _ACTIVE_REQUESTS.copy()


def clear_active_requests() -> None:
    """Clear all active requests in the local observability log."""
    logger.debug("clear_active_requests: executed.")
    _ACTIVE_REQUESTS.clear()


def request_id(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[object]:
    """Extract, validate, and record request_id for traceability (ANL-NFR-009).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated object value.
    """
    logger.debug("request_id: executed.")
    req_id: Any = None
    if isinstance(input_value, str):
        req_id = input_value
    elif isinstance(input_value, Mapping):
        req_id = input_value.get("request_id")
    else:
        req_id = getattr(input_value, "request_id", None)

    # Fallback to config attributes if not found in input
    if not req_id:
        req_id = getattr(config, "request_id", None)

    warnings_list = []
    if not req_id:
        req_id = "UNKNOWN_REQUEST_ID"
        warnings_list.append(
            {
                "code": "MISSING_REQUEST_ID",
                "message": "Traceability request_id was not supplied or is empty.",
            }
        )
    elif not isinstance(req_id, str):
        req_id = str(req_id)
        warnings_list.append(
            {
                "code": "INVALID_REQUEST_ID_TYPE",
                "message": f"Expected string for request_id, got {type(req_id).__name__}.",
            }
        )

    # Enforce standard formatting safety (alphanumeric, underscores, hyphens)
    if isinstance(req_id, str) and not re.match(r"^[a-zA-Z0-9_\-]+$", req_id):
        warnings_list.append(
            {
                "code": "UNSAFE_REQUEST_ID",
                "message": "Request ID contains potentially unsafe characters.",
            }
        )

    # Cache in observability log
    _ACTIVE_REQUESTS.add(req_id)

    return MetricResult[object](
        value=req_id,
        confidence="normal" if not warnings_list else "degraded",
        warnings=tuple(warnings_list),
    )

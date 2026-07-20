"""Flat public notification tools.

Implementation remains in `app.services.notification`; this module exposes lazy
service fallback without a namespace class.

Public callable functions:
- __getattr__(name): Resolve lower-level notification service attributes.
"""

from __future__ import annotations

from typing import Any

from app.services import resolve_service_attr, service_modules

_SERVICE_MODULES = tuple(
    module_name
    for module_name in service_modules("app.services.notification")
    if module_name
    not in {"app.services.notification", "app.services.notification._common"}
)


def __getattr__(name: str) -> Any:
    """Resolve lower-level notification service attributes lazily."""
    if name.startswith("__"):
        raise AttributeError(name)
    return resolve_service_attr(name, _SERVICE_MODULES)


__all__: list[str] = []

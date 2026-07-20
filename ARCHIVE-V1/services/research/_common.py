"""Flat public research tools.

Purpose:
    Flat public research tools.

Classes:
    None.

Functions:
    research_modeling_module: Run research modeling module processing.
    __getattr__: Support internal getattr processing.
"""

from __future__ import annotations

from types import ModuleType
from typing import Any

from app.services import load_service_module, resolve_service_attr, service_modules

_SERVICE_MODULES = tuple(
    module_name
    for module_name in service_modules("app.services.research")
    if module_name not in {"app.services.research", "app.services.research._common"}
)


def research_modeling_module() -> ModuleType:
    """Return the research modeling service module."""
    module: ModuleType = load_service_module("app.services.research.modeling")
    return module


def __getattr__(name: str) -> Any:
    """Resolve lower-level research service attributes lazily."""
    if name.startswith("__"):
        raise AttributeError(name)
    return resolve_service_attr(name, _SERVICE_MODULES)


__all__ = ["research_modeling_module"]

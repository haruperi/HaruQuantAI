"""Shared helpers for service-level tool packages.

Public trading, data, strategy, risk, and analytics tools are exposed from
their service package, for example `app.services.data`, `app.services.simulation`, and
`app.services.strategy`. The root package intentionally does not re-export tools.
"""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from pkgutil import walk_packages
from types import ModuleType
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = str(_PACKAGE_ROOT.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def load_service_symbol(*, service_module: str, name: str) -> Any:
    module = import_module(service_module)
    value = getattr(module, name)
    return value


def load_service_module(service_module: str) -> ModuleType:
    return import_module(service_module)


def service_modules(service_package: str) -> tuple[str, ...]:
    package = import_module(service_package)
    modules = [service_package]
    package_paths = getattr(package, "__path__", None)
    if package_paths is None:
        return tuple(modules)
    modules.extend(
        module_info.name
        for module_info in walk_packages(package_paths, prefix=f"{service_package}.")
    )
    return tuple(modules)


def resolve_service_attr(name: str, modules: tuple[str, ...]) -> Any:
    last_error: AttributeError | None = None
    for module_name in modules:
        module = import_module(module_name)
        if hasattr(module, name):
            value = getattr(module, name)
            if not (
                isinstance(value, ModuleType)
                and value.__name__ == f"{module_name}.{name}"
            ):
                return value
        try:
            submodule = import_module(f"{module_name}.{name}")
            return getattr(submodule, name) if hasattr(submodule, name) else submodule
        except ModuleNotFoundError as exc:
            if exc.name != f"{module_name}.{name}":
                raise
            last_error = AttributeError(name)
    raise last_error or AttributeError(name)


__all__ = [
    "load_service_module",
    "load_service_symbol",
    "resolve_service_attr",
    "service_modules",
]

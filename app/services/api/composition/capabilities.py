"""Required and optional classification for composed API capabilities."""

from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from types import MappingProxyType, ModuleType
from typing import Final

from app.utils import get_logger

logger = get_logger(__name__)

# Capabilities whose absence degrades the gateway instead of blocking startup.
# Every entry is consumed by the API alone, so removing one cannot silently
# weaken a core execution path. Trading, Risk, Data, Strategy, Simulation,
# Simulator, Indicators, Operator, Dashboard, and Brokers stay required and
# fail closed per AGENTS.md section 3; Simulator and Indicators in particular
# remain required because Trading, Risk, and Strategy consume them directly.
_OPTIONAL_CAPABILITY_IDS: Final[frozenset[str]] = frozenset(
    {
        "agentic",
        "analytics",
        "optimization",
        "portfolio",
        "research",
    }
)

# Import prefixes each optional capability owns. A missing module is treated as
# capability absence only when it belongs to one of these prefixes, so an
# unrelated broken import inside a present capability still raises.
_CAPABILITY_PACKAGES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "agentic": (
            "app.services.api.widgets.agentic",
            "app.agentic",
        ),
        "analytics": (
            "app.services.api.widgets.analytics",
            "app.services.analytics",
        ),
        "optimization": (
            "app.services.api.widgets.optimization",
            "app.services.optimization",
        ),
        "portfolio": (
            "app.services.api.widgets.portfolio",
            "app.services.portfolio",
        ),
        "research": (
            "app.services.api.widgets.research",
            "app.services.research",
        ),
    }
)


def get_optional_capability_ids() -> frozenset[str]:
    """Return the capability identifiers allowed to degrade.

    Returns:
        Immutable set of optional capability identifiers.
    """
    return _OPTIONAL_CAPABILITY_IDS


def is_optional_capability(capability_id: str) -> bool:
    """Report whether one capability may be absent without blocking startup.

    Args:
        capability_id: Capability identifier such as ``research``.

    Returns:
        ``True`` when the capability is optional.
    """
    return capability_id in _OPTIONAL_CAPABILITY_IDS


def get_capability_id(provider_name: str) -> str:
    """Return the capability owning one named in-process provider.

    Args:
        provider_name: Provider name such as ``research.source``.

    Returns:
        Capability identifier preceding the first name separator.
    """
    return provider_name.split(".", 1)[0]


def _is_absent_capability_module(
    error: ModuleNotFoundError,
    capability_id: str,
) -> bool:
    """Report whether one import error means the capability itself is absent.

    Args:
        error: Import failure raised while resolving a capability module.
        capability_id: Capability the import belongs to.

    Returns:
        ``True`` when the missing module is one the capability owns.
    """
    if not is_optional_capability(capability_id):
        return False
    missing = error.name
    if not missing:
        return False
    return any(
        missing == package or missing.startswith(f"{package}.")
        for package in _CAPABILITY_PACKAGES.get(capability_id, ())
    )


def import_capability_module(
    module_path: str,
    *,
    capability_id: str,
) -> ModuleType | None:
    """Import one capability module, tolerating absence of optional capabilities.

    Args:
        module_path: Absolute module path owned by the capability.
        capability_id: Capability the module belongs to.

    Returns:
        Imported module, or ``None`` when an optional capability is absent.

    Raises:
        ModuleNotFoundError: If the capability is required, or the missing
            module is not one the capability owns.
    """
    try:
        return import_module(module_path)
    except ModuleNotFoundError as error:
        if not _is_absent_capability_module(error, capability_id):
            raise
        logger.warning(
            "Optional API capability unavailable: %s",
            capability_id,
        )
        return None


def import_capability_attribute(
    module_path: str,
    attribute: str,
    *,
    capability_id: str,
) -> object | None:
    """Resolve one attribute from a capability module that may be absent.

    Args:
        module_path: Absolute module path owned by the capability.
        attribute: Attribute name to resolve from the module.
        capability_id: Capability the module belongs to.

    Returns:
        Resolved attribute, or ``None`` when an optional capability is absent.

    Raises:
        ModuleNotFoundError: If the capability is required, or the missing
            module is not one the capability owns.
    """
    module = import_capability_module(module_path, capability_id=capability_id)
    if module is None:
        return None
    return getattr(module, attribute)


def get_capability_attribute(
    module: ModuleType | None, attribute: str
) -> object | None:
    """Return one attribute from an already-resolved capability module.

    Args:
        module: Resolved capability module, or ``None`` when it is absent.
        attribute: Attribute name to resolve from the module.

    Returns:
        Resolved attribute, or ``None`` when the capability is absent.
    """
    if module is None:
        return None
    return getattr(module, attribute)


__all__ = (
    "get_capability_attribute",
    "get_capability_id",
    "get_optional_capability_ids",
    "import_capability_attribute",
    "import_capability_module",
    "is_optional_capability",
)

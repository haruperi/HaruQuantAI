"""Discovery and resolution of declared optional API capabilities."""

from __future__ import annotations

import pkgutil
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from types import MappingProxyType, ModuleType
from typing import Final, cast

from app.utils import get_logger

logger = get_logger(__name__)

_WIDGETS_PACKAGE: Final[str] = "app.services.api.widgets"
_DECLARATION_MODULE: Final[str] = "capability"

# Capability identifiers that may legitimately be absent. A declaration lives
# inside the capability and disappears with it, so knowing a capability is
# *missing* requires a record here that it was expected. Each declaration still
# owns its own packages and requirements; this registry owns only expectation.
_EXPECTED_OPTIONAL_IDS: Final[frozenset[str]] = frozenset(
    {
        "agentic",
        "optimization",
        "portfolio",
        "research",
    }
)

# Reasons a declared capability is not active in this composition.
CAPABILITY_ABSENT: Final[str] = "CAPABILITY_ABSENT"
REQUIREMENT_UNAVAILABLE: Final[str] = "REQUIREMENT_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class _Declaration:
    """One capability's declared identity, packages, and requirements."""

    capability_id: str
    packages: tuple[str, ...]
    requires: tuple[str, ...]


def _read_declaration(widget: str) -> _Declaration | None:
    """Read one widget package's capability declaration.

    Args:
        widget: Widget package name under the workstation namespace.

    Returns:
        The declaration, or ``None`` when the widget declares no capability.
    """
    module_path = f"{_WIDGETS_PACKAGE}.{widget}.{_DECLARATION_MODULE}"
    try:
        if find_spec(module_path) is None:
            return None
    except ImportError, ValueError:
        return None
    declaration = import_module(module_path)
    return _Declaration(
        capability_id=str(declaration.CAPABILITY_ID),
        packages=tuple(str(package) for package in declaration.PACKAGES),
        requires=tuple(str(requirement) for requirement in declaration.REQUIRES),
    )


def _discover_declarations() -> Mapping[str, _Declaration]:
    """Discover every declared optional capability under the widgets namespace.

    A widget without a declaration is required: absence of a declaration fails
    closed rather than silently making a capability optional.

    Returns:
        Immutable mapping from capability identifier to its declaration.
    """
    widgets = import_module(_WIDGETS_PACKAGE)
    discovered: dict[str, _Declaration] = {}
    for module in pkgutil.iter_modules(widgets.__path__):
        if not module.ispkg:
            continue
        declaration = _read_declaration(module.name)
        if declaration is not None:
            discovered[declaration.capability_id] = declaration
    return MappingProxyType(discovered)


_DECLARATIONS: Final[Mapping[str, _Declaration]] = _discover_declarations()


def _is_present(declaration: _Declaration) -> bool:
    """Report whether every package a capability owns is importable.

    Args:
        declaration: Declared capability under inspection.

    Returns:
        ``True`` when the capability's own packages are all present.
    """
    for package in declaration.packages:
        try:
            if find_spec(package) is None:
                return False
        except ImportError, ValueError:
            return False
    return True


def _resolve() -> Mapping[str, str]:
    """Resolve which declared capabilities cannot be composed, and why.

    Absent capabilities deactivate first; any capability requiring an inactive
    one then deactivates transitively until the result is stable.

    Returns:
        Immutable mapping from inactive capability identifier to its reason.
    """
    inactive: dict[str, str] = {
        capability_id: CAPABILITY_ABSENT
        for capability_id in _EXPECTED_OPTIONAL_IDS
        if capability_id not in _DECLARATIONS
    }
    inactive.update(
        {
            capability_id: CAPABILITY_ABSENT
            for capability_id, declaration in _DECLARATIONS.items()
            if not _is_present(declaration)
        }
    )
    changed = True
    while changed:
        changed = False
        for capability_id, declaration in _DECLARATIONS.items():
            if capability_id in inactive:
                continue
            if any(requirement in inactive for requirement in declaration.requires):
                inactive[capability_id] = REQUIREMENT_UNAVAILABLE
                changed = True
    for capability_id, reason in sorted(inactive.items()):
        logger.warning(
            "Optional API capability inactive: %s (%s)",
            capability_id,
            reason,
        )
    return MappingProxyType(inactive)


_INACTIVE: Final[Mapping[str, str]] = _resolve()


def get_optional_capability_ids() -> frozenset[str]:
    """Return every declared optional capability identifier.

    Returns:
        Immutable set of declared optional capability identifiers.
    """
    return frozenset(_DECLARATIONS) | _EXPECTED_OPTIONAL_IDS


def get_inactive_capabilities() -> Mapping[str, str]:
    """Return inactive capability identifiers mapped to their reason.

    Returns:
        Immutable mapping from capability identifier to degradation reason.
    """
    return _INACTIVE


def is_optional_capability(capability_id: str) -> bool:
    """Report whether one capability declared itself optional.

    Args:
        capability_id: Capability identifier such as ``research``.

    Returns:
        ``True`` when the capability carries a declaration.
    """
    return capability_id in _DECLARATIONS or capability_id in _EXPECTED_OPTIONAL_IDS


def is_active_capability(capability_id: str) -> bool:
    """Report whether one capability can be composed.

    Args:
        capability_id: Capability identifier such as ``research``.

    Returns:
        ``True`` when the capability is required, or declared and resolvable.
    """
    return capability_id not in _INACTIVE


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
        ``True`` when the missing module is one the capability declared.
    """
    declaration = _DECLARATIONS.get(capability_id)
    missing = error.name
    if declaration is None or not missing:
        return False
    return any(
        missing == package or missing.startswith(f"{package}.")
        for package in declaration.packages
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
        Imported module, or ``None`` when the capability is inactive.

    Raises:
        ModuleNotFoundError: If the capability is required, or the missing
            module is not one the capability declared.
    """
    if not is_active_capability(capability_id):
        return None
    try:
        return import_module(module_path)
    except ModuleNotFoundError as error:
        if not _is_absent_capability_module(error, capability_id):
            raise
        logger.warning("Optional API capability unavailable: %s", capability_id)
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
        Resolved attribute, or ``None`` when the capability is inactive.

    Raises:
        ModuleNotFoundError: If the capability is required, or the missing
            module is not one the capability declared.
    """
    module = import_capability_module(module_path, capability_id=capability_id)
    if module is None:
        return None
    return cast("object", getattr(module, attribute))


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
    return cast("object", getattr(module, attribute))


__all__ = (
    "get_capability_attribute",
    "get_capability_id",
    "get_inactive_capabilities",
    "get_optional_capability_ids",
    "import_capability_attribute",
    "import_capability_module",
    "is_active_capability",
    "is_optional_capability",
)

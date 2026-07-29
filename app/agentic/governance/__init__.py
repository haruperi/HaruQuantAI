"""Public `FEAT-AGT-02` firm governance, roster, and authority API."""

from app.agentic.governance.models import FirmMandate, RoleManifest
from app.agentic.governance.registry import (
    RoleRegistry,
    get_registry_mandate,
    get_role_registry,
    list_enabled_roles,
    list_registered_roles,
    resolve_role_manifest,
    validate_firm_mandate,
)

__all__: tuple[str, ...] = (
    "FirmMandate",
    "RoleManifest",
    "RoleRegistry",
    "get_registry_mandate",
    "get_role_registry",
    "list_enabled_roles",
    "list_registered_roles",
    "resolve_role_manifest",
    "validate_firm_mandate",
)

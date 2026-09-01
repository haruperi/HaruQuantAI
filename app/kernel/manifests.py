"""Strict provider manifest definitions and parser."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.kernel.errors import ManifestValidationError
from app.kernel.identifiers import CapabilityId, ProviderId


class Cardinality(StrEnum):
    """Capability cardinality."""

    EXACTLY_ONE = "exactly_one"
    MANY = "many"


class LifecyclePolicy(StrEnum):
    """Provider lifecycle policy."""

    SINGLETON = "singleton"
    SCOPED = "scoped"
    EPHEMERAL = "ephemeral"


class ReloadPolicy(StrEnum):
    """Provider reload policy."""

    DYNAMIC = "dynamic"
    PROCESS_RESTART = "process_restart"


class EffectClass(StrEnum):
    """Provider effect class."""

    REVERSIBLE_EPHEMERAL = "reversible_ephemeral"
    DURABLE_COMPENSATABLE = "durable_compensatable"


@dataclass(frozen=True, slots=True)
class ProvidedCapability:
    """Capability provided by a manifest."""

    capability_id: str
    contract_version: str | Any = "1.0.0"
    schema_id: str = "kernel.capability.v1"
    cardinality: str | Cardinality = "exactly_one"


@dataclass(frozen=True, slots=True)
class RequiredCapability:
    """Capability required by a manifest."""

    capability_id: str
    contract_version: str | Any = "1.0.0"
    schema_id: str = "kernel.capability.v1"
    optional: bool = False


@dataclass(frozen=True, slots=True)
class ProviderManifest:
    """Immutable parsed provider manifest."""

    id: str = ""
    version: str | Any = "1.0.0"
    entry_point: str = ""
    provides: tuple[ProvidedCapability, ...] = ()
    requires: tuple[RequiredCapability, ...] = ()
    optional_requires: tuple[RequiredCapability, ...] = ()
    profiles: tuple[str | Any, ...] = ()
    scopes: tuple[str, ...] = ()
    effect_classes: tuple[str | EffectClass, ...] = ()
    lifecycle: str | LifecyclePolicy = "singleton"
    reload: str | ReloadPolicy = "dynamic"
    config_schema: Any = None
    state_schema_id: str | None = None
    state_schema_version: str | None = None
    migration_manifest: str | None = None
    compatible_prior_majors: tuple[int, ...] = ()
    compatible_state_majors: tuple[int, ...] = ()
    downgrade_policy: str | None = None
    uninstall_retention: str | None = None
    purge_requires_authorization: bool = False
    provider_id: str = ""
    provider_version: Any = None

    def __post_init__(self) -> None:
        """Normalize provider identity and version aliases."""
        if self.provider_id and not self.id:
            object.__setattr__(self, "id", str(self.provider_id))
        elif self.id and not self.provider_id:
            object.__setattr__(self, "provider_id", str(self.id))
        if self.provider_version and not self.version:
            object.__setattr__(self, "version", str(self.provider_version))
        elif self.version and not self.provider_version:
            object.__setattr__(self, "provider_version", self.version)


def load_manifest(path: str | Path) -> ProviderManifest:
    """Load and strictly validate a provider manifest TOML file.

    Args:
        path: Path to manifest.toml file.

    Returns:
        Validated ProviderManifest instance.

    Raises:
        ManifestValidationError: If the manifest structure or values are invalid.
    """
    path_obj = Path(path).resolve()
    try:
        data = tomllib.loads(path_obj.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ManifestValidationError(
            f"invalid provider manifest {path_obj}: {exc}"
        ) from exc

    if "provider" not in data:
        raise ManifestValidationError(
            f"invalid provider manifest {path_obj}: missing key 'provider'"
        )

    provider_sec = data.get("provider", {})
    provider_id_str = str(provider_sec.get("id", ""))
    provider_id = ProviderId.parse(provider_id_str) if provider_id_str else ""
    version = str(provider_sec.get("version", ""))
    entry_point = str(provider_sec.get("entry_point", ""))

    provides_list = []
    for item in data.get("provides", []):
        cap_str = str(item.get("capability_id", ""))
        cap_id = CapabilityId.parse(cap_str) if cap_str else ""
        provides_list.append(
            ProvidedCapability(
                capability_id=cap_id,
                contract_version=str(item.get("contract_version", "")),
                cardinality=str(item.get("cardinality", "exactly_one")),
            )
        )

    requires_list = []
    for item in data.get("requires", []):
        cap_str = str(item.get("capability_id", ""))
        cap_id = CapabilityId.parse(cap_str) if cap_str else ""
        requires_list.append(
            RequiredCapability(
                capability_id=cap_id,
                contract_version=str(item.get("contract_version", "")),
                optional=bool(item.get("optional", False)),
            )
        )

    runtime_sec = data.get("runtime", {})
    profiles = tuple(str(x) for x in runtime_sec.get("profiles", ()))
    scopes = tuple(str(x) for x in runtime_sec.get("scopes", ()))
    effect_classes = tuple(str(x) for x in runtime_sec.get("effect_classes", ()))
    lifecycle = str(runtime_sec.get("lifecycle", "singleton"))
    reload_mode = str(runtime_sec.get("reload", "dynamic"))

    state_sec = data.get("state", {})
    state_schema_id = state_sec.get("schema_id")
    state_schema_version = state_sec.get("schema_version")
    migration_manifest = state_sec.get("migration_manifest")
    compatible_prior_majors = tuple(
        int(x) for x in state_sec.get("compatible_prior_majors", ())
    )
    if any(x <= 0 for x in compatible_prior_majors):
        msg = f"invalid provider manifest {path_obj}: compatible_prior_majors must contain positive integers"
        raise ManifestValidationError(msg)
    downgrade_policy = state_sec.get("downgrade_policy")
    uninstall_retention = state_sec.get("uninstall_retention")
    purge_auth = bool(state_sec.get("purge_requires_authorization", False))

    return ProviderManifest(
        id=provider_id,
        version=version,
        entry_point=entry_point,
        provides=tuple(provides_list),
        requires=tuple(requires_list),
        profiles=profiles,
        scopes=scopes,
        effect_classes=effect_classes,
        lifecycle=lifecycle,
        reload=reload_mode,
        state_schema_id=state_schema_id,
        state_schema_version=state_schema_version,
        migration_manifest=migration_manifest,
        compatible_prior_majors=compatible_prior_majors,
        downgrade_policy=downgrade_policy,
        uninstall_retention=uninstall_retention,
        purge_requires_authorization=purge_auth,
    )

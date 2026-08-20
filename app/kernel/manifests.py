"""Static manifest records and parser for spatiotemporal providers.

Traces to: P4-T02, Gate G4
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.kernel.errors import ManifestValidationError
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.profiles import RuntimeProfile


class Cardinality(StrEnum):
    """Supported cardinality between provider and capability."""

    EXACTLY_ONE = "exactly_one"
    ZERO_OR_ONE = "zero_or_one"
    ONE_OF_SEVERAL = "one_of_several"
    MANY = "many"


class OnMissing(StrEnum):
    """Policy when a required capability is missing."""

    FAIL_CLOSED = "fail_closed"
    DEGRADE = "degrade"
    SKIP = "skip"


class EffectClass(StrEnum):
    """Classification of side effects produced by a provider."""

    REVERSIBLE_EPHEMERAL = "reversible_ephemeral"
    DURABLE_COMPENSATABLE = "durable_compensatable"
    IRREVERSIBLE_EXTERNAL = "irreversible_external"


class LifecyclePolicy(StrEnum):
    """Lifecycle policy of a provider component."""

    PURE = "pure"
    SCOPED = "scoped"


class ReloadPolicy(StrEnum):
    """Policy for runtime configuration reloading."""

    CONFIG_RESTART = "config_restart"
    PROCESS_RESTART = "process_restart"


@dataclass(frozen=True, slots=True)
class ProvidedCapability:
    """Capability provided by a manifest."""

    capability_id: CapabilityId
    contract_version: SemanticVersion
    cardinality: Cardinality


@dataclass(frozen=True, slots=True)
class RequiredCapability:
    """Capability required by a manifest."""

    capability_id: CapabilityId
    supported_majors: tuple[int, ...]
    cardinality: Cardinality
    on_missing: OnMissing = OnMissing.FAIL_CLOSED


@dataclass(frozen=True, slots=True)
class ProviderManifest:
    """Complete static manifest for a provider implementation."""

    provider_id: ProviderId
    provider_version: SemanticVersion
    entry_point: str
    provides: tuple[ProvidedCapability, ...]
    requires: tuple[RequiredCapability, ...]
    optional_requires: tuple[RequiredCapability, ...]
    profiles: tuple[RuntimeProfile, ...]
    scopes: tuple[str, ...]
    effect_classes: tuple[EffectClass, ...]
    lifecycle: LifecyclePolicy
    reload: ReloadPolicy
    config_schema: str | None
    state_schema_id: str | None
    state_schema_version: SemanticVersion | None
    migration_manifest: str | None
    compatible_state_majors: tuple[int, ...]
    uninstall_retention: str | None
    purge_requires_authorization: bool


_ALLOWED_ROOT_KEYS = {
    "provider",
    "provides",
    "requires",
    "optional_requires",
    "runtime",
    "state",
}
_ALLOWED_PROVIDER_KEYS = {"id", "version", "entry_point", "config_schema"}
_ALLOWED_PROVIDES_KEYS = {"capability_id", "contract_version", "cardinality"}
_ALLOWED_REQUIRES_KEYS = {
    "capability_id",
    "supported_majors",
    "cardinality",
    "on_missing",
}
_ALLOWED_RUNTIME_KEYS = {"profiles", "scopes", "effect_classes", "lifecycle", "reload"}
_ALLOWED_STATE_KEYS = {
    "state_schema_id",
    "state_schema_version",
    "migration_manifest",
    "compatible_state_majors",
    "uninstall_retention",
    "purge_requires_authorization",
}


def _check_keys(
    data: dict[str, Any], allowed: set[str], path: Path, _table_name: str
) -> None:
    """Assert dictionary contains only allowed keys."""
    for k in data:
        if k not in allowed:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: unknown key {k!r}"
            )


def _check_required_keys(
    data: dict[str, Any], required: set[str], path: Path, _table_name: str
) -> None:
    """Assert dictionary contains all mandatory keys."""
    for k in required:
        if k not in data:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: missing key {k!r}"
            )


def load_manifest(path: Path) -> ProviderManifest:
    """Load and strictly validate a provider manifest TOML file.

    Args:
        path: Path to manifest.toml file.

    Returns:
        Immutable ProviderManifest object.

    Raises:
        ManifestValidationError: If file fails any schema or consistency check.
    """
    try:
        content = path.read_text(encoding="utf-8")
        data = tomllib.loads(content)
    except Exception as exc:
        raise ManifestValidationError(
            f"invalid provider manifest {path}: {exc}"
        ) from exc

    _check_keys(data, _ALLOWED_ROOT_KEYS, path, "root")
    _check_required_keys(data, {"provider", "runtime"}, path, "root")

    # 1. [provider]
    provider_tbl = data["provider"]
    if not isinstance(provider_tbl, dict):
        raise ManifestValidationError(
            f"invalid provider manifest {path}: [provider] must be a table"
        )
    _check_keys(provider_tbl, _ALLOWED_PROVIDER_KEYS, path, "[provider]")
    _check_required_keys(
        provider_tbl, {"id", "version", "entry_point"}, path, "[provider]"
    )

    try:
        provider_id = ProviderId.parse(provider_tbl["id"])
    except ValueError as exc:
        raise ManifestValidationError(
            f"invalid provider manifest {path}: {exc}"
        ) from exc

    try:
        provider_version = SemanticVersion.parse(provider_tbl["version"])
    except ValueError as exc:
        raise ManifestValidationError(
            f"invalid provider manifest {path}: {exc}"
        ) from exc

    entry_point = provider_tbl["entry_point"]
    if (
        not isinstance(entry_point, str)
        or ":" not in entry_point
        or len(entry_point.split(":")) != 2
    ):
        raise ManifestValidationError(
            f"invalid provider manifest {path}: entry_point must be '<module>:<factory>'"
        )
    mod_part, factory_part = entry_point.split(":")
    if not mod_part or not factory_part:
        raise ManifestValidationError(
            f"invalid provider manifest {path}: entry_point must be '<module>:<factory>'"
        )

    config_schema = provider_tbl.get("config_schema")
    if config_schema is not None and not isinstance(config_schema, str):
        raise ManifestValidationError(
            f"invalid provider manifest {path}: config_schema must be string"
        )

    # 2. [[provides]]
    provides_raw = data.get("provides", [])
    if not isinstance(provides_raw, list):
        raise ManifestValidationError(
            f"invalid provider manifest {path}: [[provides]] must be a list of tables"
        )

    provides_list: list[ProvidedCapability] = []
    seen_provided_ids: set[CapabilityId] = set()
    for item in provides_raw:
        if not isinstance(item, dict):
            raise ManifestValidationError(
                f"invalid provider manifest {path}: [[provides]] entry must be a table"
            )
        _check_keys(item, _ALLOWED_PROVIDES_KEYS, path, "[[provides]]")
        _check_required_keys(item, _ALLOWED_PROVIDES_KEYS, path, "[[provides]]")

        try:
            cap_id = CapabilityId.parse(item["capability_id"])
            c_ver = SemanticVersion.parse(item["contract_version"])
            card = Cardinality(item["cardinality"])
        except ValueError as exc:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: {exc}"
            ) from exc

        if cap_id in seen_provided_ids:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: duplicate provided capability {cap_id}"
            )
        seen_provided_ids.add(cap_id)
        provides_list.append(
            ProvidedCapability(
                capability_id=cap_id,
                contract_version=c_ver,
                cardinality=card,
            )
        )

    # 3. [[requires]]
    requires_raw = data.get("requires", [])
    if not isinstance(requires_raw, list):
        raise ManifestValidationError(
            f"invalid provider manifest {path}: [[requires]] must be a list of tables"
        )

    requires_list: list[RequiredCapability] = []
    seen_required_ids: set[CapabilityId] = set()
    for item in requires_raw:
        if not isinstance(item, dict):
            raise ManifestValidationError(
                f"invalid provider manifest {path}: [[requires]] entry must be a table"
            )
        _check_keys(item, _ALLOWED_REQUIRES_KEYS, path, "[[requires]]")
        _check_required_keys(
            item,
            {"capability_id", "supported_majors", "cardinality"},
            path,
            "[[requires]]",
        )

        try:
            cap_id = CapabilityId.parse(item["capability_id"])
            card = Cardinality(item["cardinality"])
            on_missing = OnMissing(item.get("on_missing", "fail_closed"))
        except ValueError as exc:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: {exc}"
            ) from exc

        majors_raw = item["supported_majors"]
        if not isinstance(majors_raw, list) or not all(
            isinstance(m, int) and m >= 1 for m in majors_raw
        ):
            raise ManifestValidationError(
                f"invalid provider manifest {path}: supported_majors must be list of positive ints"
            )
        supported_majors = tuple(sorted(set(majors_raw)))

        if cap_id in seen_required_ids:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: duplicate required capability {cap_id}"
            )
        seen_required_ids.add(cap_id)
        requires_list.append(
            RequiredCapability(
                capability_id=cap_id,
                supported_majors=supported_majors,
                cardinality=card,
                on_missing=on_missing,
            )
        )

    # 4. [[optional_requires]]
    opt_requires_raw = data.get("optional_requires", [])
    if not isinstance(opt_requires_raw, list):
        raise ManifestValidationError(
            f"invalid provider manifest {path}: [[optional_requires]] must be a list of tables"
        )

    opt_requires_list: list[RequiredCapability] = []
    for item in opt_requires_raw:
        if not isinstance(item, dict):
            raise ManifestValidationError(
                f"invalid provider manifest {path}: [[optional_requires]] entry must be a table"
            )
        _check_keys(item, _ALLOWED_REQUIRES_KEYS, path, "[[optional_requires]]")
        _check_required_keys(
            item,
            {"capability_id", "supported_majors", "cardinality"},
            path,
            "[[optional_requires]]",
        )

        try:
            cap_id = CapabilityId.parse(item["capability_id"])
            card = Cardinality(item["cardinality"])
            on_missing = OnMissing(item.get("on_missing", "fail_closed"))
        except ValueError as exc:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: {exc}"
            ) from exc

        majors_raw = item["supported_majors"]
        if not isinstance(majors_raw, list) or not all(
            isinstance(m, int) and m >= 1 for m in majors_raw
        ):
            raise ManifestValidationError(
                f"invalid provider manifest {path}: supported_majors must be list of positive ints"
            )
        supported_majors = tuple(sorted(set(majors_raw)))

        if cap_id in seen_required_ids:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: duplicate required capability {cap_id}"
            )
        seen_required_ids.add(cap_id)
        opt_requires_list.append(
            RequiredCapability(
                capability_id=cap_id,
                supported_majors=supported_majors,
                cardinality=card,
                on_missing=on_missing,
            )
        )

    # 5. [runtime]
    runtime_tbl = data["runtime"]
    if not isinstance(runtime_tbl, dict):
        raise ManifestValidationError(
            f"invalid provider manifest {path}: [runtime] must be a table"
        )
    _check_keys(runtime_tbl, _ALLOWED_RUNTIME_KEYS, path, "[runtime]")
    _check_required_keys(runtime_tbl, _ALLOWED_RUNTIME_KEYS, path, "[runtime]")

    try:
        profiles = tuple(sorted({RuntimeProfile(p) for p in runtime_tbl["profiles"]}))
        scopes = tuple(sorted({str(s) for s in runtime_tbl["scopes"]}))
        effect_classes = tuple(
            sorted({EffectClass(e) for e in runtime_tbl["effect_classes"]})
        )
        lifecycle = LifecyclePolicy(runtime_tbl["lifecycle"])
        reload = ReloadPolicy(runtime_tbl["reload"])
    except ValueError as exc:
        raise ManifestValidationError(
            f"invalid provider manifest {path}: {exc}"
        ) from exc

    # 6. [state] (optional)
    state_tbl = data.get("state")
    if state_tbl is not None:
        if not isinstance(state_tbl, dict):
            raise ManifestValidationError(
                f"invalid provider manifest {path}: [state] must be a table"
            )
        _check_keys(state_tbl, _ALLOWED_STATE_KEYS, path, "[state]")
        if set(state_tbl.keys()) != _ALLOWED_STATE_KEYS:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: state fields must be all present or all absent"
            )

        try:
            state_schema_id = str(state_tbl["state_schema_id"])
            state_schema_version = SemanticVersion.parse(
                state_tbl["state_schema_version"]
            )
            migration_manifest = str(state_tbl["migration_manifest"])
            compatible_state_majors = tuple(
                sorted({int(m) for m in state_tbl["compatible_state_majors"]})
            )
            uninstall_retention = str(state_tbl["uninstall_retention"])
            purge_requires_auth = bool(state_tbl["purge_requires_authorization"])
        except ValueError as exc:
            raise ManifestValidationError(
                f"invalid provider manifest {path}: {exc}"
            ) from exc
    else:
        state_schema_id = None
        state_schema_version = None
        migration_manifest = None
        compatible_state_majors = ()
        uninstall_retention = None
        purge_requires_auth = False

    return ProviderManifest(
        provider_id=provider_id,
        provider_version=provider_version,
        entry_point=entry_point,
        provides=tuple(provides_list),
        requires=tuple(requires_list),
        optional_requires=tuple(opt_requires_list),
        profiles=profiles,
        scopes=scopes,
        effect_classes=effect_classes,
        lifecycle=lifecycle,
        reload=reload,
        config_schema=config_schema,
        state_schema_id=state_schema_id,
        state_schema_version=state_schema_version,
        migration_manifest=migration_manifest,
        compatible_state_majors=compatible_state_majors,
        uninstall_retention=uninstall_retention,
        purge_requires_authorization=purge_requires_auth,
    )


__all__ = (
    "Cardinality",
    "EffectClass",
    "LifecyclePolicy",
    "OnMissing",
    "ProvidedCapability",
    "ProviderManifest",
    "ReloadPolicy",
    "RequiredCapability",
    "load_manifest",
)

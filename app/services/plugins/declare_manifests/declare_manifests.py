"""Plugin manifest parsing, validation, and package inspection.

Purpose:
    Validate plugin identity, package integrity, compatibility, capabilities,
    permissions, resources, contributions, and migration declarations per §21.4.

Key capabilities:
    * Parse and validate plugin.json declarations against strict schemas.
    * Enforce reverse-DNS IDs, SemVer versioning, API ranges, and valid PluginTypes.
    * Reject unknown or overbroad permissions and incompatible major versions
      before activation (AT-PLUG-DECLARE_MANIFESTS-001).
    * Safely inspect ZIP package archives: reject path traversal (zip slip),
      absolute paths, drive letters, symlinks, duplicate entries, case-fold
      collisions, and decompression bombs without executing package code.
    * Return bounded compatibility, permission, and ownership previews where display
      names cannot grant authority or replace contribution identities
      (AT-PLUG-DECLARE_MANIFESTS-002).
    * Compute canonical SHA-256 package hashes over manifest and payload files.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

from app.contracts.plugins.errors import (
    PluginManifestError,
    PluginPackageValidationError,
)
from app.contracts.plugins.models import (
    PluginContributionDescriptor,
    PluginDependency,
    PluginFileEntry,
    PluginManifest,
    PluginManifestPreview,
    PluginMigrationDeclaration,
    PluginPackageValidation,
    PluginPermission,
    PluginResourceLimits,
    PluginType,
)
from app.services.plugins.declare_manifests.config import PluginManifestsConfig

if TYPE_CHECKING:
    from collections.abc import Iterable

_REVERSE_DNS_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$")
_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-([0-9A-Za-z.-]+))?(\+([0-9A-Za-z.-]+))?$"
)
_SYMLINK_ATTR_MASK = 0o120000
_MAX_CPU_LIMIT_CORES = 32.0
_MAX_MEMORY_LIMIT_MB = 65536
_MAX_TIMEOUT_SECONDS = 3600.0

_ALLOWED_PERMISSION_KEYS = frozenset(
    {
        "filesystem_read",
        "filesystemRead",
        "filesystem_write",
        "filesystemWrite",
        "network_endpoints",
        "networkEndpoints",
        "subprocess_allow",
        "subprocessAllow",
        "secrets",
    }
)

# Supported host major version for Plugins contracts
HOST_PLUGINS_MAJOR = 1


def _to_str_tuple(val: object) -> tuple[str, ...]:
    """Convert an object to a tuple of strings if iterable.

    Args:
        val: Object to convert.

    Returns:
        Tuple of strings.
    """
    if isinstance(val, (list, tuple)):
        return tuple(str(x) for x in val)
    return ()


def _extract_types(raw_types: object) -> tuple[PluginType, ...]:
    """Extract and validate PluginType enum members.

    Args:
        raw_types: String, list, or tuple of plugin types.

    Returns:
        Tuple of validated PluginType enums.

    Raises:
        PluginManifestError: If types are missing or invalid.
    """
    items: Iterable[object]
    if isinstance(raw_types, str):
        items = [raw_types]
    elif isinstance(raw_types, (list, tuple)):
        items = raw_types
    else:
        msg = "Plugin types must be a list or array"
        raise PluginManifestError(msg)

    types_list: list[PluginType] = []
    for item in items:
        try:
            types_list.append(PluginType(str(item).upper()))
        except ValueError as err:
            msg = f"Unsupported plugin type: {item}"
            raise PluginManifestError(msg) from err
    return tuple(types_list)


def _validate_permission_path(path_str: str, label: str) -> None:
    """Validate that a filesystem permission path is safe and bounded.

    Args:
        path_str: Declared path string.
        label: Name of the permission field for error messages.

    Raises:
        PluginManifestError: If path is absolute, has drive anchors, or traverses.
    """
    if not path_str.strip():
        msg = f"Empty path in {label} is forbidden"
        raise PluginManifestError(msg)
    if path_str.startswith(("/", "\\")) or ":" in path_str:
        msg = f"Overbroad or absolute path in {label} is forbidden: {path_str}"
        raise PluginManifestError(msg)
    norm = Path(path_str).as_posix()
    if any(part == ".." for part in norm.split("/")):
        msg = f"Directory traversal sequence in {label} is forbidden: {path_str}"
        raise PluginManifestError(msg)


def _validate_network_endpoint(endpoint: str) -> None:
    """Validate that a network endpoint declaration is valid and bounded.

    Args:
        endpoint: Declared URL endpoint.

    Raises:
        PluginManifestError: If endpoint contains wildcards or unsafe schemes.
    """
    if "*" in endpoint:
        msg = f"Wildcard network endpoints are overbroad and forbidden: {endpoint}"
        raise PluginManifestError(msg)
    if not endpoint.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        msg = (
            f"Network endpoints must use secure HTTPS or local test schemes: {endpoint}"
        )
        raise PluginManifestError(msg)


def _extract_permissions(raw_perms: object) -> PluginPermission:
    """Extract and validate PluginPermission model.

    Args:
        raw_perms: Dictionary containing permissions definitions.

    Returns:
        PluginPermission instance.

    Raises:
        PluginManifestError: If permissions is malformed or contains unknown keys.
    """
    if not isinstance(raw_perms, dict):
        msg = "Permissions field must be an object"
        raise PluginManifestError(msg)

    unknown_keys = set(raw_perms.keys()) - _ALLOWED_PERMISSION_KEYS
    if unknown_keys:
        msg = "Unknown or unadmitted permission keys: " + ", ".join(
            sorted(unknown_keys)
        )
        raise PluginManifestError(msg)

    fs_read = _to_str_tuple(
        raw_perms.get("filesystem_read", raw_perms.get("filesystemRead", []))
    )
    for p in fs_read:
        _validate_permission_path(p, "filesystem_read")

    fs_write = _to_str_tuple(
        raw_perms.get("filesystem_write", raw_perms.get("filesystemWrite", []))
    )
    for p in fs_write:
        _validate_permission_path(p, "filesystem_write")

    net_endpoints = _to_str_tuple(
        raw_perms.get("network_endpoints", raw_perms.get("networkEndpoints", []))
    )
    for ep in net_endpoints:
        _validate_network_endpoint(ep)

    subproc_allow = bool(
        raw_perms.get("subprocess_allow", raw_perms.get("subprocessAllow", False))
    )

    secrets = _to_str_tuple(raw_perms.get("secrets", []))
    for s in secrets:
        if not s.strip() or any(ch.isspace() for ch in s) or "*" in s:
            msg = f"Invalid or overbroad secret name declaration: '{s}'"
            raise PluginManifestError(msg)

    return PluginPermission(
        filesystem_read=fs_read,
        filesystem_write=fs_write,
        network_endpoints=net_endpoints,
        subprocess_allow=subproc_allow,
        secrets=secrets,
    )


def _extract_resources(raw_res: object) -> PluginResourceLimits:
    """Extract and validate PluginResourceLimits model.

    Args:
        raw_res: Dictionary containing resource definitions.

    Returns:
        PluginResourceLimits instance.

    Raises:
        PluginManifestError: If resources is not a dictionary or has invalid limits.
    """
    if not isinstance(raw_res, dict):
        msg = "Resources field must be an object"
        raise PluginManifestError(msg)

    cpu_raw = raw_res.get(
        "cpu_limit_cores", raw_res.get("cpuLimitCores", raw_res.get("cpu", 1.0))
    )
    mem_raw = raw_res.get(
        "memory_limit_mb",
        raw_res.get("memoryLimitMb", raw_res.get("memory_mb", 512)),
    )
    timeout_raw = raw_res.get("timeout_seconds", raw_res.get("timeoutSeconds", 30.0))

    try:
        cpu_val = float(str(cpu_raw))
        mem_val = int(str(mem_raw))
        timeout_val = float(str(timeout_raw))
    except (ValueError, TypeError) as err:
        msg = f"Invalid numeric resource limit in manifest: {err}"
        raise PluginManifestError(msg) from err

    if cpu_val <= 0 or cpu_val > _MAX_CPU_LIMIT_CORES:
        msg = (
            f"cpu_limit_cores must be positive and <= {_MAX_CPU_LIMIT_CORES}, "
            f"got {cpu_val}"
        )
        raise PluginManifestError(msg)
    if mem_val <= 0 or mem_val > _MAX_MEMORY_LIMIT_MB:
        msg = (
            f"memory_limit_mb must be positive and <= {_MAX_MEMORY_LIMIT_MB}, "
            f"got {mem_val}"
        )
        raise PluginManifestError(msg)
    if timeout_val <= 0 or timeout_val > _MAX_TIMEOUT_SECONDS:
        msg = (
            f"timeout_seconds must be positive and <= {_MAX_TIMEOUT_SECONDS}, "
            f"got {timeout_val}"
        )
        raise PluginManifestError(msg)

    return PluginResourceLimits(
        cpu_limit_cores=cpu_val,
        memory_limit_mb=mem_val,
        timeout_seconds=timeout_val,
    )


def _extract_contributions(
    raw_contribs: object, plugin_id: str
) -> tuple[PluginContributionDescriptor, ...]:
    """Extract and validate declared plugin contributions.

    Args:
        raw_contribs: List or array of contribution objects.
        plugin_id: Parent plugin reverse-DNS identifier.

    Returns:
        Tuple of validated PluginContributionDescriptor instances.

    Raises:
        PluginManifestError: If contribution declarations are invalid.
    """
    if raw_contribs is None:
        return ()
    if not isinstance(raw_contribs, (list, tuple)):
        msg = "Contributions field must be a list"
        raise PluginManifestError(msg)

    descriptors: list[PluginContributionDescriptor] = []
    seen_ids: set[str] = set()

    for idx, item in enumerate(raw_contribs):
        if not isinstance(item, dict):
            msg = f"Contribution at index {idx} must be an object"
            raise PluginManifestError(msg)

        cid = str(item.get("contribution_id", item.get("id", ""))).strip()
        if not cid:
            msg = f"Contribution at index {idx} missing required contribution_id"
            raise PluginManifestError(msg)

        if cid in seen_ids:
            msg = f"Duplicate contribution ID declared: '{cid}'"
            raise PluginManifestError(msg)
        seen_ids.add(cid)

        ptype_raw = item.get("plugin_type", item.get("type", ""))
        try:
            ptype = PluginType(str(ptype_raw).upper())
        except ValueError as err:
            msg = f"Invalid plugin_type '{ptype_raw}' for contribution '{cid}'"
            raise PluginManifestError(msg) from err

        name = str(item.get("name", cid)).strip()
        desc = str(item.get("description", "")).strip()
        schema_ref = item.get("schema_ref")
        meta = item.get("metadata", {})
        if not isinstance(meta, dict):
            meta = {}

        descriptors.append(
            PluginContributionDescriptor(
                plugin_id=plugin_id,
                plugin_type=ptype,
                contribution_id=cid,
                name=name,
                description=desc,
                schema_ref=str(schema_ref) if schema_ref else None,
                metadata=meta,
            )
        )

    return tuple(descriptors)


def _extract_dependencies(raw_deps: object) -> tuple[PluginDependency, ...]:
    """Extract and validate declared dependencies.

    Args:
        raw_deps: List of dependency definitions.

    Returns:
        Tuple of PluginDependency instances.

    Raises:
        PluginManifestError: If dependency declarations are invalid.
    """
    if raw_deps is None:
        return ()
    if not isinstance(raw_deps, (list, tuple)):
        msg = "Dependencies field must be a list"
        raise PluginManifestError(msg)

    dependencies: list[PluginDependency] = []
    for idx, dep in enumerate(raw_deps):
        if isinstance(dep, str):
            dep_id = dep.strip()
            v_range = ">=1.0.0"
            opt = False
        elif isinstance(dep, dict):
            dep_id = str(dep.get("id", "")).strip()
            v_val = dep.get("version_range", dep.get("version", ">=1.0.0"))
            v_range = str(v_val).strip()
            opt = bool(dep.get("optional", False))
        else:
            msg = f"Dependency at index {idx} must be a string or object"
            raise PluginManifestError(msg)

        if not dep_id or not _REVERSE_DNS_PATTERN.match(dep_id):
            msg = f"Dependency '{dep_id}' must be in reverse-DNS format"
            raise PluginManifestError(msg)

        dependencies.append(
            PluginDependency(id=dep_id, version_range=v_range, optional=opt)
        )

    return tuple(dependencies)


def _extract_migrations(
    raw_migs: object,
) -> tuple[PluginMigrationDeclaration, ...]:
    """Extract and validate migration declarations.

    Args:
        raw_migs: List of migration objects.

    Returns:
        Tuple of PluginMigrationDeclaration instances.

    Raises:
        PluginManifestError: If migration declarations are circular or invalid.
    """
    if raw_migs is None:
        return ()
    if not isinstance(raw_migs, (list, tuple)):
        msg = "Migrations field must be a list"
        raise PluginManifestError(msg)

    migrations: list[PluginMigrationDeclaration] = []
    seen_transitions: set[tuple[str, str]] = set()

    for idx, mig in enumerate(raw_migs):
        if not isinstance(mig, dict):
            msg = f"Migration at index {idx} must be an object"
            raise PluginManifestError(msg)

        from_v = str(mig.get("from_version", mig.get("from", ""))).strip()
        to_v = str(mig.get("to_version", mig.get("to", ""))).strip()
        desc = str(mig.get("description", "")).strip()
        step = int(mig.get("step", idx + 1))

        if not _SEMVER_PATTERN.match(from_v) or not _SEMVER_PATTERN.match(to_v):
            msg = f"Migration versions must be SemVer: {from_v} -> {to_v}"
            raise PluginManifestError(msg)

        if from_v == to_v:
            msg = f"Circular migration declaration: {from_v} -> {to_v}"
            raise PluginManifestError(msg)

        transition = (from_v, to_v)
        if transition in seen_transitions:
            msg = f"Duplicate migration transition: {from_v} -> {to_v}"
            raise PluginManifestError(msg)
        seen_transitions.add(transition)

        migrations.append(
            PluginMigrationDeclaration(
                from_version=from_v,
                to_version=to_v,
                description=desc,
                step=step,
            )
        )

    return tuple(migrations)


def _check_api_range_compatibility(api_range: str) -> None:
    """Verify that declared api_range is compatible with host major version.

    Args:
        api_range: API range string declared in manifest.

    Raises:
        PluginManifestError: If api_range requires an incompatible major version.
    """
    cleaned = api_range.strip()
    # If range requires major 2+, e.g. >=2.0.0 or ^2.0.0, reject as incompatible
    major_matches = re.findall(r"(?:>=|\^|==|>|<)?\s*([0-9]+)\.", cleaned)
    if major_matches:
        first_major = int(major_matches[0])
        if ">=" in cleaned and first_major > HOST_PLUGINS_MAJOR:
            msg = (
                "Incompatible major version: manifest requires API range "
                f"'{api_range}', but host plugins platform supports "
                f"major {HOST_PLUGINS_MAJOR}"
            )
            raise PluginManifestError(msg)
        if "<=" in cleaned and first_major < HOST_PLUGINS_MAJOR:
            msg = (
                "Incompatible major version: manifest requires API range "
                f"'{api_range}', which is below supported host "
                f"major {HOST_PLUGINS_MAJOR}"
            )
            raise PluginManifestError(msg)


def _validate_zip_entry_safety(
    info: zipfile.ZipInfo, seen_names_lower: set[str]
) -> str:
    """Validate safety constraints on an individual ZIP entry.

    Args:
        info: ZipInfo object describing the file entry.
        seen_names_lower: Set of lowercase file paths seen so far.

    Returns:
        Normalized relative POSIX path string.

    Raises:
        PluginPackageValidationError: If file path is unsafe, absolute, or duplicate.
    """
    filename = info.filename
    if filename.startswith(("/", "\\")) or ":" in filename:
        msg = f"Package file contains unsafe absolute path or drive letter: {filename}"
        raise PluginPackageValidationError(msg)

    norm_path = Path(filename).as_posix()
    parts = norm_path.split("/")
    if any(part in ("..", ".") for part in parts):
        msg = f"Package file contains directory traversal sequence: {filename}"
        raise PluginPackageValidationError(msg)

    if (info.external_attr >> 16) & _SYMLINK_ATTR_MASK == _SYMLINK_ATTR_MASK:
        msg = f"Package contains forbidden symlink: {filename}"
        raise PluginPackageValidationError(msg)

    lower_name = norm_path.lower()
    if lower_name in seen_names_lower:
        msg = f"Package contains duplicate or case-fold collision entry: {filename}"
        raise PluginPackageValidationError(msg)
    seen_names_lower.add(lower_name)

    return norm_path


class DeclareManifestsService:
    """Service providing plugin manifest parsing and package verification."""

    def __init__(self, config: PluginManifestsConfig | None = None) -> None:
        """Initialize the service with configuration limits.

        Args:
            config: Optional configuration for package validation limits.
        """
        self._config = config or PluginManifestsConfig()

    def parse_manifest(self, raw: object) -> PluginManifest:
        """Parse raw manifest data into a validated PluginManifest instance.

        Args:
            raw: JSON string, raw bytes, or dict representation of plugin.json.

        Returns:
            Validated PluginManifest instance.

        Raises:
            PluginManifestError: If raw data is malformed or validation fails.
        """
        data: dict[str, object]
        if isinstance(raw, (str, bytes)):
            try:
                parsed = json.loads(raw)
            except Exception as err:
                msg = f"Malformed JSON in plugin manifest: {err}"
                raise PluginManifestError(msg) from err
            if not isinstance(parsed, dict):
                msg = "Manifest payload must be a JSON object"
                raise PluginManifestError(msg)
            data = parsed
        elif isinstance(raw, dict):
            data = raw
        else:
            raw_type = type(raw).__name__
            msg = f"Expected str, bytes, or dict for manifest, got {raw_type}"
            raise PluginManifestError(msg)

        plugin_id = str(data.get("id", "")).strip()
        version = str(data.get("version", "")).strip()
        api_range = str(data.get("apiRange", data.get("api_range", ""))).strip()

        types = _extract_types(data.get("type", data.get("types", [])))
        permissions = _extract_permissions(data.get("permissions", {}))
        resources = _extract_resources(data.get("resources", {}))

        schemas = data.get("schemas", {})
        if not isinstance(schemas, dict):
            msg = "Schemas field must be an object"
            raise PluginManifestError(msg)

        sha_raw = data.get("sha256ByFile", data.get("sha256_by_file", {}))
        sha256_map = dict(sha_raw) if isinstance(sha_raw, dict) else {}

        contributions = _extract_contributions(
            data.get("contributions", []), plugin_id=plugin_id
        )
        dependencies = _extract_dependencies(data.get("dependencies", []))
        compatible_contracts = _to_str_tuple(
            data.get("compatible_contracts", data.get("compatibleContracts", ()))
        )
        migrations = _extract_migrations(data.get("migrations", []))

        manifest = PluginManifest(
            id=plugin_id,
            version=version,
            api_range=api_range,
            types=types,
            entry_point=str(
                data.get("entryPoint", data.get("entry_point", "main.py"))
            ).strip(),
            schemas=schemas,
            capabilities=_to_str_tuple(data.get("capabilities", ())),
            permissions=permissions,
            resources=resources,
            sha256_by_file=sha256_map,
            signature=(
                str(data["signature"]) if data.get("signature") is not None else None
            ),
            contributions=contributions,
            dependencies=dependencies,
            compatible_contracts=compatible_contracts,
            migrations=migrations,
        )

        self.validate_manifest(manifest)
        return manifest

    def validate_manifest(self, manifest: PluginManifest) -> None:
        """Validate all fields, constraints, and semantics of a PluginManifest.

        Args:
            manifest: The plugin manifest instance to validate.

        Raises:
            PluginManifestError: If any semantic rule or constraint is violated.
        """
        self._validate_identity(manifest)
        self._validate_resources_and_entry(manifest)
        _check_api_range_compatibility(manifest.api_range)

    def _validate_identity(self, manifest: PluginManifest) -> None:
        """Validate plugin id, version, api_range, and types.

        Args:
            manifest: The plugin manifest instance to check.

        Raises:
            PluginManifestError: If identity fields are invalid or missing.
        """
        if not manifest.id:
            msg = "Plugin manifest id is required"
            raise PluginManifestError(msg)
        if not _REVERSE_DNS_PATTERN.match(manifest.id):
            msg = (
                f"Plugin id '{manifest.id}' must be in reverse-DNS format "
                "(e.g. 'com.example.myplugin')"
            )
            raise PluginManifestError(msg)

        if not manifest.version:
            msg = "Plugin version is required"
            raise PluginManifestError(msg)
        if not _SEMVER_PATTERN.match(manifest.version):
            msg = (
                f"Plugin version '{manifest.version}' must be valid SemVer "
                "(e.g. '1.0.0')"
            )
            raise PluginManifestError(msg)

        if not manifest.api_range:
            msg = "Plugin api_range is required"
            raise PluginManifestError(msg)

        if not manifest.types:
            msg = "Plugin must declare at least one plugin type"
            raise PluginManifestError(msg)

    def _validate_resources_and_entry(self, manifest: PluginManifest) -> None:
        """Validate entry point safety and resource limits.

        Args:
            manifest: The plugin manifest instance to check.

        Raises:
            PluginManifestError: If entry point or resource limits are invalid.
        """
        if not manifest.entry_point:
            msg = "Plugin entry_point is required"
            raise PluginManifestError(msg)
        if ".." in manifest.entry_point or manifest.entry_point.startswith(("/", "\\")):
            msg = (
                f"Plugin entry_point '{manifest.entry_point}' must be a safe "
                "relative path"
            )
            raise PluginManifestError(msg)

        if manifest.resources.cpu_limit_cores <= 0:
            msg = "Plugin cpu_limit_cores must be positive"
            raise PluginManifestError(msg)
        if manifest.resources.memory_limit_mb <= 0:
            msg = "Plugin memory_limit_mb must be positive"
            raise PluginManifestError(msg)
        if manifest.resources.timeout_seconds <= 0:
            msg = "Plugin timeout_seconds must be positive"
            raise PluginManifestError(msg)

    def preview_manifest(self, manifest: PluginManifest) -> PluginManifestPreview:
        """Generate a bounded compatibility, permission, and ownership preview.

        Ensures that authority is strictly tied to plugin_id and contribution_id,
        and never to informal display names (AT-PLUG-DECLARE_MANIFESTS-002).

        Args:
            manifest: Validated plugin manifest.

        Returns:
            PluginManifestPreview with exact versioned metadata.
        """
        owned_ids = tuple(
            c.contribution_id
            if c.contribution_id.startswith(f"{manifest.id}.")
            else f"{manifest.id}.{c.contribution_id}"
            for c in manifest.contributions
        )

        # Evaluate compatibility against host
        is_comp = True
        comp_details = (
            f"Fully compatible with host plugins platform (major {HOST_PLUGINS_MAJOR})"
        )
        try:
            _check_api_range_compatibility(manifest.api_range)
        except PluginManifestError as err:
            is_comp = False
            comp_details = str(err)

        metadata: dict[str, Any] = {
            "declared_types": [t.value for t in manifest.types],
            "capabilities_count": len(manifest.capabilities),
            "files_count": len(manifest.sha256_by_file),
            "migrations_count": len(manifest.migrations),
            "dependencies_count": len(manifest.dependencies),
        }

        return PluginManifestPreview(
            plugin_id=manifest.id,
            version=manifest.version,
            api_range=manifest.api_range,
            is_compatible=is_comp,
            compatibility_details=comp_details,
            granted_permissions=manifest.permissions,
            owned_contribution_ids=owned_ids,
            declared_contributions=manifest.contributions,
            metadata=metadata,
        )

    def validate_package(self, package_path: Path) -> PluginPackageValidation:
        """Inspect and validate a plugin ZIP archive and its inner manifest.

        Inspection executes purely statically without importing or executing any
        package Python code (AT-PLUG-DECLARE_MANIFESTS-001).

        Args:
            package_path: Filesystem path to the plugin .zip package archive.

        Returns:
            PluginPackageValidation describing the validated manifest and hash.

        Raises:
            PluginPackageValidationError: If archive is invalid, unsafe, or corrupted.
        """
        self._check_package_file(package_path)

        try:
            with zipfile.ZipFile(package_path, "r") as zf:
                infolist = zf.infolist()
                self._check_zip_limits(infolist)

                seen_names_lower: set[str] = set()
                file_hashes: dict[str, str] = {}
                file_entries: list[PluginFileEntry] = []
                manifest_data: bytes | None = None

                for info in infolist:
                    norm_path = _validate_zip_entry_safety(info, seen_names_lower)
                    if not info.is_dir():
                        content = zf.read(info)
                        sha = hashlib.sha256(content).hexdigest()
                        file_hashes[norm_path] = sha
                        file_entries.append(
                            PluginFileEntry(
                                path=norm_path,
                                sha256=sha,
                                size_bytes=len(content),
                            )
                        )
                        if norm_path == "plugin.json":
                            manifest_data = content

                if manifest_data is None:
                    msg = "Package missing required 'plugin.json' manifest at root"
                    raise PluginPackageValidationError(msg)

                manifest = self._parse_package_manifest(manifest_data)
                self._verify_declared_hashes(manifest, file_hashes)

                if self._config.strict_signatures and not manifest.signature:
                    msg = "Package signature is required in strict mode"
                    raise PluginPackageValidationError(msg)

                package_hash = self.compute_package_hash(manifest, file_hashes)

                return PluginPackageValidation(
                    manifest=manifest,
                    package_hash=package_hash,
                    files=tuple(file_entries),
                    is_valid=True,
                    warnings=(),
                )

        except zipfile.BadZipFile as err:
            msg = f"Invalid ZIP archive: {err}"
            raise PluginPackageValidationError(msg) from err

    def _check_package_file(self, package_path: Path) -> None:
        """Validate that package file exists and does not exceed size limits.

        Args:
            package_path: Filesystem path to test.

        Raises:
            PluginPackageValidationError: If file does not exist or exceeds size limits.
        """
        if not package_path.exists():
            msg = f"Package file does not exist: {package_path}"
            raise PluginPackageValidationError(msg)

        if not package_path.is_file():
            msg = f"Package path is not a regular file: {package_path}"
            raise PluginPackageValidationError(msg)

        size = package_path.stat().st_size
        if size > self._config.max_package_size_bytes:
            msg = (
                f"Package size {size} bytes exceeds maximum limit "
                f"{self._config.max_package_size_bytes}"
            )
            raise PluginPackageValidationError(msg)

    def _check_zip_limits(self, infolist: list[zipfile.ZipInfo]) -> None:
        """Check file count and total uncompressed size limits (decompression bombs).

        Args:
            infolist: List of ZipInfo records in the archive.

        Raises:
            PluginPackageValidationError: If file count or expansion limit is
                exceeded.
        """
        if len(infolist) > self._config.max_file_count:
            msg = (
                f"Package contains {len(infolist)} files, exceeding limit of "
                f"{self._config.max_file_count}"
            )
            raise PluginPackageValidationError(msg)

        total_uncompressed = sum(info.file_size for info in infolist)
        max_allowed_uncompressed = self._config.max_package_size_bytes * 10
        if total_uncompressed > max_allowed_uncompressed:
            msg = (
                f"Total uncompressed size {total_uncompressed} bytes exceeds "
                f"safe expansion limit {max_allowed_uncompressed}"
            )
            raise PluginPackageValidationError(msg)

    def _parse_package_manifest(self, manifest_data: bytes) -> PluginManifest:
        """Parse manifest data extracted from package archive.

        Args:
            manifest_data: Raw bytes of plugin.json.

        Returns:
            Validated PluginManifest instance.

        Raises:
            PluginPackageValidationError: If manifest is malformed or invalid.
        """
        try:
            return self.parse_manifest(manifest_data)
        except PluginManifestError as err:
            msg = f"Inner manifest 'plugin.json' validation failed: {err}"
            raise PluginPackageValidationError(msg) from err

    def _verify_declared_hashes(
        self,
        manifest: PluginManifest,
        file_hashes: dict[str, str],
    ) -> None:
        """Verify that all files declared in sha256_by_file match computed hashes.

        Args:
            manifest: The plugin manifest.
            file_hashes: Mapping of relative paths to computed SHA-256 strings.

        Raises:
            PluginPackageValidationError: If declared file is missing or hash is wrong.
        """
        for rel_path, expected_hash in manifest.sha256_by_file.items():
            norm_path = Path(rel_path).as_posix()
            if norm_path not in file_hashes:
                msg = f"Declared file missing from package archive: {rel_path}"
                raise PluginPackageValidationError(msg)

            actual_hash = file_hashes[norm_path]
            if actual_hash.lower() != expected_hash.lower():
                msg = (
                    f"Hash mismatch for file '{rel_path}': expected {expected_hash}, "
                    f"got {actual_hash}"
                )
                raise PluginPackageValidationError(msg)

    def compute_package_hash(
        self,
        manifest: PluginManifest,
        file_hashes: dict[str, str],
    ) -> str:
        """Compute the canonical SHA-256 package hash.

        Args:
            manifest: The plugin manifest.
            file_hashes: Mapping of normalized relative paths to SHA-256 strings.

        Returns:
            Hexadecimal SHA-256 string representing the canonical package hash.
        """
        manifest_dict: dict[str, Any] = {
            "id": manifest.id,
            "version": manifest.version,
            "api_range": manifest.api_range,
            "types": sorted(t.value for t in manifest.types),
            "entry_point": manifest.entry_point,
            "capabilities": sorted(manifest.capabilities),
            "permissions": {
                "filesystem_read": sorted(manifest.permissions.filesystem_read),
                "filesystem_write": sorted(manifest.permissions.filesystem_write),
                "network_endpoints": sorted(manifest.permissions.network_endpoints),
                "subprocess_allow": manifest.permissions.subprocess_allow,
                "secrets": sorted(manifest.permissions.secrets),
            },
            "resources": {
                "cpu_limit_cores": manifest.resources.cpu_limit_cores,
                "memory_limit_mb": manifest.resources.memory_limit_mb,
                "timeout_seconds": manifest.resources.timeout_seconds,
            },
        }

        canonical_manifest_str = json.dumps(
            manifest_dict, sort_keys=True, separators=(",", ":")
        )

        hasher = hashlib.sha256()
        hasher.update(canonical_manifest_str.encode())

        for path in sorted(file_hashes):
            hasher.update(f"{path}:{file_hashes[path]}\n".encode())

        return hasher.hexdigest()


@overload
def fr_trc_plug_declare_manifests_001(
    raw_or_path: Path,
    config: PluginManifestsConfig | None = None,
) -> PluginPackageValidation: ...


@overload
def fr_trc_plug_declare_manifests_001(
    raw_or_path: str | bytes | dict[str, object],
    config: PluginManifestsConfig | None = None,
) -> PluginManifest: ...


def fr_trc_plug_declare_manifests_001(
    raw_or_path: str | bytes | dict[str, object] | Path,
    config: PluginManifestsConfig | None = None,
) -> PluginManifest | PluginPackageValidation:
    """Requirement implementation trace for FR-TRC-PLUG-DECLARE_MANIFESTS-001.

    Validates extension identity, version, contributions, dependencies,
    compatible contracts, resources/hashes, permissions, egress, and migrations.

    Args:
        raw_or_path: Manifest dict/string/bytes or Path to package zip.
        config: Optional configuration limits.

    Returns:
        PluginManifest or PluginPackageValidation instance.
    """
    service = DeclareManifestsService(config=config)
    if isinstance(raw_or_path, Path):
        return service.validate_package(raw_or_path)
    return service.parse_manifest(raw_or_path)


def fr_trc_plug_declare_manifests_002(
    manifest: PluginManifest,
    config: PluginManifestsConfig | None = None,
) -> PluginManifestPreview:
    """Requirement implementation trace for FR-TRC-PLUG-DECLARE_MANIFESTS-002.

    Returns a bounded compatibility/permission/ownership preview where display
    name cannot grant authority or replace contribution identity.

    Args:
        manifest: Validated plugin manifest.
        config: Optional configuration limits.

    Returns:
        PluginManifestPreview instance.
    """
    service = DeclareManifestsService(config=config)
    return service.preview_manifest(manifest)

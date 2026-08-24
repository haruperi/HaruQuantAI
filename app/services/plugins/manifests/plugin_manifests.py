"""Plugin manifest parsing, validation, and package inspection.

Purpose:
    Validate plugin identity, package integrity, compatibility, capabilities,
    permissions, and resource declarations per §21.4.

Key capabilities:
    * Parse and validate plugin.json declarations against strict schemas.
    * Enforce reverse-DNS IDs, SemVer versioning, API ranges, and valid PluginTypes.
    * Safely inspect ZIP package archives: reject path traversal (zip slip),
      absolute paths, drive letters, symlinks, duplicate entries, case-fold
      collisions, and decompression bombs.
    * Compute canonical SHA-256 package hashes over manifest and payload files.

Python API usage:
    service = DeclareManifestsService()
    manifest = service.parse_manifest(raw_manifest_dict)
    validation = service.validate_package(Path("my_plugin.zip"))

CLI usage:
    uv run python -m app.services.plugins.manifests.plugin_manifests
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from app.contracts.plugins.errors import (
    PluginManifestError,
    PluginPackageValidationError,
)
from app.contracts.plugins.models import (
    PluginFileEntry,
    PluginManifest,
    PluginPackageValidation,
    PluginPermission,
    PluginResourceLimits,
    PluginType,
)
from app.services.plugins.manifests.config import PluginManifestsConfig

if TYPE_CHECKING:
    from collections.abc import Iterable

_REVERSE_DNS_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$")
_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-([0-9A-Za-z.-]+))?(\+([0-9A-Za-z.-]+))?$"
)
_SYMLINK_ATTR_MASK = 0o120000


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


def _extract_permissions(raw_perms: object) -> PluginPermission:
    """Extract and validate PluginPermission model.

    Args:
        raw_perms: Dictionary containing permissions definitions.

    Returns:
        PluginPermission instance.

    Raises:
        PluginManifestError: If permissions is not a dictionary.
    """
    if not isinstance(raw_perms, dict):
        msg = "Permissions field must be an object"
        raise PluginManifestError(msg)

    fs_read = _to_str_tuple(
        raw_perms.get("filesystem_read", raw_perms.get("filesystemRead", []))
    )
    fs_write = _to_str_tuple(
        raw_perms.get("filesystem_write", raw_perms.get("filesystemWrite", []))
    )
    net_endpoints = _to_str_tuple(
        raw_perms.get("network_endpoints", raw_perms.get("networkEndpoints", []))
    )
    subproc_allow = bool(
        raw_perms.get("subprocess_allow", raw_perms.get("subprocessAllow", False))
    )
    secrets = _to_str_tuple(raw_perms.get("secrets", []))

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
        PluginManifestError: If resources is not a dictionary.
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

    return PluginResourceLimits(
        cpu_limit_cores=cpu_val,
        memory_limit_mb=mem_val,
        timeout_seconds=timeout_val,
    )


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

        types = _extract_types(data.get("type", data.get("types", [])))
        permissions = _extract_permissions(data.get("permissions", {}))
        resources = _extract_resources(data.get("resources", {}))

        schemas = data.get("schemas", {})
        if not isinstance(schemas, dict):
            msg = "Schemas field must be an object"
            raise PluginManifestError(msg)

        sha_raw = data.get("sha256ByFile", data.get("sha256_by_file", {}))
        sha256_map = dict(sha_raw) if isinstance(sha_raw, dict) else {}

        manifest = PluginManifest(
            id=str(data.get("id", "")).strip(),
            version=str(data.get("version", "")).strip(),
            api_range=str(data.get("apiRange", data.get("api_range", ""))).strip(),
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

    def validate_package(self, package_path: Path) -> PluginPackageValidation:
        """Inspect and validate a plugin ZIP archive and its inner manifest.

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

        file_size = package_path.stat().st_size
        if file_size > self._config.max_package_size_bytes:
            msg = (
                f"Package file size ({file_size} bytes) exceeds maximum limit "
                f"({self._config.max_package_size_bytes} bytes)"
            )
            raise PluginPackageValidationError(msg)

    def _check_zip_limits(self, infolist: list[zipfile.ZipInfo]) -> None:
        """Check total file count and uncompressed size against limits.

        Args:
            infolist: List of ZipInfo entries in the archive.

        Raises:
            PluginPackageValidationError: If file count or size exceeds limits.
        """
        if len(infolist) > self._config.max_file_count:
            msg = (
                f"Package contains {len(infolist)} files, exceeding limit "
                f"of {self._config.max_file_count}"
            )
            raise PluginPackageValidationError(msg)

        total_uncompressed = sum(info.file_size for info in infolist)
        if total_uncompressed > self._config.max_package_size_bytes:
            msg = (
                f"Total uncompressed size ({total_uncompressed} bytes) "
                f"exceeds limit ({self._config.max_package_size_bytes} bytes)"
            )
            raise PluginPackageValidationError(msg)

    def _parse_package_manifest(self, manifest_data: bytes) -> PluginManifest:
        """Parse manifest data inside a package archive.

        Args:
            manifest_data: Raw JSON bytes from plugin.json.

        Returns:
            Validated PluginManifest instance.

        Raises:
            PluginPackageValidationError: If manifest parsing or validation fails.
        """
        try:
            return self.parse_manifest(manifest_data)
        except PluginManifestError as err:
            msg = f"Invalid package manifest: {err}"
            raise PluginPackageValidationError(msg) from err

    def _verify_declared_hashes(
        self, manifest: PluginManifest, file_hashes: dict[str, str]
    ) -> None:
        """Verify that declared sha256 hashes match actual files.

        Args:
            manifest: The plugin manifest.
            file_hashes: Map of file paths to SHA-256 strings.

        Raises:
            PluginPackageValidationError: If a declared file is missing or hash
                comparison fails.
        """
        for declared_path, expected_hash in manifest.sha256_by_file.items():
            norm_decl = Path(declared_path).as_posix()
            actual_hash = file_hashes.get(norm_decl)
            if actual_hash is None:
                msg = (
                    f"Manifest declares hash for '{declared_path}', but "
                    "file is missing from package"
                )
                raise PluginPackageValidationError(msg)
            if actual_hash != expected_hash:
                msg = (
                    f"Hash mismatch for '{declared_path}': "
                    f"expected {expected_hash}, got {actual_hash}"
                )
                raise PluginPackageValidationError(msg)

    def compute_package_hash(
        self,
        manifest: PluginManifest,
        file_hashes: dict[str, str],
    ) -> str:
        """Compute the canonical SHA-256 package hash over manifest and file hashes.

        Args:
            manifest: The plugin manifest.
            file_hashes: Mapping of normalized relative file paths to SHA-256 strings.

        Returns:
            Hexadecimal SHA-256 string representing the canonical package hash.
        """
        manifest_dict = asdict(manifest)
        manifest_dict.pop("signature", None)
        canonical_manifest_str = json.dumps(
            manifest_dict, sort_keys=True, separators=(",", ":")
        )

        hasher = hashlib.sha256()
        hasher.update(canonical_manifest_str.encode())

        for path in sorted(file_hashes):
            hasher.update(f"{path}:{file_hashes[path]}\n".encode())

        return hasher.hexdigest()


def fr_plug_declare_plugin_manifests(
    raw_or_path: str | bytes | dict[str, object] | Path,
    config: PluginManifestsConfig | None = None,
) -> PluginManifest | PluginPackageValidation:
    """Requirement implementation trace for FR-PLUG-DECLARE_PLUGIN_MANIFESTS.

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


def _run_usage_example() -> None:
    """Execute the bounded public usage demonstration and verification harness.

    Raises:
        RuntimeError: If usage verification fails.
    """
    import tempfile

    print("=== Demonstrating FR-PLUG-DECLARE_PLUGIN_MANIFESTS Usage ===")
    service = DeclareManifestsService()

    # 1. Parse and validate valid in-memory manifest
    manifest_dict: dict[str, object] = {
        "id": "com.haruquantai.sample.momentum",
        "version": "1.0.0",
        "apiRange": ">=1.0.0,<2.0.0",
        "type": ["INDICATOR", "FILTER"],
        "entryPoint": "momentum_filter.py",
        "capabilities": ["indicator.momentum", "filter.trend"],
        "permissions": {
            "filesystem_read": ["data/"],
            "network_endpoints": [],
            "subprocess_allow": False,
        },
        "resources": {
            "cpu_limit_cores": 1.5,
            "memory_limit_mb": 256,
            "timeout_seconds": 15.0,
        },
    }

    manifest = service.parse_manifest(manifest_dict)
    types_str = ", ".join(t.value for t in manifest.types)
    print(
        f"1. Successfully parsed manifest: {manifest.id} v{manifest.version} "
        f"([{types_str}])"
    )

    # 2. Package into a zip archive with files and validate package
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "sample_plugin.zip"
        main_content = b"print('Hello from momentum plugin')\n"
        main_hash = hashlib.sha256(main_content).hexdigest()

        # Update manifest with file hash
        manifest_dict["sha256ByFile"] = {"momentum_filter.py": main_hash}
        manifest_json = json.dumps(manifest_dict, indent=2).encode()

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("plugin.json", manifest_json)
            zf.writestr("momentum_filter.py", main_content)

        validation = service.validate_package(zip_path)
        print(f"2. Successfully validated package: {zip_path.name}")
        print(f"   Canonical package hash: {validation.package_hash}")
        print(f"   Verified {len(validation.files)} files.")

        # 3. Demonstrate rejection of path traversal attack
        bad_zip = Path(tmpdir) / "malicious.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("plugin.json", manifest_json)
            zf.writestr("../evil.py", b"evil code")

        try:
            service.validate_package(bad_zip)
            msg = "Expected malicious package to be rejected"
            raise RuntimeError(msg)
        except PluginPackageValidationError as err:
            print(f"3. Successfully caught and rejected malicious zip slip: {err}")

    print("=== Usage demonstration completed successfully ===")


if __name__ == "__main__":
    _run_usage_example()

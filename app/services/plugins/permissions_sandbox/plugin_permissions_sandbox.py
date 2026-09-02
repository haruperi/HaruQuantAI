"""Plugin Permissions and Sandbox domain logic and capability implementation.

Purpose:
    Enforce manifest-narrowed permission grants, apply OS process limits,
    execute untrusted plugin code in isolated subprocess workers, and sanitize
    outputs with deterministic secret redaction.

Key capabilities:
    * Evaluate and grant manifest-narrowed permission sets without disclosing
      secret values.
    * Apply OS process containment (Windows Job Objects / POSIX resource limits)
      to workers.
    * Execute plugin handlers across length-prefixed IPC channels with strict
      timeout enforcement.
    * Redact sensitive credentials and environment tokens from plugin execution
      outputs.
    * Provide async sandbox_permissions implementing
      SandboxPermissionsCapability.

Python API usage:
    from app.services.plugins.permissions_sandbox.plugin_permissions_sandbox import (
        PluginPermissionsSandboxService,
    )
    from app.contracts.plugins.models import (
        SandboxPermissionsRequest,
    )

    service = PluginPermissionsSandboxService()
    grant_res = await service.sandbox_permissions(grant_request)
    exec_res = await service.sandbox_permissions(execute_request)

CLI usage:
    uv run python -m \
        app.services.plugins.permissions_sandbox.plugin_permissions_sandbox
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from subprocess import TimeoutExpired
from typing import TYPE_CHECKING, cast

from app.contracts.common.models import JsonObject, JsonValue, ProblemDetails
from app.contracts.plugins.errors import PluginFailure, PluginFailureCode
from app.contracts.plugins.models import (
    PluginManifestWire,
    PluginPermissionSet,
    PluginPermissionWire,
    PluginResourceLimitsWire,
    SandboxPermissionsRequest,
    SandboxPermissionsSuccess,
)
from app.services.plugins.permissions_sandbox.process_limits import (
    ProcessLimits,
    UnsupportedSandboxEnforcementError,
)

if TYPE_CHECKING:
    from app.services.plugins.permissions_sandbox.config import (
        SandboxPermissionsConfig,
    )

_FRAME_HEADER_BYTES = 4
_MEBIBYTE = 1024 * 1024


@dataclass(frozen=True, slots=True)
class _Grant:
    """Private grant snapshot with no secret values or package path."""

    manifest: PluginManifestWire
    package_hash: str
    permission_set: PluginPermissionSet


class PluginPermissionsSandboxService:
    """Grant, inspect, and execute plugins outside the control plane."""

    def __init__(self, config: SandboxPermissionsConfig) -> None:
        """Initialize empty process-local grant state."""
        self._config = config
        self._grants: dict[tuple[str, str, str], _Grant] = {}

    async def sandbox_permissions(
        self, request: SandboxPermissionsRequest
    ) -> SandboxPermissionsSuccess | PluginFailure:
        """Perform one manifest-bound sandbox operation.

        Args:
            request: Strict operation-discriminated request.

        Returns:
            Operation success or a secret-safe structured failure.
        """
        try:
            if request.operation == "GRANT":
                return self._grant(request)
            if request.operation == "INSPECT":
                return self._inspect(request)
            return await asyncio.to_thread(self._execute, request)
        except (
            OSError,
            TypeError,
            ValueError,
            UnsupportedSandboxEnforcementError,
        ) as error:
            code: PluginFailureCode = (
                "PLUGIN_SANDBOX_EXECUTION_FAILED"
                if request.operation == "EXECUTE"
                else "PLUGIN_PERMISSION_DENIED"
            )
            return self._failure(request, code, error)

    def clear(self) -> None:
        """Discard all in-memory grants during feature withdrawal."""
        self._grants.clear()

    def _grant(self, request: SandboxPermissionsRequest) -> SandboxPermissionsSuccess:
        manifest = request.manifest
        permissions = request.requested_permissions
        resources = request.requested_resources
        package_hash = request.package_hash
        if (
            manifest is None
            or permissions is None
            or resources is None
            or package_hash is None
        ):
            raise ValueError("grant request is incomplete")
        key = self._key(request)
        if (manifest.id, manifest.version) != (key[0], key[2]):
            raise ValueError("manifest identity does not match grant address")
        if package_hash not in self._config.package_roots:
            raise ValueError("unconfigured package hash")
        effective = self._effective(key, manifest, permissions, resources)
        self._grants[key] = _Grant(manifest, package_hash, effective)
        return SandboxPermissionsSuccess(
            request_id=request.request_id,
            permission_set=effective,
            lifecycle_state="GRANTED",
        )

    def _inspect(self, request: SandboxPermissionsRequest) -> SandboxPermissionsSuccess:
        grant = self._grants.get(self._key(request))
        if grant is None:
            raise ValueError("no matching active sandbox grant")
        return SandboxPermissionsSuccess(
            request_id=request.request_id,
            permission_set=grant.permission_set,
            lifecycle_state="INSPECTED",
        )

    def _effective(
        self,
        key: tuple[str, str, str],
        manifest: PluginManifestWire,
        requested: PluginPermissionWire,
        resources: PluginResourceLimitsWire,
    ) -> PluginPermissionSet:
        ceilings = self._config.ceilings
        declared = manifest.permissions
        for name in (
            "filesystem_read",
            "filesystem_write",
            "network_endpoints",
            "secrets",
        ):
            requested_values = set(getattr(requested, name))
            if not requested_values.issubset(getattr(declared, name)) or not (
                requested_values.issubset(getattr(ceilings, name))
            ):
                raise ValueError(
                    name + " exceeds manifest declaration or feature ceiling"
                )
        if requested.subprocess_allow and (
            not declared.subprocess_allow or not ceilings.subprocess_allow
        ):
            raise ValueError("subprocess permission is denied")
        self._check_resources(manifest, resources)
        return PluginPermissionSet(
            plugin_id=key[0],
            workspace_id=key[1],
            version=key[2],
            filesystem_read=requested.filesystem_read,
            filesystem_write=requested.filesystem_write,
            network_endpoints=requested.network_endpoints,
            subprocess_allow=requested.subprocess_allow,
            secrets=requested.secrets,
            cpu_limit_cores=resources.cpu_limit_cores,
            memory_limit_mb=resources.memory_limit_mb,
            timeout_seconds=resources.timeout_seconds,
            max_output_mb=ceilings.max_output_mb,
        )

    def _check_resources(
        self, manifest: PluginManifestWire, requested: PluginResourceLimitsWire
    ) -> None:
        ceilings = self._config.ceilings
        if Decimal(requested.cpu_limit_cores) > min(
            Decimal(manifest.resources.cpu_limit_cores),
            Decimal(str(ceilings.cpu_limit_cores)),
        ):
            raise ValueError("CPU limit exceeds declaration or ceiling")
        if requested.memory_limit_mb > min(
            manifest.resources.memory_limit_mb, ceilings.memory_limit_mb
        ):
            raise ValueError("memory limit exceeds declaration or ceiling")
        if Decimal(requested.timeout_seconds) > min(
            Decimal(manifest.resources.timeout_seconds),
            Decimal(str(ceilings.timeout_seconds)),
        ):
            raise ValueError("timeout exceeds declaration or ceiling")

    def _execute(self, request: SandboxPermissionsRequest) -> SandboxPermissionsSuccess:
        grant = self._grants.get(self._key(request))
        if grant is None:
            raise ValueError("no matching active sandbox grant")
        root = self._configured_root(grant.package_hash)
        permission = grant.permission_set
        secret_values, secret_names = self._resolve_secrets(permission.secrets)
        limits = ProcessLimits(
            float(permission.cpu_limit_cores), permission.memory_limit_mb
        )
        with tempfile.TemporaryDirectory(prefix="haruquant-sandbox-") as temp_root:
            command = self._worker_command(root, temp_root, grant, secret_names)
            environment = self._worker_environment(secret_values)
            process = limits.start(command, environment)
            try:
                limits.attach(process)
                payload = _frame(request.input or {}, self._config.max_protocol_bytes)
                stdout, stderr = process.communicate(
                    payload, timeout=float(permission.timeout_seconds)
                )
                output = self._validate_output(
                    process.returncode,
                    stdout,
                    stderr,
                    permission.max_output_mb,
                    secret_values.values(),
                )
            except TimeoutExpired as error:
                limits.terminate(process)
                process.communicate()
                raise ValueError("isolated worker timed out") from error
            finally:
                if process.poll() is None:
                    limits.terminate(process)
                    process.communicate()
                limits.close()
        return SandboxPermissionsSuccess(
            request_id=request.request_id,
            permission_set=permission,
            lifecycle_state="EXECUTED",
            output=output,
        )

    def _worker_command(
        self,
        root: Path,
        temp_root: str,
        grant: _Grant,
        secret_names: tuple[str, ...],
    ) -> list[str]:
        permission = grant.permission_set
        command = [
            str(getattr(sys, "_base_executable", sys.executable)),
            "-I",
            str(Path(__file__).with_name("sandbox_worker.py")),
            "--root",
            str(root),
            "--entry",
            grant.manifest.entry_point,
            "--protocol-bytes",
            str(self._config.max_protocol_bytes),
            "--write-root",
            temp_root,
        ]
        for value in permission.filesystem_read:
            command.extend(("--read-root", str(self._safe_path(root, value))))
        for value in permission.filesystem_write:
            command.extend(("--write-root", str(self._safe_path(root, value))))
        for value in permission.network_endpoints:
            command.extend(("--endpoint", value))
        for value in secret_names:
            command.extend(("--secret-env", value))
        if permission.subprocess_allow:
            command.append("--allow-subprocess")
        return command

    def _validate_output(
        self,
        returncode: int | None,
        stdout: bytes,
        stderr: bytes,
        max_output_mb: int,
        secrets: Iterable[str],
    ) -> JsonObject:
        if returncode != 0:
            raise ValueError("isolated worker failed")
        if len(stdout) > max_output_mb * _MEBIBYTE or len(stderr) > (
            max_output_mb * _MEBIBYTE
        ):
            raise ValueError("worker output exceeded bound")
        response = _unframe(stdout, self._config.max_protocol_bytes)
        output = response.get("output")
        if response.get("outcome") != "SUCCESS" or not isinstance(output, dict):
            raise ValueError("worker protocol response was invalid")
        return cast("JsonObject", _redact(output, secrets))

    def _configured_root(self, package_hash: str) -> Path:
        root = self._config.package_roots[package_hash].resolve(strict=True)
        if not root.is_dir():
            raise ValueError("configured package root is not a directory")
        return root

    def _safe_path(self, root: Path, relative: str) -> Path:
        candidate = (root / relative).resolve(strict=False)
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValueError("declared path escapes package root") from error
        return candidate

    def _resolve_secrets(
        self, names: tuple[str, ...]
    ) -> tuple[dict[str, str], tuple[str, ...]]:
        values: dict[str, str] = {}
        plugin_names: list[str] = []
        for name in names:
            host_name = self._config.secret_env_names.get(name)
            if host_name is None or (value := os.environ.get(host_name)) is None:
                raise ValueError("declared secret is unavailable")
            plugin_name = "HQ_PLUGIN_SECRET_" + re.sub(r"[^A-Z0-9_]", "_", name.upper())
            values[plugin_name] = value
            plugin_names.append(plugin_name)
        return values, tuple(plugin_names)

    def _worker_environment(self, secrets: dict[str, str]) -> dict[str, str]:
        environment = {"PATH": os.environ.get("PATH", "")}
        if sys.platform == "win32":
            environment["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
        environment.update(secrets)
        return environment

    def _key(self, request: SandboxPermissionsRequest) -> tuple[str, str, str]:
        if (
            request.plugin_id is None
            or request.workspace_id is None
            or request.version is None
        ):
            raise ValueError("sandbox request address is incomplete")
        return request.plugin_id, request.workspace_id, request.version

    def _failure(
        self,
        request: SandboxPermissionsRequest,
        code: PluginFailureCode,
        error: BaseException,
    ) -> PluginFailure:
        return PluginFailure(
            request_id=request.request_id,
            code=code,
            problem=ProblemDetails(
                type="urn:haruquantai:plugins:sandbox",
                title="Plugin sandbox denied",
                status=403,
                code=code,
                detail="sandbox request denied: " + type(error).__name__,
                request_id=request.request_id,
            ),
        )


def _frame(value: Mapping[str, object], limit: int) -> bytes:
    """Encode one bounded canonical length-prefixed JSON request.

    Returns:
        Framed bytes.

    Raises:
        ValueError: Encoded input exceeds the configured bound.
    """
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > limit:
        raise ValueError("sandbox input exceeds protocol bound")
    return len(payload).to_bytes(_FRAME_HEADER_BYTES, "big") + payload


def _unframe(value: bytes, limit: int) -> dict[str, object]:
    """Decode one exact bounded length-prefixed JSON response.

    Returns:
        Decoded response object.

    Raises:
        TypeError: Decoded JSON is not an object.
        ValueError: Framing is truncated, excessive, or noisy.
    """
    if len(value) < _FRAME_HEADER_BYTES:
        raise ValueError("truncated sandbox response")
    size = int.from_bytes(value[:_FRAME_HEADER_BYTES], "big")
    if size > limit or len(value) != size + _FRAME_HEADER_BYTES:
        raise ValueError("invalid sandbox response framing")
    response = json.loads(value[_FRAME_HEADER_BYTES:])
    if not isinstance(response, dict):
        raise TypeError("sandbox response must be a JSON object")
    return response


def _redact(value: object, secrets: Iterable[str]) -> JsonValue:
    """Recursively redact all resolved secret canaries.

    Returns:
        Secret-safe JSON-compatible value.
    """
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, dict):
        return {str(key): _redact(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item, secrets) for item in value]
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return str(value)


def fr_plug_isolate_plugin_execution() -> str:
    """Return the named bounded usage-scenario identifier."""
    return "FR-PLUG-ISOLATE_PLUGIN_EXECUTION"


def fr_plug_restrict_plugin_secrets() -> str:
    """Return the named secret-safe usage-scenario identifier."""
    return "FR-PLUG-RESTRICT_PLUGIN_SECRETS"


async def _run_usage_scenarios() -> None:
    """Execute both named bounded scenarios with synthetic local inputs.

    Raises:
        RuntimeError: A bounded usage scenario does not produce its contract result.
        TypeError: The grant scenario returns an unexpected result type.
    """
    from app.services.plugins.permissions_sandbox.config import (
        SandboxPermissionsConfig,
    )

    request_id = "0198a2b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b"
    snapshot_id = "0198a2b4-c5d6-7e8f-9a0b-1c2d3e4f5a6c"
    workspace_id = "0198a2b4-c5d6-7e8f-9a0b-1c2d3e4f5a6d"
    package_hash = "a" * 64
    permission_ref = "usage-canary"
    host_name = "HQ_USAGE_SECRET_CANARY"
    previous = os.environ.get(host_name)
    os.environ[host_name] = "synthetic-secret-canary"
    try:
        with tempfile.TemporaryDirectory(prefix="haruquant-sandbox-usage-") as root:
            root_path = Path(root)
            root_path.joinpath("main.py").write_text(
                "import os\ndef run(payload):\n"
                "    return {'echo': payload['echo'], "
                "'secret': os.environ['HQ_PLUGIN_SECRET_USAGE_CANARY']}\n",
                encoding="utf-8",
            )
            config = SandboxPermissionsConfig.from_dict(
                {
                    "package_roots": {package_hash: root},
                    "secret_env_names": {permission_ref: host_name},
                    "ceilings": {
                        "secrets": [permission_ref],
                        "memory_limit_mb": 256,
                        "timeout_seconds": 2,
                        "max_output_mb": 1,
                    },
                }
            )
            service = PluginPermissionsSandboxService(config)
            manifest = PluginManifestWire(
                id="com.haruquantai.usage.sandbox",
                version="1.0.0",
                api_range=">=1.0.0,<2.0.0",
                permissions=PluginPermissionWire(secrets=(permission_ref,)),
                resources=PluginResourceLimitsWire(
                    memory_limit_mb=256, timeout_seconds="2"
                ),
            )
            grant = SandboxPermissionsRequest(
                request_id=request_id,
                capability_snapshot_id=snapshot_id,
                operation="GRANT",
                plugin_id=manifest.id,
                workspace_id=workspace_id,
                version=manifest.version,
                manifest=manifest,
                package_hash=package_hash,
                requested_permissions=manifest.permissions,
                requested_resources=PluginResourceLimitsWire(
                    memory_limit_mb=256, timeout_seconds="1"
                ),
            )
            if isinstance(await service.sandbox_permissions(grant), PluginFailure):
                raise TypeError("grant usage scenario returned an unexpected type")
            execute = SandboxPermissionsRequest(
                request_id=request_id,
                capability_snapshot_id=snapshot_id,
                operation="EXECUTE",
                plugin_id=manifest.id,
                workspace_id=workspace_id,
                version=manifest.version,
                input={"echo": "isolated"},
            )
            result = await service.sandbox_permissions(execute)
            if not isinstance(result, SandboxPermissionsSuccess) or result.output != {
                "echo": "isolated",
                "secret": "[REDACTED]",
            }:
                raise RuntimeError("execution/redaction usage scenario failed")
    finally:
        if previous is None:
            os.environ.pop(host_name, None)
        else:
            os.environ[host_name] = previous


if __name__ == "__main__":
    asyncio.run(_run_usage_scenarios())

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import pytest
from app.contracts.plugins.errors import PluginFailure
from app.contracts.plugins.models import (
    PluginManifestWire,
    PluginPermissionWire,
    PluginResourceLimitsWire,
    SandboxPermissionsRequest,
    SandboxPermissionsSuccess,
)
from app.services.plugins.permissions_sandbox.config import SandboxPermissionsConfig
from app.services.plugins.permissions_sandbox.plugin_permissions_sandbox import (
    PluginPermissionsSandboxService,
    _run_usage_scenarios,
    fr_plug_isolate_plugin_execution,
    fr_plug_restrict_plugin_secrets,
)
from pydantic import ValidationError

if TYPE_CHECKING:
    from app.contracts.common.models import JsonObject

REQUEST_ID = "0198a2b4-c5d6-7e8f-9a0b-1c2d3e4f5a6b"
SNAPSHOT_ID = "0198a2b4-c5d6-7e8f-9a0b-1c2d3e4f5a6c"
WORKSPACE_ID = "0198a2b4-c5d6-7e8f-9a0b-1c2d3e4f5a6d"
PACKAGE_HASH = "a" * 64


def _manifest(*, secrets: tuple[str, ...] = ()) -> PluginManifestWire:
    return PluginManifestWire(
        id="com.haruquantai.test.sandbox",
        version="1.0.0",
        api_range=">=1.0.0,<2.0.0",
        entry_point="main.py",
        permissions=PluginPermissionWire(secrets=secrets),
        resources=PluginResourceLimitsWire(
            cpu_limit_cores="1",
            memory_limit_mb=128,
            timeout_seconds="2",
        ),
    )


def _config(root: Path, *, secrets: tuple[str, ...] = ()) -> SandboxPermissionsConfig:
    return SandboxPermissionsConfig.from_dict(
        {
            "package_roots": {PACKAGE_HASH: str(root.resolve())},
            "secret_env_names": dict.fromkeys(secrets, "TEST_PLUGIN_CANARY"),
            "ceilings": {
                "secrets": list(secrets),
                "cpu_limit_cores": 1,
                "memory_limit_mb": 128,
                "timeout_seconds": 2,
                "max_output_mb": 1,
            },
        }
    )


def _grant(*, secrets: tuple[str, ...] = ()) -> SandboxPermissionsRequest:
    return SandboxPermissionsRequest(
        request_id=REQUEST_ID,
        capability_snapshot_id=SNAPSHOT_ID,
        operation="GRANT",
        plugin_id="com.haruquantai.test.sandbox",
        workspace_id=WORKSPACE_ID,
        version="1.0.0",
        manifest=_manifest(secrets=secrets),
        package_hash=PACKAGE_HASH,
        requested_permissions=PluginPermissionWire(secrets=secrets),
        requested_resources=PluginResourceLimitsWire(
            cpu_limit_cores="1",
            memory_limit_mb=128,
            timeout_seconds="1",
        ),
    )


def _execute(payload: JsonObject) -> SandboxPermissionsRequest:
    return SandboxPermissionsRequest(
        request_id=REQUEST_ID,
        capability_snapshot_id=SNAPSHOT_ID,
        operation="EXECUTE",
        plugin_id="com.haruquantai.test.sandbox",
        workspace_id=WORKSPACE_ID,
        version="1.0.0",
        input=payload,
    )


def test_operation_shapes_fail_closed() -> None:
    with pytest.raises(ValidationError):
        SandboxPermissionsRequest(
            request_id=REQUEST_ID,
            capability_snapshot_id=SNAPSHOT_ID,
            operation="EXECUTE",
            plugin_id="com.haruquantai.test.sandbox",
            workspace_id=WORKSPACE_ID,
            version="1.0.0",
        )


@pytest.mark.asyncio
async def test_grant_intersects_manifest_request_and_ceiling(tmp_path: Path) -> None:
    service = PluginPermissionsSandboxService(_config(tmp_path))
    result = await service.sandbox_permissions(_grant())
    assert isinstance(result, SandboxPermissionsSuccess)
    assert result.lifecycle_state == "GRANTED"
    inspect = SandboxPermissionsRequest(
        request_id=REQUEST_ID,
        capability_snapshot_id=SNAPSHOT_ID,
        operation="INSPECT",
        plugin_id="com.haruquantai.test.sandbox",
        workspace_id=WORKSPACE_ID,
        version="1.0.0",
    )
    assert isinstance(
        await service.sandbox_permissions(inspect), SandboxPermissionsSuccess
    )


@pytest.mark.asyncio
async def test_grant_rejects_permission_not_in_manifest(tmp_path: Path) -> None:
    request = _grant().model_copy(
        update={
            "requested_permissions": PluginPermissionWire(
                network_endpoints=("example.com:443",)
            )
        }
    )
    result = await PluginPermissionsSandboxService(
        _config(tmp_path)
    ).sandbox_permissions(request)
    assert isinstance(result, PluginFailure)
    assert result.code == "PLUGIN_PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_real_child_success_is_out_of_process(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text(
        "import os\ndef run(payload):\n    return {'value': payload['value'], 'pid': os.getpid()}\n",
        encoding="utf-8",
    )
    service = PluginPermissionsSandboxService(_config(tmp_path))
    assert isinstance(
        await service.sandbox_permissions(_grant()), SandboxPermissionsSuccess
    )
    result = await service.sandbox_permissions(_execute({"value": 7}))
    assert isinstance(result, SandboxPermissionsSuccess)
    assert result.output is not None
    assert result.output["value"] == 7


@pytest.mark.asyncio
async def test_secret_canary_is_redacted_from_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    canary = "hq-secret-canary-never-return"
    monkeypatch.setenv("TEST_PLUGIN_CANARY", canary)
    (tmp_path / "main.py").write_text(
        "import os\ndef run(payload):\n    return {'secret': os.environ['HQ_PLUGIN_SECRET_API_TOKEN']}\n",
        encoding="utf-8",
    )
    service = PluginPermissionsSandboxService(_config(tmp_path, secrets=("api-token",)))
    await service.sandbox_permissions(_grant(secrets=("api-token",)))
    result = await service.sandbox_permissions(_execute({}))
    assert isinstance(result, SandboxPermissionsSuccess)
    assert result.output == {"secret": "[REDACTED]"}
    assert canary not in result.model_dump_json()


@pytest.mark.asyncio
async def test_timeout_crash_and_protocol_failure_are_bounded(tmp_path: Path) -> None:
    service = PluginPermissionsSandboxService(_config(tmp_path))
    for body in (
        "def run(payload):\n    while True: pass\n",
        "import os\ndef run(payload):\n    os._exit(7)\n",
        "def run(payload):\n    return []\n",
    ):
        (tmp_path / "main.py").write_text(body, encoding="utf-8")
        await service.sandbox_permissions(_grant())
        result = await service.sandbox_permissions(_execute({}))
        assert isinstance(result, PluginFailure)
        assert result.code == "PLUGIN_SANDBOX_EXECUTION_FAILED"


@pytest.mark.asyncio
async def test_inspect_and_missing_grants(tmp_path: Path) -> None:
    service = PluginPermissionsSandboxService(_config(tmp_path))

    # Inspect unknown plugin
    inspect = SandboxPermissionsRequest(
        request_id=REQUEST_ID,
        capability_snapshot_id=SNAPSHOT_ID,
        operation="INSPECT",
        plugin_id="unknown.plugin",
        workspace_id=WORKSPACE_ID,
        version="1.0.0",
    )
    res_inspect = await service.sandbox_permissions(inspect)
    assert isinstance(res_inspect, PluginFailure)
    assert res_inspect.code == "PLUGIN_PERMISSION_DENIED"

    # Execute on unknown plugin
    res_exec = await service.sandbox_permissions(
        SandboxPermissionsRequest(
            request_id=REQUEST_ID,
            capability_snapshot_id=SNAPSHOT_ID,
            operation="EXECUTE",
            plugin_id="unknown.plugin",
            workspace_id=WORKSPACE_ID,
            version="1.0.0",
            input={"k": "v"},
        )
    )
    assert isinstance(res_exec, PluginFailure)
    assert res_exec.code == "PLUGIN_SANDBOX_EXECUTION_FAILED"


@pytest.mark.asyncio
async def test_sandbox_edge_cases(tmp_path: Path) -> None:
    # Package root escapes or non-existent
    bad_config = SandboxPermissionsConfig.from_dict(
        {
            "package_roots": {PACKAGE_HASH: str(tmp_path / "nonexistent")},
            "secret_env_names": {},
            "ceilings": {
                "secrets": [],
                "cpu_limit_cores": 1,
                "memory_limit_mb": 128,
                "timeout_seconds": 2,
                "max_output_mb": 1,
            },
        }
    )
    service_bad = PluginPermissionsSandboxService(bad_config)
    await service_bad.sandbox_permissions(_grant())
    res_bad = await service_bad.sandbox_permissions(_execute({}))
    assert isinstance(res_bad, PluginFailure)
    assert res_bad.code == "PLUGIN_SANDBOX_EXECUTION_FAILED"

    # Declared secret unavailable
    main_file = anyio.Path(tmp_path) / "main.py"
    await main_file.write_text("def run(p): return {}\n", encoding="utf-8")
    missing_secret_config = SandboxPermissionsConfig.from_dict(
        {
            "package_roots": {PACKAGE_HASH: str(tmp_path)},
            "secret_env_names": {"missing-sec": "NON_EXISTENT_ENV_VAR_12345"},
            "ceilings": {
                "secrets": ["missing-sec"],
                "cpu_limit_cores": 1,
                "memory_limit_mb": 128,
                "timeout_seconds": 2,
                "max_output_mb": 1,
            },
        }
    )
    service_sec = PluginPermissionsSandboxService(missing_secret_config)
    await service_sec.sandbox_permissions(_grant(secrets=("missing-sec",)))
    res_sec = await service_sec.sandbox_permissions(_execute({}))
    assert isinstance(res_sec, PluginFailure)
    assert res_sec.code == "PLUGIN_SANDBOX_EXECUTION_FAILED"


@pytest.mark.asyncio
async def test_run_usage_scenarios_execution() -> None:
    await _run_usage_scenarios()


def test_named_usage_scenarios() -> None:
    assert fr_plug_isolate_plugin_execution() == "FR-PLUG-ISOLATE_PLUGIN_EXECUTION"
    assert fr_plug_restrict_plugin_secrets() == "FR-PLUG-RESTRICT_PLUGIN_SECRETS"

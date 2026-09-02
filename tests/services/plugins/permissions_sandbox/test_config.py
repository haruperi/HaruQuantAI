from pathlib import Path

import pytest
from app.services.plugins.permissions_sandbox.config import SandboxPermissionsConfig


def test_config_is_strict_and_has_deny_by_default_ceilings(tmp_path: Path) -> None:
    package_hash = "a" * 64
    config = SandboxPermissionsConfig.from_dict(
        {"package_roots": {package_hash: str(tmp_path.resolve())}}
    )
    assert config.package_roots == {package_hash: tmp_path.resolve()}
    assert config.ceilings.network_endpoints == ()
    assert not config.ceilings.subprocess_allow


@pytest.mark.parametrize(
    "value",
    [
        None,
        {"unknown": True},
        {"package_roots": {"bad": "C:/tmp"}},
        {"secret_env_names": {"api": "not-safe"}},
        {"max_protocol_bytes": 1},
        {"enforcement_mode": "BEST_EFFORT"},
    ],
)
def test_config_rejects_missing_unknown_and_unsafe_values(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        SandboxPermissionsConfig.from_dict(value)  # type: ignore[arg-type]

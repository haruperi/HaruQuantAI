"""Configuration and explicit assembly acceptance for the rebuilt host."""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest
from app.host.bootstrap import BootstrapCoordinator
from app.host.config import HostSettings, load_settings
from app.persistence.host import (
    HostSettingRecord,
    HostStore,
    prepare_boot_database,
    utc_now_iso,
)
from pydantic import ValidationError


def test_configuration_precedence_and_readonly(tmp_path):
    path = tmp_path / "database" / "haruquantai.db"
    prepare_boot_database(path)
    HostStore(path).upsert_setting(
        HostSettingRecord(
            "host", "runtime", json.dumps({"port": 9000}), 1, utc_now_iso()
        )
    )
    before = path.read_bytes()
    assert load_settings({"data_dir": tmp_path}, environment={}).port == 9000
    assert (
        load_settings({"data_dir": tmp_path}, environment={"HARU_PORT": "9001"}).port
        == 9001
    )
    assert (
        load_settings(
            {"data_dir": tmp_path, "port": 9002}, environment={"HARU_PORT": "9001"}
        ).port
        == 9002
    )
    assert path.read_bytes() == before


def test_fresh_config_does_not_create_database(tmp_path):
    result = load_settings(environment={"HARU_DATA_DIR": str(tmp_path)})
    assert not result.database_path.exists()
    assert result.port == 8000


@pytest.mark.parametrize(
    "values",
    [
        {"port": 0},
        {"host": "0.0.0.0"},
        {"host": "example.com"},
        {"workers": -1},
        {"password": ""},
        {"certificate": Path("cert")},
    ],
)
def test_invalid_configuration_fails_closed(values):
    with pytest.raises(ValidationError):
        HostSettings(**values)


def test_boot_stages_and_logging_are_real(host_config):
    host = BootstrapCoordinator(host_config)

    async def run() -> None:
        await host.initialize()
        await host.initialize()
        stages = host.startup.results
        assert stages["I01"].outcome == "succeeded"
        assert stages["I08"].outcome == "unavailable"
        pool = host.pool
        assert pool is not None
        assert len(stages) == 37
        await host.close()
        assert host.pool is None

    asyncio.run(run())
    events = [
        json.loads(line)
        for line in (host_config.log_dir / "haruquantai.log").read_text().splitlines()
    ]
    assert any(
        e.get("fields", {}).get("stage") == "I08"
        and e["fields"]["outcome"] == "unavailable"
        for e in events
    )
    assert not any(
        getattr(handler, "_host_telemetry_owned", False)
        for handler in logging.getLogger("app").handlers
    )


def test_imports_do_not_configure_handlers_or_touch_disk(tmp_path):
    root = str(Path(__file__).resolve().parents[2])
    code = f"import sys; sys.path.insert(0, {root!r}); import app.main, app.cli, app.host.bootstrap; import logging; assert not logging.getLogger('app').handlers"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


def test_existing_database_requires_explicit_migration(host_config):
    from app.persistence.host import HostPersistenceSchemaError, ensure_schema

    ensure_schema(host_config.database_path)
    before = host_config.database_path.read_bytes()
    host = BootstrapCoordinator(host_config)
    with pytest.raises(HostPersistenceSchemaError, match="Migration required"):
        asyncio.run(host.initialize())
    assert host.startup.state == "FAILED"
    assert host_config.database_path.read_bytes() == before


def test_missing_auth_schema_has_actionable_diagnostic(tmp_path, caplog):
    from app.persistence.host import HostPersistenceSchemaError, ensure_schema

    settings = HostSettings(data_dir=tmp_path)
    ensure_schema(settings.database_path)
    host = BootstrapCoordinator(settings)
    with caplog.at_level(logging.ERROR), pytest.raises(HostPersistenceSchemaError):
        asyncio.run(host.initialize())
    assert "--migrate-auth-schema" in caplog.text
    assert host.startup.state == "FAILED"

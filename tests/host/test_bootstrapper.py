"""Tests for host configuration resolution and telemetry setup."""

import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.host.bootstrapper import (
    DEFAULT_ADDRESS,
    DEFAULT_EXCHANGE_ROOT,
    DEFAULT_LOG_DIR,
    DEFAULT_PORT,
    DEFAULT_UI_DIST,
    ENV_ADDRESS,
    ENV_DATABASE_PATH,
    ENV_DOMAIN_ROOTS,
    ENV_EXCHANGE_ROOT,
    ENV_LOG_DIR,
    ENV_PASSWORD,
    ENV_PORT,
    ENV_UI_DIST,
    HostConfig,
    config_from_env,
)
from app.host.logging import LOGGER_NAME, configure_host_logging, host_log_path
from app.host.settings import DEFAULT_DATABASE_PATH


def test_defaults_match_owner_decisions() -> None:
    config = config_from_env(env={})

    assert config == HostConfig(
        address=DEFAULT_ADDRESS,
        port=DEFAULT_PORT,
        log_dir=DEFAULT_LOG_DIR,
        password=None,
        database_path=DEFAULT_DATABASE_PATH,
        exchange_root=DEFAULT_EXCHANGE_ROOT,
        domain_roots=(Path("app") / "workspace", Path("app") / "plugins"),
        ui_dist=DEFAULT_UI_DIST,
    )
    assert (DEFAULT_ADDRESS, DEFAULT_PORT) == ("127.0.0.1", 8000)
    assert DEFAULT_LOG_DIR == Path("data") / "logs"
    assert DEFAULT_DATABASE_PATH == Path("data") / "database" / "haruquantai.db"
    assert DEFAULT_EXCHANGE_ROOT == Path("data") / "exchange"


def test_environment_overrides_are_respected(tmp_path: Path) -> None:
    config = config_from_env(
        env={
            ENV_ADDRESS: "0.0.0.0",
            ENV_PORT: "9001",
            ENV_LOG_DIR: str(tmp_path / "logs"),
            ENV_PASSWORD: "s3cret",  # pragma: allowlist secret
            ENV_DATABASE_PATH: str(tmp_path / "database" / "haruquantai.db"),
            ENV_EXCHANGE_ROOT: str(tmp_path / "exchange"),
            ENV_DOMAIN_ROOTS: "custom/domains, other/domains",
            ENV_UI_DIST: "",
        }
    )

    assert config.address == "0.0.0.0"
    assert config.port == 9001
    assert config.log_dir == tmp_path / "logs"
    assert config.password == "s3cret"  # pragma: allowlist secret
    assert config.database_path == tmp_path / "database" / "haruquantai.db"
    assert config.exchange_root == tmp_path / "exchange"
    assert config.domain_roots == (Path("custom/domains"), Path("other/domains"))
    assert config.ui_dist is None


def test_empty_domain_roots_fail_closed() -> None:
    with pytest.raises(ValueError, match=ENV_DOMAIN_ROOTS):
        config_from_env(env={ENV_DOMAIN_ROOTS: " , , "})


@pytest.mark.parametrize("bad_port", ["not-a-number", "0", "70000", "-1"])
def test_invalid_port_fails_closed(bad_port: str) -> None:
    with pytest.raises(ValueError, match=ENV_PORT):
        config_from_env(env={ENV_PORT: bad_port})


def test_empty_address_fails_closed() -> None:
    with pytest.raises(ValueError, match=ENV_ADDRESS):
        config_from_env(env={ENV_ADDRESS: "   "})


def test_configure_host_logging_writes_dated_file(tmp_path: Path) -> None:
    logger = configure_host_logging(tmp_path, also_stderr=False)

    logger.info("hello host")

    expected = host_log_path(tmp_path, datetime.now(tz=UTC))
    assert expected.exists()
    assert "hello host" in expected.read_text(encoding="utf-8")
    assert logger.name == LOGGER_NAME


def test_configure_host_logging_is_idempotent(tmp_path: Path) -> None:
    first = configure_host_logging(tmp_path, also_stderr=False)
    second = configure_host_logging(tmp_path, also_stderr=False)

    assert first is second
    file_handlers = [
        handler
        for handler in first.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    assert len(file_handlers) == 1

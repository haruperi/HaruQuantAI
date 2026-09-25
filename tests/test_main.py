"""Isolated B01/B02 tests for the staged host process entrypoint."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from app.main import (
    HostConfigurationError,
    LaunchOptions,
    effective_settings,
    main,
    parse_launch_args,
)

REPO = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPO / "app" / "main.py"


def write_settings_rows(
    data_dir: Path,
    rows: list[tuple[str, str, object, int]],
) -> Path:
    """Create only an isolated test host_settings table with the given rows.

    A row value is a raw JSON string or any JSON-serializable object.
    """
    path = data_dir / "database" / "haruquantai.db"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.execute(
                "CREATE TABLE host_settings ("
                "scope TEXT NOT NULL, key TEXT NOT NULL, value_json TEXT NOT NULL, "
                "schema_version INTEGER NOT NULL, updated_at_utc TEXT NOT NULL, "
                "PRIMARY KEY (scope, key))"
            )
            for scope, key, value, version in rows:
                raw = value if isinstance(value, str) else json.dumps(value)
                connection.execute(
                    "INSERT INTO host_settings VALUES (?, ?, ?, ?, ?)",
                    (scope, key, raw, version, "2026-01-01T00:00:00+00:00"),
                )
    return path


def test_launch_defaults_are_typed_and_do_not_create_data(tmp_path: Path) -> None:
    options = parse_launch_args([])
    assert options == LaunchOptions("127.0.0.1", 8000, Path("data"))
    assert options.explicit_fields == frozenset()
    assert not (tmp_path / "data").exists()


def test_launch_overrides_and_immutable_options() -> None:
    options = parse_launch_args(
        ["--host", "example.local", "--port", "9001", "--data-dir", "custom-data"]
    )
    assert options == LaunchOptions("example.local", 9001, Path("custom-data"))
    assert options.explicit_fields == frozenset({"host", "port", "data_dir"})
    with pytest.raises(FrozenInstanceError):
        options.port = 9002  # type: ignore[misc]


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["--host", " "], "host must not be empty"),
        (["--port", "abc"], "port must be an integer"),
        (["--port", "0"], "port must be between 1 and 65535"),
        (["--port", "65536"], "port must be between 1 and 65535"),
        (["--data-dir", " "], "data directory must not be empty"),
        (["--unknown"], "unrecognized arguments"),
    ],
)
def test_invalid_args_exit_two(
    argv: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        parse_launch_args(argv)
    assert error.value.code == 2
    assert message in capsys.readouterr().err


def test_help_exits_zero_and_lists_launch_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        parse_launch_args(["--help"])
    assert error.value.code == 0
    output = capsys.readouterr().out
    for flag in ("--host", "--port", "--data-dir"):
        assert flag in output


def test_main_fails_honestly_after_valid_b01_args(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as error:
        main(["--port", "8000"])
    assert "B03-B05" in str(error.value)


# -- B02 effective settings resolution ----------------------------------------


def test_effective_settings_defaults_without_a_database(tmp_path: Path) -> None:
    resolved = effective_settings(parse_launch_args(["--data-dir", str(tmp_path)]))
    assert resolved == resolved.model_copy(update={"data_dir": tmp_path})
    assert resolved.port == 8000
    assert resolved.gpu_accelerated is True
    assert resolved.records == {}


def test_effective_settings_applies_stored_then_cli(tmp_path: Path) -> None:
    write_settings_rows(
        tmp_path,
        [("application", "app.general", {"web_server_port": 8101}, 1)],
    )
    stored = effective_settings(parse_launch_args(["--data-dir", str(tmp_path)]))
    assert stored.port == 8101
    cli = effective_settings(
        parse_launch_args(["--data-dir", str(tmp_path), "--port", "9001"])
    )
    assert cli.port == 9001


def test_effective_settings_loads_every_record(tmp_path: Path) -> None:
    write_settings_rows(
        tmp_path,
        [
            ("application", "app.general", {"gpu_accelerated": False}, 1),
            ("application", "config.cpu", {"core_usage": "all"}, 1),
            ("host", "__revision__", "3", 1),
        ],
    )
    resolved = effective_settings(parse_launch_args(["--data-dir", str(tmp_path)]))
    assert resolved.gpu_accelerated is False
    assert resolved.records["application"]["config.cpu"] == {"core_usage": "all"}
    assert resolved.records["host"]["__revision__"] == 3


@pytest.mark.parametrize(
    ("raw", "version"),
    [
        ("{broken", 1),
        ('{"web_server_port":8101,"web_server_port":8102}', 1),
        ('{"web_server_port":NaN}', 1),
        ('{"web_server_port":0}', 1),
        ('{"gpu_accelerated":"maybe"}', 1),
        ('{"web_server_port":8101}', 2),
        ("[1, 2]", 1),
    ],
)
def test_effective_settings_rejects_invalid_stored_records(
    tmp_path: Path, raw: str, version: int
) -> None:
    write_settings_rows(tmp_path, [("application", "app.general", raw, version)])
    with pytest.raises(HostConfigurationError):
        effective_settings(parse_launch_args(["--data-dir", str(tmp_path)]))


def test_effective_settings_rejects_incompatible_schema(tmp_path: Path) -> None:
    path = tmp_path / "database" / "haruquantai.db"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.execute("CREATE TABLE host_settings (key TEXT PRIMARY KEY)")
    with pytest.raises(HostConfigurationError, match="Incompatible"):
        effective_settings(parse_launch_args(["--data-dir", str(tmp_path)]))


def test_effective_settings_rejects_data_dir_file(tmp_path: Path) -> None:
    path = tmp_path / "not-a-directory"
    path.write_text("sample", encoding="utf-8")
    with pytest.raises(HostConfigurationError, match="Data directory"):
        effective_settings(parse_launch_args(["--data-dir", str(path)]))


# -- isolated process behavior ---------------------------------------------------


def test_import_is_inert_in_isolated_process(tmp_path: Path) -> None:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import logging; import app.main; "
                "assert not logging.getLogger('app').handlers; "
                "assert not logging.getLogger('haruquantai').handlers"
            ),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "data").exists()


def test_documented_script_help_and_valid_launch(tmp_path: Path) -> None:
    help_result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert "--data-dir" in help_result.stdout
    launch_result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "--port", "8000"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert launch_result.returncode != 0
    assert "B03-B05" in launch_result.stderr
    lines = launch_result.stderr.splitlines()
    assert "B01 App booting initiated" in lines[0]
    assert (
        'B02 Runtime configuration loaded: host="127.0.0.1" '
        "port=8000 gpu_accelerated=True"
    ) in lines[1]
    assert not (tmp_path / "data" / "database").exists()


def test_boot_failure_is_logged_without_creating_a_data_directory(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "--data-dir", " "],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "B01 App booting initiated" not in result.stderr
    assert not (tmp_path / "data").exists()


def test_runtime_configuration_failure_is_visible_without_file_creation(
    tmp_path: Path,
) -> None:
    write_settings_rows(
        tmp_path / "data",
        [("application", "app.general", '{"web_server_port":NaN}', 1)],
    )
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    lines = result.stderr.splitlines()
    assert "B01 App booting initiated" in lines[0]
    assert "B02 Runtime configuration failed:" in lines[1]
    assert not (tmp_path / "data" / "logs").exists()

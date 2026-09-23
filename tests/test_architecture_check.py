"""Behavioral checks for the restored architecture gate."""

from pathlib import Path

from scripts.architecture_check import check_repository


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_clean_host_passes(tmp_path: Path) -> None:
    _write(tmp_path, "app/__init__.py", '"""Package."""\n')
    _write(tmp_path, "app/host/__init__.py", '"""Host."""\n')
    _write(tmp_path, "app/host/server.py", "import pathlib\n")
    assert check_repository(tmp_path) == []


def test_host_domain_import_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "app/host/server.py", "from app.plugins.foo import impl\n")
    assert "host imports domain" in check_repository(tmp_path)[0]


def test_init_and_kernel_import_violations_are_reported(tmp_path: Path) -> None:
    _write(tmp_path, "app/__init__.py", "VALUE = 1\n")
    _write(tmp_path, "app/kernel/math.py", "import numpy\n")
    issues = check_repository(tmp_path)
    assert any("docstring-only" in issue for issue in issues)
    assert any("non-stdlib" in issue for issue in issues)


def test_plugin_private_sibling_import_is_rejected(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/plugins/indicators/rsi.py",
        "import app.plugins.indicators.macd\n",
    )
    _write(tmp_path, "app/plugins/indicators/macd.py", "VALUE = 1\n")
    assert "plugin imports sibling" in check_repository(tmp_path)[0]


def test_relative_domain_import_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "app/host/server.py", "from ..plugins import sample\n")
    assert "host imports domain" in check_repository(tmp_path)[0]

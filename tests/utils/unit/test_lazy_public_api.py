"""Tests for lazy public API resolution in app.utils."""

import os
import subprocess
import sys
from pathlib import Path

import app.utils
import pytest


def test_utils_all_is_tuple() -> None:
    """Verify app.utils.__all__ is a tuple and matches _EXPORTS keys."""
    assert isinstance(app.utils.__all__, tuple)
    assert sorted(app.utils.__all__) == list(app.utils.__all__)
    assert set(app.utils.__all__) == set(app.utils._EXPORTS.keys())


def test_utils_dir_matches_all() -> None:
    """Verify dir() on app.utils contains all public exports."""
    mod_dir = dir(app.utils)
    for name in app.utils.__all__:
        assert name in mod_dir


def test_resolve_every_public_export() -> None:
    """Verify every declared public export resolves to a callable or type."""
    for name in app.utils.__all__:
        sym = getattr(app.utils, name)
        assert sym is not None
        assert callable(sym) or isinstance(sym, type)


def test_unknown_attribute_raises_exact_attribute_error() -> None:
    """Verify accessing unknown attribute raises exact PEP 562 AttributeError."""
    with pytest.raises(
        AttributeError,
        match=r"module 'app\.utils' has no attribute 'non_existent_symbol'",
    ):
        _ = getattr(app.utils, "non_existent_symbol")  # noqa: B009


def test_lazy_import_in_fresh_process() -> None:
    """Verify importing app.utils does not eagerly import notifications."""
    repo_root = str(Path(__file__).resolve().parents[3])
    env = dict(os.environ)
    env["PYTHONPATH"] = repo_root
    script = (
        "import sys\n"
        "import app.utils\n"
        "loaded = [m for m in sys.modules if m.startswith('app.utils.notifications')]\n"
        "if loaded:\n"
        "    raise SystemExit(f'Eager notifications loaded: {loaded}')\n"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=env,
        check=False,
    )
    assert result.returncode == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"


def test_lazy_import_from_logger_in_fresh_process() -> None:
    """Verify importing get_logger does not eagerly import notifications."""
    repo_root = str(Path(__file__).resolve().parents[3])
    env = dict(os.environ)
    env["PYTHONPATH"] = repo_root
    script = (
        "import sys\n"
        "from app.utils import get_logger\n"
        "loaded = [m for m in sys.modules if m.startswith('app.utils.notifications')]\n"
        "if loaded:\n"
        "    raise SystemExit(f'Eager notifications loaded: {loaded}')\n"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=env,
        check=False,
    )
    assert result.returncode == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

"""NFR-INDI-001/NFR-INDI-003: purity, dependency, and import-safety guards."""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

INDICATORS_ROOT = Path("app/services/indicators").resolve()
DOMAIN_PREFIX = "app.services.indicators"

# The complete approved runtime dependency surface for this pure domain.
ALLOWED_THIRD_PARTY = {"numpy", "pandas"}
ALLOWED_LOCAL_PREFIXES = ("app.utils", "app.services.data.contracts", DOMAIN_PREFIX)

# Modules that would give this domain I/O, persistence, network, subprocess,
# environment, wall-clock, or nondeterminism capability it must never hold.
FORBIDDEN_MODULES = {
    "asyncio",
    "http",
    "httpx",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "random",
    "requests",
    "shutil",
    "socket",
    "sqlite3",
    "subprocess",
    "tempfile",
    "threading",
    "urllib",
}


def _python_files() -> list[Path]:
    """Return every non-cached source file in the Indicators package.

    Returns:
        Sorted list of source file paths.
    """
    return sorted(
        p for p in INDICATORS_ROOT.rglob("*.py") if "__pycache__" not in p.parts
    )


def _imported_roots(path: Path) -> set[str]:
    """Return the top-level module names imported by one source file.

    Walks the whole tree so deferred and ``TYPE_CHECKING`` imports are included:
    a forbidden dependency is forbidden regardless of where it is written.

    Args:
        path: Python source file to parse.

    Returns:
        Set of imported dotted module names.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
    return found


def _is_allowed(module: str) -> bool:
    """Report whether one imported module is inside the approved surface.

    Args:
        module: Dotted module name.

    Returns:
        ``True`` when the module is stdlib, approved third-party, or approved local.
    """
    if module.startswith(ALLOWED_LOCAL_PREFIXES):
        return True
    root = module.split(".", maxsplit=1)[0]
    if root in ALLOWED_THIRD_PARTY:
        return True
    return root in sys.stdlib_module_names


def test_indicators_imports_only_approved_modules() -> None:
    """NFR-INDI-003: no undeclared dependency or forbidden deep import exists."""
    violations: list[str] = []
    for path in _python_files():
        for module in _imported_roots(path):
            if not _is_allowed(module):
                violations.append(f"{path.name}: {module}")
    assert violations == [], f"unapproved imports: {violations}"


def test_indicators_declares_no_forbidden_io_modules() -> None:
    """NFR-INDI-001: the domain holds no I/O, network, or nondeterminism capability."""
    violations: list[str] = []
    for path in _python_files():
        for module in _imported_roots(path):
            if module.split(".", maxsplit=1)[0] in FORBIDDEN_MODULES:
                violations.append(f"{path.name}: {module}")
    assert violations == [], f"forbidden I/O imports: {violations}"


def test_indicators_never_imports_a_peer_service_domain() -> None:
    """NFR-INDI-001: Indicators depends on no domain other than Utils and Data."""
    violations: list[str] = []
    for path in _python_files():
        for module in _imported_roots(path):
            if module.startswith("app.services.") and not module.startswith(
                (DOMAIN_PREFIX, "app.services.data.contracts")
            ):
                violations.append(f"{path.name}: {module}")
    assert violations == [], f"cross-domain imports: {violations}"


def test_registry_does_not_import_feature_implementations() -> None:
    """The immutable registry stores import-path identity, never live imports."""
    registry_path = INDICATORS_ROOT / "core" / "registry.py"
    feature_packages = ("trend", "volatility", "momentum", "volume", "candles")
    imported = _imported_roots(registry_path)
    for module in imported:
        for feature in feature_packages:
            assert not module.startswith(f"{DOMAIN_PREFIX}.{feature}"), (
                f"registry imports feature implementation {module}"
            )


def test_importing_indicators_has_no_persistent_side_effects() -> None:
    """NFR-INDI-001: importing the package writes nothing and starts nothing.

    Runs in a subprocess rather than purging ``sys.modules`` in place. A fresh
    interpreter is both a stronger check (nothing is already imported) and
    safe: rebinding live modules would break class identity for every other
    test sharing this session.
    """
    probe = (
        "import pathlib,sys;"
        "before={p.name for p in pathlib.Path.cwd().iterdir()};"
        "import app.services.indicators as ind;"
        "after={p.name for p in pathlib.Path.cwd().iterdir()};"
        "assert before==after,'import created filesystem entries';"
        "assert len(ind.__all__)==32,'unexpected public surface';"
        "print('OK')"
    )
    completed = subprocess.run(  # noqa: S603 - fixed inline probe, no shell.
        [sys.executable, "-c", probe],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"import probe failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
    assert "OK" in completed.stdout


def test_public_port_exposes_no_callable_stub_for_unsupported_modes() -> None:
    """Excluded capabilities appear only as matrix metadata, never as callables."""
    module = importlib.import_module(DOMAIN_PREFIX)
    unsupported = (
        "incremental",
        "streaming",
        "cache",
        "composition",
        "custom_registration",
        "out_of_core",
        "acceleration",
        "proprietary",
    )
    for name in module.__all__:
        for mode in unsupported:
            assert mode not in name, f"unsupported mode {mode} exposed as {name}"

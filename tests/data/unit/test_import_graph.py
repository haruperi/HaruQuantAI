"""Structural guards for the current focused DATA domain architecture."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

DATA_ROOT = Path("app/services/data").resolve()
DOMAIN_README = DATA_ROOT / "README.md"
DOMAIN_PREFIX = "app.services.data"

FEATURE_DIRECTORIES = frozenset(
    {
        "audit",
        "contracts",
        "data_jobs",
        "economic_calendar",
        "evidence",
        "local_datasets",
        "market_data",
        "persistence",
        "quality",
        "realtime_feeds",
        "research_sources",
        "sources",
        "synthetic_data",
        "tick_derivation",
        "time_sessions",
        "transformation",
    }
)
PERMITTED_ROOT_FILES = frozenset(
    {
        "README.md",
        "__init__.py",
        "_limits.py",
        "_settings.py",
        "operations.py",
        "py.typed",
    }
)
REQUIRED_ROOT_FILES = frozenset(
    {"README.md", "__init__.py", "_limits.py", "_settings.py"}
)
REMOVED_LEGACY_DIRECTORIES = frozenset(
    {
        "adapters",
        "config",
        "gateway",
        "limits",
        "models",
        "retrieval",
        "scheduler",
        "security",
        "storage",
        "time",
        "validation",
    }
)


def _python_files(package: Path) -> list[Path]:
    """Return every non-cached Python source file below a package.

    Args:
        package: Package directory to scan.

    Returns:
        Sorted Python source paths.
    """
    return sorted(
        path for path in package.rglob("*.py") if "__pycache__" not in path.parts
    )


def _domain_imports(path: Path, *, module_level_only: bool) -> set[str]:
    """Return DATA-domain imports used by one Python source file.

    Args:
        path: Python source file to parse.
        module_level_only: Whether to inspect only the module body.

    Returns:
        Imported module paths within the DATA domain.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    nodes = tree.body if module_level_only else ast.walk(tree)
    imports: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(DOMAIN_PREFIX):
                imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(
                alias.name
                for alias in node.names
                if alias.name.startswith(DOMAIN_PREFIX)
            )
    return imports


def _registered_feature_modules() -> set[str]:
    """Return owning modules declared by the canonical Feature Registry.

    Returns:
        Registered feature-module directory names.
    """
    readme = DOMAIN_README.read_text(encoding="utf-8")
    registry_match = re.search(
        r"^### Feature Registry\s*$"
        r"(?P<body>.*?)"
        r"(?=^### |\Z)",
        readme,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert registry_match is not None, "The DATA README has no Feature Registry."
    return {
        match.group("module")
        for match in re.finditer(
            r"^\| (?:Completed|Partial|Pending) \| `FEAT-DATA-\d{2}` .*?"
            r"\| `(?P<module>[a-z_]+)/` \|",
            registry_match.group("body"),
            flags=re.MULTILINE,
        )
    }


def test_registered_feature_directories_match_the_current_package() -> None:
    """Assert the registry and actual focused feature directories agree."""
    actual = {
        path.name
        for path in DATA_ROOT.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    }
    assert actual == FEATURE_DIRECTORIES
    assert _registered_feature_modules() == FEATURE_DIRECTORIES


def test_only_permitted_infrastructure_files_exist_at_package_root() -> None:
    """Assert production behavior is contained by its owning feature folder."""
    actual = {path.name for path in DATA_ROOT.iterdir() if path.is_file()}
    assert REQUIRED_ROOT_FILES <= actual <= PERMITTED_ROOT_FILES


def test_every_feature_has_module_documentation() -> None:
    """Assert each focused feature folder owns one module README."""
    missing = [
        feature
        for feature in sorted(FEATURE_DIRECTORIES)
        if not (DATA_ROOT / feature / "README.md").is_file()
    ]
    assert not missing, f"Focused feature README files are missing: {missing}"


def test_removed_legacy_packages_are_absent_and_unreferenced() -> None:
    """Assert retired parallel implementations cannot re-enter the package."""
    assert not REMOVED_LEGACY_DIRECTORIES & {
        path.name for path in DATA_ROOT.iterdir() if path.is_dir()
    }
    legacy_prefixes = tuple(
        f"{DOMAIN_PREFIX}.{name}" for name in REMOVED_LEGACY_DIRECTORIES
    )
    offenders: dict[str, list[str]] = {}
    for path in _python_files(DATA_ROOT):
        imports = sorted(
            module
            for module in _domain_imports(path, module_level_only=False)
            if any(
                module == prefix or module.startswith(f"{prefix}.")
                for prefix in legacy_prefixes
            )
        )
        if imports:
            offenders[str(path.relative_to(DATA_ROOT))] = imports
    assert not offenders


def test_canonical_contracts_do_not_depend_on_feature_behavior() -> None:
    """Assert canonical shared contracts remain the dependency root."""
    contracts_root = DATA_ROOT / "contracts"
    offenders: dict[str, list[str]] = {}
    for path in _python_files(contracts_root):
        imports = sorted(
            module
            for module in _domain_imports(path, module_level_only=False)
            if not module.startswith(f"{DOMAIN_PREFIX}.contracts")
        )
        if imports:
            offenders[str(path.relative_to(DATA_ROOT))] = imports
    assert not offenders


def test_package_root_has_no_runtime_side_effect_statements() -> None:
    """Assert the public import boundary contains imports and declarations only."""
    root_module = ast.parse(
        (DATA_ROOT / "__init__.py").read_text(encoding="utf-8"),
        filename=str(DATA_ROOT / "__init__.py"),
    )
    permitted = (
        ast.Expr,
        ast.Import,
        ast.ImportFrom,
        ast.Assign,
        ast.AnnAssign,
    )
    unexpected = [
        type(node).__name__
        for node in root_module.body
        if not isinstance(node, permitted)
    ]
    assert not unexpected, f"Unexpected package-root statements: {unexpected}"


def test_public_evidence_uses_only_domain_root_imports() -> None:
    """Keep Data usage and integration evidence on domain package roots."""
    repository_root = DATA_ROOT.parents[2]
    evidence_files = [
        *(repository_root / "tests" / "data" / "usage").rglob("*.py"),
        *(repository_root / "tests" / "data" / "integration").rglob("*.py"),
    ]
    violations: list[str] = []
    for path in evidence_files:
        relative = path.relative_to(repository_root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and (
                    node.module.startswith("app.services.data.")
                    or node.module.startswith("app.services.brokers.")
                )
            ):
                violations.append(f"{relative}:{node.lineno}:{node.module}")
    assert not violations, f"Domain deep imports are prohibited: {violations}"


def test_domain_import_has_no_external_or_persistent_side_effect() -> None:
    """Assert a fresh Data import cannot write, connect, spawn, or mutate env."""
    script = """
import asyncio
import builtins
import os
import socket
import sqlite3
import subprocess
import threading

environment = dict(os.environ)
real_open = builtins.open

def guarded_open(file, mode="r", *args, **kwargs):
    if any(flag in mode for flag in ("w", "a", "x", "+")):
        raise AssertionError(f"import attempted filesystem mutation: {file}")
    return real_open(file, mode, *args, **kwargs)

def blocked(*args, **kwargs):
    raise AssertionError("import attempted an external side effect")

builtins.open = guarded_open
socket.socket.connect = blocked
sqlite3.connect = blocked
subprocess.Popen = blocked
threading.Thread.start = blocked
os.mkdir = blocked
os.makedirs = blocked

import app.services.data

assert dict(os.environ) == environment
assert app.services.data.__all__
"""
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and source.
        [sys.executable, "-c", script],
        cwd=Path(__file__).parents[3],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr

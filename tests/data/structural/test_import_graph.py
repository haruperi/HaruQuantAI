"""Repository-scale structural guards for the focused DATA architecture."""

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
        "alignment",
        "data_jobs",
        "datasets",
        "economic_calendar",
        "evidence",
        "integrity",
        "market_data",
        "market_events",
        "replay",
        "runtime_stores",
        "sources",
        "synthetic_data",
        "time_sessions",
        "transformation",
    }
)
# Directories that hold internal support rather than a registered feature, and so
# carry no `FEAT-DATA-NN` row. `migrations/` holds schema definitions applied by
# the runner in `persistence/`; it is deliberately not a feature, per the decision
# that persistence and schema packages are private support packages.
SUPPORT_DIRECTORIES = frozenset({"_shared", "contracts", "migrations", "persistence"})
PERMITTED_ROOT_FILES = frozenset(
    {
        "README.md",
        "__init__.py",
        "_limits.py",
        "_settings.py",
        "py.typed",
    }
)
REQUIRED_ROOT_FILES = frozenset(
    {"README.md", "__init__.py", "_limits.py", "_settings.py"}
)
REMOVED_LEGACY_DIRECTORIES = frozenset(
    {
        "adapters",
        "artifact_catalog",
        "audit",
        "config",
        "gateway",
        "limits",
        "local_datasets",
        "models",
        "quality",
        "realtime_feeds",
        "replay_packages",
        "research_sources",
        "retrieval",
        "scheduler",
        "security",
        "storage",
        "time",
        "tick_derivation",
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
            r"^\|\s*(?:Completed|Partial|Pending)\s*\|\s*"
            r"`FEAT-DATA-\d{2}`[^|]*\|\s*"
            r"`(?P<module>[a-z_]+)/`\s*\|",
            registry_match.group("body"),
            flags=re.MULTILINE,
        )
    }


def test_registered_feature_directories_match_the_current_package() -> None:
    """Assert the registry and actual focused feature directories agree."""
    actual = {
        path.name
        for path in DATA_ROOT.iterdir()
        if path.is_dir() and path.name != "__pycache__" and any(path.glob("*.py"))
    } - SUPPORT_DIRECTORIES
    assert actual == FEATURE_DIRECTORIES
    assert _registered_feature_modules() == FEATURE_DIRECTORIES


def test_only_permitted_infrastructure_files_exist_at_package_root() -> None:
    """Assert production behavior is contained by its owning feature folder."""
    actual = {path.name for path in DATA_ROOT.iterdir() if path.is_file()}
    assert REQUIRED_ROOT_FILES <= actual <= PERMITTED_ROOT_FILES


def test_shared_operations_is_private_boundary_support_only() -> None:
    """Keep the reconciliation-excluded adapter narrow and package-root owned."""
    support_file = DATA_ROOT / "_shared" / "operations.py"
    source = support_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(support_file))
    prohibited_calls = {
        "open",
        "urlopen",
        "execute_transaction",
        "run_data_migrations",
        "run_domain_migrations",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not prohibited_calls & called_names
    assert "logger." not in source

    repository_root = DATA_ROOT.parents[2]
    importers: set[str] = set()
    consumer_roots = (
        repository_root / "app" / "services",
        repository_root / "app" / "agentic",
    )
    for path in (path for root in consumer_roots for path in _python_files(root)):
        if path == support_file:
            continue
        if "app.services.data._shared" in path.read_text(encoding="utf-8"):
            importers.add(path.relative_to(repository_root).as_posix())
    assert importers == {"app/services/data/__init__.py"}


def test_every_feature_has_module_documentation() -> None:
    """Assert each focused feature folder owns one module README."""
    missing = [
        feature
        for feature in sorted(FEATURE_DIRECTORIES)
        if not (DATA_ROOT / feature / "README.md").is_file()
    ]
    assert not missing, f"Focused feature README files are missing: {missing}"


def test_market_data_production_files_are_in_authoritative_inventory() -> None:
    """Reconcile every FEAT-DATA-01 production file with the Data README."""
    readme = DOMAIN_README.read_text(encoding="utf-8")
    inventory = readme.split(
        "### Authoritative current production-file inventory", maxsplit=1
    )[1].split("### 4.1", maxsplit=1)[0]
    market_data_root = DATA_ROOT / "market_data"
    production_files = {
        f"market_data/{path.name}" for path in market_data_root.glob("*.py")
    }
    missing = sorted(path for path in production_files if f"`{path}`" not in inventory)
    assert not missing, f"Unregistered FEAT-DATA-01 production files: {missing}"


def test_market_data_usage_covers_registered_added_surface() -> None:
    """Keep the reconciled FEAT-DATA-01 operations in numbered usage evidence."""
    usage = (
        DATA_ROOT.parents[2] / "tests/data/usage/features/01_market_data.py"
    ).read_text(encoding="utf-8")
    required_operations = {
        "build_market_directory_request",
        "build_market_snapshot_request",
        "build_symbols_quote_request",
        "classify_symbol",
        "get_display_asset_classes",
        "get_market_snapshot",
        "get_symbols_quotes",
        "list_market_directory",
    }
    missing = sorted(name for name in required_operations if name not in usage)
    assert not missing, f"FEAT-DATA-01 usage operations are missing: {missing}"


def test_registered_features_have_exactly_one_numbered_usage_program() -> None:
    """Reconcile registry IDs, documented evidence, and numbered programs."""
    readme = DOMAIN_README.read_text(encoding="utf-8")
    registry = re.search(
        r"^### Feature Registry\s*$\n(?P<body>.*?)(?=^### |\Z)",
        readme,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert registry is not None
    registered = {
        int(match.group("number")): match.group("path")
        for match in re.finditer(
            r"`FEAT-DATA-(?P<number>\d{2})`[^\n]*?"
            r"`(?P<path>tests/data/usage/features/\d{2}_[a-z_]+\.py)`",
            registry.group("body"),
        )
    }
    usage_root = DATA_ROOT.parents[2] / "tests" / "data" / "usage" / "features"
    actual = {
        int(path.name[:2]): path.relative_to(DATA_ROOT.parents[2]).as_posix()
        for path in usage_root.glob("[0-9][0-9]_*.py")
    }
    assert registered == actual


def test_removed_legacy_packages_are_absent_and_unreferenced() -> None:
    """Assert retired parallel implementations cannot re-enter the package."""
    assert not REMOVED_LEGACY_DIRECTORIES & {
        path.name
        for path in DATA_ROOT.iterdir()
        if path.is_dir() and any(path.glob("*.py"))
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
    # The lazy boundary adds a `typing.TYPE_CHECKING` guard and the two dunder
    # resolvers. Both are declarations, not side effects, so they are permitted
    # in exactly that shape and nothing else.
    allowed_functions = {"__getattr__", "__dir__"}
    unexpected: list[str] = []
    for node in root_module.body:
        if isinstance(node, permitted):
            continue
        if isinstance(node, ast.FunctionDef) and node.name in allowed_functions:
            continue
        if isinstance(node, ast.If):
            test = node.test
            guarded = (
                isinstance(test, ast.Attribute)
                and test.attr == "TYPE_CHECKING"
                and isinstance(test.value, ast.Name)
                and test.value.id == "typing"
            )
            if guarded and all(
                isinstance(stmt, (ast.Import, ast.ImportFrom)) for stmt in node.body
            ):
                continue
        unexpected.append(type(node).__name__)
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


def test_cross_domain_consumers_use_only_the_data_package_root() -> None:
    """Reject static deep Data imports in the governed consumer categories."""
    repository_root = DATA_ROOT.parents[2]
    candidate_files = [
        *(
            path
            for path in (repository_root / "app" / "services").rglob("*.py")
            if DATA_ROOT not in path.parents
        ),
        *(repository_root / "app" / "agentic").rglob("*.py"),
        *(repository_root / "tests").glob("*/usage/**/*.py"),
        *(repository_root / "tests").glob("*/integration/**/*.py"),
    ]
    violations: list[str] = []
    for path in candidate_files:
        for module in sorted(_domain_imports(path, module_level_only=False)):
            if module != DOMAIN_PREFIX:
                relative = path.relative_to(repository_root).as_posix()
                violations.append(f"{relative}:{module}")
    assert not violations, f"Cross-domain consumers deep-import Data: {violations}"


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

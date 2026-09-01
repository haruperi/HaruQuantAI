"""NFR-INDI-001/NFR-INDI-003: purity, dependency, and import-safety guards."""

from __future__ import annotations

import ast
import functools
import importlib
import re
import sys
from pathlib import Path

INDICATORS_ROOT = Path("app/services/indicators").resolve()
DOMAIN_PREFIX = "app.services.indicators"
DATA_PUBLIC_ROOT = "app.services.data"

# The complete approved runtime dependency surface for this pure domain.
ALLOWED_THIRD_PARTY = {"numpy", "pandas"}
ALLOWED_LOCAL_PREFIXES = (
    DOMAIN_PREFIX,
    "app.contracts",
    "app.composition",
    "app.kernel",
)

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

EXPECTED_FEATURE_DIRECTORIES = {
    "core",
    "liquidity",
    "market_speed",
    "momentum",
    "order_flow",
    "patterns",
    "regime",
    "snapshots",
    "structure",
    "trend",
    "volatility",
    "volume",
}
EXPECTED_FEATURE_IDS = tuple(f"FEAT-INDI-{index:02d}" for index in range(1, 13))


def _python_files() -> list[Path]:
    """Return every non-cached production source file in the Indicators package.

    Returns:
        Sorted list of source file paths.
    """
    return sorted(
        p
        for p in INDICATORS_ROOT.rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "example.py"
    )


@functools.cache
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
    if module == DATA_PUBLIC_ROOT or module.startswith(ALLOWED_LOCAL_PREFIXES):
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


def test_production_feature_directories_match_consolidated_registry() -> None:
    """Production feature folders match the twelve registered owners."""
    actual = {
        path.name
        for path in INDICATORS_ROOT.iterdir()
        if path.is_dir()
        and path.name not in {"__pycache__", "migrations"}
        and any(path.glob("*.py"))
    }
    assert actual == EXPECTED_FEATURE_DIRECTORIES
    assert not any((INDICATORS_ROOT / "candles").glob("*.py"))
    assert not any((INDICATORS_ROOT / "input_guards").glob("*.py"))


def test_feature_registry_ids_are_contiguous() -> None:
    """The owning registry uses the contiguous 01-through-12 identity range."""
    readme = (INDICATORS_ROOT / "README.md").read_text(encoding="utf-8")
    start = readme.index("### Feature Registry")
    end = readme.index("\n### ", start + 1)
    feature_ids = tuple(
        re.findall(
            r"^\| Completed \| `(FEAT-INDI-\d{2})`",
            readme[start:end],
            re.MULTILINE,
        )
    )
    assert feature_ids == EXPECTED_FEATURE_IDS


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
            if module.startswith("app.services.") and not (
                module.startswith(DOMAIN_PREFIX) or module == DATA_PUBLIC_ROOT
            ):
                violations.append(f"{path.name}: {module}")
    assert violations == [], f"cross-domain imports: {violations}"


def test_registry_does_not_import_feature_implementations() -> None:
    """The immutable registry stores import-path identity, never live imports."""
    registry_path = INDICATORS_ROOT / "core" / "registry.py"
    feature_packages = ("trend", "volatility", "momentum", "volume", "patterns")
    imported = _imported_roots(registry_path)
    for module in imported:
        for feature in feature_packages:
            assert not module.startswith(f"{DOMAIN_PREFIX}.{feature}"), (
                f"registry imports feature implementation {module}"
            )


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
        "proprietary",
    )
    for name in module.__all__:
        for mode in unsupported:
            assert mode not in name, f"unsupported mode {mode} exposed as {name}"

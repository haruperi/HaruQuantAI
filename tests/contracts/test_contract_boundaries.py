"""Dependency-boundary and import-purity tests for the contracts package.

Verifies statically (AST) that no contracts module imports services,
composition, or UI code, that every ``__init__.py`` stays import-pure, and
that cross-model references stay inside ``app.contracts``; then verifies
the same dynamically by importing every models module in a fresh
subprocess and inspecting ``sys.modules``. Finally, executes every
``@runtime_checkable`` Protocol stub method declared by the namespace
ports modules (including the frozen legacy workspace/interfaces/plugins/ui
ports) so their documented ``...`` bodies run under coverage.
"""

from __future__ import annotations

import ast
import asyncio
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_ROOT = REPO_ROOT / "app" / "contracts"

OWNERS: tuple[str, ...] = (
    "common",
    "workspace",
    "catalogue",
    "data",
    "strategy",
    "simulator",
    "analytics",
    "research",
    "portfolio",
    "orchestration",
    "interfaces",
    "ui",
    "plugins",
    "broker",
    "risk",
    "trading",
)

# Forbidden upstream dependency roots for the contracts package.
FORBIDDEN_IMPORT_ROOTS: tuple[str, ...] = (
    "app.services",
    "app.composition",
    "app.ui",
)

# Modules whose app-internal imports may only reference app.contracts.*.
MODEL_MODULES: tuple[str, ...] = ("models", "events", "errors")

# Module-level cache of parsed trees so the file-heavy AST scans run once.
_PARSED_TREES: dict[str, object] = {}


def _iter_contract_modules() -> list[Path]:
    """Collect every Python module under app/contracts except __init__ files."""
    return [
        path
        for path in sorted(CONTRACTS_ROOT.rglob("*.py"))
        if path.name != "__init__.py"
        and "__pycache__" not in path.parts
        and "wire" not in path.parts
    ]


def _parsed_tree(path: Path) -> ast.Module:
    """Parse one contracts module once and reuse the cached AST.

    Args:
        path: Python module path under app/contracts.

    Returns:
        The parsed module AST.
    """
    key = str(path.relative_to(REPO_ROOT))
    tree = _PARSED_TREES.get(key)
    if tree is None:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        _PARSED_TREES[key] = tree
    assert isinstance(tree, ast.Module)
    return tree


def _imported_modules(node: ast.AST) -> set[str]:
    """Extract the absolute module names imported by one AST node set.

    Args:
        node: Parsed module AST.

    Returns:
        Every module referenced by ``import x`` and ``from x import y``.
    """
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            names.update(alias.name for alias in child.names)
        elif (
            isinstance(child, ast.ImportFrom)
            and child.module is not None
            and child.level == 0
        ):
            names.add(child.module)
    return names


def test_contract_modules_never_import_forbidden_roots() -> None:
    """Verify no contracts module imports services, composition, or UI."""
    violations: list[str] = []
    for path in _iter_contract_modules():
        tree = _parsed_tree(path)
        for module_name in _imported_modules(tree):
            if module_name.startswith(FORBIDDEN_IMPORT_ROOTS):
                violations.append(
                    f"{path.relative_to(REPO_ROOT)} imports {module_name}"
                )
    assert not violations, f"forbidden contract imports: {violations}"


def test_init_files_are_docstring_or_empty_only() -> None:
    """Verify every __init__.py contains no imports or executable statements."""
    init_files = sorted(CONTRACTS_ROOT.rglob("__init__.py"))
    assert init_files, "no __init__.py files found under app/contracts"
    for path in init_files:
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        forbidden = [
            node
            for node in tree.body
            if not (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
        ]
        assert not forbidden, (
            f"{path.relative_to(REPO_ROOT)} contains statements beyond a docstring: "
            f"{[type(node).__name__ for node in forbidden]}"
        )
        assert not _imported_modules(tree), (
            f"{path.relative_to(REPO_ROOT)} contains imports"
        )


def test_model_modules_only_reference_contracts() -> None:
    """Verify model/event/error modules import only app.contracts namespaces."""
    violations: list[str] = []
    for path in _iter_contract_modules():
        if path.stem not in MODEL_MODULES:
            continue
        tree = _parsed_tree(path)
        for module_name in _imported_modules(tree):
            if module_name.startswith("app.") and not module_name.startswith(
                "app.contracts"
            ):
                violations.append(
                    f"{path.relative_to(REPO_ROOT)} imports {module_name}"
                )
    assert not violations, f"cross-owner imports outside app.contracts: {violations}"


def test_models_import_purity_in_fresh_subprocess() -> None:
    """Verify importing every models module never loads services or composition."""
    probe = "\n".join(
        [
            "import importlib",
            "import json",
            "import sys",
            "OWNERS = (",
            *(f"    {owner!r}," for owner in OWNERS),
            ")",
            "for owner in OWNERS:",
            "    importlib.import_module(f'app.contracts.{owner}.models')",
            "loaded = [",
            "    name",
            "    for name in sys.modules",
            "    if name.startswith(('app.services', 'app.composition', 'app.ui'))",
            "]",
            "print(json.dumps(loaded))",
        ]
    )
    completed = subprocess.run(  # noqa: S603 - fixed argv of trusted constants
        [sys.executable, "-c", probe],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, (
        f"fresh imports failed:\nstdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    loaded = completed.stdout.strip().splitlines()[-1]
    assert loaded == "[]", f"impure modules loaded by contracts imports: {loaded}"


# ---------------------------------------------------------------------------
# Execution of every ports-module Protocol stub body
# ---------------------------------------------------------------------------

# The frozen legacy ports modules whose protocol bodies must also execute.
LEGACY_PORTS_OWNERS: frozenset[str] = frozenset(
    {"workspace", "interfaces", "plugins", "ui"}
)


def _ports_module_owners() -> list[str]:
    """List owner identifiers whose namespace exports a ports module.

    Returns:
        Owners from the canonical namespace order that define ``ports.py``.
    """
    return [
        owner for owner in OWNERS if (CONTRACTS_ROOT / owner / "ports.py").is_file()
    ]


def _is_local_runtime_protocol(obj: object, module_name: str) -> bool:
    """Determine whether one object is a runtime-checkable Protocol class.

    Args:
        obj: Candidate module attribute.
        module_name: Dotted name of the owning ports module.

    Returns:
        True when the object is a class directly defined in the module and
        carrying both the Protocol and runtime-checkable markers.
    """
    if not isinstance(obj, type):
        return False
    return (
        getattr(obj, "_is_protocol", False) is True
        and getattr(obj, "_is_runtime_protocol", False) is True
        and obj.__module__ == module_name
    )


def _discover_port_method_cases() -> list[tuple[str, str, str]]:
    """Discover every callable stub of every ports-module Protocol class.

    Returns:
        Tuples of (owner, protocol name, method name) for every
        non-dunder callable attribute defined directly on a discovered
        ``@runtime_checkable`` Protocol, in canonical owner order.
    """
    cases: list[tuple[str, str, str]] = []
    for owner in _ports_module_owners():
        module = importlib.import_module(f"app.contracts.{owner}.ports")
        for protocol_name, protocol in sorted(vars(module).items()):
            if not _is_local_runtime_protocol(protocol, module.__name__):
                continue
            for method_name, stub in sorted(vars(protocol).items()):
                if method_name.startswith("__") or not callable(stub):
                    continue
                cases.append((owner, protocol_name, method_name))
    return cases


# Discovered once at import so every ports module is imported and scanned a
# single time per test process.
PORT_METHOD_CASES: list[tuple[str, str, str]] = _discover_port_method_cases()


def test_ports_discovery_spans_every_namespace_module() -> None:
    """Verify protocol stub discovery covers every ports module."""
    cases = PORT_METHOD_CASES
    assert cases, "no ports protocol methods discovered"
    owners = {owner for owner, _protocol, _method in cases}
    assert owners == set(_ports_module_owners())
    assert owners >= LEGACY_PORTS_OWNERS
    protocols = {(owner, protocol) for owner, protocol, _method in cases}
    assert len(protocols) >= 100
    assert len(cases) >= 150


@pytest.mark.parametrize(
    ("owner", "protocol_name", "method_name"),
    PORT_METHOD_CASES,
    ids=[f"{o}.{p}.{m}" for o, p, m in PORT_METHOD_CASES],
)
def test_protocol_stub_body_executes_and_returns_none(
    owner: str,
    protocol_name: str,
    method_name: str,
) -> None:
    """Execute one Protocol stub body through a minimal concrete subclass.

    The ``...`` bodies exist to carry signatures and docstrings; invoking
    them with ``None`` bound to every declared parameter (keyword-only
    signatures included) proves each stub is callable and returns None
    while executing the protocol body for coverage.

    Args:
        owner: Namespace owning the ports module.
        protocol_name: Protocol class name.
        method_name: Stub method name.
    """
    module = importlib.import_module(f"app.contracts.{owner}.ports")
    protocol = getattr(module, protocol_name)
    assert isinstance(protocol, type)
    stub = vars(protocol)[method_name]
    impl = type("Impl", (protocol,), {})()
    args: list[object] = []
    kwargs: dict[str, object] = {}
    for param_name, param in inspect.signature(stub).parameters.items():
        if param_name == "self":
            continue
        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            args.append(None)
        elif param.kind is inspect.Parameter.KEYWORD_ONLY:
            kwargs[param_name] = None
    result = getattr(impl, method_name)(*args, **kwargs)
    if inspect.isawaitable(result):
        assert asyncio.run(result) is None
    else:
        assert result is None

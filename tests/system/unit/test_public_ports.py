import ast
import importlib
from pathlib import Path

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_APP_ROOT = _REPOSITORY_ROOT / "app"
_DOMAIN_PORTS = (
    "app.utils",
    "app.services.brokers",
    "app.services.data",
    "app.services.indicators",
    "app.services.strategy",
    "app.services.risk",
    "app.services.trading",
    "app.services.simulator",
    "app.services.analytics",
    "app.services.optimization",
    "app.services.research",
    "app.services.portfolio",
    "app.services.api",
)
_DOMAIN_BY_PATH = {tuple(port.split(".")): port for port in _DOMAIN_PORTS}


@pytest.mark.parametrize("port", _DOMAIN_PORTS)
def test_domain_exposes_explicit_package_root_port(port):
    module = importlib.import_module(port)

    assert isinstance(module.__all__, tuple)
    assert len(module.__all__) == len(set(module.__all__))
    assert all(not name.startswith("_") for name in module.__all__)
    assert all(hasattr(module, name) for name in module.__all__)


def test_cross_domain_imports_use_public_ports_and_remain_acyclic():
    dependency_graph = {port: set() for port in _DOMAIN_PORTS}

    for path in sorted(_APP_ROOT.rglob("*.py")):
        source_domain = _domain_for_path(path)
        if source_domain is None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for imported_module in _imported_modules(tree):
            target_domain = _domain_for_module(imported_module)
            if target_domain is None or target_domain == source_domain:
                continue
            _assert_public_import(imported_module, target_domain, path)
            dependency_graph[source_domain].add(target_domain)

    _assert_acyclic(dependency_graph)


def test_shared_contract_classes_keep_version_and_schema_identity_together():
    for path in sorted(_APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            fields = {
                statement.target.id
                for statement in node.body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
            }
            identity_fields = fields & {"contract_version", "schema_id"}
            assert not identity_fields or identity_fields == {
                "contract_version",
                "schema_id",
            }, f"{path}:{node.lineno} must define contract_version and schema_id"


def test_registered_system_contracts_have_explicit_v1_versions():
    project = (_REPOSITORY_ROOT / "docs" / "PROJECT.md").read_text(
        encoding="utf-8",
    )
    contract_section = project.split("## 5. System Interfaces and Contracts", 1)[1]
    contract_table = contract_section.split("### Contract ownership rules", 1)[0]
    rows = [
        tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        for line in contract_table.splitlines()
        if line.startswith(("| Missing", "| Partial", "| Completed"))
    ]

    assert rows
    assert all(row[2] == "`v1`" for row in rows)


def _domain_for_path(path: Path) -> str | None:
    relative_parts = path.relative_to(_REPOSITORY_ROOT).with_suffix("").parts
    for package_parts, domain in _DOMAIN_BY_PATH.items():
        if relative_parts[: len(package_parts)] == package_parts:
            return domain
    return None


def _domain_for_module(module: str) -> str | None:
    module_parts = tuple(module.split("."))
    for package_parts, domain in _DOMAIN_BY_PATH.items():
        if module_parts[: len(package_parts)] == package_parts:
            return domain
    return None


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    return tuple(imported)


def _assert_public_import(module: str, domain: str, path: Path) -> None:
    module_depth = len(module.split("."))
    public_feature_depth = len(domain.split(".")) + 1
    assert module_depth <= public_feature_depth, (
        f"{path} imports internal cross-domain module {module}; "
        f"use the {domain} root or an immediate public feature port"
    )


def _assert_acyclic(graph: dict[str, set[str]]) -> None:
    incoming = dict.fromkeys(graph, 0)
    for dependencies in graph.values():
        for dependency in dependencies:
            incoming[dependency] += 1
    ready = [node for node, count in incoming.items() if count == 0]
    visited = 0
    while ready:
        node = ready.pop()
        visited += 1
        for dependency in graph[node]:
            incoming[dependency] -= 1
            if incoming[dependency] == 0:
                ready.append(dependency)

    assert visited == len(graph), "Observed cross-domain import graph contains a cycle"

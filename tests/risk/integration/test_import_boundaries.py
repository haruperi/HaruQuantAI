"""Integration checks for Risk package dependency and import boundaries."""

import ast
from pathlib import Path

from app.services import risk


def test_risk_imports_do_not_cross_execution_or_provider_boundaries() -> None:
    """Reject direct broker, provider, database, or Trading implementation imports."""
    root = Path(risk.__file__).resolve().parent
    forbidden = (
        "app.services.brokers",
        "app.services.trading",
        "sqlalchemy",
        "MetaTrader5",
    )
    violations: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.append(node.module)
        if any(name.startswith(forbidden) for name in imported):
            violations.append(str(path.relative_to(root)))
    assert violations == []


def test_private_state_ports_are_not_root_exports() -> None:
    """Keep signer material, storage ports, and persistence schemas private."""
    private_names = {
        "_TokenStateStore",
        "_RiskAuditStore",
        "_KillSwitchStateStore",
        "_AllocationDecisionStore",
        "_EligibilityDecisionStore",
    }
    assert private_names.isdisjoint(risk.__all__)


def test_repository_consumers_use_only_the_risk_package_root() -> None:
    """Reject deep Risk imports from production and non-unit consumer evidence."""
    repository = Path(__file__).resolve().parents[3]
    risk_root = repository / "app" / "services" / "risk"
    candidates = [
        *(
            path
            for path in (repository / "app").rglob("*.py")
            if not path.is_relative_to(risk_root)
        ),
        *(
            path
            for path in (repository / "tests").rglob("*.py")
            if "unit" not in path.relative_to(repository / "tests").parts
        ),
    ]
    violations: list[str] = []
    for path in candidates:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.module.startswith("app.services.risk.")
            ):
                violations.append(
                    f"{path.relative_to(repository)}:{node.lineno}:{node.module}"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("app.services.risk."):
                        violations.append(
                            f"{path.relative_to(repository)}:{node.lineno}:{alias.name}"
                        )
    assert violations == []

"""Automated tests enforcing architectural rules and structural invariants."""

import ast
from pathlib import Path

from scripts.architecture_check import (
    APP_ROOT,
    ArchitecturalVisitor,
    check_directory,
)


def test_codebase_architectural_invariants_pass() -> None:
    """Verify that all files across the current codebase pass architectural checks."""
    violations = check_directory(APP_ROOT)
    assert not violations, f"Expected 0 violations, found: {violations}"


def test_init_purity_violation(tmp_path: Path) -> None:
    """Test ARCH-001: __init__.py containing executable code is flagged."""
    init_file = tmp_path / "app" / "services" / "workspace" / "__init__.py"
    init_file.parent.mkdir(parents=True, exist_ok=True)
    init_file.write_text("x = 10\nimport foo\n", encoding="utf-8")

    tree = ast.parse(init_file.read_text(encoding="utf-8"))
    visitor = ArchitecturalVisitor(init_file)
    visitor.check_init_purity(tree)
    visitor.visit(tree)

    rules = [v.rule for v in visitor.violations]
    assert "ARCH-001-INIT-PURITY" in rules


def test_unmanaged_task_violation(tmp_path: Path) -> None:
    """Test ARCH-002: direct asyncio.create_task in a service is flagged."""
    service_file = (
        tmp_path / "app" / "services" / "workspace" / "consumer" / "worker.py"
    )
    service_file.parent.mkdir(parents=True, exist_ok=True)
    service_file.write_text(
        "import asyncio\nasync def run(): asyncio.create_task(run())\n",
        encoding="utf-8",
    )

    tree = ast.parse(service_file.read_text(encoding="utf-8"))
    visitor = ArchitecturalVisitor(service_file)
    visitor.visit(tree)

    rules = [v.rule for v in visitor.violations]
    assert "ARCH-002-MANAGED-TASKS" in rules


def test_logging_basic_config_violation(tmp_path: Path) -> None:
    """Test ARCH-003: logging.basicConfig in a service is flagged."""
    service_file = tmp_path / "app" / "services" / "beta" / "provider" / "setup.py"
    service_file.parent.mkdir(parents=True, exist_ok=True)
    service_file.write_text(
        "import logging\nlogging.basicConfig(level=logging.INFO)\n",
        encoding="utf-8",
    )

    tree = ast.parse(service_file.read_text(encoding="utf-8"))
    visitor = ArchitecturalVisitor(service_file)
    visitor.visit(tree)

    rules = [v.rule for v in visitor.violations]
    assert "ARCH-003-NO-LOGGING-BASICCONFIG" in rules


def test_contract_purity_violation(tmp_path: Path) -> None:
    """Test ARCH-004: contract importing a service is flagged."""
    contract_file = tmp_path / "app" / "contracts" / "data" / "bad_contract.py"
    contract_file.parent.mkdir(parents=True, exist_ok=True)
    contract_file.write_text(
        "from app.services.alpha.consumer.worker import Foo\n",
        encoding="utf-8",
    )

    tree = ast.parse(contract_file.read_text(encoding="utf-8"))
    visitor = ArchitecturalVisitor(contract_file)
    visitor.visit(tree)

    rules = [v.rule for v in visitor.violations]
    assert "ARCH-004-CONTRACT-PURITY" in rules


def test_feature_independence_violation(tmp_path: Path) -> None:
    """Test ARCH-006: Feature A importing Feature B is flagged."""
    feature_file = (
        tmp_path / "app" / "services" / "workspace" / "consumer" / "consumer.py"
    )
    feature_file.parent.mkdir(parents=True, exist_ok=True)
    feature_file.write_text(
        "from app.services.workspace.provider.service import Provider\n",
        encoding="utf-8",
    )

    tree = ast.parse(feature_file.read_text(encoding="utf-8"))
    visitor = ArchitecturalVisitor(feature_file)
    visitor.visit(tree)

    rules = [v.rule for v in visitor.violations]
    assert "ARCH-006-FEATURE-INDEPENDENCE" in rules

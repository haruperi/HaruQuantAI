"""Enforce that capability specifications import with zero business packages installed.

Traces to: P3-T05, Gate G3
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.removability.harness import run_in_fresh_process

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS_ROOT = _REPO_ROOT / "app" / "contracts"


def test_capability_specs_have_no_business_imports() -> None:
    """Verify via AST that no file under app/contracts imports app.services or app.agentic."""
    cap_files = sorted(_CONTRACTS_ROOT.rglob("*.py"))
    assert len(cap_files) >= 5, "Expected at least 5 capability files"

    for cap_file in cap_files:
        rel_path = cap_file.relative_to(_REPO_ROOT).as_posix()
        tree = ast.parse(cap_file.read_text(encoding="utf-8"), filename=rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("app.services"), (
                        f"Forbidden import '{alias.name}' in {rel_path}:{node.lineno}"
                    )
                    assert not alias.name.startswith("app.agentic"), (
                        f"Forbidden import '{alias.name}' in {rel_path}:{node.lineno}"
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not module.startswith("app.services"), (
                    f"Forbidden from-import '{module}' in {rel_path}:{node.lineno}"
                )
                assert not module.startswith("app.agentic"), (
                    f"Forbidden from-import '{module}' in {rel_path}:{node.lineno}"
                )


def test_capability_specs_import_without_business_packages() -> None:
    """Verify all capability modules import in fresh process with app.services and app.agentic blocked."""
    isolation_script = """
import sys
from importlib.abc import MetaPathFinder

class BlockedDomainFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("app.services") or fullname.startswith("app.agentic"):
            raise ImportError(f"blocked business import: {fullname}")
        return None

sys.meta_path.insert(0, BlockedDomainFinder())

import app.contracts
import app.contracts.indicator
import app.contracts.indicator.common
import app.contracts.indicator.common.v1
import app.contracts.indicator.rsi
import app.contracts.indicator.rsi.v1
import app.contracts.indicator.williams_r
import app.contracts.indicator.williams_r.v1

for mod in sys.modules:
    assert not mod.startswith("app.services"), f"Blocked module was loaded: {mod}"
    assert not mod.startswith("app.agentic"), f"Blocked module was loaded: {mod}"

print("CAPABILITIES_ISOLATION_OK")
"""

    result = run_in_fresh_process(
        repository_root=_REPO_ROOT,
        script=isolation_script,
        timeout_seconds=30.0,
    )

    assert result.returncode == 0, (
        f"Capability import isolation failed with returncode {result.returncode}:\n"
        f"  STDOUT: {result.stdout}\n"
        f"  STDERR: {result.stderr}"
    )
    assert "CAPABILITIES_ISOLATION_OK" in result.stdout
    assert result.stderr == ""


def test_capability_public_exports_are_frozen() -> None:
    """Verify exact public exports for every capability module."""
    import app.contracts as cap_root
    import app.contracts.indicator as cap_ind
    import app.contracts.indicator.common as cap_common_pkg
    import app.contracts.indicator.common.v1 as cap_common_v1
    import app.contracts.indicator.rsi as cap_rsi_pkg
    import app.contracts.indicator.rsi.v1 as cap_rsi_v1
    import app.contracts.indicator.williams_r as cap_wr_pkg
    import app.contracts.indicator.williams_r.v1 as cap_wr_v1

    assert cap_root.__all__ == ()
    assert cap_ind.__all__ == ()
    assert cap_common_pkg.__all__ == ()
    assert cap_common_v1.__all__ == (
        "IndicatorConfigV1",
        "IndicatorResultV1",
        "MarketDatasetV1",
        "OHLCVRecordV1",
    )
    assert cap_rsi_pkg.__all__ == ()
    assert cap_rsi_v1.__all__ == (
        "CAPABILITY_ID",
        "RsiCapabilityV1",
        "RsiFunctionV1",
    )
    assert cap_wr_pkg.__all__ == ()
    assert cap_wr_v1.__all__ == (
        "CAPABILITY_ID",
        "WilliamsRCapabilityV1",
        "WilliamsRFunctionV1",
    )

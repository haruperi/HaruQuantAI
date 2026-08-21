#!/usr/bin/env python
"""Physically remove one feature and verify graceful application degradation."""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class FeatureRemovalTarget:
    feature_id: str
    pkg_rel_path: str
    test_rel_path: str
    entry_point_name: str
    expected_missing_capability: str


TARGETS: dict[str, FeatureRemovalTarget] = {
    "FEAT-DATA-RETRIEVE_BARS": FeatureRemovalTarget(
        "FEAT-DATA-RETRIEVE_BARS",
        "app/services/data/historical_bars",
        "tests/services/data/historical_bars",
        "data-historical-bars",
        "data.historical-bars@1",
    ),
    "FEAT-BROKER-FEED_MOCK": FeatureRemovalTarget(
        "FEAT-BROKER-FEED_MOCK",
        "app/services/broker/mock_feed",
        "tests/services/broker/mock_feed",
        "broker-mock-feed",
        "broker.market-data@1",
    ),
    "FEAT-SYS-PERSIST_STORAGE": FeatureRemovalTarget(
        "FEAT-SYS-PERSIST_STORAGE",
        "app/services/system/storage",
        "tests/services/system/storage",
        "system.storage@1",
        "system.storage@1",
    ),
}
# Correct the storage entry-point name while keeping target construction compact.
TARGETS["FEAT-SYS-PERSIST_STORAGE"] = FeatureRemovalTarget(
    "FEAT-SYS-PERSIST_STORAGE",
    "app/services/system/storage",
    "tests/services/system/storage",
    "system-persist-storage",
    "system.storage@1",
)


def run_cmd(cmd: list[str], cwd: Path, step_name: str) -> None:
    print(f"--> {step_name}: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True, check=False)
    if result.returncode != 0:
        msg = f"Step '{step_name}' failed with exit code {result.returncode}"
        raise RuntimeError(msg)


def remove_entry_point(pyproject_path: Path, entry_point_name: str) -> None:
    content = pyproject_path.read_text(encoding="utf-8")
    pattern = rf"^{re.escape(entry_point_name)}\s*=.*$\n?"
    pyproject_path.write_text(
        re.sub(pattern, "", content, flags=re.MULTILINE),
        encoding="utf-8",
    )


def remove_import_linter_module(linter_path: Path, pkg_rel_path: str) -> None:
    if not linter_path.exists():
        return
    module_name = pkg_rel_path.replace("/", ".")
    lines = [
        line
        for line in linter_path.read_text(encoding="utf-8").splitlines()
        if module_name not in line
    ]
    linter_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def runtime_verification_script(target: FeatureRemovalTarget) -> str:
    return f'''
import asyncio
from app.composition.engine import CompositionEngine
from app.kernel.feature import FeatureState

async def main():
    engine = CompositionEngine()
    config = """
    [application]
    profile = "research"
    [features.FEAT-SYS-PERSIST_STORAGE]
    enabled = true
    driver = "disk"
    base_path = "removal-test-storage"
    [features.FEAT-BROKER-FEED_MOCK]
    enabled = true
    [features.FEAT-DATA-RETRIEVE_BARS]
    enabled = true
    """
    await engine.load_and_reconcile_toml(config)
    status = engine.get_status()
    assert "{target.feature_id}" not in status.active_features
    assert not engine.registry.is_available("{target.expected_missing_capability}")

    if "{target.feature_id}" == "FEAT-BROKER-FEED_MOCK":
        assert status.feature_states["FEAT-DATA-RETRIEVE_BARS"] == FeatureState.BLOCKED
        assert engine.registry.is_available("system.storage@1")
    elif "{target.feature_id}" == "FEAT-DATA-RETRIEVE_BARS":
        assert engine.registry.is_available("broker.market-data@1")
        assert engine.registry.is_available("system.storage@1")
    else:
        assert engine.registry.is_available("broker.market-data@1")
        assert engine.registry.is_available("data.historical-bars@1")

    await engine.shutdown()

asyncio.run(main())
'''


def verify_feature_removal(target: FeatureRemovalTarget) -> bool:
    print(f"Physical-removal verification: {target.feature_id}")
    with tempfile.TemporaryDirectory(prefix="haru_removal_") as temp_dir:
        temp_path = Path(temp_dir)

        def ignore_patterns(_path: str, names: list[str]) -> set[str]:
            return {
                ".git",
                ".venv",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "htmlcov",
                ".coverage",
            }.intersection(names)

        shutil.copytree(ROOT_DIR, temp_path, dirs_exist_ok=True, ignore=ignore_patterns)
        package = temp_path / target.pkg_rel_path
        if package.exists():
            shutil.rmtree(package)
        feature_tests = temp_path / target.test_rel_path
        if feature_tests.exists():
            shutil.rmtree(feature_tests)

        remove_entry_point(temp_path / "pyproject.toml", target.entry_point_name)
        remove_import_linter_module(temp_path / ".importlinter", target.pkg_rel_path)

        commands = [
            (["uv", "sync", "--frozen", "--dev"], "Environment sync"),
            (["uv", "run", "--frozen", "ruff", "format", "--check", "."], "Ruff format"),
            (["uv", "run", "--frozen", "ruff", "check", "."], "Ruff lint"),
            (["uv", "run", "--frozen", "mypy"], "Mypy"),
            (["uv", "run", "--frozen", "lint-imports"], "Import Linter"),
            (
                ["uv", "run", "--frozen", "python", "scripts/architecture_check.py"],
                "Architecture AST",
            ),
            (["uv", "run", "--frozen", "pytest"], "Remaining test suite"),
            (
                [
                    "uv",
                    "run",
                    "--frozen",
                    "python",
                    "-c",
                    runtime_verification_script(target),
                ],
                "Runtime degradation assertions",
            ),
        ]
        for command, name in commands:
            run_cmd(command, temp_path, name)

    print(f"[SUCCESS] {target.feature_id} is physically removable")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feature_id", choices=sorted(TARGETS))
    args = parser.parse_args()
    try:
        return 0 if verify_feature_removal(TARGETS[args.feature_id]) else 1
    except RuntimeError as error:
        print(f"[FAILURE] {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

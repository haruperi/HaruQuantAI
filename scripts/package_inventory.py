"""Inventory shipping ownership without executing feature code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.host.packages import PACKAGE_ROOTS, PackageInventory, scan_packages

SOURCE_SUFFIXES = frozenset(
    {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".css",
        ".json",
        ".png",
        ".svg",
        ".jpg",
        ".md",
    }
)
TEST_ROOTS = (
    "tests/workspace",
    "tests/plugins",
    "app/ui/tests/unit/workspace",
    "app/ui/tests/unit/plugins",
)


def unowned_files(root: Path, inventory: PackageInventory) -> tuple[str, ...]:
    """Find unclaimed shipping files and tests, including invalid packages."""
    owned = {name for p in inventory.packages for name in p.owned_paths.files()}
    found: set[str] = set()
    for prefix in (*PACKAGE_ROOTS, *TEST_ROOTS):
        directory = root / prefix
        if not directory.is_dir():
            continue
        for path in directory.rglob("*", recurse_symlinks=False):
            if (
                path.suffix in SOURCE_SUFFIXES
                and path.is_file()
                and "__pycache__" not in path.parts
            ):
                name = path.relative_to(root).as_posix()
                if name not in owned and name not in {
                    "app/workspace/__init__.py",
                    "app/plugins/__init__.py",
                }:
                    found.add(name)
    return tuple(sorted(found))


def source_fingerprint(root: Path) -> str:
    """Bind evidence to actual source/config/test files, excluding generated output."""
    files: list[Path] = []
    for prefix in ("app", "tests", "scripts", "docs/dev/schemas", ".github/workflows"):
        folder = root / prefix
        if not folder.is_dir():
            continue
        excluded = {
            "node_modules",
            "__pycache__",
            "dist",
            "test-results",
            "playwright-report",
        }
        for directory, children, names in os.walk(folder, followlinks=False):
            children[:] = [
                name
                for name in children
                if name not in excluded
                and not (Path(directory) / name).is_symlink()
                and not (Path(directory) / name).is_junction()
            ]
            files.extend(
                Path(directory) / name
                for name in names
                if Path(name).suffix
                in SOURCE_SUFFIXES | {".yml", ".yaml", ".toml", ".cjs"}
            )
    files.extend(
        root / name
        for name in (
            "pyproject.toml",
            "uv.lock",
            "AGENTS.md",
            "docs/PROJECT.md",
            "docs/ARCHITECTURE.md",
        )
        if (root / name).is_file()
    )
    digest = hashlib.sha256()
    for path in sorted(set(files)):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main() -> int:
    """Emit an inventory and fail for structurally unqualified contributions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    inventory = scan_packages(args.root)
    unowned = unowned_files(args.root, inventory)
    print(
        json.dumps(
            {**inventory.model_dump(mode="json"), "unowned_files": unowned}, indent=2
        )
    )
    return int(bool(inventory.issues or unowned))


if __name__ == "__main__":
    raise SystemExit(main())

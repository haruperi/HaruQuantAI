"""Nonexecuting package ownership and attachment validation.

Metadata never authorizes execution or deletion. Consumers must use the validated
snapshot, recheck its fingerprint before mutation, and retain protected data.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Literal, Self

from pydantic import Field, model_validator

from app.host.contracts import Document
from app.host.logging import get_logger

logger = get_logger(__name__)

MAX_MANIFEST_BYTES = 262144
MAX_PACKAGES = 4096
IDENTITY = r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$"
VERSION = r"^\d+\.\d+\.\d+$"
PACKAGE_ROOTS = (
    "app/workspace",
    "app/plugin",
    "app/plugins",
    "app/ui/app/workspace",
    "app/ui/app/plugins",
)
OWNED_ROOTS = (
    *PACKAGE_ROOTS,
    "tests/workspace",
    "tests/plugin",
    "tests/plugins",
    "tests/examples",
    "app/ui/tests/unit/workspace",
    "app/ui/tests/unit/plugins",
    "app/ui/tests/e2e",
)


class Attachment(Document):
    """One exact version of one owner's extension slot."""

    slot_id: str = Field(pattern=IDENTITY)
    contract_version: str = Field(pattern=VERSION)


class OwnedPaths(Document):
    """Exact exclusively owned files; no glob or data-root authority."""

    source: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    metadata: tuple[str, ...] = ()

    def files(self) -> tuple[str, ...]:
        """Return all declared files, retaining duplicates for validation."""
        return self.source + self.tests + self.assets + self.examples + self.metadata


class Package(Document):
    """Immutable packaging identity, exclusive ownership and entry locations."""

    schema_version: Literal[1]
    id: str = Field(pattern=IDENTITY)
    kind: Literal["workspace", "plugin"]
    version: str = Field(pattern=VERSION)
    host_contract: Literal["1.0.0"]
    mode: Literal["ui_only", "headless", "paired"]
    owner_workspace_id: str | None = Field(default=None, pattern=IDENTITY)
    attachment: Attachment | None = None
    backend_entry: str | None = None
    ui_entry: str | None = None
    owned_paths: OwnedPaths

    @model_validator(mode="after")
    def coherent(self) -> Self:
        """Reject contradictory modes, attachment, or duplicate owned paths."""
        if self.kind == "plugin":
            if self.owner_workspace_id is None or self.attachment is None:
                raise ValueError("Plugin requires one owner and attachment")
        elif self.owner_workspace_id is not None or self.attachment is not None:
            raise ValueError("Workspace cannot attach to another workspace")
        present = (self.backend_entry is not None, self.ui_entry is not None)
        expected = {"ui_only": (False, True), "headless": (True, False)}
        if present != expected.get(self.mode, (True, True)):
            raise ValueError("Counterpart mode mismatch")
        files = self.owned_paths.files()
        if len(files) != len(set(files)):
            raise ValueError("Duplicate owned path")
        for entry in (self.backend_entry, self.ui_entry):
            if entry is not None and entry not in self.owned_paths.source:
                raise ValueError("Entrypoint must be an owned source file")
        return self


class PackageIssue(Document):
    """Safe attributed validation failure; contains no source or exception text."""

    package_id: str
    code: str
    path: str = ""


class PackageInventory(Document):
    """Validated accepted packages and isolated failures at one source fingerprint."""

    packages: tuple[Package, ...]
    issues: tuple[PackageIssue, ...]
    fingerprint: str


def confined_file(root: Path, relative: str, *, exists: bool = True) -> Path:
    """Validate one normal relative package file without following links.

    Args:
        root: Explicit installation boundary.
        relative: POSIX relative path under a permitted package/test root.
        exists: Require an existing regular file when true.

    Returns:
        Absolute lexical path confined to root.

    Raises:
        ValueError: Invalid, protected, missing, linked, or escaped path.
    """
    parts = PurePosixPath(relative).parts
    if (
        not parts
        or PurePosixPath(relative).as_posix() != relative
        or any(part in {".", ".."} for part in relative.split("/"))
        or re.search(r"[\\:*?]", relative)
        or not any(relative.startswith(prefix + "/") for prefix in OWNED_ROOTS)
    ):
        raise ValueError("Invalid or protected package path")
    boundary = root.resolve()
    path = boundary.joinpath(*parts)
    if not path.resolve().is_relative_to(boundary):
        raise ValueError("Escaped package path")
    for item in (path, *path.parents):
        if item == boundary:
            break
        if item.is_symlink() or item.is_junction():
            raise ValueError("Linked package path")
    if exists and not path.is_file():
        raise ValueError("Incomplete package")
    return path


def _read_package(root: Path, path: Path) -> Package:
    """Read one bounded nonexecuting declaration and verify its owned files."""
    relative = path.relative_to(root).as_posix()
    confined_file(root, relative)
    with path.open("rb") as stream:
        data = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(data) > MAX_MANIFEST_BYTES:
        raise ValueError("Package manifest too large")
    package = Package.model_validate_json(data)
    if relative not in package.owned_paths.metadata:
        raise ValueError("Manifest must own itself")
    for name in package.owned_paths.files():
        confined_file(root, name)
    return package


def _relationships(packages: list[Package]) -> list[PackageIssue]:
    """Check exclusive file/identity ownership and workspace presence."""
    issues: list[PackageIssue] = []
    ids = Counter(package.id for package in packages)
    files = Counter(
        name.casefold() for package in packages for name in package.owned_paths.files()
    )
    owners = {p.id for p in packages if p.kind == "workspace" and ids[p.id] == 1}
    for package in packages:
        if ids[package.id] != 1:
            issues.append(
                PackageIssue(package_id=package.id, code="ambiguous_identity")
            )
        if any(files[p.casefold()] != 1 for p in package.owned_paths.files()):
            issues.append(PackageIssue(package_id=package.id, code="overlapping_paths"))
        if package.kind == "plugin" and package.owner_workspace_id not in owners:
            issues.append(PackageIssue(package_id=package.id, code="missing_owner"))
    return issues


def scan_packages(root: Path) -> PackageInventory:
    """Discover and isolate malformed ownership documents without importing code.

    Args:
        root: Explicit installation root; only declared contribution roots are read.

    Returns:
        Immutable accepted packages and bounded attributed issues.
    """
    root = root.resolve()
    packages: list[Package] = []
    issues: list[PackageIssue] = []
    for prefix in PACKAGE_ROOTS:
        directory = root / prefix
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("package.json", recurse_symlinks=False)):
            if len(packages) + len(issues) >= MAX_PACKAGES:
                issues.append(PackageIssue(package_id="", code="package_limit"))
                break
            try:
                packages.append(_read_package(root, path))
            except OSError, ValueError:
                issues.append(
                    PackageIssue(
                        package_id="",
                        code="invalid_package",
                        path=path.relative_to(root).as_posix(),
                    )
                )
    issues.extend(_relationships(packages))
    rejected = {issue.package_id for issue in issues}
    accepted = [p for p in packages if p.id not in rejected]
    available_owners = {p.id for p in accepted if p.kind == "workspace"}
    for package in tuple(accepted):
        if (
            package.kind == "plugin"
            and package.owner_workspace_id not in available_owners
        ):
            issues.append(PackageIssue(package_id=package.id, code="missing_owner"))
            accepted.remove(package)
    digest = hashlib.sha256()
    for package in sorted(accepted, key=lambda p: p.id):
        digest.update(package.model_dump_json().encode())
        for name in sorted(package.owned_paths.files()):
            digest.update(name.encode())
            digest.update(hashlib.sha256((root / name).read_bytes()).digest())
    digest.update(json.dumps([i.model_dump() for i in issues], sort_keys=True).encode())
    logger.debug(
        "Scanned packages in %s: %d accepted, %d issue(s)",
        root,
        len(accepted),
        len(issues),
    )
    return PackageInventory(
        packages=tuple(accepted), issues=tuple(issues), fingerprint=digest.hexdigest()
    )

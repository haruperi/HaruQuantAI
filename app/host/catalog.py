"""Inspect contribution descriptors without executing discovered code.

Discovery accepts JSON manifests and one literal PLUGIN assignment per Python
file. It records content fingerprints and isolates malformed contributions.
Descriptors remain metadata-only and unavailable: validation neither imports a
provider nor resolves its capabilities or mounts routes. Bootstrap owns when
roots are inspected and exposes the resulting snapshot to clients.
"""

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from app.host.contracts import PluginDescriptor
from app.host.logging import get_logger

logger = get_logger(__name__)
MAX_SOURCE_BYTES = 262144
MAX_ENTRIES = 4096


def safe_files(root: Path, pattern: str) -> list[Path]:
    """Enumerate sorted files confined to an explicitly supplied root.

    Containment checks do not provide isolation against concurrent filesystem changes.

    Args:
        root: Discovery directory; absent or non-directory roots produce an empty list.
        pattern: Path.rglob pattern applied without recursing through directory
            symlinks.

    Returns:
        Sorted matching files whose resolved targets remain inside root.

    Raises:
        ValueError: More than MAX_ENTRIES accepted files were encountered.
        OSError: Filesystem enumeration or resolution failed.
    """
    if not root.is_dir():
        return []
    found: list[Path] = []
    for path in root.rglob(pattern, recurse_symlinks=False):
        if path.is_file() and path.resolve().is_relative_to(root.resolve()):
            found.append(path)
        if len(found) > MAX_ENTRIES:
            raise ValueError("Discovery file limit exceeded")
    return sorted(found)


def read_descriptor(path: Path) -> tuple[PluginDescriptor, str]:
    """Read and validate one bounded contribution declaration.

    Only AST literal evaluation is used; imports, functions, and registration code
    from the source are never executed.

    Args:
        path: JSON manifest or UTF-8 Python source with a single literal PLUGIN
            assignment.

    Returns:
        Validated PluginDescriptor and SHA-256 digest of the original bytes.

    Raises:
        OSError: The source cannot be read.
        ValueError: Content exceeds MAX_SOURCE_BYTES or cannot be parsed/validated.
        SyntaxError: Python source is syntactically invalid.
        TypeError: The literal declaration has an unsupported shape.
    """
    with path.open("rb") as stream:
        content = stream.read(MAX_SOURCE_BYTES + 1)
    if len(content) > MAX_SOURCE_BYTES:
        raise ValueError("Descriptor exceeds size limit")
    if path.suffix == ".json":
        raw = json.loads(content)
    else:
        tree = ast.parse(content.decode("utf-8"))
        values = [
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "PLUGIN" for t in node.targets)
        ]
        if len(values) != 1:
            raise ValueError("Expected one literal PLUGIN descriptor")
        raw = ast.literal_eval(values[0])
    descriptor = PluginDescriptor.model_validate(raw)
    return descriptor, hashlib.sha256(content).hexdigest()


def scan_catalog(roots: tuple[Path, ...]) -> dict[str, Any]:
    """Build a metadata snapshot from declared contribution roots.

    Unreadable roots and invalid descriptors become bounded issue records. Duplicate
    IDs/routes are marked ambiguous, and declared requirements remain unbound.
    Logs actual descriptor/issue totals without exposing source contents.

    Args:
        roots: Directories searched for Python files and manifest.json; package
            initializers are ignored.

    Returns:
        Mapping with domains entries and issues; every descriptor remains unmounted and
        unavailable.
    """
    entries: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for root in roots:
        try:
            files = safe_files(root, "*.py") + safe_files(root, "manifest.json")
        except OSError, ValueError:
            issues.append({"code": "root_unreadable", "path": root.name})
            continue
        for path in files:
            if path.name == "__init__.py":
                continue
            locator = root.name + "/" + path.relative_to(root).as_posix()
            try:
                descriptor, digest = read_descriptor(path)
                entries.append(
                    {
                        **descriptor.model_dump(mode="json"),
                        "sha256": digest,
                        "locator": locator,
                        "mounted": False,
                        "available": False,
                        "reason": "metadata_only",
                    }
                )
            except OSError, ValueError, SyntaxError, TypeError, RecursionError:
                issues.append({"code": "invalid_descriptor", "path": locator})
                logger.warning("I06 Invalid contribution isolated")
    ids = [entry["id"] for entry in entries]
    routes = [entry["route_base"] for entry in entries if entry["route_base"]]
    for entry in entries:
        if ids.count(entry["id"]) > 1 or (
            entry["route_base"] and routes.count(entry["route_base"]) > 1
        ):
            entry["reason"] = "ambiguous_descriptor"
            issues.append({"code": "duplicate", "path": entry["locator"]})
        if entry["requires"]:
            entry["reason"] = "unbound_capabilities"
    logger.info(
        "I06 Catalog inspected: %s descriptors, %s issues", len(entries), len(issues)
    )
    return {"domains": entries, "issues": issues}

"""Non-Executing Static Descriptor and Preset Discovery.

Description:
    This module provides static parsing and non-executing inspection of plugin
    descriptors, package manifests, and configuration presets. It exists to guarantee
    that metadata, capabilities, and parameters can be discovered, indexed, and
    fingerprinted without executing untrusted third-party or quantitative code.
    Externally, it participates in three key workflows: (1) `BootstrapCoordinator`
    calls `scan_presets()` during `_services()` to inventory stored workspace
    configuration documents; (2) The package composition engine (`app.host.packages`)
    invokes `read_descriptor()` to validate plugin contracts and host capability
    requirements before any module import is permitted; and (3) Verification
    utilities and CI checks inspect file containment and manifest consistency using
    `safe_files()`. Internally, `safe_files()` guards against path traversal and
    symlink escapes; `read_descriptor()` uses Python's AST parser or JSON decoders
    to extract literal declarations (`PLUGIN = {...}`); and `scan_presets()` scans
    directory trees while isolating malformed documents.

Purpose:
    FEAT-HOST-DISCOVERY: Static AST & JSON Manifest and Preset Discovery.
    Provides non-executing contribution descriptor parsing, path-confined
    directory scanning, and fault-tolerant preset indexing without code execution.

Key Capabilities:
    - FR-HOST-DISCOVERY-PATH-CONFINEMENT: Bounded Confined File Enumeration
      Associated: `safe_files()`
      Logging: Emits debug log on file enumeration with matched file counts
      and pattern filters.
    - FR-HOST-DISCOVERY-STATIC-DESCRIPTOR: AST/JSON Static Descriptor Parsing
      Associated: `read_descriptor()`
      Logging: Emits debug log with descriptor ID and version upon successful
      static parsing.
    - FR-HOST-DISCOVERY-PRESET-INDEXING: Fault-Tolerant Preset Indexing
      Associated: `scan_presets()`
      Logging: Emits info log summarizing inspected preset counts and warning
      log when malformed presets are isolated.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.discovery import read_descriptor, scan_presets

    # 1. Statically parse a plugin descriptor without importing code
    descriptor, sha256 = read_descriptor(Path("app/plugin/DataSource/dukascopy.py"))

    # 2. Inspect workspace configuration presets safely
    presets = scan_presets(Path("data/presets"))
    entries, issues = presets["entries"], presets["issues"]
    ```

CLI Usage:
    Descriptor discovery and inventory validation are executed via testing
    and inventory scripts:
    ```bash
    # Test static AST discovery and isolation invariants
    uv run pytest tests/host/test_discovery.py

    # Verify all package manifests statically
    uv run python scripts/package_inventory.py
    ```
"""

from __future__ import annotations

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
    logger.info(
        "Safe file scan in %s: %d file(s) matched pattern %s",
        root,
        len(found),
        pattern,
    )
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
    logger.info("Descriptor parsed: %s (version=%s)", descriptor.id, descriptor.version)
    return descriptor, hashlib.sha256(content).hexdigest()


def scan_presets(root: Path) -> dict[str, Any]:
    """Inspect JSON presets and retain per-document validation issues.

    Individual read, decoding, size, and object-shape failures are isolated. The
    logged count describes accepted documents, not owner-validated or applied presets.

    Args:
        root: Explicit preset directory; a missing directory has zero entries.

    Returns:
        entries with relative paths/fingerprints/status, plus issues for rejected
        documents.

    Raises:
        OSError: Root enumeration fails before document-level handling.
        ValueError: Enumeration exceeds the discovery file limit.
    """
    entries: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    for path in safe_files(root, "*.json"):
        locator = path.relative_to(root).as_posix()
        try:
            with path.open("rb") as stream:
                content = stream.read(MAX_SOURCE_BYTES + 1)
            if len(content) > MAX_SOURCE_BYTES:
                raise ValueError("Preset limit exceeded")  # noqa: TRY301 -- isolate this document.
            raw = json.loads(content)
            if not isinstance(raw, dict):
                raise TypeError("Preset must be an object")  # noqa: TRY301 -- isolate this document.
            entries.append(
                {
                    "path": locator,
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "status": "owner_validation_unavailable",
                }
            )
        except OSError, ValueError, TypeError:
            issues.append({"path": locator, "code": "invalid_preset"})
            logger.warning("Invalid preset isolated")
    logger.info("Presets inspected: %s documents", len(entries))
    return {"entries": entries, "issues": issues}

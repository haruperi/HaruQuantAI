"""Inventory preset documents for host initialization.

The scan verifies bounded JSON-object structure and records fingerprints, not
quantitative meaning. Each accepted entry explicitly lacks owner validation.
Bootstrap supplies the preset directory; no scan runs at import time and no
preset is applied to runtime state by this module.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.host.catalog import MAX_SOURCE_BYTES, safe_files
from app.host.logging import get_logger

logger = get_logger(__name__)


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

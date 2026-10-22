"""Secret redaction and machine-path normalization for host telemetry."""

from __future__ import annotations

import contextlib
import hashlib
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REDACTION_FR = "FR-HOST-LOGGING-REDACTION"
REDACTED_STR = "***REDACTED***"
SENSITIVE_KEY_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(?:^|[_-])(?:password|passwd|token|secret|key|api_?key|"
    r"auth|authorization|credential|hash|bearer)(?:$|[_-])"
)
SENSITIVE_VALUE_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(bearer\s+[^\s,'\";]+)|"
    r"((?:token|secret|password|api_?key|key)['\"]?\s*[:=]\s*"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s,;}\]]+))"
)


def normalize_path(path_str: str, root_dir: Path | None = None) -> str:
    """Normalize absolute paths to relative tokens to prevent environment leaks.

    Args:
        path_str: Path string to normalize.
        root_dir: Optional root directory to normalize against (defaults to cwd).

    Returns:
        Path string with repository or home directory prefixes masked.
    """
    normalized = path_str.replace("\\", "/")
    roots = [(str((root_dir or Path.cwd()).resolve()), "[WORKSPACE]")]
    with contextlib.suppress(RuntimeError):
        roots.append((str(Path.home().resolve()), "~"))
    for root_prefix, replacement in roots:
        prefix = root_prefix.replace("\\", "/").rstrip("/")
        flags = re.IGNORECASE if sys.platform == "win32" else 0
        normalized = re.sub(
            r"(?<![\w/])" + re.escape(prefix) + r"(?=$|[/\s\"'\),;\]])",
            replacement,
            normalized,
            flags=flags,
        )
    return normalized


def fingerprint_secret(value: Any) -> str:
    """Compute a non-reversible SHA-256 redaction fingerprint for a secret value."""
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:8]
    return f"***REDACTED:sha256:{digest}***"


def redact_value(value: Any, *, fingerprint: bool = False) -> Any:
    """Recursively mask sensitive patterns in strings, sequences, or nested mappings.

    Args:
        value: Arbitrary value to scrub.
        fingerprint: When True, emit SHA-256 fingerprint token
            ``***REDACTED:sha256:<8-hex>***`` instead of ``***REDACTED***``.

    Returns:
        Scrubbed value with sensitive tokens masked.
    """
    if isinstance(value, str):
        if fingerprint:
            return SENSITIVE_VALUE_PATTERN.sub(
                lambda m: fingerprint_secret(m.group(0)), value
            )
        return SENSITIVE_VALUE_PATTERN.sub(REDACTED_STR, value)
    if isinstance(value, Mapping):
        return redact_mapping(value, fingerprint=fingerprint)
    if isinstance(value, list):
        return [redact_value(item, fingerprint=fingerprint) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item, fingerprint=fingerprint) for item in value)
    return value


def redact_mapping(
    mapping: Mapping[Any, Any],
    *,
    fingerprint: bool = False,
) -> dict[str, Any]:
    """Recursively mask sensitive keys and nested values in a mapping.

    Args:
        mapping: Mapping to scrub.
        fingerprint: When True, emit SHA-256 fingerprint token for sensitive keys.

    Returns:
        New dictionary with sensitive keys and values scrubbed.
    """
    scrubbed_dict: dict[str, Any] = {}
    for k, v in mapping.items():
        key_str = str(k)
        if SENSITIVE_KEY_PATTERN.search(key_str):
            scrubbed_dict[key_str] = (
                fingerprint_secret(v) if fingerprint else REDACTED_STR
            )
        else:
            scrubbed_dict[key_str] = redact_value(v, fingerprint=fingerprint)
    return scrubbed_dict


def _boundary_diagnostic() -> None:
    """Report failure without recursive logging or sensitive payloads."""
    with contextlib.suppress(Exception):
        sys.stderr.write("[LOGGING-ERROR-BOUNDARY] telemetry record dropped\n")



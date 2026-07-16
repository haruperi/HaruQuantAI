"""Expose deterministic JSON-safe conversion and canonical serialization.

Serialization never performs implicit redaction; producers sanitize sensitive
values before calling this feature package.
"""

from app.utils.serialization.canonical import canonical_json, to_json_safe

__all__ = ("canonical_json", "to_json_safe")

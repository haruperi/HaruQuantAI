"""Canonical, deterministic report hash creation for Analytics.

All functions are stateless pure functions.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from enum import StrEnum
from typing import Any


class HashPolicy(StrEnum):
    """Policies for computing report verification hashes."""

    SHA256 = "sha256"
    MD5 = "md5"


def _decimal_default(obj: object) -> float:
    if isinstance(obj, Decimal):
        return float(obj)
    msg = f"Object of type {type(obj)} is not JSON serializable"
    raise TypeError(msg)


def compute_report_hash(
    report: dict[str, Any] | object,
    policy: HashPolicy | None = None,
) -> str:
    """Compute deterministic hash of report sections, excluding metadata."""
    rep_dict: dict[str, Any] = {}
    if report is not None:
        if isinstance(report, dict):
            rep_dict = dict(report)
        elif hasattr(report, "sections"):
            rep_dict = {
                "report_id": getattr(report, "report_id", ""),
                "report_status": getattr(report, "report_status", ""),
                "sections": getattr(report, "sections", {}),
                "warnings": getattr(report, "warnings", []),
                "quality_flags": getattr(report, "quality_flags", []),
            }

    # Exclude metadata and non-deterministic fields from the hash
    rep_dict.pop("metadata", None)
    rep_dict.pop("created_at", None)
    rep_dict.pop("request_id", None)

    serialized = json.dumps(
        rep_dict,
        sort_keys=True,
        default=_decimal_default,
    )

    pol = policy or HashPolicy.SHA256
    hasher = (
        hashlib.md5() if pol == HashPolicy.MD5 else hashlib.sha256()  # noqa: S324
    )
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()

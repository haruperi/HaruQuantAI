"""Deterministic signing helpers for risk artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_hash(value: Any) -> str:
    """Function stable_hash provides risk service behavior."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def sign_payload(value: Any, *, namespace: str = "risk") -> str:
    """Function sign_payload provides risk service behavior."""
    return stable_hash({"namespace": namespace, "payload": value})

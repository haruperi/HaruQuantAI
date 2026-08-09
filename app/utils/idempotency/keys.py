"""Owner-bound deterministic idempotency-key mappings."""

from __future__ import annotations

import re
from collections.abc import Mapping

from app.utils.errors.exceptions import ValidationError
from app.utils.security import redact_mapping_value
from app.utils.serialization import canonical_digest, to_json_safe

_OWNER = re.compile(r"[a-z][a-z0-9_]*:[a-z][a-z0-9_]*\Z")


def derive_idempotency_key(
    *, owner: str, intent: Mapping[str, object]
) -> dict[str, str]:
    """Derive an owner-bound key without embedding intent data.

    Args:
        owner: Domain and store owner scope.
        intent: Economic intent material.

    Returns:
        IdempotencyKey v1 mapping.

    Raises:
        ValidationError: If material is invalid or sensitive.
    """
    if _OWNER.fullmatch(owner) is None or not intent:
        raise ValidationError("IDEMPOTENCY_KEY_INVALID")
    safe = to_json_safe(intent)
    redacted = redact_mapping_value(intent)
    if redacted.redacted_paths:
        raise ValidationError("IDEMPOTENCY_INTENT_SENSITIVE")
    return {
        "contract_version": "v1",
        "schema_id": "utils.idempotency_key.v1",
        "owner": owner,
        "digest": canonical_digest(safe),
    }


def parse_idempotency_key(value: Mapping[str, object]) -> dict[str, str]:
    """Strictly parse an IdempotencyKey v1 mapping.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached key.

    Raises:
        ValidationError: If validation fails.
    """
    expected = {"contract_version", "schema_id", "owner", "digest"}
    if (
        set(value) != expected
        or value.get("contract_version") != "v1"
        or value.get("schema_id") != "utils.idempotency_key.v1"
        or not isinstance(value.get("owner"), str)
        or not isinstance(value.get("digest"), str)
    ):
        raise ValidationError("IDEMPOTENCY_KEY_INVALID")
    owner, digest = str(value["owner"]), str(value["digest"])
    if _OWNER.fullmatch(owner) is None or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValidationError("IDEMPOTENCY_KEY_INVALID")
    return {key: str(value[key]) for key in expected}


def get_key_owner(value: Mapping[str, object]) -> str:
    """Return the validated owner scope from a key.

    Args:
        value: IdempotencyKey mapping.

    Returns:
        Owner scope.
    """
    return parse_idempotency_key(value)["owner"]

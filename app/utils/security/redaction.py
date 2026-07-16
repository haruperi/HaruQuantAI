"""Validate the Stage 2 redaction policy used by structured logging.

Only ``RedactionPolicy`` is public in Phase 1. Text and mapping redaction
helpers remain private until the complete diagnostic API is delivered.
"""

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from app.utils.errors.exceptions import SecurityError, ValidationError

_DEFAULT_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "authorization",
        "credential",
        "private_key",
        "access_key",
        "client_secret",
    }
)
_PROTECTED_KEYS = frozenset(
    {"password", "passwd", "privatekey", "clientsecret", "apikey", "authorization"}
)


def _normalize_key(value: str) -> str:
    """Normalize a field name for case-insensitive policy matching.

    Args:
        value: Source field name or configured sensitive key.

    Returns:
        A case-folded key without hyphens or underscores.
    """
    return value.casefold().replace("-", "").replace("_", "")


@dataclass(frozen=True, slots=True)
class RedactionPolicy:
    """Represent the immutable redaction policy required by logging.

    Attributes:
        sensitive_keys: Normalized denylist matched case-insensitively.
        allowlisted_paths: Exact dot paths allowed to bypass ordinary
            sensitive-key matching; protected credential fields remain barred.
        replacement: Fixed text substituted for removed secret values.
        max_text_length: Maximum safe text length after redaction.
        max_depth: Maximum nested mapping or sequence depth.
        max_items: Maximum aggregate mapping and sequence items.
    """

    sensitive_keys: frozenset[str] = field(
        default_factory=lambda: _DEFAULT_SENSITIVE_KEYS
    )
    allowlisted_paths: frozenset[str] = field(default_factory=frozenset)
    replacement: str = "[REDACTED]"
    max_text_length: int = 4_096
    max_depth: int = 16
    max_items: int = 1_000

    def __post_init__(self) -> None:
        """Normalize the denylist and reject an unsafe policy.

        Raises:
            ValidationError: Required values or configured bounds are invalid.
            SecurityError: An allowlisted path ends in a protected credential
                field.
        """
        if not self.sensitive_keys or not self.replacement.strip():
            raise ValidationError("REDACTION_POLICY_INVALID")
        if min(self.max_text_length, self.max_depth, self.max_items) < 1:
            raise ValidationError("REDACTION_POLICY_INVALID")
        normalized_keys = frozenset(_normalize_key(key) for key in self.sensitive_keys)
        if "" in normalized_keys:
            raise ValidationError("REDACTION_POLICY_INVALID")
        for path in self.allowlisted_paths:
            parts = path.split(".")
            if not path or path != path.strip() or any(not part for part in parts):
                raise ValidationError("REDACTION_POLICY_INVALID")
            if _normalize_key(parts[-1]) in _PROTECTED_KEYS:
                raise SecurityError("REDACTION_PROTECTED_ALLOWLIST")
        object.__setattr__(self, "sensitive_keys", normalized_keys)


def _redact_text(value: str, policy: RedactionPolicy) -> str:
    """Redact recognized secret assignments before bounded truncation.

    Args:
        value: Source message or text value.
        policy: Validated immutable redaction policy.

    Returns:
        Redacted text no longer than ``policy.max_text_length``.
    """
    keys = sorted(policy.sensitive_keys, key=len, reverse=True)
    alternation = "|".join(re.escape(key) for key in keys)
    pattern = re.compile(
        rf"(?i)(\b(?:{alternation})\b\s*[:=]\s*)([^\s,;]+)|"
        r"(\bBearer\s+)([^\s,;]+)"
    )

    def replace(match: re.Match[str]) -> str:
        """Build a fixed replacement while preserving the matched label.

        Args:
            match: Regular-expression match containing a secret label/value.

        Returns:
            The original label followed by the policy replacement marker.
        """
        return f"{match.group(1) or match.group(3) or ''}{policy.replacement}"

    return pattern.sub(replace, value)[: policy.max_text_length]


def _redact_mapping(  # noqa: C901
    value: Mapping[str, object],
    policy: RedactionPolicy,
) -> dict[str, object]:
    """Return a bounded deep-redacted copy of structured context.

    Args:
        value: Source structured context mapping.
        policy: Validated immutable redaction policy.

    Returns:
        A newly allocated mapping containing only safe supported values.

    Raises:
        ValidationError: A value is unsupported or non-finite, a key is
            invalid, or a depth/item bound is exceeded.
    """
    item_count = [0]

    def redact(  # noqa: C901, PLR0912
        nested: object,
        *,
        path: str,
        depth: int,
    ) -> object:
        """Redact one value while tracking its path and traversal depth.

        Args:
            nested: Current scalar or container value.
            path: Exact dot path to the current value.
            depth: Current traversal depth, starting at zero.

        Returns:
            A safe scalar or newly allocated container.

        Raises:
            ValidationError: The value is invalid or exceeds policy bounds.
        """
        if depth > policy.max_depth:
            raise ValidationError("REDACTION_DEPTH_EXCEEDED")
        if nested is None or isinstance(nested, bool | int):
            return nested
        if isinstance(nested, float):
            if not math.isfinite(nested):
                raise ValidationError("REDACTION_VALUE_INVALID")
            return nested
        if isinstance(nested, str):
            return _redact_text(nested, policy)
        if isinstance(nested, Mapping):
            item_count[0] += len(nested)
            if item_count[0] > policy.max_items:
                raise ValidationError("REDACTION_ITEMS_EXCEEDED")
            output: dict[str, object] = {}
            for key, child in nested.items():
                if not isinstance(key, str) or not key:
                    raise ValidationError("REDACTION_MAPPING_INVALID")
                child_path = f"{path}.{key}" if path else key
                normalized = _normalize_key(key)
                sensitive = any(
                    normalized == candidate or normalized.endswith(candidate)
                    for candidate in policy.sensitive_keys
                )
                if sensitive and child_path not in policy.allowlisted_paths:
                    output[key] = policy.replacement
                else:
                    output[key] = redact(child, path=child_path, depth=depth + 1)
            return output
        if isinstance(nested, list | tuple):
            item_count[0] += len(nested)
            if item_count[0] > policy.max_items:
                raise ValidationError("REDACTION_ITEMS_EXCEEDED")
            return [
                redact(child, path=f"{path}.{index}", depth=depth + 1)
                for index, child in enumerate(nested)
            ]
        raise ValidationError("REDACTION_VALUE_INVALID")

    return redact(value, path="", depth=0)  # type: ignore[return-value]

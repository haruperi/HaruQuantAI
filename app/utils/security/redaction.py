"""Denylist-first secret redaction for text and JSON-safe mappings."""

from __future__ import annotations

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
    {
        "password",
        "passwd",
        "privatekey",
        "clientsecret",
        "apikey",
        "authorization",
    }
)


def _normalize_key(value: str) -> str:
    """Normalize a key case-insensitively, removing hyphens and underscores.

    Args:
        value: String key to normalize.

    Returns:
        The normalized canonical key.
    """
    return value.casefold().replace("-", "").replace("_", "")


@dataclass(frozen=True, slots=True)
class RedactionPolicy:
    """Immutable denylist-first redaction policy.

    Attributes:
        sensitive_keys: A frozen set of lowercase key names to redact.
        allowlisted_paths: A frozen set of JSON paths exempt from redaction.
        replacement: String substitution value.
        max_text_length: Bounded maximum size in characters for text nodes.
        max_depth: Bounded maximum nesting depth for maps/sequences.
        max_items: Bounded maximum total item count allowed.
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
        """Validate and normalize the policy definition.

        Raises:
            ValidationError: If key, path, replacement format, or numeric limit
                bounds are violated.
            SecurityError: If trying to allowlist protected credential keys.
        """
        if not self.sensitive_keys:
            raise ValidationError("REDACTION_POLICY_INVALID")
        normalized_keys: set[str] = set()
        for key in self.sensitive_keys:
            if not key or key != key.strip():
                raise ValidationError("REDACTION_POLICY_INVALID")
            normalized_keys.add(_normalize_key(key))
        if not self.replacement or self.replacement != self.replacement.strip():
            raise ValidationError("REDACTION_POLICY_INVALID")
        if self.max_text_length < 1 or self.max_depth < 1 or self.max_items < 1:
            raise ValidationError("REDACTION_POLICY_INVALID")
        normalized_paths: set[str] = set()
        for path in self.allowlisted_paths:
            parts = path.split(".")
            if not path or path != path.strip() or any(not part for part in parts):
                raise ValidationError("REDACTION_POLICY_INVALID")
            if _normalize_key(parts[-1]) in _PROTECTED_KEYS:
                raise SecurityError("REDACTION_PROTECTED_ALLOWLIST")
            normalized_paths.add(path)
        object.__setattr__(self, "sensitive_keys", frozenset(normalized_keys))
        object.__setattr__(self, "allowlisted_paths", frozenset(normalized_paths))


@dataclass(frozen=True, slots=True)
class RedactionResult:
    """Redacted value plus secret-free diagnostics.

    Attributes:
        value: The newly constructed redacted and bounded JSON-safe object.
        redacted_paths: Lexicographically sorted list of redacted paths.
        truncated_paths: Lexicographically sorted list of truncated node paths.
    """

    value: object
    redacted_paths: tuple[str, ...]
    truncated_paths: tuple[str, ...]

    @property
    def truncated(self) -> bool:
        """Return whether any value was truncated.

        Returns:
            True if any values or strings were truncated.
        """
        return bool(self.truncated_paths)


def is_sensitive_key(key: str, policy: RedactionPolicy | None = None) -> bool:
    """Return whether a key is sensitive under a policy.

    Args:
        key: Candidate mapping key.
        policy: Optional redaction policy.

    Returns:
        Whether the key is sensitive, case-insensitively.
    """
    active_policy = policy or RedactionPolicy()
    normalized = _normalize_key(key)
    return any(
        normalized == item or normalized.endswith(item)
        for item in active_policy.sensitive_keys
    )


def _text_pattern(policy: RedactionPolicy) -> re.Pattern[str]:
    """Compile a regex pattern to scan for sensitive key-value pairs.

    Args:
        policy: Active redaction policy.

    Returns:
        The compiled regex Pattern.
    """
    keys = sorted(policy.sensitive_keys, key=len, reverse=True)
    tolerant_keys = (
        "[_-]*".join(re.escape(character) for character in key) for key in keys
    )
    alternation = "|".join(
        rf"(?<![A-Za-z0-9]){key_pattern}(?![A-Za-z0-9])"
        for key_pattern in tolerant_keys
    )
    return re.compile(
        rf"(?i)((?:{alternation})\s*[:=]\s*)"
        r"((?:(?:Bearer|Basic)\s+)?[^\s,;]+)|"
        r"(\bBearer\s+)([^\s,;]+)"
    )


def redact_text_value(
    value: str,
    policy: RedactionPolicy | None = None,
) -> RedactionResult:
    """Redact and bound text without mutating the source.

    Args:
        value: Source text.
        policy: Optional redaction policy.

    Returns:
        Redacted text and secret-free diagnostics.
    """
    active_policy = policy or RedactionPolicy()
    pattern = _text_pattern(active_policy)
    redacted = False

    def replace(match: re.Match[str]) -> str:
        """Substitute matched sensitive value with redaction replacement.

        Args:
            match: The regex match object.

        Returns:
            The replacement string containing the key prefix and replacement value.
        """
        nonlocal redacted
        redacted = True
        prefix = match.group(1) or match.group(3) or ""
        return f"{prefix}{active_policy.replacement}"

    safe_value = pattern.sub(replace, value)
    truncated_paths: tuple[str, ...] = ()
    if len(safe_value) > active_policy.max_text_length:
        safe_value = safe_value[: active_policy.max_text_length]
        truncated_paths = ("$text",)
    redacted_paths = ("$text",) if redacted else ()
    return RedactionResult(safe_value, redacted_paths, truncated_paths)


def _redact_value(  # noqa: C901, PLR0912 - bounded recursive type dispatch.
    value: object,
    *,
    policy: RedactionPolicy,
    path: str,
    depth: int,
    item_count: list[int],
    redacted_paths: list[str],
    truncated_paths: list[str],
) -> object:
    """Recursively redact and validate nodes.

    Args:
        value: Node value to process.
        policy: Active redaction policy.
        path: Dot-separated JSON path to the current node.
        depth: Current recursion depth.
        item_count: Aggregate item counter list.
        redacted_paths: Output log of redacted paths.
        truncated_paths: Output log of truncated paths.

    Returns:
        The redacted/validated node representation.

    Raises:
        ValidationError: If nesting depth, total item limits, or JSON-safe checks fail.
    """
    if depth > policy.max_depth:
        raise ValidationError("REDACTION_DEPTH_EXCEEDED")
    if value is None or isinstance(value, bool | int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError("REDACTION_VALUE_INVALID")
        return value
    if isinstance(value, str):
        text_result = redact_text_value(value, policy)
        if text_result.redacted_paths:
            redacted_paths.append(path)
        if text_result.truncated_paths:
            truncated_paths.append(path)
        return text_result.value
    if isinstance(value, Mapping):
        item_count[0] += len(value)
        if item_count[0] > policy.max_items:
            raise ValidationError("REDACTION_ITEMS_EXCEEDED")
        safe_mapping: dict[str, object] = {}
        for key, nested in value.items():
            if not isinstance(key, str) or not key:
                raise ValidationError("REDACTION_MAPPING_INVALID")
            nested_path = f"{path}.{key}" if path else key
            if is_sensitive_key(key, policy) and (
                nested_path not in policy.allowlisted_paths
            ):
                safe_mapping[key] = policy.replacement
                redacted_paths.append(nested_path)
                continue
            safe_mapping[key] = _redact_value(
                nested,
                policy=policy,
                path=nested_path,
                depth=depth + 1,
                item_count=item_count,
                redacted_paths=redacted_paths,
                truncated_paths=truncated_paths,
            )
        return safe_mapping
    if isinstance(value, list | tuple):
        item_count[0] += len(value)
        if item_count[0] > policy.max_items:
            raise ValidationError("REDACTION_ITEMS_EXCEEDED")
        return [
            _redact_value(
                item,
                policy=policy,
                path=f"{path}.{index}" if path else str(index),
                depth=depth + 1,
                item_count=item_count,
                redacted_paths=redacted_paths,
                truncated_paths=truncated_paths,
            )
            for index, item in enumerate(value)
        ]
    raise ValidationError("REDACTION_VALUE_INVALID")


def redact_mapping_value(
    value: Mapping[str, object],
    policy: RedactionPolicy | None = None,
) -> RedactionResult:
    """Recursively redact a JSON-safe mapping without mutating it.

    Args:
        value: Source JSON-safe mapping.
        policy: Optional redaction policy.

    Returns:
        Redacted mapping and secret-free diagnostics.

    Raises:
        ValidationError: If the mapping is not JSON-safe or exceeds bounds.
    """
    active_policy = policy or RedactionPolicy()
    redacted_paths: list[str] = []
    truncated_paths: list[str] = []
    safe_value = _redact_value(
        value,
        policy=active_policy,
        path="",
        depth=0,
        item_count=[0],
        redacted_paths=redacted_paths,
        truncated_paths=truncated_paths,
    )
    if not isinstance(safe_value, dict):
        raise ValidationError("REDACTION_MAPPING_INVALID")
    return RedactionResult(
        safe_value,
        tuple(sorted(set(redacted_paths))),
        tuple(sorted(set(truncated_paths))),
    )

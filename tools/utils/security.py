"""Security helpers for HaruQuant secret redaction and secret metadata.

Provides HaruQuant secret redaction, security metadata helpers, and internal
crypto/password utilities.

Only safe redaction and secret-reference metadata functions are intended to be
official AI-callable tools. Crypto, decryption, key generation, password hashing,
and password verification are intentionally kept as deterministic developer
utilities and should not be exposed through the utils tool registry.

Exported AI Tools:
    - is_sensitive_key
    - redact_text
    - redact_mapping
    - select_active_secret_version

Public Utility Helpers:
    - redact_scalar_value
    - generate_encryption_key
    - encrypt_data_value
    - decrypt_data_value
    - hash_password_value
    - verify_password_value
    - secret_ref_to_dict
    - rotation_policy_to_dict

Internal Helpers:
    - _metadata
    - _success_response
    - _error_response
    - _is_sensitive_key_value
    - _redact_text_value
    - _redact_mapping_value

Classes:
    - SecretRef
    - SecretRotationPolicy
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence, cast

from cryptography.fernet import Fernet
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL = "low"
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

REDACTED = "***REDACTED***"
REDACTED_VALUE = REDACTED

SENSITIVE_KEYWORDS = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "auth",
    "authorization",
    "credential",
    "bearer",
    "smtp_password",
    "connection_string",
)

_JSON_PAIR_PATTERN = re.compile(
    (
        r'("(?P<key>[^"]*(?:password|passwd|pwd|token|secret|api[_-]?key|'
        r'access[_-]?key|private[_-]?key|auth|credential)[^"]*)"\s*:\s*")'
        r'(?P<value>[^"]*)(")'
    ),
    re.IGNORECASE,
)
_KV_PATTERN = re.compile(
    (
        r"(?i)\b(?P<key>password|passwd|pwd|token|secret|api[_-]?key|"
        r"access[_-]?key|private[_-]?key|auth|credential|smtp_password)\b"
        r"\s*[:=]\s*(?P<quote>['\"]?)(?P<value>[^\s,;'\"]+)(?P=quote)"
    )
)
_AUTH_HEADER_PATTERN = re.compile(
    (
        r"(?i)\b(?P<header>Authorization|Proxy-Authorization)\s*:\s*"
        r"(?P<scheme>Bearer|Basic)\s+(?P<value>[A-Za-z0-9\-._~+/=]+)"
    )
)
_X_API_KEY_PATTERN = re.compile(
    r"(?i)\b(?P<header>x-api-key|api-key)\s*:\s*(?P<value>[A-Za-z0-9\-._~+/=]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)\b(Bearer)\s+([A-Za-z0-9\-._~+/=]+)")
_AWS_ACCESS_KEY_PATTERN = re.compile(r"\bAKIA[0-9A-Z]{16}\b")

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class SecretRef:
    """
    Versioned secret reference without exposing secret material.

    Args:
        secret_id (str): Unique identifier for the secret.
        version (str): Version identifier.
        created_at (datetime): Creation timestamp.
        active (bool): Whether the version is active.
    """

    secret_id: str
    version: str
    created_at: datetime
    active: bool = True


@dataclass(frozen=True)
class SecretRotationPolicy:
    """
    Secret rotation policy metadata.

    Args:
        secret_id (str): Identifier for the secret this policy applies to.
        max_age_days (int): Maximum age before rotation is required.
        overlap_versions (int): Number of active versions allowed during rotation.
    """

    secret_id: str
    max_age_days: int
    overlap_versions: int = 2


def _metadata(
    tool_name: str, request_id: str | None, execution_ms: float
) -> dict[str, Any]:
    """Build standard AI-tool metadata."""
    return {
        "tool_name": tool_name,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL,
        "request_id": request_id,
        "execution_ms": execution_ms,
        "read_only": READ_ONLY,
        "writes_file": WRITES_FILE,
        "modifies_database": MODIFIES_DATABASE,
        "places_trade": PLACES_TRADE,
        "requires_network": REQUIRES_NETWORK,
    }


def _success_response(
    *,
    tool_name: str,
    message: str,
    data: Any,
    request_id: str | None,
    started_at: float,
) -> dict[str, Any]:
    """Build a standard successful AI-tool response."""
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": "success",
        "message": message,
        "data": data,
        "error": None,
        "metadata": _metadata(tool_name, request_id, execution_ms),
    }


def _error_response(
    *,
    tool_name: str,
    message: str,
    code: str,
    details: str,
    request_id: str | None,
    started_at: float,
) -> dict[str, Any]:
    """Build a standard error AI-tool response."""
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": "error",
        "message": message,
        "data": None,
        "error": {"code": code, "details": details},
        "metadata": _metadata(tool_name, request_id, execution_ms),
    }


def secret_ref_to_dict(ref: SecretRef) -> dict[str, Any]:
    """
    Convert a SecretRef to a JSON-safe dictionary.

    Args:
        ref (SecretRef): Secret reference to serialize.

    Returns:
        dict[str, Any]: JSON-safe metadata.
    """
    if not isinstance(ref, SecretRef):
        raise TypeError("ref must be a SecretRef.")

    created_at = ref.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return {
        "secret_id": ref.secret_id,
        "version": ref.version,
        "created_at": created_at.astimezone(timezone.utc).isoformat(),
        "active": ref.active,
    }


def rotation_policy_to_dict(policy: SecretRotationPolicy) -> dict[str, Any]:
    """
    Convert a SecretRotationPolicy to a JSON-safe dictionary.

    Args:
        policy (SecretRotationPolicy): Rotation policy to serialize.

    Returns:
        dict[str, Any]: JSON-safe policy metadata.
    """
    if not isinstance(policy, SecretRotationPolicy):
        raise TypeError("policy must be a SecretRotationPolicy.")

    return {
        "secret_id": policy.secret_id,
        "max_age_days": policy.max_age_days,
        "overlap_versions": policy.overlap_versions,
    }


def _is_sensitive_key_value(key: str) -> bool:
    """Return whether a key name likely represents sensitive data."""
    key_l = str(key).lower()
    return any(token in key_l for token in SENSITIVE_KEYWORDS)


def is_sensitive_key(key: str, request_id: str | None = None) -> dict[str, Any]:
    """
    Check whether a key name likely contains secret material.

    Use this tool before logging or displaying configuration keys.

    Args:
        key (str): Key name to inspect.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with a boolean result.
    """
    tool_name = "is_sensitive_key"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    if not isinstance(key, str) or not key.strip():
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="key must be a non-empty string.",
            request_id=request_id,
            started_at=started_at,
        )

    result = _is_sensitive_key_value(key)
    return _success_response(
        tool_name=tool_name,
        message="Sensitivity check completed.",
        data={"key": key, "sensitive": result},
        request_id=request_id,
        started_at=started_at,
    )


def redact_scalar_value(value: Any) -> Any:
    """
    Redact a known sensitive scalar value.

    Args:
        value (Any): Sensitive value.

    Returns:
        Any: None when the input is None, otherwise the redaction marker.
    """
    if value is None:
        return None
    return REDACTED


def _redact_text_value(text: str) -> str:
    """Redact common secret patterns in free-form text."""
    if not text:
        return text

    result = str(text)
    result = _JSON_PAIR_PATTERN.sub(
        lambda match: f"{match.group(1)}{REDACTED}{match.group(4)}", result
    )
    result = _KV_PATTERN.sub(lambda match: f"{match.group('key')}={REDACTED}", result)
    result = _AUTH_HEADER_PATTERN.sub(
        lambda match: f"{match.group('header')}: {match.group('scheme')} {REDACTED}",
        result,
    )
    result = _X_API_KEY_PATTERN.sub(
        lambda match: f"{match.group('header')}: {REDACTED}", result
    )
    result = _BEARER_PATTERN.sub(rf"\1 {REDACTED}", result)
    result = _AWS_ACCESS_KEY_PATTERN.sub(REDACTED, result)
    return result


def redact_text(text: Any, request_id: str | None = None) -> dict[str, Any]:
    """
    Redact common secret patterns from free-form text.

    Use this tool to sanitize log messages, trace payloads, and user-visible
    diagnostics before exposing them to agents or logs.

    Args:
        text (str): Text to sanitize.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with redacted text.
    """
    tool_name = "redact_text"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    if not isinstance(text, str):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="text must be a string.",
            request_id=request_id,
            started_at=started_at,
        )

    return _success_response(
        tool_name=tool_name,
        message="Text redacted.",
        data={"redacted_text": _redact_text_value(text)},
        request_id=request_id,
        started_at=started_at,
    )


def _redact_mapping_value(data: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively redact sensitive values in a mapping."""
    out: dict[str, Any] = {}
    for key, value in data.items():
        key_text = str(key)
        if _is_sensitive_key_value(key_text):
            if isinstance(value, list):
                out[key] = [redact_scalar_value(item) for item in value]
            else:
                out[key] = redact_scalar_value(value)
            continue

        if isinstance(value, Mapping):
            out[key] = _redact_mapping_value(value)
        elif isinstance(value, list):
            out[key] = [
                _redact_mapping_value(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        elif isinstance(value, str):
            out[key] = _redact_text_value(value)
        else:
            out[key] = value

    return out


def _redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Backward-compatible internal mapping redaction helper for logging."""
    return _redact_mapping_value(value)


def redact_mapping(data: Any, request_id: str | None = None) -> dict[str, Any]:
    """
    Recursively redact sensitive values in a dictionary.

    Use this tool before logging or returning configuration, environment, state,
    or tool-result mappings that may contain credentials.

    Args:
        data (dict[str, Any]): Mapping to sanitize.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with redacted mapping.
    """
    tool_name = "redact_mapping"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    if not isinstance(data, dict):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="data must be a dictionary.",
            request_id=request_id,
            started_at=started_at,
        )

    return _success_response(
        tool_name=tool_name,
        message="Mapping redacted.",
        data={"redacted_mapping": _redact_mapping_value(data)},
        request_id=request_id,
        started_at=started_at,
    )


def _redact_text(value: str) -> str:
    """Backward-compatible internal text redaction helper for logging."""
    return _redact_text_value(value)


def _select_active_secret_version(
    refs: Sequence[SecretRef],
    policy: SecretRotationPolicy,
) -> SecretRef:
    """Select the newest active secret version within the policy overlap."""
    if not isinstance(policy, SecretRotationPolicy):
        raise TypeError("policy must be a SecretRotationPolicy.")
    if not isinstance(refs, Sequence):
        raise TypeError("refs must be a sequence of SecretRef objects.")
    if policy.overlap_versions < 1:
        raise ValueError("policy.overlap_versions must be >= 1.")

    candidates = [
        ref
        for ref in refs
        if isinstance(ref, SecretRef)
        and ref.secret_id == policy.secret_id
        and ref.active
    ]
    if not candidates:
        raise LookupError(f"No active secret versions found for '{policy.secret_id}'.")

    ordered = sorted(candidates, key=lambda item: item.created_at, reverse=True)
    return ordered[: policy.overlap_versions][0]


def select_active_secret_version(
    refs: Sequence[SecretRef],
    policy: SecretRotationPolicy,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Resolve the newest active secret version within an overlap policy.

    This tool returns only secret reference metadata. It never returns secret
    material.

    Args:
        refs (Sequence[SecretRef]): Candidate secret references.
        policy (SecretRotationPolicy): Rotation policy.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response with selected reference metadata.
    """
    tool_name = "select_active_secret_version"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        ref = _select_active_secret_version(refs, policy)
    except TypeError as error:
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )
    except ValueError as error:
        return _error_response(
            tool_name=tool_name,
            message="Invalid rotation policy.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )
    except LookupError as error:
        return _error_response(
            tool_name=tool_name,
            message="No active secret version found.",
            code="DATA_NOT_FOUND",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    return _success_response(
        tool_name=tool_name,
        message="Active secret version selected.",
        data={
            "secret_ref": secret_ref_to_dict(ref),
            "policy": rotation_policy_to_dict(policy),
        },
        request_id=request_id,
        started_at=started_at,
    )


def generate_encryption_key() -> str:
    """
    Generate a Fernet encryption key as a string.

    This is a deterministic application utility, not an AI tool. Do not expose
    generated keys to agents, logs, or model context.

    Returns:
        str: Fernet key.
    """
    return cast(bytes, Fernet.generate_key()).decode("utf-8")


def encrypt_data_value(data: str, key: str | bytes) -> str:
    """
    Encrypt string data using Fernet.

    This is an internal application utility, not an AI tool.
    """
    if not isinstance(data, str) or not data:
        raise ValueError("data must be a non-empty string.")
    if not isinstance(key, (str, bytes)) or not key:
        raise ValueError("key must be a non-empty string or bytes value.")

    active_key = key.encode("utf-8") if isinstance(key, str) else key
    encrypted = Fernet(active_key).encrypt(data.encode("utf-8")).decode("utf-8")
    return cast(str, encrypted)


def decrypt_data_value(token: str, key: str | bytes) -> str:
    """
    Decrypt Fernet ciphertext.

    This is an internal application utility, not an AI tool. Never return
    plaintext secrets to agents or logs.
    """
    if not isinstance(token, str) or not token:
        raise ValueError("token must be a non-empty string.")
    if not isinstance(key, (str, bytes)) or not key:
        raise ValueError("key must be a non-empty string or bytes value.")

    active_key = key.encode("utf-8") if isinstance(key, str) else key
    decrypted = Fernet(active_key).decrypt(token.encode("utf-8")).decode("utf-8")
    return cast(str, decrypted)


def hash_password_value(password: str) -> str:
    """
    Hash a password with the configured password context.

    This is an internal application utility, not an AI tool.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string.")

    return cast(str, pwd_context.hash(password))


def verify_password_value(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a password hash.

    This is an internal application utility, not an AI tool.
    """
    if not isinstance(plain_password, str) or not plain_password:
        raise ValueError("plain_password must be a non-empty string.")
    if not isinstance(hashed_password, str) or not hashed_password:
        raise ValueError("hashed_password must be a non-empty string.")

    return cast(bool, pwd_context.verify(plain_password, hashed_password))


__all__ = [
    "REDACTED",
    "REDACTED_VALUE",
    "SENSITIVE_KEYWORDS",
    "SecretRef",
    "SecretRotationPolicy",
    "decrypt_data_value",
    "encrypt_data_value",
    "generate_encryption_key",
    "hash_password_value",
    "is_sensitive_key",
    "redact_mapping",
    "redact_scalar_value",
    "redact_text",
    "rotation_policy_to_dict",
    "secret_ref_to_dict",
    "select_active_secret_version",
    "verify_password_value",
]

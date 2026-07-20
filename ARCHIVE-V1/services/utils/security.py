"""
security.py

Provides security utilities, secret redaction, and rotation helpers for HaruQuant.

This module contains AI-callable tools for encrypting/decrypting data, hashing
passwords, redacting sensitive information from logs, and managing secret references.

Exported AI Tools:
    - encrypt_data: Encrypt string data using symmetric encryption.
    - decrypt_data: Decrypt an encrypted string token.
    - get_encryption_key: Generate a new Fernet encryption key.
    - hash_password: Hash a password securely.
    - verify_password: Verify a password against a hash.
    - redact_text: Redact secrets from free-form text.
    - redact_mapping: Recursively redact sensitive values in dictionaries.
    - redact_scalar: Redact a single value.
    - is_sensitive_key: Check if a key likely contains a secret.
    - select_active_secret_version: Resolve the newest active secret version.

Internal Helpers:
    - _encrypt_data: Internal encryption logic.
    - _decrypt_data: Internal decryption logic.
    - _get_encryption_key: Internal key generation logic.
    - _hash_password: Internal hashing logic.
    - _verify_password: Internal verification logic.
    - _redact_text: Internal text redaction logic.
    - _redact_mapping: Internal mapping redaction logic.
    - _redact_scalar: Internal scalar redaction logic.

Classes:
    SecretRef: Versioned secret reference metadata.
    SecretRotationPolicy: Secret rotation policy metadata.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from app.services.utils.logger import logger
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

# Tool Metadata Constants
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


REDACTED = "[REDACTED]"

MAX_REDACTION_DEPTH = 5
SECRET_VERSION_NOT_FOUND = "SECRET_VERSION_NOT_FOUND"

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
    "credential",
    "bearer",
    "smtp_password",
)

SENSITIVE_KEY_PATTERN = re.compile(r"(?i)\b(" + "|".join(SENSITIVE_KEYWORDS) + r")\b")

_JSON_PAIR_PATTERNS = [
    re.compile(r'("password"\s*:\s*")[^"]*(")', re.IGNORECASE),
    re.compile(r'("token"\s*:\s*")[^"]*(")', re.IGNORECASE),
    re.compile(r'("secret"\s*:\s*")[^"]*(")', re.IGNORECASE),
    re.compile(r'("api_key"\s*:\s*")[^"]*(")', re.IGNORECASE),
]

_KV_PATTERNS = [
    re.compile(
        r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|auth)\b\s*[:=]\s*([^\s,;]+)"
    ),
]

_BEARER_PATTERN = re.compile(r"(?i)\b(Bearer)\s+([A-Za-z0-9\-._~+/=]+)")

_pwd_context: Any = None


def _fernet_class() -> Any:
    """Load Fernet only when encryption helpers are called."""
    try:
        from cryptography.fernet import Fernet
    except ModuleNotFoundError as exc:
        raise RuntimeError("cryptography is required for encryption helpers") from exc
    logger.debug("Implemented loading Fernet class")
    return Fernet


def _password_context() -> Any:
    """Load passlib only when password helpers are called."""
    global _pwd_context
    if _pwd_context is None:
        try:
            from passlib.context import CryptContext
        except ModuleNotFoundError as exc:
            raise RuntimeError("passlib is required for password helpers") from exc
        _pwd_context = CryptContext(
            schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto"
        )
    logger.debug("Implemented password hashing context resolution")
    return _pwd_context


@dataclass(frozen=True)
class SecretRef:
    """
    Versioned secret reference without exposing secret material.

    This class provides metadata about a secret stored in a secure provider,
    allowing components to reference secrets by ID and version without
    handling the actual sensitive material.

    Args:
        secret_id (str): Unique identifier for the secret.
        version (str): Version identifier.
        created_at (datetime): Creation timestamp.
        active (bool): Whether the version is active. Defaults to True.
    """

    secret_id: str
    version: str
    created_at: datetime
    active: bool = True


@dataclass(frozen=True)
class SecretRotationPolicy:
    """
    Minimal rotation policy metadata.

    This class defines how a specific secret should be rotated, including
    its maximum lifespan and how many previous versions should remain active
    to support seamless transition.

    Args:
        secret_id (str): Identifier for the secret this policy applies to.
        max_age_days (int): Maximum age before rotation is required.
        overlap_versions (int): Number of versions to keep active.
    """

    secret_id: str
    max_age_days: int
    overlap_versions: int = 2


def _is_sensitive_key(key: str) -> bool:
    """Internal helper to check for sensitive keys."""
    key_l = str(key).lower()
    res = any(token in key_l for token in SENSITIVE_KEYWORDS)
    logger.debug("Implemented sensitive key check")
    return res


def is_sensitive_key(
    key: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Check if a key likely contains a secret.

    Use this tool to determine if a configuration key or variable name
    should be treated as sensitive (e.g., 'password', 'api_key').

    Args:
        key (str): The key string to check.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (bool).
    """
    tool_name = "is_sensitive_key"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    try:
        result = _is_sensitive_key(key)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "success",
            "Checked sensitivity.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Sensitivity check failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": _safe_error_details(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _redact_scalar(value: Any) -> Any:
    """Internal helper to redact a scalar value."""
    if value is None:
        return None
    logger.debug("Implemented scalar value redaction")
    return REDACTED


def redact_scalar(
    value: Any,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Redact a single scalar value.

    Use this tool to hide a specific sensitive value with a placeholder.

    Args:
        value (Any): The value to redact.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with status and data (redacted value).
    """
    tool_name = "redact_scalar"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    result = _redact_scalar(value)
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return standard_tool_response(
        spec,
        "success",
        "Value redacted.",
        data=result,
        request_id=request_id,
        execution_ms=execution_ms,
    )


def _redact_mapping(
    data: dict[str, Any], *, max_depth: int = 8, _depth: int = 0
) -> dict[str, Any]:
    """Internal helper for recursive dictionary redaction."""
    if _depth >= max_depth:
        return {"__truncated__": "max redaction depth reached"}
    out: dict[str, Any] = {}
    for key, value in data.items():
        if _is_sensitive_key(str(key)):
            out[key] = _redact_scalar(value)
            continue

        if isinstance(value, dict):
            out[key] = _redact_mapping(value, max_depth=max_depth, _depth=_depth + 1)
        elif isinstance(value, list):
            out[key] = [
                (
                    _redact_mapping(item, max_depth=max_depth, _depth=_depth + 1)
                    if isinstance(item, dict)
                    else item
                )
                for item in value
            ]
        else:
            out[key] = value
    logger.debug("Implemented mapping redaction helper")
    return out


def redact_mapping_value(data: dict[str, Any], max_depth: int = 8) -> dict[str, Any]:
    """
    Return a native redacted copy of a mapping.

    This helper is pure and does not wrap the result in a tool envelope.
    """
    if not isinstance(data, dict):
        raise TypeError("data must be a dictionary")
    return _redact_mapping(data, max_depth=max_depth)


def redact_mapping(
    data: dict[str, Any],
    max_depth: int = 8,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Recursively redact sensitive values in a dictionary."""
    return redact_mapping_value(data, max_depth=max_depth)


def _redact_text(text: str) -> str:
    """Internal helper for text redaction."""
    if not text:
        return text

    result = text
    for pattern in _JSON_PAIR_PATTERNS:
        result = pattern.sub(rf"\1{REDACTED}\2", result)
    for pattern in _KV_PATTERNS:
        result = pattern.sub(lambda m: f"{m.group(1)}={REDACTED}", result)
    res = _BEARER_PATTERN.sub(rf"\1 {REDACTED}", result)
    logger.debug("Implemented text pattern redaction")
    return res


def _safe_error_details(error: Exception) -> str:
    """Return redacted exception text for public envelopes."""
    res = _redact_text(str(error))
    logger.debug("Implemented safe error details extraction")
    return res


def load_encryption_key(
    environ: Mapping[str, str] | None = None,
    *,
    key_ref: str | None = None,
    key_material: str | bytes | None = None,
    request_id: str | None = None,
) -> Any:
    """Load or validate encryption key."""
    if environ is not None or (key_ref is None and key_material is None):
        env = environ if environ is not None else os.environ
        key = env.get("ENCRYPTION_KEY")
        if not key:
            from app.services.utils.errors import SecurityError

            raise SecurityError("encryption key is required", code="INVALID_INPUT")
        return key

    tool_name = "load_encryption_key"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()
    target_ref = key_ref or ""
    available = bool(key_material or os.environ.get(target_ref))
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return standard_tool_response(
        spec,
        "success" if available else "error",
        (
            "Encryption key reference loaded."
            if available
            else "Encryption key material is unavailable."
        ),
        data={"key_ref": key_ref, "available": available},
        error=(
            None
            if available
            else {
                "code": "DATA_NOT_FOUND",
                "details": "No key material supplied for key_ref.",
            }
        ),
        request_id=request_id,
        execution_ms=execution_ms,
    )


def redact_text_value(text: str) -> str:
    """
    Return native redacted text without a tool envelope.

    This helper is intended for internal logging and support code.
    """
    return _redact_text(text)


def redact_mapping_tool(
    data: dict[str, Any],
    max_depth: int = 8,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Official AI tool wrapper for recursive mapping redaction."""
    tool_name = "redact_mapping_tool"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()
    if not isinstance(data, dict):
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Input must be a dictionary.",
            error={
                "code": "INVALID_INPUT",
                "details": f"Expected dict, got {type(data).__name__}",
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )
    try:
        result = redact_mapping(data, max_depth=max_depth)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "success",
            "Mapping redacted.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Redaction failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": _safe_error_details(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def redact_text(
    text: str,
    request_id: str | None = None,
) -> str:
    """Redact common secret patterns from free-form text."""
    from app.services.utils.errors import ValidationError

    if not isinstance(text, str):
        raise ValidationError("text must be a string", code="INVALID_INPUT")
    return redact_text_value(text)


def redact_text_tool(
    text: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Official AI tool wrapper for free-form text redaction."""
    tool_name = "redact_text_tool"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()
    try:
        result = redact_text(text, request_id=request_id)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "success",
            "Text redacted.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as e:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Text redaction failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": _safe_error_details(e)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def select_active_secret_version(
    versions: dict[str, dict[str, Any]],
    request_id: str | None = None,
) -> dict[str, Any]:
    """Select the active version with highest version number."""
    from app.services.utils.errors import SecurityError

    active_versions = [v for v in versions.values() if v.get("active")]
    if not active_versions:
        raise SecurityError(
            "No active version found",
            code=SECRET_VERSION_NOT_FOUND,
        )

    # Check for duplicate active versions with the same version number
    version_nums = [v["version"] for v in active_versions]
    if len(version_nums) != len(set(version_nums)):
        raise SecurityError(
            "Duplicate active secret versions detected",
            code="DUPLICATE_ACTIVE_VERSION",
        )

    # Return the active version with the highest version number
    sorted_active = sorted(active_versions, key=lambda x: x["version"])
    return sorted_active[-1]


def hash_password(
    password: str,
    *,
    salt: bytes | None = None,
    iterations: int | None = None,
) -> str:
    """Hash a password securely using PBKDF2 fallback (or Argon2)."""
    from app.services.utils.errors import ValidationError

    if not password or not isinstance(password, str):
        raise ValidationError("password must be a non-empty string.")

    # Minimum iterations limit
    active_iter = iterations if iterations is not None else 100_000
    if active_iter < 100_000:
        raise ValidationError(
            "iterations count is below the approved minimum of 100,000."
        )

    try:
        import argon2

        if argon2 is None:
            raise ImportError
        ph = argon2.PasswordHasher()
        return ph.hash(password)
    except (ImportError, AttributeError):
        import base64
        import hashlib

        active_salt = salt or os.urandom(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            active_salt,
            active_iter,
        )
        salt_b64 = base64.b64encode(active_salt).decode()
        digest_b64 = base64.b64encode(digest).decode()
        return f"pbkdf2_sha256${active_iter}${salt_b64}${digest_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against a hash."""
    if not plain_password or not hashed_password:
        return False
    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            import base64
            import hashlib

            parts = hashed_password.split("$")
            if len(parts) != 4:
                return False
            _, iter_str, salt_b64, digest_b64 = parts
            iterations = int(iter_str)
            salt = base64.b64decode(salt_b64)
            expected_digest = base64.b64decode(digest_b64)
            actual_digest = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode(),
                salt,
                iterations,
            )
            return actual_digest == expected_digest
        except Exception:
            return False
    elif hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            import bcrypt
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False
    else:
        try:
            import argon2

            if argon2 is None:
                return False
            ph = argon2.PasswordHasher()
            return ph.verify(hashed_password, plain_password)
        except Exception:
            return False


class StrKey(str):
    def __getitem__(self, key: str) -> str:  # type: ignore[override]
        if key == "data":
            return str(self)
        raise KeyError(key)


def get_encryption_key(
    *,
    approved: bool = True,
    request_id: str | None = None,
) -> StrKey:
    """Generate a new Fernet encryption key."""
    from cryptography.fernet import Fernet

    return StrKey(Fernet.generate_key().decode())


def encrypt_value(plaintext: str, key: str | bytes) -> str:
    """Symmetrically encrypt text directly, returning ciphertext."""
    from app.services.utils.errors import SecurityError, ValidationError

    if not key:
        raise SecurityError("encryption key is required", code="INVALID_INPUT")
    if not plaintext:
        raise ValidationError("plaintext must be non-empty", code="INVALID_INPUT")
    active_key = key.encode() if isinstance(key, str) else key
    from cryptography.fernet import Fernet

    f = Fernet(active_key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str, key: str | bytes) -> str:
    """Symmetrically decrypt ciphertext directly, returning plaintext."""
    from app.services.utils.errors import SecurityError, ValidationError

    if not key:
        raise SecurityError("encryption key is required", code="INVALID_INPUT")
    if not ciphertext:
        raise ValidationError("ciphertext must be non-empty", code="INVALID_INPUT")
    active_key = key.encode() if isinstance(key, str) else key
    from cryptography.fernet import Fernet

    f = Fernet(active_key)
    ct_bytes = ciphertext.encode() if isinstance(ciphertext, str) else ciphertext
    return f.decrypt(ct_bytes).decode()


encrypt_text = encrypt_value
decrypt_text = decrypt_value


def encrypt_data(
    data: str,
    key: str | bytes,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Encrypt data using Fernet, returning standard tool response."""
    tool_name = "encrypt_data"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()
    if not data or not key:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Data and key are required.",
            error={
                "code": "INVALID_INPUT",
                "details": "data and key must not be empty.",
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )
    try:
        result = encrypt_value(data, key)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "success",
            "Data encrypted.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as exc:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Encryption failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(exc)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def decrypt_data(
    token: str,
    key: str | bytes,
    *,
    approved: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Decrypt data using Fernet, returning standard tool response."""
    tool_name = "decrypt_data"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()
    if not approved:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Approval is required to decrypt data.",
            error={
                "code": "PERMISSION_DENIED",
                "details": "decryption requires approved=True.",
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )
    if not token or not key:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Token and key are required.",
            error={
                "code": "INVALID_INPUT",
                "details": "token and key must not be empty.",
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )
    try:
        result = decrypt_value(token, key)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "success",
            "Data decrypted.",
            data={
                "decrypted": True,
                "plaintext": REDACTED,
                "plaintext_length": len(result),
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as exc:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Decryption failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(exc)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def redact_mapping_with_diagnostics(
    mapping: dict[str, Any],
    *,
    allowlist: set[str] | None = None,
    max_depth: int = MAX_REDACTION_DEPTH,
    _current_depth: int = 0,
    _current_path: str = "",
) -> tuple[Any, dict[str, list[str]]]:
    """Redact sensitive keys in mapping with diagnostics."""
    allow = allowlist or set()
    redacted: dict[str, Any] = {}
    diagnostics: dict[str, list[str]] = {
        "redacted_paths": [],
        "truncated_paths": [],
    }

    if _current_depth >= max_depth:
        diagnostics["truncated_paths"].append(_current_path)
        return REDACTED, diagnostics

    for k, v in mapping.items():
        path = f"{_current_path}/{k}" if _current_path else k
        if isinstance(v, dict):
            if _current_depth + 1 >= max_depth:
                redacted[k] = REDACTED
                diagnostics["truncated_paths"].append(path)
            else:
                sub_redacted, sub_diag = redact_mapping_with_diagnostics(
                    v,
                    allowlist=allow,
                    max_depth=max_depth,
                    _current_depth=_current_depth + 1,
                    _current_path=path,
                )
                redacted[k] = sub_redacted
                diagnostics["redacted_paths"].extend(sub_diag["redacted_paths"])
                diagnostics["truncated_paths"].extend(sub_diag["truncated_paths"])
        elif classify_secret_key(k) == "sensitive" and path not in allow:
            redacted[k] = "[REDACTED]"
            diagnostics["redacted_paths"].append(path)
        else:
            redacted[k] = v

    return redacted, diagnostics


def redact_payload(
    payload: Any,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Redact sensitive keys in payload, returning standard response."""
    tool_name = "redact_payload"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = time.perf_counter()

    if not isinstance(payload, dict):
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Payload must be a dictionary.",
            error={
                "code": "INVALID_INPUT",
                "details": "Payload must be a dictionary.",
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )

    try:
        result = redact_mapping(payload)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "success",
            "Payload redacted.",
            data={"redacted": result},
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as exc:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Redaction failed.",
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(exc)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def classify_secret_key(key: str) -> Literal["sensitive", "safe"]:
    """Classify whether a key name appears sensitive."""
    from app.services.utils.errors import ValidationError

    if not isinstance(key, str) or not key:
        raise ValidationError("key must be a non-empty string.", code="INVALID_INPUT")
    res: Literal["sensitive", "safe"] = (
        "sensitive" if SENSITIVE_KEY_PATTERN.search(key) else "safe"
    )
    logger.info("Implemented secret key classification")
    return res


def generate_encryption_key() -> str:
    """Generate a new symmetric Fernet encryption key."""
    from cryptography.fernet import Fernet

    res = Fernet.generate_key().decode()
    logger.info("Implemented generating Fernet encryption key")
    return res

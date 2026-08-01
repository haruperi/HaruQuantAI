"""Authenticated encryption and persistence of broker credential material."""

from __future__ import annotations

import base64
import json
import secrets
from collections.abc import Mapping
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel, ConfigDict, SecretStr

from app.services.api.identity.accounts import IdentityError, _execute
from app.utils import canonical_json, derive_stable_id, get_logger, utc_now

logger = get_logger(__name__)


class CredentialRecord(BaseModel):
    """Secret-free persisted credential metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reference: str
    owner_id: str
    key_id: str
    created_at: datetime
    version: int = 1


def _select_key(key_set: Mapping[str, bytes], active_key_id: str) -> tuple[str, bytes]:
    """Select exactly one explicitly active authenticated-encryption key.

    Returns:
        Selected key identifier and bytes.

    Raises:
        IdentityError: If selection is missing or key length is invalid.
    """
    if not active_key_id or active_key_id not in key_set:
        raise IdentityError("CREDENTIAL_ACTIVE_KEY_MISSING")
    key = key_set[active_key_id]
    if len(key) not in {16, 24, 32}:
        raise IdentityError("CREDENTIAL_ACTIVE_KEY_INVALID")
    return active_key_id, key


def store_credential(
    *,
    owner_id: str,
    label: str,
    material: Mapping[str, SecretStr | str],
    key_set: Mapping[str, bytes],
    active_key_id: str,
    request_id: str,
) -> CredentialRecord:
    """Encrypt credential material before persistence.

    Args:
        owner_id: Authorized credential owner.
        label: Stable non-secret provider/account label.
        material: Credential values to encrypt.
        key_set: Externally provisioned in-memory keys by ID.
        active_key_id: Explicit key used for this record.
        request_id: Canonical operation request identifier.

    Returns:
        Secret-free persisted record metadata.

    Raises:
        IdentityError: If key selection, material, encryption, or storage fails.
    """
    logger.info("Encrypting and storing one UI/API credential record")
    key_id, key = _select_key(key_set, active_key_id)
    if not owner_id or not label or not material:
        raise IdentityError("CREDENTIAL_INPUT_INVALID")
    plaintext_values = {
        name: value.get_secret_value() if isinstance(value, SecretStr) else value
        for name, value in material.items()
    }
    if any(not name or not value for name, value in plaintext_values.items()):
        raise IdentityError("CREDENTIAL_INPUT_INVALID")
    reference_id = derive_stable_id("id", f"api-credential:{owner_id}:{label}")
    reference = f"secret://{reference_id}"
    nonce = secrets.token_bytes(12)
    associated_data = f"{reference}|{owner_id}|{key_id}|1".encode()
    plaintext = canonical_json(plaintext_values).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    created_at = utc_now()
    _execute(
        (
            "INSERT INTO api_credentials "
            "(reference, owner_id, key_id, nonce_b64, ciphertext_b64, "
            "created_at, version) "
            "VALUES (?, ?, ?, ?, ?, ?, 1) "
            "ON CONFLICT(reference) DO UPDATE SET key_id=excluded.key_id, "
            "nonce_b64=excluded.nonce_b64, ciphertext_b64=excluded.ciphertext_b64, "
            "created_at=excluded.created_at, version=excluded.version",
        ),
        (
            (
                reference,
                owner_id,
                key_id,
                base64.urlsafe_b64encode(nonce).decode("ascii"),
                base64.urlsafe_b64encode(ciphertext).decode("ascii"),
                created_at.isoformat(),
            ),
        ),
        request_id=request_id,
    )
    return CredentialRecord(
        reference=reference,
        owner_id=owner_id,
        key_id=key_id,
        created_at=created_at,
    )


def resolve_credential_reference(
    reference: str,
    *,
    owner_id: str,
    key_set: Mapping[str, bytes],
    request_id: str,
) -> Mapping[str, SecretStr]:
    """Resolve an authorized opaque reference into in-memory secret values.

    Args:
        reference: Exact ``secret://`` reference.
        owner_id: Authenticated owner expected by the persisted record.
        key_set: Externally provisioned in-memory keys by ID.
        request_id: Canonical operation request identifier.

    Returns:
        Decrypted values wrapped in ``SecretStr``.

    Raises:
        IdentityError: If reference, ownership, key, integrity, or storage fails.
    """
    logger.info("Resolving one authorized UI/API credential reference")
    if not reference.startswith("secret://"):
        raise IdentityError("CREDENTIAL_REFERENCE_INVALID")
    result = _execute(
        (
            "SELECT owner_id, key_id, nonce_b64, ciphertext_b64, version "
            "FROM api_credentials WHERE reference = ?",
        ),
        ((reference,),),
        request_id=request_id,
    )
    rows = tuple(result.rows)
    if len(rows) != 1:
        raise IdentityError("CREDENTIAL_REFERENCE_UNKNOWN")
    row = rows[0]
    if str(row["owner_id"]) != owner_id:
        raise IdentityError("CREDENTIAL_ACCESS_DENIED")
    key_id = str(row["key_id"])
    if key_id not in key_set:
        raise IdentityError("CREDENTIAL_KEY_UNKNOWN")
    associated_data = (
        f"{reference}|{owner_id}|{key_id}|{int(str(row['version']))}".encode()
    )
    try:
        plaintext = AESGCM(key_set[key_id]).decrypt(
            base64.urlsafe_b64decode(str(row["nonce_b64"])),
            base64.urlsafe_b64decode(str(row["ciphertext_b64"])),
            associated_data,
        )
        parsed = json.loads(plaintext.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise IdentityError("CREDENTIAL_INTEGRITY_FAILED") from error
    if not isinstance(parsed, dict) or any(
        not isinstance(name, str) or not isinstance(value, str)
        for name, value in parsed.items()
    ):
        raise IdentityError("CREDENTIAL_PAYLOAD_INVALID")
    return {name: SecretStr(value) for name, value in parsed.items()}


__all__ = ("CredentialRecord", "resolve_credential_reference", "store_credential")

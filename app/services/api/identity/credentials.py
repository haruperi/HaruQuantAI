"""Authenticated encryption and persistence of broker credential material."""

from __future__ import annotations

import base64
import json
import secrets
from collections.abc import Mapping
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel, ConfigDict, SecretStr

from app.composition.logging import get_logger
from app.kernel.identity import derive_stable_id
from app.kernel.serialization import canonical_json
from app.kernel.time import utc_now
from app.services.api.identity.errors import IdentityError
from app.services.api.identity.persistence import (
    read_credential_record,
    update_credential_record,
)
from app.services.api.identity.system_settings import (
    get_credential_manifest,
    validate_credential_material,
)

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
    update_credential_record(
        reference=reference,
        owner_id=owner_id,
        key_id=key_id,
        nonce_b64=base64.urlsafe_b64encode(nonce).decode("ascii"),
        ciphertext_b64=base64.urlsafe_b64encode(ciphertext).decode("ascii"),
        created_at=created_at.isoformat(),
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
    rows = read_credential_record(reference, request_id=request_id)
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


def get_system_credential_statuses(
    *,
    request_id: str,
) -> tuple[Mapping[str, object], ...]:
    """Return secret-free status for every manifest-approved credential slot.

    Args:
        request_id: Canonical operation request identifier.

    Returns:
        Ordered credential-slot status mappings with no protected values.
    """
    statuses: list[Mapping[str, object]] = []
    for definition in get_credential_manifest():
        slot = str(definition["slot"])
        reference_id = derive_stable_id("id", f"api-credential:system:{slot}")
        rows = read_credential_record(
            f"secret://{reference_id}",
            request_id=request_id,
        )
        status: dict[str, object] = {
            "slot": slot,
            "label": definition["label"],
            "fields": definition["fields"],
            "activation": definition["activation"],
            "configured": bool(rows),
            "version": int(str(rows[0]["version"])) if rows else 0,
            "updated_at": str(rows[0]["created_at"]) if rows else None,
        }
        statuses.append(status)
    return tuple(statuses)


def store_system_credential(
    slot: str,
    material: Mapping[str, str],
    *,
    key_set: Mapping[str, bytes],
    active_key_id: str,
    request_id: str,
) -> CredentialRecord:
    """Validate and encrypt one system-owned credential slot.

    Args:
        slot: Manifest-approved credential slot.
        material: Complete write-only credential material.
        key_set: Externally provisioned encryption keys.
        active_key_id: Explicit active encryption key identifier.
        request_id: Canonical operation request identifier.

    Returns:
        Secret-free persisted credential metadata.

    Raises:
        IdentityError: If slot validation, encryption, or persistence fails.
    """
    validated = validate_credential_material(slot, material)
    return store_credential(
        owner_id="system",
        label=slot,
        material=validated,
        key_set=key_set,
        active_key_id=active_key_id,
        request_id=request_id,
    )


__all__ = (
    "CredentialRecord",
    "get_system_credential_statuses",
    "resolve_credential_reference",
    "store_credential",
    "store_system_credential",
)

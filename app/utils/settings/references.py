"""Strict versioned reference mappings for immutable configuration artifacts."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from types import MappingProxyType

from app.utils.errors.exceptions import ConfigurationError, ValidationError
from app.utils.serialization import canonical_digest, to_json_safe

_VERSION = "v1"
_PROFILE_SCHEMA = "utils.profile_ref.v1"
_ARTIFACT_SCHEMA = "utils.version_ref.v1"
_VERSION_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def _validate_reference(
    value: Mapping[str, object], *, schema_id: str, kind_field: str, id_field: str
) -> dict[str, str]:
    """Validate one strict reference mapping.

    Args:
        value: Candidate mapping.
        schema_id: Required schema identity.
        kind_field: Kind field name.
        id_field: Identifier field name.

    Returns:
        Validated detached reference.

    Raises:
        ValidationError: If validation fails.
    """
    expected = {
        "contract_version",
        "schema_id",
        kind_field,
        id_field,
        "version",
        "content_hash",
    }
    if set(value) != expected:
        raise ValidationError("REFERENCE_SHAPE_INVALID")
    if value.get("contract_version") != _VERSION or value.get("schema_id") != schema_id:
        raise ValidationError("REFERENCE_VERSION_INCOMPATIBLE")
    result: dict[str, str] = {}
    for key in expected:
        item = value[key]
        if not isinstance(item, str) or not item or item != item.strip():
            raise ValidationError("REFERENCE_VALUE_INVALID")
        result[key] = item
    if _VERSION_PATTERN.fullmatch(result["version"]) is None:
        raise ValidationError("REFERENCE_VERSION_INVALID")
    if _HASH_PATTERN.fullmatch(result["content_hash"]) is None:
        raise ValidationError("REFERENCE_HASH_INVALID")
    return result


def build_profile_ref(
    *, profile_kind: str, profile_id: str, version: str, content_hash: str
) -> dict[str, str]:
    """Build a ProfileRef v1 mapping.

    Args:
        profile_kind: Profile kind.
        profile_id: Profile identifier.
        version: Immutable version.
        content_hash: SHA-256 content hash.

    Returns:
        ProfileRef v1 mapping.
    """
    return parse_profile_ref(
        {
            "contract_version": _VERSION,
            "schema_id": _PROFILE_SCHEMA,
            "profile_kind": profile_kind,
            "profile_id": profile_id,
            "version": version,
            "content_hash": content_hash,
        }
    )


def parse_profile_ref(value: Mapping[str, object]) -> dict[str, str]:
    """Validate and detach a ProfileRef v1 mapping.

    Args:
        value: Candidate mapping.

    Returns:
        Validated reference.
    """
    return _validate_reference(
        value,
        schema_id=_PROFILE_SCHEMA,
        kind_field="profile_kind",
        id_field="profile_id",
    )


def build_version_ref(
    *, artifact_kind: str, artifact_id: str, version: str, content_hash: str
) -> dict[str, str]:
    """Build a VersionRef v1 mapping.

    Args:
        artifact_kind: Artifact kind.
        artifact_id: Artifact identifier.
        version: Immutable version.
        content_hash: SHA-256 content hash.

    Returns:
        VersionRef v1 mapping.
    """
    return parse_version_ref(
        {
            "contract_version": _VERSION,
            "schema_id": _ARTIFACT_SCHEMA,
            "artifact_kind": artifact_kind,
            "artifact_id": artifact_id,
            "version": version,
            "content_hash": content_hash,
        }
    )


def parse_version_ref(value: Mapping[str, object]) -> dict[str, str]:
    """Validate and detach a VersionRef v1 mapping.

    Args:
        value: Candidate mapping.

    Returns:
        Validated reference.
    """
    return _validate_reference(
        value,
        schema_id=_ARTIFACT_SCHEMA,
        kind_field="artifact_kind",
        id_field="artifact_id",
    )


def load_profile_document(
    document: Mapping[str, object],
    *,
    required_fields: Sequence[str],
    compatible_versions: Sequence[str],
) -> tuple[MappingProxyType[str, object], dict[str, str]]:
    """Strictly validate a profile document and resolve its reference.

    Args:
        document: Candidate profile document.
        required_fields: Exact domain-owned payload fields.
        compatible_versions: Explicit compatible versions.

    Returns:
        Immutable document and ProfileRef.

    Raises:
        ConfigurationError: If shape or version is incompatible.
    """
    expected = {"profile_kind", "profile_id", "version"} | set(required_fields)
    if not required_fields or set(document) != expected:
        raise ConfigurationError("PROFILE_DOCUMENT_INVALID")
    version = document.get("version")
    if not isinstance(version, str) or version not in compatible_versions:
        raise ConfigurationError("PROFILE_VERSION_INCOMPATIBLE")
    safe = to_json_safe(document)
    if not isinstance(safe, dict):
        raise ConfigurationError("PROFILE_DOCUMENT_INVALID")
    reference = build_profile_ref(
        profile_kind=str(document["profile_kind"]),
        profile_id=str(document["profile_id"]),
        version=version,
        content_hash=canonical_digest(safe),
    )
    return MappingProxyType(deepcopy(safe)), reference

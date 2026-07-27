"""Deterministic validation for immutable error catalogues."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

from app.utils.errors.exceptions import ValidationError
from app.utils.errors.metadata import normalize_error_code

if TYPE_CHECKING:
    from app.utils.errors.contracts import ErrorDefinition


def validate_error_catalog(
    catalog: Mapping[str, ErrorDefinition],
) -> Mapping[str, ErrorDefinition]:
    """Validate and copy an immutable domain error catalogue.

    Args:
        catalog: Mapping from approved code to its immutable definition.

    Returns:
        A detached immutable mapping containing the validated definitions.

    Raises:
        ValidationError: If the catalogue is empty, malformed, or inconsistent.
    """
    if not catalog:
        raise ValidationError("ERROR_CATALOG_INVALID", "EMPTY")
    validated: dict[str, ErrorDefinition] = {}
    for code, definition in catalog.items():
        try:
            normalized = normalize_error_code(code)
        except ValidationError as error:
            raise ValidationError("ERROR_CATALOG_INVALID", "CODE_INVALID") from error
        if normalized != code or definition.code != code:
            raise ValidationError("ERROR_CATALOG_INVALID", "CODE_MISMATCH")
        if code in validated:
            raise ValidationError("ERROR_CATALOG_INVALID", "CODE_DUPLICATE")
        validated[code] = definition
    return MappingProxyType(validated)


def require_error_definition(
    code: str,
    catalog: Mapping[str, ErrorDefinition],
) -> ErrorDefinition:
    """Return an approved definition or reject an unknown code.

    Args:
        code: Candidate symbolic error code.
        catalog: Owning domain's immutable error catalogue.

    Returns:
        The approved immutable error definition.

    Raises:
        ValidationError: If the catalogue or code is invalid or unapproved.
    """
    validated = validate_error_catalog(catalog)
    try:
        normalized = normalize_error_code(code)
    except ValidationError as error:
        raise ValidationError("ERROR_CODE_UNAPPROVED", "CODE_INVALID") from error
    definition = validated.get(normalized)
    if definition is None:
        raise ValidationError("ERROR_CODE_UNAPPROVED", "CODE_UNKNOWN")
    return definition


__all__ = ["require_error_definition", "validate_error_catalog"]

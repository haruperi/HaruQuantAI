"""Define the immutable authentication and trace-context contract.

The module validates caller-supplied identity, authorization labels, and trace
identifiers without performing authentication or permission decisions.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.utils.contracts.audit import (
    validate_non_empty,
    validate_trace_id,
    validate_utc,
)


class AuthContext(BaseModel):
    """Represent an immutable authenticated principal and trace context.

    The contract carries authentication evidence produced by the owning
    boundary. It does not verify identities or authorize operations.

    Attributes:
        contract_version: Fixed contract version, always ``"v1"``.
        schema_id: Fixed schema identity, always
            ``"utils.auth_context.v1"``.
        principal_id: Non-empty identifier for the authenticated principal.
        principal_type: Supported human or service-account principal type.
        roles: Ordered, duplicate-free role labels.
        permissions: Ordered, duplicate-free permission labels.
        scopes: Ordered, duplicate-free authorization scopes.
        tenant_or_environment: Tenant or environment bound to the evidence.
        request_id: Canonical request trace identifier.
        workflow_id: Canonical workflow trace identifier.
        correlation_id: Canonical correlation trace identifier.
        issued_at: Aware UTC instant when the evidence was issued.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["v1"]
    schema_id: Literal["utils.auth_context.v1"]
    principal_id: str
    principal_type: Literal["USER", "SERVICE_ACCOUNT"]
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    scopes: tuple[str, ...]
    tenant_or_environment: str
    request_id: str
    workflow_id: str
    correlation_id: str
    issued_at: datetime

    @field_validator("principal_id", "tenant_or_environment")
    @classmethod
    def _validate_identity(cls, value: str, info: object) -> str:
        """Validate a required identity field.

        Args:
            value: Candidate identity value.
            info: Pydantic validation metadata containing the field name.

        Returns:
            The unchanged, validated value.

        Raises:
            ValueError: The value is empty or contains outer whitespace.
        """
        return validate_non_empty(value, str(getattr(info, "field_name", "field")))

    @field_validator("roles", "permissions", "scopes")
    @classmethod
    def _validate_string_tuple(
        cls,
        value: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        """Validate an ordered tuple of authorization labels.

        Args:
            value: Candidate role, permission, or scope labels.
            info: Pydantic validation metadata containing the field name.

        Returns:
            A tuple containing the validated labels in caller order.

        Raises:
            ValueError: A label is empty, untrimmed, or duplicated.
        """
        field_name = str(getattr(info, "field_name", "contract tuple"))
        if len(set(value)) != len(value):
            message = f"{field_name} must not contain duplicates"
            raise ValueError(message)
        return tuple(validate_non_empty(item, field_name) for item in value)

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate and return a canonical request identifier.

        Args:
            value: Candidate request identifier.

        Returns:
            The validated identifier.

        Raises:
            ValueError: The identifier is not canonical.
        """
        return validate_trace_id(value, "req", "request_id")

    @field_validator("workflow_id")
    @classmethod
    def _validate_workflow_id(cls, value: str) -> str:
        """Validate and return a canonical workflow identifier.

        Args:
            value: Candidate workflow identifier.

        Returns:
            The validated identifier.

        Raises:
            ValueError: The identifier is not canonical.
        """
        return validate_trace_id(value, "wf", "workflow_id")

    @field_validator("correlation_id")
    @classmethod
    def _validate_correlation_id(cls, value: str) -> str:
        """Validate and return a canonical correlation identifier.

        Args:
            value: Candidate correlation identifier.

        Returns:
            The validated identifier.

        Raises:
            ValueError: The identifier is not canonical.
        """
        return validate_trace_id(value, "cor", "correlation_id")

    @field_validator("issued_at")
    @classmethod
    def _validate_issued_at(cls, value: datetime) -> datetime:
        """Validate and return the issuance instant.

        Args:
            value: Candidate issuance timestamp.

        Returns:
            The same aware UTC timestamp.

        Raises:
            ValueError: The timestamp is naive or not UTC.
        """
        return validate_utc(value, "issued_at")

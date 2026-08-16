"""Shared immutable authentication-context contract."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils.contracts.audit import (
    validate_non_empty,
    validate_trace_id,
    validate_utc,
)


class AuthContext(BaseModel):
    """Immutable authenticated principal and trace context.

    Attributes:
        contract_version: The version string, either 'v1' or 'v2'.
        schema_id: The matching versioned schema identifier.
        principal_id: Unique identity of the authenticated user or service.
        principal_type: Categorization as USER or SERVICE_ACCOUNT.
        roles: Bounded unique roles assigned to the principal.
        permissions: Bounded unique fine-grained permissions.
        scopes: Bounded unique scopes requested/granted.
        tenant_or_environment: Namespace of the tenant or environment.
        runtime_profile: Separate execution-safety profile in version 2.
        request_id: Trace identifier of the outer request.
        workflow_id: Trace identifier tracking the orchestrating workflow.
        correlation_id: Trace identifier tracking the entire flow.
        issued_at: Aware UTC datetime representing token issuance.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["v1", "v2"]
    schema_id: Literal["utils.auth_context.v1", "utils.auth_context.v2"]
    principal_id: str
    principal_type: Literal["USER", "SERVICE_ACCOUNT"]
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    scopes: tuple[str, ...]
    tenant_or_environment: str
    runtime_profile: Literal["research", "simulation", "demo", "live"] | None = None
    request_id: str
    workflow_id: str
    correlation_id: str
    issued_at: datetime

    @model_validator(mode="after")
    def _validate_contract_version(self) -> AuthContext:
        """Require exact schema and runtime-profile semantics for each version.

        Returns:
            Validated authentication context.

        Raises:
            ValueError: If version, schema, and runtime profile do not agree.
        """
        if self.contract_version == "v1":
            if self.schema_id != "utils.auth_context.v1":
                raise ValueError("AuthContext v1 requires its v1 schema")
            if self.runtime_profile is not None:
                raise ValueError("AuthContext v1 cannot carry runtime_profile")
            return self
        if self.schema_id != "utils.auth_context.v2" or self.runtime_profile is None:
            message = "AuthContext v2 requires its v2 schema and runtime_profile"
            raise ValueError(message)
        return self

    @field_validator("principal_id", "tenant_or_environment")
    @classmethod
    def _validate_identity(cls, value: str, info: object) -> str:
        """Validate principal identity or environment string is non-empty.

        Args:
            value: The string value to validate.
            info: Validation context information.

        Returns:
            The validated non-empty string.
        """
        field_name = getattr(info, "field_name", "contract field")
        return validate_non_empty(value, str(field_name))

    @field_validator("roles", "permissions", "scopes")
    @classmethod
    def _validate_string_tuple(
        cls,
        value: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        """Validate that the string tuple is non-empty and has no duplicates.

        Args:
            value: The tuple of strings to validate.
            info: Validation context information.

        Returns:
            The validated tuple of non-empty strings.

        Raises:
            ValueError: If there are duplicate items in the tuple.
        """
        field_name = str(getattr(info, "field_name", "contract tuple"))
        if len(set(value)) != len(value):
            message = f"{field_name} must not contain duplicates"
            raise ValueError(message)
        return tuple(validate_non_empty(item, field_name) for item in value)

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate the canonical request trace identifier.

        Args:
            value: Trace identifier to validate.

        Returns:
            The validated trace identifier string.
        """
        return validate_trace_id(value, "req", "request_id")

    @field_validator("workflow_id")
    @classmethod
    def _validate_workflow_id(cls, value: str) -> str:
        """Validate the canonical workflow trace identifier.

        Args:
            value: Trace identifier to validate.

        Returns:
            The validated trace identifier string.
        """
        return validate_trace_id(value, "wf", "workflow_id")

    @field_validator("correlation_id")
    @classmethod
    def _validate_correlation_id(cls, value: str) -> str:
        """Validate the canonical correlation trace identifier.

        Args:
            value: Trace identifier to validate.

        Returns:
            The validated trace identifier string.
        """
        return validate_trace_id(value, "cor", "correlation_id")

    @field_validator("issued_at")
    @classmethod
    def _validate_issued_at(cls, value: datetime) -> datetime:
        """Validate that the issuance time is timezone-aware and set to UTC.

        Args:
            value: The datetime to validate.

        Returns:
            The validated UTC datetime.
        """
        return validate_utc(value, "issued_at")


def create_auth_context(
    *,
    principal_id: str,
    principal_type: Literal["USER", "SERVICE_ACCOUNT"],
    roles: tuple[str, ...],
    permissions: tuple[str, ...],
    scopes: tuple[str, ...],
    tenant_or_environment: str,
    runtime_profile: Literal["research", "simulation", "demo", "live"] | None = None,
    request_id: str,
    workflow_id: str,
    correlation_id: str,
    issued_at: datetime,
    contract_version: Literal["v1", "v2"] = "v1",
    schema_id: Literal[
        "utils.auth_context.v1", "utils.auth_context.v2"
    ] = "utils.auth_context.v1",
) -> AuthContext:
    """Construct an immutable AuthContext instance.

    Args:
        principal_id: Unique identity of the authenticated user or service.
        principal_type: Categorization as USER or SERVICE_ACCOUNT.
        roles: Bounded unique roles assigned to the principal.
        permissions: Bounded unique fine-grained permissions.
        scopes: Bounded unique scopes requested/granted.
        tenant_or_environment: Namespace of the tenant or environment.
        runtime_profile: Separate execution-safety profile required by version 2.
        request_id: Trace identifier of the outer request.
        workflow_id: Trace identifier tracking the orchestrating workflow.
        correlation_id: Trace identifier tracking the entire flow.
        issued_at: Aware UTC datetime representing token issuance.
        contract_version: Version string, either 'v1' or 'v2'.
        schema_id: Matching versioned schema identifier.

    Returns:
        Validated immutable AuthContext instance.
    """
    return AuthContext(
        contract_version=contract_version,
        schema_id=schema_id,
        principal_id=principal_id,
        principal_type=principal_type,
        roles=roles,
        permissions=permissions,
        scopes=scopes,
        tenant_or_environment=tenant_or_environment,
        runtime_profile=runtime_profile,
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        issued_at=issued_at,
    )

"""Shared immutable authentication-context contract."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.utils.contracts.audit import (
    validate_non_empty,
    validate_trace_id,
    validate_utc,
)


class AuthContext(BaseModel):
    """Immutable authenticated principal and trace context version 1."""

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
        field_name = getattr(info, "field_name", "contract field")
        return validate_non_empty(value, str(field_name))

    @field_validator("roles", "permissions", "scopes")
    @classmethod
    def _validate_string_tuple(
        cls,
        value: tuple[str, ...],
        info: object,
    ) -> tuple[str, ...]:
        field_name = str(getattr(info, "field_name", "contract tuple"))
        if len(set(value)) != len(value):
            message = f"{field_name} must not contain duplicates"
            raise ValueError(message)
        return tuple(validate_non_empty(item, field_name) for item in value)

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        return validate_trace_id(value, "req", "request_id")

    @field_validator("workflow_id")
    @classmethod
    def _validate_workflow_id(cls, value: str) -> str:
        return validate_trace_id(value, "wf", "workflow_id")

    @field_validator("correlation_id")
    @classmethod
    def _validate_correlation_id(cls, value: str) -> str:
        return validate_trace_id(value, "cor", "correlation_id")

    @field_validator("issued_at")
    @classmethod
    def _validate_issued_at(cls, value: datetime) -> datetime:
        return validate_utc(value, "issued_at")

"""Private immutable contracts for durable Trading execution sessions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

type SessionMode = Literal["sim", "demo", "live"]
type SessionState = Literal[
    "draft",
    "stopped",
    "starting",
    "running",
    "stopping",
    "recovery_required",
    "verified",
    "error",
    "archived",
]


class _SessionRecord(BaseModel):
    """Validated durable execution-session projection."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    session_id: str
    principal_id: str
    environment_id: str
    name: str
    description: str = ""
    mode: SessionMode
    provider: str
    provider_account_ref: str | None = None
    credential_ref: str | None = None
    simulation_session_id: str | None = None
    sim_sequence: int | None = Field(default=None, ge=1)
    simulation_runtime_ref: str | None = None
    dataset_ref: str | None = None
    dataset_revision: str | None = None
    dataset_hash: str | None = None
    sim_initial_balance: Decimal | None = None
    sim_leverage: int | None = Field(default=None, ge=1, le=1000)
    sim_account_currency: str | None = None
    lifecycle_state: SessionState = "stopped"
    recovery_state: str = "not_required"
    is_default: bool = False
    is_active: bool = False
    auto_start: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)
    last_error_code: str | None = None
    last_reconciled_at: datetime | None = None
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    archived_at: datetime | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime

    @field_validator("session_id", "principal_id", "environment_id", "name", "provider")
    @classmethod
    def _require_text(cls, value: str) -> str:
        """Require nonempty, already-trimmed identity text.

        Args:
            value: Identity string to validate.

        Returns:
            Validated identity string.

        Raises:
            ValueError: If string is empty or not trimmed.
        """
        if not value or value != value.strip():
            raise ValueError("session identity text is invalid")
        return value

    @field_validator("sim_initial_balance")
    @classmethod
    def _validate_sim_balance(cls, value: Decimal | None) -> Decimal | None:
        """Require a finite positive SIM opening balance when supplied.

        Args:
            value: Balance Decimal or None.

        Returns:
            Validated balance Decimal or None.

        Raises:
            ValueError: If balance is not finite or <= 0.
        """
        if value is not None and (not value.is_finite() or value <= 0):
            raise ValueError("SIM initial balance must be finite and positive")
        return value

    @field_validator("sim_account_currency")
    @classmethod
    def _validate_sim_currency(cls, value: str | None) -> str | None:
        """Require an uppercase ISO-style account currency when supplied.

        Args:
            value: Currency string or None.

        Returns:
            Validated currency string or None.

        Raises:
            ValueError: If currency is not 3 uppercase letters.
        """
        iso_currency_length = 3
        if value is not None and (
            len(value) != iso_currency_length
            or not value.isalpha()
            or value != value.upper()
        ):
            raise ValueError("SIM account currency must be three uppercase letters")
        return value


class _SessionEvent(BaseModel):
    """Immutable session lifecycle event."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    event_id: str
    session_id: str
    sequence: int = Field(ge=0)
    event_type: str
    payload: dict[str, str] = Field(default_factory=dict)
    occurred_at: datetime
    request_id: str


__all__: list[str] = []

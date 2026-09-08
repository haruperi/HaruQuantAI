"""Public contract for Agentic operations, containment, and replay validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable


class ReadinessStatus(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    CONTAINED = "CONTAINED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class OperationRecord:
    operation_id: str
    workspace_path: Path
    account_id: str
    correlation_id: str
    event_class: str
    safe_payload: str
    artifact_refs: tuple[str, ...] = ()
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ContainmentDecision:
    decision_id: str
    workspace_path: Path
    account_id: str
    status: ReadinessStatus
    reason_code: str
    generation: int
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ReadinessQuery:
    workspace_path: Path
    account_id: str


@dataclass(frozen=True, slots=True)
class ReadinessView:
    status: ReadinessStatus
    reason_code: str
    generation: int
    checked_at: datetime


@dataclass(frozen=True, slots=True)
class ReplayValidationRequest:
    workspace_path: Path
    account_id: str
    expected_refs: tuple[tuple[str, str], ...]
    observed_refs: tuple[tuple[str, str], ...]
    side_effect_free: bool = True


@dataclass(frozen=True, slots=True)
class ReplayDecision:
    eligible: bool
    reason_codes: tuple[str, ...]
    checked_at: datetime


@runtime_checkable
class AgenticOperationsCapability(Protocol):
    async def record_operation(self, record: OperationRecord) -> OperationRecord: ...
    async def contain(self, decision: ContainmentDecision) -> ReadinessView: ...
    async def readiness(self, query: ReadinessQuery) -> ReadinessView: ...
    async def validate_replay(self, request: ReplayValidationRequest) -> ReplayDecision: ...


__all__ = [
    "AgenticOperationsCapability", "ContainmentDecision", "OperationRecord", "ReadinessQuery",
    "ReadinessStatus", "ReadinessView", "ReplayDecision", "ReplayValidationRequest",
]

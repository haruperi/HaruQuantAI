"""Immutable contracts for simulation checklists and mission outcomes."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ChecklistStepState = Literal[
    "LOCKED",
    "AVAILABLE",
    "ACTIVE",
    "SATISFIED",
    "FAILED",
    "BLOCKED",
    "BYPASSED",
    "REGRESSED",
]
SimulationMode = Literal["Guided", "Standard", "Expert", "Challenge"]


class ChecklistStepDefinition(BaseModel):
    """One declarative checklist step bound to actual-state evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    step_id: str = Field(min_length=1, max_length=100)
    evidence_key: str = Field(min_length=1, max_length=200)
    comparator: Literal["eq", "ne", "gte", "lte", "truthy"]
    expected: bool | int | str | None = None
    prerequisites: tuple[str, ...] = ()
    mandatory: bool = True

    @field_validator("step_id", "evidence_key")
    @classmethod
    def _strip_identifiers(cls, value: str) -> str:
        """Reject surrounding whitespace in stable identifiers."""
        if value != value.strip():
            raise ValueError("checklist identifiers must not contain outer whitespace")
        return value

    @model_validator(mode="after")
    def _validate_predicate(self) -> ChecklistStepDefinition:
        """Validate comparator and prerequisite relationships."""
        if self.comparator == "truthy" and self.expected is not None:
            raise ValueError("truthy checklist predicates do not accept expected")
        if self.comparator != "truthy" and self.expected is None:
            raise ValueError("checklist predicate requires expected evidence")
        if self.step_id in self.prerequisites:
            raise ValueError("a checklist step cannot depend on itself")
        if len(set(self.prerequisites)) != len(self.prerequisites):
            raise ValueError("checklist prerequisites must be unique")
        return self


class ChecklistDefinition(BaseModel):
    """One immutable ordered checklist definition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checklist_id: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    steps: tuple[ChecklistStepDefinition, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def _validate_graph(self) -> ChecklistDefinition:
        """Require unique steps and prerequisites that precede their consumer."""
        known: set[str] = set()
        for step in self.steps:
            if step.step_id in known:
                raise ValueError("checklist step identities must be unique")
            if not set(step.prerequisites) <= known:
                raise ValueError("checklist prerequisites must precede their step")
            known.add(step.step_id)
        return self


class ChecklistStepRuntime(BaseModel):
    """Current state and bounded evidence for one checklist step."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    step_id: str
    state: ChecklistStepState
    evidence: bool | int | str | None = None
    reason: str | None = Field(default=None, max_length=500)


class ChecklistRuntime(BaseModel):
    """Immutable runtime projection of one checklist execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checklist_id: str
    version: str
    mode: SimulationMode
    steps: tuple[ChecklistStepRuntime, ...]


class MissionOutcome(BaseModel):
    """Deterministic completion result for one simulation mission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["PASSED", "FAILED", "INCOMPLETE"]
    reason: str
    safe_stand_down: bool
    satisfied_steps: int = Field(ge=0)
    required_steps: int = Field(ge=0)


def build_checklist_definition(**fields: object) -> ChecklistDefinition:
    """Build one validated checklist definition.

    Args:
        **fields: Checklist definition fields.

    Returns:
        Validated immutable definition.
    """
    return ChecklistDefinition.model_validate(fields)


def parse_checklist_runtime(value: Mapping[str, object]) -> ChecklistRuntime:
    """Parse one JSON-safe checklist runtime.

    Args:
        value: Runtime mapping.

    Returns:
        Validated immutable runtime.
    """
    return ChecklistRuntime.model_validate(value)


__all__ = [
    "ChecklistDefinition",
    "ChecklistRuntime",
    "ChecklistStepDefinition",
    "ChecklistStepRuntime",
    "MissionOutcome",
    "build_checklist_definition",
    "parse_checklist_runtime",
]

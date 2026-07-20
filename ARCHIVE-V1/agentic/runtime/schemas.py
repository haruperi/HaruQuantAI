"""Small shared schemas for early agent handoffs."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Common status values returned by lightweight agents."""

    SUCCESS = "success"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"
    FAILED = "failed"


class SimpleAgentResult(BaseModel):
    """Minimal structured result for early workflows."""

    agent_name: str
    status: AgentStatus
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    next_step: str | None = None


class ResearchEvidencePack(BaseModel):
    """Minimal research handoff package."""

    symbol: str
    timeframe: str
    summary: str
    observations: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StrategySpec(BaseModel):
    """Minimal strategy specification for validation handoff."""

    name: str
    symbol: str
    timeframe: str
    direction: str
    entry_rules: list[str]
    exit_rules: list[str]
    risk_rules: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

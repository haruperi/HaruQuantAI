"""Shadow-mode execution gating.

Classes and functions:
    ShadowExecutionRequest: Class. Provides ShadowExecutionRequest behavior for execution workflows.
    ShadowExecutionDecision: Class. Provides ShadowExecutionDecision behavior for execution workflows.
    ShadowExecutionService: Class. Provides ShadowExecutionService behavior for execution workflows.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agentic.contracts.execution_intent.model import ExecutionIntent
from app.services.execution import BrokerSendResult, ExecutionSendService


@dataclass(frozen=True)
class ShadowExecutionRequest:
    """Execution request with an explicit shadow-mode flag."""

    intent: ExecutionIntent
    shadow_enabled: bool


@dataclass(frozen=True)
class ShadowExecutionDecision:
    """Stable shadow execution outcome."""

    blocked_side_effects: bool
    result: BrokerSendResult | None
    reason: str


class ShadowExecutionService:
    """Fail-closed execution gate for production-like shadow workflows."""

    def __init__(self, send_service: ExecutionSendService) -> None:
        self._send_service = send_service

    def execute(self, request: ShadowExecutionRequest) -> ShadowExecutionDecision:
        """Perform the execute execution service operation."""
        if request.shadow_enabled:
            return ShadowExecutionDecision(
                blocked_side_effects=True,
                result=None,
                reason="shadow_mode_blocks_broker_side_effects",
            )
        return ShadowExecutionDecision(
            blocked_side_effects=False,
            result=self._send_service.send(request.intent),
            reason="live_send_allowed",
        )

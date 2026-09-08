"""Public provider-neutral structured model invocation contract."""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol, runtime_checkable
from app.contracts.agentic.mandate import FirmMandate
from app.contracts.agentic.roles import RoleEligibilityRequest

@dataclass(frozen=True, slots=True)
class ModelProfile:
    profile_id: str
    provider_id: str
    model_id: str
    profile_digest: str
    max_input_tokens: int
    max_output_tokens: int
    max_calls: int
    max_cost: Decimal
    timeout_seconds: float
    task_scope: str
    privacy_region: str
    retention_policy: str

@dataclass(frozen=True, slots=True)
class ModelInvocationRequest:
    request_id: str
    workspace_path: Path
    account_id: str
    mandate: FirmMandate
    role_request: RoleEligibilityRequest
    profile: ModelProfile
    fallbacks: tuple[ModelProfile, ...]
    prompt_hash: str
    composite_hash: str
    context_hash: str
    output_schema: str
    payload: dict[str, object]

@dataclass(frozen=True, slots=True)
class ModelUsage:
    input_tokens: int | None
    output_tokens: int | None
    observed_cost: Decimal | None

@dataclass(frozen=True, slots=True)
class ProviderModelResult:
    provider_id: str
    model_id: str
    payload: dict[str, object]
    usage: ModelUsage
    provenance_ref: str

@dataclass(frozen=True, slots=True)
class ModelInvocationResult:
    profile_id: str
    provider_id: str
    model_id: str
    payload: dict[str, object]
    usage: ModelUsage
    provenance_ref: str

@runtime_checkable
class ModelRuntimeProvider(Protocol):
    async def invoke(self, profile: ModelProfile, payload: dict[str, object]) -> ProviderModelResult: ...

@runtime_checkable
class ModelInferenceCapability(Protocol):
    async def register_provider(self, provider_id: str, provider: ModelRuntimeProvider, generation: int) -> None: ...
    async def invoke_model(self, request: ModelInvocationRequest) -> ModelInvocationResult: ...

__all__=["ModelInferenceCapability","ModelInvocationRequest","ModelInvocationResult","ModelProfile","ModelRuntimeProvider","ModelUsage","ProviderModelResult"]

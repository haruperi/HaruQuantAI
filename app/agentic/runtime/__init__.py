"""Public `FEAT-AGT-03` runtime and provider-neutral model API."""

from app.agentic.runtime.adk import (
    AdkRuntime,
    build_deterministic_adk_runtime,
    build_deterministic_model_gateway,
)
from app.agentic.runtime.gateway import ModelGateway, invoke_model
from app.agentic.runtime.models import (
    ModelInvocation,
    ModelOutcome,
    ModelProfile,
    build_model_invocation,
    build_model_profile,
    derive_profile_digest,
)
from app.agentic.runtime.upgrades import (
    get_required_upgrade_gates,
    validate_model_upgrade,
)

__all__: tuple[str, ...] = (
    "AdkRuntime",
    "ModelGateway",
    "ModelInvocation",
    "ModelOutcome",
    "ModelProfile",
    "build_deterministic_adk_runtime",
    "build_deterministic_model_gateway",
    "build_model_invocation",
    "build_model_profile",
    "derive_profile_digest",
    "get_required_upgrade_gates",
    "invoke_model",
    "validate_model_upgrade",
)

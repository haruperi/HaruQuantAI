"""Agent-graph runtime boundary.

`AdkRuntime` is the HaruQuantAI-owned port through which orchestration executes
one provider-neutral agent node. It is the *only* place a Google ADK binding
may ever be constructed, so no ADK or provider object can reach an Agentic
public contract or a persisted canonical record.

This module supplies three things: the port, a deterministic in-repo runtime
used by tests and usage programs, and the concrete Google ADK 2.x binding.
Google ADK is imported lazily inside the binding, so importing `app.agentic`
never loads an ADK or provider module.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from decimal import Decimal
from time import perf_counter_ns
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.runtime.gateway import invoke_model
from app.agentic.runtime.models import ModelOutcome
from app.composition.logging import get_logger

if TYPE_CHECKING:
    from google.adk import Agent as AdkAgent
    from google.genai import types as genai_types

    from app.agentic.runtime.gateway import ModelGateway
    from app.agentic.runtime.models import ModelInvocation, ModelProfile

logger = get_logger(__name__)


@runtime_checkable
class AdkRuntime(Protocol):
    """Executes one provider-neutral agent node."""

    def execute_node(
        self,
        node_id: str,
        profile: ModelProfile,
        invocation: ModelInvocation,
    ) -> ModelOutcome:
        """Execute one registered workflow node.

        Args:
            node_id: Registered workflow node identity.
            profile: Pinned evaluated model profile.
            invocation: Bounded governed invocation.

        Returns:
            The normalized provider-neutral outcome.
        """
        ...


class _DeterministicAdkRuntime:
    """Reproducible in-repo runtime satisfying the `AdkRuntime` port.

    Delegates to an injected `ModelGateway` through the governed
    `invoke_model` path, so profile bounds and substitution detection are
    exercised exactly as they will be under the real binding.
    """

    def __init__(self, gateway: ModelGateway) -> None:
        """Store the injected provider adapter.

        Args:
            gateway: Injected provider adapter.
        """
        self._gateway = gateway

    def execute_node(
        self,
        node_id: str,
        profile: ModelProfile,
        invocation: ModelInvocation,
    ) -> ModelOutcome:
        """Execute one registered workflow node deterministically.

        Args:
            node_id: Registered workflow node identity.
            profile: Pinned evaluated model profile.
            invocation: Bounded governed invocation.

        Returns:
            The normalized provider-neutral outcome.
        """
        logger.debug("Executing Agentic node %s deterministically", node_id)
        return invoke_model(self._gateway, profile, invocation)


class _ScriptedModelGateway:
    """Deterministic gateway returning pre-declared outcomes by invocation."""

    def __init__(self, outcomes: Mapping[str, ModelOutcome]) -> None:
        """Store the scripted outcomes.

        Args:
            outcomes: Invocation identity to declared outcome.
        """
        self._outcomes = dict(outcomes)

    def invoke(
        self,
        profile: ModelProfile,
        invocation: ModelInvocation,
    ) -> ModelOutcome:
        """Return the declared outcome for one invocation.

        Args:
            profile: Pinned evaluated model profile.
            invocation: Bounded governed invocation.

        Returns:
            The declared provider-neutral outcome.

        Raises:
            ValueError: If no outcome was declared for the invocation.
        """
        del profile
        outcome = self._outcomes.get(invocation.invocation_id)
        if outcome is None:
            message = f"no scripted outcome for invocation {invocation.invocation_id}"
            raise ValueError(message)
        return outcome


def build_deterministic_model_gateway(
    outcomes: Mapping[str, ModelOutcome],
) -> ModelGateway:
    """Build a deterministic gateway returning declared outcomes.

    Args:
        outcomes: Invocation identity to declared outcome.

    Returns:
        A gateway satisfying the `ModelGateway` port.
    """
    logger.debug("Building a deterministic Agentic model gateway")
    return _ScriptedModelGateway(outcomes)


def build_deterministic_adk_runtime(gateway: ModelGateway) -> AdkRuntime:
    """Build the deterministic in-repo agent-graph runtime.

    Args:
        gateway: Injected provider adapter.

    Returns:
        A runtime satisfying the `AdkRuntime` port.
    """
    logger.debug("Building the deterministic Agentic agent-graph runtime")
    return _DeterministicAdkRuntime(gateway)


# --------------------------------------------------------------------------
# Google ADK 2.x binding
#
# This is the only place in the repository that constructs a Google ADK object,
# and ADK is imported lazily inside these methods so that importing
# `app.agentic` never loads a provider module. Nothing below crosses the
# Agentic public boundary: `execute_node` returns a HaruQuantAI `ModelOutcome`
# and nothing else.
# --------------------------------------------------------------------------

_DEFAULT_APP_NAME = "haruquant-agentic"
_TOKENS_PER_PRICE_UNIT = Decimal(1000)


def _derive_cost(
    profile: ModelProfile,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    """Derive the observed cost of one call from reported token usage.

    An unpriced profile raises rather than reporting zero: a false zero would
    silently defeat the `max_cost_per_call` ceiling `invoke_model` enforces.

    Args:
        profile: Pinned evaluated model profile.
        input_tokens: Reported input tokens.
        output_tokens: Reported output tokens.

    Returns:
        The exact observed cost.

    Raises:
        ValueError: If the profile declares no token pricing.
    """
    if profile.cost_per_1k_input is None or profile.cost_per_1k_output is None:
        message = (
            f"model profile {profile.profile_id} declares no token pricing; "
            "an observed cost cannot be derived and must not be reported as zero"
        )
        raise ValueError(message)
    return (
        profile.cost_per_1k_input * Decimal(input_tokens) / _TOKENS_PER_PRICE_UNIT
        + profile.cost_per_1k_output * Decimal(output_tokens) / _TOKENS_PER_PRICE_UNIT
    )


def _structured_output(text: str) -> dict[str, str]:
    """Adapt one provider text response into the flat output contract.

    Agentic roles consume `dict[str, str]` with prefixed keys. The adapter
    absorbs the shape difference, so no agent or test changes when the binding
    replaces the deterministic double.

    Args:
        text: Raw provider response text.

    Returns:
        A flat string mapping.
    """
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            logger.warning("Provider response was not valid JSON; keeping raw text")
        else:
            if isinstance(parsed, dict):
                return {str(key): str(value) for key, value in parsed.items()}
    return {"text": stripped}


class _AdkBoundRuntime:
    """The Google ADK 2.x implementation of the `AdkRuntime` port.

    Instruction text is supplied by the composition root, which has already
    loaded and hash-verified each package-local `prompt.md`. This class never
    reads a prompt file and never accepts an unverified instruction.
    """

    def __init__(
        self,
        profile: ModelProfile,
        api_key: str,
        instructions: Mapping[str, str],
        app_name: str = _DEFAULT_APP_NAME,
    ) -> None:
        """Store the pinned profile, resolved credential, and instructions.

        Args:
            profile: Pinned evaluated model profile.
            api_key: Resolved provider credential, held in memory only.
            instructions: Registered role identity to verified instruction.
            app_name: ADK application name for session scoping.
        """
        self._profile = profile
        self._api_key = api_key
        self._instructions = dict(instructions)
        self._app_name = app_name

    def _build_agent(self, node_id: str, invocation: ModelInvocation) -> AdkAgent:
        """Construct the ADK agent for one node.

        Args:
            node_id: Registered workflow node identity.
            invocation: Bounded governed invocation.

        Returns:
            A configured ADK agent.

        Raises:
            ValueError: If no verified instruction exists for the role.
        """
        from google.adk import Agent
        from google.adk.models import Gemini

        instruction = self._instructions.get(invocation.role_id)
        if instruction is None:
            message = (
                f"no verified instruction supplied for role {invocation.role_id}; "
                "the composition root must verify prompt integrity first"
            )
            raise ValueError(message)
        return Agent(
            name=node_id,
            model=Gemini(
                model=self._profile.model_identifier,
                client_kwargs={"api_key": self._api_key},
            ),
            instruction=instruction,
            description=f"HaruQuantAI Agentic role {invocation.role_id}",
        )

    def _build_message(self, invocation: ModelInvocation) -> genai_types.Content:
        """Build the ADK content payload for one invocation.

        Trusted context and untrusted evidence stay separately labelled in the
        payload, preserving the separation the context layer established.

        Args:
            invocation: Bounded governed invocation.

        Returns:
            An ADK content value carrying the payload.
        """
        from google.genai import types

        payload = json.dumps(
            {
                "trusted_context": dict(invocation.trusted_context),
                "untrusted_evidence": dict(invocation.untrusted_evidence),
            },
            sort_keys=True,
        )
        return types.Content(role="user", parts=[types.Part(text=payload)])

    async def _run(self, node_id: str, invocation: ModelInvocation) -> ModelOutcome:
        """Execute one node against the ADK runner.

        Args:
            node_id: Registered workflow node identity.
            invocation: Bounded governed invocation.

        Returns:
            The normalized provider-neutral outcome.
        """
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService

        session_service = InMemorySessionService()  # type: ignore[no-untyped-call]
        await session_service.create_session(
            app_name=self._app_name,
            user_id=invocation.task_id,
            session_id=invocation.invocation_id,
        )
        runner = Runner(
            agent=self._build_agent(node_id, invocation),
            app_name=self._app_name,
            session_service=session_service,
        )

        started = perf_counter_ns()
        text_parts: list[str] = []
        input_tokens = 0
        output_tokens = 0
        async for event in runner.run_async(
            user_id=invocation.task_id,
            session_id=invocation.invocation_id,
            new_message=self._build_message(invocation),
        ):
            usage = getattr(event, "usage_metadata", None)
            if usage is not None:
                input_tokens = getattr(usage, "prompt_token_count", 0) or input_tokens
                output_tokens = (
                    getattr(usage, "candidates_token_count", 0) or output_tokens
                )
            if event.is_final_response() and event.content is not None:
                for part in event.content.parts or ():
                    part_text = part.text
                    if part_text:
                        text_parts.append(part_text)
        latency_ms = (perf_counter_ns() - started) // 1_000_000
        cost = _derive_cost(self._profile, input_tokens, output_tokens)

        if not text_parts:
            logger.warning("Provider returned no content for node %s", node_id)
            return ModelOutcome(
                invocation_id=invocation.invocation_id,
                status="failed",
                output=None,
                reasons=("PROVIDER_RETURNED_NO_CONTENT",),
                provider=self._profile.provider,
                model_identifier=self._profile.model_identifier,
                tokens_used=input_tokens + output_tokens,
                latency_ms=latency_ms,
                cost=cost,
            )
        return ModelOutcome(
            invocation_id=invocation.invocation_id,
            status="ok",
            output=_structured_output("".join(text_parts)),
            reasons=(),
            provider=self._profile.provider,
            model_identifier=self._profile.model_identifier,
            tokens_used=input_tokens + output_tokens,
            latency_ms=latency_ms,
            cost=cost,
        )

    def execute_node(
        self,
        node_id: str,
        profile: ModelProfile,
        invocation: ModelInvocation,
    ) -> ModelOutcome:
        """Execute one registered workflow node through Google ADK.

        The ADK runner is asynchronous while this port is synchronous, so the
        call is bridged here. A caller already inside an event loop fails
        closed rather than deadlocking.

        Args:
            node_id: Registered workflow node identity.
            profile: Pinned evaluated model profile.
            invocation: Bounded governed invocation.

        Returns:
            The normalized provider-neutral outcome.

        Raises:
            ValueError: If the supplied profile differs from the bound profile,
                or the caller is already inside a running event loop.
        """
        if profile.profile_id != self._profile.profile_id:
            message = (
                f"runtime is bound to profile {self._profile.profile_id}; "
                f"refusing to serve {profile.profile_id}"
            )
            raise ValueError(message)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            message = (
                "the ADK binding bridges an asynchronous runner from a "
                "synchronous port and cannot be called from inside a running "
                "event loop"
            )
            raise ValueError(message)
        logger.info("Executing Agentic node %s through Google ADK", node_id)
        return asyncio.run(self._run(node_id, invocation))


def build_adk_runtime(
    profile: ModelProfile,
    api_key: str,
    instructions: Mapping[str, str],
    app_name: str = _DEFAULT_APP_NAME,
) -> AdkRuntime:
    """Build the Google ADK 2.x agent-graph runtime.

    Constructed only by an approved composition root, which resolves the
    provider credential and supplies instructions it has already hash-verified.
    The credential lives only for this runtime's lifetime and never enters a
    contract, a log, a provenance record, or an audit store.

    Args:
        profile: Pinned evaluated model profile.
        api_key: Resolved provider credential.
        instructions: Registered role identity to verified instruction.
        app_name: ADK application name for session scoping.

    Returns:
        A runtime satisfying the `AdkRuntime` port.

    Raises:
        ValueError: If the credential is blank or the profile is unpriced.
    """
    if not api_key or not api_key.strip():
        message = "a resolved provider credential is required"
        raise ValueError(message)
    if profile.cost_per_1k_input is None or profile.cost_per_1k_output is None:
        message = (
            f"model profile {profile.profile_id} must declare token pricing "
            "before it can serve a real provider call"
        )
        raise ValueError(message)
    logger.info("Building the Google ADK runtime for profile %s", profile.profile_id)
    return _AdkBoundRuntime(profile, api_key, instructions, app_name)

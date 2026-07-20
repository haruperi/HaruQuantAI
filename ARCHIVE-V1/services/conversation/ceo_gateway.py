"""Production CEO chat gateway for the global HaruQuant chat widget."""

from __future__ import annotations

import os
import re
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
from app.agentic.agents._shared.base_contracts import AgentContext, AgentRequest
from app.agentic.agents._shared.schemas import AgentPlan
from app.agentic.agents.executive.ceo_agent.service import CEOAgent
from app.agentic.agents.executive.planner_agent.service import PlannerAgent
from app.agentic.agents.research.news_sentiment_agent import NewsSentimentAgentService
from app.agentic.agents.research.shared.workflow import run_research_workflow_sync
from app.agentic.agents.runtime.tool_executor import (
    AIChatReadOnlyToolExecutor,
    ChatToolCall,
    tool_results_as_prompt,
)
from app.agentic.capabilities.tools.read_only import list_read_only_tool_definitions
from app.agentic.capabilities.tools.read_only.contracts import ReadOnlyToolResult
from app.agentic.config.agent_model import AGENT_MODEL
from app.services.conversation.context.service import ContextAssembler
from app.services.conversation.prompt_builder import PromptBuilder
from app.services.conversation.service import ConversationService
from app.services.conversation.stream_manager import (
    ModelConfigurationError,
    ModelRuntimeError,
    OpenAICompatibleStreamClient,
    StreamManager,
)
from app.services.schemas.chat import (
    ChatMessage,
    ChatResponseMetadata,
    ChatRouteDecision,
    ChatThreadDetail,
    ChatToolDefinition,
    ChatTurnRequest,
    ChatTurnResult,
    PageContext,
)


class CEOChatGateway:
    """Runs chat through the CEO and planner while preserving production streaming."""

    def __init__(
        self,
        conversation_service: ConversationService,
        *,
        planner: PlannerAgent | None = None,
        ceo: CEOAgent | None = None,
        context_assembler: ContextAssembler | None = None,
        prompt_builder: PromptBuilder | None = None,
        stream_manager: StreamManager | None = None,
        model_client: OpenAICompatibleStreamClient | None = None,
        tool_executor: AIChatReadOnlyToolExecutor | None = None,
    ) -> None:
        self.conversations = conversation_service
        self.planner = planner or PlannerAgent()
        self.ceo = ceo or CEOAgent()
        self.context_assembler = context_assembler or ContextAssembler()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.stream_manager = stream_manager or StreamManager()
        self.model_client = model_client or OpenAICompatibleStreamClient()
        self.tool_executor = tool_executor or AIChatReadOnlyToolExecutor()

    def handle_turn(
        self, *, thread_id: str, user_id: str, request: ChatTurnRequest
    ) -> ChatTurnResult:
        result: ChatTurnResult | None = None
        for event_name, data in self.stream_turn(
            thread_id=thread_id, user_id=user_id, request=request
        ):
            if event_name != "done":
                continue
            thread_payload = data.get("thread")
            message_payload = data.get("assistant_message")
            user_message_payload = data.get("user_message")
            metadata_payload = data.get("metadata")
            if thread_payload and message_payload and metadata_payload:
                result = ChatTurnResult(
                    thread=ChatThreadDetail(**thread_payload),  # type: ignore[arg-type]
                    user_message=ChatMessage(**user_message_payload)
                    if user_message_payload
                    else None,  # type: ignore[arg-type]
                    assistant_message=ChatMessage(**message_payload),  # type: ignore[arg-type]
                    metadata=ChatResponseMetadata(**metadata_payload),  # type: ignore[arg-type]
                )
        if result is None:
            raise RuntimeError("CEO chat gateway did not complete the turn.")
        return result

    def stream_turn(
        self, *, thread_id: str, user_id: str, request: ChatTurnRequest
    ) -> Iterator[tuple[str, dict[str, object]]]:
        started = time.perf_counter()
        request_id = request.request_id or f"chat-{uuid4()}"
        yield _progress_event(
            request_id=request_id,
            step=1,
            total=10,
            label="Received request",
            detail="Preparing CEO workflow.",
        )
        page_context = self.context_assembler.from_chat_request(request)
        yield _progress_event(
            request_id=request_id,
            step=2,
            total=10,
            label="Context assembled",
            detail=page_context.page_title
            or page_context.route
            or "Current workspace context loaded.",
        )
        self.conversations.update_context(
            thread_id=thread_id,
            user_id=user_id,
            current_route=page_context.route,
            current_page_type=page_context.page_type,
            active_context_revision=page_context.context_revision,
        )
        thread = self.conversations.get_thread(thread_id=thread_id, user_id=user_id)
        existing_request_ids = {
            message.request_id for message in thread.messages if message.request_id
        }
        should_persist_user_message = request_id not in existing_request_ids
        effective_request = _request_with_pending_research_context(
            request=request, thread=thread
        )
        if effective_request.prompt != request.prompt:
            yield _progress_event(
                request_id=request_id,
                step=2,
                total=10,
                label="Continuation resolved",
                detail="Merged supplied data window with pending Research request.",
            )

        plan = self.planner.create_plan(
            user_request=effective_request.prompt, request_id=request_id
        )
        yield _progress_event(
            request_id=request_id,
            step=3,
            total=10,
            label="Planner route selected",
            detail=f"{plan.intent}"
            + (f" / {plan.workflow_id}" if plan.workflow_id else ""),
        )
        route = _route_from_plan(
            plan=plan,
            request=effective_request,
            page_context=page_context,
            ceo=self.ceo,
        )
        yield _progress_event(
            request_id=request_id,
            step=4,
            total=10,
            label="Tool plan prepared",
            detail="Selecting read-only evidence tools.",
        )
        tool_results = self.tool_executor.execute(
            _planned_read_only_tool_calls(
                planner=self.planner,
                request=effective_request,
                plan=plan,
                page_context=page_context,
                thread_id=thread_id,
                user_id=user_id,
            )
        )
        yield _progress_event(
            request_id=request_id,
            step=5,
            total=10,
            label="Evidence tools completed",
            detail=_tool_progress_detail(tool_results),
        )
        if plan.needs_clarification:
            yield _progress_event(
                request_id=request_id,
                step=10,
                total=10,
                label="Waiting for required input",
                detail=", ".join(plan.missing_inputs)
                or "More detail is required before agents run.",
                status="needs_input",
            )
        elif plan.intent == "research" and _has_successful_market_data(tool_results):
            yield _progress_event(
                request_id=request_id,
                step=6,
                total=10,
                label="Running Research agents",
                detail="Specialists are processing MT5-backed evidence.",
            )
        agent_outputs = self._build_agent_outputs(
            plan=plan,
            page_context=page_context,
            tool_results=tool_results,
            request_id=request_id,
        )
        if "news_sentiment_agent" in agent_outputs:
            memo = _news_sentiment_completed_memo(
                request=effective_request,
                plan=plan,
                agent_outputs=agent_outputs,
            )
        elif "research_workflow" in agent_outputs:
            memo = _research_completed_memo(
                request=effective_request,
                plan=plan,
                agent_outputs=agent_outputs,
                tool_results=tool_results,
            )
        else:
            memo = (
                self.ceo.page_identity_memo(
                    request=effective_request.prompt, page_context=page_context
                )
                if _is_page_identity_question(effective_request.prompt)
                else self.ceo.create_final_memo(
                    request=effective_request.prompt,
                    planner_result=plan,
                    agent_outputs=agent_outputs,
                    evidence_refs=self._evidence_refs(plan, page_context, tool_results),
                )
            )
        if "news_sentiment_agent" in agent_outputs:
            yield _progress_event(
                request_id=request_id,
                step=7,
                total=10,
                label="Specialist agent completed",
                detail="News Sentiment report assembled.",
            )
        elif "research_workflow" in agent_outputs:
            yield _progress_event(
                request_id=request_id,
                step=7,
                total=10,
                label="Research agents completed",
                detail="Research workflow package assembled.",
            )
        research_evidence_pending = _research_market_evidence_pending(
            plan=plan, tool_results=tool_results
        )
        if research_evidence_pending:
            memo = _research_evidence_pending_memo(
                request=effective_request, plan=plan, tool_results=tool_results
            )
            yield _progress_event(
                request_id=request_id,
                step=10,
                total=10,
                label="Waiting for market evidence",
                detail="Current market metrics were not available, so Research did not run.",
                status="needs_input",
            )
        route.response_mode = self.ceo.response_mode_for_memo(plan=plan, memo=memo)
        route.structured_schema = route.response_mode
        yield _progress_event(
            request_id=request_id,
            step=8,
            total=10,
            label="Composing CEO response",
            detail=route.response_mode,
        )
        prompt = self.prompt_builder.build(
            request=effective_request,
            request_id=request_id,
            thread=thread,
            page_context=page_context,
            route=route,
            tool_evidence=tool_results_as_prompt(tool_results)
            if tool_results
            else None,
        )
        ceo_state_content = (
            "CEO/planner state for this turn. The user is talking to the CEO. "
            "Use this plan and memo as the executive routing contract.\n"
            f"planner={plan.model_dump()}\nceo_memo={memo}\nresearch_outputs={_research_outputs_for_prompt(agent_outputs)}"
        )
        prompt.messages.insert(
            1,
            {
                "role": "system",
                "content": ceo_state_content,
            },
        )
        prompt.composition.message_count = len(prompt.messages)
        prompt.composition.token_estimate += max(1, len(ceo_state_content) // 4)
        model = self._select_model(route)
        deterministic_block = (
            plan.intent
            in {"planner_direct_call_blocked", "specialist_direct_call_blocked"}
            or memo.get("memo_type") == "live_strategy_blocked"
        )
        use_model = (
            self._should_use_model(model=model)
            and not research_evidence_pending
            and not deterministic_block
        )
        metadata = self._metadata(
            request_id=request_id,
            plan=plan,
            route=route,
            memo=memo,
            page_context=page_context,
            model=model or "fallback",
            prompt_composition=prompt.composition.model_dump(),
            generation_source="llm_runtime" if use_model else "fallback",
            provider_name=self.model_client.provider_label_for_model(model or "")
            if use_model
            else None,
            attached_tools=request.attached_tools,
            tool_results=[result.model_dump() for result in tool_results],
            started=started,
        )
        metadata.deterministic_decision = _deterministic_decision_for_turn(
            plan=plan, route=route, llm_used=use_model
        )
        if not use_model:
            metadata.audit["degraded_reason"] = (
                "Research market evidence is pending, so the CEO returned a deterministic evidence-pending memo."
                if research_evidence_pending
                else "Direct internal-agent or live-execution requests are blocked by CEO governance, so the CEO returned a deterministic refusal memo."
                if deterministic_block
                else "CEO chat model is not configured. Set HARUQUANT_AGENT_MODEL and the matching "
                "GOOGLE_API_KEY, OPENAI_API_KEY, or local Ollama server in agentic/config/environments/.env."
            )

        user_message = (
            self.conversations.add_message(
                thread_id=thread_id,
                user_id=user_id,
                role="user",
                content=request.prompt,
                request_id=request_id,
                context_revision=page_context.context_revision,
            )
            if should_persist_user_message
            else next(
                message
                for message in reversed(thread.messages)
                if message.request_id == request_id and message.role == "user"
            )
        )

        yield "meta", metadata.model_dump()
        yield _progress_event(
            request_id=request_id,
            step=9,
            total=10,
            label="Streaming response",
            detail=metadata.generation_source,
        )

        assistant_parts: list[str] = []
        try:
            if use_model:
                retry_count = 0
                max_retries = int(os.getenv("HARUQUANT_CEO_CHAT_MAX_RETRIES", "1"))
                while True:
                    try:
                        for token in self.model_client.stream_chat(
                            messages=prompt.messages, model=model or ""
                        ):
                            assistant_parts.append(token)
                            yield "token", {"delta": token}
                        break
                    except (
                        httpx.HTTPError,
                        ModelConfigurationError,
                        ModelRuntimeError,
                        TimeoutError,
                    ):
                        if assistant_parts or retry_count >= max_retries:
                            raise
                        retry_count += 1
                        metadata.audit["retry_count"] = retry_count
                        time.sleep(min(0.5 * retry_count, 2.0))
            else:
                fallback = self._fallback_answer(
                    request=effective_request,
                    page_context=page_context,
                    route=route,
                    memo=memo,
                )
                for token in self.stream_manager.text_tokens(fallback):
                    assistant_parts.append(token)
                    yield "token", {"delta": token}
        except (
            httpx.HTTPError,
            ModelConfigurationError,
            ModelRuntimeError,
            TimeoutError,
        ) as exc:
            if assistant_parts:
                raise
            metadata.generation_source = "fallback"
            metadata.provider_name = None
            metadata.model = "fallback"
            metadata.audit["degraded_reason"] = str(exc)
            fallback = self._fallback_answer(
                request=effective_request,
                page_context=page_context,
                route=route,
                memo=memo,
                error=exc,
            )
            for token in self.stream_manager.text_tokens(fallback):
                assistant_parts.append(token)
                yield "token", {"delta": token}

        response_text = "".join(assistant_parts).strip()
        latency_ms = int((time.perf_counter() - started) * 1000)
        metadata.telemetry["latency_ms"] = latency_ms
        _apply_usage_and_cost_metadata(
            metadata=metadata,
            model_client=self.model_client,
            model=model or "",
            response_text=response_text,
        )

        assistant_message = self.conversations.add_message(
            thread_id=thread_id,
            user_id=user_id,
            role="assistant",
            content=response_text
            or "I could not produce a CEO response for this turn.",
            request_id=request_id,
            context_revision=page_context.context_revision,
            tool_calls=metadata.tools_used,
            metadata=metadata,
            latency_ms=latency_ms,
        )
        yield _progress_event(
            request_id=request_id,
            step=10,
            total=10,
            label="Complete",
            detail="CEO response saved.",
            status="completed",
        )
        yield (
            "done",
            {
                "message_id": assistant_message.message_id,
                "assistant_message": assistant_message.model_dump(),
                "user_message": user_message.model_dump(),
                "thread": self.conversations.get_thread(
                    thread_id=thread_id, user_id=user_id
                ).model_dump(),
                "metadata": metadata.model_dump(),
            },
        )

    def _build_agent_outputs(
        self,
        *,
        plan: AgentPlan,
        page_context: PageContext,
        tool_results: list[ReadOnlyToolResult],
        request_id: str,
    ) -> dict[str, object]:
        outputs: dict[str, object] = {
            "planner": plan.model_dump(),
            "page_context": page_context.model_dump(),
            "read_only_tools": [result.model_dump() for result in tool_results],
        }
        direct_specialist_output = _run_direct_specialist_agent(
            plan=plan, request_id=request_id
        )
        if direct_specialist_output is not None:
            outputs.update(direct_specialist_output)
            return outputs
        research_payload = _research_payload_from_market_data(
            plan=plan, tool_results=tool_results
        )
        if research_payload is not None:
            package = run_research_workflow_sync(
                AgentRequest(
                    request_id=request_id,
                    agent_name="research_orchestrator_agent",
                    task=plan.user_goal,
                    payload=research_payload,
                ),
                AgentContext(session_id=request_id),
            )
            outputs["research_workflow"] = {
                "research_execution_plan": package.research_execution_plan,
                "agent_routing_plan": package.agent_routing_plan,
                "agent_responses": {
                    name: response.model_dump()
                    for name, response in package.agent_responses.items()
                },
                "final_research_report": package.final_research_report,
                "research_to_strategy_handoff": package.research_to_strategy_handoff,
                "audit": package.audit,
            }
        return outputs

    def _evidence_refs(
        self,
        plan: AgentPlan,
        page_context: PageContext,
        tool_results: list[ReadOnlyToolResult],
    ) -> list[str]:
        refs = list(plan.evidence_requirements)
        if page_context.route:
            refs.append(f"ui:{page_context.route}")
        for result in tool_results:
            refs.extend(result.sources or [])
        return list(dict.fromkeys(refs))

    def _select_model(self, route: ChatRouteDecision) -> str | None:
        policy_key = route.model_policy_key or "fast"
        env_by_policy = {
            "fast": "HARUQUANT_AI_MODEL_FAST",
            "plain_answer": "HARUQUANT_AI_MODEL_FAST",
            "analysis": "HARUQUANT_AI_MODEL_ANALYSIS",
            "strong": "HARUQUANT_AI_MODEL_STRONG",
        }
        return (
            os.getenv(env_by_policy.get(policy_key, "HARUQUANT_AI_MODEL_FAST"))
            or os.getenv("HARUQUANT_CEO_CHAT_MODEL")
            or AGENT_MODEL
        )

    def _should_use_model(self, *, model: str | None) -> bool:
        disabled = os.getenv("HARUQUANT_CEO_CHAT_ENABLED", "true").lower() in {
            "0",
            "false",
            "no",
        }
        return bool(
            model and self.model_client.is_configured_for(model=model) and not disabled
        )

    def _metadata(
        self,
        *,
        request_id: str,
        plan: AgentPlan,
        route: ChatRouteDecision,
        memo: dict[str, object],
        page_context: PageContext,
        model: str,
        prompt_composition: dict[str, object],
        generation_source: str,
        provider_name: str | None,
        attached_tools: list[str],
        tool_results: list[dict[str, object]],
        started: float,
    ) -> ChatResponseMetadata:
        prompt_tokens = int(prompt_composition.get("token_estimate") or 0)
        tool_attachments = [
            {
                "tool_id": tool_id,
                "display_name": tool_id,
                "authority_band": "read_only",
                "side_effect_policy": "none",
                "capability_type": "operator_hint",
            }
            for tool_id in attached_tools
        ]
        return ChatResponseMetadata(
            request_id=request_id,
            response_mode=route.response_mode,
            response_style=route.response_style,
            task_class=route.task_class,
            domain_focus=route.domain_focus,
            answer_mode="ceo_agent_gateway",
            generation_source=generation_source,
            provider_name=provider_name,
            model=model,
            tools_used=[
                str(result.get("tool_name"))
                for result in tool_results
                if result.get("tool_name")
            ],
            conversation_plan_id=plan.conversation_plan_id,
            clarification_required=plan.needs_clarification,
            active_topic=plan.intent,
            specialist_agents_used=[
                agent for agent in plan.allowed_agents if agent != "ceo"
            ],
            specialist_artifacts=[
                {
                    "agent_name": "read_only_tool_executor",
                    "summary": str(result.get("summary") or result.get("tool_name")),
                    "findings": [f"status: {result.get('status')}"],
                    "sources": list(result.get("sources") or []),
                }
                for result in tool_results
            ],
            telemetry={
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": 0,
                "total_tokens": prompt_tokens,
                "cost_usd": 0.0,
            },
            cost_policy={
                "request_budget_key": f"ceo_chat_{route.model_policy_key}",
                "estimated_cost_usd": 0.0,
                "pricing_source": "pending_provider_usage",
                "budget_downgraded": False,
                "workflow_cost_usd": 0.0,
                "within_workflow_budget": True,
            },
            attached_tools=tool_attachments,
            ceo_memo=memo,
            planner=plan.model_dump(),
            page_context=page_context.model_dump(),
            audit={
                "event": "ceo_chat_turn",
                "trace_id": request_id,
                "policy_version": "ceo_governance_policy_v1",
                "prompt_version": "ceo_gateway_prompt_v1",
                "prompt_composition": prompt_composition,
                "context_revision_event": "context_revision_changed",
                "context_schema_version": page_context.context_schema_version,
                "context_revision": page_context.context_revision,
                "context_route": page_context.route,
                "context_page_type": page_context.page_type,
                "structured_schema": route.structured_schema,
                "stream_transport": "server_sent_events",
                "assistant_persisted_after_stream_complete": True,
                "regeneration_side_effect_policy": "read_only_no_tool_side_effects",
                "read_only_tool_calls": tool_results,
                "live_execution_enabled": False,
                "risk_governor_bypass_allowed": False,
            },
        )

    def _fallback_answer(
        self,
        *,
        request: ChatTurnRequest,
        page_context: PageContext,
        route: ChatRouteDecision,
        memo: dict[str, object],
        error: BaseException | None = None,
    ) -> str:
        title = str(
            (page_context.summary or {}).get("headline")
            or page_context.page_title
            or "Current page"
        )
        route_text = page_context.route or "/"
        if route.intent == "page_identity":
            return (
                f"You are on {title} ({page_context.page_type}) at route {route_text}."
            )
        direct_context_answer = _direct_context_answer(request.prompt, page_context)
        if direct_context_answer:
            return direct_context_answer
        memo_text = self.ceo.format_memo(memo=memo, page_context=page_context)
        if memo_text and memo_text != "CEO Agent prepared a governed firm workflow.":
            return memo_text
        degraded = (
            " The live model is not configured or temporarily unavailable, so this is a safe CEO fallback."
            if error
            else ""
        )
        bullets = [
            str(item)
            for item in list((page_context.summary or {}).get("bullets") or [])[:3]
        ]
        context_line = (
            f"Current page: {title} ({page_context.page_type}) at {route_text}."
        )
        if bullets:
            context_line += f" Visible context: {'; '.join(bullets)}."
        return (
            f"{context_line}{degraded}\n\n"
            "I can still use current page context, planner output, CEO governance boundaries, and read-only HaruQuant tools."
        )


def list_ceo_chat_tools() -> list[ChatToolDefinition]:
    return [
        ChatToolDefinition(
            tool_id=tool.tool_id,
            display_name=tool.display_name,
            description=tool.description,
            capability_type="haruquant_read_only",
            authority_band="read_only",
            side_effect_policy="none",
            input_schema=tool.input_schema,
            output_schema=tool.output_schema,
            required_context=[],
            allowed_backend_tools=[tool.tool_id],
            allowed_specialist_agents=["read_only_tool_executor", "ceo"],
            artifact_type="state_snapshot",
            required_user_ack=False,
        )
        for tool in list_read_only_tool_definitions()
    ]


def _route_from_plan(
    *,
    plan: AgentPlan,
    request: ChatTurnRequest,
    page_context: PageContext,
    ceo: CEOAgent,
) -> ChatRouteDecision:
    if _is_page_identity_question(request.prompt):
        return ChatRouteDecision(
            intent="page_identity",
            task_class="context_lookup",
            response_mode="page_aware_summary",
            response_style="summary",
            domain_focus=page_context.page_type,
            route_mode="plain_answer",
            model_policy_key="fast",
            structured_schema="page_context_answer",
        )
    response_mode = ceo.response_mode_for_memo(plan=plan)
    model_policy_key = (
        "strong" if plan.risk_level in {"medium", "high", "critical"} else "fast"
    )
    if plan.intent in {"backtest_diagnosis", "optimization_comparison"}:
        model_policy_key = "analysis"
    return ChatRouteDecision(
        intent=plan.intent,
        task_class=plan.task_class,
        response_mode=response_mode,
        response_style=_response_style(plan),
        domain_focus=page_context.page_type
        if page_context.page_type != "generic"
        else (plan.domain_focus or "trading"),
        route_mode="ceo_planner",
        requires_tools=bool(plan.backend_tools_to_run or plan.attached_tools),
        model_policy_key=model_policy_key,
        structured_schema=response_mode,
    )


def _response_style(plan: AgentPlan) -> str:
    if plan.needs_clarification:
        return "clarification"
    if plan.intent in {"risk_review", "execution_proposal", "governed_action_draft"}:
        return "warning"
    if plan.intent in {"backtest_diagnosis", "optimization_comparison"}:
        return "diagnostic"
    if plan.intent == "strategy_creation":
        return "recommendation"
    return "summary"


def _planned_read_only_tool_calls(
    *,
    planner: PlannerAgent,
    request: ChatTurnRequest,
    plan: AgentPlan,
    page_context: PageContext,
    thread_id: str,
    user_id: str,
) -> list[ChatToolCall]:
    names = planner.plan_read_only_tools(
        user_request=request.prompt, plan=plan, attached_tools=request.attached_tools
    )
    common = {
        "user_id": user_id,
        "thread_id": thread_id,
        "symbol": _entity_ref(page_context, "symbol")
        or _symbol_from_prompt(request.prompt),
        "timeframe": _entity_ref(page_context, "timeframe")
        or _timeframe_from_prompt(request.prompt),
        **_research_data_window_from_prompt(request.prompt),
        "strategy_id": _entity_ref(page_context, "strategy")
        or _entity_ref(page_context, "strategy_id"),
        "session_id": _session_id(page_context),
        "page_context": page_context.model_dump(),
        "reason": request.prompt[:300],
    }
    return [
        ChatToolCall(tool_call_id=f"tool-{name}", tool_name=name, parameters=common)
        for name in names
    ]


def _direct_context_answer(prompt: str, page_context: PageContext) -> str | None:
    lowered = " ".join(prompt.lower().strip().split())
    if "account login" in lowered or "login number" in lowered:
        value = _find_page_metric(page_context, labels=("account login", "login"))
        if value is not None:
            return f"The account login shown on this page is {value}."
    if "account server" in lowered or lowered == "server":
        value = _find_page_metric(page_context, labels=("account server", "server"))
        if value is not None:
            return f"The account server shown on this page is {value}."
    if "account name" in lowered:
        value = _find_page_metric(page_context, labels=("account name", "name"))
        if value is not None:
            return f"The account name shown on this page is {value}."
    return None


def _deterministic_decision_for_turn(
    *, plan: AgentPlan, route: ChatRouteDecision, llm_used: bool
) -> dict[str, object]:
    if plan.needs_clarification:
        return {
            "status": "clarification_required",
            "decision": "needs_more_context",
            "policy_version": "ceo_governance_policy_v1",
            "prompt_version": "ceo_gateway_prompt_v1",
            "llm_used": llm_used,
            "allowed_actions": ["ask_clarifying_question"],
            "blocked_actions": [
                "strategy_creator_agent",
                "backtest_agent",
                "risk_governor_review",
                "code_generation",
                "execution_workflow",
            ],
            "reasons": ["minimum_strategy_inputs_missing"],
            "missing_inputs": list(plan.missing_inputs),
        }
    if plan.intent == "planner_direct_call_blocked":
        return {
            "status": "blocked",
            "decision": "planner_direct_call_blocked",
            "policy_version": "ceo_governance_policy_v1",
            "prompt_version": "ceo_gateway_prompt_v1",
            "llm_used": llm_used,
            "allowed_actions": ["explain_governed_ceo_workflow"],
            "blocked_actions": [
                "planner_agent_direct_call",
                "strategy_creator_agent_direct_call",
            ],
            "reasons": ["planner_is_internal_not_user_callable"],
        }
    if plan.intent == "specialist_direct_call_blocked":
        return {
            "status": "blocked",
            "decision": "specialist_direct_call_blocked",
            "policy_version": "ceo_governance_policy_v1",
            "prompt_version": "ceo_gateway_prompt_v1",
            "llm_used": llm_used,
            "allowed_actions": ["request_research_through_ceo_workflow"],
            "blocked_actions": [
                "market_intelligence_agent_direct_call",
                "raw_specialist_output",
            ],
            "reasons": ["specialist_agents_are_internal_not_user_callable"],
        }
    if _requests_live_or_run_now(plan.user_goal):
        return {
            "status": "blocked",
            "decision": "live_execution_blocked",
            "policy_version": "ceo_governance_policy_v1",
            "prompt_version": "ceo_gateway_prompt_v1",
            "llm_used": llm_used,
            "allowed_actions": ["request_strategy_creation_through_ceo_workflow"],
            "blocked_actions": [
                "live_strategy_activation",
                "live_execution",
                "order_router",
                "broker_bridge",
                "side_effect_execution",
            ],
            "reasons": [
                "live_execution_requires_governed_lifecycle_risk_review_audit_and_board_approval"
            ],
            "missing_inputs": list(plan.missing_inputs),
        }
    blocked_actions = list(plan.blocked_agents or [])
    if route.response_mode == "blocked_by_policy":
        blocked_actions.extend(["live_execution", "side_effect_execution"])
    return {
        "status": "planned",
        "decision": plan.intent,
        "policy_version": "ceo_governance_policy_v1",
        "prompt_version": "ceo_gateway_prompt_v1",
        "llm_used": llm_used,
        "allowed_actions": list(plan.allowed_agents),
        "blocked_actions": list(dict.fromkeys(blocked_actions)),
        "reasons": [plan.rationale],
        "missing_inputs": list(plan.missing_inputs),
    }


def _apply_usage_and_cost_metadata(
    *,
    metadata: ChatResponseMetadata,
    model_client: OpenAICompatibleStreamClient,
    model: str,
    response_text: str,
) -> None:
    provider = model_client.provider_for_model(model) if model else ""
    usage = dict(getattr(model_client, "last_usage_metadata", {}) or {})
    if provider == "google" and usage:
        prompt_tokens = int(usage.get("prompt_token_count") or 0)
        candidate_tokens = int(usage.get("candidates_token_count") or 0)
        thought_tokens = int(usage.get("thoughts_token_count") or 0)
        completion_tokens = candidate_tokens + thought_tokens
        total_tokens = int(
            usage.get("total_token_count") or prompt_tokens + completion_tokens
        )
        metadata.telemetry.update(
            {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "candidate_tokens": candidate_tokens,
                "thought_tokens": thought_tokens,
                "cached_content_tokens": int(
                    usage.get("cached_content_token_count") or 0
                ),
                "total_tokens": total_tokens,
                "token_source": "gemini_usage_metadata",
            }
        )
    else:
        completion_tokens = max(1, len(response_text) // 4) if response_text else 0
        prompt_tokens = int(metadata.telemetry.get("prompt_tokens") or 0)
        metadata.telemetry.update(
            {
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "token_source": "prompt_and_response_length_estimate",
            }
        )

    prompt_tokens = int(metadata.telemetry.get("prompt_tokens") or 0)
    completion_tokens = int(metadata.telemetry.get("completion_tokens") or 0)
    cost_usd, pricing_source = _estimate_model_cost_usd(
        model=model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
    )
    workflow_budget = float(os.getenv("HARUQUANT_CEO_CHAT_WORKFLOW_BUDGET_USD", "0.05"))
    metadata.telemetry["cost_usd"] = cost_usd
    metadata.cost_policy["estimated_cost_usd"] = cost_usd
    metadata.cost_policy["workflow_cost_usd"] = cost_usd
    metadata.cost_policy["workflow_budget_usd"] = workflow_budget
    metadata.cost_policy["within_workflow_budget"] = cost_usd <= workflow_budget
    metadata.cost_policy["pricing_source"] = pricing_source


def _estimate_model_cost_usd(
    *, model: str, prompt_tokens: int, completion_tokens: int
) -> tuple[float, str]:
    provider_model = model.lower()
    if "gemini" not in provider_model and not provider_model.startswith("google/"):
        return 0.0, "not_configured_for_non_gemini_provider"

    input_rate, output_rate, source = _gemini_rates_per_million(model)
    cost = (prompt_tokens * input_rate / 1_000_000) + (
        completion_tokens * output_rate / 1_000_000
    )
    return round(cost, 8), source


def _gemini_rates_per_million(model: str) -> tuple[float, float, str]:
    override_input = os.getenv("HARUQUANT_GEMINI_INPUT_USD_PER_1M")
    override_output = os.getenv("HARUQUANT_GEMINI_OUTPUT_USD_PER_1M")
    if override_input is not None and override_output is not None:
        return (
            float(override_input),
            float(override_output),
            "env:HARUQUANT_GEMINI_INPUT_USD_PER_1M/HARUQUANT_GEMINI_OUTPUT_USD_PER_1M",
        )

    lowered = model.lower()
    if "flash-lite" in lowered:
        return (
            float(os.getenv("HARUQUANT_GEMINI_FLASH_LITE_INPUT_USD_PER_1M", "0.10")),
            float(os.getenv("HARUQUANT_GEMINI_FLASH_LITE_OUTPUT_USD_PER_1M", "0.40")),
            "gemini_flash_lite_default_rates",
        )
    if "flash" in lowered:
        return (
            float(os.getenv("HARUQUANT_GEMINI_FLASH_INPUT_USD_PER_1M", "0.30")),
            float(os.getenv("HARUQUANT_GEMINI_FLASH_OUTPUT_USD_PER_1M", "2.50")),
            "gemini_flash_default_rates",
        )
    if "pro" in lowered:
        return (
            float(os.getenv("HARUQUANT_GEMINI_PRO_INPUT_USD_PER_1M", "1.25")),
            float(os.getenv("HARUQUANT_GEMINI_PRO_OUTPUT_USD_PER_1M", "10.00")),
            "gemini_pro_default_rates",
        )
    return (
        float(os.getenv("HARUQUANT_GEMINI_DEFAULT_INPUT_USD_PER_1M", "0.10")),
        float(os.getenv("HARUQUANT_GEMINI_DEFAULT_OUTPUT_USD_PER_1M", "0.40")),
        "gemini_default_rates",
    )


def _symbol_from_prompt(prompt: str) -> str | None:
    compact = re.sub(r"[^A-Za-z0-9]", "", prompt).upper()
    assets = (
        "EUR",
        "GBP",
        "AUD",
        "NZD",
        "USD",
        "JPY",
        "CHF",
        "CAD",
        "XAU",
        "XAG",
        "BTC",
        "ETH",
    )
    for base in assets:
        for quote in assets:
            if base == quote:
                continue
            symbol = f"{base}{quote}"
            if symbol in compact:
                return symbol
    return None


def _timeframe_from_prompt(prompt: str) -> str | None:
    match = re.search(r"\b(M1|M5|M15|M30|H1|H4|D1|W1|MN1)\b", prompt.upper())
    return match.group(1) if match else None


def _research_data_window_from_prompt(prompt: str) -> dict[str, object]:
    lowered = " ".join(prompt.lower().split())
    dates = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", lowered)
    window: dict[str, object] = {}
    if dates:
        window["start_date"] = dates[0]
        if len(dates) > 1:
            window["end_date"] = dates[1]
    bars = re.search(
        r"\b(?:last|past)?\s*(\d+)\s+(?:m1|m5|m15|m30|h1|h4|d1|w1|mn1)?\s*(?:bars?|candles?)\b",
        lowered,
    )
    if bars:
        window["bar_count"] = int(bars.group(1))
    lookback = re.search(
        r"\b(?:last|past)\s+(\d+)\s+(days?|weeks?|months?|years?)\b", lowered
    )
    if lookback and "start_date" not in window:
        amount = int(lookback.group(1))
        unit = lookback.group(2)
        days = amount
        if unit.startswith("week"):
            days = amount * 7
        elif unit.startswith("month"):
            days = amount * 30
        elif unit.startswith("year"):
            days = amount * 365
        end = datetime.now(UTC).date()
        start = end - timedelta(days=days)
        window["start_date"] = start.isoformat()
        window["end_date"] = end.isoformat()
    return window


def _research_market_evidence_pending(
    *, plan: AgentPlan, tool_results: list[ReadOnlyToolResult]
) -> bool:
    if plan.intent != "research" or plan.needs_clarification:
        return False
    if plan.workflow_id is None:
        return False
    market_data_results = [
        result for result in tool_results if result.tool_name == "mt5_market_data"
    ]
    if any(result.status == "success" for result in market_data_results):
        return False
    symbol_results = [
        result for result in tool_results if result.tool_name == "symbol_stats"
    ]
    if not symbol_results:
        return True
    for result in symbol_results:
        visible_metrics = (
            result.data.get("visible_metrics")
            if isinstance(result.data, dict)
            else None
        )
        if (
            result.status == "success"
            and isinstance(visible_metrics, list)
            and len(visible_metrics) > 0
        ):
            return False
    return True


def _has_successful_market_data(tool_results: list[ReadOnlyToolResult]) -> bool:
    return any(
        result.tool_name == "mt5_market_data" and result.status == "success"
        for result in tool_results
    )


def _request_with_pending_research_context(
    *,
    request: ChatTurnRequest,
    thread: ChatThreadDetail,
) -> ChatTurnRequest:
    if not _looks_like_pending_research_input_reply(request.prompt):
        return request
    pending_goal = _latest_pending_research_goal(thread)
    if not pending_goal:
        return request
    return request.model_copy(
        update={"prompt": f"{pending_goal} over the {request.prompt.strip()}"}
    )


def _latest_pending_research_goal(thread: ChatThreadDetail) -> str | None:
    for message in reversed(thread.messages):
        metadata = message.metadata
        if message.role != "assistant" or metadata is None:
            continue
        planner = metadata.planner or {}
        ceo_memo = metadata.ceo_memo or {}
        missing = (
            ceo_memo.get("what_is_missing") if isinstance(ceo_memo, dict) else None
        )
        if (
            isinstance(planner, dict)
            and planner.get("intent") == "research"
            and (
                metadata.clarification_required
                or (
                    isinstance(missing, list)
                    and "research_data_window_or_bar_count" in missing
                )
            )
        ):
            goal = planner.get("user_goal")
            return str(goal) if goal else None
    return None


def _looks_like_pending_research_input_reply(prompt: str) -> bool:
    lowered = " ".join(prompt.lower().split())
    if _contains_market_symbol_text(lowered):
        return False
    if _timeframe_from_prompt(prompt) and len(lowered.split()) <= 4:
        return True
    return bool(_research_data_window_from_prompt(prompt)) or bool(
        re.search(r"\b(last|past)\s+\d+\s+(days?|weeks?|months?|years?)\b", lowered)
    )


def _contains_market_symbol_text(lowered: str) -> bool:
    compact = re.sub(r"[^a-z0-9]", "", lowered).upper()
    assets = (
        "EUR",
        "GBP",
        "AUD",
        "NZD",
        "USD",
        "JPY",
        "CHF",
        "CAD",
        "XAU",
        "XAG",
        "BTC",
        "ETH",
    )
    return any(
        f"{base}{quote}" in compact
        for base in assets
        for quote in assets
        if base != quote
    )


def _research_payload_from_market_data(
    *,
    plan: AgentPlan,
    tool_results: list[ReadOnlyToolResult],
) -> dict[str, object] | None:
    if plan.intent != "research" or plan.needs_clarification:
        return None
    market_data = next(
        (
            result
            for result in tool_results
            if result.tool_name == "mt5_market_data" and result.status == "success"
        ),
        None,
    )
    if market_data is None:
        return None
    data = dict(market_data.data or {})
    payload: dict[str, object] = {
        **data,
        "workflow_id": plan.workflow_id or "research.full_edge_research",
        "research_workflow_id": plan.workflow_id or "research.full_edge_research",
        "research_question": plan.user_goal,
        "research_objective": "full_research",
        "evidence_refs": list(market_data.sources or []),
        "data_window": _format_research_data_window(data),
    }
    return payload


def _format_research_data_window(data: dict[str, object]) -> str:
    start = data.get("requested_start_date") or data.get("data_start")
    end = data.get("requested_end_date") or data.get("data_end")
    bars = data.get("requested_bar_count") or data.get("sample_size")
    if start and end:
        return f"{start} to {end}"
    if bars:
        return f"last {bars} bars"
    return "provided_market_data_window"


def _progress_event(
    *,
    request_id: str,
    step: int,
    total: int,
    label: str,
    detail: str | None = None,
    status: str = "running",
) -> tuple[str, dict[str, object]]:
    percent = int(round((step / max(total, 1)) * 100))
    return (
        "progress",
        {
            "request_id": request_id,
            "step": step,
            "total": total,
            "percent": max(0, min(100, percent)),
            "label": label,
            "detail": detail or "",
            "status": status,
        },
    )


def _tool_progress_detail(tool_results: list[ReadOnlyToolResult]) -> str:
    if not tool_results:
        return "No read-only evidence tools were needed."
    summary = ", ".join(
        f"{result.tool_name}:{result.status}" for result in tool_results
    )
    return summary[:240]


def _research_outputs_for_prompt(agent_outputs: dict[str, object]) -> dict[str, object]:
    news_sentiment = agent_outputs.get("news_sentiment_agent")
    if isinstance(news_sentiment, dict):
        return {"news_sentiment_agent": news_sentiment}
    workflow = agent_outputs.get("research_workflow")
    if not isinstance(workflow, dict):
        return {}
    return {
        "research_execution_plan": workflow.get("research_execution_plan"),
        "final_research_report": workflow.get("final_research_report"),
        "research_to_strategy_handoff": workflow.get("research_to_strategy_handoff"),
        "audit": workflow.get("audit"),
    }


def _run_direct_specialist_agent(
    *, plan: AgentPlan, request_id: str
) -> dict[str, object] | None:
    specialist_agents = [
        agent for agent in plan.allowed_agents if agent not in {"audit", "ceo"}
    ]
    if plan.workflow_id is not None or len(specialist_agents) != 1:
        return None
    agent_name = specialist_agents[0]
    if agent_name != "news_sentiment_agent":
        return None
    payload = _direct_news_sentiment_payload(plan.user_goal)
    previous_provider = os.environ.get("HARUQUANT_NEWS_SENTIMENT_PROVIDER")
    if _requests_forexfactory_provider(plan.user_goal):
        os.environ["HARUQUANT_NEWS_SENTIMENT_PROVIDER"] = "forexfactory"
    try:
        response = _run_agent_sync(
            NewsSentimentAgentService().run(
                AgentRequest(
                    request_id=request_id,
                    agent_name=agent_name,
                    task=plan.user_goal,
                    payload=payload,
                ),
                AgentContext(session_id=request_id),
            )
        )
    finally:
        if _requests_forexfactory_provider(plan.user_goal):
            if previous_provider is None:
                os.environ.pop("HARUQUANT_NEWS_SENTIMENT_PROVIDER", None)
            else:
                os.environ["HARUQUANT_NEWS_SENTIMENT_PROVIDER"] = previous_provider
    return {
        agent_name: {
            "status": response.status.value
            if hasattr(response.status, "value")
            else str(response.status),
            "decision": response.decision.model_dump(mode="json"),
            "artifacts": response.artifacts,
            "audit": response.audit,
        }
    }


def _run_agent_sync(awaitable):
    import asyncio

    return asyncio.run(awaitable)


def _direct_news_sentiment_payload(prompt: str) -> dict[str, object]:
    currencies = _currencies_from_prompt(prompt)
    symbol = _symbol_from_prompt(prompt) or (
        "".join(currencies[:2]) if len(currencies) >= 2 else "EURUSD"
    )
    timeframe = _timeframe_from_prompt(prompt) or "H1"
    payload: dict[str, object] = {
        "symbol": symbol,
        "timeframe": timeframe,
        "currencies": currencies or _currencies_for_symbol(symbol),
        "lookback_minutes": 10080 if "full" in prompt.lower() else 240,
        "calendar_window_minutes": 10080 if "full" in prompt.lower() else 1440,
        "min_event_impact": "low" if "full" in prompt.lower() else "medium",
        "research_question": prompt,
    }
    calendar_window = _calendar_window_from_prompt(prompt)
    if calendar_window:
        payload.update(calendar_window)
    return payload


def _currencies_for_symbol(symbol: str | None) -> list[str]:
    if not symbol:
        return []
    compact = re.sub(r"[^A-Za-z]", "", symbol).upper()
    currencies = [
        compact[index : index + 3] for index in range(0, min(len(compact), 6), 3)
    ]
    known = {"EUR", "GBP", "AUD", "NZD", "USD", "JPY", "CHF", "CAD"}
    return [currency for currency in currencies if currency in known]


def _currencies_from_prompt(prompt: str) -> list[str]:
    found: list[str] = []
    known = ("EUR", "GBP", "AUD", "NZD", "USD", "JPY", "CHF", "CAD")
    upper = prompt.upper()
    for currency in known:
        if re.search(rf"\b{currency}\b", upper):
            found.append(currency)
    return found


def _calendar_window_from_prompt(prompt: str) -> dict[str, object]:
    lowered = " ".join(prompt.lower().split())
    if "tomorrow" not in lowered:
        return {}
    tomorrow = datetime.now(UTC).date() + timedelta(days=1)
    start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=UTC)
    end = start + timedelta(days=1)
    return {
        "calendar_start_time": start.isoformat(),
        "calendar_end_time": end.isoformat(),
        "calendar_window_minutes": 1440,
    }


def _requests_forexfactory_provider(prompt: str) -> bool:
    lowered = " ".join(prompt.lower().split())
    return "forexfactory" in lowered or "forex factory" in lowered


def _news_sentiment_completed_memo(
    *,
    request: ChatTurnRequest,
    plan: AgentPlan,
    agent_outputs: dict[str, object],
) -> dict[str, object]:
    output = agent_outputs.get("news_sentiment_agent")
    output_data = output if isinstance(output, dict) else {}
    artifacts = (
        output_data.get("artifacts")
        if isinstance(output_data.get("artifacts"), dict)
        else {}
    )
    report = (
        artifacts.get("news_sentiment_report_structured")
        if isinstance(artifacts.get("news_sentiment_report_structured"), dict)
        else {}
    )
    audit = (
        output_data.get("audit") if isinstance(output_data.get("audit"), dict) else {}
    )
    symbol = str(
        report.get("symbol")
        or _symbol_from_prompt(request.prompt)
        or "requested symbol"
    )
    sentiment = (
        report.get("sentiment_snapshot")
        if isinstance(report.get("sentiment_snapshot"), dict)
        else {}
    )
    news_items = list(report.get("news_items") or [])
    calendar_events = list(report.get("calendar_events") or [])
    answer = (
        f"### News and Sentiment Report: {symbol}\n"
        f"**Status:** Completed | **Agent:** News and Sentiment Agent | **Risk Level:** {report.get('risk_level', 'unknown')}\n\n"
        f"{report.get('summary') or 'News and sentiment review completed.'}\n\n"
        "#### News\n"
        f"- Items found: {len(news_items)}\n"
        + "\n".join(
            f"- {str(item.get('title') if isinstance(item, dict) else item)[:180]}"
            for item in news_items[:5]
        )
        + "\n\n#### Sentiment\n"
        f"- Overall: {sentiment.get('overall_sentiment', 'unknown') if isinstance(sentiment, dict) else 'unknown'}\n"
        f"- Confidence: {sentiment.get('confidence', 'unknown') if isinstance(sentiment, dict) else 'unknown'}\n\n"
        "#### Calendar\n"
        f"- Upcoming events found: {len(calendar_events)}\n"
        + "\n".join(
            f"- {str(event.get('event_name') if isinstance(event, dict) else event)[:180]}"
            for event in calendar_events[:5]
        )
        + "\n\n#### Tool Audit\n"
        f"- Executed tools: {', '.join(str(tool) for tool in audit.get('tools_called', [])) or 'None reported'}\n\n"
        "*No execution or trade-related actions were taken. This is a read-only specialist research response.*"
    )
    return {
        "memo_type": "news_sentiment_report",
        "request": request.prompt,
        "decision": "specialist_completed",
        "summary": f"News and Sentiment Agent completed a direct specialist report for {symbol}.",
        "answer": answer,
        "planner_intent": plan.intent,
        "workflow_id": plan.workflow_id,
        "evidence_refs": list(
            dict.fromkeys(
                [*plan.evidence_requirements, *list(audit.get("evidence_refs") or [])]
            )
        ),
        "news_sentiment_report": report,
        "agent_audit": audit,
    }


def _research_completed_memo(
    *,
    request: ChatTurnRequest,
    plan: AgentPlan,
    agent_outputs: dict[str, object],
    tool_results: list[ReadOnlyToolResult],
) -> dict[str, object]:
    workflow = agent_outputs.get("research_workflow")
    workflow_data = workflow if isinstance(workflow, dict) else {}
    final_report = (
        workflow_data.get("final_research_report")
        if isinstance(workflow_data.get("final_research_report"), dict)
        else {}
    )
    handoff = (
        workflow_data.get("research_to_strategy_handoff")
        if isinstance(workflow_data.get("research_to_strategy_handoff"), dict)
        else {}
    )
    mt5_result = next(
        (result for result in tool_results if result.tool_name == "mt5_market_data"),
        None,
    )
    mt5_data = mt5_result.data if mt5_result else {}
    symbol = mt5_data.get("symbol") if isinstance(mt5_data, dict) else None
    timeframe = mt5_data.get("timeframe") if isinstance(mt5_data, dict) else None
    sample_size = mt5_data.get("sample_size") if isinstance(mt5_data, dict) else None
    data_start = mt5_data.get("data_start") if isinstance(mt5_data, dict) else None
    data_end = mt5_data.get("data_end") if isinstance(mt5_data, dict) else None
    instrument = (
        " ".join(str(value) for value in (symbol, timeframe) if value)
        or "requested market"
    )
    validation_status = str(final_report.get("validation_status") or "completed")
    handoff_status = str(handoff.get("handoff_status") or "not_ready")
    next_steps = [
        str(item) for item in list(final_report.get("recommended_next_steps") or [])
    ]
    evidence_refs = list(
        dict.fromkeys(
            [*plan.evidence_requirements, *(mt5_result.sources if mt5_result else [])]
        )
    )
    answer = (
        f"### Research Memo: {instrument}\n"
        f"**Status:** Research completed | **Workflow:** {plan.workflow_name or plan.workflow_id or 'Research'} | **Validation:** {validation_status}\n\n"
        f"Research ran against MT5-backed market evidence for **{instrument}**"
        f"{f' using {sample_size} bars' if sample_size else ''}"
        f"{f' from {data_start} to {data_end}' if data_start or data_end else ''}.\n\n"
        "#### Pipeline result\n"
        f"- Workflow ID: `{plan.workflow_id}`\n"
        f"- Research agents completed: {len(workflow_data.get('agent_responses') or {})}\n"
        f"- Edge Lab coverage: {final_report.get('edge_lab_coverage')}\n"
        f"- Strategy handoff status: `{handoff_status}`\n\n"
        "#### Next steps\n"
        + "\n".join(
            f"- {step}"
            for step in (
                next_steps
                or ["Review final research package before Strategy Lab handoff."]
            )
        )
        + "\n\n*No execution or trade-related actions were taken. This remains a read-only research process.*"
    )
    return {
        "memo_type": "research_memo",
        "request": request.prompt,
        "decision": "research_completed",
        "summary": f"Research completed for {instrument} using MT5-backed market evidence.",
        "answer": answer,
        "planner_intent": plan.intent,
        "workflow_id": plan.workflow_id,
        "workflow_name": plan.workflow_name,
        "evidence_refs": evidence_refs,
        "research_report": final_report,
        "research_to_strategy_handoff": handoff,
    }


def _research_evidence_pending_memo(
    *,
    request: ChatTurnRequest,
    plan: AgentPlan,
    tool_results: list[ReadOnlyToolResult],
) -> dict[str, object]:
    symbol_result = next(
        (result for result in tool_results if result.tool_name == "symbol_stats"), None
    )
    data = symbol_result.data if symbol_result else {}
    symbol = data.get("symbol") if isinstance(data, dict) else None
    timeframe = data.get("timeframe") if isinstance(data, dict) else None
    instrument = (
        " ".join(str(value) for value in (symbol, timeframe) if value)
        or "the requested market"
    )
    evidence_refs = list(
        dict.fromkeys(
            [
                *plan.evidence_requirements,
                *(symbol_result.sources if symbol_result else []),
            ]
        )
    )
    return {
        "memo_type": "research_memo",
        "request": request.prompt,
        "decision": "evidence_pending",
        "summary": (
            f"Research routing is active for {instrument}, but current market evidence is not sufficient to classify "
            "regime, volatility, momentum, liquidity clusters, or strategy suitability yet."
        ),
        "answer": (
            f"### Research Memo: {instrument} Strategy Suitability\n"
            "**Status:** Evidence pending | **Governance:** Standard | **Risk Level:** Low\n\n"
            "The CEO routed this request to the Research Department through the planner, but the available read-only "
            "evidence does not yet contain current market metrics. I will not classify the current regime or rank "
            "strategy families from unsupported assumptions.\n\n"
            "#### Planner-selected route\n"
            "- Department: Research Department\n"
            "- Specialists: Market Intelligence Agent, Technical Analyst Agent, Strategy Scout Agent, Evidence Curator Agent\n"
            f"- Evidence required: {', '.join(plan.evidence_requirements)}\n\n"
            "#### Evidence state\n"
            f"- Symbol/timeframe identified: {instrument}\n"
            f"- Market metrics: {symbol_result.summary if symbol_result else 'No symbol_stats evidence was returned.'}\n"
            "- Strategy suitability: pending evidence\n\n"
            "#### Next step\n"
            f"Connect or refresh {instrument} market metrics, then rerun the research request. After evidence is available, "
            "the CEO can summarize which families are suitable and hand the validated direction to Strategy Lab.\n\n"
            "*No execution or trade-related actions have been taken. This remains a read-only research process.*"
        ),
        "planner_intent": plan.intent,
        "evidence_refs": evidence_refs,
        "missing_evidence": [
            "current_market_metrics",
            "regime_evidence",
            "volatility_evidence",
            "strategy_fit_evidence",
        ],
    }


def _find_page_metric(
    page_context: PageContext, *, labels: tuple[str, ...]
) -> object | None:
    intelligence = dict((page_context.payload or {}).get("page_intelligence") or {})
    for metric in list(intelligence.get("visibleMetrics") or []):
        if not isinstance(metric, dict):
            continue
        metric_label = str(metric.get("label") or metric.get("id") or "").lower()
        if any(label in metric_label for label in labels):
            return metric.get("value")
    semantic_blocks = list(
        dict((page_context.payload or {}).get("dom") or {}).get("semantic_blocks") or []
    )
    for block in semantic_blocks:
        if not isinstance(block, dict):
            continue
        for metric in list(block.get("metrics") or []):
            if not isinstance(metric, dict):
                continue
            metric_label = str(metric.get("label") or metric.get("id") or "").lower()
            if any(label in metric_label for label in labels):
                return metric.get("value")
    return None


def _requests_live_or_run_now(request: str) -> bool:
    lowered = request.lower()
    return any(
        term in lowered
        for term in (
            "live",
            "run now",
            "execute now",
            "start now",
            "place a trade",
            "place live",
            "go live",
        )
    )


def _entity_ref(page_context: PageContext, ref_type: str) -> str | None:
    for ref in page_context.entity_refs:
        if ref.type == ref_type:
            return ref.id
    return None


def _session_id(page_context: PageContext) -> int | None:
    value = _entity_ref(page_context, "session") or _entity_ref(
        page_context, "live_session"
    )
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _is_page_identity_question(prompt: str) -> bool:
    lowered = " ".join(prompt.lower().strip().split())
    page_terms = (
        "what page am i on",
        "which page am i on",
        "where am i",
        "what screen am i on",
        "which screen am i on",
        "what route am i on",
        "current page",
        "current screen",
    )
    return any(term in lowered for term in page_terms)


__all__ = ["CEOChatGateway", "list_ceo_chat_tools"]

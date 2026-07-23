## FEAT-CONV-01: Production CEO chat gateway for the global HaruQuant chat widget (app.services.conversation.ceo_gateway)

| Function | Purpose |
|----------|---------|
| `CEOChatGateway.__init__(conversation_service: ConversationService, *, planner: PlannerAgent \| None = None, ceo: CEOAgent \| None = None, context_assembler: ContextAssembler \| None = None, prompt_builder: PromptBuilder \| None = None, stream_manager: StreamManager \| None = None, model_client: OpenAICompatibleStreamClient \| None = None, tool_executor: AIChatReadOnlyToolExecutor \| None = None) -> None` | Runs chat through the CEO and planner while preserving production streaming. |
| `CEOChatGateway.handle_turn(*, thread_id: str, user_id: str, request: ChatTurnRequest) -> ChatTurnResult` | Runs chat through the CEO and planner while preserving production streaming. |
| `CEOChatGateway.stream_turn(*, thread_id: str, user_id: str, request: ChatTurnRequest) -> Iterator[tuple[str, dict[str, object]]]` | Runs chat through the CEO and planner while preserving production streaming. |
| `list_ceo_chat_tools() -> list[ChatToolDefinition]` | List ceo chat tools. |


## FEAT-CONV-02: Page context services and builders for CEO chat (app.services.conversation.context)

| Function | Purpose |
|----------|---------|
| `get_context_builder(route: str \| None, page_type_hint: str \| None = None)` | Return context builder. |


## FEAT-CONV-03: Backtest detail page-context builder (app.services.conversation.context.backtest_detail)

| Function | Purpose |
|----------|---------|
| `build_backtest_detail_context(**kwargs: object) -> PageContext` | Build backtest detail context. |


## FEAT-CONV-04: Route-aware page-context builders for AI Chat (app.services.conversation.context.base)

| Function | Purpose |
|----------|---------|
| `normalize_text(value: object, limit: int = 240) -> str` | Normalize text. |
| `infer_page_type(route: str \| None, page_type_hint: str \| None = None) -> str` | Infer page type operation. |
| `compact_dom_snapshot(dom_snapshot: dict[str, object] \| None) -> dict[str, object]` | Compact dom snapshot operation. |
| `compact_page_intelligence(page_intelligence: dict[str, object] \| None) -> dict[str, object]` | Compact page intelligence operation. |
| `entity_refs_from_state(*, session_id: int \| None, symbol: str \| None, timeframe: str \| None, page_intelligence: dict[str, object] \| None) -> list[ChatEntityRef]` | Entity refs from state operation. |
| `build_compact_context(*, route: str \| None, page_title: str \| None, page_type: str, session_id: int \| None = None, symbol: str \| None = None, timeframe: str \| None = None, dom_snapshot: dict[str, object] \| None = None, page_intelligence: dict[str, object] \| None = None, summary_bullets: list[str] \| None = None, authority_source: str = 'ui_observer') -> PageContext` | Build compact context. |


## FEAT-CONV-05: Builders for compact AI chat page context (app.services.conversation.context.builders)

| Function | Purpose |
|----------|---------|
| `build_page_context(*, route: str \| None = None, page_title: str \| None = None, session_id: int \| None = None, symbol: str \| None = None, timeframe: str \| None = None, dom_snapshot: dict[str, object] \| None = None, page_intelligence: dict[str, object] \| None = None) -> PageContext` | Build page context. |


## FEAT-CONV-06: Dashboard page-context builder (app.services.conversation.context.dashboard)

| Function | Purpose |
|----------|---------|
| `build_dashboard_context(**kwargs: object) -> PageContext` | Build dashboard context. |


## FEAT-CONV-07: Data workspace page-context builder (app.services.conversation.context.data_workspace)

| Function | Purpose |
|----------|---------|
| `build_data_workspace_context(**kwargs: object) -> PageContext` | Build data workspace context. |


## FEAT-CONV-08: Freshness helpers for ephemeral page context (app.services.conversation.context.freshness)

| Function | Purpose |
|----------|---------|
| `freshness_payload(*, source: str = 'ui_page_context') -> dict[str, object]` | Freshness payload operation. |


## FEAT-CONV-09: Generic fallback page-context builder (app.services.conversation.context.generic)

| Function | Purpose |
|----------|---------|
| `build_generic_context(**kwargs: object) -> PageContext` | Build generic context. |


## FEAT-CONV-10: Live trading page-context builder (app.services.conversation.context.live_trading)

| Function | Purpose |
|----------|---------|
| `build_live_trading_context(**kwargs: object) -> PageContext` | Build live trading context. |


## FEAT-CONV-11: Operator workflow page-context builder (app.services.conversation.context.operator_workflow)

| Function | Purpose |
|----------|---------|
| `build_operator_workflow_context(**kwargs: object) -> PageContext` | Build operator workflow context. |


## FEAT-CONV-12: Optimization page-context builder (app.services.conversation.context.optimization)

| Function | Purpose |
|----------|---------|
| `build_optimization_context(**kwargs: object) -> PageContext` | Build optimization context. |


## FEAT-CONV-13: Portfolio risk page-context builder (app.services.conversation.context.portfolio_risk)

| Function | Purpose |
|----------|---------|
| `build_portfolio_risk_context(**kwargs: object) -> PageContext` | Build portfolio risk context. |


## FEAT-CONV-14: Ephemeral page-context assembly for AI Chat turns (app.services.conversation.context.service)

| Function | Purpose |
|----------|---------|
| `PageContextService.from_chat_request(request: ChatTurnRequest) -> PageContext` | Builds compact page context without persisting it as durable memory. |
| `ContextAssembler` (model) | Canonical context assembler alias used by route and chat tools. |


## FEAT-CONV-15: Strategy detail page-context builder (app.services.conversation.context.strategy_detail)

| Function | Purpose |
|----------|---------|
| `build_strategy_detail_context(**kwargs: object) -> PageContext` | Build strategy detail context. |


## FEAT-CONV-16: Durable memory facade for CEO chat conversations (app.services.conversation.memory)

| Function | Purpose |
|----------|---------|
| `ConversationMemoryService.__init__(repository: AiChatRepository) -> None` | Keeps durable chat memory separate from ephemeral page context. |
| `ConversationMemoryService.maybe_refresh_summary(*, thread_id: str, user_id: str, messages: list[ChatMessage], every_messages: int = 6) -> ChatMemorySummary \| None` | Keeps durable chat memory separate from ephemeral page context. |
| `ConversationMemoryService.list_pinned_facts(*, thread_id: str, user_id: str) -> list[ChatPinnedFact]` | Keeps durable chat memory separate from ephemeral page context. |


## FEAT-CONV-17: Prompt composition for the AI Chat gateway (app.services.conversation.prompt_builder)

| Function | Purpose |
|----------|---------|
| `PromptBuildResult` (model) | Prompt Build Result data model. |
| `PromptBuilder.build(*, request: ChatTurnRequest, request_id: str, thread: ChatThreadDetail, page_context: PageContext, route: ChatRouteDecision, tool_evidence: str \| None = None) -> PromptBuildResult` | Builds layered, auditable prompts from thread, memory, and page context. |


## FEAT-CONV-18: Retention lifecycle policy for AI chat conversations (app.services.conversation.retention)

| Function | Purpose |
|----------|---------|
| `RetentionDecision` (model) | Retention Decision data model. |
| `utc_now() -> datetime` | Utc now operation. |
| `to_sqlite_timestamp(value: datetime) -> str` | To sqlite timestamp operation. |
| `redact_sensitive_text(content: str) -> str` | Redact sensitive text operation. |
| `retention_expiry_for(retention_class: str, now: datetime \| None = None) -> str \| None` | Retention expiry for operation. |
| `purge_after_for(retention_class: str, now: datetime \| None = None) -> str \| None` | Purge after for operation. |
| `ConversationRetentionService.__init__(repository: AiChatRepository) -> None` | Applies lifecycle, archival, legal hold, and purge rules. |
| `ConversationRetentionService.initialize_thread_policy(*, thread_id: str, user_id: str, retention_class: str = 'standard') -> AiChatThreadRow` | Applies lifecycle, archival, legal hold, and purge rules. |
| `ConversationRetentionService.mark_regulated(*, thread_id: str, user_id: str, reason: str) -> AiChatThreadRow` | Applies lifecycle, archival, legal hold, and purge rules. |
| `ConversationRetentionService.set_ephemeral(*, thread_id: str, user_id: str, reason: str = 'User requested ephemeral retention.') -> AiChatThreadRow` | Applies lifecycle, archival, legal hold, and purge rules. |
| `ConversationRetentionService.apply_legal_hold(*, thread_id: str, user_id: str, actor_id: str, reason: str, until: str \| None = None) -> AiChatThreadRow` | Applies lifecycle, archival, legal hold, and purge rules. |
| `ConversationRetentionService.release_legal_hold(*, thread_id: str, user_id: str, actor_id: str, reason: str) -> AiChatThreadRow` | Applies lifecycle, archival, legal hold, and purge rules. |
| `ConversationRetentionService.run_lifecycle(*, now: datetime \| None = None, limit: int = 200) -> list[RetentionDecision]` | Applies lifecycle, archival, legal hold, and purge rules. |


## FEAT-CONV-19: Conversation service for the canonical HaruQuant CEO chat (app.services.conversation.service)

| Function | Purpose |
|----------|---------|
| `ActionDraftRecord.model_dump(mode: str \| None = None) -> dict[str, object]` | Model dump operation. |
| `ConversationService.__init__(repository: AiChatRepository) -> None` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.create_thread(*, user_id: str, title: str \| None = None, current_route: str \| None = None, current_page_type: str \| None = None, active_context_revision: str \| None = None) -> ChatThreadDetail` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.list_threads(*, user_id: str, query: str \| None = None, include_archived: bool = False, limit: int = 50) -> list[ChatThread]` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.get_thread(*, thread_id: str, user_id: str) -> ChatThreadDetail` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.rename_thread(*, thread_id: str, user_id: str, title: str) -> ChatThreadDetail` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.delete_thread(*, thread_id: str, user_id: str) -> bool` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.archive_thread(*, thread_id: str, user_id: str) -> ChatThreadDetail` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.restore_thread(*, thread_id: str, user_id: str) -> ChatThreadDetail` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.retention_detail(*, thread_id: str, user_id: str) -> ChatRetentionPolicyDetail` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.set_thread_retention_class(*, thread_id: str, user_id: str, retention_class: str, reason: str) -> ChatThreadDetail` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.update_context(*, thread_id: str, user_id: str, current_route: str \| None, current_page_type: str \| None, active_context_revision: str \| None) -> ChatThreadDetail` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.add_message(*, thread_id: str, user_id: str, role: str, content: str, request_id: str \| None = None, context_revision: str \| None = None, tool_calls: list[str] \| None = None, signal_proposal_id: str \| None = None, action_draft_id: str \| None = None, metadata: ChatResponseMetadata \| dict[str, object] \| None = None, latency_ms: int \| None = None) -> ChatMessage` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.export_thread(*, thread_id: str, user_id: str, format: str = 'markdown') -> str` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.create_action_draft(*, thread_id: str, user_id: str, request_id: str \| None, draft_type: str, title: str, description: str, payload: dict[str, object], risk_precheck_status: str = 'not_required', risk_precheck_notes: str = 'Draft only. No side effect has been executed.') -> ActionDraftRecord` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.get_action_draft(*, user_id: str \| int, draft_id: str) -> ActionDraftRecord` | Durable chat operations used by the UI API and CEO gateway. |
| `ConversationService.list_action_drafts(*, user_id: str \| int, thread_id: str \| None = None, status: str \| None = None) -> list[ActionDraftRecord]` | Durable chat operations used by the UI API and CEO gateway. |


## FEAT-CONV-20: Streaming transport utilities for AI Chat (app.services.conversation.stream_manager)

| Function | Purpose |
|----------|---------|
| `StreamCancelled` (model) | Raised when the caller stops consuming a response stream. |
| `ModelConfigurationError` (model) | Raised when model streaming is requested without runtime configuration. |
| `ModelRuntimeError` (model) | Raised when a configured provider cannot complete a stream. |
| `OpenAICompatibleStreamClient.__init__(*, base_url: str \| None = None, api_key: str \| None = None, provider_name: str \| None = None, timeout_seconds: float \| None = None) -> None` | Provider-aware streaming client. |
| `OpenAICompatibleStreamClient.is_configured -> bool` | Provider-aware streaming client. |
| `OpenAICompatibleStreamClient.is_configured_for(*, model: str \| None) -> bool` | Provider-aware streaming client. |
| `OpenAICompatibleStreamClient.provider_for_model(model: str) -> str` | Provider-aware streaming client. |
| `OpenAICompatibleStreamClient.provider_label_for_model(model: str) -> str` | Provider-aware streaming client. |
| `OpenAICompatibleStreamClient.stream_chat(*, messages: list[dict[str, str]], model: str, temperature: float = 0.2, max_tokens: int \| None = None) -> Iterator[str]` | Provider-aware streaming client. |
| `StreamManager.text_tokens(text: str, *, chunk_size: int = 48, delay_seconds: float = 0.0) -> Iterator[str]` | Converts model and fallback text into UI stream events. |


## FEAT-CONV-21: Deterministic rolling summaries for durable CEO chat memory (app.services.conversation.summaries)

| Function | Purpose |
|----------|---------|
| `build_rolling_summary(messages: list[ChatMessage], *, max_chars: int = 700) -> str` | Create a compact summary without relying on an LLM provider. |


## FEAT-CONV-22: Conversation title helpers for CEO chat threads (app.services.conversation.title)

| Function | Purpose |
|----------|---------|
| `generate_thread_title(prompt: str, *, fallback: str = 'CEO conversation') -> str` | Generate thread title. |


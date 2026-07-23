# Conversation AI Domain — Capability Feature Extraction (from `13-conversation-ai.md`)

Source: `docs/dev/phase-implementation-plan/13-conversation-ai.md`. Module paths follow the plan's target tree under `app.services.conversation`.

---

## FEAT-CONV-01: Package Gate and Capability Catalog (app.services.conversation / .catalog)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `domain_export_metadata() -> ConversationDomainMetadata` | Immutable domain metadata (`tool_category="conversation"`). | Missing |
| `list_ceo_chat_tools() -> tuple[ChatToolDefinition, ...]` | Declared CEO-chat tool catalog read; no execution or persistence. | Missing |
| `get_public_service_exports() -> Mapping[str, PublicCapability]` | Describe stable importable APIs without registering external function tools. | Missing |
| `build_capability_catalog(capabilities: Sequence[PublicCapability]) -> CapabilityCatalog` | Capability catalog construction (with contract validation, requirement-test lookup, and usage-example manifests). | Missing |

## FEAT-CONV-02: Conversation Contracts, Errors, Ports, and Stream Events (app.services.conversation.contracts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_model_schema(model: VersionedModel) -> ValidationResult` | Versioned model validation (with ActionDraftRecord, RetentionDecision, and PromptBuildResult contracts). | Missing |
| `map_conversation_error(error: Error \| Exception) -> ConversationErrorEnvelope` | Redacted deterministic error envelopes; never raw exceptions (with typed configuration/runtime errors and request-ID validation). | Missing |
| `ConversationRepository.create_thread(request: CreateThreadRequest, tx: TransactionBoundary) -> ThreadDetail` | Durable-store port (with idempotent-turn lookup and lifecycle audit writes). | Missing |
| `PlannerPort.plan(request: PlannerRequest) -> PlannerDecision` | Planning port with no conversation persistence (with authorization-evidence, read-only tool-executor, and model-stream ports). | Missing |
| `make_progress_event(stage: ProgressStage, context: StreamEventContext) -> StreamEvent` | Stream-event construction: progress, terminal, and error events with validation. | Missing |

## FEAT-CONV-03: Conversation Configuration (app.services.conversation.config)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `load_conversation_config(source: Mapping[str, str], overrides: Mapping[str, JsonValue] \| None = None) -> ConversationConfig` | Injected-environment configuration loading. | Missing |
| `resolve_provider_config(config: ConversationConfig, environment: Mapping[str, str]) -> ProviderRuntimeConfig` | Redacted provider runtime configuration from approved environment references. | Missing |
| `ConversationConfig.validate() -> ValidationResult` | Config validation (with retention-policy, prompt-budget, streaming-policy, and pagination-limit validators). | Missing |

## FEAT-CONV-04: Redaction, Tool Permissions, and Prompt-Injection Defense (app.services.conversation.security)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `redact_sensitive_text(text: str, policy: RedactionPolicy) -> RedactedText` | Text/payload redaction with normalization and `assert_safe_for_persistence` fail-closed check. | Missing |
| `classify_tool(tool: ChatToolDefinition, registry: ToolPermissionRegistry) -> ToolPermissionClass` | Tool permission classification (with evidence-permission and read-only evidence validation and quarantine). | Missing |
| `classify_untrusted_content(content: UntrustedContent, policy: PromptInjectionPolicy) -> ContentSafetyAssessment` | Prompt-injection assessment with evidence sanitization and memory-safe excerpts. | Missing |

## FEAT-CONV-05: Durable Conversation Persistence (app.services.conversation.persistence)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `SQLiteConversationRepository.in_transaction(operation: Callable[[TransactionBoundary], T]) -> T` | Transactional durable I/O. | Missing |
| `SQLiteConversationRepository.acquire_thread_turn_lock(user_id: str, thread_id: str, request_id: str) -> TurnLockLease` | Per-thread turn locking with idempotent turn commit; `(user_id, thread_id, request_id)` is the idempotency scope and material mismatch is a conflict. | Missing |
| `to_sqlite_timestamp(value: datetime) -> str` | UTC time codec (with `from_sqlite_timestamp` and injected-clock `utc_now`). | Missing |

## FEAT-CONV-06: Thread and Message Lifecycle (app.services.conversation.services.conversation_service)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `ConversationService.create_thread(request: CreateThreadRequest, actor: ActorContext) -> ThreadDetail` | Ownership-checked thread creation with retention initialization. | Missing |
| `ConversationService.list_threads(user_id: str, include_archived: bool = False, limit: int \| None = None, title_query: str \| None = None) -> ThreadList` | Thread listing/reads (with `get_thread`). | Missing |
| `ConversationService.rename_thread(user_id: str, thread_id: str, title: str) -> ThreadDetail` | Thread management: rename, archive, restore, soft delete, context updates with audit. | Missing |
| `ConversationService.add_message(request: AddMessageRequest, actor: ActorContext) -> MessageRecord` | Redacted, idempotency-checked message persistence with auto-titling and retention regulation. | Missing |
| `ConversationService.export_thread(user_id: str, thread_id: str, format: ExportFormat = ExportFormat.MARKDOWN) -> ThreadExport` | Thread export with lifecycle audit events. | Missing |
| `ConversationService.retention_detail(user_id: str, thread_id: str) -> ThreadRetentionDetail` | Retention reads and class updates (with `get_action_draft` read). | Missing |

## FEAT-CONV-07: Retention Policy and Lifecycle (app.services.conversation.services.retention_service)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `ConversationRetentionService.initialize_thread_policy(thread: ThreadRecord, policy: RetentionPolicy, now: datetime) -> ThreadRetentionDetail` | Retention initialization through the repository. | Missing |
| `ConversationRetentionService.apply_legal_hold(user_id: str, thread_id: str, reason: str, ends_at: datetime \| None = None) -> ThreadRetentionDetail` | Legal hold application/release, regulated marking, and ephemeral classification. | Missing |
| `ConversationRetentionService.run_lifecycle(now: datetime, batch_limit: int, time_budget: timedelta) -> LifecycleRunResult` | Bounded archive/purge lifecycle runs with audit events. | Missing |
| `retention_expiry_for(retention_class: RetentionClass, created_at: datetime, policy: RetentionPolicy) -> datetime \| None` | Deterministic expiry/purge time calculation. | Missing |

## FEAT-CONV-08: Conversation Memory (app.services.conversation.services.memory_service)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `ConversationMemoryService.maybe_refresh_summary(thread: ThreadDetail, cadence: SummaryCadence) -> MemorySummary` | Cadence-gated rolling summary refresh. | Missing |
| `build_rolling_summary(messages: Sequence[MessageRecord], budget: SummaryBudget) -> MemorySummaryDraft` | Budgeted summary drafts with recent-message selection and pinned-fact listing. | Missing |

## FEAT-CONV-09: Draft-Only Action Drafts (app.services.conversation.services.action_drafts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `ActionDraftService.create_action_draft(request: CreateActionDraftRequest, actor: ActorContext) -> ActionDraftRecord` | Schema-validated draft creation with persistence, retention escalation, and audit. | Missing |
| `validate_action_draft_payload(draft_type: ActionDraftType, payload: Mapping[str, JsonValue], schema_registry: DraftSchemaRegistry) -> ValidatedDraftPayload` | Registry-driven draft payload validation (with draft listing and draft-only status marking). | Missing |

## FEAT-CONV-10: Page Context and Prompt Composition (app.services.conversation.context)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `PageContextService.from_chat_request(request: ChatTurnRequest, limits: PageContextLimits) -> PageContext` | Bounded page context from chat requests (with DOM-snapshot compaction, entity references, page intelligence, and freshness payloads). | Missing |
| `ContextAssembler.build_page_context(request: ChatTurnRequest, state: UiPageState) -> PageContext` | Route/page-type-aware context assembly with builders for dashboard, data workspace, strategy/backtest detail, optimization, portfolio-risk, live trading, operator workflow, and generic pages. | Missing |
| `build_governance_system_context(policy_version: str) -> PromptMessage` | Governance system prompt with contract validation. | Missing |
| `PromptBuilder.build(input: PromptBuildInput) -> PromptBuildResult` | Layered prompt composition with budget truncation, pending-research merge, token estimation, and composition logs. | Missing |

## FEAT-CONV-11: Read-Only Tool Orchestration and CEO Chat Gateway (app.services.conversation.orchestration)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_tool_plan_read_only(plan: ToolPlan, registry: ToolPermissionRegistry) -> ReadOnlyToolPlan` | Enforce read-only tool plans before execution. | Missing |
| `ReadOnlyToolExecutor.execute(plan: ReadOnlyToolPlan, permission: PermissionDecision) -> ToolEvidenceBundle` | Permissioned read-only external I/O (with evidence attachment to prompt input). | Missing |
| `CEOChatGateway.stream_turn(request: ChatTurnRequest, actor: ActorContext) -> AsyncIterator[StreamEvent]` | Coordinating turn boundary: idempotent persistence, model and evidence calls through ports, streamed events. | Missing |
| `CEOChatGateway.reject_direct_specialist_or_live_request(request: ChatTurnRequest) -> DraftOnlyResponse` | Reject direct specialist or live-execution requests as draft-only (with turn metadata, needs-input events, and completed-turn persistence). | Missing |

## FEAT-CONV-12: Conversation Action Boundary (app.services.conversation.governance)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `classify_requested_action(prompt: str, policy: ConversationActionPolicy) -> RequestedActionClassification` | Classify requested actions against the conversation action policy. | Missing |
| `build_draft_only_response(action: RequestedActionClassification, evidence: EvidenceAvailability) -> DraftOnlyResponse` | Draft-only responses with direct operator-path references. | Missing |
| `assert_conversation_cannot_execute(action: RequestedActionType) -> None` | Deterministic policy error for prohibited execution attempts. | Missing |

## FEAT-CONV-13: Model Providers (app.services.conversation.providers)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `ModelStreamClient.stream_chat(request: ModelStreamRequest) -> AsyncIterator[ProviderToken]` | Streaming provider protocol (with `is_configured_for` configuration check). | Missing |
| `OpenAICompatibleStreamClient.stream_chat(request: ModelStreamRequest) -> AsyncIterator[ProviderToken]` | OpenAI-compatible HTTPS/local streaming with provider resolution per model and in-memory usage collection. | Missing |

## FEAT-CONV-14: Streaming Management and Deterministic Fallback (app.services.conversation.streaming)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_deterministic_fallback(request: ChatTurnRequest, reason: FallbackReason, policy: FallbackPolicy) -> FallbackResponse` | Deterministic fallback responses with metadata, ordered fallback events, and `validate_no_invented_evidence`. | Missing |
| `StreamManager.text_tokens(text: str, chunk_size: int, delay: timedelta \| None = None) -> AsyncIterator[str]` | Chunked token streaming. | Missing |
| `StreamManager.apply_backpressure(events: AsyncIterator[StreamEvent], policy: BackpressurePolicy) -> AsyncIterator[StreamEvent]` | Bounded in-memory stream backpressure (with `cancel` and terminal-event-enforcing `handle_turn`). | Missing |

## FEAT-CONV-15: Conversation Observability (app.services.conversation.observability)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `record_prompt_composition_metrics(result: PromptBuildResult, context: TraceContext) -> None` | Redacted telemetry for prompt composition (with turn-metadata recording). | Missing |
| `observe_conversation_operation(operation: str) -> Callable[[Callable[..., T]], Callable[..., T]]` | Decorator boundary emitting structured logs/metrics only. | Missing |

---

**Note:** the conversation domain is draft-only and read-only by construction: it can never place trades, mutate risk, or execute operator actions — governed actions surface as validated action drafts routed to operator controls. `ConversationService` is an importable class API; no function is an external agent tool unless approved in the package `__all__` registry.

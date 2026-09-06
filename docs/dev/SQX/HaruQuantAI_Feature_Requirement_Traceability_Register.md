# HaruQuantAI — Feature–Requirement Traceability Register

| Field | Value |
|---|---|
| Status | Adopted target-scope traceability companion; implementation evidence remains repository-owned |
| Source | [HaruQuantAI Unified Specification](HaruQuantAI_Unified_Specification.md) |
| Product | HaruQuantAI V3 |
| Validation | `uv run python scripts/validate_unified_feature_traceability.py` |

## 1. Authority and purpose

This register is the canonical cross-domain **traceability projection** of the Unified Specification. It defines the target Product → Domain → atomic Feature decomposition and gives every normative behavior one primary `FEAT-*` owner. It does not replace an owning package README as the canonical current-state feature/FR/status registry, and it does not prove that a target feature is registered or implemented.

Authority is therefore deliberately split: owning package READMEs and runtime manifests establish `REGISTERED_CURRENT`; this register establishes `SPECIFIED_TARGET` identities and complete source coverage. A later implementation Task must reconcile the target card into the owning README, contracts, manifest, usage evidence, and tests before changing status.

## 2. Feature and counting rules

A feature is one independently valuable behavior with one semantic owner, coherent public capability, authoritative state/policy boundary, lifecycle/removal unit, and primary acceptance scenario. A screen, widget, route, algorithm, role, record, requirement group, milestone, or task is not independently a feature unless it passes that boundary test.

Every behavioral requirement has exactly one primary feature. Supporting features and public contracts are dependencies, not co-owners. Shared NFRs are many-to-many overlays. §27 master FRs are traceability summaries and are never added to primary behavior totals. §54 numeric Agentic features and `FR-AGENTIC-001`–`072` are legacy aliases/dispositions, never current duplicates.

Evidence states are:

- `SPECIFIED_ACCEPTANCE`: the source defines evidence that must exist.
- `VERIFIED_CURRENT`: the owning current README/runtime and cited tests were inspected and agree.
- `PENDING_EVIDENCE`: specified evidence is absent or was not established by this documentation Task.

## 3. Source inventory and definitive count taxonomy

The definitive counts are intentionally typed, not collapsed into one misleading “requirements” number. Primary functional behavior is 290 IDs: 149 workbench + 52 engine + 81 Agentic + 8 tick-execution. The 32 master FRs are non-additive overlays. Shared NFRs are 52 IDs after assigning the five §28.5 integrity clauses stable IDs; twelve `PER-*` obligations are feature-specific NFRs.

<!-- DECLARED_TOTALS_START -->
| Metric | Count |
|---|---:|
| `surface_functional` | 149 |
| `engine_functional` | 52 |
| `agentic_functional` | 81 |
| `tick_functional` | 8 |
| `primary_functional` | 290 |
| `master_overlays` | 32 |
| `platform_nfr` | 33 |
| `financial_nfr` | 5 |
| `agentic_nfr` | 14 |
| `shared_nfr` | 52 |
| `feature_nfr` | 12 |
| `extensions` | 8 |
| `decisions` | 17 |
| `reconciliations` | 30 |
| `integrations` | 14 |
| `workflows` | 12 |
| `benchmarks` | 12 |
| `performance_tasks` | 17 |
| `performance_gates` | 12 |
| `control_records` | 122 |
| `milestones` | 14 |
| `agentic_tasks` | 41 |
| `delivery_records` | 55 |
| `legacy_agentic_features` | 22 |
| `legacy_agentic_requirements` | 72 |
| `legacy_aliases` | 94 |
| `features` | 98 |
| `registered_current` | 22 |
| `specified_target` | 76 |
<!-- DECLARED_TOTALS_END -->

## 4. Product → Domain → Feature index

<!-- FEATURE_INDEX_START -->
| Feature ID | Domain | Status | Atomic value |
|---|---|---|---|
| `FEAT-WS-BUILD_DIAGNOSTICS` | Workspace | REGISTERED_CURRENT | Give operators a safe, portable explanation of application and run health. |
| `FEAT-UI-OPERATE_WORKSPACE` | UI | SPECIFIED_TARGET | Let users compose, navigate, persist, recover, and keyboard-operate research widgets without changing domain truth. |
| `FEAT-UI-DISCOVER_COMMANDS` | UI | SPECIFIED_TARGET | Provide permission-aware global discovery of commands, resources, and contextual help. |
| `FEAT-UI-PRESENT_RUNS` | UI | SPECIFIED_TARGET | Keep long-running work observable and controllable independently of any originating widget. |
| `FEAT-UI-DESIGN_RESEARCH_SPACES` | UI | SPECIFIED_TARGET | Provide a typed Builder surface for strategy-space configuration and effective-plan preview. |
| `FEAT-UI-PRESENT_RESULTS` | UI | SPECIFIED_TARGET | Compose result tabs, synchronized selections, bounded grids, charts, and accessible fallbacks. |
| `FEAT-UI-COMPOSE_PORTFOLIOS` | UI | SPECIFIED_TARGET | Provide manual and search portfolio workspaces without owning portfolio mathematics. |
| `FEAT-UI-MANAGE_DATA` | UI | SPECIFIED_TARGET | Provide pageable data, profile, quality, instrument, session, and connector workflows through owner capabilities. |
| `FEAT-UI-EDIT_STRATEGIES` | UI | SPECIFIED_TARGET | Provide canvas, tree, form, and source projections over one Strategy-owned AST. |
| `FEAT-UI-DEVELOP_EXTENSIONS` | UI | SPECIFIED_TARGET | Provide authorized code/resource editing and test/build feedback without host authority. |
| `FEAT-UI-PRESENT_OVERLAYS` | UI | SPECIFIED_TARGET | Provide accessible modals/drawers/confirmations with typed drafts and concrete mutation scope. |
| `FEAT-UI-RENDER_CHARTS` | UI | SPECIFIED_TARGET | Render bounded, synchronized, provenance-aware charts with accessible nonvisual alternatives. |
| `FEAT-UI-CHAT_BOT` | UI | SPECIFIED_TARGET | Present fresh workspace context and same-conversation specialist results without direct business mutation. |
| `FEAT-STRAT-DEFINE_STRATEGIES` | Strategy | SPECIFIED_TARGET | Own HSL v2 AST meaning, validation, canonical identity, revisions, templates, and strategy-space schemas. |
| `FEAT-STRAT-CATALOG_BLOCKS` | Strategy | SPECIFIED_TARGET | Resolve compatible typed building blocks and provider/version metadata. |
| `FEAT-STRAT-COMPILE_STRATEGIES` | Strategy | SPECIFIED_TARGET | Lower validated HSL into immutable reusable execution plans without changing meaning. |
| `FEAT-STRAT-GENERATE_TARGETS` | Strategy | SPECIFIED_TARGET | Produce only declared, semantically verified source/pseudocode artifacts. |
| `FEAT-STRAT-EXCHANGE_STRATEGIES` | Strategy | SPECIFIED_TARGET | Import/export native bundles and isolated external formats with explicit loss and provenance. |
| `FEAT-STRAT-PACKAGE_STRATEGIES` | Strategy | SPECIFIED_TARGET | Build reproducible distribution packages without deploying or activating trading. |
| `FEAT-STRAT-ACCEPT_PROPOSALS` | Strategy | SPECIFIED_TARGET | Validate and record user-reviewed Agentic or external candidates as Strategy-owned revisions/receipts. |
| `FEAT-RES-GENERATE_STRATEGIES` | Research | SPECIFIED_TARGET | Run bounded random, seeded, evolutionary, and advanced candidate search with complete lineage. |
| `FEAT-RES-QUALIFY_STRATEGIES` | Research | SPECIFIED_TARGET | Own ordered robustness/cross-check/acceptance policy and explain every rejection or promotion. |
| `FEAT-RES-GOVERN_CAMPAIGNS` | Research | SPECIFIED_TARGET | Own campaign, family, protocol, budget, holdout, attempt, and sealed-sample truth for every caller. |
| `FEAT-RES-TRAIN_NEURAL_MODELS` | Research | SPECIFIED_TARGET | Create leakage-controlled, versioned research model evidence and portable qualified inference artifacts. |
| `FEAT-SIM-SIMULATE_ORDERS` | Simulator | SPECIFIED_TARGET | Own deterministic tick-event execution, fills, costs, exits, valuation, checkpoints, and result truth. |
| `FEAT-SIM-RETEST_STRATEGIES` | Simulator | SPECIFIED_TARGET | Re-evaluate immutable strategy populations under changed data/cost/precision/perturbation contexts. |
| `FEAT-SIM-MANAGE_TICK_METHODS` | Simulator | SPECIFIED_TARGET | Select, validate, generate/consume, and disclose exact recorded/generated tick evidence for every backtest. |
| `FEAT-OPT-SEARCH_PARAMETERS` | Optimization | SPECIFIED_TARGET | Own bounded parameter spaces, trials, search methods, checkpoints, surfaces, and reproducible exports. |
| `FEAT-OPT-VALIDATE_WALK_FORWARD` | Optimization | SPECIFIED_TARGET | Own WFO/WFM window mechanics and stability surfaces while Research owns qualification policy. |
| `FEAT-ANLT-MANAGE_DATABANKS` | Analytics | SPECIFIED_TARGET | Own versioned result membership, stable selection, saved views, and governed bulk actions. |
| `FEAT-ANLT-QUERY_RESULTS` | Analytics | SPECIFIED_TARGET | Provide bounded cursor-based result/trade/series projections over immutable snapshots. |
| `FEAT-ANLT-INTERPRET_RESULTS` | Analytics | SPECIFIED_TARGET | Own canonical metrics, comparisons, provenance, null semantics, and report projections. |
| `FEAT-ANLT-ANALYZE_TRADES` | Analytics | SPECIFIED_TARGET | Own trade/equity/time-series analytical projections and cross-panel trade identity. |
| `FEAT-ANLT-ANALYZE_CORRELATION` | Analytics | SPECIFIED_TARGET | Compute aligned correlation and explain deterministic retain/remove decisions. |
| `FEAT-PORT-COMPOSE_PORTFOLIOS` | Portfolio | SPECIFIED_TARGET | Own versioned constituents, weights, capital/leverage/sizing compatibility, and portfolio revisions. |
| `FEAT-PORT-SIMULATE_PORTFOLIOS` | Portfolio | SPECIFIED_TARGET | Produce combined interacting-capital portfolio results with constituent lineage. |
| `FEAT-PORT-OPTIMIZE_WEIGHTS` | Portfolio | SPECIFIED_TARGET | Provide registered weighting and constrained allocation methods. |
| `FEAT-PORT-SEARCH_PORTFOLIOS` | Portfolio | SPECIFIED_TARGET | Search bounded strategy combinations and commit selected portfolio candidates atomically. |
| `FEAT-PORT-ANALYZE_CORRELATION` | Portfolio | SPECIFIED_TARGET | Own portfolio-specific alignment/covariance/correlation inputs and diversification evidence. |
| `FEAT-ORCH-MANAGE_RUNS` | Orchestration | SPECIFIED_TARGET | Own idempotent run/job plans, states, attempts, pause/stop/cancel, retention, and restart policy. |
| `FEAT-ORCH-DEFINE_PROJECTS` | Orchestration | SPECIFIED_TARGET | Own versioned typed project graphs, drafts, publication validation, and cloning. |
| `FEAT-ORCH-RUN_PROJECTS` | Orchestration | SPECIFIED_TARGET | Plan and execute whole/from-here/only project scopes with durable attempts and lineage. |
| `FEAT-ORCH-EVALUATE_CONDITIONS` | Orchestration | SPECIFIED_TARGET | Evaluate typed branches deterministically with bounded loops and replayable inputs. |
| `FEAT-ORCH-DISTRIBUTE_WORKERS` | Orchestration | SPECIFIED_TARGET | Run authenticated bounded local/remote work with leases, fencing, deterministic aggregation, and drain. |
| `FEAT-ORCH-ADMIT_RESOURCES` | Orchestration | SPECIFIED_TARGET | Enforce one hierarchical finite CPU, memory, thread, I/O, disk, device, and model budget across work. |
| `FEAT-ORCH-MEASURE_PERFORMANCE` | Orchestration | SPECIFIED_TARGET | Run reproducible workload/gate evaluation and block affected releases on confirmed regression. |
| `FEAT-DATA-BROWSE_REFERENCE` | Data | REGISTERED_CURRENT | Expose bounded research reference/data/profile views through one existing owner boundary. |
| `FEAT-DATA-BIND_RUN_DATA` | Data | REGISTERED_CURRENT | Resolve immutable series/profile/sample versions for reproducible runs. |
| `FEAT-DATA-MARKET_DATA_STORE` | Data | REGISTERED_CURRENT | Own bounded append/read/partition/manifest behavior for immutable bulk bars and ticks. |
| `FEAT-DATA-SYNC_CONNECTORS` | Data | REGISTERED_CURRENT | Validate source configuration and perform bounded authorized connector synchronization. |
| `FEAT-DATA-RESOLVE_QUALITY` | Data | REGISTERED_CURRENT | Create versioned findings and non-destructive repair outputs. |
| `FEAT-DATA-MANAGE_RETENTION` | Data | REGISTERED_CURRENT | Govern clone/delete/retention and reference impact without orphaning evidence. |
| `FEAT-DATA-INGEST_HISTORY` | Data | REGISTERED_CURRENT | Import supported market-data files through pinned adapters and truthful manifests. |
| `FEAT-DATA-NORMALIZE_TICKS` | Data | REGISTERED_CURRENT | Canonicalize provider ticks without changing source ordering/evidence class. |
| `FEAT-DATA-GENERATE_SCENARIOS` | Data | REGISTERED_CURRENT | Generate seeded tick/scenario streams with explicit model and evidence classification. |
| `FEAT-DATA-ALIGN_SERIES` | Data | REGISTERED_CURRENT | Align multi-symbol/timeframe/external evidence backward-only with explicit availability. |
| `FEAT-CAT-CATALOG_INSTRUMENTS` | Catalogue | REGISTERED_CURRENT | Own stable instrument identities and versioned trading/data metadata. |
| `FEAT-CAT-DEFINE_SESSIONS` | Catalogue | REGISTERED_CURRENT | Own venue calendars, sessions, holidays, and timezone/DST rules. |
| `FEAT-CAT-MAP_PROVIDERS` | Catalogue | REGISTERED_CURRENT | Map provider-local identifiers/values to canonical catalogue identities without leaking SDK objects. |
| `FEAT-PLUG-DECLARE_MANIFESTS` | Plugins | REGISTERED_CURRENT | Validate typed extension identity, contributions, permissions, compatibility, and resources. |
| `FEAT-PLUG-REGISTER_CONTRIBUTIONS` | Plugins | REGISTERED_CURRENT | Publish and withdraw typed provider/widget/panel/tool contributions atomically. |
| `FEAT-PLUG-MANAGE_LIFECYCLE` | Plugins | REGISTERED_CURRENT | Quarantine, scan, install, enable, disable, upgrade, and remove extensions without implicit data purge. |
| `FEAT-PLUG-SANDBOX_PERMISSIONS` | Plugins | REGISTERED_CURRENT | Enforce least-privilege filesystem, process, network, secret, and resource boundaries. |
| `FEAT-PLUG-ISOLATE_ANALYSIS` | Plugins | REGISTERED_CURRENT | Compile/test/analyze untrusted extension source outside browser/application authority. |
| `FEAT-PLUG-RENDER_RESULT_PANELS` | Plugins | REGISTERED_CURRENT | Run custom result panels against read-only projections in a contained frame. |
| `FEAT-PLUG-MAINTAIN_COMPATIBILITY` | Plugins | REGISTERED_CURRENT | Evaluate contract/toolchain/schema compatibility and explicit migrations. |
| `FEAT-PLUG-DEVELOP_EXTENSIONS` | Plugins | SPECIFIED_TARGET | Own authorized resource revisions, conflict-aware saves, searches, and package-local development state. |
| `FEAT-INDI-CALCULATE_INDICATORS` | Indicators | SPECIFIED_TARGET | Own causal incremental/native indicator algorithms and versioned descriptors. |
| `FEAT-INDI-TEST_INDICATORS` | Indicators | SPECIFIED_TARGET | Compare extension indicator outputs against owner-qualified reference calculations. |
| `FEAT-INDI-ANALYZE_MARKET_PROFILE` | Indicators | SPECIFIED_TARGET | Produce typed Volume Profile/TPO derived layers with accessible projections. |
| `FEAT-IFACE-SERVE_API_EVENTS` | Interfaces | REGISTERED_CURRENT | Authenticate/validate cohesive commands and provide idempotent job references plus resumable SSE. |
| `FEAT-IFACE-OPERATE_STRATEGIES` | Interfaces | SPECIFIED_TARGET | Translate strategy authoring/exchange/generation requests without owning semantics. |
| `FEAT-IFACE-OPERATE_RESEARCH` | Interfaces | SPECIFIED_TARGET | Translate Builder/Retester/Optimization research commands and observations. |
| `FEAT-IFACE-OPERATE_ANALYTICS` | Interfaces | SPECIFIED_TARGET | Translate databank/result/trade/report queries and governed bulk commands. |
| `FEAT-IFACE-OPERATE_PORTFOLIOS` | Interfaces | SPECIFIED_TARGET | Translate portfolio composition/search/simulation commands and views. |
| `FEAT-IFACE-OPERATE_PROJECTS` | Interfaces | SPECIFIED_TARGET | Translate project draft/publish/run/control/history operations. |
| `FEAT-IFACE-OPERATE_PLUGINS` | Interfaces | SPECIFIED_TARGET | Translate authorized extension resource/build/lifecycle/panel operations. |
| `FEAT-IFACE-AGENTIC_GATEWAY` | Interfaces | SPECIFIED_TARGET | Authenticate Chat Bot/workflow/action/inspection requests and stream bounded Agentic events. |
| `FEAT-AGT-ENFORCE_MANDATE` | Agentic | SPECIFIED_TARGET | Enforce immutable firm mandate and prohibited authority. |
| `FEAT-AGT-OPERATE_RUNS` | Agentic | SPECIFIED_TARGET | Record redacted operations, contain incidents, validate replay, and publish readiness. |
| `FEAT-AGT-REGISTER_ROLES` | Agentic | SPECIFIED_TARGET | Register immutable evaluated role contributions with exact disposal. |
| `FEAT-AGT-GOVERN_TOOL_CALLS` | Agentic | SPECIFIED_TARGET | Register governed tools, issue invocation-bound leases, and bind typed human actions. |
| `FEAT-AGT-INVOKE_MODELS` | Agentic | SPECIFIED_TARGET | Invoke pinned model profiles under schema, privacy, budget, and fallback policy. |
| `FEAT-AGT-RUN_WORKFLOWS` | Agentic | SPECIFIED_TARGET | Run bounded checkpointed Agentic workflows with explicit terminal states. |
| `FEAT-AGT-ASSEMBLE_CONTEXT` | Agentic | SPECIFIED_TARGET | Assemble bounded eligible evidence separated structurally from instructions. |
| `FEAT-AGT-MANAGE_MEMORY` | Agentic | SPECIFIED_TARGET | Classify, promote, retrieve, retain, and purge scoped memory safely. |
| `FEAT-AGT-EVALUATE_PROFILES` | Agentic | SPECIFIED_TARGET | Evaluate and ablate profiles/topologies and determine deterministic eligibility. |
| `FEAT-AGT-ASSIST_OPERATOR` | Agentic | SPECIFIED_TARGET | Answer contextual questions or route eligible specialists in one conversation. |
| `FEAT-AGT-MANAGE_CLAIMS` | Agentic | SPECIFIED_TARGET | Create typed claims, bind evidence, propagate status, and assess reliability. |
| `FEAT-AGT-DELIBERATE_RESEARCH` | Agentic | SPECIFIED_TARGET | Collect independent bounded challenge while preserving dissent. |
| `FEAT-AGT-SYNTHESIZE_RESEARCH` | Agentic | SPECIFIED_TARGET | Synthesize only supported claim graphs with uncertainty and refusal. |
| `FEAT-AGT-GOVERN_RESEARCH_SEARCH` | Agentic | SPECIFIED_TARGET | Account campaigns, variants, failed attempts, budgets, and holdout receipts. |
| `FEAT-AGT-DESIGN_RESEARCH` | Agentic | SPECIFIED_TARGET | Compose falsifiable hypotheses and receiver-owned experiment/search requests. |
| `FEAT-AGT-COMPOSE_STRATEGY_SPECS` | Agentic | SPECIFIED_TARGET | Compose reviewed receiver-owned DSL candidates with provenance. |
| `FEAT-AGT-ADVISE_PORTFOLIO` | Agentic | SPECIFIED_TARGET | Produce expiring non-binding portfolio advice with independent risk challenge. |
| `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS` | Agentic | SPECIFIED_TARGET | Compose and submit expiring Strategy-owned proposal candidates without execution fields. |
| `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS` | Agentic | SPECIFIED_TARGET | Author staged source only after a proven DSL gap under sandbox authority. |
| `FEAT-AGT-CALIBRATE_OUTCOMES` | Agentic | SPECIFIED_TARGET | Match outcomes, score calibration/value, and propose evidence-backed profile changes. |
<!-- FEATURE_INDEX_END -->

## 5. Primary functional ownership

<!-- PRIMARY_REQUIREMENTS_START -->
| Class | Primary feature | Source IDs | Supporting features |
|---|---|---|---|
| Workbench | `FEAT-UI-OPERATE_WORKSPACE` | `SHELL-001`–`SHELL-004`, `SHELL-007`–`SHELL-008`, `UI-DCK-001`–`UI-DCK-006` | — |
| Workbench | `FEAT-UI-DISCOVER_COMMANDS` | `SHELL-005` | — |
| Workbench | `FEAT-UI-PRESENT_RUNS` | `SHELL-006` | `FEAT-ORCH-MANAGE_RUNS` |
| Workbench | `FEAT-WS-BUILD_DIAGNOSTICS` | `SHELL-009`, `RUN-010` | — |
| Workbench | `FEAT-ORCH-MANAGE_RUNS` | `RUN-001`–`RUN-002`, `RUN-004`–`RUN-009` | `FEAT-IFACE-SERVE_API_EVENTS`, `FEAT-UI-PRESENT_RUNS` |
| Workbench | `FEAT-IFACE-SERVE_API_EVENTS` | `RUN-003` | — |
| Workbench | `FEAT-STRAT-DEFINE_STRATEGIES` | `BLD-001`, `GEN-003`, `STU-001`, `STU-003`–`STU-004`, `STU-009`, `AST-001`–`AST-004`, `AST-007` | — |
| Workbench | `FEAT-STRAT-CATALOG_BLOCKS` | `BLD-002`, `STU-002` | — |
| Workbench | `FEAT-UI-DESIGN_RESEARCH_SPACES` | `BLD-003` | — |
| Workbench | `FEAT-RES-GENERATE_STRATEGIES` | `BLD-004`, `BLD-006`, `GEN-001`–`GEN-002`, `GEN-004`–`GEN-006`, `GEN-008`, `GEN-010` | — |
| Workbench | `FEAT-RES-QUALIFY_STRATEGIES` | `BLD-005`, `BLD-009`, `GEN-007`, `GEN-009` | — |
| Workbench | `FEAT-ANLT-MANAGE_DATABANKS` | `BLD-007`, `DBK-001`–`DBK-006` | — |
| Workbench | `FEAT-RES-GOVERN_CAMPAIGNS` | `BLD-008` | — |
| Workbench | `FEAT-PLUG-ISOLATE_ANALYSIS` | `BLD-010`, `CED-003`, `CED-008` | — |
| Workbench | `FEAT-SIM-RETEST_STRATEGIES` | `RET-001`–`RET-007` | — |
| Workbench | `FEAT-STRAT-ACCEPT_PROPOSALS` | `OPT-009`, `STU-007` | — |
| Workbench | `FEAT-OPT-SEARCH_PARAMETERS` | `OPT-001`–`OPT-003`, `OPT-005`–`OPT-006`, `OPT-010` | — |
| Workbench | `FEAT-OPT-VALIDATE_WALK_FORWARD` | `OPT-004`, `OPT-007`–`OPT-008` | — |
| Workbench | `FEAT-ANLT-QUERY_RESULTS` | `DBK-007` | — |
| Workbench | `FEAT-ANLT-ANALYZE_CORRELATION` | `DBK-008` | — |
| Workbench | `FEAT-STRAT-GENERATE_TARGETS` | `DBK-009`, `STU-005`, `AST-009` | — |
| Workbench | `FEAT-STRAT-EXCHANGE_STRATEGIES` | `DBK-010`, `XCH-001`–`XCH-010` | — |
| Workbench | `FEAT-ANLT-INTERPRET_RESULTS` | `RES-OV-001`–`RES-OV-004`, `RES-003`–`RES-004`, `RES-008`, `RES-010` | — |
| Workbench | `FEAT-ANLT-ANALYZE_TRADES` | `RES-TRD-001`–`RES-TRD-004` | — |
| Workbench | `FEAT-UI-PRESENT_RESULTS` | `RES-001`–`RES-002`, `RES-005`–`RES-007` | — |
| Workbench | `FEAT-PLUG-RENDER_RESULT_PANELS` | `RES-009` | — |
| Workbench | `FEAT-PORT-COMPOSE_PORTFOLIOS` | `PFC-001`–`PFC-004`, `PFC-008` | — |
| Workbench | `FEAT-PORT-SIMULATE_PORTFOLIOS` | `PFC-005`, `PFM-008` | — |
| Workbench | `FEAT-PORT-OPTIMIZE_WEIGHTS` | `PFC-006` | — |
| Workbench | `FEAT-UI-COMPOSE_PORTFOLIOS` | `PFC-007` | — |
| Workbench | `FEAT-PORT-SEARCH_PORTFOLIOS` | `PFM-001`–`PFM-006` | — |
| Workbench | `FEAT-PORT-ANALYZE_CORRELATION` | `PFM-007` | — |
| Workbench | `FEAT-DATA-BROWSE_REFERENCE` | `DAT-001` | — |
| Workbench | `FEAT-DATA-BIND_RUN_DATA` | `DAT-002` | — |
| Workbench | `FEAT-DATA-MARKET_DATA_STORE` | `DAT-003` | — |
| Workbench | `FEAT-DATA-SYNC_CONNECTORS` | `DAT-004`, `DAT-009` | — |
| Workbench | `FEAT-DATA-RESOLVE_QUALITY` | `DAT-005`–`DAT-006` | — |
| Workbench | `FEAT-UI-MANAGE_DATA` | `DAT-007` | — |
| Workbench | `FEAT-DATA-MANAGE_RETENTION` | `DAT-008` | — |
| Workbench | `FEAT-DATA-INGEST_HISTORY` | `DAT-010` | — |
| Workbench | `FEAT-ORCH-DEFINE_PROJECTS` | `PRJ-001`–`PRJ-003`, `PRJ-010` | — |
| Workbench | `FEAT-ORCH-RUN_PROJECTS` | `PRJ-004`–`PRJ-005`, `PRJ-007`, `PRJ-011`–`PRJ-012` | — |
| Workbench | `FEAT-PLUG-SANDBOX_PERMISSIONS` | `PRJ-006` | — |
| Workbench | `FEAT-ORCH-EVALUATE_CONDITIONS` | `PRJ-008`–`PRJ-009` | — |
| Workbench | `FEAT-UI-EDIT_STRATEGIES` | `STU-010`, `AST-008` | — |
| Workbench | `FEAT-SIM-SIMULATE_ORDERS` | `STU-006`, `AST-005`–`AST-006`, `AST-011` | — |
| Workbench | `FEAT-AGT-COMPOSE_STRATEGY_SPECS` | `STU-008`, `AST-010` | — |
| Workbench | `FEAT-PLUG-DEVELOP_EXTENSIONS` | `CED-001`–`CED-002`, `CED-004` | — |
| Workbench | `FEAT-PLUG-MANAGE_LIFECYCLE` | `CED-005` | — |
| Workbench | `FEAT-STRAT-PACKAGE_STRATEGIES` | `CED-006` | — |
| Workbench | `FEAT-INDI-TEST_INDICATORS` | `CED-007` | — |
| Workbench | `FEAT-UI-PRESENT_OVERLAYS` | `MOD-001`–`MOD-006` | — |
| Workbench | `FEAT-UI-RENDER_CHARTS` | `CHR-001`–`CHR-007` | — |
| Engine | `FEAT-STRAT-COMPILE_STRATEGIES` | `AST-012` | — |
| Engine | `FEAT-RES-TRAIN_NEURAL_MODELS` | `NRL-001`–`NRL-010` | — |
| Engine | `FEAT-ORCH-DISTRIBUTE_WORKERS` | `WRK-001`–`WRK-010` | — |
| Tick | `FEAT-SIM-MANAGE_TICK_METHODS` | `TCK-001`–`TCK-002`, `TCK-006`, `TCK-008` | — |
| Tick | `FEAT-SIM-SIMULATE_ORDERS` | `TCK-003`–`TCK-005`, `TCK-007` | — |
| Agentic | `FEAT-AGT-ENFORCE_MANDATE` | `FR-AGT-VALIDATE_MANDATE`, `FR-AGT-ENFORCE_AUTHORITY_BOUNDARY`, `FR-AGT-FAIL_CLOSED_ON_MANDATE` | — |
| Agentic | `FEAT-AGT-OPERATE_RUNS` | `FR-AGT-RECORD_OPERATIONS`, `FR-AGT-CONTAIN_INCIDENTS`, `FR-AGT-VALIDATE_REPLAY`, `FR-AGT-PUBLISH_AGENTIC_READINESS` | — |
| Agentic | `FEAT-AGT-REGISTER_ROLES` | `FR-AGT-REGISTER_ROLE_CONTRIBUTIONS`, `FR-AGT-VERIFY_ROLE_ARTIFACTS`, `FR-AGT-RESOLVE_ELIGIBLE_ROLES` | — |
| Agentic | `FEAT-AGT-GOVERN_TOOL_CALLS` | `FR-AGT-REGISTER_AGENTIC_TOOLS`, `FR-AGT-ISSUE_CAPABILITY_LEASES`, `FR-AGT-ENFORCE_TOOL_INVOCATIONS`, `FR-AGT-FILTER_TOOL_RESULTS`, `FR-AGT-BIND_TYPED_HUMAN_ACTIONS` | — |
| Agentic | `FEAT-AGT-INVOKE_MODELS` | `FR-AGT-PIN_MODEL_INVOCATIONS`, `FR-AGT-ENFORCE_MODEL_BUDGETS`, `FR-AGT-REFUSE_SILENT_MODEL_SUBSTITUTION`, `FR-AGT-CONTAIN_MODEL_OUTPUT` | — |
| Agentic | `FEAT-AGT-RUN_WORKFLOWS` | `FR-AGT-SUBMIT_WORKFLOWS`, `FR-AGT-CHECKPOINT_WORKFLOWS`, `FR-AGT-BOUND_ADAPTIVE_ESCALATION`, `FR-AGT-TERMINATE_WORKFLOWS`, `FR-AGT-APPLY_BACKPRESSURE` | — |
| Agentic | `FEAT-AGT-ASSEMBLE_CONTEXT` | `FR-AGT-ASSEMBLE_POINT_IN_TIME_CONTEXT`, `FR-AGT-SEPARATE_EVIDENCE_FROM_INSTRUCTIONS`, `FR-AGT-REPORT_CONTEXT_EXCLUSIONS`, `FR-AGT-BOUND_CONTEXT_SIZE` | — |
| Agentic | `FEAT-AGT-MANAGE_MEMORY` | `FR-AGT-CLASSIFY_MEMORY`, `FR-AGT-PROMOTE_MEMORY`, `FR-AGT-RETRIEVE_MEMORY`, `FR-AGT-RETAIN_AND_PURGE_MEMORY` | — |
| Agentic | `FEAT-AGT-EVALUATE_PROFILES` | `FR-AGT-EVALUATE_PROFILES`, `FR-AGT-ABLATE_TOPOLOGIES`, `FR-AGT-DETERMINE_PROFILE_ELIGIBILITY`, `FR-AGT-CALIBRATE_GRADERS` | — |
| Agentic | `FEAT-AGT-ASSIST_OPERATOR` | `FR-AGT-READ_WORKSPACE_CONTEXT`, `FR-AGT-ANSWER_CONTEXTUAL_QUESTIONS`, `FR-AGT-ROUTE_SPECIALIST_QUESTIONS`, `FR-AGT-PRESERVE_CHAT_HANDOFF_LINEAGE`, `FR-AGT-RESTRICT_CHAT_ACTIONS` | — |
| Agentic | `FEAT-AGT-MANAGE_CLAIMS` | `FR-AGT-CREATE_TYPED_CLAIMS`, `FR-AGT-LINK_CLAIM_EVIDENCE`, `FR-AGT-PROPAGATE_CLAIM_STATUS`, `FR-AGT-ASSESS_CLAIM_RELIABILITY` | — |
| Agentic | `FEAT-AGT-DELIBERATE_RESEARCH` | `FR-AGT-COLLECT_INDEPENDENT_CHALLENGES`, `FR-AGT-PRESERVE_DELIBERATION_DISSENT`, `FR-AGT-BOUND_DELIBERATION`, `FR-AGT-STOP_LOW_VALUE_DELIBERATION` | — |
| Agentic | `FEAT-AGT-SYNTHESIZE_RESEARCH` | `FR-AGT-SYNTHESIZE_CLAIM_GRAPHS`, `FR-AGT-PRESERVE_SYNTHESIS_UNCERTAINTY`, `FR-AGT-REFUSE_UNSUPPORTED_SYNTHESIS` | — |
| Agentic | `FEAT-AGT-GOVERN_RESEARCH_SEARCH` | `FR-AGT-REGISTER_RESEARCH_CAMPAIGNS`, `FR-AGT-ACCOUNT_RESEARCH_VARIANTS`, `FR-AGT-PRESERVE_FAILED_ATTEMPTS`, `FR-AGT-GOVERN_HOLDOUT_REQUESTS` | — |
| Agentic | `FEAT-AGT-DESIGN_RESEARCH` | `FR-AGT-DESIGN_FALSIFIABLE_HYPOTHESES`, `FR-AGT-COMPOSE_EXPERIMENT_REQUESTS`, `FR-AGT-COMPOSE_SEARCH_REQUESTS`, `FR-AGT-BIND_RESEARCH_PROTOCOLS` | — |
| Agentic | `FEAT-AGT-COMPOSE_STRATEGY_SPECS` | `FR-AGT-COMPOSE_STRATEGY_DSL`, `FR-AGT-VALIDATE_DSL_HANDOFF`, `FR-AGT-REPORT_UNSUPPORTED_EXPRESSIONS`, `FR-AGT-PRESERVE_DSL_PROVENANCE` | — |
| Agentic | `FEAT-AGT-ADVISE_PORTFOLIO` | `FR-AGT-ADVISE_PORTFOLIO_ALLOCATION`, `FR-AGT-CHALLENGE_PORTFOLIO_RISK`, `FR-AGT-EXPIRE_PORTFOLIO_ADVICE`, `FR-AGT-PRESERVE_PORTFOLIO_AUTHORITY` | — |
| Agentic | `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS` | `FR-AGT-COMPOSE_STRATEGY_PROPOSALS`, `FR-AGT-SUBMIT_STRATEGY_PROPOSALS`, `FR-AGT-RECORD_STRATEGY_RECEIPTS`, `FR-AGT-PRESERVE_STRATEGY_AUTHORITY` | — |
| Agentic | `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS` | `FR-AGT-PROVE_DSL_GAP`, `FR-AGT-AUTHOR_SANDBOX_ARTIFACTS`, `FR-AGT-RECORD_ARTIFACT_MANIFEST`, `FR-AGT-ENFORCE_STAGING_ONLY`, `FR-AGT-CLEANUP_SANDBOX_ARTIFACTS` | — |
| Agentic | `FEAT-AGT-CALIBRATE_OUTCOMES` | `FR-AGT-MATCH_OUTCOMES`, `FR-AGT-SCORE_CALIBRATION`, `FR-AGT-ATTRIBUTE_INCREMENTAL_VALUE`, `FR-AGT-PROPOSE_PROFILE_CHANGES` | — |
<!-- PRIMARY_REQUIREMENTS_END -->

## 6. Feature-specific non-functional ownership

<!-- FEATURE_NFR_START -->
| Class | Primary feature | Source IDs | Scope |
|---|---|---|---|
| FEATURE_NFR | `FEAT-SIM-SIMULATE_ORDERS` | `PER-001`, `PER-005` | Exact feature obligation; shared gates remain referenced separately. |
| FEATURE_NFR | `FEAT-ORCH-ADMIT_RESOURCES` | `PER-002`, `PER-006` | Exact feature obligation; shared gates remain referenced separately. |
| FEATURE_NFR | `FEAT-DATA-MARKET_DATA_STORE` | `PER-003`–`PER-004` | Exact feature obligation; shared gates remain referenced separately. |
| FEATURE_NFR | `FEAT-AGT-INVOKE_MODELS` | `PER-007` | Exact feature obligation; shared gates remain referenced separately. |
| FEATURE_NFR | `FEAT-UI-OPERATE_WORKSPACE` | `PER-008` | Exact feature obligation; shared gates remain referenced separately. |
| FEATURE_NFR | `FEAT-RES-GENERATE_STRATEGIES` | `PER-009` | Exact feature obligation; shared gates remain referenced separately. |
| FEATURE_NFR | `FEAT-ORCH-MEASURE_PERFORMANCE` | `PER-010`–`PER-012` | Exact feature obligation; shared gates remain referenced separately. |
<!-- FEATURE_NFR_END -->

## 7. Shared NFR catalogue

<!-- SHARED_NFR_START -->
| Class | Applicability | Source IDs |
|---|---|---|
| PLATFORM | All applicable features | `NFR-P-001`–`NFR-P-016`, `NFR-R-001`–`NFR-R-005`, `NFR-S-001`–`NFR-S-006`, `NFR-A-001`–`NFR-A-006` |
| FINANCIAL_INTEGRITY | All research/evidence/strategy/simulation/optimization/portfolio/Agentic/UI/export features | `NFR-F-001`–`NFR-F-005` |
| AGENTIC_DOMAIN | All `FEAT-AGT-*` plus Agentic gateway/widget where applicable | `NFR-AGT-SECURITY`, `NFR-AGT-AUTHORITY`, `NFR-AGT-RELIABILITY`, `NFR-AGT-REPRODUCIBILITY`, `NFR-AGT-OBSERVABILITY`, `NFR-AGT-PERFORMANCE`, `NFR-AGT-DATA_GOVERNANCE`, `NFR-AGT-MODEL_GOVERNANCE`, `NFR-AGT-EVALUATION`, `NFR-AGT-COMPATIBILITY`, `NFR-AGT-REMOVABILITY`, `NFR-AGT-PRIVACY`, `NFR-AGT-CHAT_CONTEXT`, `NFR-AGT-COVERAGE` |
<!-- SHARED_NFR_END -->

## 8. Non-additive master overlays

<!-- OVERLAY_REQUIREMENTS_START -->
| Disposition | Primary feature | Source IDs | Rule |
|---|---|---|---|
| SUMMARY_OVERLAY | `FEAT-STRAT-DEFINE_STRATEGIES` | `FR-STR-001`–`FR-STR-002` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-STRAT-GENERATE_TARGETS` | `FR-STR-003` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-RES-GENERATE_STRATEGIES` | `FR-RES-001` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-RES-QUALIFY_STRATEGIES` | `FR-RES-002`, `FR-RES-004` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-OPT-SEARCH_PARAMETERS` | `FR-RES-003` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-SIM-SIMULATE_ORDERS` | `FR-SIM-001` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-SIM-RETEST_STRATEGIES` | `FR-SIM-002` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-ANLT-QUERY_RESULTS` | `FR-ANA-001` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-ANLT-MANAGE_DATABANKS` | `FR-ANA-002` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-ANLT-INTERPRET_RESULTS` | `FR-ANA-003` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-ANLT-ANALYZE_TRADES` | `FR-ANA-004` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-ANLT-ANALYZE_CORRELATION` | `FR-ANA-005` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-PLUG-RENDER_RESULT_PANELS` | `FR-ANA-006` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-PORT-COMPOSE_PORTFOLIOS` | `FR-POR-001` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-PORT-SIMULATE_PORTFOLIOS` | `FR-POR-002` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-PORT-SEARCH_PORTFOLIOS` | `FR-POR-003` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-ORCH-DEFINE_PROJECTS` | `FR-ORC-001` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-ORCH-RUN_PROJECTS` | `FR-ORC-002` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-ORCH-EVALUATE_CONDITIONS` | `FR-ORC-003` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-DATA-BROWSE_REFERENCE` | `FR-DAT-001` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-DATA-INGEST_HISTORY` | `FR-DAT-002` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-DATA-RESOLVE_QUALITY` | `FR-DAT-003` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-PLUG-MANAGE_LIFECYCLE` | `FR-PLG-001` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-PLUG-ISOLATE_ANALYSIS` | `FR-PLG-002` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-IFACE-SERVE_API_EVENTS` | `FR-IF-001`–`FR-IF-002` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-UI-OPERATE_WORKSPACE` | `FR-UI-001` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
| SUMMARY_OVERLAY | `FEAT-UI-PRESENT_RESULTS` | `FR-UI-002`–`FR-UI-004` | Summary binding only; primary behavior is in §§4–19/36–40/52/56. |
<!-- OVERLAY_REQUIREMENTS_END -->

## 9. Decisions, integrations, workflows, extensions, and performance controls

<!-- CONTROL_COVERAGE_START -->
| Disposition | Primary feature / governance | Source IDs | Treatment |
|---|---|---|---|
| FEATURE_CONTROL | `FEAT-STRAT-DEFINE_STRATEGIES` | `DEC-001` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| SHARED_GOVERNANCE | SHARED-GOVERNANCE | `DEC-002`–`DEC-005` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-UI-OPERATE_WORKSPACE` | `DEC-006` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-UI-RENDER_CHARTS` | `DEC-007` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-PLUG-ISOLATE_ANALYSIS` | `DEC-008` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-STRAT-GENERATE_TARGETS` | `DEC-009` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-STRAT-EXCHANGE_STRATEGIES` | `DEC-010` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-AGT-COMPOSE_STRATEGY_SPECS` | `DEC-011` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-ORCH-DISTRIBUTE_WORKERS` | `DEC-012` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-RES-TRAIN_NEURAL_MODELS` | `DEC-013` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| SHARED_GOVERNANCE | SHARED-GOVERNANCE | `DEC-014` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-STRAT-PACKAGE_STRATEGIES` | `DEC-015` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-UI-OPERATE_WORKSPACE` | `DEC-016` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| FEATURE_CONTROL | `FEAT-DATA-SYNC_CONNECTORS` | `DEC-017` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| SHARED_GOVERNANCE | SHARED-GOVERNANCE | `REC-001`–`REC-030` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| SHARED_INTEGRATION | SHARED-GOVERNANCE | `INT-PLATFORM-01`, `INT-JOBS-01`, `INT-MODEL-01`, `INT-EVIDENCE-01`, `INT-RESEARCH-01`, `INT-OPTIMIZATION-01`, `INT-STRATEGY-01`, `INT-ADVISORY-01`, `INT-OUTCOME-01`, `INT-CONVERSATION-01`, `INT-SANDBOX-01`, `INT-TICKS-01`, `INT-NATIVE-01`, `INT-RESOURCES-01` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-ASSIST_OPERATOR` | `WF-AGT-ASSIST_OPERATOR` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-MANAGE_CLAIMS` | `WF-AGT-REVIEW_EVIDENCE` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-RUN_WORKFLOWS` | `WF-AGT-RESEARCH_OBJECTIVE` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-DESIGN_RESEARCH` | `WF-AGT-DESIGN_RESEARCH` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-GOVERN_RESEARCH_SEARCH` | `WF-AGT-GOVERNED_SEARCH` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-COMPOSE_STRATEGY_SPECS` | `WF-AGT-COMPOSE_STRATEGY_SPEC` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-ADVISE_PORTFOLIO` | `WF-AGT-ADVISE_PORTFOLIO` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS` | `WF-AGT-COMPOSE_STRATEGY_PROPOSAL` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS` | `WF-AGT-AUTHOR_SANDBOX_ARTIFACT` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-EVALUATE_PROFILES` | `WF-AGT-EVALUATE_PROFILE` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-CALIBRATE_OUTCOMES` | `WF-AGT-CALIBRATE_OUTCOME` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| WORKFLOW | `FEAT-AGT-OPERATE_RUNS` | `WF-AGT-RESPOND_INCIDENT` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| BENCHMARK | `FEAT-ORCH-MEASURE_PERFORMANCE` | `BM-TICK-01`, `BM-TICK-02`, `BM-TICK-03`, `BM-TICK-20Y`, `BM-DATA-01`, `BM-IND-01`, `BM-SEARCH-01`, `BM-ANA-01`, `BM-PORT-01`, `BM-APP-01`, `BM-LIFE-01`, `BM-EXT-01` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| PERFORMANCE_TASK | `FEAT-ORCH-MEASURE_PERFORMANCE` | `PERF-00`, `PERF-01`, `PERF-02`, `PERF-03`, `PERF-04`, `PERF-05`, `PERF-06`, `PERF-07`, `PERF-08`, `PERF-09`, `PERF-10`, `PERF-11`, `PERF-12`, `PERF-13`, `PERF-14`, `PERF-15`, `PERF-16` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| PERFORMANCE_GATE | `FEAT-ORCH-MEASURE_PERFORMANCE` | `PERF-G01`, `PERF-G02`, `PERF-G03`, `PERF-G04`, `PERF-G05`, `PERF-G06`, `PERF-G07`, `PERF-G08`, `PERF-G09`, `PERF-G10`, `PERF-G11`, `PERF-G12` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| EXTENSION | `FEAT-UI-RENDER_CHARTS` | `EXT-001` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| EXTENSION | `FEAT-INDI-ANALYZE_MARKET_PROFILE` | `EXT-002` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| EXTENSION | `FEAT-PORT-OPTIMIZE_WEIGHTS` | `EXT-003` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| EXTENSION | `FEAT-STRAT-PACKAGE_STRATEGIES` | `EXT-004` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| EXTENSION | `FEAT-DATA-SYNC_CONNECTORS` | `EXT-005` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| EXTENSION | `FEAT-AGT-ASSIST_OPERATOR` | `EXT-006` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| EXTENSION | `FEAT-PLUG-DEVELOP_EXTENSIONS` | `EXT-007` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
| EXTENSION | `FEAT-ORCH-RUN_PROJECTS` | `EXT-008` | Delivered or enforced through the named feature; shared rows constrain all affected cards. |
<!-- CONTROL_COVERAGE_END -->

### 9.1 Milestone and implementation-task dispositions

Milestones and implementation tasks schedule or gate delivery; they do not create extra product features. Each stable identifier nevertheless has one explicit delivery disposition.

<!-- DELIVERY_COVERAGE_START -->
| Class | Primary feature/disposition | Source IDs | Treatment |
|---|---|---|---|
| MILESTONE | SHARED_ROADMAP | `U0`, `U1`, `U2`, `U3`, `U4`, `U5`, `U6`, `U7`, `U8`, `U9`, `U10`, `U11`, `U12`, `U13` | Sequencing and exit gates; non-additive to feature and requirement counts. |
| AGENTIC_TASK | SHARED_AGENTIC_FOUNDATION | `AGT-0.01`, `AGT-0.02`, `AGT-0.03`, `AGT-0.04`, `AGT-0.05`, `AGT-0.06`, `AGT-0.07`, `AGT-0.08`, `AGT-0.09`, `AGT-0.10`, `AGT-0.11`, `AGT-0.GATE`, `AGT-1.00` | Contract, ownership, evidence, readiness, and authorization work shared by the receiving features. |
| AGENTIC_TASK | `FEAT-AGT-ENFORCE_MANDATE` | `AGT-1.01` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-OPERATE_RUNS` | `AGT-1.02` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-REGISTER_ROLES` | `AGT-1.03` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-GOVERN_TOOL_CALLS` | `AGT-1.04` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-INVOKE_MODELS` | `AGT-1.05` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-RUN_WORKFLOWS` | `AGT-2.06` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-ASSEMBLE_CONTEXT` | `AGT-2.07` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-MANAGE_MEMORY` | `AGT-2.08` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-EVALUATE_PROFILES` | `AGT-2.09` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-ASSIST_OPERATOR` | `AGT-2.10` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-MANAGE_CLAIMS` | `AGT-3.11` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-DELIBERATE_RESEARCH` | `AGT-3.12` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-SYNTHESIZE_RESEARCH` | `AGT-3.13` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-GOVERN_RESEARCH_SEARCH` | `AGT-4.14` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-DESIGN_RESEARCH` | `AGT-4.15` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-COMPOSE_STRATEGY_SPECS` | `AGT-5.16` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-ADVISE_PORTFOLIO` | `AGT-5.17` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS` | `AGT-5.18` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS` | `AGT-6.19` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-CALIBRATE_OUTCOMES` | `AGT-6.20` | Feature delivery task; not a second feature identity. |
| AGENTIC_TASK | `FEAT-AGT-ASSIST_OPERATOR` | `AGT-7.01` | First read-only Chat Bot integration slice. |
| AGENTIC_TASK | `FEAT-AGT-DELIBERATE_RESEARCH` | `AGT-7.02` | Adaptive research/deliberation integration suite. |
| AGENTIC_TASK | SHARED_AGENTIC_INTEGRATION | `AGT-7.03`, `AGT-7.04`, `AGT-7.05`, `AGT-7.06` | Cross-feature receiver, security, removability, and final release gates. |
| AGENTIC_TASK | `FEAT-IFACE-AGENTIC_GATEWAY` | `AGT-X-IFACE-01` | Interfaces companion task. |
| AGENTIC_TASK | `FEAT-UI-CHAT_BOT` | `AGT-X-UI-01` | UI companion task. |
<!-- DELIVERY_COVERAGE_END -->

## 10. Numbered-section coverage

Unnumbered catalogues, algorithms, schemas, controls, routes, grids, charts, records, and acceptance prose remain normative through the card source references below. This table prevents an ID-only audit from dropping those clauses.

<!-- SECTION_COVERAGE_START -->
| Sections | Primary disposition | Coverage |
|---|---|---|
| 1–3 | Product/shared governance | Direction, decisions, scope, exclusions, success criteria. |
| 4–20 | Feature cards and workbench ownership | Shell, run grammar, product workbenches, overlays, grids, charts, workflows. |
| 21–26 | Architecture/shared governance plus feature cards | Owners, decomposition, transport, persistence, UI/backend implementation rules. |
| 27–28 | Overlay and shared-NFR matrices | Master FR overlay and all global/integrity NFRs. |
| 29–35 | Delivery/control coverage | Milestones, verification, risks, DoD, references, acceptance register. |
| 36–40 | Strategy/Research/Simulator/Data/Orchestration feature cards | Generator, AST, exchange, neural, worker requirements and algorithms. |
| 41–42 | Shared governance and control coverage | Reconciliation and integration contracts. |
| 43–53 | Agentic feature cards and workflow/control coverage | Features, roles, records, workflows, policies, state, NFRs, tasks, acceptance. |
| 54–55 | Legacy appendix and source coverage | Alias/disposition only; no duplicate current ownership. |
| 56 | Tick, resource, performance feature cards and controls | TCK/PER requirements, workloads, gates, tasks, completion. |
<!-- SECTION_COVERAGE_END -->

## 11. Complete feature cards


## 11.1 Domain — Workspace

<!-- FEATURE_CARD_START FEAT-WS-BUILD_DIAGNOSTICS -->
### FEAT-WS-BUILD_DIAGNOSTICS — Build diagnostic bundles

- **Atomic value:** Give operators a safe, portable explanation of application and run health.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Give operators a safe, portable explanation of application and run health.
- **Does not own:** Transport/presentation or domain calculations outside Workspace's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `SHELL-009`, `RUN-010`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** workspace.diagnostics@1 (target)
- **Depends on:** All domains contribute redacted health projections.

#### Catalogue entries / algorithms / controls delivered

- Help routing, version inventory, redacted traces, diagnostic export.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Redaction, permission, missing-provider, and reproducible-bundle tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-WS-BUILD_DIAGNOSTICS -->

## 11.2 Domain — UI

<!-- FEATURE_CARD_START FEAT-UI-OPERATE_WORKSPACE -->
### FEAT-UI-OPERATE_WORKSPACE — Operate the composable workspace

- **Atomic value:** Let users compose, navigate, persist, recover, and keyboard-operate research widgets without changing domain truth.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Let users compose, navigate, persist, recover, and keyboard-operate research widgets without changing domain truth.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `SHELL-001`–`SHELL-004`, `SHELL-007`–`SHELL-008`, `UI-DCK-001`–`UI-DCK-006`

#### Feature-specific non-functional requirements

- `PER-008`

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Typed widget-manifest and workspace-layout contracts
- **Depends on:** Workspace layout storage; Interfaces capability discovery; every widget owner.

#### Catalogue entries / algorithms / controls delivered

- Research template, docking, navigation, focus, layout migration, unavailable-widget recovery, lazy loading.
- FEATURE_CONTROL: `DEC-006`
- FEATURE_CONTROL: `DEC-016`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Manifest uniqueness, keyboard/focus, layout round-trip/migration, removal, bundle, and browser E2E tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-OPERATE_WORKSPACE -->

<!-- FEATURE_CARD_START FEAT-UI-DISCOVER_COMMANDS -->
### FEAT-UI-DISCOVER_COMMANDS — Discover commands and resources

- **Atomic value:** Provide permission-aware global discovery of commands, resources, and contextual help.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide permission-aware global discovery of commands, resources, and contextual help.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `SHELL-005`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** UI command contribution/query contract (target)
- **Depends on:** Interfaces identity/authorization and registered contributions.

#### Catalogue entries / algorithms / controls delivered

- Command palette, resource search, contextual documentation links.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Permission filtering, keyboard operation, unavailable provider, and result-routing tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-DISCOVER_COMMANDS -->

<!-- FEATURE_CARD_START FEAT-UI-PRESENT_RUNS -->
### FEAT-UI-PRESENT_RUNS — Present durable run state

- **Atomic value:** Keep long-running work observable and controllable independently of any originating widget.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Keep long-running work observable and controllable independently of any originating widget.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `SHELL-006`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Run/job typed client and resumable-event projection
- **Depends on:** Orchestration run owner; Interfaces events.

#### Catalogue entries / algorithms / controls delivered

- Global run monitor, partial/terminal state, pause/stop controls, provenance drill-down.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Unmount/reopen, cursor replay, stale/gap, cancellation, and accessibility E2E tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-PRESENT_RUNS -->

<!-- FEATURE_CARD_START FEAT-UI-DESIGN_RESEARCH_SPACES -->
### FEAT-UI-DESIGN_RESEARCH_SPACES — Design strategy search spaces

- **Atomic value:** Provide a typed Builder surface for strategy-space configuration and effective-plan preview.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide a typed Builder surface for strategy-space configuration and effective-plan preview.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `BLD-003`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Strategy/Research typed clients (target)
- **Depends on:** Strategy catalogue and Research plan validation.

#### Catalogue entries / algorithms / controls delivered

- Builder settings taxonomy, effective search-space preview, stage ordering UI.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Schema rendering, invalid/unavailable provider, keyboard, and snapshot tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-DESIGN_RESEARCH_SPACES -->

<!-- FEATURE_CARD_START FEAT-UI-PRESENT_RESULTS -->
### FEAT-UI-PRESENT_RESULTS — Present result workspaces

- **Atomic value:** Compose result tabs, synchronized selections, bounded grids, charts, and accessible fallbacks.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Compose result tabs, synchronized selections, bounded grids, charts, and accessible fallbacks.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `RES-001`–`RES-002`, `RES-005`–`RES-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Analytics result-projection and typed-selection contracts
- **Depends on:** Analytics, Research, Optimization, Portfolio, Plugins.

#### Catalogue entries / algorithms / controls delivered

- Overview/trades/equity/analysis/WF/Monte Carlo/configuration panels and presentation state.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Cross-panel identity, stale/partial state, large-result, accessibility, and plugin-removal E2E tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-PRESENT_RESULTS -->

<!-- FEATURE_CARD_START FEAT-UI-COMPOSE_PORTFOLIOS -->
### FEAT-UI-COMPOSE_PORTFOLIOS — Compose portfolio workspaces

- **Atomic value:** Provide manual and search portfolio workspaces without owning portfolio mathematics.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide manual and search portfolio workspaces without owning portfolio mathematics.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PFC-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Portfolio typed clients and selection contracts
- **Depends on:** Portfolio and Analytics capabilities.

#### Catalogue entries / algorithms / controls delivered

- Composer/builder editors, normalized-weight display, candidate grids, correlation views.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Draft/dirty state, keyboard, unavailable provider, and result-lineage E2E tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-COMPOSE_PORTFOLIOS -->

<!-- FEATURE_CARD_START FEAT-UI-MANAGE_DATA -->
### FEAT-UI-MANAGE_DATA — Manage research data

- **Atomic value:** Provide pageable data, profile, quality, instrument, session, and connector workflows through owner capabilities.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide pageable data, profile, quality, instrument, session, and connector workflows through owner capabilities.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DAT-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Data/Catalogue typed clients
- **Depends on:** Data, Catalogue, Workspace, Interfaces.

#### Catalogue entries / algorithms / controls delivered

- Data Manager grids, preview/chart levels, quality findings, instruments, sessions, broker profiles.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Paging, LOD disclosure, authorization, destructive confirmation, and degraded-source tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-MANAGE_DATA -->

<!-- FEATURE_CARD_START FEAT-UI-EDIT_STRATEGIES -->
### FEAT-UI-EDIT_STRATEGIES — Edit strategies accessibly

- **Atomic value:** Provide canvas, tree, form, and source projections over one Strategy-owned AST.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide canvas, tree, form, and source projections over one Strategy-owned AST.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `STU-010`, `AST-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Strategy editor projection and patch contracts
- **Depends on:** Strategy catalogue/validation; Agentic candidate patches.

#### Catalogue entries / algorithms / controls delivered

- Canvas/tree/form equivalence, node chooser, structured diff, undo/redo.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Round-trip, keyboard-complete editing, conflict, privacy-scope, and provider-removal tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-EDIT_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-UI-DEVELOP_EXTENSIONS -->
### FEAT-UI-DEVELOP_EXTENSIONS — Develop extensions

- **Atomic value:** Provide authorized code/resource editing and test/build feedback without host authority.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide authorized code/resource editing and test/build feedback without host authority.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Plugins/Workspace development typed clients
- **Depends on:** Plugins sandbox/lifecycle; Workspace artifacts.

#### Catalogue entries / algorithms / controls delivered

- Code editor, resource browser, search, diagnostics, Indicator Tester presentation.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Dirty conflict, path denial, bounded logs, isolation, and keyboard tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-DEVELOP_EXTENSIONS -->

<!-- FEATURE_CARD_START FEAT-UI-PRESENT_OVERLAYS -->
### FEAT-UI-PRESENT_OVERLAYS — Present governed overlays

- **Atomic value:** Provide accessible modals/drawers/confirmations with typed drafts and concrete mutation scope.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide accessible modals/drawers/confirmations with typed drafts and concrete mutation scope.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `MOD-001`–`MOD-006`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Shared UI overlay/draft contract
- **Depends on:** All UI features; domain validation remains authoritative.

#### Catalogue entries / algorithms / controls delivered

- Modal/drawer/confirmation registry, focus/escape, dirty guards, deep-link routing.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Focus trap/restore, nested overlay, dirty close, server error, and destructive-scope tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-PRESENT_OVERLAYS -->

<!-- FEATURE_CARD_START FEAT-UI-RENDER_CHARTS -->
### FEAT-UI-RENDER_CHARTS — Render analytical charts

- **Atomic value:** Render bounded, synchronized, provenance-aware charts with accessible nonvisual alternatives.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Render bounded, synchronized, provenance-aware charts with accessible nonvisual alternatives.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `CHR-001`–`CHR-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** Typed chart-series/selection contract
- **Depends on:** Analytics/Data projections and registered panel contributions.

#### Catalogue entries / algorithms / controls delivered

- Time series, distributions, matrices, 3D optional panels, LOD, table/export fallback.
- FEATURE_CONTROL: `DEC-007`
- EXTENSION: `EXT-001`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Timezone/gap, sampling disclosure, GPU-off, keyboard, memory, and fallback tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-RENDER_CHARTS -->

<!-- FEATURE_CARD_START FEAT-UI-CHAT_BOT -->
### FEAT-UI-CHAT_BOT — Operate the Chat Bot widget

- **Atomic value:** Present fresh workspace context and same-conversation specialist results without direct business mutation.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Present fresh workspace context and same-conversation specialist results without direct business mutation.
- **Does not own:** Transport/presentation or domain calculations outside UI's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`, `NFR-P-005`, `NFR-R-005`, `NFR-S-003`–`NFR-S-004`, `NFR-A-001`–`NFR-A-006`, `NFR-F-001`.

#### Public contracts and dependencies

- **Provides:** ChatContextContribution and Interfaces Agentic client (target)
- **Depends on:** FEAT-IFACE-AGENTIC_GATEWAY; FEAT-AGT-ASSIST_OPERATOR.

#### Catalogue entries / algorithms / controls delivered

- Chat widget, context contributions, streaming attribution/refusal states.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Freshness, widget removal, stream order, accessibility, and no-mutation E2E tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-UI-CHAT_BOT -->

## 11.3 Domain — Strategy

<!-- FEATURE_CARD_START FEAT-STRAT-DEFINE_STRATEGIES -->
### FEAT-STRAT-DEFINE_STRATEGIES — Define and version strategies

- **Atomic value:** Own HSL v2 AST meaning, validation, canonical identity, revisions, templates, and strategy-space schemas.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own HSL v2 AST meaning, validation, canonical identity, revisions, templates, and strategy-space schemas.
- **Does not own:** Transport/presentation or domain calculations outside Strategy's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `BLD-001`, `GEN-003`, `STU-001`, `STU-003`–`STU-004`, `STU-009`, `AST-001`–`AST-004`, `AST-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** strategy.define-ast@1; strategy.version-strategies@1 (target names)
- **Depends on:** Catalogue/Indicators descriptors; Risk sizing references.

#### Catalogue entries / algorithms / controls delivered

- HSL nodes, clocks, variables, orders/exits, templates, symmetry, canonicalization.
- FEATURE_CONTROL: `DEC-001`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Schema/type/context/clock, round-trip, optimistic conflict, symmetry, and no-lookahead tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-STRAT-DEFINE_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-STRAT-CATALOG_BLOCKS -->
### FEAT-STRAT-CATALOG_BLOCKS — Catalogue strategy blocks

- **Atomic value:** Resolve compatible typed building blocks and provider/version metadata.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Resolve compatible typed building blocks and provider/version metadata.
- **Does not own:** Transport/presentation or domain calculations outside Strategy's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `BLD-002`, `STU-002`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** strategy.catalog-blocks@1 (target)
- **Depends on:** Indicators and Plugins contributions.

#### Catalogue entries / algorithms / controls delivered

- Node descriptors, categories, ports, parameters, constraints, availability.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Descriptor golden, compatibility, provider removal/replacement, and ordering tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-STRAT-CATALOG_BLOCKS -->

<!-- FEATURE_CARD_START FEAT-STRAT-COMPILE_STRATEGIES -->
### FEAT-STRAT-COMPILE_STRATEGIES — Compile target-neutral strategies

- **Atomic value:** Lower validated HSL into immutable reusable execution plans without changing meaning.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Lower validated HSL into immutable reusable execution plans without changing meaning.
- **Does not own:** Transport/presentation or domain calculations outside Strategy's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `AST-012`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** strategy.compile-strategies@1
- **Depends on:** Strategy AST and qualified numerical-provider descriptors.

#### Catalogue entries / algorithms / controls delivered

- Typed operations/state, parameter buffers, source maps, native-plan compatibility.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Reference equivalence, source diagnostics, cache identity, overflow, and provider-generation tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-STRAT-COMPILE_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-STRAT-GENERATE_TARGETS -->
### FEAT-STRAT-GENERATE_TARGETS — Generate strategy targets

- **Atomic value:** Produce only declared, semantically verified source/pseudocode artifacts.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Produce only declared, semantically verified source/pseudocode artifacts.
- **Does not own:** Transport/presentation or domain calculations outside Strategy's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DBK-009`, `STU-005`, `AST-009`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** strategy.generate-targets@1 (target)
- **Depends on:** Strategy compiler; Workspace custody; Plugins toolchains where applicable.

#### Catalogue entries / algorithms / controls delivered

- Native JSON, pseudocode, MQL/Python/later target adapters and compatibility reports.
- FEATURE_CONTROL: `DEC-009`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Per-target golden/compile/incompatibility, provenance, and unsupported-node tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-STRAT-GENERATE_TARGETS -->

<!-- FEATURE_CARD_START FEAT-STRAT-EXCHANGE_STRATEGIES -->
### FEAT-STRAT-EXCHANGE_STRATEGIES — Exchange strategy artifacts

- **Atomic value:** Import/export native bundles and isolated external formats with explicit loss and provenance.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Import/export native bundles and isolated external formats with explicit loss and provenance.
- **Does not own:** Transport/presentation or domain calculations outside Strategy's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DBK-010`, `XCH-001`–`XCH-010`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** strategy.exchange-strategies@1 (target)
- **Depends on:** Workspace artifact custody; Plugins sandbox; semantic owners.

#### Catalogue entries / algorithms / controls delivered

- Canonical manifests, hashes, staged import, schema migrations, opaque members, conversion reports.
- FEATURE_CONTROL: `DEC-010`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Hostile archive, corruption, conflict, migration, atomic publication, and round-trip tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-STRAT-EXCHANGE_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-STRAT-PACKAGE_STRATEGIES -->
### FEAT-STRAT-PACKAGE_STRATEGIES — Package strategies

- **Atomic value:** Build reproducible distribution packages without deploying or activating trading.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Build reproducible distribution packages without deploying or activating trading.
- **Does not own:** Transport/presentation or domain calculations outside Strategy's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `CED-006`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** strategy.package-strategies@1 (target)
- **Depends on:** Plugins isolated build; Workspace custody.

#### Catalogue entries / algorithms / controls delivered

- Package metadata/resources/restrictions, SBOM, target builds.
- FEATURE_CONTROL: `DEC-015`
- EXTENSION: `EXT-004`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Reproducible hash, secret exclusion, restriction compatibility, and no-deployment tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-STRAT-PACKAGE_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-STRAT-ACCEPT_PROPOSALS -->
### FEAT-STRAT-ACCEPT_PROPOSALS — Accept reviewed strategy candidates

- **Atomic value:** Validate and record user-reviewed Agentic or external candidates as Strategy-owned revisions/receipts.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Validate and record user-reviewed Agentic or external candidates as Strategy-owned revisions/receipts.
- **Does not own:** Transport/presentation or domain calculations outside Strategy's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `OPT-009`, `STU-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** strategy.proposal-intake@1 (target)
- **Depends on:** Agentic candidate producers; Strategy validator/version owner.

#### Catalogue entries / algorithms / controls delivered

- Structured patch review, candidate intake, rejection/receipt, explicit promotion action.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Idempotency, conflict, malformed candidate, granular acceptance, and authority-boundary tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-STRAT-ACCEPT_PROPOSALS -->

## 11.4 Domain — Research

<!-- FEATURE_CARD_START FEAT-RES-GENERATE_STRATEGIES -->
### FEAT-RES-GENERATE_STRATEGIES — Generate strategy candidates

- **Atomic value:** Run bounded random, seeded, evolutionary, and advanced candidate search with complete lineage.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Run bounded random, seeded, evolutionary, and advanced candidate search with complete lineage.
- **Does not own:** Transport/presentation or domain calculations outside Research's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `BLD-004`, `BLD-006`, `GEN-001`–`GEN-002`, `GEN-004`–`GEN-006`, `GEN-008`, `GEN-010`

#### Feature-specific non-functional requirements

- `PER-009`

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** research.generate-strategies@1 (target)
- **Depends on:** Strategy grammar/compiler; Simulator; Analytics; Orchestration admission.

#### Catalogue entries / algorithms / controls delivered

- Full/Grow/ramped initialization, islands, crossover/mutation, diversity, Pareto ranking, deduplication.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Seed golden, operator properties, lineage, budget, deterministic reduction, and replay tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-RES-GENERATE_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-RES-QUALIFY_STRATEGIES -->
### FEAT-RES-QUALIFY_STRATEGIES — Qualify research evidence

- **Atomic value:** Own ordered robustness/cross-check/acceptance policy and explain every rejection or promotion.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own ordered robustness/cross-check/acceptance policy and explain every rejection or promotion.
- **Does not own:** Transport/presentation or domain calculations outside Research's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `BLD-005`, `BLD-009`, `GEN-007`, `GEN-009`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** research.test-robustness@1; research.accept-research@1 (target)
- **Depends on:** Simulator/Analytics/Optimization evidence; campaign governance.

#### Catalogue entries / algorithms / controls delivered

- Cross-check pipelines, sample policy, hard filters, robustness verdicts, rejection taxonomy.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Threshold boundary, stage ordering, null metric, sample isolation, and explainability tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-RES-QUALIFY_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-RES-GOVERN_CAMPAIGNS -->
### FEAT-RES-GOVERN_CAMPAIGNS — Govern research campaigns

- **Atomic value:** Own campaign, family, protocol, budget, holdout, attempt, and sealed-sample truth for every caller.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own campaign, family, protocol, budget, holdout, attempt, and sealed-sample truth for every caller.
- **Does not own:** Transport/presentation or domain calculations outside Research's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `BLD-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** research.campaigns@1; research.holdouts@1 (target)
- **Depends on:** Orchestration resources; Strategy/Data immutable identities.

#### Catalogue entries / algorithms / controls delivered

- Campaign/family ledger, pre-registration, variant accounting, holdout reservations, budgets.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Near-duplicate, budget reconciliation, holdout race/reuse, provenance, and restart tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-RES-GOVERN_CAMPAIGNS -->

<!-- FEATURE_CARD_START FEAT-RES-TRAIN_NEURAL_MODELS -->
### FEAT-RES-TRAIN_NEURAL_MODELS — Train research models

- **Atomic value:** Create leakage-controlled, versioned research model evidence and portable qualified inference artifacts.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Create leakage-controlled, versioned research model evidence and portable qualified inference artifacts.
- **Does not own:** Transport/presentation or domain calculations outside Research's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `NRL-001`–`NRL-010`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** research.train-networks@1 (target)
- **Depends on:** Data features/labels; Orchestration jobs; Strategy model nodes.

#### Catalogue entries / algorithms / controls delivered

- Fitted preprocessing, labels, MLP/TCN/LSTM/GRU providers, checkpoints, model cards, inference vectors.
- FEATURE_CONTROL: `DEC-013`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Temporal leakage, deterministic baseline, checkpoint, calibration, OOD, and golden-vector tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-RES-TRAIN_NEURAL_MODELS -->

## 11.5 Domain — Simulator

<!-- FEATURE_CARD_START FEAT-SIM-SIMULATE_ORDERS -->
### FEAT-SIM-SIMULATE_ORDERS — Simulate orders on ticks

- **Atomic value:** Own deterministic tick-event execution, fills, costs, exits, valuation, checkpoints, and result truth.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own deterministic tick-event execution, fills, costs, exits, valuation, checkpoints, and result truth.
- **Does not own:** Transport/presentation or domain calculations outside Simulator's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `STU-006`, `AST-005`–`AST-006`, `AST-011`
- `TCK-003`–`TCK-005`, `TCK-007`

#### Feature-specific non-functional requirements

- `PER-001`, `PER-005`

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** simulator.simulate-orders@1 (target)
- **Depends on:** Data tick streams; Strategy plans; Indicators; Risk/Trading pure policies; Orchestration admission.

#### Catalogue entries / algorithms / controls delivered

- Ordered event engine, order/fill state, exact money policy, output profiles, checkpoints.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: No-lookahead, event order, fill/cost/exit, chunk/restart equivalence, cancellation, and native oracle tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-SIM-SIMULATE_ORDERS -->

<!-- FEATURE_CARD_START FEAT-SIM-RETEST_STRATEGIES -->
### FEAT-SIM-RETEST_STRATEGIES — Retest strategies

- **Atomic value:** Re-evaluate immutable strategy populations under changed data/cost/precision/perturbation contexts.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Re-evaluate immutable strategy populations under changed data/cost/precision/perturbation contexts.
- **Does not own:** Transport/presentation or domain calculations outside Simulator's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `RET-001`–`RET-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** simulator.perturb-inputs@1 (target)
- **Depends on:** Strategy, Data, Research qualification, Analytics metrics.

#### Catalogue entries / algorithms / controls delivered

- Batch selection, perturbations, precision methods, baseline deltas, partial results.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Seed replay, immutable source, multi-context, cancellation boundary, and routing tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-SIM-RETEST_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-SIM-MANAGE_TICK_METHODS -->
### FEAT-SIM-MANAGE_TICK_METHODS — Manage tick methods

- **Atomic value:** Select, validate, generate/consume, and disclose exact recorded/generated tick evidence for every backtest.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Select, validate, generate/consume, and disclose exact recorded/generated tick evidence for every backtest.
- **Does not own:** Transport/presentation or domain calculations outside Simulator's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `TCK-001`–`TCK-002`, `TCK-006`, `TCK-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** simulator.tick-methods@1 (target)
- **Depends on:** Data normalization/store/scenario features.

#### Catalogue entries / algorithms / controls delivered

- TickMethodSpec, TickStreamManifest, coverage classes, generation seeds, event counts.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Every-caller preflight, no fallback/thinning, count reconciliation, provider removal, and evidence disclosure tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-SIM-MANAGE_TICK_METHODS -->

## 11.6 Domain — Optimization

<!-- FEATURE_CARD_START FEAT-OPT-SEARCH_PARAMETERS -->
### FEAT-OPT-SEARCH_PARAMETERS — Search strategy parameters

- **Atomic value:** Own bounded parameter spaces, trials, search methods, checkpoints, surfaces, and reproducible exports.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own bounded parameter spaces, trials, search methods, checkpoints, surfaces, and reproducible exports.
- **Does not own:** Transport/presentation or domain calculations outside Optimization's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `OPT-001`–`OPT-003`, `OPT-005`–`OPT-006`, `OPT-010`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** optimization.search@1 (target)
- **Depends on:** Strategy revisions; Simulator; Analytics; Orchestration admission.

#### Catalogue entries / algorithms / controls delivered

- Cartesian/sequential/evolutionary methods, trial ledger, combination bounds, surface retention.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Range/cardinality, deterministic seed/tie, checkpoint/cancel, complete-trial, and export tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-OPT-SEARCH_PARAMETERS -->

<!-- FEATURE_CARD_START FEAT-OPT-VALIDATE_WALK_FORWARD -->
### FEAT-OPT-VALIDATE_WALK_FORWARD — Validate walk-forward stability

- **Atomic value:** Own WFO/WFM window mechanics and stability surfaces while Research owns qualification policy.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own WFO/WFM window mechanics and stability surfaces while Research owns qualification policy.
- **Does not own:** Transport/presentation or domain calculations outside Optimization's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `OPT-004`, `OPT-007`–`OPT-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** optimization.walk-forward@1 (target)
- **Depends on:** Optimization trials; Research protocols; Simulator/Analytics evidence.

#### Catalogue entries / algorithms / controls delivered

- Sequential optimization, WFO/WFM matrices, parameter permutation, stability regions.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Window/overlap, threshold boundary, sample identity, insufficient data, and provenance tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-OPT-VALIDATE_WALK_FORWARD -->

## 11.7 Domain — Analytics

<!-- FEATURE_CARD_START FEAT-ANLT-MANAGE_DATABANKS -->
### FEAT-ANLT-MANAGE_DATABANKS — Manage databanks

- **Atomic value:** Own versioned result membership, stable selection, saved views, and governed bulk actions.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own versioned result membership, stable selection, saved views, and governed bulk actions.
- **Does not own:** Transport/presentation or domain calculations outside Analytics's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `BLD-007`, `DBK-001`–`DBK-006`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** analytics.databank-membership@1; analytics.bulk-databank@1
- **Depends on:** Analytics queries; Strategy/Workspace exchange.

#### Catalogue entries / algorithms / controls delivered

- Databank definitions, snapshot membership, bulk move/copy/delete, dynamic columns/views.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Atomic membership, page-independent selection, reference checks, conflict, and large-grid tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ANLT-MANAGE_DATABANKS -->

<!-- FEATURE_CARD_START FEAT-ANLT-QUERY_RESULTS -->
### FEAT-ANLT-QUERY_RESULTS — Query results

- **Atomic value:** Provide bounded cursor-based result/trade/series projections over immutable snapshots.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide bounded cursor-based result/trade/series projections over immutable snapshots.
- **Does not own:** Transport/presentation or domain calculations outside Analytics's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DBK-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** analytics.query-results@1
- **Depends on:** Simulator/Workspace artifacts; metric definitions.

#### Catalogue entries / algorithms / controls delivered

- Paging, sorting, filtering, projections, cursors, LOD chunks.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Cursor expiry/resync, 1M-row/10M-trade fixtures, memory, and identity tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ANLT-QUERY_RESULTS -->

<!-- FEATURE_CARD_START FEAT-ANLT-INTERPRET_RESULTS -->
### FEAT-ANLT-INTERPRET_RESULTS — Interpret results

- **Atomic value:** Own canonical metrics, comparisons, provenance, null semantics, and report projections.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own canonical metrics, comparisons, provenance, null semantics, and report projections.
- **Does not own:** Transport/presentation or domain calculations outside Analytics's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `RES-OV-001`–`RES-OV-004`, `RES-003`–`RES-004`, `RES-008`, `RES-010`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** analytics.interpret-results@1
- **Depends on:** Simulator results; Strategy/Data identities; Plugins templates.

#### Catalogue entries / algorithms / controls delivered

- Metric descriptors, overview, comparison, warnings, provenance-complete reports.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Metric golden, currency/sample compatibility, null reason, stale/partial, and export tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ANLT-INTERPRET_RESULTS -->

<!-- FEATURE_CARD_START FEAT-ANLT-ANALYZE_TRADES -->
### FEAT-ANLT-ANALYZE_TRADES — Analyze trades

- **Atomic value:** Own trade/equity/time-series analytical projections and cross-panel trade identity.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own trade/equity/time-series analytical projections and cross-panel trade identity.
- **Does not own:** Transport/presentation or domain calculations outside Analytics's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `RES-TRD-001`–`RES-TRD-004`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** analytics.analyze-trades@1
- **Depends on:** Result queries; Data market series.

#### Catalogue entries / algorithms / controls delivered

- Trade ledger, equity, MAE/MFE, distributions, periods, trades-on-chart.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Timezone, selection identity, missing tick path, series bounds, and export tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ANLT-ANALYZE_TRADES -->

<!-- FEATURE_CARD_START FEAT-ANLT-ANALYZE_CORRELATION -->
### FEAT-ANLT-ANALYZE_CORRELATION — Analyze result correlation

- **Atomic value:** Compute aligned correlation and explain deterministic retain/remove decisions.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Compute aligned correlation and explain deterministic retain/remove decisions.
- **Does not own:** Transport/presentation or domain calculations outside Analytics's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DBK-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** analytics.match-results@1 (target)
- **Depends on:** Result queries and metric definitions.

#### Catalogue entries / algorithms / controls delivered

- Alignment policy, coefficient/method, threshold, tie-break decision artifacts.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Insufficient overlap, currency/frequency, coefficient, negative handling, and tie-break goldens.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ANLT-ANALYZE_CORRELATION -->

## 11.8 Domain — Portfolio

<!-- FEATURE_CARD_START FEAT-PORT-COMPOSE_PORTFOLIOS -->
### FEAT-PORT-COMPOSE_PORTFOLIOS — Compose portfolios

- **Atomic value:** Own versioned constituents, weights, capital/leverage/sizing compatibility, and portfolio revisions.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own versioned constituents, weights, capital/leverage/sizing compatibility, and portfolio revisions.
- **Does not own:** Transport/presentation or domain calculations outside Portfolio's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PFC-001`–`PFC-004`, `PFC-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** portfolio.compose-portfolios@1 (target)
- **Depends on:** Strategy/Analytics references; Risk policies.

#### Catalogue entries / algorithms / controls delivered

- Constituent registry, raw/normalized weights, benchmarks, composition revisions.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Weight normalization, currency/sizing, conflict, duplicate, and optimistic-revision tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PORT-COMPOSE_PORTFOLIOS -->

<!-- FEATURE_CARD_START FEAT-PORT-SIMULATE_PORTFOLIOS -->
### FEAT-PORT-SIMULATE_PORTFOLIOS — Simulate portfolios

- **Atomic value:** Produce combined interacting-capital portfolio results with constituent lineage.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Produce combined interacting-capital portfolio results with constituent lineage.
- **Does not own:** Transport/presentation or domain calculations outside Portfolio's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PFC-005`, `PFM-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** portfolio.simulate-portfolios@1 (target)
- **Depends on:** Simulator, Analytics, Strategy, Risk.

#### Catalogue entries / algorithms / controls delivered

- Combined accounting, benchmark, per-constituent/combined evidence.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Accounting fixtures, missing constituent, cancellation, lineage, and reproducibility tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PORT-SIMULATE_PORTFOLIOS -->

<!-- FEATURE_CARD_START FEAT-PORT-OPTIMIZE_WEIGHTS -->
### FEAT-PORT-OPTIMIZE_WEIGHTS — Optimize portfolio weights

- **Atomic value:** Provide registered weighting and constrained allocation methods.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Provide registered weighting and constrained allocation methods.
- **Does not own:** Transport/presentation or domain calculations outside Portfolio's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PFC-006`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** portfolio.optimize-markowitz@1; portfolio.extend-methods@1 (target)
- **Depends on:** Analytics covariance/correlation; Risk constraints.

#### Catalogue entries / algorithms / controls delivered

- Equal/manual/Markowitz/later providers, objectives, seeds, risk-free inputs.
- EXTENSION: `EXT-003`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Constraint, covariance, objective, solver, tie, and provider-removal tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PORT-OPTIMIZE_WEIGHTS -->

<!-- FEATURE_CARD_START FEAT-PORT-SEARCH_PORTFOLIOS -->
### FEAT-PORT-SEARCH_PORTFOLIOS — Search portfolio candidates

- **Atomic value:** Search bounded strategy combinations and commit selected portfolio candidates atomically.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Search bounded strategy combinations and commit selected portfolio candidates atomically.
- **Does not own:** Transport/presentation or domain calculations outside Portfolio's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PFM-001`–`PFM-006`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** portfolio.search-portfolios@1 (target)
- **Depends on:** Analytics databanks; Portfolio simulation/risk; Orchestration admission.

#### Catalogue entries / algorithms / controls delivered

- Universe snapshots, eligibility constraints, brute-force/evolutionary search, rankings.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Bound estimate, no-candidate, seed replay, stop/cancel, and membership atomicity tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PORT-SEARCH_PORTFOLIOS -->

<!-- FEATURE_CARD_START FEAT-PORT-ANALYZE_CORRELATION -->
### FEAT-PORT-ANALYZE_CORRELATION — Analyze portfolio correlation

- **Atomic value:** Own portfolio-specific alignment/covariance/correlation inputs and diversification evidence.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own portfolio-specific alignment/covariance/correlation inputs and diversification evidence.
- **Does not own:** Transport/presentation or domain calculations outside Portfolio's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PFM-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** portfolio.analyze-correlation@1 (target)
- **Depends on:** Analytics projections and currency policy.

#### Catalogue entries / algorithms / controls delivered

- Correlation/covariance matrices, alignment, diversification measures.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Missing-period, frequency/currency, numerical, matrix scale, and provenance tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PORT-ANALYZE_CORRELATION -->

## 11.9 Domain — Orchestration

<!-- FEATURE_CARD_START FEAT-ORCH-MANAGE_RUNS -->
### FEAT-ORCH-MANAGE_RUNS — Manage durable runs

- **Atomic value:** Own idempotent run/job plans, states, attempts, pause/stop/cancel, retention, and restart policy.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own idempotent run/job plans, states, attempts, pause/stop/cancel, retention, and restart policy.
- **Does not own:** Transport/presentation or domain calculations outside Orchestration's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `RUN-001`–`RUN-002`, `RUN-004`–`RUN-009`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** orchestration.jobs@1; orchestration.run-history@1 (target)
- **Depends on:** Domain capabilities; Workspace artifacts; Interfaces events.

#### Catalogue entries / algorithms / controls delivered

- Run lifecycle, immutable plans, attempts, partial/terminal states, reproducibility inspection.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Idempotency, state races, restart, retention/reference, cancellation, and checkpoint tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ORCH-MANAGE_RUNS -->

<!-- FEATURE_CARD_START FEAT-ORCH-DEFINE_PROJECTS -->
### FEAT-ORCH-DEFINE_PROJECTS — Define research projects

- **Atomic value:** Own versioned typed project graphs, drafts, publication validation, and cloning.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own versioned typed project graphs, drafts, publication validation, and cloning.
- **Does not own:** Transport/presentation or domain calculations outside Orchestration's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PRJ-001`–`PRJ-003`, `PRJ-010`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** orchestration.define-projects@1 (target)
- **Depends on:** Capability/schema catalogue.

#### Catalogue entries / algorithms / controls delivered

- Graph nodes/edges, UI coordinates, schema compatibility, publish revisions.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Cycle/unreachable/schema/capability/budget, clone, and optimistic conflict tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ORCH-DEFINE_PROJECTS -->

<!-- FEATURE_CARD_START FEAT-ORCH-RUN_PROJECTS -->
### FEAT-ORCH-RUN_PROJECTS — Run research projects

- **Atomic value:** Plan and execute whole/from-here/only project scopes with durable attempts and lineage.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Plan and execute whole/from-here/only project scopes with durable attempts and lineage.
- **Does not own:** Transport/presentation or domain calculations outside Orchestration's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PRJ-004`–`PRJ-005`, `PRJ-007`, `PRJ-011`–`PRJ-012`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** orchestration.run-tasks@1 (target)
- **Depends on:** Domain capabilities; conditions; resources; Plugins utilities.

#### Catalogue entries / algorithms / controls delivered

- Execution plans, reused/skipped outputs, node attempts, artifacts, recovery.
- EXTENSION: `EXT-008`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Post-edit isolation, missing input, retry history, restart, utility permission, and lineage tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ORCH-RUN_PROJECTS -->

<!-- FEATURE_CARD_START FEAT-ORCH-EVALUATE_CONDITIONS -->
### FEAT-ORCH-EVALUATE_CONDITIONS — Evaluate project conditions

- **Atomic value:** Evaluate typed branches deterministically with bounded loops and replayable inputs.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Evaluate typed branches deterministically with bounded loops and replayable inputs.
- **Does not own:** Transport/presentation or domain calculations outside Orchestration's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PRJ-008`–`PRJ-009`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** orchestration.evaluate-conditions@1 (target)
- **Depends on:** Project state snapshots and owner metrics.

#### Catalogue entries / algorithms / controls delivered

- Condition expressions, branch decisions, loop/cycle budgets.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Boundary, missing measure, cycle/loop, deterministic replay, and version tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ORCH-EVALUATE_CONDITIONS -->

<!-- FEATURE_CARD_START FEAT-ORCH-DISTRIBUTE_WORKERS -->
### FEAT-ORCH-DISTRIBUTE_WORKERS — Distribute work

- **Atomic value:** Run authenticated bounded local/remote work with leases, fencing, deterministic aggregation, and drain.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Run authenticated bounded local/remote work with leases, fencing, deterministic aggregation, and drain.
- **Does not own:** Transport/presentation or domain calculations outside Orchestration's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `WRK-001`–`WRK-010`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** orchestration.workers@1 (target)
- **Depends on:** Workspace artifact transfer; resource admission; domain work-unit contracts.

#### Catalogue entries / algorithms / controls delivered

- Worker registration, leases, attempts, checkpoints, quarantine, aggregation.
- FEATURE_CONTROL: `DEC-012`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Unauthorized worker, lease expiry, duplicate/late completion, partition, retry, cancel, and drain tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ORCH-DISTRIBUTE_WORKERS -->

<!-- FEATURE_CARD_START FEAT-ORCH-ADMIT_RESOURCES -->
### FEAT-ORCH-ADMIT_RESOURCES — Admit shared resources

- **Atomic value:** Enforce one hierarchical finite CPU, memory, thread, I/O, disk, device, and model budget across work.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Enforce one hierarchical finite CPU, memory, thread, I/O, disk, device, and model budget across work.
- **Does not own:** Transport/presentation or domain calculations outside Orchestration's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- `PER-002`, `PER-006`

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** orchestration.resource-admission@1 (target)
- **Depends on:** All heavy-work owners and platform telemetry.

#### Catalogue entries / algorithms / controls delivered

- Resource profiles/reservations, fair queues, nested budgets, observed-use reconciliation.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Overload, fairness/starvation, oversubscription, nested bypass, release, and mixed-load tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ORCH-ADMIT_RESOURCES -->

<!-- FEATURE_CARD_START FEAT-ORCH-MEASURE_PERFORMANCE -->
### FEAT-ORCH-MEASURE_PERFORMANCE — Measure application performance

- **Atomic value:** Run reproducible workload/gate evaluation and block affected releases on confirmed regression.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Run reproducible workload/gate evaluation and block affected releases on confirmed regression.
- **Does not own:** Transport/presentation or domain calculations outside Orchestration's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- `PER-010`–`PER-012`

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** orchestration.performance-lab@1 (target)
- **Depends on:** All benchmarked feature owners; Workspace report custody.

#### Catalogue entries / algorithms / controls delivered

- Hardware/fixture manifests, benchmark runner, comparator, profiles, regression reports.
- BENCHMARK: `BM-TICK-01`, `BM-TICK-02`, `BM-TICK-03`, `BM-TICK-20Y`, `BM-DATA-01`, `BM-IND-01`, `BM-SEARCH-01`, `BM-ANA-01`, `BM-PORT-01`, `BM-APP-01`, `BM-LIFE-01`, `BM-EXT-01`
- PERFORMANCE_TASK: `PERF-00`, `PERF-01`, `PERF-02`, `PERF-03`, `PERF-04`, `PERF-05`, `PERF-06`, `PERF-07`, `PERF-08`, `PERF-09`, `PERF-10`, `PERF-11`, `PERF-12`, `PERF-13`, `PERF-14`, `PERF-15`, `PERF-16`
- PERFORMANCE_GATE: `PERF-G01`, `PERF-G02`, `PERF-G03`, `PERF-G04`, `PERF-G05`, `PERF-G06`, `PERF-G07`, `PERF-G08`, `PERF-G09`, `PERF-G10`, `PERF-G11`, `PERF-G12`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Matched-runner, cold/warm separation, threshold repeat, lifecycle leak, and report integrity tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-ORCH-MEASURE_PERFORMANCE -->

## 11.10 Domain — Data

<!-- FEATURE_CARD_START FEAT-DATA-BROWSE_REFERENCE -->
### FEAT-DATA-BROWSE_REFERENCE — Browse reference data

- **Atomic value:** Expose bounded research reference/data/profile views through one existing owner boundary.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Expose bounded research reference/data/profile views through one existing owner boundary.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DAT-001`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.browse-reference@1
- **Depends on:** Catalogue features and authorized providers.

#### Catalogue entries / algorithms / controls delivered

- Reference catalogue projection, series/profile paging and readiness.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Capability conformance, stale/missing provider, paging, and UI contract tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-BROWSE_REFERENCE -->

<!-- FEATURE_CARD_START FEAT-DATA-BIND_RUN_DATA -->
### FEAT-DATA-BIND_RUN_DATA — Bind run data

- **Atomic value:** Resolve immutable series/profile/sample versions for reproducible runs.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Resolve immutable series/profile/sample versions for reproducible runs.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DAT-002`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.bind-run-data@1
- **Depends on:** Data store, Catalogue, Workspace manifests.

#### Catalogue entries / algorithms / controls delivered

- Run data bindings, profile revisions, sample/timezone identity.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Historical resolution, changed profile, missing artifact, and hash/lineage tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-BIND_RUN_DATA -->

<!-- FEATURE_CARD_START FEAT-DATA-MARKET_DATA_STORE -->
### FEAT-DATA-MARKET_DATA_STORE — Store market data

- **Atomic value:** Own bounded append/read/partition/manifest behavior for immutable bulk bars and ticks.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Own bounded append/read/partition/manifest behavior for immutable bulk bars and ticks.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DAT-003`

#### Feature-specific non-functional requirements

- `PER-003`–`PER-004`

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.market-data-store@1
- **Depends on:** Workspace custody and Catalogue metadata.

#### Catalogue entries / algorithms / controls delivered

- Arrow/Parquet partitions, atomic manifests, bounded readers, compaction/cache lifecycle.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Larger-than-RAM, atomic publication, corruption, range query, compaction/recovery tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-MARKET_DATA_STORE -->

<!-- FEATURE_CARD_START FEAT-DATA-SYNC_CONNECTORS -->
### FEAT-DATA-SYNC_CONNECTORS — Synchronize connectors

- **Atomic value:** Validate source configuration and perform bounded authorized connector synchronization.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Validate source configuration and perform bounded authorized connector synchronization.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DAT-004`, `DAT-009`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.connector-synchronization@1
- **Depends on:** Catalogue provider mapping; Workspace secrets; provider adapters.

#### Catalogue entries / algorithms / controls delivered

- Source profiles, readiness, rate/retry bounds, synchronization reports.
- FEATURE_CONTROL: `DEC-017`
- EXTENSION: `EXT-005`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Secret isolation, rate/backoff, cancellation, malformed provider, and redacted audit tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-SYNC_CONNECTORS -->

<!-- FEATURE_CARD_START FEAT-DATA-RESOLVE_QUALITY -->
### FEAT-DATA-RESOLVE_QUALITY — Resolve data quality

- **Atomic value:** Create versioned findings and non-destructive repair outputs.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Create versioned findings and non-destructive repair outputs.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DAT-005`–`DAT-006`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.quality-resolution@1
- **Depends on:** Market data store; session/instrument catalogues.

#### Catalogue entries / algorithms / controls delivered

- Gap/spike/OHLC rules, findings, repair policies, lineage.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Threshold/calendar, non-destructive repair, conflict, partial, and provenance tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-RESOLVE_QUALITY -->

<!-- FEATURE_CARD_START FEAT-DATA-MANAGE_RETENTION -->
### FEAT-DATA-MANAGE_RETENTION — Manage data retention

- **Atomic value:** Govern clone/delete/retention and reference impact without orphaning evidence.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Govern clone/delete/retention and reference impact without orphaning evidence.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DAT-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.inspection-retention@1
- **Depends on:** Workspace custody; all referencing domains.

#### Catalogue entries / algorithms / controls delivered

- Impact analysis, retention, legal hold/purge requests, clone/delete reports.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Referenced-object denial, retention boundary, clone identity, purge authorization tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-MANAGE_RETENTION -->

<!-- FEATURE_CARD_START FEAT-DATA-INGEST_HISTORY -->
### FEAT-DATA-INGEST_HISTORY — Ingest historical data

- **Atomic value:** Import supported market-data files through pinned adapters and truthful manifests.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Import supported market-data files through pinned adapters and truthful manifests.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `DAT-010`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.historical-ingestion@1
- **Depends on:** Workspace artifacts; provider mapping; market store.

#### Catalogue entries / algorithms / controls delivered

- CSV/SQX/registered adapters, timezone/schema options, checksums/counts/warnings.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Golden formats, corrupt/path-hostile input, containment, idempotency, and report tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-INGEST_HISTORY -->

<!-- FEATURE_CARD_START FEAT-DATA-NORMALIZE_TICKS -->
### FEAT-DATA-NORMALIZE_TICKS — Normalize tick evidence

- **Atomic value:** Canonicalize provider ticks without changing source ordering/evidence class.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Canonicalize provider ticks without changing source ordering/evidence class.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.tick-normalization@1
- **Depends on:** Provider adapters; Catalogue instrument profiles.

#### Catalogue entries / algorithms / controls delivered

- Tick schema, timestamps, flags, price/volume units, source identity.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Provider fixture, ordering, duplicate/gap, precision, and provenance tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-NORMALIZE_TICKS -->

<!-- FEATURE_CARD_START FEAT-DATA-GENERATE_SCENARIOS -->
### FEAT-DATA-GENERATE_SCENARIOS — Generate tick scenarios

- **Atomic value:** Generate seeded tick/scenario streams with explicit model and evidence classification.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Generate seeded tick/scenario streams with explicit model and evidence classification.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.synthetic-scenarios@1
- **Depends on:** Bar/tick evidence and instrument/session profiles.

#### Catalogue entries / algorithms / controls delivered

- Generation methods, seeds, gap/event scenarios, manifests.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Seed replay, coverage/count, boundary price, invalid profile, and no-recorded-label tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-GENERATE_SCENARIOS -->

<!-- FEATURE_CARD_START FEAT-DATA-ALIGN_SERIES -->
### FEAT-DATA-ALIGN_SERIES — Align external series

- **Atomic value:** Align multi-symbol/timeframe/external evidence backward-only with explicit availability.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Align multi-symbol/timeframe/external evidence backward-only with explicit availability.
- **Does not own:** Transport/presentation or domain calculations outside Data's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** data.external-series-alignment@1
- **Depends on:** Market store; Catalogue sessions; external indicator series.

#### Catalogue entries / algorithms / controls delivered

- As-of alignment, calendars, gaps, availability timestamps.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: No-lookahead, DST/session, missing series, tolerance, and lineage tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-DATA-ALIGN_SERIES -->

## 11.11 Domain — Catalogue

<!-- FEATURE_CARD_START FEAT-CAT-CATALOG_INSTRUMENTS -->
### FEAT-CAT-CATALOG_INSTRUMENTS — Catalogue instruments

- **Atomic value:** Own stable instrument identities and versioned trading/data metadata.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Own stable instrument identities and versioned trading/data metadata.
- **Does not own:** Transport/presentation or domain calculations outside Catalogue's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** catalogue.instruments@1
- **Depends on:** Provider mapping and sessions.

#### Catalogue entries / algorithms / controls delivered

- Instrument aliases, units, currencies, profiles, effective versions.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Alias conflict, version, unknown provider value, and consumer conformance tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-CAT-CATALOG_INSTRUMENTS -->

<!-- FEATURE_CARD_START FEAT-CAT-DEFINE_SESSIONS -->
### FEAT-CAT-DEFINE_SESSIONS — Define sessions

- **Atomic value:** Own venue calendars, sessions, holidays, and timezone/DST rules.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Own venue calendars, sessions, holidays, and timezone/DST rules.
- **Does not own:** Transport/presentation or domain calculations outside Catalogue's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** catalogue.sessions@1
- **Depends on:** Instrument catalogue.

#### Catalogue entries / algorithms / controls delivered

- Named sessions, calendars, holidays, timezone policy.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: DST, holiday, gap, boundary, and version fixtures.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-CAT-DEFINE_SESSIONS -->

<!-- FEATURE_CARD_START FEAT-CAT-MAP_PROVIDERS -->
### FEAT-CAT-MAP_PROVIDERS — Map providers

- **Atomic value:** Map provider-local identifiers/values to canonical catalogue identities without leaking SDK objects.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Map provider-local identifiers/values to canonical catalogue identities without leaking SDK objects.
- **Does not own:** Transport/presentation or domain calculations outside Catalogue's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** catalogue.provider-mapping@1
- **Depends on:** Broker/data provider adapters and instrument catalogue.

#### Catalogue entries / algorithms / controls delivered

- Provider aliases, format/version support, availability mappings.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Unknown value, version drift, alias collision, removal, and round-trip tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-CAT-MAP_PROVIDERS -->

## 11.12 Domain — Plugins

<!-- FEATURE_CARD_START FEAT-PLUG-DECLARE_MANIFESTS -->
### FEAT-PLUG-DECLARE_MANIFESTS — Declare extension manifests

- **Atomic value:** Validate typed extension identity, contributions, permissions, compatibility, and resources.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Validate typed extension identity, contributions, permissions, compatibility, and resources.
- **Does not own:** Transport/presentation or domain calculations outside Plugins's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** plugins.manifests@1
- **Depends on:** Public contribution schemas.

#### Catalogue entries / algorithms / controls delivered

- Extension manifests, capability/widget/panel contributions, version constraints.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Schema/signature/duplicate/unknown permission and compatibility tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PLUG-DECLARE_MANIFESTS -->

<!-- FEATURE_CARD_START FEAT-PLUG-REGISTER_CONTRIBUTIONS -->
### FEAT-PLUG-REGISTER_CONTRIBUTIONS — Register contributions

- **Atomic value:** Publish and withdraw typed provider/widget/panel/tool contributions atomically.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Publish and withdraw typed provider/widget/panel/tool contributions atomically.
- **Does not own:** Transport/presentation or domain calculations outside Plugins's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** plugins.contributions@1
- **Depends on:** Manifest validation; composition registries.

#### Catalogue entries / algorithms / controls delivered

- Contribution catalogue, generation identity, exact disposer.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Atomic registration, duplicate/ambiguity, removal/replacement, and cleanup tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PLUG-REGISTER_CONTRIBUTIONS -->

<!-- FEATURE_CARD_START FEAT-PLUG-MANAGE_LIFECYCLE -->
### FEAT-PLUG-MANAGE_LIFECYCLE — Manage extension lifecycle

- **Atomic value:** Quarantine, scan, install, enable, disable, upgrade, and remove extensions without implicit data purge.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Quarantine, scan, install, enable, disable, upgrade, and remove extensions without implicit data purge.
- **Does not own:** Transport/presentation or domain calculations outside Plugins's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `CED-005`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** plugins.lifecycle@1
- **Depends on:** Manifests, sandbox, Workspace artifacts.

#### Catalogue entries / algorithms / controls delivered

- Quarantine, scan reports, lifecycle states, compatibility/readiness.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Malicious package, signature, permission, upgrade/rollback, removal/retention tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PLUG-MANAGE_LIFECYCLE -->

<!-- FEATURE_CARD_START FEAT-PLUG-SANDBOX_PERMISSIONS -->
### FEAT-PLUG-SANDBOX_PERMISSIONS — Sandbox extension permissions

- **Atomic value:** Enforce least-privilege filesystem, process, network, secret, and resource boundaries.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Enforce least-privilege filesystem, process, network, secret, and resource boundaries.
- **Does not own:** Transport/presentation or domain calculations outside Plugins's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `PRJ-006`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** plugins.sandbox-permissions@1
- **Depends on:** Workspace capability leases and platform isolation.

#### Catalogue entries / algorithms / controls delivered

- Permission classes, leases, path/egress rules, resource ceilings.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Traversal/symlink, secret, egress, timeout, resource, and revocation tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PLUG-SANDBOX_PERMISSIONS -->

<!-- FEATURE_CARD_START FEAT-PLUG-ISOLATE_ANALYSIS -->
### FEAT-PLUG-ISOLATE_ANALYSIS — Isolate builds and analysis

- **Atomic value:** Compile/test/analyze untrusted extension source outside browser/application authority.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Compile/test/analyze untrusted extension source outside browser/application authority.
- **Does not own:** Transport/presentation or domain calculations outside Plugins's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `BLD-010`, `CED-003`, `CED-008`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** plugins.isolate-analysis@1
- **Depends on:** Sandbox permissions; Workspace staging; toolchain providers.

#### Catalogue entries / algorithms / controls delivered

- Build/test jobs, diagnostics, toolchain pins, staged outputs.
- FEATURE_CONTROL: `DEC-008`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Escape, timeout, malformed output, deterministic build, bounded/redacted log tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PLUG-ISOLATE_ANALYSIS -->

<!-- FEATURE_CARD_START FEAT-PLUG-RENDER_RESULT_PANELS -->
### FEAT-PLUG-RENDER_RESULT_PANELS — Render result panels

- **Atomic value:** Run custom result panels against read-only projections in a contained frame.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Run custom result panels against read-only projections in a contained frame.
- **Does not own:** Transport/presentation or domain calculations outside Plugins's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `RES-009`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** plugins.render-result-panels@1
- **Depends on:** Analytics projections; UI panel host; manifests.

#### Catalogue entries / algorithms / controls delivered

- Panel manifests, CSP/bridge, read-only result projection, crash boundary.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Hostile panel, permission/schema, CSP, crash containment, removal tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PLUG-RENDER_RESULT_PANELS -->

<!-- FEATURE_CARD_START FEAT-PLUG-MAINTAIN_COMPATIBILITY -->
### FEAT-PLUG-MAINTAIN_COMPATIBILITY — Maintain extension compatibility

- **Atomic value:** Evaluate contract/toolchain/schema compatibility and explicit migrations.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Evaluate contract/toolchain/schema compatibility and explicit migrations.
- **Does not own:** Transport/presentation or domain calculations outside Plugins's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** plugins.compatibility@1
- **Depends on:** Manifests and public contract versions.

#### Catalogue entries / algorithms / controls delivered

- Compatibility matrix, migrations, deprecation/incompatibility reports.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Version matrix, unknown major, migration, provider replacement, and rollback tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PLUG-MAINTAIN_COMPATIBILITY -->

<!-- FEATURE_CARD_START FEAT-PLUG-DEVELOP_EXTENSIONS -->
### FEAT-PLUG-DEVELOP_EXTENSIONS — Develop extension resources

- **Atomic value:** Own authorized resource revisions, conflict-aware saves, searches, and package-local development state.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own authorized resource revisions, conflict-aware saves, searches, and package-local development state.
- **Does not own:** Transport/presentation or domain calculations outside Plugins's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `CED-001`–`CED-002`, `CED-004`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** plugins.development@1 (target)
- **Depends on:** Workspace artifacts; sandbox analysis; lifecycle.

#### Catalogue entries / algorithms / controls delivered

- Authorized resource tree, revisions, three-way compare, scoped search.
- EXTENSION: `EXT-007`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Path/scope, dirty conflict, concurrent revision, search leakage, and retention tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-PLUG-DEVELOP_EXTENSIONS -->

## 11.13 Domain — Indicators

<!-- FEATURE_CARD_START FEAT-INDI-CALCULATE_INDICATORS -->
### FEAT-INDI-CALCULATE_INDICATORS — Calculate indicators

- **Atomic value:** Own causal incremental/native indicator algorithms and versioned descriptors.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Own causal incremental/native indicator algorithms and versioned descriptors.
- **Does not own:** Transport/presentation or domain calculations outside Indicators's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** indicators.calculate@1 (target)
- **Depends on:** Data series/ticks; Strategy block catalogue.

#### Catalogue entries / algorithms / controls delivered

- Indicator descriptors/state, multi-timeframe updates, native kernels.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Golden vectors, chunk equivalence, no-lookahead, cache/provider generation tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-INDI-CALCULATE_INDICATORS -->

<!-- FEATURE_CARD_START FEAT-INDI-TEST_INDICATORS -->
### FEAT-INDI-TEST_INDICATORS — Test indicators

- **Atomic value:** Compare extension indicator outputs against owner-qualified reference calculations.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Compare extension indicator outputs against owner-qualified reference calculations.
- **Does not own:** Transport/presentation or domain calculations outside Indicators's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `CED-007`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** indicators.test@1 (target)
- **Depends on:** Plugins isolation; Data profiles; Simulator clocks.

#### Catalogue entries / algorithms / controls delivered

- Indicator Tester plans, discrepancy pages/reports.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Engine/data/profile pin, decimal policy, paging, golden comparison tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-INDI-TEST_INDICATORS -->

<!-- FEATURE_CARD_START FEAT-INDI-ANALYZE_MARKET_PROFILE -->
### FEAT-INDI-ANALYZE_MARKET_PROFILE — Analyze volume and market profile

- **Atomic value:** Produce typed Volume Profile/TPO derived layers with accessible projections.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Produce typed Volume Profile/TPO derived layers with accessible projections.
- **Does not own:** Transport/presentation or domain calculations outside Indicators's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-002`–`NFR-P-004`, `NFR-R-001`–`NFR-R-004`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005` as applicable.

#### Public contracts and dependencies

- **Provides:** indicators.market-profile@1 (target)
- **Depends on:** Data sessions/series; Analytics/UI projections.

#### Catalogue entries / algorithms / controls delivered

- Bins, value area, POC, TPO/session layers.
- EXTENSION: `EXT-002`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Conservation, tie/bin/session, timezone, sparse-data, and table-fallback tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-INDI-ANALYZE_MARKET_PROFILE -->

## 11.14 Domain — Interfaces

<!-- FEATURE_CARD_START FEAT-IFACE-SERVE_API_EVENTS -->
### FEAT-IFACE-SERVE_API_EVENTS — Serve commands and events

- **Atomic value:** Authenticate/validate cohesive commands and provide idempotent job references plus resumable SSE.
- **Status:** `REGISTERED_CURRENT`; evidence state is `VERIFIED_CURRENT for identity only; behavioral evidence remains owning-README controlled`.
- **Owns:** Authenticate/validate cohesive commands and provide idempotent job references plus resumable SSE.
- **Does not own:** Transport/presentation or domain calculations outside Interfaces's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- `RUN-003`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-003`, `NFR-R-002`–`NFR-R-003`, `NFR-S-001`, `NFR-S-004`–`NFR-S-006`, `NFR-A-005`.

#### Public contracts and dependencies

- **Provides:** interfaces.api-events@1
- **Depends on:** Identity/session; all routed domain capabilities.

#### Catalogue entries / algorithms / controls delivered

- ApiResponse, JobRef, StreamEvent, cursor replay/resync, error mapping.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Auth/CSRF/schema/idempotency, disconnect/replay/gap/expiry tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-IFACE-SERVE_API_EVENTS -->

<!-- FEATURE_CARD_START FEAT-IFACE-OPERATE_STRATEGIES -->
### FEAT-IFACE-OPERATE_STRATEGIES — Operate strategy boundaries

- **Atomic value:** Translate strategy authoring/exchange/generation requests without owning semantics.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Translate strategy authoring/exchange/generation requests without owning semantics.
- **Does not own:** Transport/presentation or domain calculations outside Interfaces's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-003`, `NFR-R-002`–`NFR-R-003`, `NFR-S-001`, `NFR-S-004`–`NFR-S-006`, `NFR-A-005`.

#### Public contracts and dependencies

- **Provides:** interfaces.strategies@1 (target)
- **Depends on:** Strategy capabilities; Workspace downloads.

#### Catalogue entries / algorithms / controls delivered

- Strategy DTO routes, errors, job/download links.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Contract parity, authorization, capability-unavailable, and no-domain-logic tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-IFACE-OPERATE_STRATEGIES -->

<!-- FEATURE_CARD_START FEAT-IFACE-OPERATE_RESEARCH -->
### FEAT-IFACE-OPERATE_RESEARCH — Operate research boundaries

- **Atomic value:** Translate Builder/Retester/Optimization research commands and observations.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Translate Builder/Retester/Optimization research commands and observations.
- **Does not own:** Transport/presentation or domain calculations outside Interfaces's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-003`, `NFR-R-002`–`NFR-R-003`, `NFR-S-001`, `NFR-S-004`–`NFR-S-006`, `NFR-A-005`.

#### Public contracts and dependencies

- **Provides:** interfaces.research@1 (target)
- **Depends on:** Research, Simulator, Optimization, Orchestration.

#### Catalogue entries / algorithms / controls delivered

- Plan/run/query routes and bounded event projections.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Contract parity, idempotency, cancellation, stream, and unavailable-owner tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-IFACE-OPERATE_RESEARCH -->

<!-- FEATURE_CARD_START FEAT-IFACE-OPERATE_ANALYTICS -->
### FEAT-IFACE-OPERATE_ANALYTICS — Operate analytics boundaries

- **Atomic value:** Translate databank/result/trade/report queries and governed bulk commands.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Translate databank/result/trade/report queries and governed bulk commands.
- **Does not own:** Transport/presentation or domain calculations outside Interfaces's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-003`, `NFR-R-002`–`NFR-R-003`, `NFR-S-001`, `NFR-S-004`–`NFR-S-006`, `NFR-A-005`.

#### Public contracts and dependencies

- **Provides:** interfaces.analytics@1 (target)
- **Depends on:** Analytics and Workspace capabilities.

#### Catalogue entries / algorithms / controls delivered

- Cursor queries, selection tokens, report/download routes.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Auth, cursor, bulk idempotency, projection bounds, and error-map tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-IFACE-OPERATE_ANALYTICS -->

<!-- FEATURE_CARD_START FEAT-IFACE-OPERATE_PORTFOLIOS -->
### FEAT-IFACE-OPERATE_PORTFOLIOS — Operate portfolio boundaries

- **Atomic value:** Translate portfolio composition/search/simulation commands and views.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Translate portfolio composition/search/simulation commands and views.
- **Does not own:** Transport/presentation or domain calculations outside Interfaces's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-003`, `NFR-R-002`–`NFR-R-003`, `NFR-S-001`, `NFR-S-004`–`NFR-S-006`, `NFR-A-005`.

#### Public contracts and dependencies

- **Provides:** interfaces.portfolios@1 (target)
- **Depends on:** Portfolio, Analytics, Orchestration.

#### Catalogue entries / algorithms / controls delivered

- Portfolio revision/search/run/query routes.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Contract parity, authorization, idempotency, stream, and compatibility tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-IFACE-OPERATE_PORTFOLIOS -->

<!-- FEATURE_CARD_START FEAT-IFACE-OPERATE_PROJECTS -->
### FEAT-IFACE-OPERATE_PROJECTS — Operate project boundaries

- **Atomic value:** Translate project draft/publish/run/control/history operations.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Translate project draft/publish/run/control/history operations.
- **Does not own:** Transport/presentation or domain calculations outside Interfaces's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-003`, `NFR-R-002`–`NFR-R-003`, `NFR-S-001`, `NFR-S-004`–`NFR-S-006`, `NFR-A-005`.

#### Public contracts and dependencies

- **Provides:** interfaces.projects@1 (target)
- **Depends on:** Orchestration projects/jobs.

#### Catalogue entries / algorithms / controls delivered

- Graph DTOs, plan preview, run controls, history projections.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Schema/auth/idempotency, cursor, capability-removal, and error tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-IFACE-OPERATE_PROJECTS -->

<!-- FEATURE_CARD_START FEAT-IFACE-OPERATE_PLUGINS -->
### FEAT-IFACE-OPERATE_PLUGINS — Operate extension boundaries

- **Atomic value:** Translate authorized extension resource/build/lifecycle/panel operations.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Translate authorized extension resource/build/lifecycle/panel operations.
- **Does not own:** Transport/presentation or domain calculations outside Interfaces's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-003`, `NFR-R-002`–`NFR-R-003`, `NFR-S-001`, `NFR-S-004`–`NFR-S-006`, `NFR-A-005`.

#### Public contracts and dependencies

- **Provides:** interfaces.plugins@1 (target)
- **Depends on:** Plugins and Workspace capabilities.

#### Catalogue entries / algorithms / controls delivered

- Resource/build/lifecycle routes, staged downloads, diagnostics.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Permission, hostile input, job/event, content disposition, and no-host-access tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-IFACE-OPERATE_PLUGINS -->

<!-- FEATURE_CARD_START FEAT-IFACE-AGENTIC_GATEWAY -->
### FEAT-IFACE-AGENTIC_GATEWAY — Operate Agentic boundaries

- **Atomic value:** Authenticate Chat Bot/workflow/action/inspection requests and stream bounded Agentic events.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Authenticate Chat Bot/workflow/action/inspection requests and stream bounded Agentic events.
- **Does not own:** Transport/presentation or domain calculations outside Interfaces's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** None.

#### Owned functional requirements

- No separately numbered primary ID in this specification; the feature owns the normative catalogue/control scope stated below and any requirements in its owning current README.

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-003`, `NFR-R-002`–`NFR-R-003`, `NFR-S-001`, `NFR-S-004`–`NFR-S-006`, `NFR-A-005`.

#### Public contracts and dependencies

- **Provides:** interfaces.operator-chat@1 (target; exact name reconciled in U0)
- **Depends on:** Agentic capabilities; Workspace conversation/session; identity.

#### Catalogue entries / algorithms / controls delivered

- Chat/run/action/inspection routes, SSE, context validation, error mapping.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Auth/session/account, idempotent turn, action binding, cursor, removal tests.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-IFACE-AGENTIC_GATEWAY -->

## 11.15 Domain — Agentic

<!-- FEATURE_CARD_START FEAT-AGT-ENFORCE_MANDATE -->
### FEAT-AGT-ENFORCE_MANDATE — Mandate enforcement

- **Atomic value:** Enforce immutable firm mandate and prohibited authority.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Enforce immutable firm mandate and prohibited authority.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-VALIDATE_MANDATE`, `FR-AGT-ENFORCE_AUTHORITY_BOUNDARY`, `FR-AGT-FAIL_CLOSED_ON_MANDATE`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.mandate@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-ENFORCE_MANDATE -->

<!-- FEATURE_CARD_START FEAT-AGT-OPERATE_RUNS -->
### FEAT-AGT-OPERATE_RUNS — Operations, incidents, and replay validation

- **Atomic value:** Record redacted operations, contain incidents, validate replay, and publish readiness.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Record redacted operations, contain incidents, validate replay, and publish readiness.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-RECORD_OPERATIONS`, `FR-AGT-CONTAIN_INCIDENTS`, `FR-AGT-VALIDATE_REPLAY`, `FR-AGT-PUBLISH_AGENTIC_READINESS`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.operations@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-RESPOND_INCIDENT`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-OPERATE_RUNS -->

<!-- FEATURE_CARD_START FEAT-AGT-REGISTER_ROLES -->
### FEAT-AGT-REGISTER_ROLES — Role contribution registry

- **Atomic value:** Register immutable evaluated role contributions with exact disposal.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Register immutable evaluated role contributions with exact disposal.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-REGISTER_ROLE_CONTRIBUTIONS`, `FR-AGT-VERIFY_ROLE_ARTIFACTS`, `FR-AGT-RESOLVE_ELIGIBLE_ROLES`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.roles@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-REGISTER_ROLES -->

<!-- FEATURE_CARD_START FEAT-AGT-GOVERN_TOOL_CALLS -->
### FEAT-AGT-GOVERN_TOOL_CALLS — Tool governance and human actions

- **Atomic value:** Register governed tools, issue invocation-bound leases, and bind typed human actions.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Register governed tools, issue invocation-bound leases, and bind typed human actions.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-REGISTER_AGENTIC_TOOLS`, `FR-AGT-ISSUE_CAPABILITY_LEASES`, `FR-AGT-ENFORCE_TOOL_INVOCATIONS`, `FR-AGT-FILTER_TOOL_RESULTS`, `FR-AGT-BIND_TYPED_HUMAN_ACTIONS`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.tool-governance@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-GOVERN_TOOL_CALLS -->

<!-- FEATURE_CARD_START FEAT-AGT-INVOKE_MODELS -->
### FEAT-AGT-INVOKE_MODELS — Provider-neutral model invocation

- **Atomic value:** Invoke pinned model profiles under schema, privacy, budget, and fallback policy.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Invoke pinned model profiles under schema, privacy, budget, and fallback policy.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-PIN_MODEL_INVOCATIONS`, `FR-AGT-ENFORCE_MODEL_BUDGETS`, `FR-AGT-REFUSE_SILENT_MODEL_SUBSTITUTION`, `FR-AGT-CONTAIN_MODEL_OUTPUT`

#### Feature-specific non-functional requirements

- `PER-007`

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.model-inference@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-INVOKE_MODELS -->

<!-- FEATURE_CARD_START FEAT-AGT-RUN_WORKFLOWS -->
### FEAT-AGT-RUN_WORKFLOWS — Durable workflow orchestration

- **Atomic value:** Run bounded checkpointed Agentic workflows with explicit terminal states.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Run bounded checkpointed Agentic workflows with explicit terminal states.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-SUBMIT_WORKFLOWS`, `FR-AGT-CHECKPOINT_WORKFLOWS`, `FR-AGT-BOUND_ADAPTIVE_ESCALATION`, `FR-AGT-TERMINATE_WORKFLOWS`, `FR-AGT-APPLY_BACKPRESSURE`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.workflows@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-RESEARCH_OBJECTIVE`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-RUN_WORKFLOWS -->

<!-- FEATURE_CARD_START FEAT-AGT-ASSEMBLE_CONTEXT -->
### FEAT-AGT-ASSEMBLE_CONTEXT — Point-in-time context assembly

- **Atomic value:** Assemble bounded eligible evidence separated structurally from instructions.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Assemble bounded eligible evidence separated structurally from instructions.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-ASSEMBLE_POINT_IN_TIME_CONTEXT`, `FR-AGT-SEPARATE_EVIDENCE_FROM_INSTRUCTIONS`, `FR-AGT-REPORT_CONTEXT_EXCLUSIONS`, `FR-AGT-BOUND_CONTEXT_SIZE`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.context@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-ASSEMBLE_CONTEXT -->

<!-- FEATURE_CARD_START FEAT-AGT-MANAGE_MEMORY -->
### FEAT-AGT-MANAGE_MEMORY — Governed memory

- **Atomic value:** Classify, promote, retrieve, retain, and purge scoped memory safely.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Classify, promote, retrieve, retain, and purge scoped memory safely.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-CLASSIFY_MEMORY`, `FR-AGT-PROMOTE_MEMORY`, `FR-AGT-RETRIEVE_MEMORY`, `FR-AGT-RETAIN_AND_PURGE_MEMORY`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.memory@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-MANAGE_MEMORY -->

<!-- FEATURE_CARD_START FEAT-AGT-EVALUATE_PROFILES -->
### FEAT-AGT-EVALUATE_PROFILES — Profile and topology evaluation

- **Atomic value:** Evaluate and ablate profiles/topologies and determine deterministic eligibility.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Evaluate and ablate profiles/topologies and determine deterministic eligibility.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-EVALUATE_PROFILES`, `FR-AGT-ABLATE_TOPOLOGIES`, `FR-AGT-DETERMINE_PROFILE_ELIGIBILITY`, `FR-AGT-CALIBRATE_GRADERS`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.profile-evaluation@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-EVALUATE_PROFILE`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-EVALUATE_PROFILES -->

<!-- FEATURE_CARD_START FEAT-AGT-ASSIST_OPERATOR -->
### FEAT-AGT-ASSIST_OPERATOR — Website Chat Bot and specialist delegation

- **Atomic value:** Answer contextual questions or route eligible specialists in one conversation.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Answer contextual questions or route eligible specialists in one conversation.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-READ_WORKSPACE_CONTEXT`, `FR-AGT-ANSWER_CONTEXTUAL_QUESTIONS`, `FR-AGT-ROUTE_SPECIALIST_QUESTIONS`, `FR-AGT-PRESERVE_CHAT_HANDOFF_LINEAGE`, `FR-AGT-RESTRICT_CHAT_ACTIONS`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.operator-assistance@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-ASSIST_OPERATOR`
- EXTENSION: `EXT-006`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-ASSIST_OPERATOR -->

<!-- FEATURE_CARD_START FEAT-AGT-MANAGE_CLAIMS -->
### FEAT-AGT-MANAGE_CLAIMS — Claim-and-evidence graph

- **Atomic value:** Create typed claims, bind evidence, propagate status, and assess reliability.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Create typed claims, bind evidence, propagate status, and assess reliability.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-CREATE_TYPED_CLAIMS`, `FR-AGT-LINK_CLAIM_EVIDENCE`, `FR-AGT-PROPAGATE_CLAIM_STATUS`, `FR-AGT-ASSESS_CLAIM_RELIABILITY`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.claims@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-REVIEW_EVIDENCE`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-MANAGE_CLAIMS -->

<!-- FEATURE_CARD_START FEAT-AGT-DELIBERATE_RESEARCH -->
### FEAT-AGT-DELIBERATE_RESEARCH — Independent challenge and deliberation

- **Atomic value:** Collect independent bounded challenge while preserving dissent.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Collect independent bounded challenge while preserving dissent.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-COLLECT_INDEPENDENT_CHALLENGES`, `FR-AGT-PRESERVE_DELIBERATION_DISSENT`, `FR-AGT-BOUND_DELIBERATION`, `FR-AGT-STOP_LOW_VALUE_DELIBERATION`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.deliberation@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-DELIBERATE_RESEARCH -->

<!-- FEATURE_CARD_START FEAT-AGT-SYNTHESIZE_RESEARCH -->
### FEAT-AGT-SYNTHESIZE_RESEARCH — Research synthesis

- **Atomic value:** Synthesize only supported claim graphs with uncertainty and refusal.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Synthesize only supported claim graphs with uncertainty and refusal.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-SYNTHESIZE_CLAIM_GRAPHS`, `FR-AGT-PRESERVE_SYNTHESIS_UNCERTAINTY`, `FR-AGT-REFUSE_UNSUPPORTED_SYNTHESIS`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.synthesis@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- Source-section controls are traced through §10 and the primary requirement rows; no task/milestone label is treated as a feature.

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-SYNTHESIZE_RESEARCH -->

<!-- FEATURE_CARD_START FEAT-AGT-GOVERN_RESEARCH_SEARCH -->
### FEAT-AGT-GOVERN_RESEARCH_SEARCH — Research campaign and search governance

- **Atomic value:** Account campaigns, variants, failed attempts, budgets, and holdout receipts.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Account campaigns, variants, failed attempts, budgets, and holdout receipts.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-REGISTER_RESEARCH_CAMPAIGNS`, `FR-AGT-ACCOUNT_RESEARCH_VARIANTS`, `FR-AGT-PRESERVE_FAILED_ATTEMPTS`, `FR-AGT-GOVERN_HOLDOUT_REQUESTS`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.research-search@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-GOVERNED_SEARCH`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-GOVERN_RESEARCH_SEARCH -->

<!-- FEATURE_CARD_START FEAT-AGT-DESIGN_RESEARCH -->
### FEAT-AGT-DESIGN_RESEARCH — Falsifiable research design

- **Atomic value:** Compose falsifiable hypotheses and receiver-owned experiment/search requests.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Compose falsifiable hypotheses and receiver-owned experiment/search requests.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-DESIGN_FALSIFIABLE_HYPOTHESES`, `FR-AGT-COMPOSE_EXPERIMENT_REQUESTS`, `FR-AGT-COMPOSE_SEARCH_REQUESTS`, `FR-AGT-BIND_RESEARCH_PROTOCOLS`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.research-design@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-DESIGN_RESEARCH`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-DESIGN_RESEARCH -->

<!-- FEATURE_CARD_START FEAT-AGT-COMPOSE_STRATEGY_SPECS -->
### FEAT-AGT-COMPOSE_STRATEGY_SPECS — JSON strategy and indicator DSL composition

- **Atomic value:** Compose reviewed receiver-owned DSL candidates with provenance.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Compose reviewed receiver-owned DSL candidates with provenance.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `STU-008`, `AST-010`
- `FR-AGT-COMPOSE_STRATEGY_DSL`, `FR-AGT-VALIDATE_DSL_HANDOFF`, `FR-AGT-REPORT_UNSUPPORTED_EXPRESSIONS`, `FR-AGT-PRESERVE_DSL_PROVENANCE`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.strategy-specs@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- FEATURE_CONTROL: `DEC-011`
- WORKFLOW: `WF-AGT-COMPOSE_STRATEGY_SPEC`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-COMPOSE_STRATEGY_SPECS -->

<!-- FEATURE_CARD_START FEAT-AGT-ADVISE_PORTFOLIO -->
### FEAT-AGT-ADVISE_PORTFOLIO — Portfolio and risk advisory

- **Atomic value:** Produce expiring non-binding portfolio advice with independent risk challenge.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Produce expiring non-binding portfolio advice with independent risk challenge.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-ADVISE_PORTFOLIO_ALLOCATION`, `FR-AGT-CHALLENGE_PORTFOLIO_RISK`, `FR-AGT-EXPIRE_PORTFOLIO_ADVICE`, `FR-AGT-PRESERVE_PORTFOLIO_AUTHORITY`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.portfolio-advisory@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-ADVISE_PORTFOLIO`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-ADVISE_PORTFOLIO -->

<!-- FEATURE_CARD_START FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS -->
### FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS — Strategy proposal composition and handoff

- **Atomic value:** Compose and submit expiring Strategy-owned proposal candidates without execution fields.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Compose and submit expiring Strategy-owned proposal candidates without execution fields.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-COMPOSE_STRATEGY_PROPOSALS`, `FR-AGT-SUBMIT_STRATEGY_PROPOSALS`, `FR-AGT-RECORD_STRATEGY_RECEIPTS`, `FR-AGT-PRESERVE_STRATEGY_AUTHORITY`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.strategy-proposals@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-COMPOSE_STRATEGY_PROPOSAL`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS -->

<!-- FEATURE_CARD_START FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS -->
### FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS — Sandboxed source artifact fallback

- **Atomic value:** Author staged source only after a proven DSL gap under sandbox authority.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Author staged source only after a proven DSL gap under sandbox authority.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-PROVE_DSL_GAP`, `FR-AGT-AUTHOR_SANDBOX_ARTIFACTS`, `FR-AGT-RECORD_ARTIFACT_MANIFEST`, `FR-AGT-ENFORCE_STAGING_ONLY`, `FR-AGT-CLEANUP_SANDBOX_ARTIFACTS`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.sandbox-artifacts@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-AUTHOR_SANDBOX_ARTIFACT`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS -->

<!-- FEATURE_CARD_START FEAT-AGT-CALIBRATE_OUTCOMES -->
### FEAT-AGT-CALIBRATE_OUTCOMES — Post-horizon outcome calibration

- **Atomic value:** Match outcomes, score calibration/value, and propose evidence-backed profile changes.
- **Status:** `SPECIFIED_TARGET`; evidence state is `PENDING_EVIDENCE`.
- **Owns:** Match outcomes, score calibration/value, and propose evidence-backed profile changes.
- **Does not own:** Transport/presentation or domain calculations outside Agentic's semantic boundary; dependency owners retain their state and policy.
- **State, lifecycle, and removal boundary:** One feature generation and disposer; durable state, when required, stays in the semantic owner's namespace and removal follows declared retention.
- **Source coverage:** Primary IDs below plus the applicable Unified Specification sections, controls, catalogues, and algorithms named in this card.
- **Legacy aliases:** §54 legacy FEAT-AGT-01–22 mapping where applicable; alias only.

#### Owned functional requirements

- `FR-AGT-MATCH_OUTCOMES`, `FR-AGT-SCORE_CALIBRATION`, `FR-AGT-ATTRIBUTE_INCREMENTAL_VALUE`, `FR-AGT-PROPOSE_PROFILE_CHANGES`

#### Feature-specific non-functional requirements

- No exclusive `PER-*` owner row; feature-local bounds and cleanup obligations are derived from its source requirements and shared NFR references without creating duplicate IDs.

#### References to applicable shared NFRs

- `NFR-P-009`, `NFR-R-003`, `NFR-S-001`–`NFR-S-005`, `NFR-F-001`–`NFR-F-005`, all `NFR-AGT-*` in the shared catalogue.

#### Public contracts and dependencies

- **Provides:** agentic.outcome-calibration@1
- **Depends on:** Other declared Agentic capabilities plus receiver-owned deterministic contracts exactly as §43.1.

#### Catalogue entries / algorithms / controls delivered

- Strict records, profiles, roles/tools/workflows and controls in §§43–52.
- WORKFLOW: `WF-AGT-CALIBRATE_OUTCOME`

#### Acceptance tests and evidence

- `SPECIFIED_ACCEPTANCE`: Feature-card contract/schema/security/removal suites and the exact §52 acceptance evidence.
- `VERIFIED_CURRENT`: only evidence cited by the owning package README/runtime registry; this Task makes no new implementation-complete claim.
<!-- FEATURE_CARD_END FEAT-AGT-CALIBRATE_OUTCOMES -->

## 12. Legacy and summary disposition

<!-- LEGACY_COVERAGE_START -->
| Class | Disposition | Source IDs | Treatment |
|---|---|---|---|
| LEGACY_FEATURE_ALIAS | §54 action-based feature/receiver mapping | `FEAT-AGT-01`–`FEAT-AGT-22` | Alias only; excluded from the 98-feature index and current/target totals. |
| LEGACY_REQUIREMENT_ALIAS | §54 parity/adapt/merge/retire mapping | `FR-AGENTIC-001`–`FR-AGENTIC-072` | Alias only; excluded from the 290 primary-functional total. |
<!-- LEGACY_COVERAGE_END -->

- `FEAT-AGT-01`–`FEAT-AGT-22` are §54 legacy aliases. Their dispositions map into the twenty action-based Agentic target features or receiver-owned contracts; they are excluded from the feature index and totals.
- `FR-AGENTIC-001`–`FR-AGENTIC-072` are legacy range aliases and never primary rows.
- The 32 §27 `FR-*` rows remain useful acceptance/traceability bindings, but §8 marks them non-additive so they do not inflate the 290 primary-functional total.
- Product surfaces, widgets, roles, workflows, algorithms, benchmarks, tasks, and milestones are catalogues/controls or contributions unless they independently satisfy the atomic-feature test.
- Existing numeric current IDs in owning READMEs are neither silently retired nor duplicated here. A later owner-approved implementation Task must reconcile any true semantic match or conflict.

## 13. Completion rule

This register is complete only when its validator reports zero omissions, duplicate primary mappings, undefined feature references, legacy-current identities, missing card sections, unknown NFR references, section gaps, or total drift. Implementation completion remains a separate owning-feature claim requiring contracts, provider, registration/composition, Interfaces/UI where applicable, executable usage, tests, removal evidence, and current README status.

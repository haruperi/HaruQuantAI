# Agentic

> **Package:** `app/services/agentic/`  
> **Domain ID:** `D-AGT`  
> **Status:** `Missing` — authoritative target specification; no legacy implementation status carries forward  
> **Last updated:** `2026-09-03`  
> **Feature count:** `20` focused service features  
> **Built-in LLM profiles:** `22` across `7` role families  
> **Architecture decisions:** `ADR-AGT-001` and `ADR-AGT-001-A1`

> This README is the Agentic domain package's **single source of truth** for domain boundaries, focused feature capabilities, semantic contract ownership, role contributions, workflows, state ownership, configuration, implementation sequence, deletion behavior, acceptance evidence, and current status. Update it before modifying or adding Agentic code.

---

## Code-Aligned Implementation Convention

Agentic uses the repository's current feature substrate. Every feature lives directly under `app/services/agentic/<feature>/`, declares one immutable `SPEC: FeatureSpec` in `manifest.py`, parses only its exact strict `config.py` keys, mounts through `feature.py`, publishes versioned capability contracts from `app/contracts/agentic/`, and owns every reversible effect through `FeatureContext`/`FeatureScope`.

There are no domain YAML manifests, package-root facades, shared Agentic settings modules, shared Agentic persistence packages, agent-per-folder service hierarchies, import-time registration, or cross-feature implementation imports. Role profiles are immutable contributions registered by their owning feature through `agentic.roles@1` with exact disposal. Receiver domains own the canonical contracts they validate or execute.

Every implemented feature contains:

```text
app/services/agentic/<feature>/
├── README.md
├── __init__.py          # empty or module docstring only
├── manifest.py          # immutable SPEC; no behavior
├── config.py            # strict immutable parser; unknown keys fail
├── feature.py           # mount/create_feature lifecycle adapter
├── <primary_module>.py  # focused business responsibility + executable usage
└── optional focused files owned by that feature only
```

Feature-level tests live at `tests/services/agentic/<feature>/`. The designated primary module contains the executable usage demonstration; automated tests and usage evidence are separate. D-IFACE/API owns external transport and authentication. UI owns widget rendering and context-contribution collection. The code-backed delivery authority is `docs/dev/feature_implementation_pipeline.md`.

---

## 1. Purpose and Boundary

### Purpose

Agentic converts governed evidence into typed, attributable, challenge-tested research and decision-support artifacts and receiver-owned candidate requests. It coordinates LLM reasoning, context, specialist delegation, research design, DSL authoring, challenge, synthesis, and outcome calibration while keeping deterministic domains authoritative.

The website includes one context-aware LLM agent named exactly **Chat Bot** (`chat_bot`). Chat Bot can understand a bounded typed snapshot of the current page and widgets, answer safe contextual questions, and delegate to an eligible specialist. It is not a CEO, Firm Coordinator, risk authority, strategy authority, trader, broker controller, or UI mutation engine.

### Authority hierarchy

1. The authenticated human Owner defines mandates and supplies exact human actions where policy requires them.
2. System, Workspace, Data, Catalogue, Indicators, Analytics, Research, Simulation, Optimization, Strategy, Portfolio, Risk, Trading, Brokers, and D-IFACE retain their semantic and consequential authority.
3. Agentic interprets, challenges, designs, composes, and proposes through public capability contracts.
4. Model/workflow frameworks such as Google ADK are optional replaceable providers behind HaruQuantAI contracts.
5. Model output, retrieved content, browser context, memory, and peer messages are untrusted until the owning deterministic rules validate their permitted use.

### Owns

- the 20 focused feature capabilities in the registry below;
- Agentic tasks, workflows, checkpoints, budgets, provenance, operations, incidents, leases, human actions, context bundles, memory, role contributions, claim graphs, deliberation, synthesis, research-search accounting, Agentic-authored candidates, and calibration evidence;
- provider-neutral model invocation and role/profile policy;
- the Chat Bot conversational and specialist-delegation semantics;
- Agentic-side research campaign and near-duplicate accounting;
- staged sandbox-artifact metadata when code fallback is explicitly allowed.

### Does not own

- UI widget rendering, DOM, browser state, navigation execution, or workspace-context capture;
- external HTTP/SSE/WebSocket authentication and transport;
- canonical market/document/account data, source licensing, instruments, sessions, indicators, analytics, research results, simulation runs, optimization trials, strategy definitions, portfolio decisions, risk approvals, orders, fills, broker state, or production deployment;
- receiver-owned request/result contracts after handoff;
- an alternate policy, persistence, calculation, lifecycle, or execution engine for another domain.

### Deletion boundary

Deleting `app/services/agentic/` removes new Agentic reasoning, Chat Bot assistance, specialist workflows, Agentic research design, and Agentic-authored candidates. It must not prevent the kernel, composition substrate, UI shell, or deterministic domains from starting; weaken Risk/Trading/Brokers safety; change already accepted strategies; delete receiver-owned evidence; or fabricate fallback decisions. Consumers expose explicit capability-unavailable or degraded states.

---

## 2. Constitutional Invariants

1. An agent may propose; only the owning deterministic domain may decide or mutate.
2. No Agentic capability or role imports broker SDKs, holds broker credentials, constructs orders, clears kill switches, approves risk, or deploys artifacts.
3. Titles and role names grant no authority.
4. Every model, prompt, role, tool, lease, human action, handoff, artifact, state transition, and result is typed, versioned, bounded, attributable, and auditable.
5. Retrieved content, page text, widget values, memory, and peer messages are data, never instructions.
6. Missing, stale, poisoned, unlicensed, incompatible, out-of-scope, or unverifiable evidence fails closed or produces explicit partial coverage.
7. Claim graphs—not unrestricted transcripts or hidden reasoning—are the canonical reasoning record.
8. Independent first-pass challenge precedes exposure to proposer narrative when challenge is required.
9. Consensus is not truth, authorization, position size, or promotion evidence by itself.
10. Councils, roles, models, prompts, tools, and rounds must demonstrate uncertainty-adjusted value over simpler baselines.
11. JSON strategy/indicator DSL is the default generated artifact; arbitrary code is an exceptional sandboxed fallback.
12. Search variants, failures, amendments, researcher degrees of freedom, and holdout receipts remain visible.
13. Outcome calibration can propose change candidates but never self-modify production policy, prompts, permissions, thresholds, or eligibility.
14. Disabling/removing Agentic preserves deterministic safety equivalence.

---

## 3. Focused Feature Registry
| Order | Status | Wave | Feature | Folder | Provides | State | Primary responsibility | Removal result |
|---:|---|---:|---|---|---|---|---|---|
| 1 | Missing | 1 | `FEAT-AGT-ENFORCE_MANDATE` — Mandate Enforcement | `enforce_mandate/` | `agentic.mandate@1` | None | Validate the immutable Agentic operating envelope and answer exact scope, budget, environment, role, feature, and prohibited-authority questions. The stricter system, Risk, venue, or runtime rule always wins. | Reject all new Agentic work. Retained evidence stays readable through its owning capabilities; deterministic safety remains unchanged. |
| 2 | Missing | 1 | `FEAT-AGT-OPERATE_RUNS` — Operations, Incidents, and Replay Validation | `operate_runs/` | `agentic.operations@1` | `agentic.operations` / RETAIN | Record correlated redacted operational evidence, inspect traces, classify incidents, contain affected work, expose readiness/cost diagnostics, and validate side-effect-free replay references. This feature is deterministic and invokes no model. | Stop Agentic work that requires mandatory audit. Preserve retained traces/incidents. Cancel subscriptions and exact callbacks; do not affect deterministic-domain audit or safety. |
| 3 | Missing | 1 | `FEAT-AGT-REGISTER_ROLES` — Role Contribution Registry | `register_roles/` | `agentic.roles@1` | None | Register, verify, resolve, list, enable, disable, and exactly dispose versioned role contributions and prompt artifacts. Registration does not grant eligibility or authority. | Remove the role registry capability and exactly dispose all contributions registered through it. Model-dependent workflows become unready; retained operations/workflow evidence remains. |
| 4 | Missing | 1 | `FEAT-AGT-GOVERN_TOOL_CALLS` — Tool Governance and Human Actions | `govern_tool_calls/` | `agentic.tool-governance@1` | `agentic.tool_governance` / RETAIN | Register eligible Agentic tools, issue invocation-bound capability leases, authorize every call/retry, filter returned content before model access, revoke leases, and manage typed human actions. This feature is deterministic and invokes no model. | Revoke all outstanding leases, dispose tool contributions, refuse new tool calls and pending actions, and preserve retained approval/audit evidence. Model-only workflows may continue only when their profiles permit zero tools. |
| 5 | Missing | 1 | `FEAT-AGT-INVOKE_MODELS` — Provider-Neutral Model Invocation | `invoke_models/` | `agentic.model-inference@1` | None | Validate an evaluated model profile and execute one schema-bound model invocation without silent provider/model substitution. Provider adapters are replaceable; provider objects never cross the contract. | Cancel/drain managed invocations, close provider clients, and make model-dependent capabilities unready unless composition has an independently evaluated compatible provider replacement. |
| 6 | Missing | 2 | `FEAT-AGT-RUN_WORKFLOWS` — Durable Workflow Orchestration | `run_workflows/` | `agentic.workflows@1` | `agentic.workflows` / RETAIN | Submit, route, checkpoint, resume, cancel, expire, drain, and inspect bounded idempotent workflows. Routing and bounds are deterministic. This feature owns the Research Planner and Artifact Planner role contributions but gives them no authority. | Stop new workflows, revoke child leases, cancel or drain active tasks according to policy, and preserve checkpoints/results. Consumers lose Agentic workflow execution, not deterministic domain operations. |
| 7 | Missing | 2 | `FEAT-AGT-ASSEMBLE_CONTEXT` — Point-in-Time Context Assembly | `assemble_context/` | `agentic.context@1` | None | Assemble bounded task context from public evidence and UI context using provenance, availability, freshness, licensing, trust, injection, scope, and deduplication filters. Browser context or memory never substitutes for authoritative evidence. | New model work requiring governed context becomes unready. Pure deterministic Agentic reads that do not require context may continue. No retained state is deleted. |
| 8 | Missing | 2 | `FEAT-AGT-MANAGE_MEMORY` — Governed Memory | `manage_memory/` | `agentic.memory@1` | `agentic.memory` / RETAIN | Accept memory candidates; validate, redact, classify, promote, retrieve, supersede, expire, purge, and export workflow, working, episodic, validated-semantic, and audit memory. Memory remains context, not market truth or policy. | New memory reads/writes stop. Workflows may continue statelessly only when memory is optional. Retained records remain subject to policy and audit access; TTL-bound working state is cleaned by declared policy. |
| 9 | Missing | 2 | `FEAT-AGT-EVALUATE_PROFILES` — Profile and Topology Evaluation | `evaluate_profiles/` | `agentic.profile-evaluation@1` | `agentic.profile_evaluation` / RETAIN | Aggregate feature-local evaluation evidence and deterministically decide eligibility for role, prompt, model, tool, workflow, and council-topology profiles. Compare deterministic, single-agent, and council baselines with uncertainty and cost. | Freeze current evidence as retained history but prevent new or changed profiles/topologies from becoming eligible. Existing eligible profiles may run only while mandate and policy permit. |
| 10 | Missing | 2 | `FEAT-AGT-ASSIST_OPERATOR` — Website Chat Bot and Specialist Delegation | `assist_operator/` | `agentic.operator-assistance@1` | `agentic.operator_conversations` / DELETE | Run the website agent named exactly Chat Bot. Validate current page/widget context, answer safe contextual questions, deterministically verify specialist routes, wait for specialist results, and present one coherent response in the same conversation. Initial actions are read context, answer, explain, delegate, summarize, and suggest navigation only. | Chat Bot becomes unavailable. Existing session/task conversation state is deleted or expires by policy; specialists and internal workflows may remain available through other authorized interfaces. UI shell and widgets remain usable without LLM assistance. |
| 11 | Missing | 3 | `FEAT-AGT-MANAGE_CLAIMS` — Claim-and-Evidence Graph | `manage_claims/` | `agentic.claims@1` | `agentic.claims` / RETAIN | Normalize, validate, relate, version, expire, and inspect observed facts, deterministic derivations, model inferences, forecasts, recommendations, assumptions, contradictions, falsifiers, and uncertainty. Own the five evidence-analysis role contributions. | Stop new claim graph mutation and claim-based reasoning. Preserve retained graphs and facts for audit/export. Capabilities requiring a canonical reasoning record become unready. |
| 12 | Missing | 3 | `FEAT-AGT-DELIBERATE_RESEARCH` — Independent Challenge and Deliberation | `deliberate_research/` | `agentic.deliberation@1` | `agentic.deliberation` / RETAIN | Run bounded independent challenge and rebuttal against claim graphs. Challengers assess objective/evidence before proposer narrative, preserve dissent, record independence correlation, and cannot authorize outcomes. Own the six challenge profiles. | Councils and challenge-required workflows become unavailable. Low-risk single-specialist paths may continue when their workflow policy allows. Preserve retained dissent and records. |
| 13 | Missing | 3 | `FEAT-AGT-SYNTHESIZE_RESEARCH` — Research Synthesis | `synthesize_research/` | `agentic.synthesis@1` | None | Produce a typed decision-support synthesis from the current claim graph and deliberation record, preserving unsupported, contested, refuted, unknown, expired, and dissenting material. Own the Research Synthesizer role. | New multi-source research synthesis becomes unavailable. Specialist results and retained claim/deliberation evidence remain separately accessible. |
| 14 | Missing | 4 | `FEAT-AGT-GOVERN_RESEARCH_SEARCH` — Research Campaign and Search Governance | `govern_research_search/` | `agentic.research-search@1` | `agentic.research_search` / RETAIN | Track research campaigns, hypothesis families, dataset families, variants, prompts/models, amendments, all attempts/failures, search budgets, holdout reservations, and degrees of freedom; classify near-duplicates deterministically. | Refuse new governed research design, optimization, or holdout use. Preserve campaign/search history and outstanding reservations for audit; do not permit a different feature to reset budgets. |
| 15 | Missing | 4 | `FEAT-AGT-DESIGN_RESEARCH` — Falsifiable Research Design | `design_research/` | `agentic.research-design@1` | None | Convert supported claim graphs into falsifiable hypothesis, experiment-request, and bounded-search candidates using receiver-owned schemas and registered campaign/search identity. Own Hypothesis Designer, Experiment Designer, and Bounded Search Designer roles. | Stop new model-assisted research design. Existing receiver-owned runs and Agentic search ledgers remain valid and accessible. |
| 16 | Missing | 5 | `FEAT-AGT-COMPOSE_STRATEGY_SPECS` — JSON Strategy and Indicator DSL Composition | `compose_strategy_specs/` | `agentic.strategy-specs@1` | None | Compose candidate JSON strategy/indicator DSL artifacts from approved hypotheses and exact Strategy/Indicators schema capabilities. Own the Strategy DSL Author role. Agentic stages a candidate; the receiver validates, compiles, registers, and owns lifecycle. | Stop new Agentic DSL composition. Existing Strategy/Indicators artifacts and registered versions are unaffected. |
| 17 | Missing | 5 | `FEAT-AGT-ADVISE_PORTFOLIO` — Portfolio and Risk Advisory | `advise_portfolio/` | `agentic.portfolio-advisory@1` | None | Produce expiring non-binding portfolio/risk advice from current receiver-owned evidence and independent challenges. Own the Portfolio Advisory Synthesizer. Output contains no approval, executable quantity, lot size, order, or kill-switch action. | Stop new Agentic advisory. Portfolio and Risk continue normally; existing advice expires and remains only in retained workflow/audit evidence. |
| 18 | Missing | 5 | `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS` — Strategy Proposal Composition and Handoff | `compose_strategy_proposals/` | `agentic.strategy-proposals@1` | None | Compose an untrusted Strategy-owned proposal request with thesis, evidence, horizon, invalidation, uncertainty, scope, and expiry; submit it through Strategy's public intake. Own the Strategy Proposal Synthesizer. A receipt is never an order or fill. | Stop new Agentic proposals and handoffs. Strategy/Risk/Trading/Brokers remain unaffected; accepted receiver-owned records retain their own lifecycle. |
| 19 | Missing | 6 | `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS` — Sandboxed Source Artifact Fallback | `author_sandbox_artifacts/` | `agentic.sandbox-artifacts@1` | `agentic.sandbox_artifacts` / DELETE | As an exceptional fallback, generate source artifacts only from an authenticated specification and a real attested sandbox lease; validate raw/resolved paths, stage outputs, hashes, tests, dependencies/SBOM, search history, and provenance. Own the Sandbox Code Author role. | Revoke sandbox leases, cancel tasks, clean ephemeral/staged artifacts according to policy, and refuse new code generation. No production code or receiver-owned artifact is removed. |
| 20 | Missing | 6 | `FEAT-AGT-CALIBRATE_OUTCOMES` — Post-Horizon Outcome Calibration | `calibrate_outcomes/` | `agentic.outcome-calibration@1` | `agentic.outcome_calibration` / RETAIN | Bind matured outcomes to forecasts, recommendations, role/workflow topology, receiver decisions, costs, regimes, and simpler baselines; compute calibration and incremental utility; produce governed change candidates without self-modification. | Stop new calibration and profile-change candidates. Preserve historical calibration evidence. Eligibility falls back to existing evidence without inventing neutral performance. |

### Dependency waves

| Wave | Features | Purpose |
|---:|---|---|
| 1 | `ENFORCE_MANDATE`, `OPERATE_RUNS`, `REGISTER_ROLES`, `GOVERN_TOOL_CALLS`, `INVOKE_MODELS` | Establish authority, audit, role contribution, invocation permissions, and provider-neutral model seams. |
| 2 | `RUN_WORKFLOWS`, `ASSEMBLE_CONTEXT`, `MANAGE_MEMORY`, `EVALUATE_PROFILES`, `ASSIST_OPERATOR` | Establish durable execution, bounded context, governed memory, evaluated eligibility, and website assistance. |
| 3 | `MANAGE_CLAIMS`, `DELIBERATE_RESEARCH`, `SYNTHESIZE_RESEARCH` | Establish canonical reasoning records, independent challenge, dissent, and synthesis. |
| 4 | `GOVERN_RESEARCH_SEARCH`, `DESIGN_RESEARCH` | Establish campaign accounting and falsifiable experiment/search design. |
| 5 | `COMPOSE_STRATEGY_SPECS`, `ADVISE_PORTFOLIO`, `COMPOSE_STRATEGY_PROPOSALS` | Produce receiver-owned candidate requests without receiver authority. |
| 6 | `AUTHOR_SANDBOX_ARTIFACTS`, `CALIBRATE_OUTCOMES` | Add exceptional code fallback and outcome-grounded evolution. |

---

## 4. Actual Agent Roster

The built-in workforce contains 22 immutable LLM role profiles. Profiles are not 22 service features, standing processes, or authority-bearing persons. A workflow invokes only eligible roles required by the task.

| # | Role family | Display name | Canonical role ID | Owning feature |
|---:|---|---|---|---|
| 1 | Operator Chat | Chat Bot | `chat_bot` | `FEAT-AGT-ASSIST_OPERATOR` |
| 2 | Coordinator/Planner | Research Planner | `research_planner` | `FEAT-AGT-RUN_WORKFLOWS` |
| 3 | Coordinator/Planner | Artifact Planner | `artifact_planner` | `FEAT-AGT-RUN_WORKFLOWS` |
| 4 | Evidence Analyst | Analytics Evidence Reviewer | `analytics_evidence_reviewer` | `FEAT-AGT-MANAGE_CLAIMS` |
| 5 | Evidence Analyst | Fundamental Analyst | `fundamental_analyst` | `FEAT-AGT-MANAGE_CLAIMS` |
| 6 | Evidence Analyst | Sentiment Analyst | `sentiment_analyst` | `FEAT-AGT-MANAGE_CLAIMS` |
| 7 | Evidence Analyst | Technical and Market-Structure Analyst | `technical_structure_analyst` | `FEAT-AGT-MANAGE_CLAIMS` |
| 8 | Evidence Analyst | Quantitative Analyst | `quantitative_analyst` | `FEAT-AGT-MANAGE_CLAIMS` |
| 9 | Research Designer | Hypothesis Designer | `hypothesis_designer` | `FEAT-AGT-DESIGN_RESEARCH` |
| 10 | Research Designer | Experiment Designer | `experiment_designer` | `FEAT-AGT-DESIGN_RESEARCH` |
| 11 | Research Designer | Bounded Search Designer | `bounded_search_designer` | `FEAT-AGT-DESIGN_RESEARCH` |
| 12 | Independent Challenger | Causality Challenger | `causality_challenger` | `FEAT-AGT-DELIBERATE_RESEARCH` |
| 13 | Independent Challenger | Leakage Challenger | `leakage_challenger` | `FEAT-AGT-DELIBERATE_RESEARCH` |
| 14 | Independent Challenger | Robustness Challenger | `robustness_challenger` | `FEAT-AGT-DELIBERATE_RESEARCH` |
| 15 | Independent Challenger | Risk Challenger | `risk_challenger` | `FEAT-AGT-DELIBERATE_RESEARCH` |
| 16 | Independent Challenger | Compliance Challenger | `compliance_challenger` | `FEAT-AGT-DELIBERATE_RESEARCH` |
| 17 | Independent Challenger | Operations and Security Challenger | `operations_security_challenger` | `FEAT-AGT-DELIBERATE_RESEARCH` |
| 18 | Synthesizer | Research Synthesizer | `research_synthesizer` | `FEAT-AGT-SYNTHESIZE_RESEARCH` |
| 19 | Synthesizer | Portfolio Advisory Synthesizer | `portfolio_advisory_synthesizer` | `FEAT-AGT-ADVISE_PORTFOLIO` |
| 20 | Synthesizer | Strategy Proposal Synthesizer | `strategy_proposal_synthesizer` | `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS` |
| 21 | Artifact Engineer | Strategy DSL Author | `strategy_dsl_author` | `FEAT-AGT-COMPOSE_STRATEGY_SPECS` |
| 22 | Artifact Engineer | Sandbox Code Author | `sandbox_code_author` | `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS` |

### Role artifact contract

Each role-bearing feature owns immutable package-local data:

```text
roles/<role_id>/
├── role.json
└── prompt.md
```

`role.json` conforms to `RoleManifest`. `prompt.md` contains base role instructions, evidence/citation boundaries, uncertainty, falsifiers, refusals, output protocol, and prohibited authority. The feature resolves `agentic.roles@1` during mount, registers the contribution, and registers the exact returned disposer with its scope. It does not import the role-registry implementation.

Built-in role ownership:

- `RUN_WORKFLOWS`: Research Planner, Artifact Planner.
- `ASSIST_OPERATOR`: Chat Bot.
- `MANAGE_CLAIMS`: Analytics Evidence Reviewer, Fundamental Analyst, Sentiment Analyst, Technical and Market-Structure Analyst, Quantitative Analyst.
- `DESIGN_RESEARCH`: Hypothesis Designer, Experiment Designer, Bounded Search Designer.
- `DELIBERATE_RESEARCH`: six independent challenge profiles.
- `SYNTHESIZE_RESEARCH`: Research Synthesizer.
- `ADVISE_PORTFOLIO`: Portfolio Advisory Synthesizer.
- `COMPOSE_STRATEGY_PROPOSALS`: Strategy Proposal Synthesizer.
- `COMPOSE_STRATEGY_SPECS`: Strategy DSL Author.
- `AUTHOR_SANDBOX_ARTIFACTS`: Sandbox Code Author.

Mandate enforcement, authorization, state transitions, incident containment, memory promotion, search accounting, eligibility arithmetic, receiver registration, risk approval, execution, and broker connectivity are deterministic services—not agents.

---

## 5. Shared Contract Ownership

### 5.1 Agentic-owned physical contract modules

All public definitions live under `app/contracts/agentic/`. `app/services/agentic/` implements them and does not re-export substitute models.

| Module | Capability key | Protocol | Primary async method | Request union / operation | Success or domain outcome | Streaming |
|---|---|---|---|---|---|---|
| `mandate.py` | `agentic.mandate@1` | `MandateEnforcement` | `enforce_mandate(request)` | `VALIDATE`, `CHECK_SCOPE`, `INSPECT` | `MandateAccepted`, `MandateScopeDecision`, `MandateView` plus shared refusal/failure | — |
| `operations.py` | `agentic.operations@1` | `AgenticOperations` | `operate_agentic_runs(request)` | `RECORD`, `INSPECT_TRACE`, `REPORT_INCIDENT`, `VALIDATE_REPLAY`, `INSPECT_READINESS`, `EXPORT` | `OperationReceipt`, `AgenticRunTrace`, `IncidentRecord`, `ReplayValidation`, `AgenticReadinessView`, `OperationsExport` plus shared refusal/failure | `AgenticIncidentRaised`, `AgenticReadinessChanged` |
| `roles.py` | `agentic.roles@1` | `RoleContributionRegistry` | `manage_role_contributions(request)` | `REGISTER`, `UNREGISTER`, `RESOLVE`, `LIST`, `SET_ELIGIBILITY_REFERENCE` | `RoleRegistrationReceipt`, `RoleRemovalReceipt`, `RoleResolution`, `RoleList`, `RoleEligibilityReferenceReceipt` plus shared refusal/failure | `RoleContributionRegistered`, `RoleContributionRemoved`, `RoleEligibilityReferenceChanged` |
| `tool_governance.py` | `agentic.tool-governance@1` | `ToolCallGovernance` | `govern_tool_calls(request)` | `REGISTER_TOOL`, `REQUEST_LEASE`, `AUTHORIZE_INVOCATION`, `FILTER_RESULT`, `REVOKE_LEASE`, `REQUEST_HUMAN_ACTION`, `DECIDE_HUMAN_ACTION` | `ToolRegistrationReceipt`, `CapabilityLease`, `ToolAuthorizationDecision`, `FilteredToolResult`, `LeaseRevocationReceipt`, `HumanActionRequest`, `HumanActionDecision` plus shared refusal/failure | `CapabilityLeaseIssued`, `CapabilityLeaseRevoked`, `HumanActionRequested`, `HumanActionDecided` |
| `model_inference.py` | `agentic.model-inference@1` | `ModelInference` | `invoke_model(request)` | `INVOKE` | `ModelInvocationSuccess`, `ModelInvocationRefusal` plus shared refusal/failure | `ModelInvocationStarted`, `ModelInvocationCompleted`, `ModelInvocationRefused` |
| `workflows.py` | `agentic.workflows@1` | `AgenticWorkflowRunner` | `run_agentic_workflows(request)` | `SUBMIT`, `RESUME`, `CANCEL`, `EXPIRE`, `INSPECT`, `DRAIN` | `WorkflowAccepted`, `WorkflowRun`, `WorkflowCancellationReceipt`, `WorkflowExpiryReceipt`, `WorkflowDrainReceipt` plus shared refusal/failure | `WorkflowStateChanged`, `WorkflowProgressed`, `WorkflowWaitingForHuman`, `WorkflowTerminated` |
| `context.py` | `agentic.context@1` | `AgenticContextAssembly` | `assemble_agentic_context(request)` | `ASSEMBLE`, `INSPECT_EXCLUSIONS` | `AgenticContextBundle`, `ContextExclusionReport` plus shared refusal/failure | — |
| `memory.py` | `agentic.memory@1` | `AgenticMemory` | `manage_agentic_memory(request)` | `SUBMIT_CANDIDATE`, `PROMOTE`, `RETRIEVE`, `SUPERSEDE`, `PURGE`, `EXPORT` | `MemoryCandidateReceipt`, `MemoryPromotionDecision`, `MemoryQueryResult`, `MemorySupersessionReceipt`, `MemoryPurgeReceipt`, `MemoryExport` plus shared refusal/failure | `MemoryPromoted`, `MemorySuperseded`, `MemoryExpired` |
| `profile_evaluation.py` | `agentic.profile-evaluation@1` | `AgenticProfileEvaluation` | `evaluate_agentic_profiles(request)` | `EVALUATE`, `INSPECT_ELIGIBILITY`, `REVOKE_ELIGIBILITY`, `COMPARE_BASELINE` | `ProfileEvaluationReport`, `EligibilityDecision`, `EligibilityRevocationReceipt`, `BaselineComparison` plus shared refusal/failure | `ProfileEligibilityChanged` |
| `operator_assistance.py` | `agentic.operator-assistance@1` | `OperatorAssistance` | `assist_operator(request)` | `RESPOND`, `SUMMARIZE_SPECIALIST_RESULT` | `OperatorAnswer`, `OperatorSpecialistAnswer`, `OperatorConversationSummary` plus shared refusal/failure | `OperatorTurnAccepted`, `WorkspaceContextValidated`, `SpecialistRouteProposed`, `SpecialistRouteAuthorized`, `SpecialistStarted`, `SpecialistCompleted`, `OperatorResponseDelta`, `OperatorTurnCompleted`, `OperatorTurnRefused`, `OperatorTurnFailed` |
| `claims.py` | `agentic.claims@1` | `AgenticClaimGraph` | `manage_claim_graphs(request)` | `CREATE_GRAPH`, `APPEND_CLAIM`, `RELATE_CLAIMS`, `TRANSITION_CLAIM`, `ASSESS_RELIABILITY`, `INSPECT_GRAPH` | `ClaimGraph`, `ClaimReceipt`, `ClaimRelationReceipt`, `ClaimStatusReceipt`, `ClaimReliabilityAssessment`, `ClaimGraphView` plus shared refusal/failure | `ClaimCreated`, `ClaimRelated`, `ClaimStatusChanged`, `ClaimExpired` |
| `deliberation.py` | `agentic.deliberation@1` | `AgenticDeliberation` | `deliberate_research(request)` | `START`, `CONTINUE`, `CANCEL`, `INSPECT` | `DeliberationRecord`, `DeliberationCancellationReceipt`, `DeliberationView` plus shared refusal/failure | `DeliberationRoundStarted`, `ChallengeRecorded`, `DissentRecorded`, `DeliberationStopped` |
| `synthesis.py` | `agentic.synthesis@1` | `AgenticResearchSynthesis` | `synthesize_research(request)` | `SYNTHESIZE` | `ResearchSynthesis`, `ResearchInsufficientEvidence` plus shared refusal/failure | `ResearchSynthesisCompleted` |
| `research_search.py` | `agentic.research-search@1` | `AgenticResearchSearchGovernance` | `govern_research_search(request)` | `REGISTER_CAMPAIGN`, `REGISTER_FAMILY`, `REGISTER_VARIANT`, `RECORD_ATTEMPT`, `RESERVE_HOLDOUT`, `CLOSE_CAMPAIGN`, `INSPECT` | `ResearchCampaign`, `HypothesisFamilyReceipt`, `ResearchVariantReceipt`, `ResearchAttemptReceipt`, `HoldoutReservationReceipt`, `CampaignClosureReceipt`, `ResearchSearchView` plus shared refusal/failure | `ResearchCampaignOpened`, `ResearchAttemptRecorded`, `HoldoutReserved`, `ResearchCampaignClosed` |
| `research_design.py` | `agentic.research-design@1` | `AgenticResearchDesign` | `design_research(request)` | `DESIGN_HYPOTHESIS`, `DESIGN_EXPERIMENT`, `DESIGN_SEARCH` | `HypothesisCandidate`, `ExperimentRequestCandidate`, `SearchRequestCandidate` plus shared refusal/failure | `ResearchDesignCompleted` |
| `strategy_specs.py` | `agentic.strategy-specs@1` | `AgenticStrategySpecComposition` | `compose_strategy_specs(request)` | `COMPOSE`, `VALIDATE_HANDOFF` | `StrategySpecCandidate`, `StrategySpecHandoffReceipt`, `UnsupportedExpressionReport` plus shared refusal/failure | `StrategySpecComposed` |
| `portfolio_advisory.py` | `agentic.portfolio-advisory@1` | `AgenticPortfolioAdvisory` | `advise_portfolio(request)` | `ADVISE` | `PortfolioAdvisory`, `PortfolioAdvisoryInsufficientEvidence` plus shared refusal/failure | `PortfolioAdvisoryCompleted` |
| `strategy_proposals.py` | `agentic.strategy-proposals@1` | `AgenticStrategyProposalComposition` | `compose_strategy_proposals(request)` | `COMPOSE`, `SUBMIT` | `StrategyProposalCandidate`, `StrategyProposalReceipt` plus shared refusal/failure | `StrategyProposalComposed`, `StrategyProposalSubmitted` |
| `sandbox_artifacts.py` | `agentic.sandbox-artifacts@1` | `AgenticSandboxArtifactAuthoring` | `author_sandbox_artifacts(request)` | `AUTHOR`, `INSPECT`, `CLEANUP` | `SandboxArtifactReceipt`, `SandboxArtifactView`, `SandboxCleanupReceipt` plus shared refusal/failure | `SandboxArtifactStaged`, `SandboxArtifactCleaned` |
| `outcome_calibration.py` | `agentic.outcome-calibration@1` | `AgenticOutcomeCalibration` | `calibrate_agentic_outcomes(request)` | `CALIBRATE_FORECAST`, `CALIBRATE_RECOMMENDATION`, `INSPECT` | `ForecastCalibrationResult`, `RecommendationCalibrationResult`, `OutcomeCalibrationView` plus shared refusal/failure | `OutcomeCalibrationCompleted`, `AgenticChangeCandidateCreated` |

### 5.2 Shared Agentic records

Shared records are strict, frozen, JSON-safe public models under `app/contracts/agentic/common.py` or the smallest semantic owner module. They include:

- `AgenticTaskIdentity`, `AgenticRunIdentity`, `AgenticPrincipalRef`, `AgenticScope`;
- `AgenticDeadline`, `AgenticBudget`, `AgenticBudgetUsage`;
- `AgenticProvenance`, `AgenticContentReference`, `AgenticEvidenceReference`;
- `AgenticRefusal`, `AgenticFailure`, `AgenticWarning`;
- `RoleManifest`, `PromptArtifactReference`, `ModelProfileReference`;
- `WorkflowCheckpoint`, `WorkflowTerminalReason`;
- `UncertaintyBreakdown`, `ReliabilityAssessment`.

A public cross-boundary record always carries exact schema identity/version, stable IDs, aware UTC time, correlation lineage, bounded fields, and canonical digest where integrity matters. Model output never supplies deterministic execution fields.

### 5.3 Capability-specific record inventory

#### `agentic.mandate@1` — Mandate Enforcement

- `FirmMandate`, `MandateVersion`, `MandateSignature`, `MandateValidityWindow`;
- `ValidateMandateRequest`, `CheckMandateScopeRequest`, `InspectMandateRequest`;
- `MandateAccepted`, `MandateScopeDecision`, `MandateView`.

#### `agentic.operations@1` — Operations, Incidents, and Replay Validation

- `OperationRecordRequest`, `InspectAgenticTraceRequest`, `ReportAgenticIncidentRequest`, `ValidateAgenticReplayRequest`, `InspectAgenticReadinessRequest`, `ExportAgenticOperationsRequest`;
- `AgenticOperationSpan`, `AgenticRunTrace`, `IncidentRecord`, `ReplayValidation`, `AgenticReadinessView`, `OperationsExport`;
- `AgenticIncidentKind`, `AgenticContainmentAction`, `AgenticReadinessState`.

#### `agentic.roles@1` — Role Contribution Registry

- `RegisterRoleContributionRequest`, `UnregisterRoleContributionRequest`, `ResolveRoleRequest`, `ListRolesRequest`, `SetRoleEligibilityReferenceRequest`;
- `RoleRegistrationReceipt`, `RoleRemovalReceipt`, `RoleResolution`, `RoleList`, `RoleEligibilityReferenceReceipt`;
- `RoleContribution`, `RoleCapability`, `RoleConflictClass`, `RoleEvaluationReference`.

#### `agentic.tool-governance@1` — Tool Governance and Human Actions

- `RegisterAgenticToolRequest`, `RequestCapabilityLease`, `AuthorizeToolInvocationRequest`, `FilterToolResultRequest`, `RevokeCapabilityLeaseRequest`;
- `RequestHumanAction`, `DecideHumanAction`;
- `ToolDescriptor`, `CapabilityLease`, `ToolAuthorizationDecision`, `FilteredToolResult`, `LeaseRevocationReceipt`;
- `HumanActionRequest`, `HumanActionDecision`, `HumanActionKind`, `HumanDecisionKind`.

`HumanActionKind` contains at least `CLARIFY_OBJECTIVE`, `AMEND_RESEARCH_SCOPE`, `APPROVE_TOOL_CALL`, `APPROVE_COMPUTE_BUDGET`, `APPROVE_HOLDOUT_USE`, `APPROVE_STAGED_ARTIFACT`, `APPROVE_RECEIVER_HANDOFF`, `REJECT`, and `CANCEL`.

#### `agentic.model-inference@1` — Provider-Neutral Model Invocation

- `ModelProfile`, `ModelInvocationRequest`, `ModelInvocationInput`, `ModelInvocationConstraints`;
- `ModelInvocationSuccess`, `ModelInvocationRefusal`, `ModelUsage`, `ModelObservedCost`, `ModelSubstitutionEvidence`.

#### `agentic.workflows@1` — Durable Workflow Orchestration

- `SubmitAgenticWorkflowRequest`, `ResumeAgenticWorkflowRequest`, `CancelAgenticWorkflowRequest`, `ExpireAgenticWorkflowRequest`, `InspectAgenticWorkflowRequest`, `DrainAgenticWorkflowsRequest`;
- `WorkflowDefinition`, `WorkflowNode`, `WorkflowTransition`, `WorkflowRun`, `WorkflowAccepted`, `WorkflowCancellationReceipt`, `WorkflowExpiryReceipt`, `WorkflowDrainReceipt`.

#### `agentic.context@1` — Point-in-Time Context Assembly

- `AssembleAgenticContextRequest`, `InspectContextExclusionsRequest`;
- `AgenticContextSource`, `AgenticContextItem`, `AgenticContextBundle`, `ContextExclusion`, `ContextExclusionReport`;
- `ContextTrustClass`, `InjectionAssessment`, `LicensingAssessment`, `FreshnessAssessment`.

#### `agentic.memory@1` — Governed Memory

- `SubmitMemoryCandidateRequest`, `PromoteMemoryRequest`, `RetrieveMemoryRequest`, `SupersedeMemoryRequest`, `PurgeMemoryRequest`, `ExportMemoryRequest`;
- `MemoryCandidate`, `MemoryRecord`, `MemoryPromotionDecision`, `MemoryQueryResult`, `MemorySupersessionReceipt`, `MemoryPurgeReceipt`, `MemoryExport`;
- `MemoryClass` values: `WORKFLOW`, `WORKING`, `EPISODIC`, `VALIDATED_SEMANTIC`, `OPERATIONAL_AUDIT`.

#### `agentic.profile-evaluation@1` — Profile and Topology Evaluation

- `EvaluateProfileRequest`, `InspectProfileEligibilityRequest`, `RevokeProfileEligibilityRequest`, `CompareProfileBaselineRequest`;
- `EvaluationSetReference`, `ProfileEvaluationReport`, `EligibilityDecision`, `EligibilityRevocationReceipt`, `BaselineComparison`, `CouncilAblationResult`;
- evaluated subjects: role, prompt, model, tool, workflow, and topology profiles.

#### `agentic.operator-assistance@1` — Website Chat Bot and Specialist Delegation

- `AssistOperatorRequest`, `SummarizeSpecialistResultRequest`;
- `OperatorConversationRef`, `OperatorTurn`, `WorkspaceContextSnapshot`, `AssistantContextContribution`;
- `SpecialistRouteProposal`, `SpecialistRouteDecision`, `SpecialistInvocationRef`, `SpecialistResultReference`;
- `OperatorAnswer`, `OperatorSpecialistAnswer`, `OperatorConversationSummary`.

`WorkspaceContextSnapshot` includes bounded page/route identity, focused widget, selected public entity references, filters, date/session/timeframe selections, allowed visible error/status codes, contribution versions, user permissions, redaction metadata, and observed time. It carries no raw DOM, credential, private provider object, unrestricted screenshot, or arbitrary executable content.

#### `agentic.claims@1` — Claim-and-Evidence Graph

- `CreateClaimGraphRequest`, `AppendClaimRequest`, `RelateClaimsRequest`, `TransitionClaimStatusRequest`, `AssessClaimReliabilityRequest`, `InspectClaimGraphRequest`;
- `ClaimGraph`, `Claim`, `ClaimRelation`, `ClaimReceipt`, `ClaimRelationReceipt`, `ClaimStatusReceipt`, `ClaimReliabilityAssessment`, `ClaimGraphView`;
- claim types: `OBSERVED_FACT`, `DETERMINISTIC_DERIVATION`, `MODEL_INFERENCE`, `FORECAST`, `RECOMMENDATION`;
- claim statuses: `SUPPORTED`, `CONTESTED`, `REFUTED`, `UNKNOWN`, `EXPIRED`;
- uncertainty: evidence, statistical, epistemic, operational, and calibrated-profile reliability.

#### `agentic.deliberation@1` — Independent Challenge and Deliberation

- `StartDeliberationRequest`, `ContinueDeliberationRequest`, `CancelDeliberationRequest`, `InspectDeliberationRequest`;
- `DeliberationPlan`, `IndependentAssessment`, `Challenge`, `Rebuttal`, `DissentRecord`, `IndependenceCorrelation`, `DeliberationRecord`, `DeliberationView`.

#### `agentic.synthesis@1` — Research Synthesis

- `SynthesizeResearchRequest`;
- `ResearchSynthesis`, `ResearchInsufficientEvidence`, `SynthesisClaimDisposition`, `SynthesisDissentReference`.

#### `agentic.research-search@1` — Research Campaign and Search Governance

- `RegisterResearchCampaignRequest`, `RegisterHypothesisFamilyRequest`, `RegisterResearchVariantRequest`, `RecordResearchAttemptRequest`, `ReserveHoldoutRequest`, `CloseResearchCampaignRequest`, `InspectResearchSearchRequest`;
- `ResearchCampaign`, `HypothesisFamily`, `DatasetFamily`, `ResearchVariant`, `ResearchAttempt`, `HoldoutReservation`, `SearchBudget`, `ResearchSearchView`;
- stable identities: `research_campaign_id`, `hypothesis_family_id`, `dataset_family_id`, `holdout_id`, `search_budget_id`.

#### `agentic.research-design@1` — Falsifiable Research Design

- `DesignHypothesisRequest`, `DesignExperimentRequest`, `DesignSearchRequest`;
- `HypothesisCandidate`, `ExperimentRequestCandidate`, `SearchRequestCandidate`;
- each candidate carries the receiver contract/version it targets and the registered campaign/family/search identities.

#### `agentic.strategy-specs@1` — JSON Strategy and Indicator DSL Composition

- `ComposeStrategySpecRequest`, `ValidateStrategySpecHandoffRequest`;
- `StrategySpecCandidate`, `StrategySpecHandoffReceipt`, `UnsupportedExpressionReport`;
- candidate records carry the target Strategy/Indicators schema capability and contain no compiled runtime object.

#### `agentic.portfolio-advisory@1` — Portfolio and Risk Advisory

- `AdvisePortfolioRequest`;
- `PortfolioAdvisory`, `PortfolioAdvisoryInsufficientEvidence`, `AdvisoryRisk`, `AdvisoryQuestion`, `AdvisoryExpiry`.

#### `agentic.strategy-proposals@1` — Strategy Proposal Composition and Handoff

- `ComposeStrategyProposalRequest`, `SubmitStrategyProposalRequest`;
- `StrategyProposalCandidate`, `StrategyProposalReceipt`;
- proposal candidates carry no broker-native field, order type, quantity, lot size, notional, price, or risk approval.

#### `agentic.sandbox-artifacts@1` — Sandboxed Source Artifact Fallback

- `AuthorSandboxArtifactRequest`, `InspectSandboxArtifactRequest`, `CleanupSandboxArtifactRequest`;
- `SandboxLeaseAttestation`, `SandboxArtifactManifest`, `SandboxArtifactReceipt`, `SandboxArtifactView`, `SandboxCleanupReceipt`.

#### `agentic.outcome-calibration@1` — Post-Horizon Outcome Calibration

- `CalibrateForecastRequest`, `CalibrateRecommendationRequest`, `InspectOutcomeCalibrationRequest`;
- `ScoreableForecast`, `MaturedOutcomeReference`, `ForecastCalibrationResult`, `RecommendationCalibrationResult`, `OutcomeCalibrationView`, `AgenticChangeCandidate`.

### 5.4 Consumed interface context contracts

D-IFACE owns the transport request and UI owns contribution capture, but Agentic owns the semantic records above. The interface companion feature shall provide authenticated operations equivalent to:

```text
SubmitChatTurn
CancelChatTurn
InspectChatConversation
AcknowledgeSpecialistRoute
StreamChatEvents
```

The UI companion feature shall expose one removable Chat Bot widget and a typed contribution registry. A widget contributes only its declared public context schema and exact disposer. Removing a widget removes its contribution from subsequent context snapshots.

### 5.5 Receiver-owned contracts

Agentic does not define substitutes for these semantics. Exact names are finalized in the receiver's authoritative registry before implementation.

| Receiver owner | Agentic use |
|---|---|
| Workspace/System | Opaque principal, secret, policy, clock, and runtime-profile references; Agentic does not resolve credentials in contracts. |
| UI/D-IFACE | Authenticated chat transport, conversation streaming, typed widget context contribution capture, navigation suggestion presentation. |
| Catalogue | Instrument/venue/session identity and applicability. |
| Data | Canonical point-in-time market, account, document, availability, quality, lineage, persistence-execution, and retention operations. |
| Indicators | Exact indicator schema/version, deterministic outputs, validation, and DSL schema ownership. |
| Analytics | Versioned metrics, performance/adherence evidence, formulas, uncertainty inputs, and realized outcomes. |
| Research | Canonical source-evidence, hypothesis/protocol validation where applicable, regime evidence, and research outcome truth. |
| Simulation | Simulation request/result/run/journal/artifact-manifest truth. |
| Optimization | Search request/result/trial/robustness/overfit truth. |
| Strategy | JSON strategy DSL schema, validation, compilation, proposal intake, registration, lifecycle, and decision truth. |
| Portfolio | Allocation/state/review request and portfolio decision truth. |
| Risk | Risk evidence, allocation/trade risk decisions, mandate barriers, and kill-switch truth. |
| Trading | Governed trade-intent/action/session/order/fill truth. Agentic has no mutation capability. |
| Brokers | No direct Agentic dependency. |

---

## 6. Workflow Registry

| Status | Workflow ID | Workflow | Input | Required path | Output |
|---|---|---|---|---|---|
| Missing | `WF-AGT-CHAT_CONTEXT` | Contextual Chat Bot Answer | Authenticated chat turn plus fresh `WorkspaceContextSnapshot`. | mandate → operator assistance → context → eligible model → streamed/final answer | `OperatorAnswer` or typed refusal/failure. |
| Missing | `WF-AGT-CHAT_SPECIALIST` | Chat Bot Specialist Delegation | Contextual or explicit specialist question. | Chat Bot proposes → deterministic route verification → workflow/specialist → result returns → Chat Bot presents | `OperatorSpecialistAnswer` in the same conversation. |
| Missing | `WF-AGT-REVIEW_EVIDENCE` | Deterministic Evidence Review | Completed versioned evidence from an owning domain. | mandate → workflow → context → one evidence analyst → claims → synthesis | Cited interpretation or refusal. |
| Missing | `WF-AGT-RESEARCH` | Adaptive Research and Challenge | Authenticated bounded research objective. | deterministic baseline → specialist(s) → claim graph → challenger when required → synthesis | `ResearchSynthesis`, preserving dissent or insufficient evidence. |
| Missing | `WF-AGT-DESIGN_EXPERIMENT` | Hypothesis to Experiment Candidate | Supported claim graph and campaign identity. | search governance → research design → receiver validation | Receiver-owned experiment request candidate or refusal. |
| Missing | `WF-AGT-DESIGN_SEARCH` | Bounded Search Candidate | Validated experiment identity and search budget. | research-search governance → bounded search designer → Optimization-owned validation | Search request candidate or refusal. |
| Missing | `WF-AGT-COMPOSE_DSL` | Strategy DSL Candidate | Approved hypothesis and exact DSL schema capability. | artifact planner → Strategy DSL Author → receiver validation | `StrategySpecCandidate` and receiver receipt. |
| Missing | `WF-AGT-SANDBOX_FALLBACK` | Sandboxed Code Artifact | Authenticated code specification plus sandbox lease. | artifact planner → sandbox code author → sandbox/testing/static checks → staging | Staged artifact receipt; never runtime import. |
| Missing | `WF-AGT-PORTFOLIO_ADVISORY` | Portfolio and Risk Advisory | Current receiver-owned evidence and allowed scope. | context → relevant analysis → risk/compliance challenge as required → advisory synthesis | Expiring non-binding advisory or insufficient evidence. |
| Missing | `WF-AGT-STRATEGY_PROPOSAL` | Strategy Proposal Handoff | Supported thesis and Strategy intake capability. | proposal synthesis → exact receiver request → Strategy validation | Receiver receipt, rejection, or expiry; never order/fill. |
| Missing | `WF-AGT-CALIBRATE` | Outcome Calibration | Matured forecast/recommendation and realized outcome reference. | validate horizon/outcome → compute deterministic calibration/value → compare baselines → candidate change | Calibration record and optional governed change candidate. |
| Missing | `WF-AGT-INCIDENT` | Incident, Containment, and Replay Validation | Policy, injection, schema, budget, provider, workflow, tool, or sandbox incident. | operations classify → revoke/cancel/quarantine → preserve evidence → validate replay references | Contained incident and safe recovery/terminal result. |

### 6.1 Chat Bot routing examples

| Current context and question | Route |
|---|---|
| “What does this widget show?” | Chat Bot direct answer from safe contribution metadata. |
| “Why did this backtest lose?” | Analytics Evidence Reviewer through an evidence-review workflow. |
| “Is the sample statistically meaningful?” | Quantitative Analyst. |
| “What does this divergence mean?” | Technical and Market-Structure Analyst. |
| “Which recent events may explain this move?” | Sentiment Analyst using point-in-time evidence. |
| “Could this contain look-ahead bias?” | Leakage Challenger. |
| “Is the result robust across regimes?” | Robustness Challenger. |
| “Turn this into a falsifiable hypothesis.” | Hypothesis Designer. |
| “Create a bounded backtest protocol.” | Experiment Designer. |
| “Build this as the JSON strategy DSL.” | Strategy DSL Author. |
| “Assess this portfolio concentration.” | Portfolio Advisory Synthesizer with Risk Challenger when required. |
| “Investigate this from several perspectives.” | Research Planner creates an adaptive bounded workflow. |

### 6.2 Common workflow guarantees

Every workflow:

1. verifies the mandate, principal, runtime profile, feature readiness, capability graph, budget, deadline, and idempotency before side effects;
2. persists its initial checkpoint before executing asynchronous work;
3. uses deterministic routing and model-non-overridable limits;
4. authorizes tools at every invocation/retry and filters results before model access;
5. records prompt/model/tool/data/policy/configuration lineage;
6. supports cancellation, expiration, bounded retry, backpressure, and crash-safe resume;
7. returns explicit `ok`, `refused`, `failed`, `cancelled`, or `expired` terminal semantics;
8. never resumes a terminal run under the same run identity;
9. preserves failures, dissent, null results, and partial coverage;
10. applies exact teardown, lease revocation, and retained-state policy when a capability is removed.

---

## 7. Persisted State Ownership

| Feature | Namespace | Core records | Retention | Correction/deletion rule |
|---|---|---|---|---|
| `OPERATE_RUNS` | `agentic.operations` | spans, traces, model/tool/handoff/policy/state evidence, incidents, replay validations, readiness and cost observations | RETAIN | Append immutable operational facts; redact before persistence; correction appends. |
| `GOVERN_TOOL_CALLS` | `agentic.tool_governance` | tool registrations, lease issuance/revocation/use, human action requests/decisions, nonces | RETAIN | Lease/use/action facts append; expiry/revocation append; secrets never persist. |
| `RUN_WORKFLOWS` | `agentic.workflows` | task/run identity, workflow/version, state, checkpoints, revisions, waits, terminal reason, budgets | RETAIN | Expected-version guarded transitions; checkpoints append; terminal runs never reopen. |
| `MANAGE_MEMORY` | `agentic.memory` | workflow/working/episodic/validated-semantic/operational-audit memory records and promotion evidence | RETAIN | Working records TTL/purge; other corrections append via supersession; no silent overwrite. |
| `EVALUATE_PROFILES` | `agentic.profile_evaluation` | evaluation definitions/results, grader/rubric lineage, baseline/ablation results, eligibility and revocation decisions | RETAIN | Evaluation and eligibility decisions append. No self-promotion. |
| `ASSIST_OPERATOR` | `agentic.operator_conversations` | session/task conversation state, turn references, current specialist handoff state, summary references | DELETE | Session/task scoped; TTL or explicit deletion; long-term material requires governed memory promotion. |
| `MANAGE_CLAIMS` | `agentic.claims` | graphs, claims, evidence refs, relations, statuses, uncertainty, falsifiers, versions | RETAIN | Facts/relations append; status transitions append; correction supersedes; expiry is explicit. |
| `DELIBERATE_RESEARCH` | `agentic.deliberation` | plans, independent assessments, challenges, rebuttals, dissent, correlation, stop reason | RETAIN | Records append; dissent cannot be deleted from a final record. |
| `GOVERN_RESEARCH_SEARCH` | `agentic.research_search` | campaigns, families, datasets, variants, attempts/failures, budgets, holdout reservations/receipts, amendments | RETAIN | All attempts/failures append; reservations cannot be reset by renaming/re-hashing. |
| `AUTHOR_SANDBOX_ARTIFACTS` | `agentic.sandbox_artifacts` | staging manifests, file hashes, tests, SBOM/dependencies, provenance, search history, cleanup receipts | DELETE | Ephemeral/staging only; content-addressed; cleanup according to lease/policy; production artifacts never owned. |
| `CALIBRATE_OUTCOMES` | `agentic.outcome_calibration` | forecasts, matured outcomes, scores, baseline comparisons, costs, regimes, change candidates | RETAIN | Calibration appends per fixed horizon/outcome; corrections reference prior record. |

All namespaces are declared with positive schema versions and explicit retention. Each stateful feature owns its migrations and adapter within its package and reaches database execution through the approved Data persistence capability. No `app/services/agentic/persistence/` package exists. In-memory stores are controlled tests only.

### State rules

- External receiver facts remain referenced by immutable owner IDs/digests rather than copied as alternate truth.
- Operational and memory data is redacted before persistence.
- Decimal cost/financial values never use binary floating storage.
- Requests, correlations, causation, workflow identity, schema identity, and aware UTC times are retained where applicable.
- Every irreversible or durable operation defines idempotency, reconciliation, audit, recovery, and deletion behavior.
- Removing a feature does not automatically delete retained state; deletion follows its declared state/retention contract.

---

## 8. Feature Specifications

### 8.1 `FEAT-AGT-ENFORCE_MANDATE` — Mandate Enforcement

**Folder:** `app/services/agentic/enforce_mandate/`  
**Provides:** `agentic.mandate@1`  
**Requires:** approved System/Workspace clock, principal, runtime-profile, and signed-mandate-source capabilities (exact keys finalized against owner registries)  
**Optional:** `agentic.operations@1` for audit publication  
**Conflicts:** none  
**State:** none  
**Primary module:** `mandate_enforcement.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
mandate_enforcement.py
```

**Configuration keys**

```text
accepted_mandate_schema_versions
maximum_clock_skew_seconds
require_signature_verification
fail_on_unknown_feature_or_role
```

**Functional requirements**

- `FR-AGT-MANDATE-001`: validate schema, signature, integrity digest, issuance, validity window, principal/deployment identity, runtime profile, and environment before accepting the mandate.
- `FR-AGT-MANDATE-002`: answer exact feature, role, asset, venue, account, environment, operation, budget, approval, and prohibited-authority scope queries.
- `FR-AGT-MANDATE-003`: treat absence, expiry, unverifiable signature, digest mismatch, unsupported version, unknown authority, or widened caller input as deterministic refusal.
- `FR-AGT-MANDATE-004`: a title or enabled feature never grants an undeclared tool, approval, risk, lifecycle, deployment, or execution capability.

**Effects and teardown**

Read-only mandate acquisition is scope-managed. Removing the feature refuses new Agentic work, disposes subscriptions/caches exactly, and preserves no private mutable state.

**Acceptance evidence**

Contract/config unit tests, signature/integrity/expiry/scope negative tests, mount/config/replacement/removal tests, startup-without-mandate fail-closed test, executable usage.

---

### 8.2 `FEAT-AGT-OPERATE_RUNS` — Operations, Incidents, and Replay Validation

**Folder:** `app/services/agentic/operate_runs/`  
**Provides:** `agentic.operations@1`  
**Requires:** Data persistence/audit execution, approved clock/ID/redaction capabilities  
**Optional:** event publication  
**Conflicts:** none  
**State:** `agentic.operations`, schema v1, RETAIN  
**Primary module:** `run_operations.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
run_operations.py
incident_policy.py
replay_validation.py
migration.py
storage.py
```

**Configuration keys**

```text
trace_retention_days
incident_retention_days
maximum_trace_spans
maximum_export_records
mandatory_audit
replay_allowed_profiles
```

**Functional requirements**

- `FR-AGT-OPS-001`: record correlated redacted model, tool, workflow, handoff, policy, human-action, state, cost, failure, and teardown evidence using bounded schemas.
- `FR-AGT-OPS-002`: assemble deterministic traces and readiness/cost diagnostics without exposing secrets, unrestricted prompts, hidden reasoning, or provider internals.
- `FR-AGT-OPS-003`: classify injection, poisoning, permission, schema, drift, cost, runaway, provider, workflow, sandbox, and receiver incidents using a deterministic containment table.
- `FR-AGT-OPS-004`: revoke leases, stop/cancel/quarantine affected work, preserve checkpoints/evidence, and emit a typed incident record; a model cannot reduce containment.
- `FR-AGT-OPS-005`: replay validation verifies immutable inputs and an isolated zero-side-effect profile; it does not repeat external side effects.

**Effects and teardown**

All tasks use `context.spawn`; persistence and event subscriptions are scope-managed. Teardown stops intake, drains writes, cancels tasks, unsubscribes, closes adapters, and retains committed operational evidence. Mandatory-audit dependents become unready if removal prevents safe recording.

**Acceptance evidence**

Redaction, trace completeness, cost, incident containment, replay-side-effect, persistence/restart, callback/task cleanup, mandatory-audit degradation, physical removal, and usage tests.

---

### 8.3 `FEAT-AGT-REGISTER_ROLES` — Role Contribution Registry

**Folder:** `app/services/agentic/register_roles/`  
**Provides:** `agentic.roles@1`  
**Requires:** `agentic.mandate@1`, approved digest/schema capabilities  
**Optional:** `agentic.operations@1`, event publication  
**Conflicts:** none  
**State:** none  
**Primary module:** `role_registry.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
role_registry.py
prompt_integrity.py
```

**Configuration keys**

```text
accepted_role_schema_versions
maximum_roles
maximum_roles_per_feature
allow_runtime_contributions
require_evaluation_reference
```

**Functional requirements**

- `FR-AGT-ROLE-001`: validate stable role/version, owning feature, capability set, task/asset support, prompt and manifest digests, model policy, tool IDs, schemas, conflicts, evaluation reference, and refusal conditions.
- `FR-AGT-ROLE-002`: reject duplicate identity/version, unknown feature, wildcard scope, forbidden authority class, unpinned prompt, missing eligibility evidence, or hash mismatch.
- `FR-AGT-ROLE-003`: registration and removal return exact receipts/disposers; broad name scanning is prohibited.
- `FR-AGT-ROLE-004`: role registration creates availability only; the mandate, evaluator, workflow router, tool governance, and receiver domains still authorize use.

**Effects and teardown**

Role contributions are registered at mount and exact disposers are scope-owned. Removal unregisters exact contributions, emits readiness change, and leaves workflow/operational evidence intact.

**Acceptance evidence**

Manifest/prompt integrity, duplicate/forbidden/wildcard cases, contribution replacement/removal, exact-disposer, degraded readiness, no implementation-import, and usage tests.

---

### 8.4 `FEAT-AGT-GOVERN_TOOL_CALLS` — Tool Governance and Human Actions

**Folder:** `app/services/agentic/govern_tool_calls/`  
**Provides:** `agentic.tool-governance@1`  
**Requires:** `agentic.mandate@1`, `agentic.roles@1`, approved clock/principal/digest capabilities  
**Optional:** `agentic.operations@1`, Data persistence, event publication  
**Conflicts:** none  
**State:** `agentic.tool_governance`, schema v1, RETAIN  
**Primary module:** `tool_governance.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
tool_governance.py
capability_leases.py
human_actions.py
result_filtering.py
migration.py
storage.py
```

**Configuration keys**

```text
maximum_registered_tools
maximum_active_leases_per_run
maximum_lease_seconds
maximum_tool_result_bytes
human_action_timeout_seconds
allowed_read_side_effect_classes
```

**Functional requirements**

- `FR-AGT-TOOL-001`: tool descriptors bind stable name/version, owner/capability, exact request/result schemas, side-effect class, scope model, egress class, cost model, and approval policy.
- `FR-AGT-TOOL-002`: capability leases bind principal, role, workflow/run, tool/capability version, exact request hash, scope, environment, side-effect class, egress, call/cost ceilings, issue/expiry, nonce, policy version, and required approval.
- `FR-AGT-TOOL-003`: authorization is rechecked immediately before every invocation/retry/resume; denial never invokes the receiver.
- `FR-AGT-TOOL-004`: post-call filtering validates schema, response size, redaction, provenance, resource scope, injection status, and observed cost before model context.
- `FR-AGT-TOOL-005`: human actions are typed, exact-object-bound, expiring, signed/authenticated, single-use, and invalid after material object change.
- `FR-AGT-TOOL-006`: broker mutation, order, risk approval, kill-switch clear, mandate override, production deployment, credential, or unrestricted shell/network tools are structurally unregistrable.

**Effects and teardown**

Registrations, leases, human waits, persistence, and events are scope-owned. Teardown stops issuance, revokes leases, resolves pending waits as unavailable/cancelled, unregisters exact tools, drains durable records, and preserves retained evidence.

**Acceptance evidence**

Authorization matrix, forged/replayed/expired/mutated approval, call-without-lease, retry/resume reauthorization, denied-call-never-invoked, result-injection, egress, cost, forbidden-tool, persistence/restart, removal, and usage tests.

---

### 8.5 `FEAT-AGT-INVOKE_MODELS` — Provider-Neutral Model Invocation

**Folder:** `app/services/agentic/invoke_models/`  
**Provides:** `agentic.model-inference@1`  
**Requires:** `agentic.mandate@1`, `agentic.roles@1`, approved Workspace secret-reference resolution and clock capabilities  
**Optional:** `agentic.operations@1`, `agentic.tool-governance@1`, event publication  
**Conflicts:** explicit provider-feature conflicts only when two providers claim the same exclusive configured profile  
**State:** none  
**Primary module:** `model_invocation.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
model_invocation.py
profile_validation.py
provider_adapter.py
```

**Configuration keys**

```text
accepted_profile_schema_versions
maximum_input_bytes
maximum_output_bytes
maximum_tokens_per_call
maximum_call_cost
invocation_timeout_seconds
allow_evaluated_fallback
```

**Functional requirements**

- `FR-AGT-MODEL-001`: profiles pin provider, model identifier/version, schema mode, tools, privacy, region, retention, latency, token/cost ceilings, fallback list, and eligibility reference; floating aliases are refused.
- `FR-AGT-MODEL-002`: invoke one schema-bound provider-neutral request; provider credentials reach only the provider adapter and never a contract, log, event, prompt, or persisted record.
- `FR-AGT-MODEL-003`: observed provider/model identity, tokens, cost, latency, finish status, and schema outcome are measured and compared with the requested profile; silent substitution is refused.
- `FR-AGT-MODEL-004`: fallback is explicit and only to an independently eligible profile for the same schema, tools, privacy, regional, safety, cost, and workflow-risk class.
- `FR-AGT-MODEL-005`: provider/framework objects—including ADK objects—never cross capability or persistence boundaries.

**Effects and teardown**

Provider clients are acquired with scope-managed contexts; invocations use managed tasks. Removal stops intake, cancels/drains calls, closes clients, unregisters provider contributions, and publishes unready/replacement status. No fallback is invented.

**Acceptance evidence**

Floating/silent-substitution, profile/credential/redaction, schema/timeout/cost, explicit fallback, provider replacement, no-provider-import-on-public-load, task/client cleanup, hot replacement, physical removal, and usage tests.

---

### 8.6 `FEAT-AGT-RUN_WORKFLOWS` — Durable Workflow Orchestration

**Folder:** `app/services/agentic/run_workflows/`  
**Provides:** `agentic.workflows@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, Data persistence, approved clock/ID capabilities  
**Optional:** `agentic.model-inference@1`, `agentic.tool-governance@1`, `agentic.context@1`, event publication  
**Conflicts:** none  
**State:** `agentic.workflows`, schema v1, RETAIN  
**Primary module:** `workflow_runtime.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
workflow_runtime.py
workflow_graph.py
workflow_state.py
routing.py
migration.py
storage.py
roles/research_planner/role.json
roles/research_planner/prompt.md
roles/artifact_planner/role.json
roles/artifact_planner/prompt.md
```

**Configuration keys**

```text
maximum_active_runs
maximum_nodes_per_workflow
maximum_fanout
maximum_rounds
maximum_retries
maximum_queue_depth
default_deadline_seconds
drain_timeout_seconds
```

**Functional requirements**

- `FR-AGT-WF-001`: task submission is idempotent and persists workflow/version, principal, immutable inputs, budgets, deadline, idempotency key, and initial checkpoint before execution.
- `FR-AGT-WF-002`: graphs use bounded deterministic routing, fan-out, loops, retries, backpressure, human waits, cancellation, expiration, and drain; model output cannot widen them.
- `FR-AGT-WF-003`: state transitions use expected-version guards and terminal states `SUCCEEDED`, `REFUSED`, `FAILED`, `CANCELLED`, or `EXPIRED`; terminal identity never resumes.
- `FR-AGT-WF-004`: routing selects only mandate-enabled, registry-resolved, eligible, conflict-safe roles and capabilities with available evidence/budget; absence degrades or refuses according to workflow policy.
- `FR-AGT-WF-005`: use risk/value-adaptive escalation: deterministic baseline, then one specialist, challenger when material, and council only for unresolved high-value work.
- `FR-AGT-WF-006`: Research Planner and Artifact Planner are bounded role contributions; they propose graphs inside deterministic templates and have no approval or receiver authority.

**Effects and teardown**

All child work uses managed tasks and scope-owned subscriptions/resources. Teardown stops intake, marks/drains/cancels active work by policy, revokes leases, preserves committed checkpoints/results, removes role contributions exactly, and closes storage.

**Acceptance evidence**

Idempotency/CAS, restart/resume, queue/backpressure, bounded loop/fanout/retry, cancellation/expiry/human-wait, adaptive escalation, role absence/conflict, planner authority-negative, drain/removal/replacement, and usage tests.

---

### 8.7 `FEAT-AGT-ASSEMBLE_CONTEXT` — Point-in-Time Context Assembly

**Folder:** `app/services/agentic/assemble_context/`  
**Provides:** `agentic.context@1`  
**Requires:** `agentic.mandate@1`, approved clock/redaction/digest capabilities, receiver evidence capability keys selected by configured workflow  
**Optional:** `agentic.memory@1`, `agentic.operations@1`  
**Conflicts:** none  
**State:** none  
**Primary module:** `context_assembly.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
context_assembly.py
eligibility.py
injection_filter.py
```

**Configuration keys**

```text
maximum_context_items
maximum_context_bytes
maximum_item_bytes
maximum_source_age_seconds
accepted_trust_classes
accepted_licence_classes
fail_on_required_source_exclusion
```

**Functional requirements**

- `FR-AGT-CTX-001`: each context request pins task, objective, asset/account/session scope, observation time, evidence cutoff, required/optional source classes, and output bound.
- `FR-AGT-CTX-002`: include items only after ordered availability, scope, licensing, trust, freshness, revision, deduplication, injection, redaction, and size checks.
- `FR-AGT-CTX-003`: trusted instructions and untrusted evidence occupy separate structural fields; retrieved text, page content, memory, and peer content never enter an instruction slot.
- `FR-AGT-CTX-004`: UI context provides orientation only; any material visible value must be refreshed through the owning capability before becoming an evidence claim.
- `FR-AGT-CTX-005`: excluded items and reasons are returned; missing required evidence refuses, while optional missing evidence produces explicit partial coverage.

**Effects and teardown**

Receiver reads and subscriptions are scope-managed; no durable state. Teardown cancels reads/subscriptions, clears bounded process-local caches, and publishes readiness change. No source truth is copied as a new authority.

**Acceptance evidence**

Point-in-time/lookahead, stale/revised/unlicensed/untrusted/duplicate/oversize, injection separation, UI-orientation refresh, required-vs-optional coverage, receiver absence, cancellation/removal, and usage tests.

---

### 8.8 `FEAT-AGT-MANAGE_MEMORY` — Governed Memory

**Folder:** `app/services/agentic/manage_memory/`  
**Provides:** `agentic.memory@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, Data persistence, approved clock/redaction/digest capabilities  
**Optional:** event publication  
**Conflicts:** none  
**State:** `agentic.memory`, schema v1, RETAIN  
**Primary module:** `memory_management.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
memory_management.py
promotion_policy.py
retrieval.py
migration.py
storage.py
```

**Configuration keys**

```text
maximum_record_bytes
maximum_retrieval_records
working_memory_ttl_seconds
conversation_summary_ttl_seconds
validated_memory_requires_approval
retention_days_by_class
allowed_sensitivity_classes
```

**Functional requirements**

- `FR-AGT-MEM-001`: memory records are separated into `WORKFLOW`, `WORKING`, `EPISODIC`, `VALIDATED_SEMANTIC`, and `OPERATIONAL_AUDIT` classes with scope and retention.
- `FR-AGT-MEM-002`: candidate promotion validates scope, evidence/provenance, sensitivity/redaction, freshness, injection, retention, deduplication, supersession, and required human action.
- `FR-AGT-MEM-003`: retrieval is bounded by task/principal/asset/account/time scope and revalidates expiry/freshness; memory alone never supports a material market or decision claim.
- `FR-AGT-MEM-004`: corrections append with `supersedes`; silent overwrite is forbidden. Working state expires/purges deterministically.
- `FR-AGT-MEM-005`: model reflection cannot change mandate, permissions, evaluation policy, thresholds, prompts, profile eligibility, or receiver state.

**Effects and teardown**

Storage/tasks/events are scope-managed. Removal stops new operations, cancels retrievals, drains writes, closes adapters, retains governed state by class, and deletes expired working state only through declared policy. Optional consumers can operate statelessly.

**Acceptance evidence**

Class separation, promotion, approval, redaction-before-persist, scoped retrieval, memory-not-evidence, injection, supersession, TTL/purge, restart, stateless degradation, removal, and usage tests.

---

### 8.9 `FEAT-AGT-EVALUATE_PROFILES` — Profile and Topology Evaluation

**Folder:** `app/services/agentic/evaluate_profiles/`  
**Provides:** `agentic.profile-evaluation@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, Data persistence, approved clock/digest capabilities  
**Optional:** `agentic.roles@1`, `agentic.model-inference@1`, `agentic.tool-governance@1`, event publication  
**Conflicts:** none  
**State:** `agentic.profile_evaluation`, schema v1, RETAIN  
**Primary module:** `profile_evaluation.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
profile_evaluation.py
eligibility.py
ablation.py
migration.py
storage.py
```

**Configuration keys**

```text
required_evaluation_set_versions
required_grader_versions
maximum_evaluation_cases
minimum_human_labels_for_model_grader
maximum_regression_rate
eligibility_expiry_seconds
```

**Functional requirements**

- `FR-AGT-EVAL-001`: every role, prompt, model, tool, workflow, and topology profile is evaluated against versioned contract, grounding, tool, safety, reasoning-utility, reproducibility, economic-value, and operational dimensions.
- `FR-AGT-EVAL-002`: sets include golden, ambiguous, refusal, point-in-time, injection/poisoning, authorization-forgery, provider regression, null/random-label, historical regime, stress, and out-of-distribution cases as applicable.
- `FR-AGT-EVAL-003`: deterministic graders govern schemas/calculations/permissions; human rubrics record agreement; model graders require calibration and never grade their own promotion alone.
- `FR-AGT-EVAL-004`: council ablation compares deterministic-only, best single-agent, full council, each-role-removed, and no-peer-visibility configurations.
- `FR-AGT-EVAL-005`: eligibility requires uncertainty-adjusted benefit exceeding latency, cost, and added failure surface; safety/reliability failure revokes eligibility. The evaluator records decisions but does not self-edit role manifests.

**Effects and teardown**

Evaluation runs use managed tasks/tools; storage/events are scope-managed. Removal cancels evaluations, freezes retained evidence, closes adapters, and blocks new/changed eligibility. It never invents passing evidence.

**Acceptance evidence**

Set completeness, grader calibration, self-grading negative, baseline/ablation arithmetic, eligibility/revocation/expiry, missing-evidence fail-closed, persistence/restart, role-registry integration, removal, and usage tests.

---

### 8.10 `FEAT-AGT-ASSIST_OPERATOR` — Website Chat Bot and Specialist Delegation

**Folder:** `app/services/agentic/assist_operator/`  
**Provides:** `agentic.operator-assistance@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.context@1`, `agentic.workflows@1`, approved clock/principal capabilities  
**Optional:** `agentic.memory@1`, `agentic.tool-governance@1`, D-IFACE event publication  
**Conflicts:** none  
**State:** `agentic.operator_conversations`, schema v1, DELETE  
**Primary module:** `operator_assistance.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
operator_assistance.py
context_validation.py
specialist_routing.py
conversation_state.py
migration.py
storage.py
roles/chat_bot/role.json
roles/chat_bot/prompt.md
```

**Configuration keys**

```text
maximum_message_bytes
maximum_context_contributions
maximum_context_bytes
maximum_conversation_turns
conversation_ttl_seconds
maximum_specialist_handoffs_per_turn
allow_navigation_suggestions
enable_response_streaming
```

**Functional requirements**

- `FR-AGT-CHAT-001`: the public and actual agent name is exactly **Chat Bot**. Canonical role ID: `chat_bot`. CEO/Firm Coordinator/Copilot aliases are not canonical.
- `FR-AGT-CHAT-002`: validate authenticated user, conversation/task scope, current page/route, active/focused widget, contribution versions, selected entity references, filters, timeframe/session/date selections, permissions, redactions, and observed time.
- `FR-AGT-CHAT-003`: reject raw DOM, credentials, private provider objects, unrestricted screenshots, arbitrary executable content, unknown contributions, oversized context, and stale or cross-user snapshots.
- `FR-AGT-CHAT-004`: answer directly only for safe UI explanation, navigation suggestion, definitions from public metadata, and summaries of already validated results; material domain questions require authoritative refresh or specialist delegation.
- `FR-AGT-CHAT-005`: Chat Bot proposes a specialist route; deterministic routing verifies enabled/eligible role, capability support, conflicts, required evidence, user permission, budget, limits, and readiness before invocation.
- `FR-AGT-CHAT-006`: specialist results return into the same conversation; Chat Bot preserves citations, provenance, uncertainty, refusal, failure, partial coverage, and dissent and names the specialist contribution.
- `FR-AGT-CHAT-007`: initial actions are exactly read context, answer, explain, delegate, summarize, and suggest navigation. Chat Bot cannot directly mutate widgets/settings, start runs, edit strategies, alter portfolios, approve risk, submit orders, or trade.
- `FR-AGT-CHAT-008`: page context refreshes every turn; conversation state is session/task-scoped, and long-term reuse requires governed memory promotion.

**Effects and teardown**

Chat turns, streaming, specialist tasks, context subscriptions, role contribution, and conversation store are scope-managed. Removal stops intake, cancels active turns/handoffs, unregisters Chat Bot exactly, unsubscribes, closes storage, and expires/deletes conversation state by policy. UI remains functional without Chat Bot.

**Acceptance evidence**

Context validation/staleness/cross-user/redaction/size, direct-vs-specialist routing, unsupported/disabled/conflicted specialist, same-conversation return, streaming cancellation/backpressure, action-authority negative tests, memory boundary, widget removal/stale-contribution test, feature removal and UI fallback, usage test.

---

### 8.11 `FEAT-AGT-MANAGE_CLAIMS` — Claim-and-Evidence Graph

**Folder:** `app/services/agentic/manage_claims/`  
**Provides:** `agentic.claims@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.context@1`, Data persistence, approved clock/digest capabilities  
**Optional:** `agentic.tool-governance@1`, event publication  
**Conflicts:** none  
**State:** `agentic.claims`, schema v1, RETAIN  
**Primary module:** `claim_graph.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
claim_graph.py
claim_validation.py
reliability.py
migration.py
storage.py
roles/analytics_evidence_reviewer/role.json
roles/analytics_evidence_reviewer/prompt.md
roles/fundamental_analyst/role.json
roles/fundamental_analyst/prompt.md
roles/sentiment_analyst/role.json
roles/sentiment_analyst/prompt.md
roles/technical_structure_analyst/role.json
roles/technical_structure_analyst/prompt.md
roles/quantitative_analyst/role.json
roles/quantitative_analyst/prompt.md
```

**Configuration keys**

```text
maximum_claims_per_graph
maximum_relations_per_graph
maximum_statement_bytes
maximum_evidence_refs_per_claim
claim_expiry_check_seconds
accepted_claim_schema_versions
```

**Functional requirements**

- `FR-AGT-CLAIM-001`: every material claim declares type, statement, scope, horizon/validity, evidence refs, availability, derivation/assumptions, confounders, falsifier, dependencies, contradictions, uncertainty, author profile, provenance, and status as applicable.
- `FR-AGT-CLAIM-002`: facts, deterministic derivations, model inferences, forecasts, and recommendations are structurally distinct; a model cannot promote its output to a measured fact.
- `FR-AGT-CLAIM-003`: relations are typed and acyclic where dependency semantics require it; contradiction, support, derivation, supersession, and invalidation remain queryable.
- `FR-AGT-CLAIM-004`: reliability separates evidence, statistical, epistemic, operational uncertainty, and calibrated profile reliability; displayed reliability is deterministic, not model self-confidence.
- `FR-AGT-CLAIM-005`: stale/revised/refuted evidence transitions affected claims and downstream dependencies explicitly; no final memo hides contested, unknown, refuted, or expired state.
- `FR-AGT-CLAIM-006`: evidence-analysis profiles interpret receiver evidence but never silently recalculate or replace owner outputs; missing/incompatible evidence refuses.

**Effects and teardown**

Model/tool/tasks, persistence, events, role contributions, and expiry task are scope-managed. Removal stops mutation/analysis, cancels work, unregisters roles, closes storage, retains graphs, and marks dependent capabilities unready.

**Acceptance evidence**

Claim type/status/prohibited promotion, graph relation/cycle, source expiry propagation, reliability computation, no-recomputation, analyst evidence applicability, persistence/restart, role removal/degradation, physical removal, and usage tests.

---

### 8.12 `FEAT-AGT-DELIBERATE_RESEARCH` — Independent Challenge and Deliberation

**Folder:** `app/services/agentic/deliberate_research/`  
**Provides:** `agentic.deliberation@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.workflows@1`, `agentic.context@1`, `agentic.claims@1`, Data persistence  
**Optional:** `agentic.tool-governance@1`, `agentic.profile-evaluation@1`, event publication  
**Conflicts:** none  
**State:** `agentic.deliberation`, schema v1, RETAIN  
**Primary module:** `research_deliberation.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
research_deliberation.py
independence.py
challenge_policy.py
migration.py
storage.py
roles/causality_challenger/role.json
roles/causality_challenger/prompt.md
roles/leakage_challenger/role.json
roles/leakage_challenger/prompt.md
roles/robustness_challenger/role.json
roles/robustness_challenger/prompt.md
roles/risk_challenger/role.json
roles/risk_challenger/prompt.md
roles/compliance_challenger/role.json
roles/compliance_challenger/prompt.md
roles/operations_security_challenger/role.json
roles/operations_security_challenger/prompt.md
```

**Configuration keys**

```text
maximum_participants
maximum_rounds
maximum_parallel_briefs
maximum_challenges_per_claim
minimum_independent_assessments
warn_same_model_family
require_distinct_model_family_for_high_risk
```

**Functional requirements**

- `FR-AGT-DELIB-001`: challengers first receive objective, evidence snapshot, and normalized claim IDs without proposer narrative; their independent assessment is committed before rebuttal context.
- `FR-AGT-DELIB-002`: record same provider/model/prompt/context/evidence/decoding correlations and warn or refuse when required independence is not achieved.
- `FR-AGT-DELIB-003`: challenge modes cover causality, leakage, robustness, risk, compliance, and operations/security, selected by deterministic task/risk policy rather than by role persuasion.
- `FR-AGT-DELIB-004`: preserve challenges, rebuttals, unresolved dissent, material conflict, budgets, rounds, participants, tool evidence, and terminal reason. Voting and agreement cannot authorize or size a position.
- `FR-AGT-DELIB-005`: stop on completion, insufficient evidence, material unresolved conflict, limits, deadline, budget, policy denial, incident, dependency removal, or cancellation; more discussion is not an automatic uncertainty remedy.

**Effects and teardown**

Tasks/model/tool calls, persistence, events, and role contributions are scope-managed. Removal stops new rounds, cancels/drains active deliberations, revokes leases, unregisters challenge profiles, persists terminal/degraded outcomes, closes storage, and retains dissent.

**Acceptance evidence**

Blind-first challenge, correlation warnings/distinct-family rule, challenge coverage, dissent/authority negative, bounds/stop conditions, cancellation/removal mid-round, persistence/restart, role removal/degraded low-risk path, and usage tests.

---

### 8.13 `FEAT-AGT-SYNTHESIZE_RESEARCH` — Research Synthesis

**Folder:** `app/services/agentic/synthesize_research/`  
**Provides:** `agentic.synthesis@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.context@1`, `agentic.claims@1`  
**Optional:** `agentic.deliberation@1`, `agentic.profile-evaluation@1`, event publication  
**Conflicts:** none  
**State:** none  
**Primary module:** `research_synthesis.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
research_synthesis.py
synthesis_validation.py
roles/research_synthesizer/role.json
roles/research_synthesizer/prompt.md
```

**Configuration keys**

```text
maximum_output_bytes
maximum_cited_claims
require_dissent_preservation
require_reliability_breakdown
allow_partial_coverage
```

**Functional requirements**

- `FR-AGT-SYN-001`: synthesis consumes canonical claim graphs and optional deliberation records; evidence references and statuses derive from supplied records rather than model invention.
- `FR-AGT-SYN-002`: output separates supported conclusion, contested/refuted/unknown/expired claims, uncertainty components, assumptions, invalidation, unanswered questions, partial coverage, and preserved dissent.
- `FR-AGT-SYN-003`: unresolved material dissent forces a contested or insufficient-evidence disposition; consensus cannot promote or authorize a proposal.
- `FR-AGT-SYN-004`: reject code, orders, fills, broker fields, risk approvals, authoritative size, kill-switch language, or uncited material claims.

**Effects and teardown**

Model/tasks/events and role contribution are scope-managed. Removal cancels synthesis, unregisters the role, and leaves source graphs/deliberation records accessible. There is no private durable state.

**Acceptance evidence**

Claim-binding/no invented refs, disposition/uncertainty/dissent, material-dissent outcome, authority/prohibited fields, partial coverage, missing role/model/context, cancellation/removal, and usage tests.

---

### 8.14 `FEAT-AGT-GOVERN_RESEARCH_SEARCH` — Research Campaign and Search Governance

**Folder:** `app/services/agentic/govern_research_search/`  
**Provides:** `agentic.research-search@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, Data persistence, approved clock/digest capabilities  
**Optional:** event publication, receiver dataset/holdout identity validation  
**Conflicts:** none  
**State:** `agentic.research_search`, schema v1, RETAIN  
**Primary module:** `research_search_governance.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
research_search_governance.py
near_duplicate_policy.py
holdout_policy.py
migration.py
storage.py
```

**Configuration keys**

```text
maximum_open_campaigns
maximum_variants_per_family
maximum_attempts_per_campaign
near_duplicate_threshold
maximum_holdout_reservations
require_failure_reason
require_multiple_testing_policy
```

**Functional requirements**

- `FR-AGT-SEARCH-001`: register immutable campaign, hypothesis-family, dataset-family, search-budget, and holdout identities before governed trials.
- `FR-AGT-SEARCH-002`: record every attempted variant, prompt/model/tool/profile lineage, parameters/features, amendment, completion/failure reason, and consumed budget; attempted equals completed plus failed.
- `FR-AGT-SEARCH-003`: classify near-duplicate hypotheses/specifications deterministically and charge them to the same family/campaign/holdout budget unless material independence is proven by policy.
- `FR-AGT-SEARCH-004`: holdout reservation/consumption binds campaign, hypothesis family, dataset family, holdout, protocol/request digest, principal, purpose, and expiry; renaming or rehashing cannot reset access.
- `FR-AGT-SEARCH-005`: multiple-testing, sequential-testing/alpha-spending, embargo/purge, economic-cost, null-result, and predeclared termination policies are recorded where applicable.
- `FR-AGT-SEARCH-006`: missing history, exhausted budget, conflicting reservation, undeclared amendment, or unverifiable family identity refuses before receiver execution.

**Effects and teardown**

Persistence/events and reservation-expiry task are scope-managed. Removal refuses new attempts/holdouts, cancels active reservations according to policy without freeing consumed budget, closes storage, and retains all history.

**Acceptance evidence**

Campaign/family/dataset identity, all-trial conservation, near-duplicate evasion, cross-spec holdout reuse, amendment/multiple-testing rules, concurrency/reservation/restart, exhausted budget, removal and retained scarcity, and usage tests.

---

### 8.15 `FEAT-AGT-DESIGN_RESEARCH` — Falsifiable Research Design

**Folder:** `app/services/agentic/design_research/`  
**Provides:** `agentic.research-design@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.context@1`, `agentic.claims@1`, `agentic.research-search@1`  
**Optional:** `agentic.deliberation@1`, `agentic.synthesis@1`, `agentic.tool-governance@1`, Research/Simulation/Optimization validation capability keys  
**Conflicts:** none  
**State:** none  
**Primary module:** `research_design.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
research_design.py
candidate_binding.py
roles/hypothesis_designer/role.json
roles/hypothesis_designer/prompt.md
roles/experiment_designer/role.json
roles/experiment_designer/prompt.md
roles/bounded_search_designer/role.json
roles/bounded_search_designer/prompt.md
```

**Configuration keys**

```text
maximum_hypotheses_per_request
maximum_candidate_bytes
require_receiver_schema_resolution
require_registered_campaign
allow_search_design
```

**Functional requirements**

- `FR-AGT-DESIGN-001`: hypothesis candidates bind supported claims, asset scope, horizon, mechanism, prerequisites, confounders, assumptions, rejection criterion, required data, leakage constraints, and campaign/family identity.
- `FR-AGT-DESIGN-002`: experiment candidates bind exact receiver contract/version, immutable inputs, splits, embargo, costs, seeds, baselines, metrics, stop rules, evidence classes, and falsification outcomes.
- `FR-AGT-DESIGN-003`: search candidates bind exact Optimization contract/version, declared parameter/feature space, objective, method, trial/search budget, early stop, robustness/stability/overfit requirements, and holdout policy.
- `FR-AGT-DESIGN-004`: candidates are proposals only; receiver owners validate and execute unchanged or return typed rejection. Agentic neither reconstructs receiver contracts nor alters results.
- `FR-AGT-DESIGN-005`: no candidate is created from unsupported/contested material without explicit contested status, absent rejection criterion, unregistered campaign/family, exhausted search budget, or unresolved required dissent.

**Effects and teardown**

Models/tools/tasks/events and role contributions are scope-managed. Removal cancels design work, unregisters the three roles, revokes leases, and leaves search history/receiver runs intact.

**Acceptance evidence**

Hypothesis completeness/falsifiability, exact receiver schema/binding, experiment/search completeness, unsupported/dissent/budget refusals, unchanged receiver request/results, role removal, dependency degradation, and usage tests.

---

### 8.16 `FEAT-AGT-COMPOSE_STRATEGY_SPECS` — JSON Strategy and Indicator DSL Composition

**Folder:** `app/services/agentic/compose_strategy_specs/`  
**Provides:** `agentic.strategy-specs@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.context@1`, approved Strategy/Indicators DSL schema/validation capability keys  
**Optional:** `agentic.tool-governance@1`, `agentic.claims@1`, `agentic.research-design@1`, event publication  
**Conflicts:** none  
**State:** none  
**Primary module:** `strategy_spec_composition.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
strategy_spec_composition.py
schema_binding.py
roles/strategy_dsl_author/role.json
roles/strategy_dsl_author/prompt.md
```

**Configuration keys**

```text
maximum_spec_bytes
accepted_dsl_major_versions
maximum_validation_attempts
require_hypothesis_reference
allow_indicator_spec_candidates
```

**Functional requirements**

- `FR-AGT-DSL-001`: compose only against an exact receiver-owned Strategy/Indicators DSL schema/version and approved hypothesis/claim references.
- `FR-AGT-DSL-002`: candidate contains declarative building blocks, parameters, inputs, signals, state, entries/exits, management, constraints, and metadata allowed by that schema; no compiled object, arbitrary source, broker command, or approval.
- `FR-AGT-DSL-003`: deterministic schema validation runs after model output; correction attempts are bounded and all failed candidates remain observable.
- `FR-AGT-DSL-004`: return unsupported-expression report when the DSL cannot represent the requirement; code fallback is not automatic and requires a new authenticated sandbox request.
- `FR-AGT-DSL-005`: Strategy/Indicators owns semantic validation, compilation, registration, versioning, lifecycle, and production use. Agentic receipt is never receiver acceptance unless the receiver says so.

**Effects and teardown**

Models/tools/tasks/events and role contribution are scope-managed. Removal cancels work, unregisters the role, and leaves receiver-owned artifacts intact. No private durable state.

**Acceptance evidence**

Exact schema/version, deterministic validation/correction bounds, unsupported-expression path, source/broker/approval prohibited fields, receiver rejection/acceptance truth, role removal, physical removal, and usage tests.

---

### 8.17 `FEAT-AGT-ADVISE_PORTFOLIO` — Portfolio and Risk Advisory

**Folder:** `app/services/agentic/advise_portfolio/`  
**Provides:** `agentic.portfolio-advisory@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.context@1`, current Portfolio/Risk/Analytics/account evidence capability keys  
**Optional:** `agentic.tool-governance@1`, `agentic.claims@1`, `agentic.deliberation@1`, event publication  
**Conflicts:** none  
**State:** none  
**Primary module:** `portfolio_advisory.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
portfolio_advisory.py
advisory_validation.py
roles/portfolio_advisory_synthesizer/role.json
roles/portfolio_advisory_synthesizer/prompt.md
```

**Configuration keys**

```text
maximum_advisory_bytes
maximum_evidence_age_seconds
maximum_advisory_lifetime_seconds
require_risk_challenge
require_compliance_challenge
```

**Functional requirements**

- `FR-AGT-ADV-001`: require current portfolio allocation, account, analytics, mandate, and authoritative Risk evidence for the requested scope; unreadable observation time is stale.
- `FR-AGT-ADV-002`: advice contains concerns, trade-offs, bounded allocation ranges/relative preferences where allowed, uncertainty, evidence, unanswered questions, challenge/dissent, and strict expiry.
- `FR-AGT-ADV-003`: advice contains no lot size, quantity, notional, order, price, execution instruction, risk approval, verdict-by-absence, or kill-switch action.
- `FR-AGT-ADV-004`: Risk/compliance challenge covers all configured kinds by set equality; missing required challenge refuses rather than implying consent.
- `FR-AGT-ADV-005`: Portfolio and Risk own any receiver request, validation, decision, or mutation. Stale, expired, incomplete, out-of-scope, or rejected advice never becomes authority.

**Effects and teardown**

Models/tools/tasks/events and role contribution are scope-managed. Removal cancels work, unregisters the role, and leaves Portfolio/Risk unchanged. Advice persists only through workflow/operations evidence and expires strictly.

**Acceptance evidence**

Freshness/scope/evidence, non-binding/prohibited fields, challenge set equality/dissent, strict expiry, receiver rejection/authority, role/dependency removal, and usage tests.

---

### 8.18 `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS` — Strategy Proposal Composition and Handoff

**Folder:** `app/services/agentic/compose_strategy_proposals/`  
**Provides:** `agentic.strategy-proposals@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.context@1`, Strategy proposal-intake capability  
**Optional:** `agentic.tool-governance@1`, `agentic.claims@1`, `agentic.synthesis@1`, `agentic.research-design@1`, event publication  
**Conflicts:** none  
**State:** none  
**Primary module:** `strategy_proposal_composition.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
strategy_proposal_composition.py
receiver_handoff.py
roles/strategy_proposal_synthesizer/role.json
roles/strategy_proposal_synthesizer/prompt.md
```

**Configuration keys**

```text
maximum_proposal_bytes
maximum_proposal_lifetime_seconds
require_research_synthesis
require_receiver_schema_resolution
maximum_handoff_attempts
```

**Functional requirements**

- `FR-AGT-PROP-001`: compose a proposal from supported thesis/synthesis carrying instrument/scope, intended direction/behavior, horizon, invalidation, evidence, uncertainty, assumptions, requested evaluation, and strict expiry.
- `FR-AGT-PROP-002`: the proposal type structurally lacks broker-native fields, order type, price, lot size, quantity, notional, risk approval, execution status, fill, or kill-switch action.
- `FR-AGT-PROP-003`: map to the exact Strategy-owned intake contract and submit unchanged through its capability; Agentic imports no Strategy implementation and receives no privileged validation path.
- `FR-AGT-PROP-004`: receipt reports receiver/status/request reference/rejection/expiry only; it is never interpreted as strategy acceptance, risk approval, order, or fill beyond receiver-declared semantics.
- `FR-AGT-PROP-005`: expired, stale, unsupported, out-of-scope, unresolved-required-dissent, or receiver-unavailable proposals refuse without alternate route.

**Effects and teardown**

Models/tasks/events and role contribution are scope-managed. Receiver calls are bounded/idempotent. Removal cancels handoffs, unregisters the role, and leaves receiver-owned requests/records unchanged.

**Acceptance evidence**

Proposal completeness/prohibited fields, exact receiver mapping and no implementation import, idempotency/retry, receipt truth, expiry/stale/dissent/unavailable refusal, mid-handoff removal, and usage tests.

---

### 8.19 `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS` — Sandboxed Source Artifact Fallback

**Folder:** `app/services/agentic/author_sandbox_artifacts/`  
**Provides:** `agentic.sandbox-artifacts@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.tool-governance@1`, approved sandbox-leasing and Workspace secret-isolation capabilities  
**Optional:** `agentic.workflows@1`, event publication  
**Conflicts:** none  
**State:** `agentic.sandbox_artifacts`, schema v1, DELETE  
**Primary module:** `sandbox_artifact_authoring.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
sandbox_artifact_authoring.py
path_security.py
artifact_manifest.py
migration.py
storage.py
roles/sandbox_code_author/role.json
roles/sandbox_code_author/prompt.md
```

**Configuration keys**

```text
maximum_files
maximum_file_bytes
maximum_total_bytes
maximum_cpu_seconds
maximum_memory_bytes
maximum_storage_bytes
sandbox_timeout_seconds
allowed_dependency_sources
require_network_denial
```

**Functional requirements**

- `FR-AGT-SBOX-001`: require authenticated exact code specification, reason the DSL is insufficient, human action where policy requires, and an attested lease binding ephemeral, credential-free, network-denied/allowlisted, resource-bounded, staging-only execution.
- `FR-AGT-SBOX-002`: validate every declared raw path before parsing and every resolved path after resolution; reject traversal, absolute/drive/UNC/device paths, reserved names, symlink escape, and writes outside staging.
- `FR-AGT-SBOX-003`: generated artifact records all files/digests, dependencies and sources, SBOM, tests/results, static analysis, provenance, prompt/model/tool lineage, complete search history, and specification digest.
- `FR-AGT-SBOX-004`: generated code is never imported, hot-loaded, registered, deployed, or executed in the production application directly; output is only staged for receiver/human review.
- `FR-AGT-SBOX-005`: sandbox absence, under-attested lease, unknown dependency source, failed checks, path risk, budget exhaustion, or cleanup failure refuses/contains the task and preserves audit evidence.

**Effects and teardown**

Sandbox/client/tasks/files/persistence/events and role contribution are scope-owned. Removal stops intake, revokes leases, cancels sandboxes, unregisters role, cleans ephemeral and eligible staging artifacts, closes storage, and preserves operational receipts. It cannot remove receiver-owned artifacts.

**Acceptance evidence**

Lease attestation, credential/network/resource isolation, raw/resolved/symlink path attacks, dependency/SBOM/search history, no import/hot-load/deploy, timeout/cancel/cleanup/partial failure, persistence, mid-generation removal, and usage tests.

---

### 8.20 `FEAT-AGT-CALIBRATE_OUTCOMES` — Post-Horizon Outcome Calibration

**Folder:** `app/services/agentic/calibrate_outcomes/`  
**Provides:** `agentic.outcome-calibration@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, Data persistence, approved clock/digest capabilities, receiver outcome/evaluation capabilities  
**Optional:** `agentic.profile-evaluation@1`, event publication  
**Conflicts:** none  
**State:** `agentic.outcome_calibration`, schema v1, RETAIN  
**Primary module:** `outcome_calibration.py`

**Files**

```text
README.md
__init__.py
manifest.py
config.py
feature.py
outcome_calibration.py
scoring.py
baseline_value.py
migration.py
storage.py
```

**Configuration keys**

```text
accepted_forecast_schema_versions
minimum_matured_outcomes
maximum_outcome_age_seconds
calibration_windows
required_baselines
change_candidate_thresholds
```

**Functional requirements**

- `FR-AGT-CAL-001`: a scoreable forecast declares target, probability/bounded distribution, horizon, observation rule, invalidation, expected regime, expected economic effect, and immutable provenance before the outcome.
- `FR-AGT-CAL-002`: after maturity, bind authoritative outcome, direction/magnitude error, invalidation timing, realized costs/slippage where applicable, regime, receiver rejection/amendment, and deterministic/single-agent baseline outcomes.
- `FR-AGT-CAL-003`: compute appropriate calibration/error, unsupported-claim, reversal, receiver-rejection, cost-adjusted value-of-information, latency, reliability, and incremental-utility measures deterministically.
- `FR-AGT-CAL-004`: raw P&L is not sufficient and cannot replace calibration, baseline, uncertainty, regime, and cost analysis.
- `FR-AGT-CAL-005`: learning emits a candidate role/prompt/model/workflow/topology change with evidence; it cannot modify production profiles, prompts, permissions, mandate, thresholds, or eligibility directly.

**Effects and teardown**

Receiver reads, scheduled calibration tasks, storage, and events are scope-managed. Removal stops scheduling/calculation, cancels tasks, closes adapters/storage, preserves committed calibration evidence, and prevents incomplete outcomes from being scored as neutral.

**Acceptance evidence**

Pre-outcome immutability, horizon maturity, receiver truth, probability/distribution scoring, P&L-only negative, baseline/value/cost, regime/invalidated/rejected cases, change-candidate no-self-modification, restart/removal, and usage tests.

---

## 9. Domain-Wide Configuration and Runtime Profiles

There is no root `_settings.py` or `_limits.py`. Each feature accepts only the keys listed in its section and manifest. Composition supplies validated configuration. Secrets remain opaque Workspace references and are resolved only inside the provider/sandbox adapter that requires them.

| Runtime profile | Agentic policy |
|---|---|
| `research` | Read-only evidence, research, simulation/optimization candidate requests, DSL/staging workflows according to mandate; no market mutation. |
| `simulation` | Same reasoning path using simulation-owned clock/evidence and receiver-owned simulated operations; no live mutation. |
| `demo` | Current evidence and advisory/proposal workflows may run, but deterministic receiver validation and demo authority remain mandatory. |
| `live` | Agentic remains proposal-only. No direct trading/broker mutation becomes available; receiver domains apply all live authorization and safety gates. |

A convenience domain enable flag may exist in composition, but each feature remains independently enabled/configured/discoverable. Removing one feature does not grant another feature permission to absorb its responsibility.

---

## 10. Non-Functional Requirements

| Status | Requirement | Responsibility | Verification |
|---|---|---|---|
| Missing | `NFR-AGT-SECURITY` | Least privilege, secret isolation, prompt/memory/tool injection resistance, signed/typed human actions, egress controls, sandboxing, and fail-closed behavior are release gates. | Adversarial security suite. |
| Missing | `NFR-AGT-RELIABILITY` | Durable state, idempotency, expected-version transitions, deadlines, bounded retry, backpressure, cancellation, recovery, and deterministic terminal states. | Failure/restart/concurrency suite. |
| Missing | `NFR-AGT-REPRODUCIBILITY` | Exact model, prompt, role, tool, data, policy, dependency, configuration, seed, workflow, and receiver lineage for every material result. | Lineage/replay validation. |
| Missing | `NFR-AGT-OBSERVABILITY` | Correlated traces, events, audit, metrics, cost, readiness, failure, and incident evidence without secrets or unrestricted hidden reasoning. | Trace/redaction/completeness tests. |
| Missing | `NFR-AGT-PERFORMANCE` | Each feature/workflow declares concurrency, latency, queue, context, output, model, tool, token, cost, compute, and storage bounds; overload applies backpressure. | Load/budget tests. |
| Missing | `NFR-AGT-DATA_GOVERNANCE` | Point-in-time availability, trust, licensing, revision, poisoning, retention, deletion, and source scope are enforced. | Governance/lookahead tests. |
| Missing | `NFR-AGT-MODEL_GOVERNANCE` | Provider/model/framework/profile changes are explicit, pinned, evaluated, reversible, and never silently substituted. | Provider replacement/upgrade tests. |
| Missing | `NFR-AGT-EVALUATION` | Safety, contracts, tools, grounding, reasoning utility, regression, ablation, null-data, outcome calibration, and economic value use versioned evidence. | Evaluation suite. |
| Missing | `NFR-AGT-COMPATIBILITY` | Public contracts are provider/framework-neutral and follow versioned major compatibility and explicit migration rules. | Contract compatibility/replacement tests. |
| Missing | `NFR-AGT-REMOVABILITY` | Every feature passes teardown, replacement, degraded-readiness, physical-removal, retained-state, no-stale-role/context/lease, and safety-equivalence tests. | Composition/removal suite. |
| Missing | `NFR-AGT-TEST_QUALITY` | Controlled clocks, providers, tools, persistence, network, randomness, and receiver doubles; no live provider dependency in normal tests. | Warning/duration/determinism audit. |
| Missing | `NFR-AGT-COVERAGE` | At least 80% implemented-code coverage; every feature has contract, configuration, lifecycle, failure, composition, removal, documentation, and executable usage evidence. | Coverage and pipeline checks. |

---

## 11. Cross-Domain and Interface Boundaries

### Chat Bot boundary

```text
UI widget contributions
    → D-IFACE authenticated chat operation/event stream
        → agentic.operator-assistance@1
            → deterministic route verification
                → agentic.workflows@1 / specialist capabilities
                    → receiver-owned evidence operations
```

- UI owns presentation and contribution capture; it imports no Agentic implementation.
- D-IFACE owns authentication, request envelopes, transport cancellation, streaming, rate limiting, and mapping.
- `ASSIST_OPERATOR` owns conversational semantics and same-conversation delegation.
- `ASSEMBLE_CONTEXT` validates the snapshot and refreshes material values through owner capabilities.
- Chat Bot suggests navigation only; UI decides whether/how to execute a future typed UI command.

### No direct Brokers edge

No Agentic manifest requires or optionally resolves a Brokers mutation or provider channel capability. Market/account evidence reaches Agentic only through the semantic owner chosen by the current architecture. Static and runtime checks reject broker SDK names, order/fill DTOs, credential fields, and forbidden capabilities in Agentic contracts/features.

### Framework/provider boundary

Google ADK or any later orchestration/model framework may be implemented as a replaceable provider adapter or plugin. HaruQuantAI contracts, workflow state, provenance, role manifests, tool leases, memory, claim graphs, and results remain canonical and framework-neutral.

---

## 12. Implementation Order

Documentation completion precedes production implementation. Production code follows the repository feature implementation pipeline separately for each focused feature.

| Phase | Features | Required exit |
|---:|---|---|
| 0 | Domain contract and companion-boundary reconciliation | All capability keys, receiver ownership, D-IFACE/UI companion features, Workspace/System references, and any new receiver specifications are ratified. |
| 1 | `ENFORCE_MANDATE` | Contract/config/lifecycle/removal and fail-closed startup evidence. |
| 2 | `OPERATE_RUNS` | Redacted retained operations/incident/replay capability and persistence evidence. |
| 3 | `REGISTER_ROLES` | Contribution registry, prompt/manifest integrity, exact disposal, removal evidence. |
| 4 | `GOVERN_TOOL_CALLS` | Invocation lease/human action/result-filtering and forbidden-tool evidence. |
| 5 | `INVOKE_MODELS` | Provider-neutral evaluated invocation with explicit replacement/fallback. |
| 6 | `RUN_WORKFLOWS` | Durable idempotent bounded workflow runtime and planner contributions. |
| 7 | `ASSEMBLE_CONTEXT` | Point-in-time/injection/licensing/UI-orientation context evidence. |
| 8 | `MANAGE_MEMORY` | Governed class separation, promotion, retrieval, retention, stateless degradation. |
| 9 | `EVALUATE_PROFILES` | Eligibility, regression, baseline/ablation, revocation evidence. |
| 10 | `ASSIST_OPERATOR` | Chat Bot context/direct-answer/specialist delegation, D-IFACE/UI integration, removal fallback. |
| 11 | `MANAGE_CLAIMS` | Claim graph, five analyst contributions, expiry/reliability and no-recomputation evidence. |
| 12 | `DELIBERATE_RESEARCH` | Six challengers, blind-first challenge, correlation/dissent/bounds evidence. |
| 13 | `SYNTHESIZE_RESEARCH` | Claim-bound research synthesis and insufficient-evidence behavior. |
| 14 | `GOVERN_RESEARCH_SEARCH` | Campaign/family/all-trial/holdout scarcity and evasion evidence. |
| 15 | `DESIGN_RESEARCH` | Three designer roles and exact receiver candidate bindings. |
| 16 | `COMPOSE_STRATEGY_SPECS` | JSON DSL-first composition and Strategy/Indicators receiver validation. |
| 17 | `ADVISE_PORTFOLIO` | Non-binding fresh portfolio/risk advisory and challenge evidence. |
| 18 | `COMPOSE_STRATEGY_PROPOSALS` | Strategy intake handoff and receipt-truth evidence. |
| 19 | `AUTHOR_SANDBOX_ARTIFACTS` | Only after a real sandbox provider and all isolation gates exist. |
| 20 | `CALIBRATE_OUTCOMES` | Matured outcome/baseline/value calibration and no-self-modification evidence. |
| 21 | Domain completion | All workflows/NFRs/removal scenarios, docs/registry/changelog/system architecture, coverage, usage and full quality gates pass. |

No feature may silently implement a missing receiver domain capability. Missing required receiver authority/specification is a blocker or an explicit specification-gap task, not permission to invent a local substitute.

---

## 13. Tests and Definition of Done

### Test locations

```text
tests/services/agentic/<feature>/
├── test_contract.py
├── test_config.py
├── test_feature.py
├── test_behavior.py
├── test_failures.py
└── optional focused tests

tests/contracts/agentic/
tests/composition/
tests/architecture/
tests/removal/
```

### Quality commands

```bash
uv run ruff check app/contracts/agentic app/services/agentic tests/services/agentic tests/contracts/agentic
uv run ruff format --check app/contracts/agentic app/services/agentic tests/services/agentic tests/contracts/agentic
uv run mypy app/contracts/agentic app/services/agentic tests/services/agentic tests/contracts/agentic
uv run pytest tests/contracts/agentic tests/services/agentic
uv run pytest tests/composition tests/architecture tests/removal
uv run pytest --cov=app/services/agentic --cov-fail-under=80
uv run python scripts/architecture_check.py
uv run python scripts/feature_conformance.py
uv run python scripts/documentation_drift.py
uv run python scripts/physical_removal.py
```

Exact existing script names/arguments are verified at implementation time; no README command is considered passing evidence until it runs in the current repository.

### Package completion checklist

- [ ] `app/contracts/agentic/` contains exactly the ratified public contracts and no receiver-owned duplicates.
- [ ] `app/services/agentic/README.md` remains the authoritative registry and every manifest/config/feature/feature-README/test agrees.
- [ ] All 20 semantic feature IDs are registered and independently discoverable/removable.
- [ ] All 22 built-in role profiles and seven role families have manifest/prompt/evaluation integrity and exact contribution disposal.
- [ ] The website-facing and actual agent is exactly **Chat Bot** with role ID `chat_bot`.
- [ ] Chat Bot uses bounded typed widget/page context, deterministic specialist routing, same-conversation results, and zero direct mutation authority.
- [ ] Every stateful feature declares namespace/schema/retention and owns migrations/adapters locally.
- [ ] No shared Agentic settings, limits, persistence, facade, agent hierarchy, or provider-framework object crosses boundaries.
- [ ] Claim graphs, not transcripts/hidden reasoning, are the canonical reasoning record.
- [ ] Research campaign/family/dataset/search/holdout accounting defeats trivial rehash/rename reuse and retains all failures/nulls.
- [ ] JSON strategy DSL is the primary authoring path; source code is sandbox fallback only.
- [ ] Every tool call has invocation-bound authorization and post-call filtering; forbidden consequential tools are unregistrable.
- [ ] Every consequential receiver decision remains with its deterministic owner.
- [ ] Provider/model fallback is explicit and independently eligible.
- [ ] Every effect uses feature scope; teardown cancels tasks, revokes leases, unregisters exact contributions, closes resources, and handles state by declared policy.
- [ ] Removing any feature produces its documented degraded state without fallback fabrication.
- [ ] Removing the entire Agentic domain preserves deterministic startup and safety equivalence.
- [ ] Every feature has executable primary-module usage plus contract/config/lifecycle/failure/replacement/removal tests.
- [ ] All feature workflows, NFRs, documentation drift, architecture, quality, and coverage gates pass.

---

## 14. Legacy Disposition and Authority Migration

The deleted `app/agentic/README.md` is a behavioral donor only. Its strong controls—proposal-only authority, no broker credentials, fail-closed evidence, typed provenance, bounded workflows, independent challenge, dissent, sandbox staging, evaluation, operations, and safety-equivalent disablement—are preserved or strengthened here.

Its old package path, `FEAT-AGT-01`–`22` numbering, agent-per-feature structure, global settings/limits, shared persistence, Agentic-owned receiver contracts, mandatory ADK identity, public API package, role titles, `Trader` name, exact-spec-only holdout rule, mixed implementation statuses, and completion claims do not carry forward.

`docs/dev/agentic_firm/` remains supporting policy/evidence only. Any file that declares the deleted README authoritative must be updated during documentation reconciliation. Current V3 architecture, public contracts, feature manifests, runtime evidence, and this README win over donor mechanism or status.

Legacy behavior is reconciled through the approved `KEEP / ADAPT / MERGE / REPLACE / DROP / ADD_TO_V3` matrix. Donor source/tests have not been pinned and inspected in this documentation stage, so this README makes no source-code parity claim.

---

## 15. Change Process

For every Agentic change:

1. Update this authoritative domain README first.
2. Confirm the semantic owner and exact public capability/contract version.
3. Update the feature row, dependencies, state, removal result, workflow, FR/NFR, and role roster as applicable.
4. Resolve receiver/UI/D-IFACE/System specification gaps before production invention.
5. Follow `docs/dev/feature_implementation_pipeline.md` for one focused feature task.
6. Add contract, configuration, lifecycle, behavior, failure, composition, replacement, removal, documentation, and executable usage evidence.
7. Run the complete current repository quality and architecture gates.
8. Change `Missing` status only after runtime truth and all documentation agree.
9. Record release-visible changes in `docs/CHANGELOG.md` and reconcile `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `app/services/README.md`, and interface registries when their scope changes.

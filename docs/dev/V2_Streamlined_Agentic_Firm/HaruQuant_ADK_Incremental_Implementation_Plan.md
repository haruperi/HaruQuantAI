# HaruQuant Streamlined Agent System Implementation Plan

Status: build-from-scratch implementation plan
Target runtime: Google ADK
Architecture style: agent-first, Markdown-manifest-driven, ADK-compatible, governance-aware
Goal: implement the new lean HaruQuant forecast trading agent system incrementally, agent by agent, with strict contracts, tests, permissions, audit, and quality gates.

---

## 1. Implementation Philosophy

Build this system from the bottom up:

```text
Contracts → Runtime → Policies → Tools → First Agent → First Workflow → Department → Cross-Department Workflow → Governance → Production Readiness
```

Do not begin by implementing all agents. First create the shared runtime and contracts so every agent follows the same standard.

The core rule is:

> Every agent must be runnable, testable, auditable, permissioned, and useful alone before it joins a larger workflow.

---

## 2. Universal Definition of Done

Every agent is complete only when:

- [ ] It has a valid `.agent.md`.
- [ ] It has typed input and output schemas.
- [ ] It declares execution mode: deterministic, llm, or hybrid.
- [ ] It declares allowed tools and blocked actions.
- [ ] It has deterministic policy checks.
- [ ] It has permission tests.
- [ ] It has smoke tests.
- [ ] It has evaluator checks.
- [ ] It emits audit metadata.
- [ ] It can run standalone through Google ADK.
- [ ] It is registered in `agentic/registry/agents/`.
- [ ] It has a README.
- [ ] It has an audit report before staging or production.

High-impact or production-capable agents must also have:

- [ ] human approval rules
- [ ] environment awareness
- [ ] hard control gates
- [ ] idempotency and duplicate protection
- [ ] compensation/safe-stop behavior
- [ ] incident escalation path
- [ ] security review
- [ ] production monitoring
- [ ] governance signoff

---

## 3. Build Phases

| Phase | Name | Main Outcome |
|---:|---|---|
| 0 | Repository and Documentation Foundation | Project skeleton, standards, architecture docs |
| 1 | Shared Contracts and Runtime | ADK Markdown Manifest Runtime and schemas |
| 2 | Policy, Permissions, Audit, Evaluation | Deterministic safety and observability backbone |
| 3 | Executive and Control Layer | AI CEO/CIO, Planner, Control Plane |
| 4 | Research Department | Evidence-backed research workflow |
| 5 | Strategy Development Department | Strategy spec/code package workflow |
| 6 | Simulation and Validation Department | Backtest, optimization, robustness workflow |
| 7 | Risk and Portfolio Department | Portfolio admission and risk decision workflow |
| 8 | Execution Department | Paper/live execution with readiness and kill-switch |
| 9 | Operations, Audit and Governance | Governance, audit, performance, cost monitoring |
| 10 | Cross-Department Workflows | End-to-end strategy lifecycle |
| 11 | CI, Quality Gates, Security, Production Hardening | Safe staging/production readiness |

---

## 4. Phase 0 — Repository and Documentation Foundation

### Goal

Create the repository, documentation tree, and development conventions before writing agents.

### Required Folders

```text
haruquant/
├── docs/
│   ├── architecture/
│   ├── agents/
│   ├── workflows/
│   ├── governance/
│   ├── runbooks/
│   └── adr/
├── agentic/
│   ├── host/
│   ├── agents/
│   ├── workflows/
│   ├── capabilities/
│   ├── policy/
│   ├── approvals/
│   ├── evaluation/
│   ├── observability/
│   ├── registry/
│   └── audit/
├── services/
├── tests/
└── scripts/
```

### Deliverables

- [ ] `README.md`
- [ ] `pyproject.toml`
- [ ] `.env.example`
- [ ] `docs/architecture/Streamlined_Agent_Architecture.md`
- [ ] `docs/architecture/Streamlined_Agent_Architecture.png`
- [ ] `docs/implementation/ADK_Incremental_Implementation_Plan.md`
- [ ] copied foundation docs:
  - [ ] `Agentic_AI_Playbook.md`
  - [ ] `Agent_Auditing_Checklist.md`
  - [ ] `Agent_Template.md`

### Acceptance Exit Gate

- [ ] repository opens cleanly
- [ ] docs paths exist
- [ ] test runner executes an empty test suite
- [ ] CI placeholder exists
- [ ] architecture docs are committed

---

## 5. Phase 1 — Shared Contracts and Runtime

### Goal

Build the reusable foundation that all agents use.

### Required Files

```text
agentic/agents/runtime/
├── manifest_schema.py
├── markdown_loader.py
├── instruction_loader.py
├── skill_loader.py
├── prompt_loader.py
├── tool_registry.py
├── agent_factory.py
├── agent_registry.py
├── permissions.py
├── audit.py
├── runner.py
└── adk_adapter.py

agentic/agents/shared/
├── schemas/
│   ├── agent_result.py
│   ├── handoff.py
│   ├── evidence.py
│   ├── policy.py
│   └── approval.py
├── instructions/
│   ├── global.instructions.md
│   ├── trading.instructions.md
│   ├── safety.instructions.md
│   └── coding.instructions.md
├── prompts/
│   └── clarify_request.prompt.md
└── skills/
    └── codebase_search/
        └── SKILL.md
```

### Contracts to Implement

- [ ] `AgentRequest`
- [ ] `AgentContext`
- [ ] `AgentResponse`
- [ ] `AgentStatus`
- [ ] `AgentDecision`
- [ ] `EvidenceItem`
- [ ] `AgentAudit`
- [ ] `HandoffEnvelope`
- [ ] `PolicyDecision`
- [ ] `ApprovalPacket`
- [ ] `ToolResult`
- [ ] `WorkflowState`

### Runtime Capabilities

- [ ] load `.agent.md` frontmatter and body
- [ ] validate referenced paths
- [ ] load `.instructions.md`
- [ ] load `SKILL.md`
- [ ] load `.prompt.md`
- [ ] resolve tools from registry
- [ ] build Google ADK `Agent`
- [ ] run with `Runner` and session service
- [ ] emit audit metadata
- [ ] fail fast on missing references

### Acceptance Exit Gate

- [ ] one fake demo agent can be loaded from `.agent.md`
- [ ] tool registry resolves callables
- [ ] invalid manifests fail tests
- [ ] audit object is emitted
- [ ] no real trading or broker capability exists yet

---

## 6. Phase 2 — Policy, Permissions, Audit, Evaluation

### Goal

Create deterministic enforcement before building powerful agents.

### Required Files

```text
agentic/policy/
├── permissions.py
├── environment.py
├── lifecycle.py
├── approval_rules.py
├── risk_classes.py
├── blocked_actions.py
└── policy_engine.py

agentic/observability/
├── logger.py
├── audit_logger.py
├── trace.py
├── redaction.py
└── cost_meter.py

agentic/evaluation/
├── evaluator.py
├── rubrics.py
├── golden_tasks.py
└── regression_runner.py
```

### Required Policies

- [ ] production action blocking
- [ ] live trading approval requirement
- [ ] risk-limit modification blocking
- [ ] manifest allowlist enforcement
- [ ] stale data handling
- [ ] output schema validation
- [ ] critical failure safe-stop
- [ ] environment separation
- [ ] audit logging requirement

### Acceptance Exit Gate

- [ ] policy engine blocks prohibited actions
- [ ] permission tests pass
- [ ] audit logger redacts sensitive fields
- [ ] evaluator can score a dummy response
- [ ] quality gate fails unsafe dummy agent

---

## 7. Phase 3 — Executive and Control Layer

### Goal

Create the user-facing routing and deterministic workflow control spine.

### Department Workflow

```text
User
→ AI CEO / CIO Agent
→ Planner Agent
→ Control Plane
→ Department Lead
```


### 1. AI CEO / CIO Agent

**Department:** Executive & Control
**Package path:** `agentic/agents/executive_and_control/ai_ceo_cio_agent/`
**Purpose:** single user-facing executive; routes final decisions.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/executive_and_control/ai_ceo_cio_agent/
├── ai_ceo_cio_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── ai_ceo_cio_agent.instructions.md
├── skills/
│   └── ai_ceo_cio_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: ai_ceo_cio_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - agent_registry_resource
  - workflow_registry_resource
  - permission_gate
  - audit_log_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `agent_registry_resource`
- `workflow_registry_resource`
- `permission_gate`
- `audit_log_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 2. Planner Agent

**Department:** Executive & Control
**Package path:** `agentic/agents/executive_and_control/planner_agent/`
**Purpose:** classifies intent and creates workflow plan.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/executive_and_control/planner_agent/
├── planner_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── planner_agent.instructions.md
├── skills/
│   └── planner_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: planner_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - agent_registry_resource
  - workflow_registry_resource
  - permission_gate
  - audit_log_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `agent_registry_resource`
- `workflow_registry_resource`
- `permission_gate`
- `audit_log_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 3. Control Plane

**Department:** Executive & Control
**Package path:** `agentic/agents/executive_and_control/control_plane/`
**Purpose:** deterministic policy, permissions, state, registry.
**Execution mode:** `deterministic`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/executive_and_control/control_plane/
├── control_plane.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── control_plane.instructions.md
├── skills/
│   └── control_plane_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: control_plane_v1
execution_mode: deterministic
state_mutation: read-only/advisory
allowed_tools:
  - agent_registry_resource
  - workflow_registry_resource
  - permission_gate
  - audit_log_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `agent_registry_resource`
- `workflow_registry_resource`
- `permission_gate`
- `audit_log_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- approval packet and risk evidence for high-impact decisions

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- enforce hard risk or execution gates without model override

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.
- [ ] failure-path tests: broker unavailable, stale approval, kill-switch active, duplicate request.

#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


---

## Phase 4 — Research Department

### Goal

Create the first full specialist department. It must produce Research Evidence Packs but cannot write strategies or run backtests.

### Department Workflow

```text
Control Plane
→ Research Lead / Entry Point
→ Department Specialists
→ Department Output Package
→ Audit + Next Department
```


### 4. Research Lead Agent

**Department:** Research
**Package path:** `agentic/agents/research/research_lead_agent/`
**Purpose:** owns evidence pack and department handoff.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/research/research_lead_agent/
├── research_lead_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── research_lead_agent.instructions.md
├── skills/
│   └── research_lead_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: research_lead_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - market_data_resource
  - forexfactory_news_tool
  - forexfactory_calendar_tool
  - sentiment_snapshot_tool
  - seasonality_tool
  - feature_stats_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `market_data_resource`
- `forexfactory_news_tool`
- `forexfactory_calendar_tool`
- `sentiment_snapshot_tool`
- `seasonality_tool`
- `feature_stats_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 5. Market Intelligence Agent

**Department:** Research
**Package path:** `agentic/agents/research/market_intelligence_agent/`
**Purpose:** news, calendar, sentiment, macro, seasonality.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/research/market_intelligence_agent/
├── market_intelligence_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── market_intelligence_agent.instructions.md
├── skills/
│   └── market_intelligence_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: market_intelligence_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - market_data_resource
  - forexfactory_news_tool
  - forexfactory_calendar_tool
  - sentiment_snapshot_tool
  - seasonality_tool
  - feature_stats_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `market_data_resource`
- `forexfactory_news_tool`
- `forexfactory_calendar_tool`
- `sentiment_snapshot_tool`
- `seasonality_tool`
- `feature_stats_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 6. Quant Research Agent

**Department:** Research
**Package path:** `agentic/agents/research/quant_research_agent/`
**Purpose:** technical/statistical edge discovery.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/research/quant_research_agent/
├── quant_research_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── quant_research_agent.instructions.md
├── skills/
│   └── quant_research_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: quant_research_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - market_data_resource
  - forexfactory_news_tool
  - forexfactory_calendar_tool
  - sentiment_snapshot_tool
  - seasonality_tool
  - feature_stats_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `market_data_resource`
- `forexfactory_news_tool`
- `forexfactory_calendar_tool`
- `sentiment_snapshot_tool`
- `seasonality_tool`
- `feature_stats_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 7. Research Validator Agent

**Department:** Research
**Package path:** `agentic/agents/research/research_validator_agent/`
**Purpose:** sample, bias, evidence sufficiency gate.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/research/research_validator_agent/
├── research_validator_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── research_validator_agent.instructions.md
├── skills/
│   └── research_validator_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: research_validator_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - market_data_resource
  - forexfactory_news_tool
  - forexfactory_calendar_tool
  - sentiment_snapshot_tool
  - seasonality_tool
  - feature_stats_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `market_data_resource`
- `forexfactory_news_tool`
- `forexfactory_calendar_tool`
- `sentiment_snapshot_tool`
- `seasonality_tool`
- `feature_stats_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


---

## Phase 5 — Strategy Development Department

### Goal

Convert validated hypotheses into Strategy Specification Packages and implementation-ready code/test packages.

### Department Workflow

```text
Control Plane
→ Strategy Development Lead / Entry Point
→ Department Specialists
→ Department Output Package
→ Audit + Next Department
```


### 8. Strategy Lead Agent

**Department:** Strategy Development
**Package path:** `agentic/agents/strategy_development/strategy_lead_agent/`
**Purpose:** owns strategy package and handoff.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/strategy_development/strategy_lead_agent/
├── strategy_lead_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── strategy_lead_agent.instructions.md
├── skills/
│   └── strategy_lead_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: strategy_lead_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - strategy_spec_builder
  - schema_validator
  - code_template_tool
  - indicator_registry_resource
  - strategy_registry_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `strategy_spec_builder`
- `schema_validator`
- `code_template_tool`
- `indicator_registry_resource`
- `strategy_registry_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 9. Strategy Designer Agent

**Department:** Strategy Development
**Package path:** `agentic/agents/strategy_development/strategy_designer_agent/`
**Purpose:** turns hypothesis into rules/spec.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/strategy_development/strategy_designer_agent/
├── strategy_designer_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── strategy_designer_agent.instructions.md
├── skills/
│   └── strategy_designer_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: strategy_designer_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - strategy_spec_builder
  - schema_validator
  - code_template_tool
  - indicator_registry_resource
  - strategy_registry_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `strategy_spec_builder`
- `schema_validator`
- `code_template_tool`
- `indicator_registry_resource`
- `strategy_registry_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 10. Strategy Engineer Agent

**Department:** Strategy Development
**Package path:** `agentic/agents/strategy_development/strategy_engineer_agent/`
**Purpose:** implements code + tests.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/strategy_development/strategy_engineer_agent/
├── strategy_engineer_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── strategy_engineer_agent.instructions.md
├── skills/
│   └── strategy_engineer_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: strategy_engineer_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - strategy_spec_builder
  - schema_validator
  - code_template_tool
  - indicator_registry_resource
  - strategy_registry_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `strategy_spec_builder`
- `schema_validator`
- `code_template_tool`
- `indicator_registry_resource`
- `strategy_registry_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 11. Strategy Reviewer Agent

**Department:** Strategy Development
**Package path:** `agentic/agents/strategy_development/strategy_reviewer_agent/`
**Purpose:** reviews spec/code/risk assumptions.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/strategy_development/strategy_reviewer_agent/
├── strategy_reviewer_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── strategy_reviewer_agent.instructions.md
├── skills/
│   └── strategy_reviewer_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: strategy_reviewer_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - strategy_spec_builder
  - schema_validator
  - code_template_tool
  - indicator_registry_resource
  - strategy_registry_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `strategy_spec_builder`
- `schema_validator`
- `code_template_tool`
- `indicator_registry_resource`
- `strategy_registry_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 12. Strategy Librarian Agent

**Department:** Strategy Development
**Package path:** `agentic/agents/strategy_development/strategy_librarian_agent/`
**Purpose:** versioning, registry, storage.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/strategy_development/strategy_librarian_agent/
├── strategy_librarian_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── strategy_librarian_agent.instructions.md
├── skills/
│   └── strategy_librarian_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: strategy_librarian_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - strategy_spec_builder
  - schema_validator
  - code_template_tool
  - indicator_registry_resource
  - strategy_registry_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `strategy_spec_builder`
- `schema_validator`
- `code_template_tool`
- `indicator_registry_resource`
- `strategy_registry_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


---

## Phase 6 — Simulation and Validation Department

### Goal

Run reproducible backtests, optimization, robustness testing, and validation evidence packaging.

### Department Workflow

```text
Control Plane
→ Simulation & Validation Lead / Entry Point
→ Department Specialists
→ Department Output Package
→ Audit + Next Department
```


### 13. Simulation Lead Agent

**Department:** Simulation & Validation
**Package path:** `agentic/agents/simulation_and_validation/simulation_lead_agent/`
**Purpose:** owns test suite and validation workflow.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/simulation_and_validation/simulation_lead_agent/
├── simulation_lead_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── simulation_lead_agent.instructions.md
├── skills/
│   └── simulation_lead_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: simulation_lead_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - backtest_runner_tool
  - metrics_tool
  - optimizer_tool
  - monte_carlo_tool
  - robustness_report_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `backtest_runner_tool`
- `metrics_tool`
- `optimizer_tool`
- `monte_carlo_tool`
- `robustness_report_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 14. Backtest Analyst Agent

**Department:** Simulation & Validation
**Package path:** `agentic/agents/simulation_and_validation/backtest_analyst_agent/`
**Purpose:** metrics, behavior, diagnostics.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/simulation_and_validation/backtest_analyst_agent/
├── backtest_analyst_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── backtest_analyst_agent.instructions.md
├── skills/
│   └── backtest_analyst_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: backtest_analyst_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - backtest_runner_tool
  - metrics_tool
  - optimizer_tool
  - monte_carlo_tool
  - robustness_report_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `backtest_runner_tool`
- `metrics_tool`
- `optimizer_tool`
- `monte_carlo_tool`
- `robustness_report_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 15. Optimization Agent

**Department:** Simulation & Validation
**Package path:** `agentic/agents/simulation_and_validation/optimization_agent/`
**Purpose:** parameter search, WFO/WFM, sensitivity.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/simulation_and_validation/optimization_agent/
├── optimization_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── optimization_agent.instructions.md
├── skills/
│   └── optimization_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: optimization_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - backtest_runner_tool
  - metrics_tool
  - optimizer_tool
  - monte_carlo_tool
  - robustness_report_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `backtest_runner_tool`
- `metrics_tool`
- `optimizer_tool`
- `monte_carlo_tool`
- `robustness_report_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 16. Robustness Validator Agent

**Department:** Simulation & Validation
**Package path:** `agentic/agents/simulation_and_validation/robustness_validator_agent/`
**Purpose:** Monte Carlo, spread/slippage/cross tests.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/simulation_and_validation/robustness_validator_agent/
├── robustness_validator_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── robustness_validator_agent.instructions.md
├── skills/
│   └── robustness_validator_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: robustness_validator_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - backtest_runner_tool
  - metrics_tool
  - optimizer_tool
  - monte_carlo_tool
  - robustness_report_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `backtest_runner_tool`
- `metrics_tool`
- `optimizer_tool`
- `monte_carlo_tool`
- `robustness_report_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 17. Evidence Packager Agent

**Department:** Simulation & Validation
**Package path:** `agentic/agents/simulation_and_validation/evidence_packager_agent/`
**Purpose:** validation evidence package.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/simulation_and_validation/evidence_packager_agent/
├── evidence_packager_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── evidence_packager_agent.instructions.md
├── skills/
│   └── evidence_packager_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: evidence_packager_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - backtest_runner_tool
  - metrics_tool
  - optimizer_tool
  - monte_carlo_tool
  - robustness_report_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `backtest_runner_tool`
- `metrics_tool`
- `optimizer_tool`
- `monte_carlo_tool`
- `robustness_report_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


---

## Phase 7 — Risk and Portfolio Department

### Goal

Gate strategy admission, allocation, risk limits, portfolio exposure, and lifecycle decisions.

### Department Workflow

```text
Control Plane
→ Risk & Portfolio Lead / Entry Point
→ Department Specialists
→ Department Output Package
→ Audit + Next Department
```


### 18. Risk Lead Agent

**Department:** Risk & Portfolio
**Package path:** `agentic/agents/risk_and_portfolio/risk_lead_agent/`
**Purpose:** final risk review and risk decision package.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/risk_and_portfolio/risk_lead_agent/
├── risk_lead_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── risk_lead_agent.instructions.md
├── skills/
│   └── risk_lead_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: risk_lead_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - portfolio_state_resource
  - risk_limits_resource
  - var_cvar_tool
  - correlation_tool
  - allocation_tool
  - risk_policy_gate
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `portfolio_state_resource`
- `risk_limits_resource`
- `var_cvar_tool`
- `correlation_tool`
- `allocation_tool`
- `risk_policy_gate`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 19. Risk Governor Agent

**Department:** Risk & Portfolio
**Package path:** `agentic/agents/risk_and_portfolio/risk_governor_agent/`
**Purpose:** deterministic hard limits and gates.
**Execution mode:** `deterministic`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/risk_and_portfolio/risk_governor_agent/
├── risk_governor_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── risk_governor_agent.instructions.md
├── skills/
│   └── risk_governor_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: risk_governor_agent_v1
execution_mode: deterministic
state_mutation: read-only/advisory
allowed_tools:
  - portfolio_state_resource
  - risk_limits_resource
  - var_cvar_tool
  - correlation_tool
  - allocation_tool
  - risk_policy_gate
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `portfolio_state_resource`
- `risk_limits_resource`
- `var_cvar_tool`
- `correlation_tool`
- `allocation_tool`
- `risk_policy_gate`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- approval packet and risk evidence for high-impact decisions

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- enforce hard risk or execution gates without model override

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.
- [ ] failure-path tests: broker unavailable, stale approval, kill-switch active, duplicate request.

#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 20. Portfolio Manager Agent

**Department:** Risk & Portfolio
**Package path:** `agentic/agents/risk_and_portfolio/portfolio_manager_agent/`
**Purpose:** strategy lifecycle and portfolio composition.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/risk_and_portfolio/portfolio_manager_agent/
├── portfolio_manager_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── portfolio_manager_agent.instructions.md
├── skills/
│   └── portfolio_manager_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: portfolio_manager_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - portfolio_state_resource
  - risk_limits_resource
  - var_cvar_tool
  - correlation_tool
  - allocation_tool
  - risk_policy_gate
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `portfolio_state_resource`
- `risk_limits_resource`
- `var_cvar_tool`
- `correlation_tool`
- `allocation_tool`
- `risk_policy_gate`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 21. Allocation Agent

**Department:** Risk & Portfolio
**Package path:** `agentic/agents/risk_and_portfolio/allocation_agent/`
**Purpose:** position sizing and capital allocation.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/risk_and_portfolio/allocation_agent/
├── allocation_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── allocation_agent.instructions.md
├── skills/
│   └── allocation_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: allocation_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - portfolio_state_resource
  - risk_limits_resource
  - var_cvar_tool
  - correlation_tool
  - allocation_tool
  - risk_policy_gate
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `portfolio_state_resource`
- `risk_limits_resource`
- `var_cvar_tool`
- `correlation_tool`
- `allocation_tool`
- `risk_policy_gate`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 22. Risk Auditor Agent

**Department:** Risk & Portfolio
**Package path:** `agentic/agents/risk_and_portfolio/risk_auditor_agent/`
**Purpose:** verifies risk evidence and approvals.
**Execution mode:** `hybrid`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/risk_and_portfolio/risk_auditor_agent/
├── risk_auditor_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── risk_auditor_agent.instructions.md
├── skills/
│   └── risk_auditor_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: risk_auditor_agent_v1
execution_mode: hybrid
state_mutation: read-only/advisory
allowed_tools:
  - portfolio_state_resource
  - risk_limits_resource
  - var_cvar_tool
  - correlation_tool
  - allocation_tool
  - risk_policy_gate
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `portfolio_state_resource`
- `risk_limits_resource`
- `var_cvar_tool`
- `correlation_tool`
- `allocation_tool`
- `risk_policy_gate`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


---

## Phase 8 — Execution Department

### Goal

Implement paper/live execution workflow with readiness checks and deterministic kill-switch behavior.

### Department Workflow

```text
Control Plane
→ Execution Lead / Entry Point
→ Department Specialists
→ Department Output Package
→ Audit + Next Department
```


### 23. Execution Lead Agent

**Department:** Execution
**Package path:** `agentic/agents/execution/execution_lead_agent/`
**Purpose:** coordinates approved execution workflow.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/execution/execution_lead_agent/
├── execution_lead_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── execution_lead_agent.instructions.md
├── skills/
│   └── execution_lead_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: execution_lead_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - broker_state_resource
  - execution_readiness_tool
  - paper_order_tool
  - live_order_tool
  - kill_switch_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `broker_state_resource`
- `execution_readiness_tool`
- `paper_order_tool`
- `live_order_tool`
- `kill_switch_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.
- [ ] failure-path tests: broker unavailable, stale approval, kill-switch active, duplicate request.

#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 24. Execution Readiness Agent

**Department:** Execution
**Package path:** `agentic/agents/execution/execution_readiness_agent/`
**Purpose:** broker/session/spread/margin readiness.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/execution/execution_readiness_agent/
├── execution_readiness_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── execution_readiness_agent.instructions.md
├── skills/
│   └── execution_readiness_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: execution_readiness_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - broker_state_resource
  - execution_readiness_tool
  - paper_order_tool
  - live_order_tool
  - kill_switch_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `broker_state_resource`
- `execution_readiness_tool`
- `paper_order_tool`
- `live_order_tool`
- `kill_switch_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.
- [ ] failure-path tests: broker unavailable, stale approval, kill-switch active, duplicate request.

#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 25. Paper Trading Agent

**Department:** Execution
**Package path:** `agentic/agents/execution/paper_trading_agent/`
**Purpose:** paper deployment and graduation report.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/execution/paper_trading_agent/
├── paper_trading_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── paper_trading_agent.instructions.md
├── skills/
│   └── paper_trading_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: paper_trading_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - broker_state_resource
  - execution_readiness_tool
  - paper_order_tool
  - live_order_tool
  - kill_switch_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `broker_state_resource`
- `execution_readiness_tool`
- `paper_order_tool`
- `live_order_tool`
- `kill_switch_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.
- [ ] failure-path tests: broker unavailable, stale approval, kill-switch active, duplicate request.

#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 26. Live Execution Agent

**Department:** Execution
**Package path:** `agentic/agents/execution/live_execution_agent/`
**Purpose:** permissioned live actions only.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/execution/live_execution_agent/
├── live_execution_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── live_execution_agent.instructions.md
├── skills/
│   └── live_execution_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: live_execution_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - broker_state_resource
  - execution_readiness_tool
  - paper_order_tool
  - live_order_tool
  - kill_switch_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `broker_state_resource`
- `execution_readiness_tool`
- `paper_order_tool`
- `live_order_tool`
- `kill_switch_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- approval packet and risk evidence for high-impact decisions

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- enforce hard risk or execution gates without model override

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.
- [ ] failure-path tests: broker unavailable, stale approval, kill-switch active, duplicate request.

#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 27. Kill Switch Agent

**Department:** Execution
**Package path:** `agentic/agents/execution/kill_switch_agent/`
**Purpose:** deterministic safe-stop authority.
**Execution mode:** `deterministic`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/execution/kill_switch_agent/
├── kill_switch_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── kill_switch_agent.instructions.md
├── skills/
│   └── kill_switch_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: kill_switch_agent_v1
execution_mode: deterministic
state_mutation: write-capable through policy-gated services
allowed_tools:
  - broker_state_resource
  - execution_readiness_tool
  - paper_order_tool
  - live_order_tool
  - kill_switch_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `broker_state_resource`
- `execution_readiness_tool`
- `paper_order_tool`
- `live_order_tool`
- `kill_switch_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- approval packet and risk evidence for high-impact decisions

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- enforce hard risk or execution gates without model override

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.
- [ ] failure-path tests: broker unavailable, stale approval, kill-switch active, duplicate request.

#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


---

## Phase 9 — Operations, Audit and Governance Department

### Goal

Implement governance, audit, performance monitoring, and cost controls.

### Department Workflow

```text
Control Plane
→ Operations, Audit & Governance Lead / Entry Point
→ Department Specialists
→ Department Output Package
→ Audit + Next Department
```


### 28. Governance Agent

**Department:** Operations, Audit & Governance
**Package path:** `agentic/agents/operations,_audit_and_governance/governance_agent/`
**Purpose:** policy, approval, lifecycle authority.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/operations,_audit_and_governance/governance_agent/
├── governance_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── governance_agent.instructions.md
├── skills/
│   └── governance_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: governance_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - audit_log_tool
  - approval_registry_tool
  - policy_registry_resource
  - performance_report_tool
  - cost_meter_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - execute_live_trade_without_approval
  - modify_risk_limits_without_governance
  - override_kill_switch
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `audit_log_tool`
- `approval_registry_tool`
- `policy_registry_resource`
- `performance_report_tool`
- `cost_meter_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- approval packet and risk evidence for high-impact decisions

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- enforce hard risk or execution gates without model override

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `execute_live_trade_without_approval`
- `modify_risk_limits_without_governance`
- `override_kill_switch`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.
- [ ] failure-path tests: broker unavailable, stale approval, kill-switch active, duplicate request.

#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 29. Audit Agent

**Department:** Operations, Audit & Governance
**Package path:** `agentic/agents/operations,_audit_and_governance/audit_agent/`
**Purpose:** immutable logs and traceability.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/operations,_audit_and_governance/audit_agent/
├── audit_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── audit_agent.instructions.md
├── skills/
│   └── audit_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: audit_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - audit_log_tool
  - approval_registry_tool
  - policy_registry_resource
  - performance_report_tool
  - cost_meter_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `audit_log_tool`
- `approval_registry_tool`
- `policy_registry_resource`
- `performance_report_tool`
- `cost_meter_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 30. Performance Reporter Agent

**Department:** Operations, Audit & Governance
**Package path:** `agentic/agents/operations,_audit_and_governance/performance_reporter_agent/`
**Purpose:** performance and degradation monitoring.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/operations,_audit_and_governance/performance_reporter_agent/
├── performance_reporter_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── performance_reporter_agent.instructions.md
├── skills/
│   └── performance_reporter_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: performance_reporter_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - audit_log_tool
  - approval_registry_tool
  - policy_registry_resource
  - performance_report_tool
  - cost_meter_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `audit_log_tool`
- `approval_registry_tool`
- `policy_registry_resource`
- `performance_report_tool`
- `cost_meter_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 31. Cost & Efficiency Agent

**Department:** Operations, Audit & Governance
**Package path:** `agentic/agents/operations,_audit_and_governance/cost_and_efficiency_agent/`
**Purpose:** LLM, compute, broker, data, friction cost.
**Execution mode:** `hybrid`
**State mutation:** `write-capable through policy-gated services`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/operations,_audit_and_governance/cost_and_efficiency_agent/
├── cost_and_efficiency_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── cost_and_efficiency_agent.instructions.md
├── skills/
│   └── cost_and_efficiency_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: cost_and_efficiency_agent_v1
execution_mode: hybrid
state_mutation: write-capable through policy-gated services
allowed_tools:
  - audit_log_tool
  - approval_registry_tool
  - policy_registry_resource
  - performance_report_tool
  - cost_meter_tool
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `audit_log_tool`
- `approval_registry_tool`
- `policy_registry_resource`
- `performance_report_tool`
- `cost_meter_tool`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


---

## Phase 10 — Shared Runtime and Capability Layer

### Goal

Complete shared capabilities, adapters, services, registries, observability, and evaluation tools.

### Department Workflow

```text
Control Plane
→ Shared Runtime & Capability Layer Lead / Entry Point
→ Department Specialists
→ Department Output Package
→ Audit + Next Department
```


### 32. ADK Markdown Manifest Runtime

**Department:** Shared Runtime & Capability Layer
**Package path:** `agentic/agents/shared_runtime_and_capability_layer/adk_markdown_manifest_runtime_agent/`
**Purpose:** .agent.md, .prompt.md, SKILL.md, .instructions.md.
**Execution mode:** `deterministic`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/shared_runtime_and_capability_layer/adk_markdown_manifest_runtime_agent/
├── adk_markdown_manifest_runtime_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── adk_markdown_manifest_runtime_agent.instructions.md
├── skills/
│   └── adk_markdown_manifest_runtime_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: adk_markdown_manifest_runtime_agent_v1
execution_mode: deterministic
state_mutation: read-only/advisory
allowed_tools:
  - manifest_loader
  - tool_registry
  - policy_engine
  - trace_logger
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `manifest_loader`
- `tool_registry`
- `policy_engine`
- `trace_logger`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 33. Tool / Resource Registry

**Department:** Shared Runtime & Capability Layer
**Package path:** `agentic/agents/shared_runtime_and_capability_layer/tool_resource_registry_agent/`
**Purpose:** typed governed capabilities.
**Execution mode:** `deterministic`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/shared_runtime_and_capability_layer/tool_resource_registry_agent/
├── tool_resource_registry_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── tool_resource_registry_agent.instructions.md
├── skills/
│   └── tool_resource_registry_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: tool_resource_registry_agent_v1
execution_mode: deterministic
state_mutation: read-only/advisory
allowed_tools:
  - manifest_loader
  - tool_registry
  - policy_engine
  - trace_logger
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `manifest_loader`
- `tool_registry`
- `policy_engine`
- `trace_logger`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 34. Services

**Department:** Shared Runtime & Capability Layer
**Package path:** `agentic/agents/shared_runtime_and_capability_layer/services_agent/`
**Purpose:** data, research, backtest, risk, execution adapters.
**Execution mode:** `deterministic`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/shared_runtime_and_capability_layer/services_agent/
├── services_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── services_agent.instructions.md
├── skills/
│   └── services_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: services_agent_v1
execution_mode: deterministic
state_mutation: read-only/advisory
allowed_tools:
  - manifest_loader
  - tool_registry
  - policy_engine
  - trace_logger
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `manifest_loader`
- `tool_registry`
- `policy_engine`
- `trace_logger`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


### 35. Observability / Evaluation

**Department:** Shared Runtime & Capability Layer
**Package path:** `agentic/agents/shared_runtime_and_capability_layer/observability_evaluation_agent/`
**Purpose:** traces, audits, quality gates, tests.
**Execution mode:** `deterministic`
**State mutation:** `read-only/advisory`
**Lifecycle start:** `development`
**First target:** standalone smoke test, then department workflow test.

#### Required Folders and Files

```text
agentic/agents/shared_runtime_and_capability_layer/observability_evaluation_agent/
├── observability_evaluation_agent.agent.md
├── README.md
├── agent.py
├── service.py
├── policy.py
├── permissions.py
├── evaluator.py
├── schemas/
│   ├── input_schema.py
│   └── output_schema.py
├── prompts/
│   └── main.prompt.md
├── instructions/
│   └── observability_evaluation_agent.instructions.md
├── skills/
│   └── observability_evaluation_agent_workflow/
│       └── SKILL.md
├── tools/
│   └── local_tools.py
├── fixtures/
└── tests/
    ├── test_manifest.py
    ├── test_schemas.py
    ├── test_agent.py
    ├── test_policy.py
    ├── test_permissions.py
    ├── test_evaluator.py
    └── test_smoke.py
```

#### Shared Contracts

- `AgentRequest`
- `AgentContext`
- `AgentResponse`
- `AgentAudit`
- `EvidenceItem`
- department-specific input/output schema
- `HandoffEnvelope`
- `PolicyDecision`
- `ApprovalRequirement`
- `TraceContext`

#### Shared Permission Profile

```yaml
permission_profile: observability_evaluation_agent_v1
execution_mode: deterministic
state_mutation: read-only/advisory
allowed_tools:
  - manifest_loader
  - tool_registry
  - policy_engine
  - trace_logger
blocked_actions:
  - bypass_control_plane
  - use_unregistered_tools
  - hide_missing_evidence
  - invent_metrics_or_backtest_results
  - approve_live_deployment
  - execute_live_trade
```

#### Shared Audit Requirements

- Log `trace_id`, `workflow_id`, `agent_name`, `agent_version`, `manifest_version`, `execution_mode`.
- Log input references, not secrets.
- Log tools called and tool output references.
- Log policy decisions, blocked actions, assumptions, warnings, and handoff target.
- Emit a valid `AgentAudit` object on every success, rejection, clarification, or failure.

#### Department Workflow Position

- **Upstream:** department lead, planner, or previous workflow stage.
- **Downstream:** department lead, next specialist, evaluator, or next department lead.
- **Handoff rule:** output must be schema-valid before downstream use.
- **Escalation:** return `needs_clarification`, `rejected`, or `requires_approval` instead of guessing.

#### Inputs

- structured request payload
- workflow state
- evidence references from upstream agents
- environment mode
- policy profile
- data freshness context where relevant

#### Outputs

- status: `success | rejected | needs_clarification | failed`
- evidence list
- model analysis, if applicable
- deterministic decision
- artifacts
- audit metadata
- next recommended action

#### Tools

- `manifest_loader`
- `tool_registry`
- `policy_engine`
- `trace_logger`

#### Evidence Required

- current workflow state
- relevant source data or artifact references
- freshness timestamp or snapshot ID
- policy and permission check result
- assumptions and unresolved questions
- reviewer/evaluator note before handoff if output is consequential

#### LLM Responsibilities

- interpret the request within this agent's scope
- summarize evidence
- propose recommendations or explanations
- identify uncertainty, conflicts, missing inputs, and next actions
- produce structured draft output for deterministic validation

#### Deterministic Decision Rules

- validate required inputs before model/tool use
- validate tool arguments
- validate model output schema
- reject stale or missing evidence when freshness is required
- enforce allowed/blocked tools
- enforce environment restrictions
- enforce lifecycle authority limits
- block production-impacting actions by default

#### Allowed Actions

- analyze assigned inputs
- call allowlisted tools
- generate structured output
- produce handoff package
- request clarification or escalation
- log audit metadata

#### Blocked Actions

- `bypass_control_plane`
- `use_unregistered_tools`
- `hide_missing_evidence`
- `invent_metrics_or_backtest_results`
- `approve_live_deployment`
- `execute_live_trade`

#### Functional Checklist

- [ ] Manifest declares name, version, owner, lifecycle, execution mode, model, tools, blocked actions.
- [ ] Input schema validates all required fields.
- [ ] Output schema validates `AgentResponse`.
- [ ] Permissions deny unsafe tools.
- [ ] Policy handles missing, invalid, stale, and conflicting inputs.
- [ ] Evaluator can reject poor output.
- [ ] Audit metadata is emitted on all paths.
- [ ] README explains scope, non-scope, tools, tests, and audit path.
- [ ] Agent can run alone in local/test mode.
- [ ] Agent is registered only after tests pass.

#### Tests

- [ ] `test_manifest.py`: manifest loads and referenced files exist.
- [ ] `test_schemas.py`: valid and invalid payloads.
- [ ] `test_policy.py`: blocked actions and missing evidence.
- [ ] `test_permissions.py`: allowed/forbidden tool profile.
- [ ] `test_agent.py`: normal run and rejection run.
- [ ] `test_evaluator.py`: quality checks.
- [ ] `test_smoke.py`: construct ADK agent and run one simple task.
- [ ] root contract test: upstream/downstream handoff schema.


#### Implementation Deliverables

- [ ] agent folder created
- [ ] `.agent.md` manifest
- [ ] local instructions
- [ ] main prompt
- [ ] SKILL.md workflow
- [ ] input/output schemas
- [ ] policy and permissions modules
- [ ] evaluator
- [ ] service boundary
- [ ] ADK agent factory integration
- [ ] unit tests
- [ ] registry entry
- [ ] audit report draft

#### Acceptance Exit Gate

This agent is complete when:

1. It runs standalone.
2. It passes local unit tests.
3. It emits a valid `AgentResponse`.
4. It has no unrestricted tool access.
5. It cannot perform blocked actions.
6. It has a registry entry.
7. It has a README and audit report.
8. It passes the department workflow contract test.


---

## 18. Phase 11 — Cross-Department Workflows

### Goal

Wire the departments into full end-to-end trading workflows only after the departments pass standalone and department-level tests.

### Workflow A — Research to Strategy

```text
AI CEO/CIO
→ Planner
→ Control Plane
→ Research Lead
→ Market Intelligence + Quant Research
→ Research Validator
→ Strategy Lead
→ Strategy Designer
→ Strategy Reviewer
```

Acceptance:

- [ ] vague idea becomes research hypothesis
- [ ] research evidence pack validates
- [ ] strategy spec package validates
- [ ] no backtest or live claims are made

### Workflow B — Strategy to Backtest

```text
Strategy Lead
→ Strategy Engineer
→ Strategy Reviewer
→ Strategy Librarian
→ Simulation Lead
→ Backtest Analyst
→ Evidence Packager
```

Acceptance:

- [ ] strategy code is generated or selected from template
- [ ] unit tests pass
- [ ] backtest runner is called through service/tool boundary
- [ ] backtest evidence package is produced

### Workflow C — Validation to Portfolio Admission

```text
Simulation Lead
→ Optimization Agent
→ Robustness Validator
→ Evidence Packager
→ Risk Lead
→ Risk Governor
→ Portfolio Manager
→ Allocation Agent
→ Risk Auditor
```

Acceptance:

- [ ] robustness tests complete
- [ ] optimization does not self-approve
- [ ] portfolio impact is calculated
- [ ] Risk Governor can reject deterministically
- [ ] final risk package is auditable

### Workflow D — Paper Trading

```text
Risk Lead
→ Execution Lead
→ Execution Readiness
→ Paper Trading Agent
→ Performance Reporter
→ Audit Agent
```

Acceptance:

- [ ] no live order tools are available
- [ ] paper orders are idempotent
- [ ] performance divergence is measured
- [ ] graduation report is produced

### Workflow E — Live Activation

```text
Paper Graduation Report
→ Risk Lead
→ Governance Agent
→ Human Board if required
→ Execution Lead
→ Execution Readiness
→ Live Execution Agent
→ Kill Switch monitoring
→ Audit Agent
```

Acceptance:

- [ ] approval packet exists
- [ ] Risk Governor passes
- [ ] Governance approval passes
- [ ] Live Execution cannot run if kill switch is active
- [ ] every live action has audit trace

---

## 19. Phase 12 — CI, Quality Gates, Security, Production Hardening

### Required Scripts

```text
scripts/
├── validate_agent_manifest.py
├── validate_markdown_agents.py
├── validate_workflow_registry.py
├── validate_capability_registry.py
├── agent_registry_quality_gate.py
├── workflow_quality_gate.py
├── run_agent_audit.py
└── generate_audit_report.py
```

### CI Gates

- [ ] formatting
- [ ] type checking
- [ ] unit tests
- [ ] contract tests
- [ ] security tests
- [ ] manifest validation
- [ ] workflow registry validation
- [ ] permission tests
- [ ] quality gates
- [ ] audit report generation

### Security Tests

- [ ] prompt injection into retrieved documents
- [ ] tool output poisoning
- [ ] attempt to use blocked tools
- [ ] attempt to bypass Risk Governor
- [ ] attempt to promote without approval
- [ ] stale data treated as current
- [ ] environment confusion: development vs production

### Production Hardening

- [ ] secrets stored outside code
- [ ] broker credentials isolated
- [ ] live trading disabled by default
- [ ] kill switch tested
- [ ] incident runbook written
- [ ] rollback/compensation paths documented
- [ ] audit storage append-only or immutable
- [ ] monitoring dashboards created

---

## 20. Recommended Chronological Build Order

Use this exact order to reduce complexity:

1. Repository structure.
2. Shared schemas.
3. Markdown manifest loader.
4. Tool registry.
5. ADK agent factory.
6. Audit logger.
7. Permission engine.
8. Policy engine.
9. Dummy deterministic agent.
10. AI CEO/CIO Agent.
11. Planner Agent.
12. Control Plane.
13. Research Lead Agent.
14. Market Intelligence Agent.
15. Quant Research Agent.
16. Research Validator Agent.
17. Strategy Lead Agent.
18. Strategy Designer Agent.
19. Strategy Reviewer Agent.
20. Strategy Engineer Agent.
21. Strategy Librarian Agent.
22. Simulation Lead Agent.
23. Backtest Analyst Agent.
24. Evidence Packager Agent.
25. Optimization Agent.
26. Robustness Validator Agent.
27. Risk Lead Agent.
28. Risk Governor Agent.
29. Portfolio Manager Agent.
30. Allocation Agent.
31. Risk Auditor Agent.
32. Execution Lead Agent.
33. Execution Readiness Agent.
34. Paper Trading Agent.
35. Kill Switch Agent.
36. Live Execution Agent.
37. Governance Agent.
38. Audit Agent.
39. Performance Reporter Agent.
40. Cost & Efficiency Agent.
41. End-to-end workflows.
42. CI quality gates.
43. Security tests.
44. Staging simulation.
45. Paper trading only.
46. Live trading only after governance approval.

---

## 21. Agent Promotion Checklist

### experimental → development

- [ ] manifest exists
- [ ] README exists
- [ ] schemas exist
- [ ] smoke test passes

### development → test

- [ ] unit tests pass
- [ ] permissions pass
- [ ] policy tests pass
- [ ] evaluator exists
- [ ] registry entry exists

### test → staging

- [ ] workflow tests pass
- [ ] audit report exists
- [ ] quality gate passes
- [ ] security tests pass for high-impact agents
- [ ] owner signoff

### staging → production

- [ ] governance approval
- [ ] production monitoring
- [ ] incident runbook
- [ ] rollback/safe-stop path
- [ ] live permissions explicitly enabled
- [ ] kill switch active
- [ ] Human Board approval for financially material actions

---

## 22. Final Build Rule

Do not build this as a swarm of agents.

Build it as:

```text
one runtime,
one control plane,
few department leads,
bounded specialists,
many deterministic tools,
strict contracts,
and audit-first workflows.
```

That structure gives you a streamlined forecast trading system that can grow without becoming confusing or impossible to debug.

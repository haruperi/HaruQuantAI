
# Agentic Firm Detailed Implementation Plan

> Aligned with:
>
> - `docs/Agentic_AI_Playbook.md`
> - `docs/Agent_Auditing_Checklist.md`
> - `docs/Agent_Template.md`

## Purpose

This document provides a detailed, chronological, incremental implementation plan for the full agentic firm architecture shown in the provided diagram.

The plan treats each department as a development phase and each agent as an independently buildable, testable, auditable unit.

## Core Implementation Pattern

Every agent follows this execution pattern:

```text
Validate Input
 -> Gather Evidence / Context
 -> Optional LLM Reasoning
 -> Deterministic Policy / Control Decision
 -> Structured Output
 -> Audit Log
 -> Evaluation Test
 -> Handoff or Final Response
```

LLM reasoning may assist with analysis, classification, summarization, explanation, ranking, and proposal drafting.

Deterministic code controls final decisions, permissions, blocked actions, lifecycle transitions, high-impact actions, and production gates.

## Approved Canonical Project Structure

```text
project-root/
├── docs/
│   ├── Agentic_AI_Playbook.md
│   ├── Agent_Auditing_Checklist.md
│   ├── Agent_Template.md
│   ├── agents/
│   ├── workflows/
│   ├── capabilities/
│   ├── governance/
│   ├── operations/
│   └── security/
├── agentic/
│   ├── host/
│   ├── agents/
│   │   ├── _shared/
│   │   ├── runtime/
│   │   ├── shared_contracts/
│   │   ├── control_plane/
│   │   ├── research/
│   │   ├── strategy_development/
│   │   ├── simulation/
│   │   ├── validation_backtesting/
│   │   ├── risk/
│   │   ├── portfolio_execution/
│   │   ├── operations_audit/
│   │   └── audit/
│   ├── workflows/
│   ├── capabilities/
│   ├── memory/
│   ├── state/
│   ├── policy/
│   ├── approvals/
│   ├── evaluation/
│   ├── observability/
│   ├── security/
│   └── config/
├── registry/
│   ├── agents/
│   ├── workflows/
│   └── capabilities/
├── audit/
│   ├── reports/
│   └── evidence/
├── tests/
│   ├── agents/
│   ├── workflows/
│   ├── capabilities/
│   ├── integration/
│   ├── contracts/
│   ├── security/
│   ├── failure/
│   └── evaluation/
└── scripts/
```

## Standard Folder Structure for One Agent

```text
agentic/agents/<department>/<agent_name>/
├── agent.py
├── prompt.md
├── manifest.yaml
├── schemas.py
└── README.md

tests/agents/<department>/<agent_name>/
├── test_schemas.py
├── test_agent.py
├── test_policy.py
├── test_permissions.py
├── test_evaluator.py
└── test_user_workflows.py
```

## Shared Contracts

Every agent must use or extend:

| Contract | Purpose |
|---|---|
| `AgentRequest` | Standard request envelope. |
| `AgentContext` | Session, environment, user, workflow, state, and dependency context. |
| `AgentResponse` | Standard response envelope. |
| `EvidenceItem` | Source, timestamp, freshness, confidence, and payload reference. |
| `AgentDecision` | Deterministic status, allowed actions, blocked actions, reasons, confidence, and flags. |
| `AuditRecord` | Provenance, policy, model, tool, trace, and approval metadata. |
| `PermissionProfile` | Read/write/execute permissions and approval requirements. |
| `EvaluationResult` | Quality and benchmark result. |
| `HandoffPayload` | Department-to-department handoff package. |
| `LifecycleState` | `experimental`, `development`, `test`, `staging`, `production`, `deprecated`. |

## Shared Permission Classes

| Class | Meaning | Default Rule |
|---|---|---|
| `read_only` | Retrieve or summarize only. | Allowed with logging. |
| `analysis` | Analyze and recommend but not mutate state. | Allowed with evidence. |
| `proposal` | Propose artifacts, actions, or transitions. | Requires deterministic validation. |
| `write_safe` | Write reversible artifacts or drafts. | Requires policy gate and audit. |
| `write_controlled` | Mutate important records or lifecycle states. | Requires approval gate. |
| `high_impact` | Affect production, external systems, users, capital, security, or irreversible actions. | Requires human/governance approval and strict audit. |
| `prohibited` | Not allowed for this agent. | Always blocked. |

## Shared Audit Requirements

Every agent response must include trace id, request id, agent name, department, workflow id where applicable, input refs, evidence refs, tools used, permission profile, policy version, prompt version if LLM is used, model route if LLM is used, decision path, environment, approval refs where required, and timestamp.

## Chronological Build Order

| Phase | Department / Layer | Why |
|---:|---|---|
| 0 | Foundation | Required by all other phases. |
| 1 | Research | Creates evidence; mostly read-only. |
| 2 | Strategy Development | Converts evidence into specifications, tests, and code candidates. |
| 3 | Simulation | Tests behavior, optimization, robustness, and statistical quality. |
| 4 | Validation & Backtesting Package | Reusable standalone validation package. |
| 5 | Risk | Decides whether candidates or high-impact actions may proceed. |
| 6 | Portfolio & Execution | Handles lifecycle, allocation, readiness, paper/live execution, bridge, and kill switch. |
| 7 | Operations & Audit | Monitors cost, performance, compliance, and operational health. |
| 8 | Dedicated Audit | Performs formal checklist-based audits. |

---

# Phase 0: Foundation: Shared Contracts, Runtime Layer, Control Plane, and Host

## Phase Dependency Position

Foundation has no domain dependency. It must exist before every department because it provides contracts, permissions, audit, runtime/model routing, tool execution, registry loading, approvals, state, and observability.

## Required Folders and Files

```text
agentic/agents/foundation/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/foundation/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/foundation_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/foundation/
registry/workflows/foundation_workflow.yaml
audit/reports/foundation/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/foundation_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/foundation/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- create shared services
- validate contracts
- enforce permissions
- write audit events

Blocked by default:

- perform department business decisions
- skip audit
- expose secrets

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
User/UI/API -> Host Router -> Planner -> Control Plane -> Department Workflow -> Evaluator -> Audit Log -> Final Response
```

## Department-Level Real-World Usage Examples

- Run the whole `Foundation: Shared Contracts, Runtime Layer, Control Plane, and Host` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### LLM Registry

**Purpose**

Maintains approved model/runtime profiles, model routing metadata, cost/latency limits, fallback rules, and environment eligibility.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- model task type
- environment
- budget/latency constraints
- fallback requirement

**Outputs**

- runtime profile
- model metadata
- fallback route
- usage policy

**Tools / Capabilities**

- model registry resource
- config loader

**Evidence Required**

- approved model catalog
- routing policy
- cost budget

**LLM Responsibilities**

- classify model task type
- summarize available profiles

**Deterministic Decision Rules**

- select only approved models
- production routes must have limits
- fallback must be explicit

**Allowed Actions**

- create shared services
- validate contracts
- enforce permissions
- write audit events

**Blocked Actions**

- perform department business decisions
- skip audit
- expose secrets

**Functional Checklist**

- Implements `agentic/agents/foundation/llm_registry/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `LLM Registry` alone with fixture input and verify a complete structured response.
- Ask `LLM Registry` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `LLM Registry` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/foundation/llm_registry/agent.py`
- `agentic/agents/foundation/llm_registry/prompt.md`
- `agentic/agents/foundation/llm_registry/manifest.yaml`
- `agentic/agents/foundation/llm_registry/schemas.py`
- `agentic/agents/foundation/llm_registry/README.md`
- `tests/agents/foundation/llm_registry/test_schemas.py`
- `tests/agents/foundation/llm_registry/test_agent.py`
- `tests/agents/foundation/llm_registry/test_policy.py`
- `tests/agents/foundation/llm_registry/test_permissions.py`
- `tests/agents/foundation/llm_registry/test_evaluator.py`
- `tests/agents/foundation/llm_registry/test_user_workflows.py`
- `registry/agents/foundation/llm_registry.yaml`
- `audit/reports/foundation/llm_registry_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Model Runtime Adapter

**Purpose**

Provides a generic framework-neutral boundary for model calls, structured outputs, usage tracking, and provider fallback.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- prompt
- model profile
- structured output schema
- context

**Outputs**

- model proposal
- usage metrics
- raw output reference
- schema validation status

**Tools / Capabilities**

- provider SDK adapter
- structured output validator

**Evidence Required**

- prompt version
- schema
- model profile

**LLM Responsibilities**

- generate analysis
- return JSON proposal

**Deterministic Decision Rules**

- validate output schema
- return structured errors
- load secrets only through approved config

**Allowed Actions**

- create shared services
- validate contracts
- enforce permissions
- write audit events

**Blocked Actions**

- perform department business decisions
- skip audit
- expose secrets

**Functional Checklist**

- Implements `agentic/agents/foundation/model_runtime_adapter/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Model Runtime Adapter` alone with fixture input and verify a complete structured response.
- Ask `Model Runtime Adapter` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Model Runtime Adapter` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/foundation/model_runtime_adapter/agent.py`
- `agentic/agents/foundation/model_runtime_adapter/prompt.md`
- `agentic/agents/foundation/model_runtime_adapter/manifest.yaml`
- `agentic/agents/foundation/model_runtime_adapter/schemas.py`
- `agentic/agents/foundation/model_runtime_adapter/README.md`
- `tests/agents/foundation/model_runtime_adapter/test_schemas.py`
- `tests/agents/foundation/model_runtime_adapter/test_agent.py`
- `tests/agents/foundation/model_runtime_adapter/test_policy.py`
- `tests/agents/foundation/model_runtime_adapter/test_permissions.py`
- `tests/agents/foundation/model_runtime_adapter/test_evaluator.py`
- `tests/agents/foundation/model_runtime_adapter/test_user_workflows.py`
- `registry/agents/foundation/model_runtime_adapter.yaml`
- `audit/reports/foundation/model_runtime_adapter_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Tool Executor

**Purpose**

Central permission-checked executor for tools, resources, prompts, adapters, and side-effecting capabilities.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- capability name
- arguments
- permission profile
- trace id

**Outputs**

- capability result
- audit event
- normalized error

**Tools / Capabilities**

- capability registry
- policy engine

**Evidence Required**

- capability manifest
- permission profile
- approval status

**LLM Responsibilities**

- none by default

**Deterministic Decision Rules**

- capability must be registered
- arguments must validate
- high-impact tools need approval

**Allowed Actions**

- create shared services
- validate contracts
- enforce permissions
- write audit events

**Blocked Actions**

- perform department business decisions
- skip audit
- expose secrets

**Functional Checklist**

- Implements `agentic/agents/foundation/tool_executor/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Tool Executor` alone with fixture input and verify a complete structured response.
- Ask `Tool Executor` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Tool Executor` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/foundation/tool_executor/agent.py`
- `agentic/agents/foundation/tool_executor/prompt.md`
- `agentic/agents/foundation/tool_executor/manifest.yaml`
- `agentic/agents/foundation/tool_executor/schemas.py`
- `agentic/agents/foundation/tool_executor/README.md`
- `tests/agents/foundation/tool_executor/test_schemas.py`
- `tests/agents/foundation/tool_executor/test_agent.py`
- `tests/agents/foundation/tool_executor/test_policy.py`
- `tests/agents/foundation/tool_executor/test_permissions.py`
- `tests/agents/foundation/tool_executor/test_evaluator.py`
- `tests/agents/foundation/tool_executor/test_user_workflows.py`
- `registry/agents/foundation/tool_executor.yaml`
- `audit/reports/foundation/tool_executor_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Execution Context

**Purpose**

Creates and carries run context across agents, workflows, tools, models, audit, and state.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- request
- session
- environment
- workflow metadata

**Outputs**

- context object
- trace ids
- state refs
- redacted context

**Tools / Capabilities**

- state store
- session manager
- redaction helper

**Evidence Required**

- request id
- environment
- tenant/user scope

**LLM Responsibilities**

- none by default

**Deterministic Decision Rules**

- every run needs trace id
- environment must be known
- context must be redacted before model use

**Allowed Actions**

- create shared services
- validate contracts
- enforce permissions
- write audit events

**Blocked Actions**

- perform department business decisions
- skip audit
- expose secrets

**Functional Checklist**

- Implements `agentic/agents/foundation/execution_context/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Execution Context` alone with fixture input and verify a complete structured response.
- Ask `Execution Context` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Execution Context` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/foundation/execution_context/agent.py`
- `agentic/agents/foundation/execution_context/prompt.md`
- `agentic/agents/foundation/execution_context/manifest.yaml`
- `agentic/agents/foundation/execution_context/schemas.py`
- `agentic/agents/foundation/execution_context/README.md`
- `tests/agents/foundation/execution_context/test_schemas.py`
- `tests/agents/foundation/execution_context/test_agent.py`
- `tests/agents/foundation/execution_context/test_policy.py`
- `tests/agents/foundation/execution_context/test_permissions.py`
- `tests/agents/foundation/execution_context/test_evaluator.py`
- `tests/agents/foundation/execution_context/test_user_workflows.py`
- `registry/agents/foundation/execution_context.yaml`
- `audit/reports/foundation/execution_context_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Planner Agent

**Purpose**

Classifies requests, identifies required department/workflow, missing inputs, evidence needs, permissions, and route.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- user goal
- current context
- available workflows
- permissions

**Outputs**

- plan
- department route
- missing inputs
- required evidence
- risk/control flags

**Tools / Capabilities**

- workflow registry
- agent registry
- policy checker

**Evidence Required**

- workflow catalog
- agent manifest registry
- input context

**LLM Responsibilities**

- intent classification
- task decomposition
- clarification drafting

**Deterministic Decision Rules**

- missing required inputs -> needs_clarification
- high-impact actions -> approval workflow
- only route to registered workflows

**Allowed Actions**

- create shared services
- validate contracts
- enforce permissions
- write audit events

**Blocked Actions**

- perform department business decisions
- skip audit
- expose secrets

**Functional Checklist**

- Implements `agentic/agents/foundation/planner_agent/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Planner Agent` alone with fixture input and verify a complete structured response.
- Ask `Planner Agent` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Planner Agent` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/foundation/planner_agent/agent.py`
- `agentic/agents/foundation/planner_agent/prompt.md`
- `agentic/agents/foundation/planner_agent/manifest.yaml`
- `agentic/agents/foundation/planner_agent/schemas.py`
- `agentic/agents/foundation/planner_agent/README.md`
- `tests/agents/foundation/planner_agent/test_schemas.py`
- `tests/agents/foundation/planner_agent/test_agent.py`
- `tests/agents/foundation/planner_agent/test_policy.py`
- `tests/agents/foundation/planner_agent/test_permissions.py`
- `tests/agents/foundation/planner_agent/test_evaluator.py`
- `tests/agents/foundation/planner_agent/test_user_workflows.py`
- `registry/agents/foundation/planner_agent.yaml`
- `audit/reports/foundation/planner_agent_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### AI CEO / CIO Agent

**Purpose**

Synthesizes final user-facing response from approved agent outputs, evidence, audit refs, and decisions.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- planner result
- agent responses
- audit refs
- user question

**Outputs**

- final memo
- summary
- next actions
- limitations

**Tools / Capabilities**

- response synthesizer
- evidence formatter

**Evidence Required**

- specialist responses
- audit records

**LLM Responsibilities**

- summarize and explain
- compare specialist outputs

**Deterministic Decision Rules**

- only summarize evidence-backed outputs
- surface blocked actions
- do not convert rejection to approval

**Allowed Actions**

- create shared services
- validate contracts
- enforce permissions
- write audit events

**Blocked Actions**

- perform department business decisions
- skip audit
- expose secrets

**Functional Checklist**

- Implements `agentic/agents/foundation/ai_ceo_cio_agent/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `AI CEO / CIO Agent` alone with fixture input and verify a complete structured response.
- Ask `AI CEO / CIO Agent` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `AI CEO / CIO Agent` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/foundation/ai_ceo_cio_agent/agent.py`
- `agentic/agents/foundation/ai_ceo_cio_agent/prompt.md`
- `agentic/agents/foundation/ai_ceo_cio_agent/manifest.yaml`
- `agentic/agents/foundation/ai_ceo_cio_agent/schemas.py`
- `agentic/agents/foundation/ai_ceo_cio_agent/README.md`
- `tests/agents/foundation/ai_ceo_cio_agent/test_schemas.py`
- `tests/agents/foundation/ai_ceo_cio_agent/test_agent.py`
- `tests/agents/foundation/ai_ceo_cio_agent/test_policy.py`
- `tests/agents/foundation/ai_ceo_cio_agent/test_permissions.py`
- `tests/agents/foundation/ai_ceo_cio_agent/test_evaluator.py`
- `tests/agents/foundation/ai_ceo_cio_agent/test_user_workflows.py`
- `registry/agents/foundation/ai_ceo_cio_agent.yaml`
- `audit/reports/foundation/ai_ceo_cio_agent_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Control Plane

**Purpose**

Coordinates registry loading, orchestration, state management, policy gates, approvals, operating mode, and tool governance.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- plan
- workflow id
- permission profile
- environment

**Outputs**

- authorized workflow run
- blocked decision
- approval request

**Tools / Capabilities**

- registry loader
- policy engine
- approval service
- state manager

**Evidence Required**

- registries
- policies
- approval records

**LLM Responsibilities**

- none by default

**Deterministic Decision Rules**

- fail closed on missing policy
- record every block/approval
- no direct side effects without tool executor

**Allowed Actions**

- create shared services
- validate contracts
- enforce permissions
- write audit events

**Blocked Actions**

- perform department business decisions
- skip audit
- expose secrets

**Functional Checklist**

- Implements `agentic/agents/foundation/control_plane/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Control Plane` alone with fixture input and verify a complete structured response.
- Ask `Control Plane` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Control Plane` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/foundation/control_plane/agent.py`
- `agentic/agents/foundation/control_plane/prompt.md`
- `agentic/agents/foundation/control_plane/manifest.yaml`
- `agentic/agents/foundation/control_plane/schemas.py`
- `agentic/agents/foundation/control_plane/README.md`
- `tests/agents/foundation/control_plane/test_schemas.py`
- `tests/agents/foundation/control_plane/test_agent.py`
- `tests/agents/foundation/control_plane/test_policy.py`
- `tests/agents/foundation/control_plane/test_permissions.py`
- `tests/agents/foundation/control_plane/test_evaluator.py`
- `tests/agents/foundation/control_plane/test_user_workflows.py`
- `registry/agents/foundation/control_plane.yaml`
- `audit/reports/foundation/control_plane_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Foundation: Shared Contracts, Runtime Layer, Control Plane, and Host Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.


# Phase 1: Research Department

## Phase Dependency Position

Research is mostly read-only and creates evidence for all downstream strategy, simulation, and risk work.

## Required Folders and Files

```text
agentic/agents/research/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/research/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/research_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/research/
registry/workflows/research_workflow.yaml
audit/reports/research/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/research_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/research/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- read sources
- analyze context
- create evidence
- handoff validated research

Blocked by default:

- execute actions
- approve lifecycle promotion
- invent evidence

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
Research Request -> Research Orchestrator -> Specialist Research Agents -> Evidence Curator -> Research Validation -> Research Evidence Package
```

## Department-Level Real-World Usage Examples

- Run the whole `Research Department` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### Research Orchestrator

**Purpose**

Coordinates research agents and produces a complete evidence package for downstream strategy/design workflows.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- research goal
- domain/entity/topic
- time window
- constraints

**Outputs**

- research evidence package
- research summary
- open questions
- handoff payload

**Tools / Capabilities**

- agent registry
- document search
- evidence store

**Evidence Required**

- current and historical sources
- agent outputs

**LLM Responsibilities**

- decompose research task
- summarize evidence
- identify gaps

**Deterministic Decision Rules**

- require evidence source
- mark stale evidence
- downgrade confidence on conflicts

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/research_orchestrator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Research Orchestrator` alone with fixture input and verify a complete structured response.
- Ask `Research Orchestrator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Research Orchestrator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/research_orchestrator/agent.py`
- `agentic/agents/research/research_orchestrator/prompt.md`
- `agentic/agents/research/research_orchestrator/manifest.yaml`
- `agentic/agents/research/research_orchestrator/schemas.py`
- `agentic/agents/research/research_orchestrator/README.md`
- `tests/agents/research/research_orchestrator/test_schemas.py`
- `tests/agents/research/research_orchestrator/test_agent.py`
- `tests/agents/research/research_orchestrator/test_policy.py`
- `tests/agents/research/research_orchestrator/test_permissions.py`
- `tests/agents/research/research_orchestrator/test_evaluator.py`
- `tests/agents/research/research_orchestrator/test_user_workflows.py`
- `registry/agents/research/research_orchestrator.yaml`
- `audit/reports/research/research_orchestrator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Market Intelligence

**Purpose**

Provides high-level situational context about the domain, environment, market, or system state.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- entity/topic
- time window
- context sources

**Outputs**

- context summary
- risk/opportunity flags
- freshness notes

**Tools / Capabilities**

- context resource
- approved external feeds

**Evidence Required**

- current context
- historical context
- source timestamps

**LLM Responsibilities**

- summarize context
- explain changes

**Deterministic Decision Rules**

- cite sources
- label current vs historical
- do not treat stale data as current

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/market_intelligence/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Market Intelligence` alone with fixture input and verify a complete structured response.
- Ask `Market Intelligence` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Market Intelligence` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/market_intelligence/agent.py`
- `agentic/agents/research/market_intelligence/prompt.md`
- `agentic/agents/research/market_intelligence/manifest.yaml`
- `agentic/agents/research/market_intelligence/schemas.py`
- `agentic/agents/research/market_intelligence/README.md`
- `tests/agents/research/market_intelligence/test_schemas.py`
- `tests/agents/research/market_intelligence/test_agent.py`
- `tests/agents/research/market_intelligence/test_policy.py`
- `tests/agents/research/market_intelligence/test_permissions.py`
- `tests/agents/research/market_intelligence/test_evaluator.py`
- `tests/agents/research/market_intelligence/test_user_workflows.py`
- `registry/agents/research/market_intelligence.yaml`
- `audit/reports/research/market_intelligence_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Technical Analyst

**Purpose**

Analyzes structured metrics, signals, features, patterns, or technical indicators relevant to the domain.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- structured dataset
- features/indicators
- analysis rules

**Outputs**

- technical analysis report
- signal flags
- limitations

**Tools / Capabilities**

- data query
- feature calculator
- statistics tool

**Evidence Required**

- validated dataset
- feature definitions
- analysis window

**LLM Responsibilities**

- interpret derived features
- explain signal meaning

**Deterministic Decision Rules**

- validate required columns
- reject insufficient data
- separate observation from recommendation

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/technical_analyst/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Technical Analyst` alone with fixture input and verify a complete structured response.
- Ask `Technical Analyst` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Technical Analyst` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/technical_analyst/agent.py`
- `agentic/agents/research/technical_analyst/prompt.md`
- `agentic/agents/research/technical_analyst/manifest.yaml`
- `agentic/agents/research/technical_analyst/schemas.py`
- `agentic/agents/research/technical_analyst/README.md`
- `tests/agents/research/technical_analyst/test_schemas.py`
- `tests/agents/research/technical_analyst/test_agent.py`
- `tests/agents/research/technical_analyst/test_policy.py`
- `tests/agents/research/technical_analyst/test_permissions.py`
- `tests/agents/research/technical_analyst/test_evaluator.py`
- `tests/agents/research/technical_analyst/test_user_workflows.py`
- `registry/agents/research/technical_analyst.yaml`
- `audit/reports/research/technical_analyst_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Hypothesis

**Purpose**

Turns research evidence into testable hypotheses for a strategy, workflow, product, or decision rule.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- evidence package
- problem statement
- constraints

**Outputs**

- hypothesis statement
- expected benefit
- assumptions
- invalidating conditions

**Tools / Capabilities**

- evidence store
- hypothesis template

**Evidence Required**

- research evidence
- negative evidence
- assumptions

**LLM Responsibilities**

- draft hypothesis
- list assumptions
- suggest tests

**Deterministic Decision Rules**

- hypothesis must be testable
- include invalidation criteria
- no validation claims

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/strategy_hypothesis/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Hypothesis` alone with fixture input and verify a complete structured response.
- Ask `Strategy Hypothesis` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Hypothesis` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/strategy_hypothesis/agent.py`
- `agentic/agents/research/strategy_hypothesis/prompt.md`
- `agentic/agents/research/strategy_hypothesis/manifest.yaml`
- `agentic/agents/research/strategy_hypothesis/schemas.py`
- `agentic/agents/research/strategy_hypothesis/README.md`
- `tests/agents/research/strategy_hypothesis/test_schemas.py`
- `tests/agents/research/strategy_hypothesis/test_agent.py`
- `tests/agents/research/strategy_hypothesis/test_policy.py`
- `tests/agents/research/strategy_hypothesis/test_permissions.py`
- `tests/agents/research/strategy_hypothesis/test_evaluator.py`
- `tests/agents/research/strategy_hypothesis/test_user_workflows.py`
- `registry/agents/research/strategy_hypothesis.yaml`
- `audit/reports/research/strategy_hypothesis_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Evidence Curator

**Purpose**

Collects, normalizes, scores, deduplicates, and packages evidence for later workflows.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- raw evidence refs
- source list
- curation rules

**Outputs**

- curated evidence list
- quality scores
- deduped refs
- source map

**Tools / Capabilities**

- document search
- evidence store
- hash/version tool

**Evidence Required**

- source metadata
- timestamps
- content snippets

**LLM Responsibilities**

- summarize relevance
- explain evidence quality

**Deterministic Decision Rules**

- keep source refs
- mark stale/low-quality evidence
- preserve contradictions

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/evidence_curator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Evidence Curator` alone with fixture input and verify a complete structured response.
- Ask `Evidence Curator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Evidence Curator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/evidence_curator/agent.py`
- `agentic/agents/research/evidence_curator/prompt.md`
- `agentic/agents/research/evidence_curator/manifest.yaml`
- `agentic/agents/research/evidence_curator/schemas.py`
- `agentic/agents/research/evidence_curator/README.md`
- `tests/agents/research/evidence_curator/test_schemas.py`
- `tests/agents/research/evidence_curator/test_agent.py`
- `tests/agents/research/evidence_curator/test_policy.py`
- `tests/agents/research/evidence_curator/test_permissions.py`
- `tests/agents/research/evidence_curator/test_evaluator.py`
- `tests/agents/research/evidence_curator/test_user_workflows.py`
- `registry/agents/research/evidence_curator.yaml`
- `audit/reports/research/evidence_curator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Macro / Fundamental Context

**Purpose**

Assesses broad external conditions, fundamental drivers, policy context, and macro-level constraints.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- topic/entity
- macro window
- source constraints

**Outputs**

- macro context report
- driver map
- risk flags

**Tools / Capabilities**

- approved news/docs
- calendar/event resource

**Evidence Required**

- macro events
- fundamental drivers
- policy notes

**LLM Responsibilities**

- summarize macro drivers
- explain relevance

**Deterministic Decision Rules**

- separate facts from interpretation
- cite timestamps
- flag uncertainty

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/macro_fundamental_context/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Macro / Fundamental Context` alone with fixture input and verify a complete structured response.
- Ask `Macro / Fundamental Context` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Macro / Fundamental Context` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/macro_fundamental_context/agent.py`
- `agentic/agents/research/macro_fundamental_context/prompt.md`
- `agentic/agents/research/macro_fundamental_context/manifest.yaml`
- `agentic/agents/research/macro_fundamental_context/schemas.py`
- `agentic/agents/research/macro_fundamental_context/README.md`
- `tests/agents/research/macro_fundamental_context/test_schemas.py`
- `tests/agents/research/macro_fundamental_context/test_agent.py`
- `tests/agents/research/macro_fundamental_context/test_policy.py`
- `tests/agents/research/macro_fundamental_context/test_permissions.py`
- `tests/agents/research/macro_fundamental_context/test_evaluator.py`
- `tests/agents/research/macro_fundamental_context/test_user_workflows.py`
- `registry/agents/research/macro_fundamental_context.yaml`
- `audit/reports/research/macro_fundamental_context_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Seasonality Calendar

**Purpose**

Identifies recurring calendar, seasonal, periodic, or schedule-based patterns.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- historical data
- calendar definitions
- aggregation frequency

**Outputs**

- seasonality report
- periodic stats
- confidence/limitations

**Tools / Capabilities**

- calendar resource
- statistics tool

**Evidence Required**

- historical observations
- calendar mappings
- sample size

**LLM Responsibilities**

- explain seasonal pattern
- draft narrative

**Deterministic Decision Rules**

- require sufficient sample size
- correlation not causation
- flag thin data

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/seasonality_calendar/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Seasonality Calendar` alone with fixture input and verify a complete structured response.
- Ask `Seasonality Calendar` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Seasonality Calendar` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/seasonality_calendar/agent.py`
- `agentic/agents/research/seasonality_calendar/prompt.md`
- `agentic/agents/research/seasonality_calendar/manifest.yaml`
- `agentic/agents/research/seasonality_calendar/schemas.py`
- `agentic/agents/research/seasonality_calendar/README.md`
- `tests/agents/research/seasonality_calendar/test_schemas.py`
- `tests/agents/research/seasonality_calendar/test_agent.py`
- `tests/agents/research/seasonality_calendar/test_policy.py`
- `tests/agents/research/seasonality_calendar/test_permissions.py`
- `tests/agents/research/seasonality_calendar/test_evaluator.py`
- `tests/agents/research/seasonality_calendar/test_user_workflows.py`
- `registry/agents/research/seasonality_calendar.yaml`
- `audit/reports/research/seasonality_calendar_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Scout

**Purpose**

Searches for candidate ideas, analogues, reusable templates, and prior patterns that fit the research evidence.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- research brief
- constraints
- search scope

**Outputs**

- candidate list
- fit rationale
- risks
- next tests

**Tools / Capabilities**

- document search
- template registry
- knowledge base

**Evidence Required**

- research evidence
- existing templates
- past results

**LLM Responsibilities**

- rank candidates
- explain fit

**Deterministic Decision Rules**

- reason for each candidate
- flag missing validation
- avoid duplicates

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/strategy_scout/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Scout` alone with fixture input and verify a complete structured response.
- Ask `Strategy Scout` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Scout` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/strategy_scout/agent.py`
- `agentic/agents/research/strategy_scout/prompt.md`
- `agentic/agents/research/strategy_scout/manifest.yaml`
- `agentic/agents/research/strategy_scout/schemas.py`
- `agentic/agents/research/strategy_scout/README.md`
- `tests/agents/research/strategy_scout/test_schemas.py`
- `tests/agents/research/strategy_scout/test_agent.py`
- `tests/agents/research/strategy_scout/test_policy.py`
- `tests/agents/research/strategy_scout/test_permissions.py`
- `tests/agents/research/strategy_scout/test_evaluator.py`
- `tests/agents/research/strategy_scout/test_user_workflows.py`
- `registry/agents/research/strategy_scout.yaml`
- `audit/reports/research/strategy_scout_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Research Validation

**Purpose**

Checks whether research evidence is consistent, supported, fresh, and ready for handoff.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- research package
- validation rubric

**Outputs**

- validation decision
- gaps
- pass/fail
- handoff readiness

**Tools / Capabilities**

- evaluator
- evidence store

**Evidence Required**

- research outputs
- source metadata
- rubric

**LLM Responsibilities**

- summarize quality issues
- suggest fixes

**Deterministic Decision Rules**

- fail missing evidence
- fail stale sources
- fail unresolved contradictions

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/research_validation/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Research Validation` alone with fixture input and verify a complete structured response.
- Ask `Research Validation` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Research Validation` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/research_validation/agent.py`
- `agentic/agents/research/research_validation/prompt.md`
- `agentic/agents/research/research_validation/manifest.yaml`
- `agentic/agents/research/research_validation/schemas.py`
- `agentic/agents/research/research_validation/README.md`
- `tests/agents/research/research_validation/test_schemas.py`
- `tests/agents/research/research_validation/test_agent.py`
- `tests/agents/research/research_validation/test_policy.py`
- `tests/agents/research/research_validation/test_permissions.py`
- `tests/agents/research/research_validation/test_evaluator.py`
- `tests/agents/research/research_validation/test_user_workflows.py`
- `registry/agents/research/research_validation.yaml`
- `audit/reports/research/research_validation_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### News Sentiment

**Purpose**

Summarizes current news, narrative, social/sentiment indicators, and event risk where relevant.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- topic/entity
- news window
- sentiment sources

**Outputs**

- sentiment snapshot
- news summary
- event risk flags

**Tools / Capabilities**

- approved news feed
- sentiment source
- calendar resource

**Evidence Required**

- news items
- sentiment metrics
- event calendar

**LLM Responsibilities**

- summarize sentiment
- cluster themes

**Deterministic Decision Rules**

- cite source/time
- separate news facts from sentiment
- label uncertainty

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/news_sentiment/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `News Sentiment` alone with fixture input and verify a complete structured response.
- Ask `News Sentiment` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `News Sentiment` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/news_sentiment/agent.py`
- `agentic/agents/research/news_sentiment/prompt.md`
- `agentic/agents/research/news_sentiment/manifest.yaml`
- `agentic/agents/research/news_sentiment/schemas.py`
- `agentic/agents/research/news_sentiment/README.md`
- `tests/agents/research/news_sentiment/test_schemas.py`
- `tests/agents/research/news_sentiment/test_agent.py`
- `tests/agents/research/news_sentiment/test_policy.py`
- `tests/agents/research/news_sentiment/test_permissions.py`
- `tests/agents/research/news_sentiment/test_evaluator.py`
- `tests/agents/research/news_sentiment/test_user_workflows.py`
- `registry/agents/research/news_sentiment.yaml`
- `audit/reports/research/news_sentiment_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Cross Asset / Intermarket

**Purpose**

Analyzes relationships between related entities, systems, markets, products, services, or external factors.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- primary entity
- related entities
- relationship window

**Outputs**

- relationship map
- correlation/interaction notes
- dependency flags

**Tools / Capabilities**

- data resource
- correlation/statistics tool

**Evidence Required**

- related series
- metadata
- time alignment

**LLM Responsibilities**

- explain relationships
- summarize dependency risk

**Deterministic Decision Rules**

- align timestamps
- require sufficient data
- correlation not causation

**Allowed Actions**

- read sources
- analyze context
- create evidence
- handoff validated research

**Blocked Actions**

- execute actions
- approve lifecycle promotion
- invent evidence

**Functional Checklist**

- Implements `agentic/agents/research/cross_asset_intermarket/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Cross Asset / Intermarket` alone with fixture input and verify a complete structured response.
- Ask `Cross Asset / Intermarket` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Cross Asset / Intermarket` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/research/cross_asset_intermarket/agent.py`
- `agentic/agents/research/cross_asset_intermarket/prompt.md`
- `agentic/agents/research/cross_asset_intermarket/manifest.yaml`
- `agentic/agents/research/cross_asset_intermarket/schemas.py`
- `agentic/agents/research/cross_asset_intermarket/README.md`
- `tests/agents/research/cross_asset_intermarket/test_schemas.py`
- `tests/agents/research/cross_asset_intermarket/test_agent.py`
- `tests/agents/research/cross_asset_intermarket/test_policy.py`
- `tests/agents/research/cross_asset_intermarket/test_permissions.py`
- `tests/agents/research/cross_asset_intermarket/test_evaluator.py`
- `tests/agents/research/cross_asset_intermarket/test_user_workflows.py`
- `registry/agents/research/cross_asset_intermarket.yaml`
- `audit/reports/research/cross_asset_intermarket_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Research Department Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.


# Phase 2: Strategy Development Department

## Phase Dependency Position

Strategy Development depends on validated research. It converts evidence into structured specifications, assumptions, test plans, code candidates, and handoff packages.

## Required Folders and Files

```text
agentic/agents/strategy_development/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/strategy_development/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/strategy_development_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/strategy_development/
registry/workflows/strategy_development_workflow.yaml
audit/reports/strategy_development/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/strategy_development_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/strategy_development/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- create specs
- normalize rules
- generate reviewed code
- create handoff

Blocked by default:

- claim validation
- deploy
- approve high-impact actions

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
Validated Research -> Strategy Orchestrator -> Creator/Validator/Normalizer/Template/Risk/Test/Cost -> Codegen -> Reviewer -> Storage -> Handoff
```

## Department-Level Real-World Usage Examples

- Run the whole `Strategy Development Department` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### Strategy Creation Orchestrator

**Purpose**

Coordinates strategy/design creation from validated research to structured specification and handoff.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- validated research package
- constraints
- target outcome

**Outputs**

- strategy creation plan
- subagent tasks
- handoff package

**Tools / Capabilities**

- workflow registry
- strategy spec store

**Evidence Required**

- validated research
- hypothesis
- constraints

**LLM Responsibilities**

- plan design tasks
- summarize requirements

**Deterministic Decision Rules**

- require validated research
- block missing constraints
- route spec through validator

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_creation_orchestrator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Creation Orchestrator` alone with fixture input and verify a complete structured response.
- Ask `Strategy Creation Orchestrator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Creation Orchestrator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_creation_orchestrator/agent.py`
- `agentic/agents/strategy_development/strategy_creation_orchestrator/prompt.md`
- `agentic/agents/strategy_development/strategy_creation_orchestrator/manifest.yaml`
- `agentic/agents/strategy_development/strategy_creation_orchestrator/schemas.py`
- `agentic/agents/strategy_development/strategy_creation_orchestrator/README.md`
- `tests/agents/strategy_development/strategy_creation_orchestrator/test_schemas.py`
- `tests/agents/strategy_development/strategy_creation_orchestrator/test_agent.py`
- `tests/agents/strategy_development/strategy_creation_orchestrator/test_policy.py`
- `tests/agents/strategy_development/strategy_creation_orchestrator/test_permissions.py`
- `tests/agents/strategy_development/strategy_creation_orchestrator/test_evaluator.py`
- `tests/agents/strategy_development/strategy_creation_orchestrator/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_creation_orchestrator.yaml`
- `audit/reports/strategy_development/strategy_creation_orchestrator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Creator

**Purpose**

Converts research hypotheses into a structured strategy, rule-system, or design proposal.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- hypothesis
- constraints
- allowed templates

**Outputs**

- strategy draft
- rules
- assumptions
- expected behavior

**Tools / Capabilities**

- template registry
- strategy spec schema

**Evidence Required**

- research package
- template constraints
- domain assumptions

**LLM Responsibilities**

- draft strategy rules
- explain rationale

**Deterministic Decision Rules**

- include triggers/exits/assumptions/invalidation
- no validation claims

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_creator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Creator` alone with fixture input and verify a complete structured response.
- Ask `Strategy Creator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Creator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_creator/agent.py`
- `agentic/agents/strategy_development/strategy_creator/prompt.md`
- `agentic/agents/strategy_development/strategy_creator/manifest.yaml`
- `agentic/agents/strategy_development/strategy_creator/schemas.py`
- `agentic/agents/strategy_development/strategy_creator/README.md`
- `tests/agents/strategy_development/strategy_creator/test_schemas.py`
- `tests/agents/strategy_development/strategy_creator/test_agent.py`
- `tests/agents/strategy_development/strategy_creator/test_policy.py`
- `tests/agents/strategy_development/strategy_creator/test_permissions.py`
- `tests/agents/strategy_development/strategy_creator/test_evaluator.py`
- `tests/agents/strategy_development/strategy_creator/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_creator.yaml`
- `audit/reports/strategy_development/strategy_creator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Spec Validator

**Purpose**

Validates a strategy specification for completeness, schema compliance, contradictions, and testability.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy spec
- validation rubric

**Outputs**

- validation result
- missing fields
- contradictions
- pass/fail

**Tools / Capabilities**

- schema validator
- policy checker

**Evidence Required**

- strategy spec
- domain constraints

**LLM Responsibilities**

- explain missing requirements

**Deterministic Decision Rules**

- fail missing required fields
- fail contradictory rules
- fail untestable vague logic

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_spec_validator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Spec Validator` alone with fixture input and verify a complete structured response.
- Ask `Strategy Spec Validator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Spec Validator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_spec_validator/agent.py`
- `agentic/agents/strategy_development/strategy_spec_validator/prompt.md`
- `agentic/agents/strategy_development/strategy_spec_validator/manifest.yaml`
- `agentic/agents/strategy_development/strategy_spec_validator/schemas.py`
- `agentic/agents/strategy_development/strategy_spec_validator/README.md`
- `tests/agents/strategy_development/strategy_spec_validator/test_schemas.py`
- `tests/agents/strategy_development/strategy_spec_validator/test_agent.py`
- `tests/agents/strategy_development/strategy_spec_validator/test_policy.py`
- `tests/agents/strategy_development/strategy_spec_validator/test_permissions.py`
- `tests/agents/strategy_development/strategy_spec_validator/test_evaluator.py`
- `tests/agents/strategy_development/strategy_spec_validator/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_spec_validator.yaml`
- `audit/reports/strategy_development/strategy_spec_validator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Rule Normalizer

**Purpose**

Normalizes rules into canonical, machine-readable, unambiguous form.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- raw rules
- canonical schema

**Outputs**

- normalized rules
- assumption map
- ambiguity list

**Tools / Capabilities**

- rule parser
- schema converter

**Evidence Required**

- source spec
- rule grammar

**LLM Responsibilities**

- clarify natural-language rules

**Deterministic Decision Rules**

- preserve intent
- flag ambiguity
- do not silently resolve critical ambiguity

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_rule_normalizer/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Rule Normalizer` alone with fixture input and verify a complete structured response.
- Ask `Strategy Rule Normalizer` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Rule Normalizer` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_rule_normalizer/agent.py`
- `agentic/agents/strategy_development/strategy_rule_normalizer/prompt.md`
- `agentic/agents/strategy_development/strategy_rule_normalizer/manifest.yaml`
- `agentic/agents/strategy_development/strategy_rule_normalizer/schemas.py`
- `agentic/agents/strategy_development/strategy_rule_normalizer/README.md`
- `tests/agents/strategy_development/strategy_rule_normalizer/test_schemas.py`
- `tests/agents/strategy_development/strategy_rule_normalizer/test_agent.py`
- `tests/agents/strategy_development/strategy_rule_normalizer/test_policy.py`
- `tests/agents/strategy_development/strategy_rule_normalizer/test_permissions.py`
- `tests/agents/strategy_development/strategy_rule_normalizer/test_evaluator.py`
- `tests/agents/strategy_development/strategy_rule_normalizer/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_rule_normalizer.yaml`
- `audit/reports/strategy_development/strategy_rule_normalizer_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Template Selector

**Purpose**

Selects the best implementation template architecture for the specification.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy spec
- available templates
- constraints

**Outputs**

- selected template
- rationale
- parameters

**Tools / Capabilities**

- template registry
- compatibility checker

**Evidence Required**

- strategy requirements
- template metadata

**LLM Responsibilities**

- compare templates
- explain tradeoffs

**Deterministic Decision Rules**

- choose only registered templates
- explain incompatibilities
- fail if no safe template

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_template_selector/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Template Selector` alone with fixture input and verify a complete structured response.
- Ask `Strategy Template Selector` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Template Selector` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_template_selector/agent.py`
- `agentic/agents/strategy_development/strategy_template_selector/prompt.md`
- `agentic/agents/strategy_development/strategy_template_selector/manifest.yaml`
- `agentic/agents/strategy_development/strategy_template_selector/schemas.py`
- `agentic/agents/strategy_development/strategy_template_selector/README.md`
- `tests/agents/strategy_development/strategy_template_selector/test_schemas.py`
- `tests/agents/strategy_development/strategy_template_selector/test_agent.py`
- `tests/agents/strategy_development/strategy_template_selector/test_policy.py`
- `tests/agents/strategy_development/strategy_template_selector/test_permissions.py`
- `tests/agents/strategy_development/strategy_template_selector/test_evaluator.py`
- `tests/agents/strategy_development/strategy_template_selector/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_template_selector.yaml`
- `audit/reports/strategy_development/strategy_template_selector_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Risk Assumption

**Purpose**

Documents risk, safety, operational, cost, and failure assumptions embedded in the strategy.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy spec
- research evidence
- domain constraints

**Outputs**

- risk assumption register
- control flags
- required tests

**Tools / Capabilities**

- policy resource
- assumption template

**Evidence Required**

- spec rules
- known constraints

**LLM Responsibilities**

- draft assumption register

**Deterministic Decision Rules**

- identify high-impact assumptions
- mark required control review
- do not approve assumptions

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_risk_assumption/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Risk Assumption` alone with fixture input and verify a complete structured response.
- Ask `Strategy Risk Assumption` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Risk Assumption` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_risk_assumption/agent.py`
- `agentic/agents/strategy_development/strategy_risk_assumption/prompt.md`
- `agentic/agents/strategy_development/strategy_risk_assumption/manifest.yaml`
- `agentic/agents/strategy_development/strategy_risk_assumption/schemas.py`
- `agentic/agents/strategy_development/strategy_risk_assumption/README.md`
- `tests/agents/strategy_development/strategy_risk_assumption/test_schemas.py`
- `tests/agents/strategy_development/strategy_risk_assumption/test_agent.py`
- `tests/agents/strategy_development/strategy_risk_assumption/test_policy.py`
- `tests/agents/strategy_development/strategy_risk_assumption/test_permissions.py`
- `tests/agents/strategy_development/strategy_risk_assumption/test_evaluator.py`
- `tests/agents/strategy_development/strategy_risk_assumption/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_risk_assumption.yaml`
- `audit/reports/strategy_development/strategy_risk_assumption_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Test Plan

**Purpose**

Creates the tests needed to prove the strategy/spec behaves correctly and is worth simulating.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy spec
- risk assumptions
- success metrics

**Outputs**

- test plan
- unit tests
- scenario tests
- evaluation metrics

**Tools / Capabilities**

- test template registry
- benchmark catalog

**Evidence Required**

- spec
- risk assumptions
- acceptance criteria

**LLM Responsibilities**

- suggest scenarios
- summarize coverage

**Deterministic Decision Rules**

- include normal/edge/failure/adversarial/regression tests
- link tests to rules

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_test_plan/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Test Plan` alone with fixture input and verify a complete structured response.
- Ask `Strategy Test Plan` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Test Plan` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_test_plan/agent.py`
- `agentic/agents/strategy_development/strategy_test_plan/prompt.md`
- `agentic/agents/strategy_development/strategy_test_plan/manifest.yaml`
- `agentic/agents/strategy_development/strategy_test_plan/schemas.py`
- `agentic/agents/strategy_development/strategy_test_plan/README.md`
- `tests/agents/strategy_development/strategy_test_plan/test_schemas.py`
- `tests/agents/strategy_development/strategy_test_plan/test_agent.py`
- `tests/agents/strategy_development/strategy_test_plan/test_policy.py`
- `tests/agents/strategy_development/strategy_test_plan/test_permissions.py`
- `tests/agents/strategy_development/strategy_test_plan/test_evaluator.py`
- `tests/agents/strategy_development/strategy_test_plan/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_test_plan.yaml`
- `audit/reports/strategy_development/strategy_test_plan_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Cost Execution

**Purpose**

Estimates operational cost, latency, compute, integration burden, and execution feasibility.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy spec
- runtime assumptions
- expected volume

**Outputs**

- cost estimate
- latency estimate
- feasibility risk

**Tools / Capabilities**

- cost model
- runtime registry

**Evidence Required**

- expected workload
- tool/model costs

**LLM Responsibilities**

- explain cost drivers

**Deterministic Decision Rules**

- include uncertainty
- flag costs above budget
- do not hide expensive paths

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_cost_execution/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Cost Execution` alone with fixture input and verify a complete structured response.
- Ask `Strategy Cost Execution` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Cost Execution` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_cost_execution/agent.py`
- `agentic/agents/strategy_development/strategy_cost_execution/prompt.md`
- `agentic/agents/strategy_development/strategy_cost_execution/manifest.yaml`
- `agentic/agents/strategy_development/strategy_cost_execution/schemas.py`
- `agentic/agents/strategy_development/strategy_cost_execution/README.md`
- `tests/agents/strategy_development/strategy_cost_execution/test_schemas.py`
- `tests/agents/strategy_development/strategy_cost_execution/test_agent.py`
- `tests/agents/strategy_development/strategy_cost_execution/test_policy.py`
- `tests/agents/strategy_development/strategy_cost_execution/test_permissions.py`
- `tests/agents/strategy_development/strategy_cost_execution/test_evaluator.py`
- `tests/agents/strategy_development/strategy_cost_execution/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_cost_execution.yaml`
- `audit/reports/strategy_development/strategy_cost_execution_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Codegen

**Purpose**

Generates implementation code or configuration from a validated, normalized specification.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- validated spec
- template
- coding standards

**Outputs**

- generated code
- artifact refs
- implementation notes

**Tools / Capabilities**

- code template registry
- formatter
- static analyzer

**Evidence Required**

- validated spec
- template files

**LLM Responsibilities**

- generate code draft
- explain code

**Deterministic Decision Rules**

- generate only from validated spec
- pass lint/static checks
- never include secrets

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_codegen/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Codegen` alone with fixture input and verify a complete structured response.
- Ask `Strategy Codegen` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Codegen` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_codegen/agent.py`
- `agentic/agents/strategy_development/strategy_codegen/prompt.md`
- `agentic/agents/strategy_development/strategy_codegen/manifest.yaml`
- `agentic/agents/strategy_development/strategy_codegen/schemas.py`
- `agentic/agents/strategy_development/strategy_codegen/README.md`
- `tests/agents/strategy_development/strategy_codegen/test_schemas.py`
- `tests/agents/strategy_development/strategy_codegen/test_agent.py`
- `tests/agents/strategy_development/strategy_codegen/test_policy.py`
- `tests/agents/strategy_development/strategy_codegen/test_permissions.py`
- `tests/agents/strategy_development/strategy_codegen/test_evaluator.py`
- `tests/agents/strategy_development/strategy_codegen/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_codegen.yaml`
- `audit/reports/strategy_development/strategy_codegen_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Reviewer

**Purpose**

Reviews spec/code for correctness, maintainability, safety, test coverage, and audit readiness.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy spec
- code artifact
- test plan

**Outputs**

- review result
- issues
- approval recommendation
- required fixes

**Tools / Capabilities**

- static analyzer
- schema validator
- policy checker

**Evidence Required**

- code
- spec
- tests
- policy

**LLM Responsibilities**

- explain review issues
- suggest fixes

**Deterministic Decision Rules**

- fail code/spec divergence
- fail missing tests
- flag safety bypasses

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_reviewer/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Reviewer` alone with fixture input and verify a complete structured response.
- Ask `Strategy Reviewer` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Reviewer` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_reviewer/agent.py`
- `agentic/agents/strategy_development/strategy_reviewer/prompt.md`
- `agentic/agents/strategy_development/strategy_reviewer/manifest.yaml`
- `agentic/agents/strategy_development/strategy_reviewer/schemas.py`
- `agentic/agents/strategy_development/strategy_reviewer/README.md`
- `tests/agents/strategy_development/strategy_reviewer/test_schemas.py`
- `tests/agents/strategy_development/strategy_reviewer/test_agent.py`
- `tests/agents/strategy_development/strategy_reviewer/test_policy.py`
- `tests/agents/strategy_development/strategy_reviewer/test_permissions.py`
- `tests/agents/strategy_development/strategy_reviewer/test_evaluator.py`
- `tests/agents/strategy_development/strategy_reviewer/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_reviewer.yaml`
- `audit/reports/strategy_development/strategy_reviewer_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Spec Storage

**Purpose**

Stores versioned strategy specifications and metadata after validation.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- validated spec
- metadata
- version

**Outputs**

- stored spec ref
- version id
- audit record

**Tools / Capabilities**

- artifact store
- versioning service

**Evidence Required**

- validated spec
- approval status

**LLM Responsibilities**

- summarize storage status

**Deterministic Decision Rules**

- versioned writes
- no silent overwrite
- preserve audit links

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_spec_storage/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Spec Storage` alone with fixture input and verify a complete structured response.
- Ask `Strategy Spec Storage` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Spec Storage` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_spec_storage/agent.py`
- `agentic/agents/strategy_development/strategy_spec_storage/prompt.md`
- `agentic/agents/strategy_development/strategy_spec_storage/manifest.yaml`
- `agentic/agents/strategy_development/strategy_spec_storage/schemas.py`
- `agentic/agents/strategy_development/strategy_spec_storage/README.md`
- `tests/agents/strategy_development/strategy_spec_storage/test_schemas.py`
- `tests/agents/strategy_development/strategy_spec_storage/test_agent.py`
- `tests/agents/strategy_development/strategy_spec_storage/test_policy.py`
- `tests/agents/strategy_development/strategy_spec_storage/test_permissions.py`
- `tests/agents/strategy_development/strategy_spec_storage/test_evaluator.py`
- `tests/agents/strategy_development/strategy_spec_storage/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_spec_storage.yaml`
- `audit/reports/strategy_development/strategy_spec_storage_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Code Storage

**Purpose**

Stores versioned generated code artifacts after review and test readiness.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- code artifact
- review result
- metadata

**Outputs**

- stored code ref
- version id
- audit record

**Tools / Capabilities**

- artifact store
- hash/versioning tool

**Evidence Required**

- code files
- review result

**LLM Responsibilities**

- summarize storage status

**Deterministic Decision Rules**

- only reviewed artifacts become candidates
- record hash/version
- no secret storage

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_code_storage/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Code Storage` alone with fixture input and verify a complete structured response.
- Ask `Strategy Code Storage` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Code Storage` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_code_storage/agent.py`
- `agentic/agents/strategy_development/strategy_code_storage/prompt.md`
- `agentic/agents/strategy_development/strategy_code_storage/manifest.yaml`
- `agentic/agents/strategy_development/strategy_code_storage/schemas.py`
- `agentic/agents/strategy_development/strategy_code_storage/README.md`
- `tests/agents/strategy_development/strategy_code_storage/test_schemas.py`
- `tests/agents/strategy_development/strategy_code_storage/test_agent.py`
- `tests/agents/strategy_development/strategy_code_storage/test_policy.py`
- `tests/agents/strategy_development/strategy_code_storage/test_permissions.py`
- `tests/agents/strategy_development/strategy_code_storage/test_evaluator.py`
- `tests/agents/strategy_development/strategy_code_storage/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_code_storage.yaml`
- `audit/reports/strategy_development/strategy_code_storage_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Handoff

**Purpose**

Creates a clean handoff package from Strategy Development to Simulation/Validation.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- spec ref
- code ref
- test plan
- assumptions

**Outputs**

- handoff package
- simulation readiness decision

**Tools / Capabilities**

- artifact store
- handoff schema validator

**Evidence Required**

- spec
- code
- test plan
- risk assumptions

**LLM Responsibilities**

- summarize handoff

**Deterministic Decision Rules**

- require spec/code/test plan/assumptions
- fail incomplete handoff

**Allowed Actions**

- create specs
- normalize rules
- generate reviewed code
- create handoff

**Blocked Actions**

- claim validation
- deploy
- approve high-impact actions

**Functional Checklist**

- Implements `agentic/agents/strategy_development/strategy_handoff/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Handoff` alone with fixture input and verify a complete structured response.
- Ask `Strategy Handoff` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Handoff` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/strategy_development/strategy_handoff/agent.py`
- `agentic/agents/strategy_development/strategy_handoff/prompt.md`
- `agentic/agents/strategy_development/strategy_handoff/manifest.yaml`
- `agentic/agents/strategy_development/strategy_handoff/schemas.py`
- `agentic/agents/strategy_development/strategy_handoff/README.md`
- `tests/agents/strategy_development/strategy_handoff/test_schemas.py`
- `tests/agents/strategy_development/strategy_handoff/test_agent.py`
- `tests/agents/strategy_development/strategy_handoff/test_policy.py`
- `tests/agents/strategy_development/strategy_handoff/test_permissions.py`
- `tests/agents/strategy_development/strategy_handoff/test_evaluator.py`
- `tests/agents/strategy_development/strategy_handoff/test_user_workflows.py`
- `registry/agents/strategy_development/strategy_handoff.yaml`
- `audit/reports/strategy_development/strategy_handoff_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Strategy Development Department Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.


# Phase 3: Simulation Department

## Phase Dependency Position

Simulation depends on complete strategy handoff packages. It verifies behavior, optimization sensitivity, robustness, and statistical validity before risk review.

## Required Folders and Files

```text
agentic/agents/simulation/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/simulation/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/simulation_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/simulation/
registry/workflows/simulation_workflow.yaml
audit/reports/simulation/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/simulation_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/simulation/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- run simulations
- analyze metrics
- curate results
- handoff evidence

Blocked by default:

- change strategy intent
- approve production
- hide failed results

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
Strategy Handoff -> Simulation Orchestrator -> Backtest -> Analyst -> Optimization -> Comparator -> Robustness -> Statistical Validation -> Evidence Curator
```

## Department-Level Real-World Usage Examples

- Run the whole `Simulation Department` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### Simulation Orchestrator

**Purpose**

Coordinates simulation, optimization, robustness, and statistical validation runs.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- simulation handoff package
- test plan
- data/config refs

**Outputs**

- simulation plan
- run ids
- assignments
- summary

**Tools / Capabilities**

- simulation engine adapter
- artifact store

**Evidence Required**

- validated spec/code
- test plan
- data refs

**LLM Responsibilities**

- plan simulation sequence
- summarize run results

**Deterministic Decision Rules**

- require complete handoff
- record data/config versions
- fail missing reproducibility inputs

**Allowed Actions**

- run simulations
- analyze metrics
- curate results
- handoff evidence

**Blocked Actions**

- change strategy intent
- approve production
- hide failed results

**Functional Checklist**

- Implements `agentic/agents/simulation/simulation_orchestrator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Simulation Orchestrator` alone with fixture input and verify a complete structured response.
- Ask `Simulation Orchestrator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Simulation Orchestrator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/simulation/simulation_orchestrator/agent.py`
- `agentic/agents/simulation/simulation_orchestrator/prompt.md`
- `agentic/agents/simulation/simulation_orchestrator/manifest.yaml`
- `agentic/agents/simulation/simulation_orchestrator/schemas.py`
- `agentic/agents/simulation/simulation_orchestrator/README.md`
- `tests/agents/simulation/simulation_orchestrator/test_schemas.py`
- `tests/agents/simulation/simulation_orchestrator/test_agent.py`
- `tests/agents/simulation/simulation_orchestrator/test_policy.py`
- `tests/agents/simulation/simulation_orchestrator/test_permissions.py`
- `tests/agents/simulation/simulation_orchestrator/test_evaluator.py`
- `tests/agents/simulation/simulation_orchestrator/test_user_workflows.py`
- `registry/agents/simulation/simulation_orchestrator.yaml`
- `audit/reports/simulation/simulation_orchestrator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Backtest

**Purpose**

Runs deterministic historical/simulated execution or scenario tests against the artifact.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy artifact
- data refs
- execution config
- test cases

**Outputs**

- backtest results
- metrics
- logs
- artifact refs

**Tools / Capabilities**

- simulation engine
- data loader
- metrics calculator

**Evidence Required**

- versioned data
- strategy code/spec
- config

**LLM Responsibilities**

- none by default

**Deterministic Decision Rules**

- record data version
- record config
- reproducible result
- reject invalid data

**Allowed Actions**

- run simulations
- analyze metrics
- curate results
- handoff evidence

**Blocked Actions**

- change strategy intent
- approve production
- hide failed results

**Functional Checklist**

- Implements `agentic/agents/simulation/backtest/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Backtest` alone with fixture input and verify a complete structured response.
- Ask `Backtest` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Backtest` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/simulation/backtest/agent.py`
- `agentic/agents/simulation/backtest/prompt.md`
- `agentic/agents/simulation/backtest/manifest.yaml`
- `agentic/agents/simulation/backtest/schemas.py`
- `agentic/agents/simulation/backtest/README.md`
- `tests/agents/simulation/backtest/test_schemas.py`
- `tests/agents/simulation/backtest/test_agent.py`
- `tests/agents/simulation/backtest/test_policy.py`
- `tests/agents/simulation/backtest/test_permissions.py`
- `tests/agents/simulation/backtest/test_evaluator.py`
- `tests/agents/simulation/backtest/test_user_workflows.py`
- `registry/agents/simulation/backtest.yaml`
- `audit/reports/simulation/backtest_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Backtest Analyst

**Purpose**

Analyzes results and explains performance, behavior, failure modes, and anomalies.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- backtest result refs
- metrics
- test plan

**Outputs**

- analysis report
- anomaly flags
- pass/fail recommendation

**Tools / Capabilities**

- metrics reader
- artifact store

**Evidence Required**

- backtest metrics
- logs
- test expectations

**LLM Responsibilities**

- explain results
- summarize anomalies

**Deterministic Decision Rules**

- do not invent metrics
- cite artifact refs
- flag failed tests

**Allowed Actions**

- run simulations
- analyze metrics
- curate results
- handoff evidence

**Blocked Actions**

- change strategy intent
- approve production
- hide failed results

**Functional Checklist**

- Implements `agentic/agents/simulation/backtest_analyst/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Backtest Analyst` alone with fixture input and verify a complete structured response.
- Ask `Backtest Analyst` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Backtest Analyst` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/simulation/backtest_analyst/agent.py`
- `agentic/agents/simulation/backtest_analyst/prompt.md`
- `agentic/agents/simulation/backtest_analyst/manifest.yaml`
- `agentic/agents/simulation/backtest_analyst/schemas.py`
- `agentic/agents/simulation/backtest_analyst/README.md`
- `tests/agents/simulation/backtest_analyst/test_schemas.py`
- `tests/agents/simulation/backtest_analyst/test_agent.py`
- `tests/agents/simulation/backtest_analyst/test_policy.py`
- `tests/agents/simulation/backtest_analyst/test_permissions.py`
- `tests/agents/simulation/backtest_analyst/test_evaluator.py`
- `tests/agents/simulation/backtest_analyst/test_user_workflows.py`
- `registry/agents/simulation/backtest_analyst.yaml`
- `audit/reports/simulation/backtest_analyst_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Optimization

**Purpose**

Runs controlled parameter/config optimization within an approved search space.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy artifact
- search space
- objective
- constraints

**Outputs**

- optimization results
- candidate variants
- overfit warnings

**Tools / Capabilities**

- optimization engine
- metrics calculator

**Evidence Required**

- search space
- data refs
- objective function

**LLM Responsibilities**

- summarize tradeoffs
- explain ranking

**Deterministic Decision Rules**

- declare search space
- record parameters
- separate optimization from validation data

**Allowed Actions**

- run simulations
- analyze metrics
- curate results
- handoff evidence

**Blocked Actions**

- change strategy intent
- approve production
- hide failed results

**Functional Checklist**

- Implements `agentic/agents/simulation/optimization/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Optimization` alone with fixture input and verify a complete structured response.
- Ask `Optimization` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Optimization` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/simulation/optimization/agent.py`
- `agentic/agents/simulation/optimization/prompt.md`
- `agentic/agents/simulation/optimization/manifest.yaml`
- `agentic/agents/simulation/optimization/schemas.py`
- `agentic/agents/simulation/optimization/README.md`
- `tests/agents/simulation/optimization/test_schemas.py`
- `tests/agents/simulation/optimization/test_agent.py`
- `tests/agents/simulation/optimization/test_policy.py`
- `tests/agents/simulation/optimization/test_permissions.py`
- `tests/agents/simulation/optimization/test_evaluator.py`
- `tests/agents/simulation/optimization/test_user_workflows.py`
- `registry/agents/simulation/optimization.yaml`
- `audit/reports/simulation/optimization_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Optimization Comparator

**Purpose**

Compares optimization candidates and selects candidates for robustness/validation using deterministic criteria.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- optimization results
- selection criteria

**Outputs**

- comparison report
- selected candidates
- rejection reasons

**Tools / Capabilities**

- metrics comparator
- artifact store

**Evidence Required**

- variant metrics
- criteria

**LLM Responsibilities**

- explain comparison

**Deterministic Decision Rules**

- use declared criteria
- record rejection reasons
- flag fragile winners

**Allowed Actions**

- run simulations
- analyze metrics
- curate results
- handoff evidence

**Blocked Actions**

- change strategy intent
- approve production
- hide failed results

**Functional Checklist**

- Implements `agentic/agents/simulation/optimization_comparator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Optimization Comparator` alone with fixture input and verify a complete structured response.
- Ask `Optimization Comparator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Optimization Comparator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/simulation/optimization_comparator/agent.py`
- `agentic/agents/simulation/optimization_comparator/prompt.md`
- `agentic/agents/simulation/optimization_comparator/manifest.yaml`
- `agentic/agents/simulation/optimization_comparator/schemas.py`
- `agentic/agents/simulation/optimization_comparator/README.md`
- `tests/agents/simulation/optimization_comparator/test_schemas.py`
- `tests/agents/simulation/optimization_comparator/test_agent.py`
- `tests/agents/simulation/optimization_comparator/test_policy.py`
- `tests/agents/simulation/optimization_comparator/test_permissions.py`
- `tests/agents/simulation/optimization_comparator/test_evaluator.py`
- `tests/agents/simulation/optimization_comparator/test_user_workflows.py`
- `registry/agents/simulation/optimization_comparator.yaml`
- `audit/reports/simulation/optimization_comparator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Robustness

**Purpose**

Runs stress, perturbation, Monte Carlo, cross-scenario, and failure-mode tests.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- candidate artifact
- robustness test plan
- data/config refs

**Outputs**

- robustness report
- stress results
- failure modes

**Tools / Capabilities**

- robustness engine
- scenario generator

**Evidence Required**

- candidate strategy
- test plan
- random seeds

**LLM Responsibilities**

- summarize stress results

**Deterministic Decision Rules**

- fixed seeds where applicable
- record scenarios
- fail below threshold

**Allowed Actions**

- run simulations
- analyze metrics
- curate results
- handoff evidence

**Blocked Actions**

- change strategy intent
- approve production
- hide failed results

**Functional Checklist**

- Implements `agentic/agents/simulation/robustness/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Robustness` alone with fixture input and verify a complete structured response.
- Ask `Robustness` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Robustness` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/simulation/robustness/agent.py`
- `agentic/agents/simulation/robustness/prompt.md`
- `agentic/agents/simulation/robustness/manifest.yaml`
- `agentic/agents/simulation/robustness/schemas.py`
- `agentic/agents/simulation/robustness/README.md`
- `tests/agents/simulation/robustness/test_schemas.py`
- `tests/agents/simulation/robustness/test_agent.py`
- `tests/agents/simulation/robustness/test_policy.py`
- `tests/agents/simulation/robustness/test_permissions.py`
- `tests/agents/simulation/robustness/test_evaluator.py`
- `tests/agents/simulation/robustness/test_user_workflows.py`
- `registry/agents/simulation/robustness.yaml`
- `audit/reports/simulation/robustness_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Statistical Validation

**Purpose**

Applies statistical checks to determine whether results are reliable enough for downstream control review.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- simulation metrics
- robustness results
- statistical thresholds

**Outputs**

- statistical decision
- confidence
- limitations

**Tools / Capabilities**

- statistical test library
- metrics store

**Evidence Required**

- metrics distributions
- sample sizes
- thresholds

**LLM Responsibilities**

- explain statistical confidence

**Deterministic Decision Rules**

- require sufficient sample size
- flag multiple testing
- fail unsupported claims

**Allowed Actions**

- run simulations
- analyze metrics
- curate results
- handoff evidence

**Blocked Actions**

- change strategy intent
- approve production
- hide failed results

**Functional Checklist**

- Implements `agentic/agents/simulation/statistical_validation/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Statistical Validation` alone with fixture input and verify a complete structured response.
- Ask `Statistical Validation` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Statistical Validation` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/simulation/statistical_validation/agent.py`
- `agentic/agents/simulation/statistical_validation/prompt.md`
- `agentic/agents/simulation/statistical_validation/manifest.yaml`
- `agentic/agents/simulation/statistical_validation/schemas.py`
- `agentic/agents/simulation/statistical_validation/README.md`
- `tests/agents/simulation/statistical_validation/test_schemas.py`
- `tests/agents/simulation/statistical_validation/test_agent.py`
- `tests/agents/simulation/statistical_validation/test_policy.py`
- `tests/agents/simulation/statistical_validation/test_permissions.py`
- `tests/agents/simulation/statistical_validation/test_evaluator.py`
- `tests/agents/simulation/statistical_validation/test_user_workflows.py`
- `registry/agents/simulation/statistical_validation.yaml`
- `audit/reports/simulation/statistical_validation_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Simulation Evidence Curator

**Purpose**

Curates simulation artifacts, metrics, config, logs, and validation outputs for downstream risk review.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- simulation outputs
- artifact refs
- validation reports

**Outputs**

- curated evidence package
- quality scores
- handoff payload

**Tools / Capabilities**

- artifact store
- evidence store

**Evidence Required**

- run ids
- metrics
- config snapshots

**LLM Responsibilities**

- summarize evidence package

**Deterministic Decision Rules**

- preserve run ids
- record failed tests
- do not hide poor results

**Allowed Actions**

- run simulations
- analyze metrics
- curate results
- handoff evidence

**Blocked Actions**

- change strategy intent
- approve production
- hide failed results

**Functional Checklist**

- Implements `agentic/agents/simulation/simulation_evidence_curator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Simulation Evidence Curator` alone with fixture input and verify a complete structured response.
- Ask `Simulation Evidence Curator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Simulation Evidence Curator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/simulation/simulation_evidence_curator/agent.py`
- `agentic/agents/simulation/simulation_evidence_curator/prompt.md`
- `agentic/agents/simulation/simulation_evidence_curator/manifest.yaml`
- `agentic/agents/simulation/simulation_evidence_curator/schemas.py`
- `agentic/agents/simulation/simulation_evidence_curator/README.md`
- `tests/agents/simulation/simulation_evidence_curator/test_schemas.py`
- `tests/agents/simulation/simulation_evidence_curator/test_agent.py`
- `tests/agents/simulation/simulation_evidence_curator/test_policy.py`
- `tests/agents/simulation/simulation_evidence_curator/test_permissions.py`
- `tests/agents/simulation/simulation_evidence_curator/test_evaluator.py`
- `tests/agents/simulation/simulation_evidence_curator/test_user_workflows.py`
- `registry/agents/simulation/simulation_evidence_curator.yaml`
- `audit/reports/simulation/simulation_evidence_curator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Simulation Department Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.


# Phase 4: Validation & Backtesting Package

## Phase Dependency Position

This package is a reusable standalone validation layer. It can be used independently or by the Simulation Department for smaller validation flows.

## Required Folders and Files

```text
agentic/agents/validation_backtesting/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/validation_backtesting/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/validation_backtesting_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/validation_backtesting/
registry/workflows/validation_backtesting_workflow.yaml
audit/reports/validation_backtesting/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/validation_backtesting_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/validation_backtesting/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- run standalone validation
- compare candidates
- produce validation package

Blocked by default:

- replace risk approval
- promote lifecycle
- alter results

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
Standalone Validation Request -> Backtest -> Optimization Comparator -> Robustness Monte Carlo -> Statistical Validation -> Validation Report
```

## Department-Level Real-World Usage Examples

- Run the whole `Validation & Backtesting Package` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### Validation Backtest

**Purpose**

Reusable standalone validation backtest interface.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- strategy artifact
- validation dataset
- config

**Outputs**

- validation result
- metrics
- run refs

**Tools / Capabilities**

- backtest engine

**Evidence Required**

- strategy artifact
- dataset refs

**LLM Responsibilities**

- none by default

**Deterministic Decision Rules**

- reproducible
- record data/config
- reject invalid dataset

**Allowed Actions**

- run standalone validation
- compare candidates
- produce validation package

**Blocked Actions**

- replace risk approval
- promote lifecycle
- alter results

**Functional Checklist**

- Implements `agentic/agents/validation_backtesting/validation_backtest/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Validation Backtest` alone with fixture input and verify a complete structured response.
- Ask `Validation Backtest` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Validation Backtest` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/validation_backtesting/validation_backtest/agent.py`
- `agentic/agents/validation_backtesting/validation_backtest/prompt.md`
- `agentic/agents/validation_backtesting/validation_backtest/manifest.yaml`
- `agentic/agents/validation_backtesting/validation_backtest/schemas.py`
- `agentic/agents/validation_backtesting/validation_backtest/README.md`
- `tests/agents/validation_backtesting/validation_backtest/test_schemas.py`
- `tests/agents/validation_backtesting/validation_backtest/test_agent.py`
- `tests/agents/validation_backtesting/validation_backtest/test_policy.py`
- `tests/agents/validation_backtesting/validation_backtest/test_permissions.py`
- `tests/agents/validation_backtesting/validation_backtest/test_evaluator.py`
- `tests/agents/validation_backtesting/validation_backtest/test_user_workflows.py`
- `registry/agents/validation_backtesting/validation_backtest.yaml`
- `audit/reports/validation_backtesting/validation_backtest_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Validation Optimization Comparator

**Purpose**

Standalone comparator for optimization outputs.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- candidate metrics
- criteria

**Outputs**

- comparison result
- selected candidates

**Tools / Capabilities**

- metrics comparator

**Evidence Required**

- candidate metrics

**LLM Responsibilities**

- explain comparison

**Deterministic Decision Rules**

- criteria declared
- flag fragile candidates

**Allowed Actions**

- run standalone validation
- compare candidates
- produce validation package

**Blocked Actions**

- replace risk approval
- promote lifecycle
- alter results

**Functional Checklist**

- Implements `agentic/agents/validation_backtesting/validation_optimization_comparator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Validation Optimization Comparator` alone with fixture input and verify a complete structured response.
- Ask `Validation Optimization Comparator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Validation Optimization Comparator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/validation_backtesting/validation_optimization_comparator/agent.py`
- `agentic/agents/validation_backtesting/validation_optimization_comparator/prompt.md`
- `agentic/agents/validation_backtesting/validation_optimization_comparator/manifest.yaml`
- `agentic/agents/validation_backtesting/validation_optimization_comparator/schemas.py`
- `agentic/agents/validation_backtesting/validation_optimization_comparator/README.md`
- `tests/agents/validation_backtesting/validation_optimization_comparator/test_schemas.py`
- `tests/agents/validation_backtesting/validation_optimization_comparator/test_agent.py`
- `tests/agents/validation_backtesting/validation_optimization_comparator/test_policy.py`
- `tests/agents/validation_backtesting/validation_optimization_comparator/test_permissions.py`
- `tests/agents/validation_backtesting/validation_optimization_comparator/test_evaluator.py`
- `tests/agents/validation_backtesting/validation_optimization_comparator/test_user_workflows.py`
- `registry/agents/validation_backtesting/validation_optimization_comparator.yaml`
- `audit/reports/validation_backtesting/validation_optimization_comparator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Validation Robustness Monte Carlo

**Purpose**

Standalone robustness and Monte Carlo validation capability.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- candidate artifact
- test plan
- seed/config

**Outputs**

- Monte Carlo report
- robustness decision

**Tools / Capabilities**

- monte carlo engine

**Evidence Required**

- candidate artifact
- random seeds

**LLM Responsibilities**

- summarize results

**Deterministic Decision Rules**

- record seeds/config
- fail below threshold

**Allowed Actions**

- run standalone validation
- compare candidates
- produce validation package

**Blocked Actions**

- replace risk approval
- promote lifecycle
- alter results

**Functional Checklist**

- Implements `agentic/agents/validation_backtesting/validation_robustness_monte_carlo/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Validation Robustness Monte Carlo` alone with fixture input and verify a complete structured response.
- Ask `Validation Robustness Monte Carlo` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Validation Robustness Monte Carlo` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/validation_backtesting/validation_robustness_monte_carlo/agent.py`
- `agentic/agents/validation_backtesting/validation_robustness_monte_carlo/prompt.md`
- `agentic/agents/validation_backtesting/validation_robustness_monte_carlo/manifest.yaml`
- `agentic/agents/validation_backtesting/validation_robustness_monte_carlo/schemas.py`
- `agentic/agents/validation_backtesting/validation_robustness_monte_carlo/README.md`
- `tests/agents/validation_backtesting/validation_robustness_monte_carlo/test_schemas.py`
- `tests/agents/validation_backtesting/validation_robustness_monte_carlo/test_agent.py`
- `tests/agents/validation_backtesting/validation_robustness_monte_carlo/test_policy.py`
- `tests/agents/validation_backtesting/validation_robustness_monte_carlo/test_permissions.py`
- `tests/agents/validation_backtesting/validation_robustness_monte_carlo/test_evaluator.py`
- `tests/agents/validation_backtesting/validation_robustness_monte_carlo/test_user_workflows.py`
- `registry/agents/validation_backtesting/validation_robustness_monte_carlo.yaml`
- `audit/reports/validation_backtesting/validation_robustness_monte_carlo_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Validation Statistical Validation

**Purpose**

Standalone statistical validation capability for final evidence checks.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- result metrics
- thresholds

**Outputs**

- statistical decision
- confidence
- limitations

**Tools / Capabilities**

- statistical tests

**Evidence Required**

- metrics
- sample size

**LLM Responsibilities**

- explain validity

**Deterministic Decision Rules**

- reject insufficient evidence
- record thresholds

**Allowed Actions**

- run standalone validation
- compare candidates
- produce validation package

**Blocked Actions**

- replace risk approval
- promote lifecycle
- alter results

**Functional Checklist**

- Implements `agentic/agents/validation_backtesting/validation_statistical_validation/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Validation Statistical Validation` alone with fixture input and verify a complete structured response.
- Ask `Validation Statistical Validation` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Validation Statistical Validation` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/validation_backtesting/validation_statistical_validation/agent.py`
- `agentic/agents/validation_backtesting/validation_statistical_validation/prompt.md`
- `agentic/agents/validation_backtesting/validation_statistical_validation/manifest.yaml`
- `agentic/agents/validation_backtesting/validation_statistical_validation/schemas.py`
- `agentic/agents/validation_backtesting/validation_statistical_validation/README.md`
- `tests/agents/validation_backtesting/validation_statistical_validation/test_schemas.py`
- `tests/agents/validation_backtesting/validation_statistical_validation/test_agent.py`
- `tests/agents/validation_backtesting/validation_statistical_validation/test_policy.py`
- `tests/agents/validation_backtesting/validation_statistical_validation/test_permissions.py`
- `tests/agents/validation_backtesting/validation_statistical_validation/test_evaluator.py`
- `tests/agents/validation_backtesting/validation_statistical_validation/test_user_workflows.py`
- `registry/agents/validation_backtesting/validation_statistical_validation.yaml`
- `audit/reports/validation_backtesting/validation_statistical_validation_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Validation & Backtesting Package Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.


# Phase 5: Risk Department

## Phase Dependency Position

Risk depends on simulation and validation evidence. It determines whether candidates or high-impact actions can proceed to lifecycle, portfolio, paper, or production workflows.

## Required Folders and Files

```text
agentic/agents/risk/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/risk/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/risk_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/risk/
registry/workflows/risk_workflow.yaml
audit/reports/risk/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/risk_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/risk/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- review risk
- enforce control gates
- approve/reject/escalate within policy
- audit limits

Blocked by default:

- execute actions
- self-approve high-impact action
- change policy without approval

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
Simulation Evidence -> Risk Orchestrator -> Reviewer/Monitor/Auditors -> Hard-Coded Governor -> Risk Decision Package
```

## Department-Level Real-World Usage Examples

- Run the whole `Risk Department` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### Risk Orchestrator

**Purpose**

Coordinates control, risk, policy, limit, and approval-review agents.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- simulation evidence package
- strategy assumptions
- policy refs
- environment

**Outputs**

- risk review plan
- risk decision package
- approval route

**Tools / Capabilities**

- policy engine
- risk/control registry

**Evidence Required**

- simulation evidence
- policy docs
- limit configs

**LLM Responsibilities**

- summarize risk findings
- draft review plan

**Deterministic Decision Rules**

- require simulation evidence
- route high-impact items to governor
- record rejection reasons

**Allowed Actions**

- review risk
- enforce control gates
- approve/reject/escalate within policy
- audit limits

**Blocked Actions**

- execute actions
- self-approve high-impact action
- change policy without approval

**Functional Checklist**

- Implements `agentic/agents/risk/risk_orchestrator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Risk Orchestrator` alone with fixture input and verify a complete structured response.
- Ask `Risk Orchestrator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Risk Orchestrator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/risk/risk_orchestrator/agent.py`
- `agentic/agents/risk/risk_orchestrator/prompt.md`
- `agentic/agents/risk/risk_orchestrator/manifest.yaml`
- `agentic/agents/risk/risk_orchestrator/schemas.py`
- `agentic/agents/risk/risk_orchestrator/README.md`
- `tests/agents/risk/risk_orchestrator/test_schemas.py`
- `tests/agents/risk/risk_orchestrator/test_agent.py`
- `tests/agents/risk/risk_orchestrator/test_policy.py`
- `tests/agents/risk/risk_orchestrator/test_permissions.py`
- `tests/agents/risk/risk_orchestrator/test_evaluator.py`
- `tests/agents/risk/risk_orchestrator/test_user_workflows.py`
- `registry/agents/risk/risk_orchestrator.yaml`
- `audit/reports/risk/risk_orchestrator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Risk Reviewer

**Purpose**

Reviews risk, safety, compliance, operational exposure, and failure modes.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- candidate package
- risk assumptions
- policy refs

**Outputs**

- risk review report
- risk flags
- recommendation

**Tools / Capabilities**

- policy resource
- evidence store

**Evidence Required**

- strategy/simulation package
- policies

**LLM Responsibilities**

- explain risk concerns
- recommend mitigation

**Deterministic Decision Rules**

- cite policy/evidence
- mark unresolved risks
- do not approve without control gate

**Allowed Actions**

- review risk
- enforce control gates
- approve/reject/escalate within policy
- audit limits

**Blocked Actions**

- execute actions
- self-approve high-impact action
- change policy without approval

**Functional Checklist**

- Implements `agentic/agents/risk/risk_reviewer/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Risk Reviewer` alone with fixture input and verify a complete structured response.
- Ask `Risk Reviewer` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Risk Reviewer` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/risk/risk_reviewer/agent.py`
- `agentic/agents/risk/risk_reviewer/prompt.md`
- `agentic/agents/risk/risk_reviewer/manifest.yaml`
- `agentic/agents/risk/risk_reviewer/schemas.py`
- `agentic/agents/risk/risk_reviewer/README.md`
- `tests/agents/risk/risk_reviewer/test_schemas.py`
- `tests/agents/risk/risk_reviewer/test_agent.py`
- `tests/agents/risk/risk_reviewer/test_policy.py`
- `tests/agents/risk/risk_reviewer/test_permissions.py`
- `tests/agents/risk/risk_reviewer/test_evaluator.py`
- `tests/agents/risk/risk_reviewer/test_user_workflows.py`
- `registry/agents/risk/risk_reviewer.yaml`
- `audit/reports/risk/risk_reviewer_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Hard-Coded Risk Governor

**Purpose**

Deterministic policy-as-code service that enforces non-negotiable control rules.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- candidate/action package
- policy config
- limits
- environment

**Outputs**

- approve/reject/escalate decision
- reasons
- blocked actions

**Tools / Capabilities**

- policy engine
- limit store

**Evidence Required**

- current limits
- policy version
- candidate package

**LLM Responsibilities**

- none; deterministic only

**Deterministic Decision Rules**

- fail closed
- reject limit breaches
- escalate ambiguity
- record every decision

**Allowed Actions**

- review risk
- enforce control gates
- approve/reject/escalate within policy
- audit limits

**Blocked Actions**

- execute actions
- self-approve high-impact action
- change policy without approval

**Functional Checklist**

- Implements `agentic/agents/risk/hard_coded_risk_governor/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Hard-Coded Risk Governor` alone with fixture input and verify a complete structured response.
- Ask `Hard-Coded Risk Governor` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Hard-Coded Risk Governor` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/risk/hard_coded_risk_governor/agent.py`
- `agentic/agents/risk/hard_coded_risk_governor/prompt.md`
- `agentic/agents/risk/hard_coded_risk_governor/manifest.yaml`
- `agentic/agents/risk/hard_coded_risk_governor/schemas.py`
- `agentic/agents/risk/hard_coded_risk_governor/README.md`
- `tests/agents/risk/hard_coded_risk_governor/test_schemas.py`
- `tests/agents/risk/hard_coded_risk_governor/test_agent.py`
- `tests/agents/risk/hard_coded_risk_governor/test_policy.py`
- `tests/agents/risk/hard_coded_risk_governor/test_permissions.py`
- `tests/agents/risk/hard_coded_risk_governor/test_evaluator.py`
- `tests/agents/risk/hard_coded_risk_governor/test_user_workflows.py`
- `registry/agents/risk/hard_coded_risk_governor.yaml`
- `audit/reports/risk/hard_coded_risk_governor_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Portfolio Risk Monitor

**Purpose**

Monitors aggregate exposure, concentration, dependency risk, usage, drawdown, and control-limit drift.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- portfolio/system state
- resource allocation
- limits

**Outputs**

- risk monitor report
- alerts
- limit status

**Tools / Capabilities**

- state resource
- metrics calculator

**Evidence Required**

- current state
- limits
- historical exposure

**LLM Responsibilities**

- explain alerts

**Deterministic Decision Rules**

- flag breaches
- distinguish warning vs violation
- timestamp snapshot

**Allowed Actions**

- review risk
- enforce control gates
- approve/reject/escalate within policy
- audit limits

**Blocked Actions**

- execute actions
- self-approve high-impact action
- change policy without approval

**Functional Checklist**

- Implements `agentic/agents/risk/portfolio_risk_monitor/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Portfolio Risk Monitor` alone with fixture input and verify a complete structured response.
- Ask `Portfolio Risk Monitor` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Portfolio Risk Monitor` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/risk/portfolio_risk_monitor/agent.py`
- `agentic/agents/risk/portfolio_risk_monitor/prompt.md`
- `agentic/agents/risk/portfolio_risk_monitor/manifest.yaml`
- `agentic/agents/risk/portfolio_risk_monitor/schemas.py`
- `agentic/agents/risk/portfolio_risk_monitor/README.md`
- `tests/agents/risk/portfolio_risk_monitor/test_schemas.py`
- `tests/agents/risk/portfolio_risk_monitor/test_agent.py`
- `tests/agents/risk/portfolio_risk_monitor/test_policy.py`
- `tests/agents/risk/portfolio_risk_monitor/test_permissions.py`
- `tests/agents/risk/portfolio_risk_monitor/test_evaluator.py`
- `tests/agents/risk/portfolio_risk_monitor/test_user_workflows.py`
- `registry/agents/risk/portfolio_risk_monitor.yaml`
- `audit/reports/risk/portfolio_risk_monitor_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Risk Limit Auditor

**Purpose**

Audits configured limits, overrides, policy versions, and changes for governance compliance.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- limit configs
- change logs
- approval records

**Outputs**

- limit audit report
- violations
- missing approvals

**Tools / Capabilities**

- config reader
- audit log reader

**Evidence Required**

- policy configs
- change history

**LLM Responsibilities**

- summarize audit issues

**Deterministic Decision Rules**

- detect unapproved changes
- compare config to policy
- preserve evidence refs

**Allowed Actions**

- review risk
- enforce control gates
- approve/reject/escalate within policy
- audit limits

**Blocked Actions**

- execute actions
- self-approve high-impact action
- change policy without approval

**Functional Checklist**

- Implements `agentic/agents/risk/risk_limit_auditor/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Risk Limit Auditor` alone with fixture input and verify a complete structured response.
- Ask `Risk Limit Auditor` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Risk Limit Auditor` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/risk/risk_limit_auditor/agent.py`
- `agentic/agents/risk/risk_limit_auditor/prompt.md`
- `agentic/agents/risk/risk_limit_auditor/manifest.yaml`
- `agentic/agents/risk/risk_limit_auditor/schemas.py`
- `agentic/agents/risk/risk_limit_auditor/README.md`
- `tests/agents/risk/risk_limit_auditor/test_schemas.py`
- `tests/agents/risk/risk_limit_auditor/test_agent.py`
- `tests/agents/risk/risk_limit_auditor/test_policy.py`
- `tests/agents/risk/risk_limit_auditor/test_permissions.py`
- `tests/agents/risk/risk_limit_auditor/test_evaluator.py`
- `tests/agents/risk/risk_limit_auditor/test_user_workflows.py`
- `registry/agents/risk/risk_limit_auditor.yaml`
- `audit/reports/risk/risk_limit_auditor_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Risk Approval Auditor

**Purpose**

Audits approval packets, reviewer decisions, and governance signoffs.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- approval packets
- decision records
- policy requirements

**Outputs**

- approval audit report
- missing approvals
- scope violations

**Tools / Capabilities**

- approval store
- audit log

**Evidence Required**

- approval records
- policy requirements

**LLM Responsibilities**

- explain approval gaps

**Deterministic Decision Rules**

- fail missing approver
- fail scope mismatch
- detect expired approvals

**Allowed Actions**

- review risk
- enforce control gates
- approve/reject/escalate within policy
- audit limits

**Blocked Actions**

- execute actions
- self-approve high-impact action
- change policy without approval

**Functional Checklist**

- Implements `agentic/agents/risk/risk_approval_auditor/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Risk Approval Auditor` alone with fixture input and verify a complete structured response.
- Ask `Risk Approval Auditor` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Risk Approval Auditor` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/risk/risk_approval_auditor/agent.py`
- `agentic/agents/risk/risk_approval_auditor/prompt.md`
- `agentic/agents/risk/risk_approval_auditor/manifest.yaml`
- `agentic/agents/risk/risk_approval_auditor/schemas.py`
- `agentic/agents/risk/risk_approval_auditor/README.md`
- `tests/agents/risk/risk_approval_auditor/test_schemas.py`
- `tests/agents/risk/risk_approval_auditor/test_agent.py`
- `tests/agents/risk/risk_approval_auditor/test_policy.py`
- `tests/agents/risk/risk_approval_auditor/test_permissions.py`
- `tests/agents/risk/risk_approval_auditor/test_evaluator.py`
- `tests/agents/risk/risk_approval_auditor/test_user_workflows.py`
- `registry/agents/risk/risk_approval_auditor.yaml`
- `audit/reports/risk/risk_approval_auditor_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Risk Department Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.


# Phase 6: Portfolio & Execution Department

## Phase Dependency Position

Portfolio and Execution depends on risk/control decisions. It handles lifecycle, allocation, execution planning, paper execution, production execution, bridge calls, kill-switch enforcement, performance, and cost.

## Required Folders and Files

```text
agentic/agents/portfolio_execution/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/portfolio_execution/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/portfolio_execution_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/portfolio_execution/
registry/workflows/portfolio_execution_workflow.yaml
audit/reports/portfolio_execution/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/portfolio_execution_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/portfolio_execution/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

Blocked by default:

- bypass risk
- execute without readiness
- ignore kill switch

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
Risk Decision -> Portfolio Orchestrator -> Portfolio Manager/Allocation/Lifecycle -> Execution Planner -> Readiness -> Paper/Live -> Bridge/Kill Switch/Reports
```

## Department-Level Real-World Usage Examples

- Run the whole `Portfolio & Execution Department` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### Portfolio Orchestrator

**Purpose**

Coordinates lifecycle, allocation, execution readiness, paper/live execution, monitoring, kill switch, and cost optimization.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- risk decision package
- candidate artifact
- portfolio/system state

**Outputs**

- portfolio workflow plan
- execution route
- lifecycle package

**Tools / Capabilities**

- state resource
- approval service
- execution registry

**Evidence Required**

- risk approval
- current state
- candidate refs

**LLM Responsibilities**

- plan execution lifecycle
- summarize readiness

**Deterministic Decision Rules**

- require risk decision
- approval before high-impact execution
- kill switch checks

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/portfolio_orchestrator/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Portfolio Orchestrator` alone with fixture input and verify a complete structured response.
- Ask `Portfolio Orchestrator` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Portfolio Orchestrator` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/portfolio_orchestrator/agent.py`
- `agentic/agents/portfolio_execution/portfolio_orchestrator/prompt.md`
- `agentic/agents/portfolio_execution/portfolio_orchestrator/manifest.yaml`
- `agentic/agents/portfolio_execution/portfolio_orchestrator/schemas.py`
- `agentic/agents/portfolio_execution/portfolio_orchestrator/README.md`
- `tests/agents/portfolio_execution/portfolio_orchestrator/test_schemas.py`
- `tests/agents/portfolio_execution/portfolio_orchestrator/test_agent.py`
- `tests/agents/portfolio_execution/portfolio_orchestrator/test_policy.py`
- `tests/agents/portfolio_execution/portfolio_orchestrator/test_permissions.py`
- `tests/agents/portfolio_execution/portfolio_orchestrator/test_evaluator.py`
- `tests/agents/portfolio_execution/portfolio_orchestrator/test_user_workflows.py`
- `registry/agents/portfolio_execution/portfolio_orchestrator.yaml`
- `audit/reports/portfolio_execution/portfolio_orchestrator_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Portfolio Manager

**Purpose**

Evaluates how candidate actions fit into overall portfolio/system/resource allocation goals.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- candidate
- current portfolio/system state
- constraints

**Outputs**

- portfolio fit assessment
- allocation recommendation
- conflicts

**Tools / Capabilities**

- state resource
- allocation calculator

**Evidence Required**

- current state
- risk decision
- constraints

**LLM Responsibilities**

- explain fit/tradeoffs

**Deterministic Decision Rules**

- respect risk decision
- flag concentration conflicts
- do not alter allocation directly

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/portfolio_manager/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Portfolio Manager` alone with fixture input and verify a complete structured response.
- Ask `Portfolio Manager` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Portfolio Manager` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/portfolio_manager/agent.py`
- `agentic/agents/portfolio_execution/portfolio_manager/prompt.md`
- `agentic/agents/portfolio_execution/portfolio_manager/manifest.yaml`
- `agentic/agents/portfolio_execution/portfolio_manager/schemas.py`
- `agentic/agents/portfolio_execution/portfolio_manager/README.md`
- `tests/agents/portfolio_execution/portfolio_manager/test_schemas.py`
- `tests/agents/portfolio_execution/portfolio_manager/test_agent.py`
- `tests/agents/portfolio_execution/portfolio_manager/test_policy.py`
- `tests/agents/portfolio_execution/portfolio_manager/test_permissions.py`
- `tests/agents/portfolio_execution/portfolio_manager/test_evaluator.py`
- `tests/agents/portfolio_execution/portfolio_manager/test_user_workflows.py`
- `registry/agents/portfolio_execution/portfolio_manager.yaml`
- `audit/reports/portfolio_execution/portfolio_manager_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Allocation Optimizer

**Purpose**

Proposes resource/capital/capacity allocation under constraints and approved limits.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- portfolio state
- candidate set
- limits
- objective

**Outputs**

- allocation proposal
- constraint report
- sensitivity notes

**Tools / Capabilities**

- optimizer
- constraint checker

**Evidence Required**

- candidate metrics
- limits
- objectives

**LLM Responsibilities**

- explain allocation rationale

**Deterministic Decision Rules**

- respect constraints
- return rejected constraints
- mark assumptions

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/allocation_optimizer/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Allocation Optimizer` alone with fixture input and verify a complete structured response.
- Ask `Allocation Optimizer` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Allocation Optimizer` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/allocation_optimizer/agent.py`
- `agentic/agents/portfolio_execution/allocation_optimizer/prompt.md`
- `agentic/agents/portfolio_execution/allocation_optimizer/manifest.yaml`
- `agentic/agents/portfolio_execution/allocation_optimizer/schemas.py`
- `agentic/agents/portfolio_execution/allocation_optimizer/README.md`
- `tests/agents/portfolio_execution/allocation_optimizer/test_schemas.py`
- `tests/agents/portfolio_execution/allocation_optimizer/test_agent.py`
- `tests/agents/portfolio_execution/allocation_optimizer/test_policy.py`
- `tests/agents/portfolio_execution/allocation_optimizer/test_permissions.py`
- `tests/agents/portfolio_execution/allocation_optimizer/test_evaluator.py`
- `tests/agents/portfolio_execution/allocation_optimizer/test_user_workflows.py`
- `registry/agents/portfolio_execution/allocation_optimizer.yaml`
- `audit/reports/portfolio_execution/allocation_optimizer_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Strategy Lifecycle

**Purpose**

Manages candidate lifecycle transitions from research to test, staging, paper/sandbox, production, paused, retired, or deprecated.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- candidate id
- current state
- evidence package
- approvals

**Outputs**

- lifecycle transition proposal/decision
- required evidence
- status

**Tools / Capabilities**

- lifecycle registry
- approval store

**Evidence Required**

- audit evidence
- approval records
- stage policy

**LLM Responsibilities**

- explain lifecycle status

**Deterministic Decision Rules**

- transitions require evidence
- high-impact transitions need approval
- no silent promotion

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/strategy_lifecycle/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Strategy Lifecycle` alone with fixture input and verify a complete structured response.
- Ask `Strategy Lifecycle` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Strategy Lifecycle` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/strategy_lifecycle/agent.py`
- `agentic/agents/portfolio_execution/strategy_lifecycle/prompt.md`
- `agentic/agents/portfolio_execution/strategy_lifecycle/manifest.yaml`
- `agentic/agents/portfolio_execution/strategy_lifecycle/schemas.py`
- `agentic/agents/portfolio_execution/strategy_lifecycle/README.md`
- `tests/agents/portfolio_execution/strategy_lifecycle/test_schemas.py`
- `tests/agents/portfolio_execution/strategy_lifecycle/test_agent.py`
- `tests/agents/portfolio_execution/strategy_lifecycle/test_policy.py`
- `tests/agents/portfolio_execution/strategy_lifecycle/test_permissions.py`
- `tests/agents/portfolio_execution/strategy_lifecycle/test_evaluator.py`
- `tests/agents/portfolio_execution/strategy_lifecycle/test_user_workflows.py`
- `registry/agents/portfolio_execution/strategy_lifecycle.yaml`
- `audit/reports/portfolio_execution/strategy_lifecycle_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Execution Planner

**Purpose**

Turns approved actions into safe execution plans with preconditions, rollback, idempotency, and monitoring.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- approved action
- state
- constraints
- target

**Outputs**

- execution plan
- prechecks
- rollback plan
- idempotency key

**Tools / Capabilities**

- execution template registry
- state resource

**Evidence Required**

- risk approval
- target state
- constraints

**LLM Responsibilities**

- draft execution plan
- explain rollback

**Deterministic Decision Rules**

- approval required
- include rollback/compensation
- define idempotency key

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/execution_planner/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Execution Planner` alone with fixture input and verify a complete structured response.
- Ask `Execution Planner` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Execution Planner` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/execution_planner/agent.py`
- `agentic/agents/portfolio_execution/execution_planner/prompt.md`
- `agentic/agents/portfolio_execution/execution_planner/manifest.yaml`
- `agentic/agents/portfolio_execution/execution_planner/schemas.py`
- `agentic/agents/portfolio_execution/execution_planner/README.md`
- `tests/agents/portfolio_execution/execution_planner/test_schemas.py`
- `tests/agents/portfolio_execution/execution_planner/test_agent.py`
- `tests/agents/portfolio_execution/execution_planner/test_policy.py`
- `tests/agents/portfolio_execution/execution_planner/test_permissions.py`
- `tests/agents/portfolio_execution/execution_planner/test_evaluator.py`
- `tests/agents/portfolio_execution/execution_planner/test_user_workflows.py`
- `registry/agents/portfolio_execution/execution_planner.yaml`
- `audit/reports/portfolio_execution/execution_planner_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Execution Readiness

**Purpose**

Checks technical, policy, approval, environment, and monitoring preconditions before execution.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- execution plan
- environment
- approval refs
- monitoring status

**Outputs**

- readiness decision
- failed checks
- go/no-go recommendation

**Tools / Capabilities**

- environment checker
- approval checker
- monitoring checker

**Evidence Required**

- execution plan
- approval records

**LLM Responsibilities**

- explain failed checks

**Deterministic Decision Rules**

- fail closed on missing check
- verify environment
- verify approval scope

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/execution_readiness/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Execution Readiness` alone with fixture input and verify a complete structured response.
- Ask `Execution Readiness` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Execution Readiness` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/execution_readiness/agent.py`
- `agentic/agents/portfolio_execution/execution_readiness/prompt.md`
- `agentic/agents/portfolio_execution/execution_readiness/manifest.yaml`
- `agentic/agents/portfolio_execution/execution_readiness/schemas.py`
- `agentic/agents/portfolio_execution/execution_readiness/README.md`
- `tests/agents/portfolio_execution/execution_readiness/test_schemas.py`
- `tests/agents/portfolio_execution/execution_readiness/test_agent.py`
- `tests/agents/portfolio_execution/execution_readiness/test_policy.py`
- `tests/agents/portfolio_execution/execution_readiness/test_permissions.py`
- `tests/agents/portfolio_execution/execution_readiness/test_evaluator.py`
- `tests/agents/portfolio_execution/execution_readiness/test_user_workflows.py`
- `registry/agents/portfolio_execution/execution_readiness.yaml`
- `audit/reports/portfolio_execution/execution_readiness_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Paper Execution

**Purpose**

Executes approved actions in sandbox/paper/simulation environment without production impact.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- approved paper plan
- sandbox environment
- candidate artifact

**Outputs**

- paper execution result
- logs
- behavior notes

**Tools / Capabilities**

- sandbox executor
- state recorder

**Evidence Required**

- execution plan
- sandbox config

**LLM Responsibilities**

- summarize paper results

**Deterministic Decision Rules**

- run only in sandbox
- record all actions
- never use production connector

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/paper_execution/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Paper Execution` alone with fixture input and verify a complete structured response.
- Ask `Paper Execution` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Paper Execution` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/paper_execution/agent.py`
- `agentic/agents/portfolio_execution/paper_execution/prompt.md`
- `agentic/agents/portfolio_execution/paper_execution/manifest.yaml`
- `agentic/agents/portfolio_execution/paper_execution/schemas.py`
- `agentic/agents/portfolio_execution/paper_execution/README.md`
- `tests/agents/portfolio_execution/paper_execution/test_schemas.py`
- `tests/agents/portfolio_execution/paper_execution/test_agent.py`
- `tests/agents/portfolio_execution/paper_execution/test_policy.py`
- `tests/agents/portfolio_execution/paper_execution/test_permissions.py`
- `tests/agents/portfolio_execution/paper_execution/test_evaluator.py`
- `tests/agents/portfolio_execution/paper_execution/test_user_workflows.py`
- `registry/agents/portfolio_execution/paper_execution.yaml`
- `audit/reports/portfolio_execution/paper_execution_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Live Execution

**Purpose**

Coordinates approved production execution through readiness, bridge, monitoring, and audit.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- approved live plan
- readiness result
- approval ref

**Outputs**

- live execution request/result
- monitoring refs
- audit trail

**Tools / Capabilities**

- execution bridge
- kill switch service
- approval store

**Evidence Required**

- readiness pass
- approval packet
- execution plan

**LLM Responsibilities**

- summarize live status

**Deterministic Decision Rules**

- require readiness pass
- verify kill switch open
- use approved bridge
- record result

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/live_execution/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Live Execution` alone with fixture input and verify a complete structured response.
- Ask `Live Execution` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Live Execution` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/live_execution/agent.py`
- `agentic/agents/portfolio_execution/live_execution/prompt.md`
- `agentic/agents/portfolio_execution/live_execution/manifest.yaml`
- `agentic/agents/portfolio_execution/live_execution/schemas.py`
- `agentic/agents/portfolio_execution/live_execution/README.md`
- `tests/agents/portfolio_execution/live_execution/test_schemas.py`
- `tests/agents/portfolio_execution/live_execution/test_agent.py`
- `tests/agents/portfolio_execution/live_execution/test_policy.py`
- `tests/agents/portfolio_execution/live_execution/test_permissions.py`
- `tests/agents/portfolio_execution/live_execution/test_evaluator.py`
- `tests/agents/portfolio_execution/live_execution/test_user_workflows.py`
- `registry/agents/portfolio_execution/live_execution.yaml`
- `audit/reports/portfolio_execution/live_execution_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### MT5 / cTrader Execution Bridge

**Purpose**

Domain-specific external execution bridge; in generic systems this represents any approved external action bridge.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- approved command
- idempotency key
- target connector

**Outputs**

- external execution result
- external id
- status

**Tools / Capabilities**

- external API adapter
- idempotency store

**Evidence Required**

- approved command
- connector config

**LLM Responsibilities**

- none by default

**Deterministic Decision Rules**

- validate approval
- enforce idempotency
- fail closed on connector error

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/mt5_ctrader_execution_bridge/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `MT5 / cTrader Execution Bridge` alone with fixture input and verify a complete structured response.
- Ask `MT5 / cTrader Execution Bridge` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `MT5 / cTrader Execution Bridge` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/mt5_ctrader_execution_bridge/agent.py`
- `agentic/agents/portfolio_execution/mt5_ctrader_execution_bridge/prompt.md`
- `agentic/agents/portfolio_execution/mt5_ctrader_execution_bridge/manifest.yaml`
- `agentic/agents/portfolio_execution/mt5_ctrader_execution_bridge/schemas.py`
- `agentic/agents/portfolio_execution/mt5_ctrader_execution_bridge/README.md`
- `tests/agents/portfolio_execution/mt5_ctrader_execution_bridge/test_schemas.py`
- `tests/agents/portfolio_execution/mt5_ctrader_execution_bridge/test_agent.py`
- `tests/agents/portfolio_execution/mt5_ctrader_execution_bridge/test_policy.py`
- `tests/agents/portfolio_execution/mt5_ctrader_execution_bridge/test_permissions.py`
- `tests/agents/portfolio_execution/mt5_ctrader_execution_bridge/test_evaluator.py`
- `tests/agents/portfolio_execution/mt5_ctrader_execution_bridge/test_user_workflows.py`
- `registry/agents/portfolio_execution/mt5_ctrader_execution_bridge.yaml`
- `audit/reports/portfolio_execution/mt5_ctrader_execution_bridge_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Kill Switch Service

**Purpose**

Blocks, pauses, or disables execution workflows when critical conditions or authorized human commands require stop.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- environment
- scope
- trigger
- authority

**Outputs**

- kill switch status
- blocked scopes
- audit event

**Tools / Capabilities**

- state store
- authority checker

**Evidence Required**

- incident status
- manual command
- policy triggers

**LLM Responsibilities**

- explain blocked scope

**Deterministic Decision Rules**

- checked before execution
- fail closed when unknown
- record trigger/authority

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/kill_switch_service/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Kill Switch Service` alone with fixture input and verify a complete structured response.
- Ask `Kill Switch Service` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Kill Switch Service` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/kill_switch_service/agent.py`
- `agentic/agents/portfolio_execution/kill_switch_service/prompt.md`
- `agentic/agents/portfolio_execution/kill_switch_service/manifest.yaml`
- `agentic/agents/portfolio_execution/kill_switch_service/schemas.py`
- `agentic/agents/portfolio_execution/kill_switch_service/README.md`
- `tests/agents/portfolio_execution/kill_switch_service/test_schemas.py`
- `tests/agents/portfolio_execution/kill_switch_service/test_agent.py`
- `tests/agents/portfolio_execution/kill_switch_service/test_policy.py`
- `tests/agents/portfolio_execution/kill_switch_service/test_permissions.py`
- `tests/agents/portfolio_execution/kill_switch_service/test_evaluator.py`
- `tests/agents/portfolio_execution/kill_switch_service/test_user_workflows.py`
- `registry/agents/portfolio_execution/kill_switch_service.yaml`
- `audit/reports/portfolio_execution/kill_switch_service_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Performance Reporter

**Purpose**

Reports performance, behavior, cost, reliability, and outcome metrics for portfolio/execution lifecycle.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- execution logs
- metrics
- time window

**Outputs**

- performance report
- alerts
- recommendations

**Tools / Capabilities**

- metrics store
- audit log

**Evidence Required**

- execution results
- monitoring data

**LLM Responsibilities**

- summarize performance

**Deterministic Decision Rules**

- separate observed metrics from recommendations
- cite run refs
- flag missing data

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/performance_reporter/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Performance Reporter` alone with fixture input and verify a complete structured response.
- Ask `Performance Reporter` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Performance Reporter` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/performance_reporter/agent.py`
- `agentic/agents/portfolio_execution/performance_reporter/prompt.md`
- `agentic/agents/portfolio_execution/performance_reporter/manifest.yaml`
- `agentic/agents/portfolio_execution/performance_reporter/schemas.py`
- `agentic/agents/portfolio_execution/performance_reporter/README.md`
- `tests/agents/portfolio_execution/performance_reporter/test_schemas.py`
- `tests/agents/portfolio_execution/performance_reporter/test_agent.py`
- `tests/agents/portfolio_execution/performance_reporter/test_policy.py`
- `tests/agents/portfolio_execution/performance_reporter/test_permissions.py`
- `tests/agents/portfolio_execution/performance_reporter/test_evaluator.py`
- `tests/agents/portfolio_execution/performance_reporter/test_user_workflows.py`
- `registry/agents/portfolio_execution/performance_reporter.yaml`
- `audit/reports/portfolio_execution/performance_reporter_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Cost Optimizer

**Purpose**

Monitors and recommends improvements to model/tool/API/compute cost and latency.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- cost logs
- latency metrics
- workflow usage

**Outputs**

- cost report
- optimization proposal
- risk of changes

**Tools / Capabilities**

- cost metrics store
- model registry

**Evidence Required**

- usage logs
- budget policy

**LLM Responsibilities**

- explain cost-saving options

**Deterministic Decision Rules**

- preserve safety gates
- approval for production routing change
- quantify risk

**Allowed Actions**

- plan execution
- manage lifecycle after approval
- run paper execution
- execute through approved bridge

**Blocked Actions**

- bypass risk
- execute without readiness
- ignore kill switch

**Functional Checklist**

- Implements `agentic/agents/portfolio_execution/cost_optimizer/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Cost Optimizer` alone with fixture input and verify a complete structured response.
- Ask `Cost Optimizer` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Cost Optimizer` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/portfolio_execution/cost_optimizer/agent.py`
- `agentic/agents/portfolio_execution/cost_optimizer/prompt.md`
- `agentic/agents/portfolio_execution/cost_optimizer/manifest.yaml`
- `agentic/agents/portfolio_execution/cost_optimizer/schemas.py`
- `agentic/agents/portfolio_execution/cost_optimizer/README.md`
- `tests/agents/portfolio_execution/cost_optimizer/test_schemas.py`
- `tests/agents/portfolio_execution/cost_optimizer/test_agent.py`
- `tests/agents/portfolio_execution/cost_optimizer/test_policy.py`
- `tests/agents/portfolio_execution/cost_optimizer/test_permissions.py`
- `tests/agents/portfolio_execution/cost_optimizer/test_evaluator.py`
- `tests/agents/portfolio_execution/cost_optimizer/test_user_workflows.py`
- `registry/agents/portfolio_execution/cost_optimizer.yaml`
- `audit/reports/portfolio_execution/cost_optimizer_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Portfolio & Execution Department Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.


# Phase 7: Operations & Audit Department

## Phase Dependency Position

Operations and Audit depends on traces, logs, metrics, approvals, and evidence generated by the rest of the system. It monitors compliance, operational health, and cost.

## Required Folders and Files

```text
agentic/agents/operations_audit/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/operations_audit/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/operations_audit_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/operations_audit/
registry/workflows/operations_audit_workflow.yaml
audit/reports/operations_audit/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/operations_audit_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/operations_audit/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- monitor compliance
- report performance
- recommend cost changes

Blocked by default:

- alter logs
- approve exceptions
- disable controls

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
Traces/Logs/Metrics -> Audit Compliance -> Performance Reporter -> Cost Optimizer -> Operations Reports -> Remediation
```

## Department-Level Real-World Usage Examples

- Run the whole `Operations & Audit Department` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### Audit Compliance

**Purpose**

Reviews workflow, policy, audit, approval, and evidence compliance across departments.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- audit logs
- policy map
- approval records
- workflow traces

**Outputs**

- compliance report
- violations
- remediation tasks

**Tools / Capabilities**

- audit log reader
- policy checker
- report writer

**Evidence Required**

- logs
- policies
- approvals

**LLM Responsibilities**

- summarize violations
- draft remediation

**Deterministic Decision Rules**

- cite trace ids
- do not hide violations
- separate breach from warning

**Allowed Actions**

- monitor compliance
- report performance
- recommend cost changes

**Blocked Actions**

- alter logs
- approve exceptions
- disable controls

**Functional Checklist**

- Implements `agentic/agents/operations_audit/audit_compliance/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Audit Compliance` alone with fixture input and verify a complete structured response.
- Ask `Audit Compliance` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Audit Compliance` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/operations_audit/audit_compliance/agent.py`
- `agentic/agents/operations_audit/audit_compliance/prompt.md`
- `agentic/agents/operations_audit/audit_compliance/manifest.yaml`
- `agentic/agents/operations_audit/audit_compliance/schemas.py`
- `agentic/agents/operations_audit/audit_compliance/README.md`
- `tests/agents/operations_audit/audit_compliance/test_schemas.py`
- `tests/agents/operations_audit/audit_compliance/test_agent.py`
- `tests/agents/operations_audit/audit_compliance/test_policy.py`
- `tests/agents/operations_audit/audit_compliance/test_permissions.py`
- `tests/agents/operations_audit/audit_compliance/test_evaluator.py`
- `tests/agents/operations_audit/audit_compliance/test_user_workflows.py`
- `registry/agents/operations_audit/audit_compliance.yaml`
- `audit/reports/operations_audit/audit_compliance_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Operations Performance Reporter

**Purpose**

Reports operational health, success rates, latency, cost, failures, incident trends, and reliability.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- metrics logs
- trace logs
- time window

**Outputs**

- operations report
- SLO/SLA status
- alerts

**Tools / Capabilities**

- metrics store
- trace store

**Evidence Required**

- latency
- cost
- error rates
- workflow completion

**LLM Responsibilities**

- summarize operational health

**Deterministic Decision Rules**

- include failed workflows
- report p95/p99
- flag threshold breaches

**Allowed Actions**

- monitor compliance
- report performance
- recommend cost changes

**Blocked Actions**

- alter logs
- approve exceptions
- disable controls

**Functional Checklist**

- Implements `agentic/agents/operations_audit/operations_performance_reporter/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Operations Performance Reporter` alone with fixture input and verify a complete structured response.
- Ask `Operations Performance Reporter` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Operations Performance Reporter` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/operations_audit/operations_performance_reporter/agent.py`
- `agentic/agents/operations_audit/operations_performance_reporter/prompt.md`
- `agentic/agents/operations_audit/operations_performance_reporter/manifest.yaml`
- `agentic/agents/operations_audit/operations_performance_reporter/schemas.py`
- `agentic/agents/operations_audit/operations_performance_reporter/README.md`
- `tests/agents/operations_audit/operations_performance_reporter/test_schemas.py`
- `tests/agents/operations_audit/operations_performance_reporter/test_agent.py`
- `tests/agents/operations_audit/operations_performance_reporter/test_policy.py`
- `tests/agents/operations_audit/operations_performance_reporter/test_permissions.py`
- `tests/agents/operations_audit/operations_performance_reporter/test_evaluator.py`
- `tests/agents/operations_audit/operations_performance_reporter/test_user_workflows.py`
- `registry/agents/operations_audit/operations_performance_reporter.yaml`
- `audit/reports/operations_audit/operations_performance_reporter_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

### Operations Cost Optimizer

**Purpose**

Optimizes operating cost across agents, models, tools, workflows, and infrastructure.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- cost metrics
- usage patterns
- routing policies

**Outputs**

- cost optimization plan
- expected savings
- risk assessment

**Tools / Capabilities**

- cost store
- routing policy reader

**Evidence Required**

- usage logs
- budgets
- model costs

**LLM Responsibilities**

- explain savings opportunities

**Deterministic Decision Rules**

- preserve safety/audit controls
- approval for production changes
- quantify impact

**Allowed Actions**

- monitor compliance
- report performance
- recommend cost changes

**Blocked Actions**

- alter logs
- approve exceptions
- disable controls

**Functional Checklist**

- Implements `agentic/agents/operations_audit/operations_cost_optimizer/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Operations Cost Optimizer` alone with fixture input and verify a complete structured response.
- Ask `Operations Cost Optimizer` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Operations Cost Optimizer` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/operations_audit/operations_cost_optimizer/agent.py`
- `agentic/agents/operations_audit/operations_cost_optimizer/prompt.md`
- `agentic/agents/operations_audit/operations_cost_optimizer/manifest.yaml`
- `agentic/agents/operations_audit/operations_cost_optimizer/schemas.py`
- `agentic/agents/operations_audit/operations_cost_optimizer/README.md`
- `tests/agents/operations_audit/operations_cost_optimizer/test_schemas.py`
- `tests/agents/operations_audit/operations_cost_optimizer/test_agent.py`
- `tests/agents/operations_audit/operations_cost_optimizer/test_policy.py`
- `tests/agents/operations_audit/operations_cost_optimizer/test_permissions.py`
- `tests/agents/operations_audit/operations_cost_optimizer/test_evaluator.py`
- `tests/agents/operations_audit/operations_cost_optimizer/test_user_workflows.py`
- `registry/agents/operations_audit/operations_cost_optimizer.yaml`
- `audit/reports/operations_audit/operations_cost_optimizer_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Operations & Audit Department Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.


# Phase 8: Dedicated Audit Department

## Phase Dependency Position

The Audit Department is built after agents have manifests, tests, logs, evidence, registry entries, and workflow memberships. It performs formal independent audit scoring.

## Required Folders and Files

```text
agentic/agents/audit/
├── <agent_name>/
│   ├── agent.py
│   ├── prompt.md
│   ├── manifest.yaml
│   ├── schemas.py
│   └── README.md

tests/agents/audit/
├── <agent_name>/
│   ├── test_schemas.py
│   ├── test_agent.py
│   ├── test_policy.py
│   ├── test_permissions.py
│   ├── test_evaluator.py
│   └── test_user_workflows.py

agentic/workflows/audit_workflow/
├── workflow.py
├── workflow.yaml
├── schemas.py
└── README.md

registry/agents/audit/
registry/workflows/audit_workflow.yaml
audit/reports/audit/
```

## Shared Contracts for This Department

- Reuse global `AgentRequest`, `AgentContext`, `AgentResponse`, `EvidenceItem`, `AgentDecision`, `AuditRecord`, `PermissionProfile`, `EvaluationResult`, and `HandoffPayload`.
- Add department-specific request, response, artifact, decision, and handoff schemas in `agentic/workflows/audit_workflow/schemas.py`.
- Every agent must register its own `manifest.yaml` and corresponding `registry/agents/audit/<agent_name>.yaml`.

## Shared Permission for This Department

Allowed by default:

- score agents
- detect critical fails
- create remediation tasks

Blocked by default:

- approve own remediation
- execute production changes
- alter evidence

## Shared Audit for This Department

Every agent and workflow run must log:

- `trace_id`
- `request_id`
- `workflow_id`
- `department`
- `agent_name`
- `environment`
- `permission_profile`
- `evidence_refs`
- `tools_used`
- `policy_version`
- `prompt_version` if LLM was used
- `decision_path`
- `allowed_actions`
- `blocked_actions`
- `approval_ref` if required
- downstream `handoff_ref` if created

## Department Workflow

```text
Agent/Workflow/Registry/Evidence -> Audit Agent -> Audit Report -> Remediation -> Re-Audit -> Approval Recommendation
```

## Department-Level Real-World Usage Examples

- Run the whole `Dedicated Audit Department` independently with fixture data and verify a complete department output.
- Run each agent independently before connecting it to the department workflow.
- Use mocked upstream handoff packages until previous phases are implemented.
- Integrate this department only after its manifest, unit tests, user workflow tests, audit records, and handoff schema pass.

## Agent-by-Agent Implementation Plan

### Audit Agent

**Purpose**

Performs formal agent, workflow, manifest, registry, and production-readiness audits using the Agent Auditing Checklist.

**Non-Goals**

- Does not bypass the Planner, Control Plane, permission model, audit layer, or approval gates.
- Does not perform work outside its manifest scope.
- Does not treat LLM output as an uncontrolled final decision.
- Does not hide missing evidence, stale data, contradictions, or failed checks.

**Inputs**

- agent manifest
- agent files
- test results
- audit checklist
- evidence refs

**Outputs**

- audit report
- score
- critical fails
- remediation tasks
- approval recommendation

**Tools / Capabilities**

- file/resource reader
- manifest validator
- test result reader
- quality gate

**Evidence Required**

- manifest
- tests
- logs
- docs
- evidence

**LLM Responsibilities**

- summarize audit findings
- explain remediation priorities

**Deterministic Decision Rules**

- critical fails override score
- missing manifest fails
- high-impact permissions require approval checks
- evidence must be cited

**Allowed Actions**

- score agents
- detect critical fails
- create remediation tasks

**Blocked Actions**

- approve own remediation
- execute production changes
- alter evidence

**Functional Checklist**

- Implements `agentic/agents/audit/audit_agent/agent.py`.
- Defines input, output, evidence, decision, and artifact schemas in `schemas.py`.
- Declares permissions, tools, lifecycle, owner, environment support, and guardrails in `manifest.yaml`.
- Uses `prompt.md` only for role, task, constraints, evidence rules, and output format.
- Validates all inputs before tool/model calls.
- Gathers evidence only from declared capabilities.
- Marks source, timestamp, freshness, and confidence on evidence.
- Uses LLM output only for allowed responsibilities.
- Applies deterministic policy before returning final status.
- Returns the standard `AgentResponse` envelope.
- Writes audit metadata with trace id, policy version, prompt version, tools used, model used, decision path, and environment.
- Provides standalone README usage examples.
- Can run independently before department integration.

**Tests: Unit and User Workflow**

- Unit: valid and invalid schema payloads.
- Unit: permission profile blocks prohibited actions.
- Unit: deterministic policy handles normal, missing-evidence, stale-evidence, and failure cases.
- Unit: evaluator returns pass/fail with reasons.
- User workflow: realistic prompt produces expected `AgentResponse`.
- User workflow: unsafe or unsupported request is rejected or escalated.

**Real-World Usage Examples**

- Run `Audit Agent` alone with fixture input and verify a complete structured response.
- Ask `Audit Agent` a realistic user request and confirm it returns evidence, decision, audit metadata, and next action.
- Send missing or unsafe input to `Audit Agent` and confirm it fails safely.

**Implementation Deliverables**

- `agentic/agents/audit/audit_agent/agent.py`
- `agentic/agents/audit/audit_agent/prompt.md`
- `agentic/agents/audit/audit_agent/manifest.yaml`
- `agentic/agents/audit/audit_agent/schemas.py`
- `agentic/agents/audit/audit_agent/README.md`
- `tests/agents/audit/audit_agent/test_schemas.py`
- `tests/agents/audit/audit_agent/test_agent.py`
- `tests/agents/audit/audit_agent/test_policy.py`
- `tests/agents/audit/audit_agent/test_permissions.py`
- `tests/agents/audit/audit_agent/test_evaluator.py`
- `tests/agents/audit/audit_agent/test_user_workflows.py`
- `registry/agents/audit/audit_agent.yaml`
- `audit/reports/audit/audit_agent_audit_report.md`

**Acceptance Exit Gate**

- Agent runs independently with fixture inputs.
- Unit tests and user workflow tests pass.
- Manifest validates against shared manifest schema.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete.
- Output can be consumed by the department workflow.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

## Dedicated Audit Department Acceptance Exit Gate

- Every agent in this phase has implementation files, manifest, schemas, prompt, README, evaluator, and tests.
- Every agent runs independently with fixture inputs.
- Every agent has unit tests and user workflow tests.
- Department workflow runs end-to-end with fixture upstream handoff.
- Department workflow rejects invalid or incomplete handoffs.
- All outputs validate against shared and department schemas.
- Permission tests prove blocked actions are blocked.
- Audit metadata is complete for every agent and workflow run.
- Registry entries exist for all agents and workflows.
- No critical fail condition from `docs/Agent_Auditing_Checklist.md` remains.

# End-to-End Integration Milestones

## Milestone 1: Foundation Ready

- Shared contracts implemented.
- Permission model implemented.
- Audit envelope implemented.
- Tool executor implemented.
- Runtime/model adapter implemented.
- Planner, AI CEO/CIO, and Control Plane run with mocked department agents.
- Registry loaders work.
- Quality gates run in CI.

## Milestone 2: Research to Strategy

```text
Research Evidence Package -> Strategy Creation Orchestrator -> Strategy Spec
```

Exit criteria:

- Research package schema validates.
- Strategy Development rejects incomplete research.
- Evidence refs are preserved.
- User can ask: “Create a strategy/design candidate from this research evidence.”

## Milestone 3: Strategy to Simulation

```text
Strategy Handoff Package -> Simulation Orchestrator -> Simulation Evidence Package
```

Exit criteria:

- Strategy handoff includes spec, code/artifact refs, assumptions, and test plan.
- Simulation rejects missing data/config.
- Results are reproducible.

## Milestone 4: Simulation to Risk

```text
Simulation Evidence Package -> Risk Orchestrator -> Risk Decision Package
```

Exit criteria:

- Risk rejects weak/missing evidence.
- Hard-coded governor fails closed.
- Approval auditor detects missing/expired approvals.

## Milestone 5: Risk to Portfolio / Execution

```text
Risk Decision Package -> Portfolio Orchestrator -> Execution Planner -> Readiness -> Paper Execution -> Live Execution
```

Exit criteria:

- No execution can happen without risk/control decision.
- Readiness blocks missing approvals.
- Kill switch blocks execution.
- Execution bridge enforces idempotency.

## Milestone 6: Operations and Audit

```text
Traces + Logs + Metrics + Evidence -> Operations & Audit -> Dedicated Audit -> Reports and Remediation
```

Exit criteria:

- Every run is traceable.
- Every agent has audit report.
- Critical fail conditions block production.
- CI quality gates fail on manifest/test/permission violations.

# Global Acceptance Criteria

The full system is implementation-ready when:

1. Every agent has a manifest.
2. Every agent has schemas.
3. Every agent has a permission profile.
4. Every agent has deterministic policy checks.
5. Every agent has audit metadata.
6. Every agent has unit tests and user workflow tests.
7. Every department runs independently.
8. Every department handoff validates.
9. All high-impact actions require approval.
10. All production actions are blocked in non-production.
11. The Audit Agent can score every agent using `docs/Agent_Auditing_Checklist.md`.
12. The system conforms to `docs/Agentic_AI_Playbook.md` and `docs/Agent_Template.md`.

# Agentic Firm Implementation Checklist

> Progress-tracking checklist derived from `Agentic_Firm_Detailed_Implementation_Plan_v2.md` and aligned with:
>
> - `docs/Agentic_AI_Playbook.md`
> - `docs/Agent_Auditing_Checklist.md`
> - `docs/Agent_Template.md`

Use this checklist to visually track what is pending, in progress, and complete. Replace `[ ]` with `[x]` as work is completed.

---

# 0. Progress Dashboard

| Area | Total Items | Done | Notes |
|---|---:|---:|---|
| Global foundation + all phases | 1855 |  | Update manually as you complete sections |
| Phase 0: Foundation: Shared Contracts, Runtime Layer, Control Plane, and Host | 197 |  |  |
| Phase 1: Research Department | 301 |  |  |
| Phase 2: Strategy Development Department | 353 |  |  |
| Phase 3: Simulation Department | 223 |  |  |
| Phase 4: Validation & Backtesting Package | 119 |  |  |
| Phase 5: Risk Department | 171 |  |  |
| Phase 6: Portfolio & Execution Department | 327 |  |  |
| Phase 7: Operations & Audit Department | 93 |  |  |
| Phase 8: Dedicated Audit Department | 41 |  |  |

---

# 1. Global Foundation Checklist

- [ ] Create `docs/Agentic_AI_Playbook.md`
- [ ] Create `docs/Agent_Auditing_Checklist.md`
- [ ] Create `docs/Agent_Template.md`
- [ ] Create canonical `agentic/` repository structure
- [ ] Create `agentic/agents/_shared/base_agent.py`
- [ ] Create `agentic/agents/_shared/manifest_schema.py`
- [ ] Create `agentic/agents/_shared/agent_result.py`
- [ ] Create `agentic/agents/_shared/guardrails.py`
- [ ] Create `agentic/agents/_shared/permissions.py`
- [ ] Create `agentic/agents/_shared/lifecycle.py`
- [ ] Create shared `EvidenceItem` contract
- [ ] Create shared `AuditRecord` contract
- [ ] Create shared `PermissionProfile` contract
- [ ] Create shared `EvaluationResult` contract
- [ ] Create shared `HandoffPayload` contract
- [ ] Create `agentic/policy/policy_engine.py`
- [ ] Create `agentic/approvals/approval_service.py`
- [ ] Create `agentic/evaluation/quality_gate.py`
- [ ] Create `agentic/observability/audit_log.py`
- [ ] Create `agentic/security/access_control.py`
- [ ] Create `registry/agents/`
- [ ] Create `registry/workflows/`
- [ ] Create `registry/capabilities/`
- [ ] Create `audit/reports/`
- [ ] Create `audit/evidence/`
- [ ] Create manifest validation script
- [ ] Create workflow registry validation script
- [ ] Create capability registry validation script
- [ ] Create agent registry quality gate
- [ ] Create CI quality gate workflow

---

# 2. Phase-by-Phase Department Checklist

# Phase 0: Foundation: Shared Contracts, Runtime Layer, Control Plane, and Host

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### LLM Registry

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `LLM Registry` with a realistic standalone request.
- [ ] User can ask `LLM Registry` to explain missing inputs or blocked actions.
- [ ] User can inspect `LLM Registry` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `LLM Registry` passes schema tests.
- [ ] `LLM Registry` passes permission tests.
- [ ] `LLM Registry` passes deterministic policy tests.
- [ ] `LLM Registry` passes evaluator tests.
- [ ] `LLM Registry` passes standalone user workflow tests.
- [ ] `LLM Registry` has no critical audit fail conditions.

### Model Runtime Adapter

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Model Runtime Adapter` with a realistic standalone request.
- [ ] User can ask `Model Runtime Adapter` to explain missing inputs or blocked actions.
- [ ] User can inspect `Model Runtime Adapter` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Model Runtime Adapter` passes schema tests.
- [ ] `Model Runtime Adapter` passes permission tests.
- [ ] `Model Runtime Adapter` passes deterministic policy tests.
- [ ] `Model Runtime Adapter` passes evaluator tests.
- [ ] `Model Runtime Adapter` passes standalone user workflow tests.
- [ ] `Model Runtime Adapter` has no critical audit fail conditions.

### Tool Executor

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Tool Executor` with a realistic standalone request.
- [ ] User can ask `Tool Executor` to explain missing inputs or blocked actions.
- [ ] User can inspect `Tool Executor` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Tool Executor` passes schema tests.
- [ ] `Tool Executor` passes permission tests.
- [ ] `Tool Executor` passes deterministic policy tests.
- [ ] `Tool Executor` passes evaluator tests.
- [ ] `Tool Executor` passes standalone user workflow tests.
- [ ] `Tool Executor` has no critical audit fail conditions.

### Execution Context

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Execution Context` with a realistic standalone request.
- [ ] User can ask `Execution Context` to explain missing inputs or blocked actions.
- [ ] User can inspect `Execution Context` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Execution Context` passes schema tests.
- [ ] `Execution Context` passes permission tests.
- [ ] `Execution Context` passes deterministic policy tests.
- [ ] `Execution Context` passes evaluator tests.
- [ ] `Execution Context` passes standalone user workflow tests.
- [ ] `Execution Context` has no critical audit fail conditions.

### Planner Agent

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Planner Agent` with a realistic standalone request.
- [ ] User can ask `Planner Agent` to explain missing inputs or blocked actions.
- [ ] User can inspect `Planner Agent` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Planner Agent` passes schema tests.
- [ ] `Planner Agent` passes permission tests.
- [ ] `Planner Agent` passes deterministic policy tests.
- [ ] `Planner Agent` passes evaluator tests.
- [ ] `Planner Agent` passes standalone user workflow tests.
- [ ] `Planner Agent` has no critical audit fail conditions.

### AI CEO / CIO Agent

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `AI CEO / CIO Agent` with a realistic standalone request.
- [ ] User can ask `AI CEO / CIO Agent` to explain missing inputs or blocked actions.
- [ ] User can inspect `AI CEO / CIO Agent` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `AI CEO / CIO Agent` passes schema tests.
- [ ] `AI CEO / CIO Agent` passes permission tests.
- [ ] `AI CEO / CIO Agent` passes deterministic policy tests.
- [ ] `AI CEO / CIO Agent` passes evaluator tests.
- [ ] `AI CEO / CIO Agent` passes standalone user workflow tests.
- [ ] `AI CEO / CIO Agent` has no critical audit fail conditions.

### Control Plane

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Control Plane` with a realistic standalone request.
- [ ] User can ask `Control Plane` to explain missing inputs or blocked actions.
- [ ] User can inspect `Control Plane` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Control Plane` passes schema tests.
- [ ] `Control Plane` passes permission tests.
- [ ] `Control Plane` passes deterministic policy tests.
- [ ] `Control Plane` passes evaluator tests.
- [ ] `Control Plane` passes standalone user workflow tests.
- [ ] `Control Plane` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 0 agents pass their agent exit gates.
- [ ] Phase 0 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 0 department handoff validates against schema.
- [ ] Phase 0 department audit metadata is complete.
- [ ] Phase 0 department can be integrated into the next phase.

---

# Phase 1: Research Department

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### Research Orchestrator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Research Orchestrator` with a realistic standalone request.
- [ ] User can ask `Research Orchestrator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Research Orchestrator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Research Orchestrator` passes schema tests.
- [ ] `Research Orchestrator` passes permission tests.
- [ ] `Research Orchestrator` passes deterministic policy tests.
- [ ] `Research Orchestrator` passes evaluator tests.
- [ ] `Research Orchestrator` passes standalone user workflow tests.
- [ ] `Research Orchestrator` has no critical audit fail conditions.

### Market Intelligence

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Market Intelligence` with a realistic standalone request.
- [ ] User can ask `Market Intelligence` to explain missing inputs or blocked actions.
- [ ] User can inspect `Market Intelligence` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Market Intelligence` passes schema tests.
- [ ] `Market Intelligence` passes permission tests.
- [ ] `Market Intelligence` passes deterministic policy tests.
- [ ] `Market Intelligence` passes evaluator tests.
- [ ] `Market Intelligence` passes standalone user workflow tests.
- [ ] `Market Intelligence` has no critical audit fail conditions.

### Technical Analyst

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Technical Analyst` with a realistic standalone request.
- [ ] User can ask `Technical Analyst` to explain missing inputs or blocked actions.
- [ ] User can inspect `Technical Analyst` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Technical Analyst` passes schema tests.
- [ ] `Technical Analyst` passes permission tests.
- [ ] `Technical Analyst` passes deterministic policy tests.
- [ ] `Technical Analyst` passes evaluator tests.
- [ ] `Technical Analyst` passes standalone user workflow tests.
- [ ] `Technical Analyst` has no critical audit fail conditions.

### Strategy Hypothesis

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Hypothesis` with a realistic standalone request.
- [ ] User can ask `Strategy Hypothesis` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Hypothesis` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Hypothesis` passes schema tests.
- [ ] `Strategy Hypothesis` passes permission tests.
- [ ] `Strategy Hypothesis` passes deterministic policy tests.
- [ ] `Strategy Hypothesis` passes evaluator tests.
- [ ] `Strategy Hypothesis` passes standalone user workflow tests.
- [ ] `Strategy Hypothesis` has no critical audit fail conditions.

### Evidence Curator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Evidence Curator` with a realistic standalone request.
- [ ] User can ask `Evidence Curator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Evidence Curator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Evidence Curator` passes schema tests.
- [ ] `Evidence Curator` passes permission tests.
- [ ] `Evidence Curator` passes deterministic policy tests.
- [ ] `Evidence Curator` passes evaluator tests.
- [ ] `Evidence Curator` passes standalone user workflow tests.
- [ ] `Evidence Curator` has no critical audit fail conditions.

### Macro / Fundamental Context

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Macro / Fundamental Context` with a realistic standalone request.
- [ ] User can ask `Macro / Fundamental Context` to explain missing inputs or blocked actions.
- [ ] User can inspect `Macro / Fundamental Context` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Macro / Fundamental Context` passes schema tests.
- [ ] `Macro / Fundamental Context` passes permission tests.
- [ ] `Macro / Fundamental Context` passes deterministic policy tests.
- [ ] `Macro / Fundamental Context` passes evaluator tests.
- [ ] `Macro / Fundamental Context` passes standalone user workflow tests.
- [ ] `Macro / Fundamental Context` has no critical audit fail conditions.

### Seasonality Calendar

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Seasonality Calendar` with a realistic standalone request.
- [ ] User can ask `Seasonality Calendar` to explain missing inputs or blocked actions.
- [ ] User can inspect `Seasonality Calendar` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Seasonality Calendar` passes schema tests.
- [ ] `Seasonality Calendar` passes permission tests.
- [ ] `Seasonality Calendar` passes deterministic policy tests.
- [ ] `Seasonality Calendar` passes evaluator tests.
- [ ] `Seasonality Calendar` passes standalone user workflow tests.
- [ ] `Seasonality Calendar` has no critical audit fail conditions.

### Strategy Scout

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Scout` with a realistic standalone request.
- [ ] User can ask `Strategy Scout` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Scout` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Scout` passes schema tests.
- [ ] `Strategy Scout` passes permission tests.
- [ ] `Strategy Scout` passes deterministic policy tests.
- [ ] `Strategy Scout` passes evaluator tests.
- [ ] `Strategy Scout` passes standalone user workflow tests.
- [ ] `Strategy Scout` has no critical audit fail conditions.

### Research Validation

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Research Validation` with a realistic standalone request.
- [ ] User can ask `Research Validation` to explain missing inputs or blocked actions.
- [ ] User can inspect `Research Validation` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Research Validation` passes schema tests.
- [ ] `Research Validation` passes permission tests.
- [ ] `Research Validation` passes deterministic policy tests.
- [ ] `Research Validation` passes evaluator tests.
- [ ] `Research Validation` passes standalone user workflow tests.
- [ ] `Research Validation` has no critical audit fail conditions.

### News Sentiment

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `News Sentiment` with a realistic standalone request.
- [ ] User can ask `News Sentiment` to explain missing inputs or blocked actions.
- [ ] User can inspect `News Sentiment` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `News Sentiment` passes schema tests.
- [ ] `News Sentiment` passes permission tests.
- [ ] `News Sentiment` passes deterministic policy tests.
- [ ] `News Sentiment` passes evaluator tests.
- [ ] `News Sentiment` passes standalone user workflow tests.
- [ ] `News Sentiment` has no critical audit fail conditions.

### Cross Asset / Intermarket

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Cross Asset / Intermarket` with a realistic standalone request.
- [ ] User can ask `Cross Asset / Intermarket` to explain missing inputs or blocked actions.
- [ ] User can inspect `Cross Asset / Intermarket` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Cross Asset / Intermarket` passes schema tests.
- [ ] `Cross Asset / Intermarket` passes permission tests.
- [ ] `Cross Asset / Intermarket` passes deterministic policy tests.
- [ ] `Cross Asset / Intermarket` passes evaluator tests.
- [ ] `Cross Asset / Intermarket` passes standalone user workflow tests.
- [ ] `Cross Asset / Intermarket` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 1 agents pass their agent exit gates.
- [ ] Phase 1 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 1 department handoff validates against schema.
- [ ] Phase 1 department audit metadata is complete.
- [ ] Phase 1 department can be integrated into the next phase.

---

# Phase 2: Strategy Development Department

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### Strategy Creation Orchestrator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Creation Orchestrator` with a realistic standalone request.
- [ ] User can ask `Strategy Creation Orchestrator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Creation Orchestrator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Creation Orchestrator` passes schema tests.
- [ ] `Strategy Creation Orchestrator` passes permission tests.
- [ ] `Strategy Creation Orchestrator` passes deterministic policy tests.
- [ ] `Strategy Creation Orchestrator` passes evaluator tests.
- [ ] `Strategy Creation Orchestrator` passes standalone user workflow tests.
- [ ] `Strategy Creation Orchestrator` has no critical audit fail conditions.

### Strategy Creator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Creator` with a realistic standalone request.
- [ ] User can ask `Strategy Creator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Creator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Creator` passes schema tests.
- [ ] `Strategy Creator` passes permission tests.
- [ ] `Strategy Creator` passes deterministic policy tests.
- [ ] `Strategy Creator` passes evaluator tests.
- [ ] `Strategy Creator` passes standalone user workflow tests.
- [ ] `Strategy Creator` has no critical audit fail conditions.

### Strategy Spec Validator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Spec Validator` with a realistic standalone request.
- [ ] User can ask `Strategy Spec Validator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Spec Validator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Spec Validator` passes schema tests.
- [ ] `Strategy Spec Validator` passes permission tests.
- [ ] `Strategy Spec Validator` passes deterministic policy tests.
- [ ] `Strategy Spec Validator` passes evaluator tests.
- [ ] `Strategy Spec Validator` passes standalone user workflow tests.
- [ ] `Strategy Spec Validator` has no critical audit fail conditions.

### Strategy Rule Normalizer

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Rule Normalizer` with a realistic standalone request.
- [ ] User can ask `Strategy Rule Normalizer` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Rule Normalizer` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Rule Normalizer` passes schema tests.
- [ ] `Strategy Rule Normalizer` passes permission tests.
- [ ] `Strategy Rule Normalizer` passes deterministic policy tests.
- [ ] `Strategy Rule Normalizer` passes evaluator tests.
- [ ] `Strategy Rule Normalizer` passes standalone user workflow tests.
- [ ] `Strategy Rule Normalizer` has no critical audit fail conditions.

### Strategy Template Selector

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Template Selector` with a realistic standalone request.
- [ ] User can ask `Strategy Template Selector` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Template Selector` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Template Selector` passes schema tests.
- [ ] `Strategy Template Selector` passes permission tests.
- [ ] `Strategy Template Selector` passes deterministic policy tests.
- [ ] `Strategy Template Selector` passes evaluator tests.
- [ ] `Strategy Template Selector` passes standalone user workflow tests.
- [ ] `Strategy Template Selector` has no critical audit fail conditions.

### Strategy Risk Assumption

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Risk Assumption` with a realistic standalone request.
- [ ] User can ask `Strategy Risk Assumption` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Risk Assumption` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Risk Assumption` passes schema tests.
- [ ] `Strategy Risk Assumption` passes permission tests.
- [ ] `Strategy Risk Assumption` passes deterministic policy tests.
- [ ] `Strategy Risk Assumption` passes evaluator tests.
- [ ] `Strategy Risk Assumption` passes standalone user workflow tests.
- [ ] `Strategy Risk Assumption` has no critical audit fail conditions.

### Strategy Test Plan

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Test Plan` with a realistic standalone request.
- [ ] User can ask `Strategy Test Plan` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Test Plan` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Test Plan` passes schema tests.
- [ ] `Strategy Test Plan` passes permission tests.
- [ ] `Strategy Test Plan` passes deterministic policy tests.
- [ ] `Strategy Test Plan` passes evaluator tests.
- [ ] `Strategy Test Plan` passes standalone user workflow tests.
- [ ] `Strategy Test Plan` has no critical audit fail conditions.

### Strategy Cost Execution

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Cost Execution` with a realistic standalone request.
- [ ] User can ask `Strategy Cost Execution` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Cost Execution` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Cost Execution` passes schema tests.
- [ ] `Strategy Cost Execution` passes permission tests.
- [ ] `Strategy Cost Execution` passes deterministic policy tests.
- [ ] `Strategy Cost Execution` passes evaluator tests.
- [ ] `Strategy Cost Execution` passes standalone user workflow tests.
- [ ] `Strategy Cost Execution` has no critical audit fail conditions.

### Strategy Codegen

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Codegen` with a realistic standalone request.
- [ ] User can ask `Strategy Codegen` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Codegen` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Codegen` passes schema tests.
- [ ] `Strategy Codegen` passes permission tests.
- [ ] `Strategy Codegen` passes deterministic policy tests.
- [ ] `Strategy Codegen` passes evaluator tests.
- [ ] `Strategy Codegen` passes standalone user workflow tests.
- [ ] `Strategy Codegen` has no critical audit fail conditions.

### Strategy Reviewer

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Reviewer` with a realistic standalone request.
- [ ] User can ask `Strategy Reviewer` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Reviewer` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Reviewer` passes schema tests.
- [ ] `Strategy Reviewer` passes permission tests.
- [ ] `Strategy Reviewer` passes deterministic policy tests.
- [ ] `Strategy Reviewer` passes evaluator tests.
- [ ] `Strategy Reviewer` passes standalone user workflow tests.
- [ ] `Strategy Reviewer` has no critical audit fail conditions.

### Strategy Spec Storage

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Spec Storage` with a realistic standalone request.
- [ ] User can ask `Strategy Spec Storage` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Spec Storage` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Spec Storage` passes schema tests.
- [ ] `Strategy Spec Storage` passes permission tests.
- [ ] `Strategy Spec Storage` passes deterministic policy tests.
- [ ] `Strategy Spec Storage` passes evaluator tests.
- [ ] `Strategy Spec Storage` passes standalone user workflow tests.
- [ ] `Strategy Spec Storage` has no critical audit fail conditions.

### Strategy Code Storage

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Code Storage` with a realistic standalone request.
- [ ] User can ask `Strategy Code Storage` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Code Storage` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Code Storage` passes schema tests.
- [ ] `Strategy Code Storage` passes permission tests.
- [ ] `Strategy Code Storage` passes deterministic policy tests.
- [ ] `Strategy Code Storage` passes evaluator tests.
- [ ] `Strategy Code Storage` passes standalone user workflow tests.
- [ ] `Strategy Code Storage` has no critical audit fail conditions.

### Strategy Handoff

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Handoff` with a realistic standalone request.
- [ ] User can ask `Strategy Handoff` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Handoff` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Handoff` passes schema tests.
- [ ] `Strategy Handoff` passes permission tests.
- [ ] `Strategy Handoff` passes deterministic policy tests.
- [ ] `Strategy Handoff` passes evaluator tests.
- [ ] `Strategy Handoff` passes standalone user workflow tests.
- [ ] `Strategy Handoff` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 2 agents pass their agent exit gates.
- [ ] Phase 2 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 2 department handoff validates against schema.
- [ ] Phase 2 department audit metadata is complete.
- [ ] Phase 2 department can be integrated into the next phase.

---

# Phase 3: Simulation Department

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### Simulation Orchestrator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Simulation Orchestrator` with a realistic standalone request.
- [ ] User can ask `Simulation Orchestrator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Simulation Orchestrator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Simulation Orchestrator` passes schema tests.
- [ ] `Simulation Orchestrator` passes permission tests.
- [ ] `Simulation Orchestrator` passes deterministic policy tests.
- [ ] `Simulation Orchestrator` passes evaluator tests.
- [ ] `Simulation Orchestrator` passes standalone user workflow tests.
- [ ] `Simulation Orchestrator` has no critical audit fail conditions.

### Backtest

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Backtest` with a realistic standalone request.
- [ ] User can ask `Backtest` to explain missing inputs or blocked actions.
- [ ] User can inspect `Backtest` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Backtest` passes schema tests.
- [ ] `Backtest` passes permission tests.
- [ ] `Backtest` passes deterministic policy tests.
- [ ] `Backtest` passes evaluator tests.
- [ ] `Backtest` passes standalone user workflow tests.
- [ ] `Backtest` has no critical audit fail conditions.

### Backtest Analyst

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Backtest Analyst` with a realistic standalone request.
- [ ] User can ask `Backtest Analyst` to explain missing inputs or blocked actions.
- [ ] User can inspect `Backtest Analyst` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Backtest Analyst` passes schema tests.
- [ ] `Backtest Analyst` passes permission tests.
- [ ] `Backtest Analyst` passes deterministic policy tests.
- [ ] `Backtest Analyst` passes evaluator tests.
- [ ] `Backtest Analyst` passes standalone user workflow tests.
- [ ] `Backtest Analyst` has no critical audit fail conditions.

### Optimization

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Optimization` with a realistic standalone request.
- [ ] User can ask `Optimization` to explain missing inputs or blocked actions.
- [ ] User can inspect `Optimization` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Optimization` passes schema tests.
- [ ] `Optimization` passes permission tests.
- [ ] `Optimization` passes deterministic policy tests.
- [ ] `Optimization` passes evaluator tests.
- [ ] `Optimization` passes standalone user workflow tests.
- [ ] `Optimization` has no critical audit fail conditions.

### Optimization Comparator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Optimization Comparator` with a realistic standalone request.
- [ ] User can ask `Optimization Comparator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Optimization Comparator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Optimization Comparator` passes schema tests.
- [ ] `Optimization Comparator` passes permission tests.
- [ ] `Optimization Comparator` passes deterministic policy tests.
- [ ] `Optimization Comparator` passes evaluator tests.
- [ ] `Optimization Comparator` passes standalone user workflow tests.
- [ ] `Optimization Comparator` has no critical audit fail conditions.

### Robustness

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Robustness` with a realistic standalone request.
- [ ] User can ask `Robustness` to explain missing inputs or blocked actions.
- [ ] User can inspect `Robustness` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Robustness` passes schema tests.
- [ ] `Robustness` passes permission tests.
- [ ] `Robustness` passes deterministic policy tests.
- [ ] `Robustness` passes evaluator tests.
- [ ] `Robustness` passes standalone user workflow tests.
- [ ] `Robustness` has no critical audit fail conditions.

### Statistical Validation

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Statistical Validation` with a realistic standalone request.
- [ ] User can ask `Statistical Validation` to explain missing inputs or blocked actions.
- [ ] User can inspect `Statistical Validation` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Statistical Validation` passes schema tests.
- [ ] `Statistical Validation` passes permission tests.
- [ ] `Statistical Validation` passes deterministic policy tests.
- [ ] `Statistical Validation` passes evaluator tests.
- [ ] `Statistical Validation` passes standalone user workflow tests.
- [ ] `Statistical Validation` has no critical audit fail conditions.

### Simulation Evidence Curator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Simulation Evidence Curator` with a realistic standalone request.
- [ ] User can ask `Simulation Evidence Curator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Simulation Evidence Curator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Simulation Evidence Curator` passes schema tests.
- [ ] `Simulation Evidence Curator` passes permission tests.
- [ ] `Simulation Evidence Curator` passes deterministic policy tests.
- [ ] `Simulation Evidence Curator` passes evaluator tests.
- [ ] `Simulation Evidence Curator` passes standalone user workflow tests.
- [ ] `Simulation Evidence Curator` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 3 agents pass their agent exit gates.
- [ ] Phase 3 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 3 department handoff validates against schema.
- [ ] Phase 3 department audit metadata is complete.
- [ ] Phase 3 department can be integrated into the next phase.

---

# Phase 4: Validation & Backtesting Package

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### Validation Backtest

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Validation Backtest` with a realistic standalone request.
- [ ] User can ask `Validation Backtest` to explain missing inputs or blocked actions.
- [ ] User can inspect `Validation Backtest` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Validation Backtest` passes schema tests.
- [ ] `Validation Backtest` passes permission tests.
- [ ] `Validation Backtest` passes deterministic policy tests.
- [ ] `Validation Backtest` passes evaluator tests.
- [ ] `Validation Backtest` passes standalone user workflow tests.
- [ ] `Validation Backtest` has no critical audit fail conditions.

### Validation Optimization Comparator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Validation Optimization Comparator` with a realistic standalone request.
- [ ] User can ask `Validation Optimization Comparator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Validation Optimization Comparator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Validation Optimization Comparator` passes schema tests.
- [ ] `Validation Optimization Comparator` passes permission tests.
- [ ] `Validation Optimization Comparator` passes deterministic policy tests.
- [ ] `Validation Optimization Comparator` passes evaluator tests.
- [ ] `Validation Optimization Comparator` passes standalone user workflow tests.
- [ ] `Validation Optimization Comparator` has no critical audit fail conditions.

### Validation Robustness Monte Carlo

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Validation Robustness Monte Carlo` with a realistic standalone request.
- [ ] User can ask `Validation Robustness Monte Carlo` to explain missing inputs or blocked actions.
- [ ] User can inspect `Validation Robustness Monte Carlo` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Validation Robustness Monte Carlo` passes schema tests.
- [ ] `Validation Robustness Monte Carlo` passes permission tests.
- [ ] `Validation Robustness Monte Carlo` passes deterministic policy tests.
- [ ] `Validation Robustness Monte Carlo` passes evaluator tests.
- [ ] `Validation Robustness Monte Carlo` passes standalone user workflow tests.
- [ ] `Validation Robustness Monte Carlo` has no critical audit fail conditions.

### Validation Statistical Validation

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Validation Statistical Validation` with a realistic standalone request.
- [ ] User can ask `Validation Statistical Validation` to explain missing inputs or blocked actions.
- [ ] User can inspect `Validation Statistical Validation` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Validation Statistical Validation` passes schema tests.
- [ ] `Validation Statistical Validation` passes permission tests.
- [ ] `Validation Statistical Validation` passes deterministic policy tests.
- [ ] `Validation Statistical Validation` passes evaluator tests.
- [ ] `Validation Statistical Validation` passes standalone user workflow tests.
- [ ] `Validation Statistical Validation` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 4 agents pass their agent exit gates.
- [ ] Phase 4 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 4 department handoff validates against schema.
- [ ] Phase 4 department audit metadata is complete.
- [ ] Phase 4 department can be integrated into the next phase.

---

# Phase 5: Risk Department

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### Risk Orchestrator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Risk Orchestrator` with a realistic standalone request.
- [ ] User can ask `Risk Orchestrator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Risk Orchestrator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Risk Orchestrator` passes schema tests.
- [ ] `Risk Orchestrator` passes permission tests.
- [ ] `Risk Orchestrator` passes deterministic policy tests.
- [ ] `Risk Orchestrator` passes evaluator tests.
- [ ] `Risk Orchestrator` passes standalone user workflow tests.
- [ ] `Risk Orchestrator` has no critical audit fail conditions.

### Risk Reviewer

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Risk Reviewer` with a realistic standalone request.
- [ ] User can ask `Risk Reviewer` to explain missing inputs or blocked actions.
- [ ] User can inspect `Risk Reviewer` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Risk Reviewer` passes schema tests.
- [ ] `Risk Reviewer` passes permission tests.
- [ ] `Risk Reviewer` passes deterministic policy tests.
- [ ] `Risk Reviewer` passes evaluator tests.
- [ ] `Risk Reviewer` passes standalone user workflow tests.
- [ ] `Risk Reviewer` has no critical audit fail conditions.

### Hard-Coded Risk Governor

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Hard-Coded Risk Governor` with a realistic standalone request.
- [ ] User can ask `Hard-Coded Risk Governor` to explain missing inputs or blocked actions.
- [ ] User can inspect `Hard-Coded Risk Governor` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Hard-Coded Risk Governor` passes schema tests.
- [ ] `Hard-Coded Risk Governor` passes permission tests.
- [ ] `Hard-Coded Risk Governor` passes deterministic policy tests.
- [ ] `Hard-Coded Risk Governor` passes evaluator tests.
- [ ] `Hard-Coded Risk Governor` passes standalone user workflow tests.
- [ ] `Hard-Coded Risk Governor` has no critical audit fail conditions.

### Portfolio Risk Monitor

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Portfolio Risk Monitor` with a realistic standalone request.
- [ ] User can ask `Portfolio Risk Monitor` to explain missing inputs or blocked actions.
- [ ] User can inspect `Portfolio Risk Monitor` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Portfolio Risk Monitor` passes schema tests.
- [ ] `Portfolio Risk Monitor` passes permission tests.
- [ ] `Portfolio Risk Monitor` passes deterministic policy tests.
- [ ] `Portfolio Risk Monitor` passes evaluator tests.
- [ ] `Portfolio Risk Monitor` passes standalone user workflow tests.
- [ ] `Portfolio Risk Monitor` has no critical audit fail conditions.

### Risk Limit Auditor

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Risk Limit Auditor` with a realistic standalone request.
- [ ] User can ask `Risk Limit Auditor` to explain missing inputs or blocked actions.
- [ ] User can inspect `Risk Limit Auditor` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Risk Limit Auditor` passes schema tests.
- [ ] `Risk Limit Auditor` passes permission tests.
- [ ] `Risk Limit Auditor` passes deterministic policy tests.
- [ ] `Risk Limit Auditor` passes evaluator tests.
- [ ] `Risk Limit Auditor` passes standalone user workflow tests.
- [ ] `Risk Limit Auditor` has no critical audit fail conditions.

### Risk Approval Auditor

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Risk Approval Auditor` with a realistic standalone request.
- [ ] User can ask `Risk Approval Auditor` to explain missing inputs or blocked actions.
- [ ] User can inspect `Risk Approval Auditor` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Risk Approval Auditor` passes schema tests.
- [ ] `Risk Approval Auditor` passes permission tests.
- [ ] `Risk Approval Auditor` passes deterministic policy tests.
- [ ] `Risk Approval Auditor` passes evaluator tests.
- [ ] `Risk Approval Auditor` passes standalone user workflow tests.
- [ ] `Risk Approval Auditor` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 5 agents pass their agent exit gates.
- [ ] Phase 5 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 5 department handoff validates against schema.
- [ ] Phase 5 department audit metadata is complete.
- [ ] Phase 5 department can be integrated into the next phase.

---

# Phase 6: Portfolio & Execution Department

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### Portfolio Orchestrator

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Portfolio Orchestrator` with a realistic standalone request.
- [ ] User can ask `Portfolio Orchestrator` to explain missing inputs or blocked actions.
- [ ] User can inspect `Portfolio Orchestrator` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Portfolio Orchestrator` passes schema tests.
- [ ] `Portfolio Orchestrator` passes permission tests.
- [ ] `Portfolio Orchestrator` passes deterministic policy tests.
- [ ] `Portfolio Orchestrator` passes evaluator tests.
- [ ] `Portfolio Orchestrator` passes standalone user workflow tests.
- [ ] `Portfolio Orchestrator` has no critical audit fail conditions.

### Portfolio Manager

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Portfolio Manager` with a realistic standalone request.
- [ ] User can ask `Portfolio Manager` to explain missing inputs or blocked actions.
- [ ] User can inspect `Portfolio Manager` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Portfolio Manager` passes schema tests.
- [ ] `Portfolio Manager` passes permission tests.
- [ ] `Portfolio Manager` passes deterministic policy tests.
- [ ] `Portfolio Manager` passes evaluator tests.
- [ ] `Portfolio Manager` passes standalone user workflow tests.
- [ ] `Portfolio Manager` has no critical audit fail conditions.

### Allocation Optimizer

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Allocation Optimizer` with a realistic standalone request.
- [ ] User can ask `Allocation Optimizer` to explain missing inputs or blocked actions.
- [ ] User can inspect `Allocation Optimizer` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Allocation Optimizer` passes schema tests.
- [ ] `Allocation Optimizer` passes permission tests.
- [ ] `Allocation Optimizer` passes deterministic policy tests.
- [ ] `Allocation Optimizer` passes evaluator tests.
- [ ] `Allocation Optimizer` passes standalone user workflow tests.
- [ ] `Allocation Optimizer` has no critical audit fail conditions.

### Strategy Lifecycle

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Strategy Lifecycle` with a realistic standalone request.
- [ ] User can ask `Strategy Lifecycle` to explain missing inputs or blocked actions.
- [ ] User can inspect `Strategy Lifecycle` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Strategy Lifecycle` passes schema tests.
- [ ] `Strategy Lifecycle` passes permission tests.
- [ ] `Strategy Lifecycle` passes deterministic policy tests.
- [ ] `Strategy Lifecycle` passes evaluator tests.
- [ ] `Strategy Lifecycle` passes standalone user workflow tests.
- [ ] `Strategy Lifecycle` has no critical audit fail conditions.

### Execution Planner

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Execution Planner` with a realistic standalone request.
- [ ] User can ask `Execution Planner` to explain missing inputs or blocked actions.
- [ ] User can inspect `Execution Planner` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Execution Planner` passes schema tests.
- [ ] `Execution Planner` passes permission tests.
- [ ] `Execution Planner` passes deterministic policy tests.
- [ ] `Execution Planner` passes evaluator tests.
- [ ] `Execution Planner` passes standalone user workflow tests.
- [ ] `Execution Planner` has no critical audit fail conditions.

### Execution Readiness

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Execution Readiness` with a realistic standalone request.
- [ ] User can ask `Execution Readiness` to explain missing inputs or blocked actions.
- [ ] User can inspect `Execution Readiness` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Execution Readiness` passes schema tests.
- [ ] `Execution Readiness` passes permission tests.
- [ ] `Execution Readiness` passes deterministic policy tests.
- [ ] `Execution Readiness` passes evaluator tests.
- [ ] `Execution Readiness` passes standalone user workflow tests.
- [ ] `Execution Readiness` has no critical audit fail conditions.

### Paper Execution

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Paper Execution` with a realistic standalone request.
- [ ] User can ask `Paper Execution` to explain missing inputs or blocked actions.
- [ ] User can inspect `Paper Execution` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Paper Execution` passes schema tests.
- [ ] `Paper Execution` passes permission tests.
- [ ] `Paper Execution` passes deterministic policy tests.
- [ ] `Paper Execution` passes evaluator tests.
- [ ] `Paper Execution` passes standalone user workflow tests.
- [ ] `Paper Execution` has no critical audit fail conditions.

### Live Execution

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Live Execution` with a realistic standalone request.
- [ ] User can ask `Live Execution` to explain missing inputs or blocked actions.
- [ ] User can inspect `Live Execution` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Live Execution` passes schema tests.
- [ ] `Live Execution` passes permission tests.
- [ ] `Live Execution` passes deterministic policy tests.
- [ ] `Live Execution` passes evaluator tests.
- [ ] `Live Execution` passes standalone user workflow tests.
- [ ] `Live Execution` has no critical audit fail conditions.

### MT5 / cTrader Execution Bridge

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `MT5 / cTrader Execution Bridge` with a realistic standalone request.
- [ ] User can ask `MT5 / cTrader Execution Bridge` to explain missing inputs or blocked actions.
- [ ] User can inspect `MT5 / cTrader Execution Bridge` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `MT5 / cTrader Execution Bridge` passes schema tests.
- [ ] `MT5 / cTrader Execution Bridge` passes permission tests.
- [ ] `MT5 / cTrader Execution Bridge` passes deterministic policy tests.
- [ ] `MT5 / cTrader Execution Bridge` passes evaluator tests.
- [ ] `MT5 / cTrader Execution Bridge` passes standalone user workflow tests.
- [ ] `MT5 / cTrader Execution Bridge` has no critical audit fail conditions.

### Kill Switch Service

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Kill Switch Service` with a realistic standalone request.
- [ ] User can ask `Kill Switch Service` to explain missing inputs or blocked actions.
- [ ] User can inspect `Kill Switch Service` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Kill Switch Service` passes schema tests.
- [ ] `Kill Switch Service` passes permission tests.
- [ ] `Kill Switch Service` passes deterministic policy tests.
- [ ] `Kill Switch Service` passes evaluator tests.
- [ ] `Kill Switch Service` passes standalone user workflow tests.
- [ ] `Kill Switch Service` has no critical audit fail conditions.

### Performance Reporter

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Performance Reporter` with a realistic standalone request.
- [ ] User can ask `Performance Reporter` to explain missing inputs or blocked actions.
- [ ] User can inspect `Performance Reporter` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Performance Reporter` passes schema tests.
- [ ] `Performance Reporter` passes permission tests.
- [ ] `Performance Reporter` passes deterministic policy tests.
- [ ] `Performance Reporter` passes evaluator tests.
- [ ] `Performance Reporter` passes standalone user workflow tests.
- [ ] `Performance Reporter` has no critical audit fail conditions.

### Cost Optimizer

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Cost Optimizer` with a realistic standalone request.
- [ ] User can ask `Cost Optimizer` to explain missing inputs or blocked actions.
- [ ] User can inspect `Cost Optimizer` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Cost Optimizer` passes schema tests.
- [ ] `Cost Optimizer` passes permission tests.
- [ ] `Cost Optimizer` passes deterministic policy tests.
- [ ] `Cost Optimizer` passes evaluator tests.
- [ ] `Cost Optimizer` passes standalone user workflow tests.
- [ ] `Cost Optimizer` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 6 agents pass their agent exit gates.
- [ ] Phase 6 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 6 department handoff validates against schema.
- [ ] Phase 6 department audit metadata is complete.
- [ ] Phase 6 department can be integrated into the next phase.

---

# Phase 7: Operations & Audit Department

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### Audit Compliance

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Audit Compliance` with a realistic standalone request.
- [ ] User can ask `Audit Compliance` to explain missing inputs or blocked actions.
- [ ] User can inspect `Audit Compliance` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Audit Compliance` passes schema tests.
- [ ] `Audit Compliance` passes permission tests.
- [ ] `Audit Compliance` passes deterministic policy tests.
- [ ] `Audit Compliance` passes evaluator tests.
- [ ] `Audit Compliance` passes standalone user workflow tests.
- [ ] `Audit Compliance` has no critical audit fail conditions.

### Operations Performance Reporter

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Operations Performance Reporter` with a realistic standalone request.
- [ ] User can ask `Operations Performance Reporter` to explain missing inputs or blocked actions.
- [ ] User can inspect `Operations Performance Reporter` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Operations Performance Reporter` passes schema tests.
- [ ] `Operations Performance Reporter` passes permission tests.
- [ ] `Operations Performance Reporter` passes deterministic policy tests.
- [ ] `Operations Performance Reporter` passes evaluator tests.
- [ ] `Operations Performance Reporter` passes standalone user workflow tests.
- [ ] `Operations Performance Reporter` has no critical audit fail conditions.

### Operations Cost Optimizer

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Operations Cost Optimizer` with a realistic standalone request.
- [ ] User can ask `Operations Cost Optimizer` to explain missing inputs or blocked actions.
- [ ] User can inspect `Operations Cost Optimizer` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Operations Cost Optimizer` passes schema tests.
- [ ] `Operations Cost Optimizer` passes permission tests.
- [ ] `Operations Cost Optimizer` passes deterministic policy tests.
- [ ] `Operations Cost Optimizer` passes evaluator tests.
- [ ] `Operations Cost Optimizer` passes standalone user workflow tests.
- [ ] `Operations Cost Optimizer` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 7 agents pass their agent exit gates.
- [ ] Phase 7 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 7 department handoff validates against schema.
- [ ] Phase 7 department audit metadata is complete.
- [ ] Phase 7 department can be integrated into the next phase.

---

# Phase 8: Dedicated Audit Department

## Department-Level Checklist

- [ ] Department folder created
- [ ] Department shared schemas/contracts created
- [ ] Department permission profile defaults defined
- [ ] Department audit requirements defined
- [ ] Department workflow folder created under `agentic/workflows/`
- [ ] `workflow.py` implemented
- [ ] `workflow.yaml` implemented
- [ ] Department README implemented
- [ ] Department registry entry added under `registry/workflows/`
- [ ] Department-level unit tests implemented
- [ ] Department-level user workflow tests implemented
- [ ] Department can run independently with fixture inputs
- [ ] Department handoff package validates
- [ ] Department audit report created
- [ ] Department acceptance exit gate passed

## Agent-by-Agent Checklist

### Audit Agent

| Status | Item |
|---|---|
| [ ] | Required folder created under `agentic/agents/<department>/<agent_name>/` |
| [ ] | `agent.py` implemented |
| [ ] | `prompt.md` implemented and versioned |
| [ ] | `manifest.yaml` implemented |
| [ ] | `schemas.py` implemented |
| [ ] | `README.md` implemented |
| [ ] | Registry entry added under `registry/agents/` |
| [ ] | Purpose documented |
| [ ] | Non-goals documented |
| [ ] | Inputs documented |
| [ ] | Outputs documented |
| [ ] | Tools/capabilities declared |
| [ ] | Evidence requirements documented |
| [ ] | LLM responsibilities documented |
| [ ] | Deterministic decision rules implemented |
| [ ] | Allowed actions documented |
| [ ] | Blocked actions documented |
| [ ] | Permission profile implemented |
| [ ] | Audit metadata implemented |
| [ ] | Evaluator implemented |
| [ ] | Standalone local run works |
| [ ] | Unit tests implemented |
| [ ] | User workflow tests implemented |
| [ ] | Integration handoff contract implemented |
| [ ] | Audit report stub created |
| [ ] | Acceptance exit gate passed |

#### User Workflow Test Prompts

- [ ] User can run `Audit Agent` with a realistic standalone request.
- [ ] User can ask `Audit Agent` to explain missing inputs or blocked actions.
- [ ] User can inspect `Audit Agent` output, evidence, decision, and audit metadata.

#### Agent Exit Gate

- [ ] `Audit Agent` passes schema tests.
- [ ] `Audit Agent` passes permission tests.
- [ ] `Audit Agent` passes deterministic policy tests.
- [ ] `Audit Agent` passes evaluator tests.
- [ ] `Audit Agent` passes standalone user workflow tests.
- [ ] `Audit Agent` has no critical audit fail conditions.

## Department Acceptance Exit Gate

- [ ] All Phase 8 agents pass their agent exit gates.
- [ ] Phase 8 department workflow runs end-to-end with fixture inputs.
- [ ] Phase 8 department handoff validates against schema.
- [ ] Phase 8 department audit metadata is complete.
- [ ] Phase 8 department can be integrated into the next phase.

---

# 3. Integration Milestone Checklist

## Milestone 1: Foundation Ready

- [ ] Shared contracts implemented
- [ ] Permission model implemented
- [ ] Audit envelope implemented
- [ ] Tool executor implemented
- [ ] Runtime/model adapter implemented
- [ ] Planner runs with mocked department agents
- [ ] Control Plane runs with mocked workflows
- [ ] Registry loaders work
- [ ] Quality gates run in CI

## Milestone 2: Research to Strategy

- [ ] Research evidence package schema validates
- [ ] Strategy Development rejects incomplete research
- [ ] Evidence references are preserved across handoff
- [ ] User can request strategy/design candidate from research evidence

## Milestone 3: Strategy to Simulation

- [ ] Strategy handoff includes spec, code/artifact refs, assumptions, and test plan
- [ ] Simulation rejects missing data/config
- [ ] Simulation results are reproducible

## Milestone 4: Simulation to Risk

- [ ] Risk rejects weak or missing evidence
- [ ] Hard-coded governor fails closed
- [ ] Approval auditor detects missing or expired approvals

## Milestone 5: Risk to Portfolio / Execution

- [ ] No execution can happen without risk/control decision
- [ ] Readiness blocks missing approvals
- [ ] Kill switch blocks execution
- [ ] Execution bridge enforces idempotency

## Milestone 6: Operations and Audit

- [ ] Every run is traceable
- [ ] Every agent has audit report
- [ ] Critical fail conditions block production
- [ ] CI quality gates fail on manifest/test/permission violations

---

# 4. Global Acceptance Checklist

- [ ] Every agent has a manifest
- [ ] Every agent has schemas
- [ ] Every agent has a permission profile
- [ ] Every agent has deterministic policy checks
- [ ] Every agent has audit metadata
- [ ] Every agent has unit tests
- [ ] Every agent has user workflow tests
- [ ] Every department runs independently
- [ ] Every department handoff validates
- [ ] All high-impact actions require approval
- [ ] All production actions are blocked in non-production
- [ ] Audit Agent can score every agent using `docs/Agent_Auditing_Checklist.md`
- [ ] System conforms to `docs/Agentic_AI_Playbook.md`
- [ ] System conforms to `docs/Agent_Template.md`

---

# 5. Audit Readiness Checklist

- [ ] All manifests validate
- [ ] All workflow registries validate
- [ ] All capability registries validate
- [ ] All agent unit tests pass
- [ ] All department workflow tests pass
- [ ] All integration tests pass
- [ ] All security tests pass
- [ ] All failure-path tests pass
- [ ] All evaluation/benchmark tests pass
- [ ] All agent audit reports exist
- [ ] All critical fail conditions are checked
- [ ] No agent has unrestricted tool access
- [ ] No high-impact action can bypass approval
- [ ] No production action can run in non-production mode
- [ ] No agent can silently promote lifecycle state
- [ ] Every agent logs trace, evidence, decision path, permissions, and environment
- [ ] Every side-effecting action has idempotency and compensation rules
- [ ] Every production-capable workflow has runbook and incident path

---

# 6. Suggested Status Legend

Use this legend in notes or issue trackers:

| Status | Meaning |
|---|---|
| `Not Started` | No implementation yet. |
| `Scaffolded` | Folder/files created, but logic incomplete. |
| `Implemented` | Logic implemented, not fully tested. |
| `Tested` | Unit/user tests pass. |
| `Integrated` | Works in department workflow. |
| `Audited` | Audit checklist passed. |
| `Approved` | Ready for intended lifecycle/environment. |

---

# 7. Recommended Tracking Columns

For a spreadsheet or project board, use:

- Phase
- Department
- Agent
- Owner
- Lifecycle Stage
- Implementation Status
- Manifest
- Schemas
- Prompt
- Permissions
- Audit
- Unit Tests
- User Workflow Tests
- Department Integration
- Audit Score
- Critical Fails
- Exit Gate
- Notes

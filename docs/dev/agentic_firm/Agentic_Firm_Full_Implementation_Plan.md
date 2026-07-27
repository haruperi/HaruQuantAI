# Agentic Firm Implementation Plan

> **Purpose:** Implement the full agentic firm architecture shown in the provided diagram using the aligned standards from:
>
> - `docs/Agentic_AI_Playbook.md`
> - `docs/Agent_Auditing_Checklist.md`
> - `docs/Agent_Template.md`
>
> **Implementation principle:** Build every department and every agent as an independently testable unit first, then integrate through workflows, registry entries, control gates, audit logs, and quality gates.

---

# 1. Implementation Strategy

The system should be implemented as an **agent-first, governance-aware, incremental architecture**.

Each agent must be built as a self-contained module under:

```text
agentic/agents/<department>/<agent_name>/
```

Each agent should have:

```text
agent.py
prompt.md
manifest.yaml
schemas.py
README.md
```

Its tests should live under:

```text
tests/agents/<department>/<agent_name>/
```

System-level tests should live under:

```text
tests/integration/
tests/contracts/
tests/security/
tests/failure/
tests/evaluation/
```

Every agent must follow the standard execution loop:

```text
Validate Input
→ Gather Evidence / Context
→ Optional LLM Reasoning
→ Deterministic Policy / Control Decision
→ Structured Output
→ Audit Log
→ Evaluation
```

The broader workflow follows:

```text
Reason → Plan → Policy Check → Act → Observe → Evaluate → Approve / Refine / Compensate / Finish
```

---

# 2. Canonical Repository Placement

```text
project-root/
├── docs/
│   ├── Agentic_AI_Playbook.md
│   ├── Agent_Auditing_Checklist.md
│   ├── Agent_Template.md
│   ├── architecture/
│   ├── adr/
│   ├── runbooks/
│   ├── agents/
│   ├── workflows/
│   ├── capabilities/
│   ├── governance/
│   ├── operations/
│   └── security/
│
├── agentic/
│   ├── host/
│   ├── agents/
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
│
├── registry/
│   ├── agents/
│   ├── workflows/
│   └── capabilities/
│
├── audit/
│   ├── reports/
│   └── evidence/
│
├── tests/
├── scripts/
└── .github/
```

---

# 3. Development Order Overview

The implementation should proceed from lowest-dependency infrastructure to highest-dependency production execution.

| Phase | Department / Layer | Dependency Level | Main Goal |
|---:|---|---|---|
| 0 | Shared Contracts | None | Define schemas, permissions, deterministic policy contracts, evaluation, tracing, persistence, and base contracts. |
| 1 | Runtime Layer | Shared Contracts | Provide model runtime, tool execution, execution context, and runtime abstraction. |
| 2 | Control Plane and Executive Orchestration | Shared Contracts + Runtime | Build control plane, planner, AI CEO/CIO gateway, and human approval boundary. |
| 3 | Research Department | Control Plane | Generate evidence, ideas, intelligence, context, and hypotheses. |
| 4 | Strategy Development Department | Research Evidence | Convert research into validated strategy specifications, code, tests, and handoff packages. |
| 5 | Validation & Backtesting Package | Strategy Specs | Provide reusable backtest, optimization, Monte Carlo, and statistical validation services. |
| 6 | Simulation Department | Strategy Specs + Validation Package | Orchestrate full simulation, robustness, optimization, and evidence curation. |
| 7 | Risk Department | Simulation Evidence | Review risk, enforce limits, monitor portfolio risk, and produce risk decisions. |
| 8 | Portfolio & Execution Department | Risk Decision | Manage lifecycle, allocation, paper execution, readiness, live bridge, and kill switch. |
| 9 | Operations & Audit Department | All Departments | Monitor cost, performance, compliance, and operational health. |
| 10 | Dedicated Audit Department | All Departments | Provide independent audit review and approval evidence. |
| 11 | End-to-End Firm Integration | All Departments | Connect lifecycle workflow from research evidence to live bridge and broker/exchange. |

---

# 4. Phase 0 — Shared Contracts

## 4.1 Purpose

The Shared Contracts layer is the foundation of the system. Nothing else should be built until these contracts exist because every agent, workflow, registry, evaluator, and audit report depends on them.

## 4.2 Components

| Component | Purpose | Example Real-World Usage |
|---|---|---|
| Schemas | Define request, response, decision, evidence, approval, and error models. | A Research Agent returns evidence in the same envelope that a Risk Agent can consume without guessing fields. |
| Permissions | Define what each agent can read, write, execute, approve, or escalate. | A Strategy Creator can generate strategy specs but cannot approve production deployment. |
| Deterministic Policy | Defines policy-as-code patterns for final decisions and guardrails. | A Risk Governor blocks a strategy promotion if drawdown exceeds a configured limit. |
| Evaluation | Defines common scoring, validation, and quality-gate interfaces. | Every agent response is evaluated for schema validity, evidence quality, and policy compliance. |
| Tracing | Defines trace IDs, step IDs, tool-call IDs, and workflow spans. | A failed live execution request can be traced back to the exact research evidence and approval packet. |
| Persistence | Defines storage contracts for runs, evidence, audit logs, approvals, and artifacts. | A board reviewer opens the evidence bundle for a strategy approved three months earlier. |
| Base Contracts | Defines base agent, workflow, result, artifact, and error contracts. | A new specialist agent can be created using the same interface as every existing agent. |

## 4.3 Implementation Deliverables

```text
agentic/agents/_shared/
  base_agent.py
  agent_result.py
  manifest_schema.py
  permissions.py
  guardrails.py
  lifecycle.py
  registry_loader.py

agentic/workflows/_shared/
  base_workflow.py
  workflow_result.py
  workflow_state.py
  handoff.py

agentic/observability/
  tracing.py
  audit_log.py
  logger.py
  metrics.py
  redaction.py

agentic/evaluation/
  evaluator.py
  rubrics.py
  quality_gate.py

agentic/state/
  state_schema.py
  state_manager.py

agentic/policy/
  policy_schema.py
  policy_engine.py
```

## 4.4 Independent Tests

```text
tests/contracts/test_base_agent_contracts.py
tests/contracts/test_agent_response_schema.py
tests/contracts/test_evidence_schema.py
tests/contracts/test_permission_schema.py
tests/contracts/test_manifest_schema.py
tests/contracts/test_workflow_handoff_schema.py
```

## 4.5 Exit Gate

Shared Contracts are complete when:

- all base schemas validate
- every required envelope serializes to JSON
- permission models support read/write/execute/approve/escalate separation
- audit metadata is standardized
- lifecycle states are standardized
- contract tests pass

---

# 5. Phase 1 — Runtime Layer

## 5.1 Purpose

The Runtime Layer provides model access, tool execution, and execution context. It allows agents to be framework-neutral by hiding provider-specific details behind common runtime interfaces.

## 5.2 Agents / Components

| Component | Purpose | Independent Usage Example |
|---|---|---|
| LLM Registry | Maintains available models, provider metadata, routing rules, and fallback policies. | A workflow asks for a low-cost classification model and the registry returns the configured provider. |
| Google ADK Runtime | Optional adapter for projects that use Google ADK. | An existing ADK agent is wrapped behind the standard runtime interface. |
| LiteLLM Runtime | Optional adapter for multi-provider routing. | A request can fail over from one provider to another without changing agent code. |
| OpenAI Runtime | Optional adapter for OpenAI model calls. | A Reviewer Agent uses an OpenAI model for summarization through the common runtime boundary. |
| Tool Executor | Validates tool requests, checks permissions, executes tools, and normalizes results. | A Research Agent requests `search_docs`; the Tool Executor validates permission and returns structured evidence. |
| Execution Context | Holds trace ID, session ID, environment, user, policy context, and runtime metadata. | A production action is blocked because the execution context says the run is in development mode. |

## 5.3 Implementation Deliverables

```text
agentic/runtime/
  llm_registry.py
  model_router.py
  runtime_protocol.py
  google_adk_runtime.py
  litellm_runtime.py
  openai_runtime.py
  tool_executor.py
  execution_context.py
  runtime_errors.py
```

If you prefer to keep runtime under the approved `agentic/` structure without introducing a new top-level folder, place these in:

```text
agentic/host/
agentic/capabilities/adapters/
agentic/config/
```

However, a dedicated `agentic/runtime/` folder is justified because the diagram explicitly has a Runtime Layer.

## 5.4 Independent Tests

```text
tests/unit/runtime/test_llm_registry.py
tests/unit/runtime/test_model_router.py
tests/unit/runtime/test_tool_executor_permissions.py
tests/unit/runtime/test_execution_context.py
tests/failure/test_runtime_fallback.py
```

## 5.5 Exit Gate

Runtime Layer is complete when:

- agents can call models without knowing provider details
- tools are executed only through permission-checked boundaries
- every runtime call records trace and cost metadata
- fallback behavior is tested
- runtime failures return structured errors

---

# 6. Phase 2 — Control Plane and Executive Orchestration

## 6.1 Purpose

The Control Plane connects the human authority layer, AI CEO/CIO gateway, Planner Agent, registries, workflows, tools, evidence, and audit controls. This is the routing and governance spine of the system.

## 6.2 Components

| Agent / Component | Purpose | Independent Usage Example |
|---|---|---|
| Human Board / Human Approver | Final authority for high-impact actions, approvals, overrides, and live decisions. | A strategy passes validation and risk review, but live activation waits for board approval. |
| AI CEO / CIO Agent | User-facing executive gateway that synthesizes final memos and routes through the Planner. | User asks, “Should we move Strategy X to paper execution?” The CEO returns a board-ready recommendation package. |
| Planner Agent | Classifies intent, selects departments, identifies evidence needs, and builds workflow plans. | User asks for a new strategy; Planner routes to Research, Strategy Development, Simulation, and Risk. |
| Control Plane | Registry, orchestrator, task manager, operating cycle, and tool policy hub. | A workflow request is accepted, assigned a trace ID, routed to agents, audited, and stored. |

## 6.3 Build Order

1. Control Plane registry loader
2. Workflow registry
3. Agent registry integration
4. Capability registry integration
5. Planner Agent
6. AI CEO/CIO Agent
7. Human approval packet support
8. Board approval workflow
9. Control Plane integration tests

## 6.4 Implementation Deliverables

```text
agentic/host/
  app.py
  router.py
  orchestrator.py
  session_manager.py

agentic/agents/executive/planner_agent/
  agent.py
  prompt.md
  manifest.yaml
  schemas.py
  README.md

agentic/agents/executive/ai_ceo_cio_agent/
  agent.py
  prompt.md
  manifest.yaml
  schemas.py
  README.md

agentic/approvals/
  approval_service.py
  approval_packet.py
  approval_schema.py
  approval_store.py

agentic/workflows/board_approval_workflow/
  workflow.py
  workflow.yaml
  schemas.py
  README.md
```

## 6.5 Independent Tests

```text
tests/agents/executive/planner_agent/
tests/agents/executive/ai_ceo_cio_agent/
tests/workflows/board_approval_workflow/
tests/integration/test_control_plane_routing.py
tests/security/test_planner_cannot_bypass_policy.py
```

## 6.6 Department-Level Real-World Usage Example

**Scenario:** User asks, “Find our best strategy candidate and tell me whether it is ready for live deployment.”

1. AI CEO/CIO receives request.
2. Planner classifies it as a strategy lifecycle decision.
3. Control Plane identifies required departments:
   - Research
   - Strategy Development
   - Simulation
   - Risk
   - Portfolio & Execution
   - Audit
4. Planner creates a workflow plan.
5. CEO returns only a synthesized final memo after evidence is collected.

## 6.7 Exit Gate

This phase is complete when:

- Planner can classify at least 20 representative requests
- CEO can synthesize structured memos from mock department outputs
- Control Plane can create traceable workflows
- approval packets can be created and stored
- high-impact actions are blocked without approval

---

# 7. Phase 3 — Research Department

## 7.1 Purpose

The Research Department produces evidence, market/context intelligence, hypotheses, and opportunity discovery. It should be read-only and advisory. It should not approve strategies, approve risk, allocate resources, or execute actions.

## 7.2 Department Agents

| Agent | Purpose | Independent Usage Example |
|---|---|---|
| Research Orchestrator | Coordinates research tasks and merges outputs from research specialists. | User asks, “Build a research brief for GBPJPY”; orchestrator calls news, technical, macro, seasonality, and intermarket agents. |
| Technical Analyst | Reviews technical structure, trends, volatility, patterns, indicators, and price behavior. | “Analyze EURUSD H1 for trend, mean reversion, volatility, and support/resistance context.” |
| Strategy Hypothesis | Converts research observations into testable strategy hypotheses. | “Based on volatility expansion after London open, propose a testable intraday breakout hypothesis.” |
| Evidence Curator | Collects, deduplicates, ranks, and references research evidence. | “Create an evidence bundle for why this idea should proceed to strategy specification.” |
| Macro / Fundamental Context | Summarizes macro, fundamental, economic, or contextual drivers. | “Summarize the macro context affecting JPY pairs this week.” |
| Seasonality Calendar | Identifies seasonal, calendar, session, weekday, or event timing patterns. | “Check whether gold behaves differently around month-end or New York session.” |
| Market Intelligence | Produces high-level environment summaries. | “Summarize current market regime and key risks for the selected instruments.” |
| Strategy Scout | Searches for promising strategy ideas, patterns, or opportunity classes. | “Find strategy concepts suitable for low-volatility Asian session conditions.” |
| Research Validation | Checks research quality, evidence sufficiency, and unsupported claims. | “Review this research brief and flag unsupported conclusions.” |
| News Sentiment | Summarizes news, sentiment, event risk, and narrative shifts. | “Summarize sentiment and news risk for GBPJPY before London open.” |
| Cross Asset Intermarket | Reviews relationships across related assets, sectors, rates, currencies, or instruments. | “Check whether bond yields, equities, and USD strength support or contradict this FX idea.” |

## 7.3 Implementation Order

1. Evidence Curator
2. Research Validation
3. Market Intelligence
4. Technical Analyst
5. Macro / Fundamental Context
6. News Sentiment
7. Seasonality Calendar
8. Cross Asset Intermarket
9. Strategy Scout
10. Strategy Hypothesis
11. Research Orchestrator

The first two should be built early because all other research agents produce evidence that must be curated and validated.

## 7.4 Implementation Deliverables

```text
agentic/agents/research/evidence_curator/
agentic/agents/research/research_validation/
agentic/agents/research/market_intelligence/
agentic/agents/research/technical_analyst/
agentic/agents/research/macro_fundamental_context/
agentic/agents/research/news_sentiment/
agentic/agents/research/seasonality_calendar/
agentic/agents/research/cross_asset_intermarket/
agentic/agents/research/strategy_scout/
agentic/agents/research/strategy_hypothesis/
agentic/agents/research/research_orchestrator/
```

Each folder contains:

```text
agent.py
prompt.md
manifest.yaml
schemas.py
README.md
```

Tests:

```text
tests/agents/research/<agent_name>/
```

## 7.5 Department Workflow

```text
Research Request
→ Research Orchestrator
→ Specialist Research Agents
→ Evidence Curator
→ Research Validation
→ Research Evidence Package
```

## 7.6 Output Artifacts

```text
research_brief.json
evidence_bundle.json
research_validation_report.json
strategy_hypothesis_candidates.json
```

## 7.7 Independent Tests

- agent schema tests
- prompt safety tests
- evidence sufficiency tests
- stale data tests
- contradiction detection tests
- unsupported claim tests
- workflow handoff tests

## 7.8 Department Exit Gate

Research Department is complete when:

- each research agent runs independently
- every research output has evidence references
- unsupported claims are flagged
- stale evidence is marked
- Research Orchestrator can produce a complete research evidence package
- output can be consumed by Strategy Development

---

# 8. Phase 4 — Strategy Development Department

## 8.1 Purpose

The Strategy Development Department converts research evidence into formal strategy specifications, normalized rules, assumptions, code, tests, review packages, and handoff artifacts.

## 8.2 Department Agents

| Agent | Purpose | Independent Usage Example |
|---|---|---|
| Strategy Creation Orchestrator | Coordinates the strategy creation workflow. | “Turn the approved research hypothesis into a complete strategy specification package.” |
| Strategy Spec Validator | Validates strategy specs for completeness, contradictions, and missing assumptions. | “Check whether this strategy spec has entry, exit, sizing, timeframe, data, and risk assumptions.” |
| Strategy Template Selector | Chooses the most appropriate template or design pattern. | “Select whether this should be event-driven, vectorized, signal-based, or state-machine strategy design.” |
| Strategy Cost Execution | Estimates implementation, compute, operational, execution, or maintenance cost. | “Estimate whether this strategy requires tick data, expensive optimization, or low-latency execution.” |
| Strategy Codegen | Generates strategy code from an approved specification. | “Generate the strategy module and tests from this validated spec.” |
| Strategy Spec Storage | Stores approved specs with version, owner, trace ID, and lifecycle state. | “Save Strategy Spec v1.0 as ready for simulation.” |
| Strategy Handoff | Packages the strategy for simulation, validation, risk, or review. | “Create a handoff bundle for Simulation Department.” |
| Strategy Creator | Drafts the initial strategy concept and formal rules. | “Create a mean-reversion strategy concept from this research evidence.” |
| Strategy Rule Normalizer | Converts natural language rules into structured machine-readable rules. | “Normalize ‘enter after breakout confirmation’ into explicit trigger logic.” |
| Strategy Risk Assumption | Documents strategy-level risk assumptions and expected failure modes. | “List assumptions about drawdown, volatility, liquidity, and regime sensitivity.” |
| Strategy Test Plan | Creates the validation and simulation test plan. | “Define the required backtests, robustness tests, and rejection criteria.” |
| Strategy Reviewer | Reviews the strategy for quality, risk, clarity, and testability. | “Review the strategy spec and decide whether it is ready for simulation.” |
| Strategy Code Storage | Stores generated code, versions, and artifacts. | “Register generated strategy code v0.1 with traceability to its spec.” |

## 8.3 Implementation Order

1. Strategy Spec Validator
2. Strategy Rule Normalizer
3. Strategy Template Selector
4. Strategy Risk Assumption
5. Strategy Test Plan
6. Strategy Creator
7. Strategy Reviewer
8. Strategy Spec Storage
9. Strategy Codegen
10. Strategy Code Storage
11. Strategy Cost Execution
12. Strategy Handoff
13. Strategy Creation Orchestrator

## 8.4 Department Workflow

```text
Research Evidence Package
→ Strategy Creator
→ Strategy Rule Normalizer
→ Strategy Risk Assumption
→ Strategy Template Selector
→ Strategy Test Plan
→ Strategy Spec Validator
→ Strategy Reviewer
→ Strategy Spec Storage
→ Optional Strategy Codegen
→ Strategy Code Storage
→ Strategy Handoff
```

## 8.5 Output Artifacts

```text
strategy_spec.json
strategy_rules.json
strategy_risk_assumptions.json
strategy_test_plan.json
strategy_review_report.json
strategy_code_artifact.json
strategy_handoff_package.json
```

## 8.6 Independent Tests

- valid strategy spec accepted
- incomplete spec rejected
- contradictory rules detected
- unsupported assumptions flagged
- code generation cannot bypass templates or safety constraints
- strategy reviewer rejects untestable specs
- storage includes version and traceability

## 8.7 Department-Level Real-World Usage Example

**Scenario:** Research identifies that a symbol tends to mean-revert after large session-opening spikes.

1. Strategy Creator drafts rules.
2. Rule Normalizer converts them into structured triggers.
3. Risk Assumption Agent records failure modes.
4. Test Plan Agent defines backtest and robustness requirements.
5. Spec Validator checks completeness.
6. Reviewer approves or rejects for simulation.
7. Handoff Agent packages the strategy for Simulation.

## 8.8 Department Exit Gate

Strategy Development is complete when:

- strategy specs are machine-readable
- every spec links to research evidence
- all assumptions are explicit
- every strategy has a test plan
- code generation is optional and controlled
- strategy handoff can be consumed by Simulation Department

---

# 9. Phase 5 — Validation & Backtesting Package

## 9.1 Purpose

This package provides reusable validation services that can be called by the Simulation Department or other workflows. It is a package because these functions are reusable capabilities, not necessarily standalone decision-making agents.

## 9.2 Package Components

| Component | Purpose | Independent Usage Example |
|---|---|---|
| Backtest | Runs historical or simulated tests for a strategy. | “Run Strategy X on EURUSD H1 from 2020 to 2024.” |
| Robustness Monte Carlo | Tests sensitivity to randomness, order, parameters, costs, or perturbations. | “Run Monte Carlo resampling to check if results depend on lucky trade order.” |
| Optimization Comparator | Compares parameter sets, optimization windows, and performance stability. | “Compare top 20 parameter sets and identify overfit candidates.” |
| Statistical Validation | Tests whether results are statistically meaningful and not random noise. | “Check whether the edge survives significance and distribution tests.” |

## 9.3 Implementation Order

1. Backtest
2. Statistical Validation
3. Robustness Monte Carlo
4. Optimization Comparator

## 9.4 Implementation Deliverables

```text
agentic/capabilities/tools/backtest.py
agentic/capabilities/tools/robustness_monte_carlo.py
agentic/capabilities/tools/optimization_comparator.py
agentic/capabilities/tools/statistical_validation.py

registry/capabilities/tools.yaml
tests/capabilities/test_backtest.py
tests/capabilities/test_robustness_monte_carlo.py
tests/capabilities/test_optimization_comparator.py
tests/capabilities/test_statistical_validation.py
```

## 9.5 Package Exit Gate

The package is complete when:

- tools are deterministic and reproducible
- all results include data version, config, seed, and trace ID
- tools reject invalid inputs
- results are machine-readable
- Simulation Department can call them through the Tool Executor

---

# 10. Phase 6 — Simulation Department

## 10.1 Purpose

The Simulation Department orchestrates backtesting, optimization, robustness testing, statistical validation, and simulation evidence curation. It turns strategy handoff packages into simulation validation reports.

## 10.2 Department Agents

| Agent | Purpose | Independent Usage Example |
|---|---|---|
| Simulation Orchestrator | Coordinates simulation workflows and evidence packages. | “Run the full validation workflow for Strategy X.” |
| Backtest Analyst | Interprets backtest results and highlights strengths, weaknesses, and anomalies. | “Explain why this strategy performed well in 2021 but failed in 2022.” |
| Optimization Comparator | Agent-level reviewer of optimization outputs and overfit risk. | “Compare optimization results and identify robust parameter regions.” |
| Statistical Validation | Agent-level reviewer of statistical validity and reliability. | “Determine whether results are statistically significant enough to proceed.” |
| Backtest | Agent wrapper or service interface around backtest capability. | “Run baseline and segmented backtests for this strategy.” |
| Optimization | Runs or manages optimization experiments. | “Optimize parameters across rolling windows and return stability summary.” |
| Robustness | Runs robustness and stress tests. | “Stress test the strategy with cost, slippage, missing data, and parameter noise.” |
| Simulation Evidence Curator | Packages and validates all simulation evidence. | “Create a simulation evidence bundle for Risk Department.” |

## 10.3 Implementation Order

1. Backtest
2. Backtest Analyst
3. Statistical Validation
4. Robustness
5. Optimization
6. Optimization Comparator
7. Simulation Evidence Curator
8. Simulation Orchestrator

## 10.4 Department Workflow

```text
Strategy Handoff Package
→ Backtest
→ Backtest Analyst
→ Statistical Validation
→ Robustness
→ Optimization
→ Optimization Comparator
→ Simulation Evidence Curator
→ Simulation Validation Package
```

## 10.5 Output Artifacts

```text
backtest_result.json
backtest_analysis_report.json
statistical_validation_report.json
robustness_report.json
optimization_report.json
simulation_evidence_bundle.json
simulation_validation_package.json
```

## 10.6 Independent Tests

- backtest rejects invalid strategy specs
- backtest result includes reproducibility metadata
- analyst flags suspicious metrics
- statistical validation rejects insufficient samples
- robustness detects fragile performance
- optimization comparator flags overfitting
- simulation evidence bundle includes all required artifacts

## 10.7 Department-Level Real-World Usage Example

**Scenario:** A strategy spec is ready for validation.

1. Simulation Orchestrator receives the strategy handoff package.
2. Backtest runs baseline historical test.
3. Backtest Analyst summarizes result quality.
4. Statistical Validation checks significance.
5. Robustness tests stress the strategy.
6. Optimization Comparator checks parameter stability.
7. Evidence Curator packages results for Risk Department.

## 10.8 Department Exit Gate

Simulation Department is complete when:

- every simulation result is reproducible
- weak or incomplete results are rejected
- simulation evidence is packaged with traceability
- Risk Department can consume the simulation validation package

---

# 11. Phase 7 — Risk Department

## 11.1 Purpose

The Risk Department reviews strategy, simulation, portfolio, policy, and governance risk. It produces risk decisions and approval/rejection evidence. It must be fail-closed: missing evidence, stale data, or policy conflicts should block promotion.

## 11.2 Department Agents / Services

| Agent / Service | Purpose | Independent Usage Example |
|---|---|---|
| Risk Orchestrator | Coordinates risk review workflow. | “Run full risk review for Strategy X using simulation evidence and portfolio context.” |
| Risk Reviewer | Reviews risk qualitatively and quantitatively. | “Summarize key risk concerns in this strategy validation package.” |
| Risk Limit Auditor | Checks proposed actions against configured risk, policy, or resource limits. | “Verify this strategy does not exceed drawdown, exposure, leverage, or capital limits.” |
| Hard-Coded Risk Governor | Deterministic control service that approves, rejects, or escalates based on policy-as-code. | “Reject live promotion because required robustness threshold failed.” |
| Portfolio Risk Monitor | Monitors portfolio-level concentration, correlation, drawdown, exposure, or resource risk. | “Check if adding this strategy increases portfolio concentration beyond limits.” |
| Risk Approval Auditor | Audits risk decisions, overrides, approvals, and rejection evidence. | “Verify that a manual override included approver, timestamp, scope, and reason.” |

## 11.3 Implementation Order

1. Risk Limit Auditor
2. Hard-Coded Risk Governor
3. Risk Approval Auditor
4. Portfolio Risk Monitor
5. Risk Reviewer
6. Risk Orchestrator

The Hard-Coded Risk Governor should be implemented before higher-level risk agents because it is the deterministic authority boundary.

## 11.4 Department Workflow

```text
Simulation Validation Package
→ Risk Limit Auditor
→ Portfolio Risk Monitor
→ Risk Reviewer
→ Hard-Coded Risk Governor
→ Risk Approval Auditor
→ Risk Decision Package
```

## 11.5 Output Artifacts

```text
risk_limit_audit.json
portfolio_risk_report.json
risk_review_report.json
risk_governor_decision.json
risk_approval_audit.json
risk_decision_package.json
```

## 11.6 Independent Tests

- missing simulation evidence fails closed
- failed threshold blocks approval
- LLM cannot override deterministic governor
- manual override requires approval record
- stale risk policy is rejected
- portfolio risk monitor flags concentration
- rejection reasons are recorded

## 11.7 Department-Level Real-World Usage Example

**Scenario:** A strategy passes simulation but has large drawdown during stressed periods.

1. Risk Limit Auditor checks thresholds.
2. Portfolio Risk Monitor checks combined portfolio impact.
3. Risk Reviewer summarizes concerns.
4. Hard-Coded Risk Governor rejects or escalates.
5. Risk Approval Auditor verifies decision traceability.

## 11.8 Department Exit Gate

Risk Department is complete when:

- all risk decisions are deterministic or deterministically verified
- every rejection includes reasons
- overrides require authorized approval
- risk decisions are audit-ready
- Portfolio & Execution Department can consume the risk decision package

---

# 12. Phase 8 — Portfolio & Execution Department

## 12.1 Purpose

The Portfolio & Execution Department manages approved strategy lifecycle, allocation, readiness, paper execution, live execution preparation, execution bridge, performance reporting, cost optimization, and kill switch control.

This department must not bypass Risk Department or Board approval.

## 12.2 Department Agents / Services

| Agent / Service | Purpose | Independent Usage Example |
|---|---|---|
| Portfolio Orchestrator | Coordinates lifecycle, allocation, execution readiness, and monitoring workflows. | “Move approved Strategy X from risk-approved to paper execution workflow.” |
| Allocation Optimizer | Suggests allocation based on constraints, portfolio state, and policy. | “Allocate capital among five approved strategies without exceeding concentration limits.” |
| Execution Planner | Converts approved lifecycle decisions into execution plans. | “Prepare paper execution instructions for Strategy X.” |
| Paper Execution | Runs strategy in simulated or paper environment. | “Start Strategy X in paper mode for 30 days.” |
| MT5 / cTrader Execution Bridge | Broker/platform execution adapter for approved orders. | “Send approved live order to execution platform after all gates pass.” |
| Performance Reporter | Reports live/paper performance, drift, drawdown, and operational health. | “Generate weekly paper performance report for Strategy X.” |
| Portfolio Manager | Manages approved portfolio state and strategy assignments. | “Add Strategy X to paper portfolio after approval.” |
| Strategy Lifecycle | Tracks lifecycle stages and promotion status. | “Move Strategy X from simulation_validated to risk_reviewed.” |
| Execution Readiness | Checks whether all prerequisites for paper/live execution are satisfied. | “Verify data feed, account, permissions, risk approval, and board approval exist.” |
| Live Execution | Manages live execution workflow after approval. | “Activate live execution for Strategy X after board approval.” |
| Kill Switch Service | Stops or blocks execution when safety conditions are triggered. | “Disable all live execution if risk breach or system anomaly occurs.” |
| Cost Optimizer | Monitors and optimizes operational, model, infrastructure, and execution costs. | “Reduce expensive model calls in monitoring workflows without reducing safety.” |

## 12.3 Implementation Order

1. Strategy Lifecycle
2. Execution Readiness
3. Portfolio Manager
4. Allocation Optimizer
5. Paper Execution
6. Performance Reporter
7. Cost Optimizer
8. Kill Switch Service
9. Execution Planner
10. MT5 / cTrader Execution Bridge
11. Live Execution
12. Portfolio Orchestrator

Execution Bridge and Live Execution should be implemented late because they are highest risk.

## 12.4 Department Workflow

```text
Risk Decision Package
→ Strategy Lifecycle
→ Portfolio Manager
→ Allocation Optimizer
→ Execution Readiness
→ Paper Execution
→ Performance Reporter
→ Board Approval
→ Live Execution
→ Execution Bridge
→ Broker / Exchange
```

## 12.5 Output Artifacts

```text
strategy_lifecycle_record.json
allocation_recommendation.json
execution_readiness_report.json
paper_execution_report.json
performance_report.json
live_execution_approval_packet.json
execution_bridge_audit.json
kill_switch_event.json
```

## 12.6 Independent Tests

- strategy cannot skip lifecycle stages
- allocation requires risk-approved strategies
- execution readiness fails if approvals are missing
- paper execution cannot call live bridge
- live execution requires board approval
- kill switch blocks execution
- bridge rejects unapproved orders
- performance reporting includes traceability

## 12.7 Department-Level Real-World Usage Example

**Scenario:** A risk-approved strategy is ready for paper trading.

1. Strategy Lifecycle updates state to `risk_approved`.
2. Portfolio Manager assigns it to the paper portfolio.
3. Allocation Optimizer proposes allocation.
4. Execution Readiness checks prerequisites.
5. Paper Execution starts the strategy.
6. Performance Reporter tracks results.
7. If paper results pass, Board Approval can consider live activation.

## 12.8 Department Exit Gate

Portfolio & Execution Department is complete when:

- lifecycle transitions are controlled
- execution readiness blocks missing approvals
- paper execution is isolated from live execution
- live bridge cannot execute without approved packet
- kill switch works and is tested
- performance and cost reporting are operational

---

# 13. Phase 9 — Operations & Audit Department

## 13.1 Purpose

The Operations & Audit Department monitors operational health, performance, cost, compliance, and quality across the system. It should provide observability, reporting, and continuous improvement signals.

## 13.2 Department Agents

| Agent | Purpose | Independent Usage Example |
|---|---|---|
| Audit Compliance | Checks whether workflows, agents, approvals, and outputs comply with standards. | “Audit whether Strategy X promotion followed required evidence and approval gates.” |
| Performance Reporter | Reports system, agent, workflow, strategy, or operational performance. | “Generate a weekly report of workflow completion rates and failed quality gates.” |
| Cost Optimizer | Reviews model, tool, infrastructure, and workflow costs. | “Find workflows where expensive model calls can be replaced by deterministic checks.” |

## 13.3 Implementation Order

1. Performance Reporter
2. Cost Optimizer
3. Audit Compliance

## 13.4 Department Workflow

```text
System Logs + Audit Records + Metrics
→ Performance Reporter
→ Cost Optimizer
→ Audit Compliance
→ Operations Report
```

## 13.5 Output Artifacts

```text
performance_report.json
cost_report.json
compliance_report.json
operations_dashboard_payload.json
```

## 13.6 Independent Tests

- reporter handles missing metrics
- cost optimizer does not remove safety checks
- compliance agent flags missing audit logs
- compliance agent detects missing approvals
- reports include trace IDs and evidence references

## 13.7 Department-Level Real-World Usage Example

**Scenario:** Weekly operating review.

1. Performance Reporter summarizes workflow success/failure rates.
2. Cost Optimizer identifies high-cost workflows.
3. Audit Compliance flags agents with missing audit metadata or failed quality gates.
4. Output becomes an operations review package.

## 13.8 Department Exit Gate

Operations & Audit Department is complete when:

- it can monitor all registered agents
- it can detect audit gaps
- it can summarize costs and performance
- it cannot override policy or approval decisions
- it produces evidence for governance review

---

# 14. Phase 10 — Dedicated Audit Department

## 14.1 Purpose

The Dedicated Audit Department provides independent audit review. It should not own daily operations, strategy creation, risk approval, or execution. Its job is to inspect evidence, detect control gaps, and produce audit decisions.

## 14.2 Department Agent

| Agent | Purpose | Independent Usage Example |
|---|---|---|
| Audit | Independently reviews complete workflow evidence, approvals, logs, and control decisions. | “Audit the full lifecycle of Strategy X from research evidence through paper execution approval.” |

## 14.3 Implementation Order

1. Audit Agent
2. Audit evidence reader
3. Audit report generator
4. Audit decision workflow

## 14.4 Output Artifacts

```text
audit_review_report.json
audit_findings.json
audit_decision.json
audit_remediation_tasks.json
```

## 14.5 Independent Tests

- detects missing evidence
- detects missing approval
- detects lifecycle skip
- detects stale policy
- detects unauthorized override
- produces machine-readable findings
- produces human-readable audit report

## 14.6 Department-Level Real-World Usage Example

**Scenario:** Post-promotion audit.

The Audit Agent reviews whether a strategy moved from research to paper execution according to policy. It checks:

- research evidence exists
- strategy spec was validated
- simulation package exists
- risk decision exists
- approval packet exists
- lifecycle state was updated correctly
- audit logs are complete

## 14.7 Department Exit Gate

Dedicated Audit Department is complete when:

- it can audit any lifecycle stage
- it can produce actionable findings
- it is independent from the agents it audits
- it cannot mutate production state except by creating audit findings or remediation tasks

---

# 15. Phase 11 — End-to-End Lifecycle Integration

## 15.1 Purpose

After every department works independently, integrate the full lifecycle shown in the architecture diagram.

```text
Research Evidence
→ Strategy Spec
→ Simulation Validation
→ Risk Decision
→ Portfolio Lifecycle
→ Paper Execution
→ Board Approval
→ Live Bridge
→ Broker / Exchange
```

## 15.2 End-to-End Workflow

```text
1. User request enters AI CEO/CIO Agent.
2. Planner Agent classifies request and creates workflow plan.
3. Research Department produces research evidence.
4. Strategy Development creates strategy spec and handoff package.
5. Validation & Backtesting Package runs reusable validation tools.
6. Simulation Department produces simulation validation package.
7. Risk Department produces risk decision package.
8. Portfolio & Execution Department manages lifecycle and paper execution.
9. Operations & Audit monitors performance, cost, and compliance.
10. Dedicated Audit reviews evidence and control compliance.
11. Human Board approves live activation if required.
12. Live Execution passes through Execution Bridge only after all gates pass.
```

## 15.3 End-to-End Integration Tests

```text
tests/integration/test_research_to_strategy_spec.py
tests/integration/test_strategy_spec_to_simulation.py
tests/integration/test_simulation_to_risk_decision.py
tests/integration/test_risk_decision_to_portfolio_lifecycle.py
tests/integration/test_paper_execution_to_board_approval.py
tests/integration/test_board_approval_to_live_bridge.py
tests/integration/test_full_lifecycle_happy_path.py
tests/integration/test_full_lifecycle_rejection_path.py
tests/security/test_no_agent_bypasses_risk_or_approval.py
tests/failure/test_kill_switch_blocks_live_bridge.py
tests/evaluation/test_full_workflow_quality_gate.py
```

## 15.4 End-to-End Real-World Usage Example

**Scenario:** “Create a new strategy idea, validate it, and tell me if it should go to paper execution.”

1. CEO receives the request.
2. Planner selects Research → Strategy Development → Simulation → Risk → Portfolio Lifecycle.
3. Research produces evidence and hypotheses.
4. Strategy Development creates a strategy spec.
5. Simulation validates the spec.
6. Risk Department approves, rejects, or escalates.
7. Portfolio Department determines if paper execution is ready.
8. CEO returns final memo:
   - decision
   - reasons
   - evidence
   - risk flags
   - next step
   - required approvals

---

# 16. Cross-Department Integration Contracts

Every department handoff must be schema-validated.

| Handoff | Producer | Consumer | Artifact |
|---|---|---|---|
| Research Evidence | Research Department | Strategy Development | `research_evidence_package.json` |
| Strategy Spec | Strategy Development | Simulation Department | `strategy_handoff_package.json` |
| Simulation Validation | Simulation Department | Risk Department | `simulation_validation_package.json` |
| Risk Decision | Risk Department | Portfolio & Execution | `risk_decision_package.json` |
| Portfolio Lifecycle | Portfolio & Execution | Operations / Audit | `strategy_lifecycle_record.json` |
| Paper Execution | Portfolio & Execution | Board / Audit | `paper_execution_report.json` |
| Board Approval | Human Board | Portfolio & Execution | `board_approval_packet.json` |
| Live Bridge | Portfolio & Execution | Broker / Exchange | `approved_execution_packet.json` |

---

# 17. Required Agent Manifest Fields

Every agent must have:

```yaml
agent_id:
name:
version:
owner:
department:
agent_type:
lifecycle:
execution_mode:
mission:
scope:
non_scope:
responsibilities:
required_inputs:
optional_inputs:
output_fields:
allowed_tools:
forbidden_tools:
read_permissions:
write_permissions:
execute_permissions:
approval_requirements:
guardrails:
handoff:
observability:
tests:
supported_environments:
documentation_paths:
prompt_paths:
source_paths:
audit_requirements:
```

---

# 18. Required Department README Template

Every department should include a `README.md`.

```md
# <Department Name>

## Purpose

<What this department does>

## Agents

| Agent | Purpose | Status |
|---|---|---|

## Inputs

<Department-level inputs>

## Outputs

<Department-level outputs>

## Workflows

<Workflow files and descriptions>

## Dependencies

<Upstream dependencies>

## Downstream Consumers

<Who consumes this department's output>

## Governance Rules

<Approval, control, and safety rules>

## Testing

<How to test department independently>

## Integration Gate

<What must be true before integration>
```

---

# 19. Required Agent README Template

Every agent should include:

```md
# <Agent Name>

## Purpose

## Scope

## Non-Scope

## Inputs

## Outputs

## Allowed Tools

## Forbidden Tools

## Execution Mode

deterministic | llm | hybrid

## Deterministic Policy

## Evidence Requirements

## Handoff Contract

## Audit Requirements

## Tests

## Real-World Usage Example

## Failure Modes
```

---

# 20. Department-Level Quality Gates

Before integration, each department must pass:

```text
1. All agents run independently.
2. All agent manifests validate.
3. All local tests pass.
4. Department workflow runs with mock upstream data.
5. Department output schema validates.
6. Department audit metadata is present.
7. Department rejects unsafe or incomplete input.
8. Department README is complete.
9. Department is registered in workflow registry.
10. Department quality gate passes.
```

---

# 21. Global Quality Gates

Before production readiness, the full system must pass:

```text
1. Manifest validation for every agent.
2. Workflow registry validation.
3. Capability registry validation.
4. Agent audit checklist for every agent.
5. Department-level integration tests.
6. End-to-end lifecycle tests.
7. Security and permission tests.
8. Prompt injection tests.
9. Failure-path tests.
10. Compensation and rollback tests.
11. Observability and audit trace tests.
12. Human approval flow tests.
13. Kill switch tests.
14. Cost and latency budget tests.
15. Production readiness review.
```

---

# 22. Recommended Chronological Backlog

## Phase 0 Backlog — Shared Contracts

- [ ] Define base request/response/evidence/decision schemas.
- [ ] Define permission schema.
- [ ] Define lifecycle schema.
- [ ] Define audit metadata schema.
- [ ] Define manifest schema.
- [ ] Define handoff schemas.
- [ ] Add contract tests.

## Phase 1 Backlog — Runtime Layer

- [ ] Implement LLM Registry.
- [ ] Implement runtime protocol.
- [ ] Implement model router.
- [ ] Implement provider adapters.
- [ ] Implement Tool Executor.
- [ ] Implement Execution Context.
- [ ] Add runtime fallback tests.

## Phase 2 Backlog — Control Plane

- [ ] Implement registry loaders.
- [ ] Implement Control Plane orchestrator.
- [ ] Implement Planner Agent.
- [ ] Implement AI CEO/CIO Agent.
- [ ] Implement approval packets.
- [ ] Implement Board approval workflow.
- [ ] Add routing and approval tests.

## Phase 3 Backlog — Research

- [ ] Build Evidence Curator.
- [ ] Build Research Validation.
- [ ] Build Market Intelligence.
- [ ] Build Technical Analyst.
- [ ] Build Macro/Fundamental Context.
- [ ] Build News Sentiment.
- [ ] Build Seasonality Calendar.
- [ ] Build Cross Asset Intermarket.
- [ ] Build Strategy Scout.
- [ ] Build Strategy Hypothesis.
- [ ] Build Research Orchestrator.
- [ ] Add department workflow tests.

## Phase 4 Backlog — Strategy Development

- [ ] Build Strategy Spec Validator.
- [ ] Build Strategy Rule Normalizer.
- [ ] Build Strategy Template Selector.
- [ ] Build Strategy Risk Assumption.
- [ ] Build Strategy Test Plan.
- [ ] Build Strategy Creator.
- [ ] Build Strategy Reviewer.
- [ ] Build Strategy Spec Storage.
- [ ] Build Strategy Codegen.
- [ ] Build Strategy Code Storage.
- [ ] Build Strategy Cost Execution.
- [ ] Build Strategy Handoff.
- [ ] Build Strategy Creation Orchestrator.
- [ ] Add department workflow tests.

## Phase 5 Backlog — Validation & Backtesting Package

- [ ] Build Backtest capability.
- [ ] Build Statistical Validation capability.
- [ ] Build Robustness Monte Carlo capability.
- [ ] Build Optimization Comparator capability.
- [ ] Add capability tests.

## Phase 6 Backlog — Simulation

- [ ] Build Backtest agent/service wrapper.
- [ ] Build Backtest Analyst.
- [ ] Build Statistical Validation agent.
- [ ] Build Robustness agent.
- [ ] Build Optimization agent.
- [ ] Build Optimization Comparator.
- [ ] Build Simulation Evidence Curator.
- [ ] Build Simulation Orchestrator.
- [ ] Add simulation workflow tests.

## Phase 7 Backlog — Risk

- [ ] Build Risk Limit Auditor.
- [ ] Build Hard-Coded Risk Governor.
- [ ] Build Risk Approval Auditor.
- [ ] Build Portfolio Risk Monitor.
- [ ] Build Risk Reviewer.
- [ ] Build Risk Orchestrator.
- [ ] Add risk workflow tests.

## Phase 8 Backlog — Portfolio & Execution

- [ ] Build Strategy Lifecycle.
- [ ] Build Execution Readiness.
- [ ] Build Portfolio Manager.
- [ ] Build Allocation Optimizer.
- [ ] Build Paper Execution.
- [ ] Build Performance Reporter.
- [ ] Build Cost Optimizer.
- [ ] Build Kill Switch Service.
- [ ] Build Execution Planner.
- [ ] Build Execution Bridge.
- [ ] Build Live Execution.
- [ ] Build Portfolio Orchestrator.
- [ ] Add execution safety tests.

## Phase 9 Backlog — Operations & Audit

- [ ] Build Performance Reporter.
- [ ] Build Cost Optimizer.
- [ ] Build Audit Compliance.
- [ ] Add monitoring and compliance tests.

## Phase 10 Backlog — Dedicated Audit

- [ ] Build Audit Agent.
- [ ] Build audit evidence reader.
- [ ] Build audit report generator.
- [ ] Build audit remediation workflow.
- [ ] Add audit independence tests.

## Phase 11 Backlog — End-to-End Integration

- [ ] Integrate research to strategy handoff.
- [ ] Integrate strategy to simulation handoff.
- [ ] Integrate simulation to risk handoff.
- [ ] Integrate risk to portfolio handoff.
- [ ] Integrate paper execution to board approval.
- [ ] Integrate board approval to live bridge.
- [ ] Add happy-path test.
- [ ] Add rejection-path test.
- [ ] Add kill-switch test.
- [ ] Add audit trace replay test.

---

# 23. Final Implementation Rule

Do not integrate an agent into the full firm until it can pass these checks independently:

```text
- Its manifest validates.
- Its schemas validate.
- Its local tests pass.
- Its evaluator passes.
- Its permissions are restricted.
- Its audit metadata is complete.
- Its README explains purpose, scope, non-scope, inputs, outputs, and examples.
- Its output can be consumed by the next downstream department.
```

Build the firm one safe, testable department at a time.


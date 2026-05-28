# Agentic AI Playbook

Status: canonical framework-neutral playbook
Scope: framework-neutral design, governance, and implementation guidance
Use this when: you need the broad operating model, not project-specific status
Companion docs: project README, folder catalogs, specifications, implementation plans, runbooks, and traceability documents
Owner: project/platform architecture
Review cadence: quarterly or when architecture/governance changes materially

> **Version:** 1.2.0 HaruQuantAI-Aligned Final
> **Editing Principle:** Re-write and re-orient when helpful, but never strip out important information
> **Purpose:** A single, sequential, detailed documentation playbook for designing, building, integrating, operating, governing, debugging, and evolving production-grade agentic AI systems. This version is aligned with the HaruQuantAI Agent Standard and HaruQuantAI AI Tool Function Standard.
> **Framework Stance:** Framework-neutral. The standards can be implemented with any suitable agent framework, orchestration library, custom workflow engine, integration protocol, or capability adapter. Examples may reference common patterns such as agent frameworks, workflow engines, tool adapters, and protocol-based integrations, but no specific framework is mandatory.
> **Audience:** AI architects, backend engineers, systems designers, implementation teams, operators, security reviewers, future maintainers, and machine-assisted builders.

---

# 1. Why This Playbook Exists

This playbook is the broad guidance layer.

## 1.0 Document Relationship and Alignment

This playbook is one half of a reusable agentic AI governance kit:

| Document | Purpose |
|---|---|
| **Agentic AI Playbook** | Defines the broad architecture philosophy, operating model, governance model, workflow patterns, production-readiness concerns, and framework-neutral design principles. |
| **HaruQuantAI Agent Standard** | Defines the concrete HaruQuantAI implementation standard for Google ADK agents, including metadata, builder functions, instructions, permissions, allowed tools, blocked tools, output contracts, logging, audit, unit tests, usage examples, and evaluation requirements. |
| **HaruQuantAI AI Tool Function Standard** | Defines the concrete HaruQuantAI implementation standard for AI-callable tool functions exposed through `tools/{domain}/__init__.py`, including structured returns, metadata, logging, error handling, risk classification, tests, and usage examples. |
| **Agent Auditing Checklist** | Verifies whether a specific agent satisfies the standards defined by the Playbook and the implementation standards. |

When these documents overlap, use this rule:

> The Playbook defines the broad architecture philosophy. The HaruQuantAI Agent Standard defines how HaruQuantAI ADK agents must be built. The HaruQuantAI AI Tool Function Standard defines how HaruQuantAI AI-callable tools must be built. The Audit Checklist defines the evidence required to prove compliance.

The Playbook should remain framework-neutral at the architecture level. A project may implement these standards using any suitable agent framework, workflow engine, direct service layer, protocol-based integration layer, or custom runtime.

For HaruQuantAI specifically:

```text
Agents are built on Google ADK.
Agent files expose builder functions that return google.adk.agents.Agent.
Tools live under tools/{domain}/.
Each tool domain __init__.py is the official domain tool registry.
Anything exported through a tool domain __all__ is an official AI Tool.
```

## 1.0.1 Shared Terminology

| Term | Meaning |
|---|---|
| **Agent** | Framework-neutral: a bounded component that reasons, plans, acts, observes, evaluates, or supports a workflow. HaruQuantAI implementation: an LLM-powered decision unit built with Google ADK that interprets evidence, uses approved tools, and returns a structured response or handoff. |
| **Workflow** | An ordered or dynamic sequence of agent/tool/service steps that transforms inputs into outputs. |
| **Host / Orchestrator** | The component that owns routing, planning, state, memory, approvals, policy checks, and final synthesis. |
| **Worker Agent** | A specialized agent that performs a bounded task within a workflow. |
| **Tool** | An approved callable capability exposed to agents. It may be read-only or side-effecting. In HaruQuantAI, any function exposed through a tool domain `__init__.py` and listed in `__all__` is an official AI Tool and must follow the HaruQuantAI AI Tool Function Standard. |
| **Resource** | A read-only capability that exposes data, state, documents, or system context. |
| **Prompt / Template** | A reusable instruction pattern used to guide model behavior or human review. |
| **Capability Layer** | The adapter, service, protocol, SDK, or API boundary through which agents access external capabilities. |
| **Approval Gate** | A required human or governance checkpoint before a sensitive action proceeds. |
| **Control Gate** | A deterministic or policy-driven check that can allow, reject, block, or escalate an action. |
| **High-Impact Action** | An action that can materially affect users, money, safety, legal/compliance posture, production systems, data integrity, or external systems. |
| **Side Effect** | Any action that changes state outside the agent's local reasoning context. |
| **Compensation** | A rollback, reversal, correction, or mitigation step after a failed or partially completed side effect. |
| **Manifest** | A machine-readable contract describing an agent's identity, scope, inputs, outputs, tools, permissions, guardrails, ownership, tests, and lifecycle status. |
| **Registry** | A controlled catalog of approved agents, workflows, tools, policies, manifests, and ownership metadata. |
| **Audit Report** | Evidence record showing whether an agent passed the audit checklist and what must be remediated. |

## 1.0.2 Lifecycle and Environment Vocabulary

Use the same lifecycle and environment language across the Playbook and Audit Checklist.

**Agent lifecycle stages:**

```text
experimental → development → test → staging → production → deprecated
```

Lifecycle stage describes an agent's authorization maturity and allowed use.

**Runtime environments:**

```text
local → development → test → staging → production
```

Runtime environment describes where the agent or workflow runs.

A production environment does not automatically mean an agent is production-authorized. A production-authorized agent must also pass the required audit, quality gates, approvals, and operational readiness checks.

## 1.0.3 Playbook-to-Audit Compatibility Matrix

| Playbook Standard | Audit Checklist Section |
|---|---|
| Core reasoning loop | Reasoning Loop Checklist |
| Capability boundaries | Tool Access and Permission Checklist |
| Agent anatomy | Identity, Role, Input, Output, and Dependency Checklists |
| Execution mode standard | LLM / Deterministic Execution Mode Checklist |
| Prompt standards | Prompt / Instruction Checklist |
| Workflow orchestration | Workflow Position and Handoff Checklists |
| Memory and state | Memory, Context, and State Mutation Checklists |
| Policy and approvals | Guardrails, Human-in-the-Loop, and Governance Checklists |
| Idempotency and compensation | Error Handling, Recovery, and State Mutation Checklists |
| Evaluation | Agent Performance Evaluation Checklist |
| Observability | Observability and Audit Logging Checklist |
| Security | Security and Access Control Checklist |
| Production readiness | Master Audit Summary and Audit Decision Rule |
| Manifest and registry governance | Manifest, Registry, and Quality Gate sections |

## 1.0.4 HaruQuantAI Implementation Alignment

This Playbook is intentionally broad. HaruQuantAI uses a stricter implementation standard.

```text
Playbook = philosophy, architecture, governance, production model
Agent Standard = concrete Google ADK agent implementation law
Tool Function Standard = concrete AI tool function implementation law
Audit Checklist = evidence and compliance verification
```

HaruQuantAI follows these implementation principles:

- flat files first
- few agents, many reliable tools
- Google ADK as the agent framework
- tool-heavy, policy-gated workflows
- deterministic policy enforcement
- `request_id` and `workflow_id` traceability
- standard tool and agent response schemas
- unit tests and usage examples for every official agent/tool
- audit footprint for important agent runs and high-impact decisions
- folders only when complexity earns them

Project-specific truth lives in the companion docs:

* agent, workflow, and tool catalogs
* implementation plans
* system specifications
* architecture decision records
* runbooks and operational guides
* live status, approvals, signoff, and traceability records

Use this playbook whenever you want to:

* design a new agentic AI system
* document a production-ready multi-agent architecture
* define system boundaries between reasoning and external capabilities
* choose the correct workflow pattern for a use case
* decide whether a capability belongs in the host/orchestrator, an agent, a workflow, a tool, a resource, a prompt/template, or an external capability provider
* structure memory, state, routing, evaluation, and approvals
* create standards for implementation, testing, deployment, debugging, governance, and operations
* build reusable, maintainable systems instead of ad hoc AI pipelines
* preserve explicit design logic for future-you

This document is intentionally written to be useful as:

* a technical architecture document
* a build and implementation playbook
* a reusable note system for future design work
* a machine-readable and human-readable reference for how the system should be built and operated

## 1.1 Authoring Rule for Future Versions

This playbook is not only a management artifact and not only a coding guide.

It is also:

* a future reference manual for the system architect
* a recovery guide when returning to the system months later
* a decision aid for choosing workflow patterns and boundaries
* a documentation backbone for companion documents like SRS, Design, Runbooks, Policy Maps, and ADRs

### Governing editorial rule

> **When in doubt, prefer explicitness over elegance.**

### Versioning rule

Future versions may re-order, tighten language, and improve structure, but should follow this rule:

> **Add and clarify. Do not silently remove useful engineering detail.**

---

# 2. Core Philosophy

An agentic system is not just an LLM with tool calls.
It is a structured system with:

* reasoning
* planning
* action
* observation
* evaluation
* refinement

That loop is the foundation of all serious agentic systems.

## 2.1 The Core Loop

```text
User Goal
 ↓
Reason → model, rules, or deterministic logic interpret the goal
 ↓
Plan → orchestrator decomposes work into tasks or workflow nodes
 ↓
Act → tools, APIs, services, or capability adapters execute bounded actions
 ↓
Observe → structured tool, resource, or service outputs are captured
 ↓
Evaluate → self-checks, external evaluators, tests, or reviewers score quality and correctness
 ↓
Refine (Loop or Finish) → Feedback loops, retry logic, or final response
```

This loop must appear explicitly or implicitly in every workflow you design.

## 2.2 Enterprise Extension of the Core Loop

In production and enterprise settings, the loop must also account for:

* policy enforcement
* approval boundaries
* evidence capture
* auditability
* rollback or compensation
* cost governance
* escalation paths

So a production interpretation often becomes:

```text
Reason → Plan → Policy Check → Act → Observe → Evaluate → Approve / Refine / Compensate / Finish
```

This is an extension, not a replacement, of the original loop.

## 2.3 Golden Mental Model

**The host/orchestrator is the brain.
The capability layer is the action and integration bus.**

This single distinction prevents a large amount of design confusion.

---

# 3. System Design Principle

Every production-grade agentic system should be designed in layers.

## 3.1 Recommended Layered Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│        Interface & Routing Layer           │
│ • User-facing entry points (FastAPI/Flask Gateway, web ui,│
│  CLI, Chat Interface, etc.)               │
│ • Router Agent   • Intent Classifier & Dispatcher  │
└───────────────────────┬─────────────────────┬───────────────┘
            │           │
┌───────────────────────▼──────────┐ ┌───────▼────────────────┐
│    Orchestration     │ │  Workflow Engine   │
│ • Session & Context Manager   │ │ • Sequential/Parallel │
│ • Task Decomposer & Planner   │ │ • Conditional Routing │
│ • Conflict & State Sync     │ │ • Eval-Optimizer Loop │
└───────────────────────┬──────────┘ └───────┬────────────────┘
            │           │
┌───────────────────────▼─────────────────────▼────────────────┐
│         Agent Layer (Workers)          │
│ • Persona/Role-Defined Agents • Tool-Augmented LLMs    │
│ • Structured I/O (typed schemas) • Short/Long-Term Memory │
└───────────────────────┬─────────────────────┬────────────────┘
            │           │
┌───────────────────────▼─────────────────────▼────────────────┐
│       Capability Bus (Integration Layer)      │
│ • Capability Client / Adapter Wrappers (stdio/HTTP) → Domain Capability Provider / Servers   │
│ • Tools (Do) • Resources (Read) • Prompts (Guide)      │
└───────────────────────┬─────────────────────┬────────────────┘
            │           │
┌───────────────────────▼─────────────────────▼────────────────┐
│        Data & External Systems            │
│ • Vector DBs (Chroma/Vertex/etc.) • SQL/NoSQL        │
│ • Web Search • REST/Capability APIs • Files • Services       │
└───────────────────────┬─────────────────────┬────────────────┘
            │           │
┌───────────────────────▼─────────────────────▼────────────────┐
│      Evaluation & Observability Layer          │
│ • Evaluator component • LLM-as-Judge • Trajectory Logs   │
│ • Capability Inspector/Debug • Cloud Logging • Cost/Latency    │
└──────────────────────────────────────────────────────────────┘
```

## 3.2 Why the Explicit Routing Layer Must Remain

The routing layer must stay visible because it answers:

* who receives the request first
* who normalizes it
* who classifies intent
* who dispatches to the correct workflow
* where first-pass policy checks happen
* where fallback/default routing lives

The routing layer is not “just a detail.”
It is one of the highest-value design anchors in an agentic system.

## 3.3 Enterprise Overlay on the Layered Architecture

The original layered design remains the technical spine.
The enterprise additions sit across these layers:

* security and identity
* approval and escalation
* policy enforcement
* audit logging
* benchmark governance
* ownership and change control
* incident response
* cost control

These are cross-cutting controls, not substitutes for the original architecture.

## 3.4 Architecture Review Questions

When reviewing architecture, ask:

* Is the routing layer explicit?
* Is orchestration separated from capability access?
* Are side-effecting capabilities behind clean boundaries?
* Is state ownership clear?
* Is evaluation visible as a first-class layer?
* Are policy, approval, and audit concerns layered on top instead of mixed into everything?

---

# 4. Unified Mental Model: Orchestrator + Capability Layer

To build robust systems, separate intelligence from capability access.

## 4.1 The Orchestrator / Agent Framework Handles

* reasoning coordination
* planning
* orchestration
* routing
* memory and state
* multi-agent workflow coordination
* evaluation and refinement loops
* policy and approval orchestration

## 4.2 The Capability Layer Handles

* standardized access to external capabilities
* action tools
* read-only resources
* reusable prompts/templates
* protocol-based or adapter-based boundaries between host and capability providers

## 4.3 Division of Responsibility

| Layer | Responsibility |
|---|---|
| **Host / Agentic App** | user interaction, reasoning, planning, memory, routing, approvals, final synthesis |
| **Capability Client / Adapter** | protocol connector, session management, capability discovery, clean interface to host |
| **Capability Provider / Server** | capability provider, domain-specific tools/resources/prompts, business logic |

**Golden Rule 1:** The host/orchestrator is the brain. The capability layer is the action and integration bus.
**Golden Rule 2:** Host plans. Adapter connects. Provider executes or returns data.

## 4.4 Design Consequence

If the system starts mixing:

* memory into capability providers
* orchestration into capability providers
* policy only into prompts
* domain logic only into the host

then boundaries usually start degrading.

---

# 5. Capability Adapter / Protocol Design Standard

External capabilities should be exposed behind clean, typed, governed boundaries. This can be done through direct tool wrappers, internal service clients, protocol servers such as an external capability protocol, HTTP APIs, SDK adapters, or other framework-specific integration mechanisms.

## 5.1 Capability Access Architecture

```text
User
 ↓
Host Application / Agent
 ↓
Capability Client / Adapter
 ↓
Capability Provider / Server
```

## 5.2 Capability Model

| Type | Purpose | Naming Convention | Example |
|---|---|---|---|
| **Tool** | Do/Act | `verb_noun` | `summarize_document`, `create_ticket`, `search_docs` |
| **Resource** | Read/State | `domain://path` | `policy://access`, `docs://project/overview` |
| **Prompt** | Guide/Template | `*_prompt` | `review_prompt`, `approval_prompt` |

### Quick rule

* does it do something? → tool
* does it show something? → resource
* does it guide something? → prompt

### HaruQuantAI Tool Domain Registry Rule

In HaruQuantAI, the capability layer is currently represented primarily by the `tools/` folder.

```text

    tools/
        data/
            __init__.py
            market_data.py
            validators.py

        execution/
            __init__.py
            orders.py
            positions.py
```

Each folder inside `tools/` is a tool domain.

The domain-level `__init__.py` file is the official registry for that domain.

Any function imported and listed in the domain `__all__` is an official AI Tool.

Official AI Tools must follow the HaruQuantAI AI Tool Function Standard.

Correct import pattern:

```python
from tools.data import get_market_data
from tools.execution import place_order
```

Avoid deep imports in agents and workflows:

```python
from tools.data.market_data import get_market_data
```

Do not introduce a separate adapter/provider layer unless there is a real boundary, such as remote deployment, shared service ownership, multi-tenant access, credential isolation, or protocol-level reuse.

## 5.3 Client / Adapter Features and Decision Rules

| Feature | Purpose | When to Use |
|---|---|---|
| **Scoped Access** | Limit a provider to approved folders, tenants, domains, or resources | Provider should not see the full project or full data estate |
| **Model Delegation** | Allow a provider to request model assistance through the host, if the chosen framework supports it | The host must control model access, credentials, cost, and policy |
| **User Input Request** | Ask the user or reviewer for missing data, confirmation, or choices | Required inputs are missing or a decision needs approval |

### Quick rule

* scope data access explicitly
* keep model credentials controlled by the host
* request user input when required information or approval is missing

## 5.4 Transport Selection

| Transport | Best For | Rule of Thumb |
|---|---|---|
| **STDIO** | local dev, subprocess, desktop | start here; host launches server directly |
| **HTTP / RPC / Streaming Protocols** | remote, multi-user, production | move here when a provider becomes deployable or shared |

## 5.5 Capability Provider Design Standards

* One capability provider = one coherent domain. Avoid god providers.
* Tools should be narrow and specific.
* Resources should be stable and readable.
* Prompts should be reusable.
* Use typed parameters, clear docstrings, and structured return values.
* Log to `stderr` only for debug in stdio mode. Never pollute `stdout`.
* Lifecycle should be: Initialize → Discover → Operate → Shutdown cleanly.

## 5.6 Adapter & Host Wrapper Pattern

```python
class KnowledgeServerConnection:
  def __init__(self, session):
    self.session = session

  async def search_docs(self, query: str) -> list[str]:
    res = await self.session.call_tool(
      "search_docs",
      arguments={"query": query}
    )
    return [item.text for item in res.content]
```

### Wrapper rules

* encapsulate client logic
* initialize once and reuse sessions
* host routes → adapter calls → capability provider executes → host synthesizes
* memory stays in the host
* do not push conversation state into capability providers

## 5.7 Capability Integration Debugging Checklist

| Symptom | Fix |
|---|---|
| Server hangs on start | normal for stdio; it waits for JSON-RPC messages |
| JSON errors on Enter | normal; raw stdin is not the expected JSON-RPC or protocol message |
| Debug inspector or client won’t connect | verify runtime path, script path, dependencies, auth, and no stdout pollution |
| Tool call fails | check name, argument types, server-side error handling |
| HTTP client fails | verify endpoint, auth, transport compatibility, availability |

## 5.8 When to Introduce a Capability Protocol or Adapter Layer

**Use a capability protocol or adapter layer when:**

* a host or agent needs repeatable access to external capabilities
* multiple apps or agents should reuse the same capability provider
* workflows rely on manual handoffs or duplicated integrations
* there is a real system boundary
* you want typed, reusable, and governed capability access

**Avoid an external protocol layer when:**

* everything is local and trivial inside one script
* no meaningful system boundary exists
* a plain internal function call is enough

## 5.9 Enterprise Additions to Capability Providers

For each capability provider, adapter, or protocol server, document:

* domain purpose
* owner
* side-effect risk level
* allowed callers
* credentials used
* audit requirements
* failure modes
* rate limits
* timeout budget
* escalation owner
* contract version
* deprecation notes

## 5.10 Capability Provider Template

```python
# Example shown as pseudocode. Implement using your chosen framework or protocol.
class KnowledgeCapabilityProvider:

    def search_docs(self, query: str) -> list[str]:
        """Search approved project documentation."""
        # validate inputs
        # apply access policy
        # execute business logic
        # return structured result
        return []

    def access_policy(self) -> str:
        return "Access policy contents"

    def review_prompt(self) -> str:
        return "Review the proposed output against the current quality and policy standards."
```

---

# 6. The Anatomy of an Agent

Every agent should be defined through core components.

| Component | Defines | Examples |
|---|---|---|
| **Persona** | role, tone, expertise, behavioral constraints | Domain Analyst |
| **Brain** | LLM, reasoning engine, output behavior, generation constraints | Gemini, OpenAI, Qwen |
| **Capabilities** | what the agent can do | call tools, query capability providers, search web, query DB |
| **Memory** | what the agent can remember or retrieve | short-term state, long-term vector memory |
| **State** | what stage the agent or workflow is in | IDLE, PLANNING, EXECUTING, OBSERVING, EVALUATING, COMPLETE, ERROR |

## 6.1 Enterprise Additions to Agent Anatomy

| Component | Defines |
|---|---|
| **Policy Profile** | what the agent is allowed to do, say, access, and trigger |
| **Approval Profile** | which actions require approval, evidence, or escalation |
| **Ownership** | team owner, operational owner, on-call owner |
| **Risk Class** | read-only, low-risk write, high-risk, irreversible side effects |
| **Audit Scope** | what must be logged for traceability |

## 6.2 Agent Definition Template

```python
# Example uses Python-style typed schemas. Use the equivalent in your stack.
from pydantic import BaseModel
# Replace `Agent` with the agent abstraction from your chosen framework.

class AnalysisInput(BaseModel):
  subject: str
  context: str | None = None

class AnalysisOutput(BaseModel):
  summary: str
  confidence: float
  flags: list[str]

analysis_agent = AgentLike(
  name="analysis_agent",
  model="gemini-3.1-pro",
  instruction="""
You are an analysis agent.
Use available tools carefully.
Return structured output only.
Escalate when evidence is weak or policy blocks action.
"""
)
```

## 6.3 Agent Catalog Requirements

Each agent should be documented with:

* purpose
* input schema
* output schema
* persona
* model
* tools/resources/prompts used
* memory usage
* state transitions
* policy profile
* approval profile
* owner
* benchmark tasks
* failure modes

## 6.4 Execution Mode Standard

Every agent must declare one execution mode:

| Mode | Meaning |
|---|---|
| **Deterministic** | Decisions are produced by fixed code, rules, schemas, or algorithms. |
| **LLM-driven** | Decisions rely primarily on model reasoning or generation. |
| **Hybrid** | Deterministic logic and model reasoning both participate, with explicit boundaries. |

For hybrid agents, document:

* which responsibilities are deterministic
* which responsibilities use model reasoning
* which safety-critical decisions require deterministic validation
* what happens when the model is unavailable or low-confidence
* how logs show whether a decision came from code, model reasoning, or a hybrid path

Safety-critical decisions should not rely only on model judgment. They should be blocked, validated, or reviewed by deterministic policy, tests, approval gates, or control gates.

## 6.5 Agent Manifest Standard

Every production-intended agent should have a machine-readable manifest. The manifest is the contract used by the agent registry, workflow catalog, CI quality gates, audit checklist, and operational review.

A useful manifest declares:

1. agent identity and version
2. owner and maintainers
3. lifecycle stage
4. execution mode
5. mission, scope, and non-scope
6. required inputs and output schema
7. allowed tools, resources, prompts, and forbidden capabilities
8. dependencies and downstream consumers
9. guardrails, control gates, and approval rules
10. observability and audit requirements
11. tests and evaluation requirements
12. supported environments
13. documentation, prompt, and source paths

## 6.6 Agent Registry Standard

A registry is the controlled catalog of agents that are allowed to participate in workflows. The registry should identify:

* approved agents
* deprecated agents
* lifecycle stage
* ownership
* manifest path
* prompt version
* source path
* allowed workflows
* approval requirements
* audit status
* last review date

No high-impact or production-capable agent should be used outside the registry unless it is explicitly marked experimental and isolated from production side effects.

## 6.7 Agent Audit Integration Standard

The Audit Checklist is the evidence mechanism for this Playbook. Use it before an agent is promoted from one lifecycle stage to another and whenever the agent gains new tools, permissions, workflow authority, or production impact.

Minimum audit moments:

* before registry acceptance
* before staging promotion
* before production promotion
* after major prompt/model/tool changes
* after incidents or repeated failures
* before allowing new side-effecting capabilities

## 6.8 HaruQuantAI Agent Implementation Standard

For HaruQuantAI, every agent must follow the HaruQuantAI Agent Standard.

At minimum, each agent must declare:

- agent name
- version
- department
- description
- risk level
- approval requirement
- input contract
- output contract
- permissions
- allowed tools
- blocked tools
- instruction text or instruction file
- builder function
- logging footprint
- unit tests
- usage example
- evaluation scenarios where needed

Every HaruQuantAI agent must be built through a builder function that returns a Google ADK `Agent`.

Example pattern:

```python
from google.adk.agents import Agent


def build_research_lead_agent() -> Agent:
    return Agent(
        name=AGENT_NAME,
        model=AGENT_MODEL,
        description=AGENT_DESCRIPTION,
        instruction=AGENT_INSTRUCTION,
        tools=ALLOWED_TOOLS,
    )
```

The builder must not call tools, mutate external state, create files, run workflows, or perform runtime work.

## 6.9 Standard HaruQuantAI Agent Response Schema

HaruQuantAI workflows should not depend on raw model output.

Agent runtime results should be normalized into this shape:

```python
{
    "status": "success | error | blocked | needs_approval | needs_clarification",
    "message": str,
    "data": Any,
    "decision": Any,
    "evidence": list,
    "tool_calls": list,
    "error": None | {
        "code": str,
        "details": str,
    },
    "metadata": {
        "agent_name": str,
        "agent_version": str,
        "agent_department": str,
        "agent_risk_level": str,
        "request_id": str,
        "workflow_id": str,
        "execution_ms": float,
        "output_contract": str,
        "approval_required": bool,
    },
}
```

Valid statuses:

```text
success
error
blocked
needs_approval
needs_clarification
```

Important workflows should validate the response before passing it downstream.

---

# 7. Agent Reasoning and Prompting Standards

Prompting is not decoration. It is system design.

## 7.1 Prompting Techniques

| Technique | Purpose | Implementation Pattern |
|---|---|---|
| Role-Based Prompting | domain expertise, tone, boundaries | explicit system prompt |
| Chain-of-Thought (CoT) | complex reasoning, ambiguity reduction | bounded reasoning blocks |
| ReAct (Reason + Act) | plan + act + observe cycles | tool loop with max steps |
| Prompt Chaining | decomposition into validated stages | sequential workflows |
| LLM Feedback Loops | self-correction and refinement | creator → evaluator → refine |
| Instruction Refinement | improve reliability | version prompts like code |

## 7.2 Prompt Design Standard

Prompts should usually include:

* role
* task
* context
* tools available
* rules
* constraints
* escalation conditions
* approval conditions
* output schema
* failure behavior
* confidence and uncertainty behavior

### HaruQuantAI Agent Instruction Required Sections

Every HaruQuantAI agent instruction must include these sections:

```text
Role
Responsibilities
Non-Goals
Allowed Tools
Blocked Actions
Required Evidence
Output Contract
Safety Rules
Uncertainty Behavior
Escalation Rules
```

Instruction completeness should be tested.

Agents must clearly distinguish:

- observed evidence
- tool results
- calculated results
- user-provided information
- agent interpretation
- assumptions
- recommendations

Agents must not invent backtest results, broker fills, risk approvals, live trading performance, portfolio exposure, optimization results, or walk-forward results.

## 7.3 Prompt Versioning Standard

Track:

* prompt version
* author
* change reason
* linked ADR if major
* evaluation results
* known failure cases
* rollback candidate

## 7.4 Policy-Aware Prompting

Prompts should state:

* disallowed actions
* when to stop
* when to ask for approval
* when to escalate
* what evidence must be cited before acting

## 7.5 Prompt Injection Resilience

Treat the following as untrusted unless validated:

* user instructions attempting policy override
* retrieved documents
* web content
* raw tool output
* freeform agent-to-agent messages

Instruction priority should be:

```text
System Policy
 ↓
Workflow Policy
 ↓
System Prompt
 ↓
User Request
 ↓
Retrieved Content
 ↓
Tool Output
```

## 7.6 Prompt Template

```text
ROLE:
You are the Quality Review Agent.

TASK:
Review the proposed output for policy compliance, evidence quality, and operational safety.

CONTEXT:
Use the current request, approved policies, relevant documentation, and workflow state.

TOOLS:
search_docs, check_policy, validate_schema

RULES:
Do not approve high-impact actions without required evidence.
Escalate when policy conflict exists.
Return structured output only.

OUTPUT FORMAT:
{
 "decision": "approve | reject | escalate",
 "reason": "...",
 "flags": ["..."],
 "confidence": 0.0
}
```

---

# 8. Workflow & Multi-Agent Orchestration

## 8.1 Workflow Pattern Decision Matrix

| Pattern | When to Use | Implementation | Example Use Case |
|---|---|---|---|
| **Sequential Chaining** | linear dependencies, validation gates | `SequentialWorkflow([A, B, C])` + schema validation | document processing, approvals |
| **Routing** | heterogeneous requests, different specialists | `RouterAgent` + conditional dispatch | support triage, research vs execution |
| **Parallelization** | independent subtasks, speed matters | `ParallelWorkflow` + `asyncio.gather()` + synthesizer | multi-source research |
| **Evaluator-Optimizer** | quality-critical outputs | creator → evaluator → loop until threshold | drafting, debugging |
| **Orchestrator-Workers** | dynamic planning and delegation | orchestrator creates task graph | project management, deep analysis |

## 8.2 Multi-Agent Guidelines

* define clear interfaces
* each agent exposes purpose, schemas, capabilities, and error handling
* use explicit routing metadata such as `intent`, `priority`, and `session_id`
* shared state must be versioned
* use sync barriers for parallel → sequential handoffs
* specialized agents beat monolithic agents
* avoid capability overlap
* design handoffs explicitly

## 8.3 Approval-Aware Workflow Design

For each workflow, document:

* approval checkpoints
* approver type
* evidence package required
* stale approval timeout
* what happens if approval is denied
* what happens if approval is unavailable

## 8.4 Compensation-Aware Workflow Design

For each side-effecting workflow, document:

* preconditions
* irreversible steps
* compensating actions
* idempotency key
* exactly-once vs at-least-once semantics
* rollback boundary
* partial completion behavior

## 8.5 Escalation-Aware Workflow Design

Specify:

* human escalation triggers
* policy escalation triggers
* ambiguity escalation triggers
* repeated-failure escalation triggers
* security anomaly escalation triggers

## 8.6 Workflow Review Template

Every significant workflow should document:

1. goal
2. trigger
3. input schema
4. output schema
5. pattern used
6. agents involved
7. tools/resources/prompts involved
8. policy checks
9. approval checks
10. compensation design
11. observability requirements
12. evaluation metrics
13. owner
14. failure modes

## 8.7 Workflow Template

```python
# Example uses Python-style typed schemas. Use the equivalent in your stack.
from pydantic import BaseModel

class ResearchRequest(BaseModel):
  query: str

class ResearchResult(BaseModel):
  summary: str
  citations: list[str]
  confidence: float

# route -> plan -> parallel retrieve -> synthesize -> evaluate -> finalize
```

---

# 9. Memory, State, and Context Engineering

## 9.1 Memory Types

| Type | Storage | Use Case |
|---|---|---|
| Short-Term | session context, ephemeral dict | active conversation, workflow state |
| Long-Term | vector DB, KB, structured records | user prefs, historical interactions, RAG |
| Procedural | tool registry, FSM, workflow defs, schemas, policies | routing rules, retry logic, state machines |

## 9.2 State Machines

All non-trivial workflows should have explicit state transitions.

```text
IDLE → PLANNING → EXECUTING → OBSERVING → EVALUATING → COMPLETE
                     ↘ ERROR
```

### Rules

* define typed schemas for state payloads
* transitions must be logged
* transitions must be bounded
* loops must have max iteration limits
* error states must be recoverable or terminal by design
* handle concurrency with async locks or optimistic concurrency when needed

## 9.3 Structured Output Standard

All important agent outputs should be structured.

* always enforce structured outputs with typed schemas, such as JSON Schema, Pydantic, Zod, protobuf, or equivalent
* prefer model-native JSON mode when available
* validate before passing to downstream steps

### HaruQuantAI Standard Tool Response Schema

Every official HaruQuantAI AI Tool should return:

```python
{
    "status": "success | error",
    "message": str,
    "data": Any,
    "error": None | {
        "code": str,
        "details": str,
    },
    "metadata": {
        "tool_name": str,
        "tool_version": str,
        "tool_category": str,
        "tool_risk_level": str,
        "request_id": str | None,
        "execution_ms": float,
        "read_only": bool,
        "writes_file": bool,
        "modifies_database": bool,
        "places_trade": bool,
        "requires_network": bool,
    },
}
```

A tool must never return `None` or silently fail.

Every official AI Tool must return either:

```text
success with data
success with empty data and a clear message
error with a clear reason
```

## 9.4 Context Engineering Standard

Many failures are context failures, not reasoning failures.

For each workflow, define:

* required context blocks
* optional context blocks
* ranking/prioritization order
* context budget allocation
* stale context eviction rules
* summarization/compression rules
* source-of-truth precedence rules
* contradiction resolution rules

### Context precedence example

```text
System Policy
 ↓
Workflow Policy
 ↓
Structured Session State
 ↓
Approved User Input
 ↓
Trusted Resources / Databases
 ↓
Retrieved Documents
 ↓
Raw Tool Output
```

### Context inclusion checklist

Before sending context to a model, ask:

* is it necessary?
* is it fresh?
* is it trusted?
* is it duplicated?
* is it too verbose?
* does it conflict with a higher-priority source?

## 9.5 Data Retention and Tenant Isolation

Define:

* what is stored
* how long it is stored
* who can access it
* what gets deleted
* what must be redacted
* what may be used for evaluation or retraining

If multi-tenant:

* isolate memory by tenant
* isolate vector stores or namespaces
* prevent cross-tenant retrieval
* log tenant context in traces

## 9.6 State Manager Template

```python
from enum import Enum
# Example uses Python-style typed schemas. Use the equivalent in your stack.
from pydantic import BaseModel

class WorkflowState(str, Enum):
  IDLE = "IDLE"
  PLANNING = "PLANNING"
  EXECUTING = "EXECUTING"
  OBSERVING = "OBSERVING"
  EVALUATING = "EVALUATING"
  COMPLETE = "COMPLETE"
  ERROR = "ERROR"

class StatePayload(BaseModel):
  state: WorkflowState
  session_id: str
  data: dict
```

---

# 10. External Integration Standard

## 10.1 Web Search

Use as a tool or external capability when current information is required.

Rules:

* ground results
* apply freshness
* cite sources
* never guess current facts

## 10.2 Databases

Use structured access patterns:

* SQLAlchemy or equivalent
* text-to-SQL with validation
* read-only replicas where appropriate
* bounded query policies

## 10.3 APIs

Wrap all major APIs through:

* agent framework tools
* capability-layer tools
* typed clients

Add:

* timeout handling
* retries
* auth rotation
* rate limits

## 10.4 Agentic RAG

Recommended loop:

* reformulate query
* retrieve
* reflect
* retry if weak
* synthesize

## 10.5 Integration Risk Classes

Document whether each integration is:

* read-only
* low-risk write
* high-risk write
* financially material
* compliance-sensitive
* irreversible

## 10.6 Integration Wrapper Policy

Every external integration wrapper should define:

* auth method
* timeout
* retry policy
* circuit breaker policy
* idempotency support
* schema validation
* logging redaction
* error mapping
* ownership

## 10.7 Tool Output Sanitization

Never treat tool output as automatically trusted.
Sanitize, validate, and reclassify it before reusing it as model context.

## 10.8 API Client Template

```python
import httpx

class ResearchApiClient:
  def __init__(self, base_url: str, api_key: str):
    self.base_url = base_url
    self.api_key = api_key

  async def search(self, query: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
      resp = await client.get(
        f"{self.base_url}/search",
        params={"q": query},
        headers={"Authorization": f"Bearer {self.api_key}"}
      )
      resp.raise_for_status()
      return resp.json()
```

---

# 11. Human Approval, Escalation, and Kill-Switch Standard

## 11.1 Action Classes

| Class | Description | Default Rule |
|---|---|---|
| A | read-only, no side effect | auto-allowed |
| B | low-risk write, reversible | allow with policy gate |
| C | material write, approval-worthy | require human approval |
| D | high-risk, financially material, compliance sensitive | require strict approval and audit |
| E | irreversible or prohibited | deny or require special process |

## 11.2 Approval Packet

Before approval, surface:

* proposed action
* reason for action
* evidence used
* confidence and uncertainty
* policy checks passed
* risk classification
* alternatives considered
* expected impact
* rollback or compensation plan

## 11.3 Escalation Triggers

Escalate when:

* policy conflict exists
* required evidence is missing
* repeated failures occur
* financial/compliance threshold exceeded
* ambiguity remains unresolved
* security anomaly detected

## 11.4 Kill Switch Design

Document:

* who can trigger it
* what it disables
* whether it is global or domain-specific
* whether it drains in-flight workflows or hard-stops them
* recovery procedure
* post-incident checks before re-enable

## 11.5 Approval Packet Template

```json
{
 "action": "publish_report",
 "reason": "Review checks passed and required evidence is attached",
 "evidence": [
  "source_summary",
  "policy_check",
  "schema_validation_result"
 ],
 "confidence": 0.86,
 "risk_class": "C",
 "alternatives": ["request more evidence", "publish as draft"],
 "compensation_plan": "retract or correct the report if post-publication checks fail"
}
```

---

# 12. Policy and Guardrail Enforcement Map

Policy must not live only in prompts.

## 12.1 Enforcement Layers

| Layer | What to Enforce |
|---|---|
| UI / Gateway | auth, request validation, rate limits |
| Routing Layer | request class, tenant checks, allowed workflow |
| Host / Orchestrator | policy selection, approval gating, escalation |
| Agent Prompt | behavioral constraints, evidence rules |
| Tool Wrapper | argument validation, timeout/retry policy |
| Capability Provider / Server | domain-specific business policy |
| Downstream System | final authorization, transaction constraints |

## 12.2 Policy Categories

* input policy
* output policy
* tool-use policy
* data access policy
* model policy
* approval policy
* escalation policy
* retention policy

## 12.3 Policy Authoring Rule

Every policy should define:

* name
* scope
* owner
* enforcement layer
* failure behavior
* logging requirement
* exception process
* review cadence

## 12.4 Policy Map Template

```yaml
policy_name: high_impact_action_policy
scope: controlled_action_workflows
owner: governance_team
enforcement_layers:
 - routing
 - orchestrator
 - capability_adapter
failure_behavior: reject_and_escalate
logging_requirement: audit_log_required
review_cadence: monthly
```

---

# 13. Failure Recovery, Idempotency, and Compensation

## 13.1 Reliability Principles

* assume retries will happen
* assume partial failures will happen
* assume duplicate requests may happen
* assume downstream systems may succeed after timeout
* assume some steps cannot be rolled back

## 13.2 Required Design Decisions

For each side-effecting action, document:

* idempotency key
* duplicate detection method
* retry semantics
* compensation action
* rollback feasibility
* exactly-once vs at-least-once semantics
* audit record

## 13.3 Compensation Patterns

Examples:

* created record → mark cancelled
* submitted external request → cancel, reverse, or issue corrective action if allowed
* provisioned resource → deprovision resource
* wrong notification → send correction

## 13.4 Saga-Style Guidance

If a workflow spans multiple systems:

* define step order
* define compensation order
* define commit boundary
* define terminal failure handling

## 13.5 Compensation Template

```python
class CompensationPlan:
  def __init__(self, action_id: str):
    self.action_id = action_id

  async def compensate(self):
    # reverse or mitigate side effect
    # log audit event
    pass
```

---

# 14. Schema Evolution and Contract Governance

## 14.1 Why It Matters

Multi-agent systems break when contracts drift invisibly.

## 14.2 Rules

* every important schema gets a version
* breaking changes require migration notes
* optional fields must be deliberate, not accidental
* contract tests must run in CI
* downstream consumers must validate, not assume

## 14.3 Contract Checklist

For each schema/interface, document:

* version
* owner
* producer
* consumer
* required fields
* optional fields
* invariants
* deprecation date
* migration strategy

## 14.4 Schema Template

```python
# Example uses Python-style typed schemas. Use the equivalent in your stack.
from pydantic import BaseModel, Field

class ReviewDecisionV1(BaseModel):
  decision: str = Field(description="approve | reject | escalate")
  reason: str
  confidence: float
  flags: list[str] = []
  schema_version: str = "1.0.0"
```

---

# 15. Evaluation, Reliability, and Quality Gates

## 15.1 Evaluation Strategies

| Level | Focus | Method |
|---|---|---|
| Response | final output quality | evaluator rubric, LLM-as-judge |
| Step | tool calls, intermediate logic | unit tests, schema validation, logs |
| Trajectory | full workflow efficiency | success rate, latency, cost, retries |

## 15.2 Metrics and Thresholds

| Metric | Threshold | How to Measure |
|---|---|---|
| Output Schema Compliance | ≥95% | validation logs |
| Tool/Capability Call Success | ≥98% | retry/failure counters |
| Workflow Completion | ≥90% | end-to-end test suite |
| Hallucination Rate | ≤5% | ground-truth comparison + judge |
| Latency (p95) | ≤3s simple / ≤10s complex | middleware / metrics |
| Cost per Query | project-defined | token usage × routing policy |

## 15.3 Enterprise Benchmark Governance

Evaluation is not complete without benchmark ownership.

Define:

* golden tasks
* adversarial tasks
* regression tasks
* domain hard cases
* failure-path benchmarks
* refresh cadence
* benchmark owner
* promotion criteria for prompts/models/tools

## 15.4 Promotion Policy

No prompt, model, workflow, or server should be promoted without:

* regression pass
* benchmark pass
* security review if needed
* rollback plan
* owner sign-off

## 15.5 Evaluator Template

```python
class EvaluationResult:
  def __init__(self, score: float, notes: str):
    self.score = score
    self.notes = notes

def evaluate_output(output: dict) -> EvaluationResult:
  # rubric scoring, schema check, evidence check
  return EvaluationResult(score=0.95, notes="Pass")
```

---

# 16. Trace-Level Observability and Auditability

## 16.1 Minimum Trace Fields

Every serious workflow should log:

* trace_id
* session_id
* user_id or tenant_id when applicable
* request_id
* task_id
* workflow_id
* step_id
* tool_call_id
* agent_name
* prompt_version
* model_name
* model_version if available
* latency
* cost
* result status

### HaruQuantAI Traceability Rule

Every HaruQuantAI agent run must include:

```text
request_id
workflow_id
```

Every HaruQuantAI tool call should accept and propagate `request_id` where possible.

The same identifiers should appear in:

- runtime logs
- tool responses
- agent responses
- audit records
- workflow handoffs
- final user-facing summaries

This allows a full chain to be reconstructed:

```text
User request -> CEO -> Planner -> Research -> Strategy -> Validation -> Risk -> Execution
```

## 16.2 Span Model

Each workflow step should be a span:

```text
Request Span
 ├─ Routing Span
 ├─ Planning Span
 ├─ Tool Call Span(s)
 ├─ Evaluation Span
 ├─ Approval Span
 └─ Final Response Span
```

## 16.3 Audit Logging

Audit logs should capture:

* who requested the action
* who approved it
* what policy applied
* what evidence was used
* what action was taken
* when it was taken
* whether compensation occurred

## 16.4 Redaction Rules

Never log secrets or unnecessary sensitive content.
Define:

* fields to redact
* fields to hash
* fields to omit
* retention period
* access controls

## 16.5 Logging Template

```python
def log_workflow_event(event: dict) -> None:
  # add trace_id, workflow_id, step_id, timestamp
  # redact sensitive fields
  # send to logging pipeline
  pass
```

---

# 17. Cost Governance and Model Strategy

## 17.1 Cost Governance Questions

For each workflow, define:

* which model tier is default
* when to use premium reasoning
* max cost per request
* max cost per workflow
* early exit rules
* caching policy
* downgrade behavior
* fallback model

## 17.2 Example Routing Policy

| Request Type | Default Model Tier | Escalation |
|---|---|---|
| Simple classification | low-cost fast model | never unless repeated failure |
| Structured extraction | mid-tier structured-output model | escalate if schema failures |
| Complex planning | premium reasoning model | approval if cost threshold exceeded |
| Multi-agent synthesis | premium or mixed routing | fallback if cost/latency exceeds budget |

## 17.3 Governance Rule

Cost should be a design constraint, not a dashboard afterthought.

## 17.4 Model Routing Template

```yaml
routing_policy:
 simple_classification: fast_model
 structured_extraction: reliable_json_model
 complex_planning: premium_reasoning_model
 fallback: lower_cost_model
 max_cost_per_workflow_usd: 0.25
```

---

# 18. Security Architecture and Prompt Injection Defense

## 18.1 Minimum Security Sections

Every system doc should state:

* identity model
* authn/authz boundaries
* secret management
* least privilege model
* network boundaries
* code execution restrictions
* sandboxing requirements
* retention and deletion rules

## 18.2 Prompt Injection Defense Rules

Treat as untrusted:

* user instructions that attempt policy override
* retrieved text from external docs
* web content
* tool outputs
* agent-to-agent freeform messages unless validated

## 18.3 Secure Handling Rules

* separate instructions from data
* validate all tool args
* restrict code execution tools
* use allowlists where possible
* log policy violations
* add security tests to CI

## 18.4 Security Review Template

```text
System:
Owner:
Sensitive capabilities:
External integrations:
Approval-gated actions:
Prompt injection exposure points:
Secrets used:
Sandboxing required:
Open risks:
Mitigations:
```

---

# 19. Testing Standard

| Test Type | Test Method |
|---|---|
| Unit Tests | tools, schemas, state transitions, helper clients, validation logic |
| Integration Tests | end-to-end workflows, capability-layer interaction, multi-agent handoffs, memory retrieval |
| Failure-Path Tests | timeouts, malformed outputs, unavailable server, stale context, invalid args |
| Evaluation Tests | rubric-based evaluation, benchmark datasets, golden tests |
| Contract Tests | agent ↔ workflow ↔ capability-layer schema compatibility |
| Security Tests | prompt injection, policy bypass, auth misuse, output poisoning |
| Compensation Tests | partial side effects, idempotent retries, rollback behavior |

## 19.1 Testing Rules

* write unit tests for every non-trivial tool wrapper
* write contract tests for every stable schema boundary
* write failure-path tests for every high-risk workflow
* write benchmark-backed evaluation tests for every critical prompt or agent
* write security tests for tool-heavy or retrieval-heavy workflows

## 19.1.1 HaruQuantAI Tool Test Requirements

Every function listed in a tool domain `__all__` must have unit tests.

Recommended structure:

```text
tests/unit/tools/{domain}/test_{source_file}.py
tests/usage/tools/{domain}/{source_file}.py
```

Each exported AI Tool must test:

- successful call
- invalid input
- empty result where applicable
- service/tool failure where applicable
- standard return schema compliance
- metadata correctness
- error code correctness
- logging footprint
- permission denial for high-risk tools

Every exported AI Tool must also have a real-world usage example that uses actual calls and avoids mocks where possible.

## 19.1.2 HaruQuantAI Agent Test Requirements

Every registered HaruQuantAI agent must have unit tests.

Recommended structure:

```text
tests/unit/agentic/agents/{department}/test_{agent_file}.py
tests/usage/agentic/agents/{department}/{agent_name}.py
tests/evals/agentic/{department}/test_{agent_name}_eval.py
```

Each agent must test:

- builder returns a Google ADK Agent
- agent name is correct
- description exists
- instruction exists
- instruction has required sections
- allowed tools are attached
- blocked tools are not attached
- metadata constants exist
- risk level is valid
- output contract is declared
- permissions are declared
- agent can be registered
- agent can run through runtime
- normalized response schema is returned
- logging footprint exists
- audit footprint exists where required

High-risk and critical agents must also test:

- approval is required
- live tools are blocked by default
- kill switch is respected
- policy gate cannot be bypassed
- fail-closed behavior works
```

## 19.2 Test Template

```python
def test_review_decision_schema():
  result = {
    "decision": "approve",
    "reason": "Within policy",
    "confidence": 0.91,
    "flags": [],
    "schema_version": "1.0.0"
  }
  assert result["decision"] in {"approve", "reject", "escalate"}
```

---

# 20. Recommended Project Structure

The canonical structure should support both a broad enterprise architecture and the current HaruQuantAI implementation style.

The Playbook remains framework-neutral, but HaruQuantAI currently follows a **Google ADK flat-first structure**.

## 20.1 HaruQuantAI ADK Flat-First Structure

Use this as the current HaruQuantAI default:

```text

    agentic/
        agents/
            executive.py
            research.py
            strategy.py
            validation.py
            risk_portfolio.py
            execution.py
            operations.py

        runtime.py
        workflows.py
        contracts.py
        policy.py
        audit.py
        registry.py

        config/
            agent_model.py

    tools/
        data/
            __init__.py
            market_data.py
            validators.py

        research/
            __init__.py

        strategy/
            __init__.py

        simulation/
            __init__.py

        optimization/
            __init__.py

        risk/
            __init__.py

        portfolio/
            __init__.py

        execution/
            __init__.py
            orders.py
            positions.py

        analytics/
            __init__.py

        governance/
            __init__.py

    tests/
        unit/
            agentic/
                agents/
                runtime/
                registry/
                policy/
                contracts/
                audit/

            tools/
                data/
                execution/
                risk/
                analytics/

        usage/
            agentic/
                agents/
            tools/

        evals/
            agentic/

        integration/
        security/
        failure/
```

## 20.2 HaruQuantAI Structure Rules

```text
Flat files first.
Folders only when earned.
Few agents, many tools.
Google ADK agents via builder functions.
Tools exposed through domain __init__.py.
Runtime owns execution normalization.
Registry owns agent discovery.
Policy owns deterministic gates.
Audit owns traceability.
Contracts own handoff structure.
```

Agents should be imported and run through the registry/runtime layer.

Tools should be imported from domain packages:

```python
from tools.data import get_market_data
from tools.execution import place_order
```

Avoid deep tool imports in agents:

```python
from tools.data.market_data import get_market_data
```

## 20.3 Agent File Placement Rule

Department files are the default:

```text
agentic/agents/research.py
agentic/agents/strategy.py
agentic/agents/execution.py
```

Each department file may contain multiple related builder functions:

```python
build_research_lead_agent()
build_market_intelligence_agent()
build_quant_research_agent()
```

Do not create one directory per agent unless the agent becomes large enough to justify it.

## 20.4 Tool Domain Placement Rule

Each folder inside `tools/` is a tool domain.

```text
tools/data/
tools/execution/
tools/risk/
tools/analytics/
```

Implementation lives in normal module files.

The domain `__init__.py` is the official public tool registry.

Only functions imported and listed in `__all__` are official AI Tools.

## 20.5 When to Split Later

A flat file may become a folder when one of these is true:

- the file becomes hard to navigate
- three or more closely related modules appear
- prompts become large enough to version separately
- tests and fixtures become large
- a real runtime or security boundary appears
- splitting removes repeated code
- ownership requires separation

Examples:

```text
agentic/policy.py
```

may later become:

```text
agentic/policy/
    permissions.py
    approvals.py
    risk_limits.py
    live_trading.py
```

```text
agentic/audit.py
```

may later become:

```text
agentic/audit/
    writer.py
    redaction.py
    storage.py
    readers.py
```

```text
agentic/workflows.py
```

may later become:

```text
agentic/workflows/
    research.py
    strategy.py
    validation.py
    risk.py
    execution.py
```

## 20.6 Enterprise Structure Option

Larger enterprise systems may still use a more expanded structure with local agent folders, YAML manifests, prompt files, capability providers, approval services, observability modules, and machine-readable registries.

That structure is appropriate when:

- many teams own different agents
- prompts need separate versioning and review
- manifests are consumed by CI/CD
- agents are deployed independently
- capability providers are remote services
- approval workflows are externalized
- audit evidence must be packaged separately

For HaruQuant’s current implementation, prefer the flat-first structure until complexity earns the split.

## 20.7 Test Placement Rule

For HaruQuantAI tools:

```text
tests/unit/tools/{domain}/test_{source_file}.py
tests/usage/tools/{domain}/{source_file}.py
```

For HaruQuantAI agents:

```text
tests/unit/agentic/agents/{department}/test_{agent_file}.py
tests/usage/agentic/agents/{department}/{agent_name}.py
tests/evals/agentic/{department}/test_{agent_name}_eval.py
```

For system-wide validation:

```text
tests/integration/
tests/security/
tests/failure/
tests/unit/agentic/contracts/
tests/unit/agentic/policy/
tests/unit/agentic/runtime/
tests/unit/agentic/registry/
tests/unit/agentic/audit/
```

## 20.8 Documentation Placement Rule

Recommended companion docs:

```text
docs/agents/Agent_Standard.md
docs/tools/AI_Tool_Function_Standard.md
docs/agents/Agent_Catalog.md
docs/tools/Tool_Catalog.md
docs/workflows/Workflow_Catalog.md
docs/governance/Policy_Map.md
docs/operations/Observability_Audit.md
docs/security/Security_Architecture.md
```

The Playbook remains the broad guide. The Agent Standard and Tool Function Standard are the concrete implementation standards.

---

# 21. Designing the System Before Coding

Follow this documentation sequence every time.

## Step 1: Define the user-facing host

Document:

* what app the user speaks to
* where orchestration lives
* where approvals happen
* where memory lives

## Step 2: Define system goals

Document:

* primary user goals
* business goals
* operational goals
* non-functional constraints

## Step 3: Define domains

Split the system into coherent capability domains.

Good examples:

* knowledge and document retrieval
* policy and governance
* external action execution
* research and analysis
* compliance and security

Bad example:

* one giant everything server

## Step 4: Define workflow types

For each user journey, specify:

* sequential
* routing
* parallel
* evaluator-optimizer
* orchestrator-workers

## Step 5: Classify capabilities

For every domain capability, classify it as:

* tool
* resource
* prompt

## Step 6: Define trust boundaries

Document:

* what is read-only
* what has side effects
* what requires approval
* what requires authentication
* what may execute external code or transactions

## Step 7: Choose transport

* stdio for local process workflows
* HTTP, RPC, streaming protocols, or managed services for remote deployable capabilities

## Step 8: Define session lifecycle

Document:

* initialize
* discover capabilities
* operate
* observe results
* shutdown or persist

## Step 9: Define approval and escalation model

Document:

* which actions are auto-approved
* which require human approval
* who can approve
* what evidence is required
* what times out
* what escalates
* what is blocked entirely

## Step 10: Define observability and audit model

Document:

* trace IDs
* session IDs
* task IDs
* tool-call IDs
* prompt versions
* model versions
* stored artifacts
* redaction rules

---

# 22. Implementation Phases

## Phase 0: Environment and Scaffold

Deliverables:

* repo initialized
* dependencies installed
* structure scaffolded
* secrets configured

Acceptance:

* imports resolve
* base agent loads
* settings validate

## Phase 1: Prompting and Reasoning Foundation

Deliverables:

* persona prompts/templates
* CoT/ReAct patterns
* creator/evaluator loop
* prompt versioning

Acceptance:

* prompt compliance tests pass
* structured output works consistently

## Phase 2: Workflow Orchestration

Deliverables:

* sequential workflows with schema gates
* router workflows with fallback
* parallel workflows with synthesis
* evaluator-optimizer loop with rubric scoring

Acceptance:

* workflows succeed end-to-end
* failures are bounded and logged

## Phase 3: Tooling, Memory, and State

Deliverables:

* capability wrappers
* tool adapters
* FSM state machine
* short-term and long-term memory
* agentic RAG flow

Acceptance:

* tools validate inputs
* state transitions logged
* retrieval quality meets threshold

## Phase 4: Multi-Agent Production Architecture

Deliverables:

* orchestration topology
* inter-agent contracts
* specialized retrievers
* evaluation metrics
* observability hooks
* shared session versioning

Acceptance:

* multi-agent coordination stable
* no stale-state corruption
* costs and latency measurable

## Phase 5: Deployment and Operations

Deliverables:

* service or CLI packaging
* containerization
* CI/CD
* monitoring and alerts
* rollback procedures

Acceptance:

* load testing passes
* alerts exist
* deployment reproducible

## Phase 6: Enterprise Hardening

Deliverables:

* policy enforcement map
* approval service
* compensation logic
* audit logging
* security review
* benchmark governance
* runbooks
* ADRs

Acceptance:

* high-risk actions gated
* audit trail complete
* compensation tested
* incident runbooks approved
* benchmark suite in place

---

# 23. Ownership, Operating Model, and Change Control

## 23.1 Every Major Component Needs an Owner

For each agent, workflow, server, and policy, define:

* product owner
* technical owner
* operational owner
* on-call owner

## 23.2 Change Control

For major changes, require:

* ADR
* benchmark results
* migration notes
* security review if relevant
* rollback plan
* owner sign-off

## 23.3 Decommissioning

Define when to retire:

* old prompts
* old models
* old workflows
* old servers
* deprecated schemas

## 23.4 Ownership Template

```yaml
component: policy_server
product_owner: platform_lead
technical_owner: backend_engineering_team
operational_owner: platform_operations
on_call_owner: system_oncall
```

---

# 24. Incident Response and Postmortems

## 24.1 Incident Classes

| Severity | Description |
|---|---|
| Sev 1 | harmful or critical action, severe outage, data/security risk |
| Sev 2 | material workflow failure, repeated bad outputs |
| Sev 3 | degraded behavior, local failures |
| Sev 4 | minor issue, non-critical defect |

## 24.2 Incident Response Checklist

* contain impact
* trigger kill switch if needed
* preserve logs and traces
* identify affected workflows
* compensate or correct side effects
* notify stakeholders
* patch and validate
* run postmortem

## 24.3 Postmortem Template

* summary
* impact
* timeline
* root cause
* contributing factors
* policy/control gaps
* what worked
* what failed
* corrective actions
* owner and due date

---

# 25. Architecture Decision Records (ADR) Standard

Use ADRs for major decisions such as:

* why a specific agent framework
* why a specific capability protocol or adapter layer
* why a workflow pattern
* why a model
* why local process, HTTP, RPC, or managed service integration
* why a server split by domain
* why a policy design

## 25.1 ADR Template

* title
* status
* date
* context
* decision
* consequences
* alternatives considered
* follow-up actions

---

# 26. Production Readiness Checklist and Anti-Patterns

The production checklist below is a quick readiness review. The Agent Auditing Checklist is the formal scoring and approval mechanism for individual agents. Use both: the Playbook checklist for design coverage and the Audit Checklist for evidence-based readiness.

## 26.1 Production Checklist

| Category | Requirement | Status |
|---|---|---|
| Prompting | role, CoT/ReAct, feedback loops versioned | ☐ |
| Outputs | Typed schema validation on important outputs | ☐ |
| State | session + FSM transitions logged & bounded | ☐ |
| Memory | short-term + long-term configured | ☐ |
| Tools/Capability Layer | wrappers with retries, timeouts, schema validation | ☐ |
| Routing | intent classifier + fallback | ☐ |
| Concurrency | bounded async parallelism | ☐ |
| Evaluation | response/step/trajectory metrics tracked | ☐ |
| Security | IAM, vaulted keys, sanitization, auth gates | ☐ |
| Approvals | approval packet + escalation model | ☐ |
| Compensation | partial-failure strategy tested | ☐ |
| Observability | trace-level logging + redaction | ☐ |
| Ownership | component owners assigned | ☐ |
| Runbooks | incident and ops runbooks exist | ☐ |

## 26.2 Common Pitfalls and Mitigations

| Pitfall | Symptom | Fix |
|---|---|---|
| Unbounded loops | runaway cost/retries | cap steps, define convergence threshold |
| Hallucinated tool calls | invalid params, failed executions | strict schema validation |
| Context overflow | degraded reasoning | sliding window, summarization |
| Tight coupling | brittle workflows | config-driven routing, dependency injection |
| No evaluation | unknown failure modes | evaluator + regression suite |
| Everything is a tool | poor capability design | classify tool/resource/prompt properly |
| God server | hard to scale/own | split by domain |
| stdout pollution | broken stdio protocol | log to `stderr` only |
| No compensation plan | unsafe partial failures | design rollback/compensation up front |
| Approval without evidence | unsafe human review | require approval packet |

---

# 27. Reference and Quick-Start

## 27.1 Learning / Capability Mapping

| Learning Area | Core Output | Framework-Neutral Equivalent |
|---|---|---|
| Prompting & Reasoning | CoT, ReAct, feedback loops | prompts, workflows, loops |
| Agentic Workflows | routing, parallel, eval-opt, orchestrator | workflows, router, evaluator |
| Building Agents | tools, structured I/O, state/memory | capability clients, session, adapters |
| Multi-Agent Systems | architecture, coordination, RAG | workers, shared state, synthesis |

## 27.2 Capstone Templates

| Template | Workflow Pattern | Focus |
|---|---|---|
| Travel Planner | routing + parallel + chaining | intent → research → synthesis |
| Project Manager | orchestrator-workers + eval-opt | planner delegates → workers → critic |
| Research Agent | agentic RAG + long-term memory | retrieve → reflect → synthesize |
| Sales Team | multi-agent state + routing + RAG | routing → CRM lookup → proposal |

## 27.3 Generic Agentic Architecture Template

```text
User
 ↓
Interface / API / UI
 ↓
Host / Router / Orchestrator
 ├─ Capability Client / Adapter → Knowledge Server
 ├─ Capability Client / Adapter → Policy Server
 ├─ Capability Client / Adapter → Action Server
 ├─ Capability Client / Adapter → Research Server
 └─ Internal Tools / Memory / DB / RAG
 ↓
Evaluation / Logging / Monitoring
```

---

# 28. Example Generic Domain Blueprint

This section shows how to split a generic agentic system into reusable capability domain providers. Adapt the names to your project domain.

## 28.1 Knowledge Capability Provider

Tools:

* `search_docs`
* `summarize_document`
* `extract_entities`

Resources:

* `docs://project/overview`
* `docs://catalog`

Prompts:

* `knowledge_summary_prompt`

## 28.2 Policy Capability Provider

Tools:

* `check_policy`
* `classify_action_risk`
* `validate_approval_requirements`

Resources:

* `policy://current`
* `policy://approval_matrix`

Prompts:

* `policy_review_prompt`
* `approval_packet_prompt`

## 28.3 Action Capability Provider

Tools:

* `create_ticket`
* `update_record`
* `send_notification`

Resources:

* `actions://available`
* `actions://recent_activity`

Prompts:

* `action_confirmation_prompt`

## 28.4 Research Capability Provider

Tools:

* `search_notes`
* `summarize_report`
* `compare_sources`

Resources:

* `research://project_docs`
* `research://reports`

Prompts:

* `research_summary_prompt`

## 28.5 Enterprise Overlays for These Capability Providers

For each domain capability provider, add:

* risk class
* policy owner
* approval class
* audit scope
* compensation options
* benchmark tasks
* on-call owner

---

# 29. Documentation Standard for Every New Agentic System

When creating system docs, include these sections in order:

1. purpose and scope
2. goals and non-goals
3. core reasoning loop
4. system architecture layers
5. host responsibilities
6. routing layer responsibilities
7. agent roles and interfaces
8. workflow patterns used
9. memory model
10. state model
11. context engineering standard
12. capability domain decomposition
13. tool/resource/prompt capability catalog
14. transport decisions
15. security and approval boundaries
16. policy enforcement map
17. failure recovery and compensation
18. evaluation framework
19. testing strategy
20. deployment architecture
21. operations and observability
22. ownership and change control
23. pitfalls and mitigations
24. acceptance criteria
25. future evolution notes

This becomes your documentation backbone.

---

# 30. Companion Documents Recommended for Enterprise Systems

For serious systems, split supporting artifacts into companion docs:

* `docs/specs/Requirements.md`
* `docs/architecture/System_Architecture.md`
* `docs/agents/Agent_Catalog.md`
* `docs/workflows/Workflow_Catalog.md`
* `docs/capabilities/Capability_Catalog.md`
* `docs/governance/Policy_Map.md`
* `docs/governance/Approval_Standard.md`
* `docs/operations/Observability_Audit.md`
* `docs/security/Security_Architecture.md`
* `docs/specs/Benchmark_Eval.md`
* `docs/runbooks/Operations_Runbook.md`
* `docs/adr/ADR_Index.md`

---

# 31. Final Condensed Rules

If you keep only one section, keep this one.

## Agentic AI essentials

* every workflow follows reason → plan → act → observe → evaluate → refine
* the host/orchestrator owns routing, planning, memory, state, policy checks, approvals, and final synthesis
* the capability layer handles standardized access to external capabilities
* clients/adapters connect
* providers/servers execute or return data
* tools do
* resources read
* prompts/templates guide
* start with the simplest local integration that works
* move remote or shared capabilities to HTTP, RPC, protocol servers, or managed services when needed
* keep capability providers domain-specific
* keep logs off stdout for stdio
* validate all important outputs
* evaluate every serious workflow
* design first, then code
* approvals must be explicit
* policies must be enforced in layers
* context must be engineered, not dumped
* side effects need compensation plans
* contracts must be versioned
* traces must be replayable and auditable
* security must assume untrusted inputs
* ownership must be explicit
* future versions should add and clarify, not silently subtract

## HaruQuantAI implementation essentials

* HaruQuantAI agents are built on Google ADK
* every HaruQuantAI agent is built through a standard builder function
* every HaruQuantAI agent declares metadata, permissions, allowed tools, blocked tools, risk level, approval requirement, and output contract
* every HaruQuantAI agent instruction includes Role, Responsibilities, Non-Goals, Allowed Tools, Blocked Actions, Required Evidence, Output Contract, Safety Rules, Uncertainty Behavior, and Escalation Rules
* every HaruQuantAI agent run uses request_id and workflow_id
* every important HaruQuantAI agent run emits logs and audit records
* every registered HaruQuantAI agent has unit tests and a usage example
* high-risk and critical agents have policy, approval, kill-switch, fail-closed, and evidence tests
* HaruQuantAI tools live under tools/{domain}/
* each tool domain __init__.py is the official public registry
* anything listed in a tool domain __all__ is an official AI Tool
* every official AI Tool follows the HaruQuantAI AI Tool Function Standard
* every official AI Tool has a standard return schema, metadata, logging footprint, error handling, unit tests, and usage examples
* policy and approval are deterministic, not prompt-only
* flat files first; folders only when earned

---

# 32. Final Note

This playbook is intentionally explicit.

It is meant to help:

* future-you design faster
* teams implement more consistently
* reviewers inspect system boundaries more clearly
* operators manage production more safely
* machine-assisted builders understand what must exist and how it should fit together

A good playbook is not only elegant.
It is usable, durable, and hard to misread.

---

*Built for production. Designed for scale. Explicit enough for future maintainers. Governed enough for enterprise use.*

# Agent Template

Status: canonical agent implementation template  
Scope: framework-neutral agent design, implementation, testing, logging, evaluation, registry, and audit alignment  
Use this when: creating, refactoring, reviewing, or onboarding any agent in an agentic AI system  
Companion docs: `docs/Agentic_AI_Playbook.md`, `docs/Agent_Auditing_Checklist.md`  
Owner: platform architecture / agent platform team  
Review cadence: quarterly or whenever the Playbook, Audit Checklist, registry schema, or canonical project structure changes materially

> **Purpose:** Standardize how every agent is built, tested, logged, evaluated, documented, registered, audited, and connected into a larger agentic system.
>
> **Primary rule:** An agent is not just a prompt. An agent is a bounded, testable, observable software component with explicit contracts, permissions, guardrails, evaluation checks, and audit evidence.
>
> **Framework stance:** This template is framework-neutral. It can be implemented with any agent runtime, workflow engine, model provider, tool protocol, or orchestration framework. Framework-specific adapters belong behind the agent runtime boundary.

---

# 1. Relationship to the Playbook and Audit Checklist

This template sits between the two foundation documents:

| Document | Role |
|---|---|
| `Agentic_AI_Playbook.md` | Defines how agentic systems should be designed, built, governed, operated, and evolved. |
| `Agent_Auditing_Checklist.md` | Defines how agents are verified, scored, approved, and promoted. |
| `Agent_Template.md` | Defines the standard implementation shape for one agent so it can satisfy the Playbook and pass the Audit Checklist. |

Use the three documents together:

```text
Playbook = design/build/operate standard
Agent Template = implementation standard for one agent
Audit Checklist = verification/scoring/approval standard
```

When the documents overlap:

```text
The Playbook defines the design standard.
The Agent Template defines the implementation pattern.
The Audit Checklist defines the evidence required to prove compliance.
```

---

# 2. Core Rule for Every Agent

Every agent must follow this execution pattern:

```text
Validate Input
→ Gather Evidence / Context
→ Plan or Select Action Path
→ Optional Model Reasoning
→ Deterministic Validation / Policy Check
→ Execute Approved Actions Only
→ Structured Output
→ Audit Log
→ Evaluation Check
```

For production or high-impact workflows, use the extended pattern from the Playbook:

```text
Reason → Plan → Policy Check → Act → Observe → Evaluate → Approve / Refine / Compensate / Finish
```

Model reasoning may assist with:

- analysis
- summarization
- classification
- explanation
- ranking
- extraction
- proposal generation
- drafting
- interpretation
- prioritization

Model reasoning must not be the only control for safety-critical, policy-critical, security-critical, high-impact, or irreversible decisions.

Use this rule:

```text
Model output = proposal or interpretation
Deterministic validation / policy = final authority for controlled decisions
```

For low-risk advisory agents, deterministic validation may simply enforce schema, evidence, permission, and output-quality rules. For high-impact agents, deterministic validation must include explicit policy gates, approval checks, idempotency rules, and safe-stop behavior.

---

# 3. Standard Agent Lifecycle

Every agent must declare its lifecycle stage:

```text
experimental → development → test → staging → production → deprecated
```

| Stage | Meaning |
|---|---|
| `experimental` | Early exploration, not relied on by workflows. |
| `development` | Built and tested locally, not production-capable. |
| `test` | Used in automated and integration test environments. |
| `staging` | Used in controlled pre-production workflows. |
| `production` | Approved for production workflows within its declared permissions. |
| `deprecated` | Retained only for migration, audit, or rollback context. |

Lifecycle stage is different from runtime environment:

```text
Lifecycle stage = agent maturity and authorization level
Runtime environment = where the agent is running
```

Standard runtime environments:

```text
local → development → test → staging → production
```

---

# 4. Execution Mode Standard

Every agent must declare one execution mode:

| Mode | Meaning |
|---|---|
| `deterministic` | Uses rules, code, schemas, and tools without model reasoning. |
| `llm` | Uses model reasoning as a core part of the output, with validation and guardrails. |
| `hybrid` | Combines deterministic code and model reasoning with explicit boundaries. |

For hybrid agents, document:

- which responsibilities are deterministic
- which responsibilities use model reasoning
- which decisions require deterministic validation
- what happens when model output is missing, invalid, low-confidence, or unsafe
- how the audit log records the path used

High-impact actions must be controlled by deterministic policy, approval rules, or external control gates. They must not depend only on freeform model judgment.

---

# 5. Architectural Position

Every agent should be built as an isolated, testable module first.

Recommended development flow:

```text
Define Agent Specification
→ Create Agent Folder
→ Write Manifest
→ Define Schemas
→ Implement Agent Logic
→ Add Prompt / Runtime Adapter if needed
→ Add Policy and Permission Checks
→ Add Logging and Audit Metadata
→ Add Evaluator
→ Add Unit Tests
→ Run Agent Standalone
→ Register Agent
→ Connect to Workflow
→ Run Integration and Contract Tests
→ Complete Audit Report
→ Promote Through Lifecycle Gates
```

No user-facing interface should call a specialist agent directly unless the architecture explicitly allows it. In most systems:

```text
User Interface / API
→ Host / Router / Orchestrator
→ Workflow
→ Specialist Agent
→ Evaluator / Reviewer
→ Final Response or Approved Action
```

Specialist agents should expose stable service interfaces and structured responses so orchestrators and workflows can consume them without knowing internal implementation details.

---

# 6. Canonical Project Structure Alignment

This template assumes the approved canonical structure:

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
│   │   ├── _shared/
│   │   └── <agent_name>/
│   │       ├── agent.py
│   │       ├── prompt.md
│   │       ├── manifest.yaml
│   │       ├── schemas.py
│   │       └── README.md
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
│   ├── checklist/
│   ├── reports/
│   └── evidence/
│
├── tests/
│   ├── agents/
│   ├── workflows/
│   ├── capabilities/
│   ├── integration/
│   ├── contracts/
│   ├── security/
│   ├── failure/
│   └── evaluation/
│
├── scripts/
└── .github/
    └── workflows/
```

## Canonical structure rule

```text
The canonical repository structure is agent-first and governance-aware.

Each agent owns its local implementation files:
- agent.py
- prompt.md
- manifest.yaml
- schemas.py
- README.md

Agent tests live in the root-level test suite:
- tests/agents/<agent_name>/

Shared infrastructure lives under shared folders:
- agentic/agents/_shared/
- agentic/workflows/_shared/
- agentic/capabilities/_shared/
- agentic/policy/
- agentic/evaluation/
- agentic/observability/
- agentic/security/

The registry/ folder is the machine-readable governance layer.
The audit/ folder is the human-readable and evidence-backed audit layer.
The docs/ folder is the architecture, operations, governance, and long-form documentation layer.
```

---

# 7. Standard Folder Structure for One Agent

Use this structure for every individual agent implementation:

```text
agentic/agents/<agent_name>/
├── agent.py
├── prompt.md
├── manifest.yaml
├── schemas.py
└── README.md
```

Use this matching root-level test structure for that agent:

```text
tests/agents/<agent_name>/
├── test_schemas.py
├── test_agent.py
├── test_policy.py
├── test_permissions.py
├── test_evaluator.py
└── test_smoke.py
```

For larger agents, use these optional files:

```text
agentic/agents/<agent_name>/
├── service.py              # stable public interface, if separate from agent.py
├── policy.py               # deterministic validation and policy checks
├── permissions.py          # allowed/forbidden actions and capability rules
├── evaluator.py            # agent-specific quality checks
├── tools.py                # agent-local tools, if not shared
├── resources.py            # agent-local read-only resources, if not shared
├── adapters.py             # runtime/framework/provider adapters, if needed
├── examples/
└── fixtures/
```

Minimum required files are intentionally small to keep agents easy to create. Optional files should be added when the agent becomes complex enough that separating responsibilities improves maintainability.

**Testing placement rule:** do not put test files inside `agentic/agents/<agent_name>/`. Keep implementation and verification separate: implementation lives under `agentic/`, while tests live under `tests/agents/<agent_name>/`.

---

# 8. Required Files for Each Agent

| File | Required | Responsibility |
|---|---:|---|
| `agent.py` | Yes | Implements or exposes the agent runtime boundary and main execution function/class. |
| `prompt.md` | Yes, if model reasoning is used | Stores versioned role instructions, constraints, output format, and safety rules. |
| `manifest.yaml` | Yes | Machine-readable contract for registry, workflow integration, audit, and CI quality gates. |
| `schemas.py` | Yes | Defines input, output, evidence, decision, artifact, and audit schemas. |
| `README.md` | Yes | Human-readable documentation for the agent. |
| `tests/agents/<agent_name>/` | Yes | Root-level agent tests proving schema, policy, permission, evaluator, and smoke behavior. |
| `service.py` | Optional | Stable public interface when the runtime wrapper should be separated from implementation. |
| `policy.py` | Optional but recommended | Deterministic policy, validation, approval, and safe-stop rules. |
| `permissions.py` | Optional but recommended | Capability-level allow/deny rules. |
| `evaluator.py` | Optional but recommended | Agent-specific quality and safety checks. |
| `tools.py` | Optional | Agent-local action capabilities. Prefer shared capabilities when reusable. |
| `resources.py` | Optional | Agent-local read-only resources. Prefer shared resources when reusable. |
| `adapters.py` | Optional | Framework, model provider, API, tool protocol, or runtime adapters. |

---

# 9. Shared Contracts

Shared contracts should live in:

```text
agentic/agents/_shared/
```

Recommended shared files:

```text
agentic/agents/_shared/
├── base_agent.py
├── agent_result.py
├── manifest_schema.py
├── guardrails.py
├── permissions.py
├── lifecycle.py
└── registry_loader.py
```

## Reference shared schema

```python
# agentic/agents/_shared/agent_result.py

from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    SUCCESS = "success"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"
    FAILED = "failed"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceItem(BaseModel):
    source: str
    description: str
    value: Any | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    timestamp: str | None = None
    freshness_status: Literal["fresh", "stale", "unknown"] = "unknown"


class AgentRequest(BaseModel):
    request_id: str
    user_id: str | None = None
    agent_name: str
    task: str
    payload: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    environment: Literal["local", "development", "test", "staging", "production"] = "development"


class AgentContext(BaseModel):
    session_id: str | None = None
    trace_id: str | None = None
    workflow_id: str | None = None
    workflow_state: dict[str, Any] = Field(default_factory=dict)
    memory_refs: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    environment: Literal["local", "development", "test", "staging", "production"] = "development"


class ModelAnalysis(BaseModel):
    summary: str
    observations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    raw_model_output_ref: str | None = None


class AgentDecision(BaseModel):
    status: AgentStatus
    decision: str
    confidence: ConfidenceLevel
    impact_level: ImpactLevel
    allowed_actions: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    control_gate_refs: list[str] = Field(default_factory=list)


class AgentAudit(BaseModel):
    agent_name: str
    agent_version: str
    manifest_version: str
    prompt_version: str | None = None
    policy_version: str | None = None
    execution_mode: Literal["deterministic", "llm", "hybrid"]
    model_provider: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    resources_used: list[str] = Field(default_factory=list)
    prompts_used: list[str] = Field(default_factory=list)
    permission_profile: str
    evidence_refs: list[str] = Field(default_factory=list)
    context_revision: str | None = None
    fallback_used: bool = False
    errors: list[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    request_id: str
    agent_name: str
    status: AgentStatus
    evidence: list[EvidenceItem] = Field(default_factory=list)
    model_analysis: ModelAnalysis | None = None
    decision: AgentDecision
    artifacts: dict[str, Any] = Field(default_factory=dict)
    audit: AgentAudit
```

Rules:

- Use typed schemas for anything crossing agent, workflow, tool, registry, or audit boundaries.
- Avoid unstructured dictionaries for public interfaces.
- Store large raw model outputs as artifact references when possible instead of embedding them directly.
- Do not log or return secrets.

---

# 10. Shared Base Agent Interface

```python
# agentic/agents/_shared/base_agent.py

from __future__ import annotations

from abc import ABC, abstractmethod

from .agent_result import (
    AgentRequest,
    AgentContext,
    AgentResponse,
    EvidenceItem,
    ModelAnalysis,
    AgentDecision,
)


class BaseAgentService(ABC):
    agent_name: str

    @abstractmethod
    async def run(
        self,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentResponse:
        """Run the agent and return a structured response."""
        raise NotImplementedError

    @abstractmethod
    async def gather_evidence(
        self,
        request: AgentRequest,
        context: AgentContext,
    ) -> list[EvidenceItem]:
        """Gather required evidence and context."""
        raise NotImplementedError

    @abstractmethod
    async def run_model_analysis(
        self,
        request: AgentRequest,
        context: AgentContext,
        evidence: list[EvidenceItem],
    ) -> ModelAnalysis | None:
        """Run optional model reasoning if the agent uses it."""
        raise NotImplementedError

    @abstractmethod
    def make_decision(
        self,
        request: AgentRequest,
        context: AgentContext,
        evidence: list[EvidenceItem],
        model_analysis: ModelAnalysis | None,
    ) -> AgentDecision:
        """Produce the final validated decision."""
        raise NotImplementedError
```

---

# 11. Agent-Specific Schemas

Every agent must define its own input and output details in `schemas.py`.

Example:

```python
# agentic/agents/document_review_agent/schemas.py

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentReviewPayload(BaseModel):
    document_id: str = Field(..., description="Document or artifact identifier")
    review_type: str = Field(default="quality", description="quality | policy | security | completeness")
    include_recommendations: bool = True


class DocumentReviewArtifact(BaseModel):
    document_id: str
    review_type: str
    summary: str
    issues: list[str] = []
    recommendations: list[str] = []
```

Rules:

- Required fields must be explicit.
- Optional fields must have safe defaults.
- Invalid or missing inputs must return structured errors or `needs_clarification`.
- Any field used for high-impact decisions must be validated before use.

---

# 12. Standard Prompt File

Use `prompt.md` for agents that use model reasoning.

Example:

```md
<!-- agentic/agents/document_review_agent/prompt.md -->

# Document Review Agent Prompt

Prompt version: document_review_agent_prompt_v1

## Role

You are a Document Review Agent.

## Task

Review the supplied document evidence for quality, completeness, policy alignment, and operational risk.

## Rules

- Use only the evidence provided or approved resources.
- Do not invent facts, citations, metrics, or results.
- Separate facts from assumptions and recommendations.
- Flag missing evidence clearly.
- Do not approve high-impact actions.
- Return analysis only; final decisions are made by deterministic validation or the workflow control gate.

## Output Format

Return structured analysis with:

- summary
- observations
- risks
- recommendations
- confidence
```

Prompt rules:

- Prompts must be versioned.
- Prompts must define role, task, constraints, forbidden actions, evidence requirements, and output format.
- Prompts must not contain hidden business logic that belongs in policy code.
- Prompts must be tested with positive and negative cases.
- Prompt instructions must align with the manifest.

---

# 13. Manifest Standard

Every agent must include `manifest.yaml`.

Example:

```yaml
agent_id: document_review_agent
name: Document Review Agent
version: 1.0.0
owner: platform_team
department: review
agent_type: specialist
lifecycle: development
execution_mode: hybrid

mission: Review documents and produce structured quality, policy, and completeness findings.

scope:
  - Review approved documents and artifacts.
  - Identify missing evidence, policy concerns, and quality gaps.
  - Produce structured review output for downstream workflows.

non_scope:
  - Approving production deployment.
  - Modifying source documents directly.
  - Performing irreversible actions.

responsibilities:
  - validate_review_request
  - gather_document_evidence
  - produce_review_analysis
  - apply_review_policy
  - return_structured_response

required_inputs:
  - document_id
  - review_type

output_fields:
  - status
  - evidence
  - model_analysis
  - decision
  - artifacts
  - audit

allowed_tools:
  - search_docs
  - validate_schema
  - check_policy

forbidden_tools:
  - deploy_to_production
  - modify_protected_config
  - delete_user_data

guardrails:
  - no_hallucinated_sources
  - schema_validation_required
  - high_impact_actions_blocked
  - stale_evidence_flag_required

approval_rules:
  high_impact_action_required: false
  human_approval_required: false
  production_action_allowed: false

handoff:
  upstream:
    - router
    - document_processing_workflow
  downstream:
    - reviewer_agent
    - approval_workflow

observability:
  log_inputs: true
  log_outputs: true
  log_tool_calls: true
  log_decisions: true
  redact_sensitive_fields: true

tests:
  - test_schemas.py
  - test_agent.py
  - test_policy.py
  - test_permissions.py
  - test_evaluator.py
  - test_smoke.py

supported_environments:
  - local
  - development
  - test
  - staging

documentation_paths:
  - agentic/agents/document_review_agent/README.md
  - docs/agents/document_review_agent.md

prompt_paths:
  - agentic/agents/document_review_agent/prompt.md

source_paths:
  - agentic/agents/document_review_agent/agent.py
  - agentic/agents/document_review_agent/schemas.py
```

Manifest rules:

- The manifest is the machine-readable contract for the registry, workflows, audit, and CI quality gates.
- It must match the implementation.
- It must not claim permissions the agent does not need.
- It must be updated whenever agent scope, tools, outputs, lifecycle, or approvals change.

---

# 14. Capability Access Standard

Capabilities should be classified as:

| Capability Type | Meaning | Examples |
|---|---|---|
| Tool | Performs an action or computation. | `validate_schema`, `create_ticket`, `send_notification` |
| Resource | Reads state or data. | `policy://access`, `docs://artifact/123`, `state://workflow/456` |
| Prompt | Reusable instruction template. | `review_prompt`, `approval_prompt`, `escalation_prompt` |
| Adapter | Integration boundary to an external system or runtime. | database adapter, file adapter, web adapter, model adapter |

Rules:

- Read-only resources should be separated from side-effecting tools.
- Side-effecting tools require permission checks.
- High-impact tools require approval or control gates.
- External integrations should be wrapped through adapters.
- Tool outputs must be validated and normalized into evidence.
- Never expose unrestricted tools to an agent.

Example agent-local capability declaration:

```python
# agentic/agents/document_review_agent/permissions.py

ALLOWED_TOOLS = [
    "search_docs",
    "validate_schema",
    "check_policy",
]

FORBIDDEN_TOOLS = [
    "deploy_to_production",
    "modify_protected_config",
    "delete_user_data",
]

PERMISSION_PROFILE = "document_review_read_only_v1"
```

---

# 15. Deterministic Policy and Validation Layer

For controlled decisions, each agent must include a deterministic validation or policy layer.

This layer may live in:

```text
agentic/agents/<agent_name>/policy.py
```

Example:

```python
# agentic/agents/document_review_agent/policy.py

from agentic.agents._shared.agent_result import (
    AgentDecision,
    AgentStatus,
    ConfidenceLevel,
    ImpactLevel,
    EvidenceItem,
    ModelAnalysis,
)


def make_decision(
    evidence: list[EvidenceItem],
    model_analysis: ModelAnalysis | None,
) -> AgentDecision:
    reasons: list[str] = []
    blocked_actions: list[str] = []
    allowed_actions: list[str] = ["return_review_summary"]

    if not evidence:
        return AgentDecision(
            status=AgentStatus.NEEDS_CLARIFICATION,
            decision="missing_required_evidence",
            confidence=ConfidenceLevel.LOW,
            impact_level=ImpactLevel.MEDIUM,
            allowed_actions=[],
            blocked_actions=["finalize_review"],
            reasons=["No evidence was provided for review."],
        )

    stale_sources = [item.source for item in evidence if item.freshness_status == "stale"]
    if stale_sources:
        blocked_actions.append("approve_output")
        reasons.append(f"Stale evidence detected: {stale_sources}")

    if model_analysis and "unsupported" in " ".join(model_analysis.risks).lower():
        blocked_actions.append("approve_output")
        reasons.append("Model analysis reported unsupported claims.")

    if not reasons:
        reasons.append("Review evidence passed baseline validation checks.")

    return AgentDecision(
        status=AgentStatus.SUCCESS,
        decision="document_review_completed",
        confidence=ConfidenceLevel.HIGH if not blocked_actions else ConfidenceLevel.MEDIUM,
        impact_level=ImpactLevel.LOW,
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        reasons=reasons,
        requires_approval=False,
    )
```

Policy rules:

- Never let raw model text become the final controlled decision.
- Model output can influence policy only through validated schema fields.
- Missing evidence must be handled explicitly.
- Stale evidence must be flagged or rejected according to task risk.
- Unsafe or forbidden actions must be blocked.
- Edge cases must be tested.
- The policy must produce a valid `AgentDecision` every time.

---

# 16. Agent Runtime Boundary

`agent.py` should expose the agent runtime boundary.

For simple agents, `agent.py` can include the full service class. For complex agents, keep `agent.py` small and delegate to `service.py`, `policy.py`, `evaluator.py`, and shared infrastructure.

Example:

```python
# agentic/agents/document_review_agent/agent.py

from __future__ import annotations

from uuid import uuid4

from agentic.agents._shared.agent_result import (
    AgentRequest,
    AgentContext,
    AgentResponse,
    AgentAudit,
    EvidenceItem,
    ModelAnalysis,
)
from .policy import make_decision


class DocumentReviewAgent:
    agent_name = "document_review_agent"
    agent_version = "1.0.0"
    manifest_version = "1.0.0"
    execution_mode = "hybrid"

    async def run(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        evidence = await self.gather_evidence(request, context)
        model_analysis = await self.run_model_analysis(request, context, evidence)
        decision = make_decision(evidence, model_analysis)

        return AgentResponse(
            request_id=request.request_id,
            agent_name=self.agent_name,
            status=decision.status,
            evidence=evidence,
            model_analysis=model_analysis,
            decision=decision,
            artifacts={},
            audit=AgentAudit(
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                manifest_version=self.manifest_version,
                prompt_version="document_review_agent_prompt_v1",
                policy_version="document_review_policy_v1",
                execution_mode=self.execution_mode,
                model_provider="configured_runtime",
                model_name="configured_model",
                tools_used=["search_docs", "validate_schema"],
                resources_used=[],
                prompts_used=["prompt.md"],
                permission_profile="document_review_read_only_v1",
                evidence_refs=[item.source for item in evidence],
                context_revision=context.trace_id or str(uuid4()),
                fallback_used=model_analysis is None,
            ),
        )

    async def gather_evidence(self, request: AgentRequest, context: AgentContext) -> list[EvidenceItem]:
        document_id = request.payload.get("document_id")
        if not document_id:
            return []

        return [
            EvidenceItem(
                source=f"document:{document_id}",
                description="Document content or metadata retrieved for review.",
                value={"document_id": document_id},
                freshness_status="unknown",
            )
        ]

    async def run_model_analysis(
        self,
        request: AgentRequest,
        context: AgentContext,
        evidence: list[EvidenceItem],
    ) -> ModelAnalysis | None:
        # Replace this with your framework/model adapter if the agent uses model reasoning.
        # Keep provider-specific logic behind a shared adapter where possible.
        if not evidence:
            return None

        return ModelAnalysis(
            summary="Draft review analysis produced by the configured model runtime.",
            observations=["Evidence was available for review."],
            risks=[],
            suggestions=["Proceed to deterministic validation."],
            raw_model_output_ref=None,
        )
```

Runtime rules:

- Keep provider-specific code behind adapters.
- Do not hardcode secrets or model credentials in agent files.
- Validate all model outputs before use.
- Record whether model reasoning was used.
- Provide fallback behavior when model reasoning is unavailable.

---

# 17. Standard Output Envelope

Every agent must return a structured response equivalent to:

```json
{
  "request_id": "req-123",
  "agent_name": "document_review_agent",
  "status": "success",
  "evidence": [],
  "model_analysis": {
    "summary": "...",
    "observations": [],
    "risks": [],
    "suggestions": []
  },
  "decision": {
    "status": "success",
    "decision": "document_review_completed",
    "confidence": "high",
    "impact_level": "low",
    "allowed_actions": [],
    "blocked_actions": [],
    "reasons": [],
    "requires_approval": false,
    "control_gate_refs": []
  },
  "artifacts": {},
  "audit": {
    "agent_name": "document_review_agent",
    "agent_version": "1.0.0",
    "manifest_version": "1.0.0",
    "prompt_version": "document_review_agent_prompt_v1",
    "policy_version": "document_review_policy_v1",
    "execution_mode": "hybrid",
    "model_provider": "configured_runtime",
    "model_name": "configured_model",
    "tools_used": ["search_docs"],
    "resources_used": [],
    "prompts_used": ["prompt.md"],
    "permission_profile": "document_review_read_only_v1",
    "evidence_refs": ["document:123"],
    "context_revision": "trace-123",
    "fallback_used": false,
    "errors": []
  }
}
```

Output rules:

- Output must be schema-validated.
- Output must distinguish evidence, model interpretation, deterministic decision, artifacts, and audit metadata.
- Output must preserve traceability through `request_id`, `trace_id`, `workflow_id`, or equivalent fields.
- Output must include errors when failed.
- Output must be consumable by workflows and downstream agents without guessing.

---

# 18. Standard Logging Requirements

Every agent run must log or emit structured trace fields:

```text
trace_id
request_id
workflow_id
agent_name
agent_version
lifecycle_stage
environment
start_time
end_time
input_validation_status
tools_called
resources_read
prompts_used
evidence_count
model_used
execution_mode
policy_version
decision
impact_level
allowed_actions
blocked_actions
requires_approval
error_if_any
context_revision
evidence_refs
permission_profile
fallback_used
```

Logging rules:

- Use structured logs.
- Redact secrets and sensitive fields.
- Do not log raw private data unless explicitly approved.
- Log tool calls and policy decisions.
- Log safe-stop and rejection reasons.
- Link logs to audit records.

---

# 19. Standard Audit Requirements

Every agent response must include machine-readable audit metadata.

Minimum audit fields:

```text
agent_name
agent_version
manifest_version
execution_mode
prompt_version, if model reasoning is used
policy_version, if policy validation is used
model_provider, if model reasoning is used
model_name, if model reasoning is used
tools_used
resources_used
prompts_used
permission_profile
evidence_refs
context_revision
fallback_used
errors
```

Audit rules:

- Audit metadata must be machine-readable.
- Audit metadata must not include secrets.
- Audit metadata must be sufficient to reproduce or explain the run.
- Audit metadata must show whether the decision came from deterministic code, model reasoning, or hybrid flow.
- Audit metadata must support the Audit Checklist evidence requirements.

---

# 20. Evaluator Standard

Each agent should define deterministic quality checks. These can live in:

```text
agentic/agents/<agent_name>/evaluator.py
```

Example:

```python
# agentic/agents/document_review_agent/evaluator.py

from agentic.agents._shared.agent_result import AgentResponse, AgentStatus


def evaluate_response(response: AgentResponse) -> dict:
    checks = {
        "has_request_id": bool(response.request_id),
        "has_agent_name": bool(response.agent_name),
        "status_valid": response.status in AgentStatus,
        "has_decision": bool(response.decision.decision),
        "has_reasons": bool(response.decision.reasons),
        "has_audit": bool(response.audit),
        "has_permission_profile": bool(response.audit.permission_profile),
        "has_execution_mode": bool(response.audit.execution_mode),
    }

    return {
        "passed": all(checks.values()),
        "checks": checks,
    }
```

Evaluation rules:

- Check response schema validity.
- Check permission compliance.
- Check that final decision exists.
- Check audit metadata.
- Check evidence quality where relevant.
- Check model-output boundaries for LLM or hybrid agents.
- Check rejection and safe-stop cases.
- Check high-impact approval behavior when relevant.

---

# 21. Standard README Template

Every agent must include `README.md`.

````md
# <Agent Name>

## Purpose

<What this agent is responsible for.>

## Lifecycle Stage

experimental | development | test | staging | production | deprecated

## Execution Mode

deterministic | llm | hybrid

## Owner

<Team or maintainer>

## Scope

- <In-scope responsibility 1>
- <In-scope responsibility 2>

## Non-Scope

- <Out-of-scope responsibility 1>
- <Forbidden responsibility 2>

## Inputs

| Field | Type | Required | Description |
|---|---|---:|---|
| artifact_id | str | Yes | Artifact to inspect. |

## Outputs

- evidence
- model analysis, if applicable
- decision
- artifacts
- audit metadata

## Allowed Capabilities

- <tool/resource/prompt 1>
- <tool/resource/prompt 2>

## Forbidden Capabilities

- <forbidden tool/action 1>
- <forbidden tool/action 2>

## Policy / Validation

Final controlled decisions are made by deterministic validation or an approved control gate.

## Tests

Run:

```bash
pytest tests/agents/<agent_name>/ -q
```

## Audit

Audit report path:

```text
audit/reports/<agent_name>_audit_report.md
```
````

---

# 22. Standard Permissions Model

Each agent must declare what it can and cannot do.

Example:

```python
# agentic/agents/document_review_agent/permissions.py

AGENT_PERMISSIONS = {
    "can_read_documents": True,
    "can_search_approved_sources": True,
    "can_generate_recommendations": True,
    "can_modify_source_artifacts": False,
    "can_modify_protected_config": False,
    "can_execute_production_action": False,
    "can_approve_high_impact_action": False,
    "can_delete_data": False,
}
```

Generic permission law:

```text
Agents should have least-privilege access.
Read-only agents must not mutate state.
Advisory agents must not perform controlled actions.
High-impact actions require approval or control gates.
No agent may bypass policy, security, or governance controls.
```

---

# 23. Callback / Hook Strategy

Agent runtimes should expose hooks around key lifecycle points. These hooks can be implemented by your framework, middleware, decorators, workflow engine, or custom runtime.

Use hooks around:

```text
Before agent:
- assign trace_id
- validate request
- check environment
- log input reference

Before model:
- redact secrets
- check prompt policy
- inject system constraints
- enforce context limits

After model:
- save output reference
- validate schema
- detect unsupported claims
- detect hallucinated tool references

Before capability call:
- check permission
- check approval requirements
- check rate limits
- check idempotency key if side-effecting

After capability call:
- log result reference
- normalize result into evidence
- validate output schema

After agent:
- write audit metadata
- run evaluator
- emit metrics
- trigger escalation if needed
```

Hooks are guardrails and observability points. They should not hide important business logic that belongs in explicit policy or workflow code.

---

# 24. Standard Test Requirements

Every agent should have these tests in the root-level test suite:

```text
tests/agents/<agent_name>/
├── test_schemas.py
├── test_agent.py
├── test_policy.py
├── test_permissions.py
├── test_evaluator.py
└── test_smoke.py
```

The agent folder contains the implementation; the root `tests/` folder contains verification. This keeps the repository consistent with the Playbook and Audit Checklist while still making the test ownership clear through the matching `<agent_name>` path.

## `test_schemas.py`

Validate:

- valid request schema
- valid response schema
- invalid payload rejection
- missing required fields
- JSON serialization

## `test_agent.py`

Validate:

- `run()` returns a structured response
- evidence is gathered or missing evidence is handled
- decision exists
- errors are structured
- audit metadata exists

## `test_policy.py`

Validate:

- normal case
- missing evidence case
- stale evidence case
- high-impact blocked case
- model output cannot override deterministic rules

## `test_permissions.py`

Validate:

- allowed tools are permitted
- forbidden tools are blocked
- production actions are blocked unless explicitly authorized
- high-impact tools require approval or control gates

## `test_evaluator.py`

Validate:

- evaluator catches missing decision
- evaluator catches missing audit metadata
- evaluator catches schema or permission failures

## `test_smoke.py`

Validate:

- agent can be constructed
- agent can process a minimal valid request
- agent does not crash in the supported local/test environment

Cross-agent and system-level tests also belong in root-level `tests/`:

```text
tests/integration/
tests/contracts/
tests/security/
tests/failure/
tests/evaluation/
```

---

# 25. Standard Agent Runner Script

Every agent should support a local runner for development and debugging.

Example:

```python
# scripts/run_document_review_agent.py

import asyncio
from uuid import uuid4

from agentic.agents._shared.agent_result import AgentRequest, AgentContext
from agentic.agents.document_review_agent.agent import DocumentReviewAgent


async def main() -> None:
    agent = DocumentReviewAgent()

    request = AgentRequest(
        request_id=str(uuid4()),
        agent_name="document_review_agent",
        task="Review this document for quality and policy issues.",
        payload={"document_id": "doc-123", "review_type": "quality"},
        environment="local",
    )

    context = AgentContext(
        session_id="local_test_session",
        trace_id=str(uuid4()),
        environment="local",
    )

    response = await agent.run(request, context)
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

---

# 26. Coding Agent Implementation Prompt

Use this prompt whenever asking a coding agent to create one agent.

```text
You are implementing one agent for a framework-neutral agentic AI system.

Follow these foundation documents:
- docs/Agentic_AI_Playbook.md
- docs/Agent_Auditing_Checklist.md
- docs/Agent_Template.md

Agent name:
<AGENT_NAME>

Owner / department:
<OWNER_OR_DEPARTMENT>

Purpose:
<PURPOSE>

Lifecycle stage:
experimental | development | test | staging | production | deprecated

Execution mode:
deterministic | llm | hybrid

Required inputs:
<INPUTS>

Allowed capabilities:
<TOOLS_RESOURCES_PROMPTS>

Forbidden capabilities:
<FORBIDDEN_CAPABILITIES>

Allowed actions:
<ALLOWED_ACTIONS>

Forbidden actions:
<FORBIDDEN_ACTIONS>

Deterministic validation / policy rules:
<POLICY_RULES>

Required folder:
agentic/agents/<agent_name>/

Required files:
- agent.py
- prompt.md, if model reasoning is used
- manifest.yaml
- schemas.py
- README.md

Required tests folder:
tests/agents/<agent_name>/

Required test files:
- test_schemas.py
- test_agent.py
- test_policy.py
- test_permissions.py
- test_evaluator.py
- test_smoke.py

Hard rules:
1. Keep the agent framework-neutral behind an adapter boundary.
2. Use structured schemas for all inputs and outputs.
3. Do not invent tools, resources, data, citations, metrics, or results.
4. Do not allow raw model text to become a final controlled decision.
5. Enforce least-privilege capability access.
6. Block forbidden capabilities.
7. Add logging and audit metadata.
8. Add tests for normal, edge, rejected, permission-denied, and missing-evidence cases.
9. Record execution mode, prompt version, policy version, and tool/resource use in audit metadata.
10. Keep the public run interface stable: run(request, context) -> AgentResponse.
11. Register the agent using manifest.yaml and registry/agents/<agent_name>.yaml.
12. Do not connect the agent to production workflows until audit, tests, registry quality gate, and approvals pass.

Return the implementation file by file.
```

---

# 27. Per-Agent Specification Template

Before implementing any agent, fill this out.

```md
# <Agent Name> Specification

## Purpose

<What this agent is responsible for.>

## Owner

<Team or maintainer.>

## Lifecycle Stage

experimental | development | test | staging | production | deprecated

## Execution Mode

deterministic | llm | hybrid

## Scope

- <In-scope responsibility 1>
- <In-scope responsibility 2>

## Non-Goals

- <Out-of-scope responsibility 1>
- <Forbidden responsibility 2>

## Inputs

| Field | Type | Required | Description |
|---|---|---:|---|
| artifact_id | str | Yes | Artifact to inspect. |

## Outputs

| Field | Type | Description |
|---|---|---|
| decision | str | Final validated decision or result. |
| evidence | list | Evidence used. |
| audit | object | Audit metadata. |

## Capabilities

| Capability | Type | Purpose | Permission Level |
|---|---|---|---|
| search_docs | tool | Search approved documents | read-only |
| policy://access | resource | Read access policy | read-only |

## Evidence Required

- <Evidence item 1>
- <Evidence item 2>

## Model Responsibilities

- <Allowed model responsibility 1>
- <Allowed model responsibility 2>

## Deterministic Validation / Policy Rules

- Rule 1:
- Rule 2:
- Rule 3:

## Allowed Actions

- <Allowed action 1>
- <Allowed action 2>

## Blocked Actions

- <Blocked action 1>
- <Blocked action 2>

## Approval Requirements

- <Human approval requirement, if any>
- <Control gate requirement, if any>

## Output Artifacts

- <Artifact 1>
- <Artifact 2>

## Tests Required

- Normal case
- Missing evidence case
- Stale evidence case
- Permission-denied case
- High-impact blocked case
- Model override attempt
```

---

# 28. Agent Category Guidelines

Use categories as reusable patterns, not fixed departments.

## Planning / Orchestration Agents

Primary responsibility:

```text
Classify intent, plan work, route tasks, coordinate agents, and manage workflow state.
```

Hard restrictions:

```text
Do not perform high-impact actions directly.
Do not bypass approval gates.
Do not hide unresolved conflicts between specialist agents.
```

## Research / Retrieval Agents

Primary responsibility:

```text
Retrieve, summarize, and organize evidence from approved sources.
```

Hard restrictions:

```text
Do not invent sources.
Do not treat stale evidence as current truth.
Do not perform write or production actions unless explicitly authorized.
```

## Data / Analysis Agents

Primary responsibility:

```text
Analyze structured or unstructured data and produce validated findings.
```

Hard restrictions:

```text
Do not ignore data quality problems.
Do not fabricate metrics.
Do not use unsupported assumptions as facts.
```

## Code Generation Agents

Primary responsibility:

```text
Generate, modify, explain, or review code under project standards.
```

Hard restrictions:

```text
Do not bypass tests, security rules, or review gates.
Do not modify protected files without approval.
Do not execute unsafe code outside a sandbox.
```

## Reviewer / Evaluator Agents

Primary responsibility:

```text
Evaluate outputs, detect defects, check policy compliance, and recommend approve/reject/revise outcomes.
```

Hard restrictions:

```text
Do not self-approve work that requires independent review.
Do not silently ignore missing evidence.
Do not hide contradictory findings.
```

## Action / Execution Agents

Primary responsibility:

```text
Perform approved side-effecting actions through controlled services.
```

Hard restrictions:

```text
Do not execute without permission.
Do not bypass policy or approval gates.
Do not perform irreversible actions without idempotency, audit, and rollback/compensation design.
```

## Monitoring / Incident Agents

Primary responsibility:

```text
Monitor system behavior, detect anomalies, create incidents, and support recovery workflows.
```

Hard restrictions:

```text
Do not suppress severe alerts.
Do not delete evidence.
Do not close incidents without required review.
```

---

# 29. Recommended Build Order

Use this generic build order for a new agentic system:

```text
1. Create docs/Agentic_AI_Playbook.md and docs/Agent_Auditing_Checklist.md.
2. Create docs/Agent_Template.md.
3. Create canonical repository structure.
4. Create shared schemas and base agent interfaces.
5. Create manifest schema and registry loader.
6. Create logging, tracing, redaction, and audit helpers.
7. Create policy, permission, and approval helpers.
8. Create the first simple deterministic agent.
9. Add local agent tests.
10. Add the first workflow.
11. Add workflow and contract tests.
12. Add registry quality gate.
13. Add CI quality gate.
14. Add evaluator and benchmark tests.
15. Add security and failure-path tests.
16. Complete the first audit report.
17. Promote agent through lifecycle stages.
18. Repeat for additional agents.
```

---

# 30. Definition of Done for Every Agent

An agent is complete only when:

```text
1. It follows the standard agent folder structure.
2. It has a valid manifest.yaml.
3. It has typed input/output schemas.
4. It declares execution mode: deterministic, llm, or hybrid.
5. It has clearly scoped capabilities.
6. It has allowed and forbidden actions.
7. It has deterministic validation or policy checks where needed.
8. It returns the standard AgentResponse envelope.
9. It includes audit metadata.
10. It has structured logging.
11. It has evaluator checks.
12. It has local unit tests.
13. It can run alone without the full multi-agent system.
14. It is registered in registry/agents/.
15. It has a README.
16. It has an audit report when moving beyond development.
17. It passes registry quality gates and CI before staging or production use.
```

High-impact or production-capable agents must also have:

```text
1. Human approval rules where required.
2. Control gate compliance.
3. Environment awareness.
4. Idempotency and duplicate protection for side effects.
5. Rollback or compensation plan where relevant.
6. Incident escalation path.
7. Security review where relevant.
8. Production monitoring.
9. Kill switch or safe-stop integration where relevant.
10. Governance approval before production use.
```

---

# 31. Alignment Checklist Before Audit

Before starting the formal audit, confirm:

| Check | Status |
|---|---|
| Agent folder is under `agentic/agents/<agent_name>/`. | ☐ |
| Required files exist. | ☐ |
| Manifest exists and matches implementation. | ☐ |
| Input and output schemas are typed. | ☐ |
| Execution mode is declared. | ☐ |
| Prompt is versioned if model reasoning is used. | ☐ |
| Allowed and forbidden capabilities are declared. | ☐ |
| Evidence requirements are defined. | ☐ |
| Policy and approval rules are defined. | ☐ |
| Audit metadata is emitted. | ☐ |
| Tests exist and pass. | ☐ |
| README is complete. | ☐ |
| Registry entry exists. | ☐ |
| Audit report path is known. | ☐ |

---

# 32. Final Architecture Rule

The most important architectural decision is this:

```text
Each agent is not just an LLM prompt.
Each agent is a bounded software component with contracts, permissions, guardrails, tests, logs, evaluation, and audit evidence.
```

That is what makes a multi-agent system reusable, debuggable, governable, and safe to expand.

---

# 33. References

Primary companion documents:

```text
docs/Agentic_AI_Playbook.md
docs/Agent_Auditing_Checklist.md
docs/Agent_Template.md
```

Recommended supporting documents:

```text
docs/architecture/System_Architecture.md
docs/agents/Agent_Catalog.md
docs/workflows/Workflow_Catalog.md
docs/capabilities/Capability_Catalog.md
docs/governance/Policy_Map.md
docs/governance/Approval_Standard.md
docs/operations/Production_Readiness.md
docs/security/Security_Architecture.md
```

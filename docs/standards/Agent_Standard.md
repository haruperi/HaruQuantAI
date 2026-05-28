# HaruQuant Agent Standard

## Status

Production-ready draft
Target runtime: Google ADK
Architecture style: flat-first, tool-heavy, policy-gated, audit-aware, contract-driven
Primary goal: define a standard for creating, auditing, testing, registering, and running HaruQuant agents safely and consistently.

---

## 1. Purpose

This document defines the HaruQuant Agent Standard.

It applies to all AI agents built on top of Google ADK inside the HaruQuant Agentic AI framework.

The purpose of this standard is to make every agent:

- easy to understand
- easy to audit
- easy to test
- safe to run
- clear in responsibility
- explicit in permissions
- traceable in logs and audit records
- compatible with HaruQuant tools, workflows, policies, and contracts

This standard is designed to match the discipline of the HaruQuant AI Tool Function Standard.

---

## 2. Core Principle

HaruQuant should be built with:

```text
Few agents.
Many tools.
Strict contracts.
Deterministic gates.
Simple files first.
Audit everything important.
```

An agent should exist only when it owns a decision, interpretation, delegation, review, or approval recommendation.

If something only fetches data, calculates metrics, validates schemas, writes logs, stores files, runs a backtest, optimizes parameters, calls a broker API, or formats a report, it should usually be a tool or deterministic service, not an agent.

---

## 3. Agent Definition

An Agent is an LLM-powered decision unit that:

- receives a user request or workflow handoff
- interprets the request
- uses approved tools where necessary
- reasons over evidence
- produces a structured response, decision, or handoff package
- operates under explicit permissions and policy gates
- leaves a logging and audit footprint

A function, service, utility, validator, data fetcher, broker bridge, or metrics calculator is not an agent unless it performs LLM-powered interpretation or decision-making.

---

## 4. Agent vs Tool Rule

Use this rule:

```text
If it decides, interprets, reviews, plans, delegates, or recommends, it can be an agent.

If it fetches, calculates, validates, stores, executes, transforms, or formats, it should be a tool or service.
```

### Examples of Agents

```text
CEO Agent
Planner Agent
Research Lead Agent
Strategy Designer Agent
Backtest Analyst Agent
Risk Governor Agent
Execution Readiness Agent
Live Execution Agent
Governance Agent
```

### Examples of Tools

```text
get_market_data
validate_ohlcv_quality
read_forexfactory_calendar
calculate_sharpe_ratio
run_backtest
run_monte_carlo_test
validate_strategy_spec
write_audit_record
place_order
close_position
```

Agents call tools.

Tools do not become agents.

---

## 5. Target Folder Structure

Use the flat-first structure:

```text
haruquant/
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
        research/
        strategy/
        simulation/
        optimization/
        risk/
        portfolio/
        execution/
        analytics/
        governance/
```

Do not create one folder per agent by default.

Avoid this early:

```text
agentic/agents/research/research_lead_agent/
    agent.py
    prompts/
    schemas/
    tests/
    evaluator.py
    permissions.py
```

Only split into folders when the file becomes too large or repeated complexity appears.

---

## 6. When to Split Later

Start with flat files.

Split a file into a folder only when at least one of these is true:

- the file becomes hard to navigate
- there are three or more closely related modules
- tests and fixtures become large
- prompts become large enough to version separately
- the split removes repeated code
- the split creates a real runtime, ownership, or security boundary

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

Folders should be earned, not created upfront.

---

## 7. Agent Department Model

The logical model is:

```text
Executive
    ceo_agent
    planner_agent

Research
    research_lead_agent
    market_intelligence_agent
    quant_research_agent
    research_validator_agent

Strategy
    strategy_lead_agent
    strategy_designer_agent
    strategy_engineer_agent
    strategy_reviewer_agent
    strategy_librarian_agent

Validation
    simulation_lead_agent
    backtest_analyst_agent
    optimization_agent
    robustness_validator_agent
    evidence_packager_agent

Risk & Portfolio
    risk_lead_agent
    risk_governor_agent
    portfolio_manager_agent
    allocation_agent
    risk_auditor_agent

Execution
    execution_lead_agent
    execution_readiness_agent
    paper_trading_agent
    live_execution_agent
    kill_switch_agent

Operations
    governance_agent
    audit_agent
    performance_reporter_agent
    cost_efficiency_agent
```

This is a logical model, not a requirement to create one folder per agent.

Implementation should remain:

```text
agentic/agents/executive.py
agentic/agents/research.py
agentic/agents/strategy.py
agentic/agents/validation.py
agentic/agents/risk_portfolio.py
agentic/agents/execution.py
agentic/agents/operations.py
```

---

## 8. Agent File-Level Docstring Rule

Every agent file must start with a file-level docstring.

The file-level docstring must include:

- file purpose
- agents defined in the file
- builder functions exposed
- allowed tool domains
- output contracts
- risk level range
- important safety notes

Example:

```python
"""
research.py

Defines Research Department agents for HaruQuant.

Agents:
    - research_lead: Coordinates market research and produces ResearchEvidencePack.
    - market_intelligence: Reviews news, calendar, and sentiment context.
    - quant_research: Interprets quantitative research evidence.
    - research_validator: Checks research completeness and evidence quality.

Builder Functions:
    - build_research_lead_agent
    - build_market_intelligence_agent
    - build_quant_research_agent
    - build_research_validator_agent

Allowed Tool Domains:
    - haruquant.tools.data
    - haruquant.tools.research
    - haruquant.tools.analytics

Output Contracts:
    - ResearchEvidencePack

Risk Level:
    low to medium

Safety:
    Research agents may analyze and recommend, but must not place trades,
    approve live trading, or invent backtest results.
"""
```

---

## 9. Logging Import Rule

Every agent file must import and configure a module logger.

```python
import logging

logger = logging.getLogger(__name__)
```

Every agent builder must log when the agent is built.

Every agent run must be logged by the runtime layer.

Do not log secrets, passwords, broker tokens, API keys, or full private credentials.

---

## 10. Agent Metadata Rule

Every agent must define metadata constants.

Required metadata:

```python
AGENT_NAME = "research_lead"
AGENT_VERSION = "1.0.0"
AGENT_DEPARTMENT = "research"
AGENT_DESCRIPTION = "Coordinates research and produces evidence packs."
AGENT_RISK_LEVEL = "medium"
AGENT_REQUIRES_APPROVAL = False
AGENT_INPUT_CONTRACT = "AgentRequest"
AGENT_OUTPUT_CONTRACT = "ResearchEvidencePack"
```

Valid risk levels:

```text
low       = read-only analysis, no state mutation
medium    = creates specs, reports, or runs expensive workflows
high      = recommends risk, allocation, or execution decisions
critical  = requests or coordinates live broker/account actions
```

---

## 11. Agent Permission Declaration Rule

Every agent must declare its permissions.

Example:

```python
CAN_READ_MARKET_DATA = True
CAN_READ_RESEARCH_DATA = True
CAN_CREATE_STRATEGY_SPEC = False
CAN_MODIFY_STRATEGY_CODE = False
CAN_RUN_BACKTEST = False
CAN_RUN_OPTIMIZATION = False
CAN_WRITE_FILES = False
CAN_MODIFY_DATABASE = False
CAN_REVIEW_RISK = False
CAN_APPROVE_RISK = False
CAN_REQUEST_PAPER_TRADING = False
CAN_REQUEST_LIVE_TRADING = False
CAN_PLACE_TRADES = False
CAN_CLOSE_TRADES = False
CAN_ACTIVATE_KILL_SWITCH = False
CAN_OVERRIDE_KILL_SWITCH = False
```

The permissions must match the agent's real scope.

Permissions must be checked deterministically by policy code.

An LLM instruction is not a security boundary.

---

## 12. Allowed Tools and Blocked Tools Rule

Every agent must declare its allowed tools.

Example:

```python
from haruquant.tools.data import get_market_data
from haruquant.tools.research import get_market_context
from haruquant.tools.analytics import calculate_basic_market_stats


ALLOWED_TOOLS = [
    get_market_data,
    get_market_context,
    calculate_basic_market_stats,
]

BLOCKED_TOOL_NAMES = [
    "place_order",
    "close_position",
    "activate_live_trading",
    "disable_risk_controls",
]
```

The policy layer must validate that:

- every attached tool is allowed
- no blocked tool is attached
- high-risk tools require approval
- critical tools fail closed by default
- agent permissions match tool side effects

Agents should import tools from domain packages.

Correct:

```python
from haruquant.tools.data import get_market_data
```

Avoid:

```python
from haruquant.tools.data.market_data import get_market_data
```

---

## 13. Agent Instruction Standard

Every agent instruction must contain the following sections:

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

### Minimum Instruction Template

```python
RESEARCH_LEAD_INSTRUCTION = """
# Role

You are the HaruQuant Research Lead Agent.

# Responsibilities

- Understand research requests.
- Gather evidence using approved tools.
- Summarize market context.
- Produce a ResearchEvidencePack.
- Clearly separate evidence, assumptions, and interpretation.

# Non-Goals

- Do not place trades.
- Do not approve risk.
- Do not claim a strategy is profitable without backtest evidence.
- Do not invent data.

# Allowed Tools

Use only the tools attached to this agent.

# Blocked Actions

- Live trading
- Broker execution
- Risk approval
- Kill-switch override

# Required Evidence

Every research conclusion must cite tool results, user-provided context,
or clearly marked assumptions.

# Output Contract

Return a ResearchEvidencePack-compatible response.

# Safety Rules

If evidence is missing, say so.
If data is stale, say so.
If a request requires risk or execution approval, escalate.

# Uncertainty Behavior

When uncertain, ask for clarification or return a clear uncertainty note.

# Escalation Rules

Escalate strategy creation to Strategy agents.
Escalate risk decisions to Risk agents.
Escalate execution decisions to Execution agents.
"""
```

Instructions may start as Python strings.

Move instructions to Markdown files when:

- instruction exceeds 80 to 120 lines
- multiple agents share instruction sections
- non-developers need to edit prompts
- prompt versioning becomes important
- evaluation depends on prompt variants

---

## 14. Agent Builder Function Standard

Each agent must be created through a builder function.

Builder functions must:

- have a clear name
- return a Google ADK `Agent`
- use metadata constants
- use explicit instructions
- use explicit allowed tools
- log construction
- not perform runtime work
- not call tools during construction
- not mutate external state

Example:

```python
from __future__ import annotations

import logging

from google.adk.agents import Agent

from haruquant.agentic.config.agent_model import AGENT_MODEL
from haruquant.tools.data import get_market_data
from haruquant.tools.research import get_market_context


logger = logging.getLogger(__name__)


AGENT_NAME = "research_lead"
AGENT_VERSION = "1.0.0"
AGENT_DEPARTMENT = "research"
AGENT_DESCRIPTION = "Coordinates market research and produces evidence packs."
AGENT_RISK_LEVEL = "medium"
AGENT_REQUIRES_APPROVAL = False
AGENT_INPUT_CONTRACT = "AgentRequest"
AGENT_OUTPUT_CONTRACT = "ResearchEvidencePack"


CAN_READ_MARKET_DATA = True
CAN_CREATE_STRATEGY_SPEC = False
CAN_RUN_BACKTEST = False
CAN_PLACE_TRADES = False
CAN_CLOSE_TRADES = False
CAN_REQUEST_LIVE_TRADING = False


ALLOWED_TOOLS = [
    get_market_data,
    get_market_context,
]

BLOCKED_TOOL_NAMES = [
    "place_order",
    "close_position",
    "activate_live_trading",
]


RESEARCH_LEAD_INSTRUCTION = """
# Role

You are the HaruQuant Research Lead Agent.

# Responsibilities

- Coordinate research workflows.
- Use approved tools to gather evidence.
- Produce a ResearchEvidencePack.

# Non-Goals

- Do not place trades.
- Do not approve risk.
- Do not invent data.

# Allowed Tools

Use only the tools attached to this agent.

# Blocked Actions

- Live trading
- Risk approval
- Broker execution

# Required Evidence

Every conclusion must be based on tool results, user context, or clearly marked assumptions.

# Output Contract

Return a ResearchEvidencePack-compatible response.

# Safety Rules

Disclose missing, stale, or conflicting evidence.

# Uncertainty Behavior

Ask for clarification when the request cannot be safely completed.

# Escalation Rules

Escalate strategy design to Strategy agents.
Escalate risk decisions to Risk agents.
Escalate execution requests to Execution agents.
"""


def build_research_lead_agent() -> Agent:
    """
    Builds the Research Lead Agent.

    The Research Lead Agent coordinates research tasks, calls approved
    market data and research tools, and returns a structured research
    evidence pack.

    Returns:
        Agent: Configured Google ADK Agent instance.
    """

    logger.info(
        "Building agent | agent_name=%s | version=%s | department=%s | risk_level=%s",
        AGENT_NAME,
        AGENT_VERSION,
        AGENT_DEPARTMENT,
        AGENT_RISK_LEVEL,
    )

    return Agent(
        name=AGENT_NAME,
        model=AGENT_MODEL,
        description=AGENT_DESCRIPTION,
        instruction=RESEARCH_LEAD_INSTRUCTION,
        tools=ALLOWED_TOOLS,
    )
```

---

## 15. Agent Builder Docstring Rule

Every builder function must have a docstring that explains:

- which agent it builds
- what the agent is responsible for
- what the agent is not allowed to do
- what tools it may use
- what output contract it should produce
- what it returns

Bad:

```python
def build_agent():
    return Agent(...)
```

Good:

```python
def build_risk_governor_agent() -> Agent:
    """
    Builds the Risk Governor Agent.

    The Risk Governor Agent reviews validation evidence, portfolio exposure,
    risk limits, and policy constraints before producing a RiskDecisionPackage.

    This agent may recommend approval or rejection, but deterministic policy
    gates remain responsible for enforcing approval rules.

    Returns:
        Agent: Configured Google ADK Agent instance.
    """
```

---

## 16. Standard Agent Response Schema

All agent runtime results should be normalized into this structure:

```python
{
    "status": "success" | "error" | "blocked" | "needs_approval" | "needs_clarification",
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
        "input_contract": str,
        "output_contract": str,
        "approval_required": bool,
    },
}
```

An agent runtime must never return unstructured raw model output directly to a workflow.

The runtime may include the raw text in `data["raw_output"]`, but workflows should depend on the normalized response.

---

## 17. Standard Agent Error Codes

Use deterministic error codes.

```text
INVALID_INPUT
MISSING_INPUT
MISSING_EVIDENCE
STALE_EVIDENCE
CONFLICTING_EVIDENCE
TOOL_FAILURE
POLICY_BLOCKED
PERMISSION_DENIED
APPROVAL_REQUIRED
OUTPUT_CONTRACT_FAILED
AGENT_EXECUTION_FAILED
UNKNOWN_AGENT
REGISTRY_ERROR
RUNTIME_ERROR
UNKNOWN_ERROR
```

Example:

```python
{
    "status": "blocked",
    "message": "Live trading is blocked without explicit approval.",
    "data": None,
    "decision": None,
    "evidence": [],
    "tool_calls": [],
    "error": {
        "code": "APPROVAL_REQUIRED",
        "details": "live_execution_agent cannot request live broker action without approval.",
    },
    "metadata": {...},
}
```

---

## 18. Request ID and Workflow ID Rule

Every agent run must include:

```python
request_id: str
workflow_id: str
```

The same IDs must be propagated through:

```text
user request
runtime
agent
tool calls
policy checks
contracts
audit logs
workflow handoffs
final response
```

This allows complete tracing of a workflow.

---

## 19. Agent Logging Footprint Rule

Every agent run must leave a logging footprint.

At minimum, log:

```text
agent build
agent run started
request id
workflow id
agent name
agent version
agent risk level
input summary
allowed tools
blocked tools
tool calls
policy check result
output contract
approval required
agent run completed
agent run failed
agent run blocked
execution time
```

Runtime example:

```python
logger.info(
    "Agent run started | request_id=%s | workflow_id=%s | agent=%s | version=%s",
    request_id,
    workflow_id,
    agent_name,
    agent_version,
)

logger.info(
    "Agent run completed | request_id=%s | workflow_id=%s | agent=%s | execution_ms=%s",
    request_id,
    workflow_id,
    agent_name,
    execution_ms,
)
```

Do not log secrets, passwords, broker tokens, API keys, or full private credentials.

---

## 20. Audit Footprint Rule

Every important agent run must emit an audit record.

At minimum, audit:

```text
timestamp
request_id
workflow_id
agent_name
agent_version
agent_department
agent_risk_level
input_summary
tools_allowed
tools_called
tool_result_references
evidence_references
decision
output_contract
approval_required
policy_result
blocked_actions
errors
execution_ms
```

Audit should start as JSONL or another append-friendly format.

Audit can later move to a database.

---

## 21. Evidence Discipline Rule

Agents must clearly separate:

```text
observed evidence
tool result
calculated result
user-provided information
agent interpretation
assumption
recommendation
```

Agents must not invent:

```text
backtest results
live performance
risk approvals
broker fills
portfolio exposure
optimization results
walk-forward results
Monte Carlo results
```

If evidence is missing, the agent must say so.

If evidence is stale, the agent must say so.

If evidence conflicts, the agent must mark the conflict and either ask for clarification or escalate.

---

## 22. Input and Output Contract Rule

Every agent must declare:

```python
AGENT_INPUT_CONTRACT = "AgentRequest"
AGENT_OUTPUT_CONTRACT = "ResearchEvidencePack"
```

Early versions may use dictionaries plus light validation.

Use Pydantic models when:

- workflows depend on fields
- missing fields cause bugs
- outputs are stored
- outputs are compared
- output reaches risk, portfolio, execution, governance, or live trading

Recommended core contracts:

```text
AgentRequest
AgentResponse
EvidenceItem
EvidencePack
ResearchEvidencePack
StrategySpecificationPackage
ValidationEvidencePackage
RiskDecisionPackage
ExecutionStatePackage
AuditPerformancePackage
ApprovalStatus
PolicyDecision
ToolCallRecord
AgentRunRecord
```

---

## 23. Department Handoff Rule

Each department should mainly produce one handoff object.

```text
Research -> ResearchEvidencePack
Strategy -> StrategySpecificationPackage
Validation -> ValidationEvidencePackage
Risk & Portfolio -> RiskDecisionPackage
Execution -> ExecutionStatePackage
Operations -> AuditPerformancePackage
```

Department leads should handle cross-department handoffs.

Avoid every sub-agent talking directly to every other sub-agent.

Preferred:

```text
Research Lead -> Strategy Lead
Strategy Lead -> Validation Lead
Validation Lead -> Risk Lead
Risk Lead -> Execution Lead
Execution Lead -> Operations
```

Avoid:

```text
every agent can call every other agent
```

---

## 24. Runtime Standard

`agentic/runtime.py` is the controlled execution layer.

It should provide:

```python
run_agent(...)
run_agent_async(...)
normalize_agent_response(...)
capture_tool_calls(...)
emit_agent_audit_record(...)
```

The runtime must:

- fetch agents through registry
- validate agent exists
- validate request_id and workflow_id
- run policy checks before execution
- normalize output
- validate output contract where applicable
- emit logs
- emit audit record
- fail clearly on unknown agents
- fail closed for high-risk and critical agents

Example runtime signature:

```python
def run_agent(
    agent_name: str,
    prompt: str,
    request_id: str,
    workflow_id: str,
    context: dict | None = None,
) -> dict:
    ...
```

---

## 25. Registry Standard

`agentic/registry.py` is the source of truth for agent discovery.

Example:

```python
from haruquant.agentic.agents.executive import build_ceo_agent
from haruquant.agentic.agents.executive import build_planner_agent
from haruquant.agentic.agents.research import build_research_lead_agent
from haruquant.agentic.agents.strategy import build_strategy_designer_agent


AGENTS = {
    "ceo": build_ceo_agent,
    "planner": build_planner_agent,
    "research_lead": build_research_lead_agent,
    "strategy_designer": build_strategy_designer_agent,
}
```

Registry must validate:

- agent names are unique
- builder functions are callable
- builders return ADK `Agent` instances
- metadata exists
- output contracts are declared
- allowed tools are approved
- high-risk agents have policy rules
- critical agents require approval

Do not use YAML registries until Python registration becomes painful.

---

## 26. Policy Gate Standard

`agentic/policy.py` enforces deterministic safety.

LLMs may explain policy, but they must not enforce or bypass policy.

Required policy checks:

```python
def validate_allowed_tools(agent_name: str, tools: list) -> dict:
    ...

def require_evidence_for_handoff(package: dict) -> dict:
    ...

def require_live_approval(action: dict) -> dict:
    ...

def block_kill_switch_override(action: dict) -> dict:
    ...

def validate_agent_permissions(agent_name: str, requested_action: dict) -> dict:
    ...

def validate_output_contract(agent_name: str, output: dict) -> dict:
    ...
```

Policy must fail closed.

If policy is uncertain, block the action.

---

## 27. Approval Standard

Approval statuses:

```text
not_required
required
requested
approved
rejected
expired
revoked
```

Rules:

- live trading requires explicit approval
- risk increase requires explicit approval
- execution state changes require approval
- kill switch override is not allowed by LLM
- expired or missing approval fails closed
- approval must be checked deterministically

Agents may request approval.

Agents may not grant approval to themselves.

---

## 28. CEO Agent Special Rules

The CEO Agent is the user-facing executive coordinator.

The CEO Agent may:

- understand broad user intent
- delegate to Planner
- summarize department results
- ask clarification questions
- explain workflow status
- communicate blocked or approval-required states

The CEO Agent must not:

- bypass Planner
- bypass Risk
- bypass Execution gates
- directly place trades
- override kill switch
- invent results
- approve its own live trading request

---

## 29. Planner Agent Special Rules

The Planner Agent converts user requests into structured execution plans.

Planner output should include:

```python
{
    "intent": str,
    "risk_level": "low" | "medium" | "high" | "critical",
    "required_agents": list[str],
    "required_tools": list[str],
    "missing_inputs": list[str],
    "evidence_required": list[str],
    "approval_required": bool,
    "blocked_actions": list[str],
    "workflow_to_run": str,
}
```

The Planner must not execute high-risk actions directly.

The Planner should route to the correct workflow or ask for clarification.

---

## 30. Risk and Execution Agent Special Rules

Risk, portfolio, governance, and execution agents are high-risk or critical.

They must have:

- explicit approval checks
- deterministic policy gates
- audit records
- strict output contracts
- fail-closed behavior
- no live action by default
- kill switch awareness
- evidence requirement enforcement

Live execution agents must never place trades unless:

```text
approval exists
approval is valid
risk decision allows it
kill switch is not active
broker state is healthy
execution tool allows it
audit record can be written
```

---

## 31. Workflow Standard

`agentic/workflows.py` contains explicit workflow functions.

Do not implement a generic workflow engine at the beginning.

Examples:

```python
def run_research_workflow(...):
    ...

def run_strategy_workflow(...):
    ...

def run_validation_workflow(...):
    ...

def run_risk_review_workflow(...):
    ...

def run_paper_execution_workflow(...):
    ...

def run_live_execution_workflow(...):
    ...
```

The full lifecycle should remain clear:

```text
User request
    -> CEO
    -> Planner
    -> Research
    -> Strategy
    -> Validation
    -> Risk & Portfolio
    -> Paper Execution
    -> Paper Performance Review
    -> Risk Re-approval
    -> Human Board Approval
    -> Live Execution
    -> Operations / Audit / Monitoring
```

---

## 32. Minimal Vertical Slice Rule

Build the smallest useful slice first:

```text
User prompt
    -> Research Lead Agent
    -> market data tool
    -> ResearchEvidencePack
    -> audit log
```

Then:

```text
ResearchEvidencePack
    -> Strategy Designer Agent
    -> StrategySpecificationPackage
```

Then:

```text
StrategySpecificationPackage
    -> Simulation Lead Agent
    -> backtest tool
    -> ValidationEvidencePackage
```

Then add:

```text
Risk review
Paper trading
Live execution approval
Live execution
Operations monitoring
```

---

## 33. Unit Testing Rule

Every agent must have unit tests.

Recommended structure:

```text
tests/unit/agentic/agents/{department}/test_{agent_file}.py
```

Examples:

```text
tests/unit/agentic/agents/research/test_research.py
tests/unit/agentic/agents/strategy/test_strategy.py
tests/unit/agentic/agents/execution/test_execution.py
```

Each agent must test:

- builder returns an ADK Agent
- agent name is correct
- agent description exists
- instruction exists
- instruction has required sections
- allowed tools are attached
- blocked tools are not attached
- metadata constants exist
- risk level is valid
- output contract is declared
- permissions are declared
- agent can be registered
- agent can be constructed without side effects

For high-risk or critical agents, also test:

- approval is required
- live tools are blocked by default
- kill switch is respected
- policy gate cannot be bypassed
- fail-closed behavior works

---

## 34. Usage Example Rule

Every agent must have a real-world usage example.

Recommended structure:

```text
tests/usage/agentic/agents/{department}/{agent_name}.py
```

Examples:

```text
tests/usage/agentic/agents/research/research_lead.py
tests/usage/agentic/agents/strategy/strategy_designer.py
tests/usage/agentic/agents/risk/risk_governor.py
tests/usage/agentic/agents/execution/execution_readiness.py
```

Usage examples should:

- use realistic prompts
- avoid mocks where possible
- call the agent through `agentic.runtime`
- include request_id
- include workflow_id
- show how result is consumed
- print or inspect the normalized agent response

Example:

```python
from haruquant.agentic.runtime import run_agent


result = run_agent(
    agent_name="research_lead",
    prompt="Analyze EURUSD H1 and summarize current market context.",
    request_id="usage-research-001",
    workflow_id="workflow-research-001",
)

if result["status"] == "success":
    print(result["data"])
else:
    print(result["error"])
```

---

## 35. Runtime Tests

`agentic/runtime.py` must have tests.

Test:

- valid agent name runs
- unknown agent fails clearly
- request_id is required
- workflow_id is required
- execution_ms is recorded
- agent output is normalized
- errors become structured responses
- audit record is emitted
- policy check runs before high-risk execution
- output contract validation runs
- high-risk agents fail closed when approval is missing

---

## 36. Registry Tests

`agentic/registry.py` must have tests.

Test:

- all registered agent names are unique
- all builders are callable
- all builders return ADK Agent objects
- unknown agent returns/raises clear error
- all agents have metadata
- all agents have output contracts
- all agents have allowed tools declared
- all high-risk agents have policy coverage
- all critical agents require approval

---

## 37. Policy Tests

`agentic/policy.py` must have tests.

Test:

- research agent cannot place trades
- strategy agent cannot approve risk
- validation agent cannot invent missing evidence
- risk agent cannot bypass evidence requirement
- execution agent cannot trade without approval
- kill switch blocks live execution
- expired approval is rejected
- missing approval is rejected
- unapproved broker actions fail closed
- LLM output cannot override deterministic policy

---

## 38. Contract Tests

`agentic/contracts.py` must have tests.

Test:

- valid AgentRequest passes
- invalid AgentRequest fails
- valid AgentResponse passes
- ResearchEvidencePack requires evidence
- StrategySpecificationPackage requires strategy logic
- ValidationEvidencePackage requires validation evidence
- RiskDecisionPackage requires approve/reject decision
- ExecutionStatePackage requires execution state
- missing evidence fails for risk and execution handoffs
- stale evidence is rejected or flagged
- invalid approval status fails

---

## 39. Audit Tests

`agentic/audit.py` must have tests.

Test:

- audit record is created
- request_id exists
- workflow_id exists
- agent_name exists
- tool calls are recorded
- evidence references are recorded
- decisions are recorded
- blocked actions are recorded
- approval requirements are recorded
- errors are recorded
- secret-like values are redacted
- audit writer fails safely

---

## 40. Instruction Completeness Tests

Every agent instruction should be tested for required sections.

Required headings:

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

Test example:

```python
REQUIRED_SECTIONS = [
    "Role",
    "Responsibilities",
    "Non-Goals",
    "Allowed Tools",
    "Blocked Actions",
    "Required Evidence",
    "Output Contract",
    "Safety Rules",
    "Uncertainty Behavior",
    "Escalation Rules",
]
```

The test should fail if any required section is missing.

---

## 41. Agent Evaluation Tests

Unit tests check construction and rules.

Evaluation tests check behavior.

Recommended structure:

```text
tests/evals/agentic/{department}/test_{agent_name}_eval.py
```

Examples:

```text
tests/evals/agentic/research/test_research_lead_eval.py
tests/evals/agentic/strategy/test_strategy_designer_eval.py
tests/evals/agentic/risk/test_risk_governor_eval.py
tests/evals/agentic/execution/test_live_execution_eval.py
```

Evaluation scenarios should include:

- normal request
- missing input
- missing evidence
- stale evidence
- conflicting evidence
- unsafe live trading request
- request to bypass risk
- request to invent backtest results
- approval-required action
- tool failure
- blocked tool request

Expected behavior:

- asks clarification when needed
- blocks unsafe action
- requests evidence
- returns structured package
- does not invent data
- does not call blocked tools
- escalates to correct department

---

## 42. Agent Standardization Audit Report

When auditing agents, produce:

```text
AGENT_STANDARDIZATION_AUDIT.md
```

Required sections:

```markdown
# Agent Standardization Audit

## 1. Executive Summary

## 2. Agent Files Audited

## 3. Registered Agents

## 4. Agent Metadata Review

## 5. Instruction Completeness Review

## 6. Allowed Tools and Blocked Tools Review

## 7. Permission Declaration Review

## 8. Output Contract Review

## 9. Runtime and Registry Review

## 10. Policy Gate Review

## 11. Audit Footprint Review

## 12. Unit Test Coverage

## 13. Usage Example Coverage

## 14. Evaluation Coverage

## 15. Non-Compliant Agents

## 16. Missing Tests

## 17. Missing Usage Examples

## 18. Risk and Execution Safety Issues

## 19. Recommended Next Actions
```

Compliance table:

| Agent | File | Department | Risk | Metadata | Instruction | Tools | Permissions | Contract | Logging | Audit | Unit Tests | Usage | Evals | Status |
| :---- | :--- | :--------- | :--- | :------- | :---------- | :---- | :---------- | :------- | :------ | :---- | :--------- | :---- | :---- | :----- |

---

## 43. Agent File Audit Checklist

For every agent file:

- [ ] File starts with file-level docstring
- [ ] File imports logger
- [ ] File contains no runtime execution logic
- [ ] File defines agent metadata constants
- [ ] File defines permission declarations
- [ ] File defines ALLOWED_TOOLS
- [ ] File defines BLOCKED_TOOL_NAMES
- [ ] File defines instruction text or loads instruction safely
- [ ] Instruction has all required sections
- [ ] Builder function exists
- [ ] Builder function has a docstring
- [ ] Builder function logs construction
- [ ] Builder function returns ADK Agent
- [ ] Builder does not call tools
- [ ] Builder does not mutate external state
- [ ] Agent output contract is declared
- [ ] Agent risk level is valid
- [ ] Agent approval requirement is correct
- [ ] Unit tests exist
- [ ] Usage example exists
- [ ] Evaluation scenarios exist where needed

---

## 44. Agent Completion Checklist

An agent is complete only when:

- [ ] Agent has clear identity
- [ ] Agent has clear department
- [ ] Agent has clear responsibility
- [ ] Agent has non-goals
- [ ] Agent has explicit allowed tools
- [ ] Agent has blocked actions
- [ ] Agent has permission declarations
- [ ] Agent has risk level
- [ ] Agent has approval requirement
- [ ] Agent has input/output contract
- [ ] Agent has evidence requirements
- [ ] Agent instruction has required sections
- [ ] Agent builder follows standard
- [ ] Agent is registered
- [ ] Agent is runnable through runtime
- [ ] Agent output is normalized
- [ ] Agent emits logs
- [ ] Agent emits audit records where required
- [ ] Agent has unit tests
- [ ] Agent has usage example
- [ ] Agent has evaluation scenarios where needed
- [ ] Agent passes policy checks
- [ ] Agent fails closed when unsafe

---

## 45. Definition of Done

### For Low and Medium Risk Agents

An agent is done when:

- builder exists
- metadata exists
- instruction is clear
- allowed tools are explicit
- blocked actions are explicit
- permissions are declared
- output contract is declared
- smoke test can construct the agent
- agent can run through runtime
- output follows normalized response schema
- usage example exists
- audit/logging footprint exists where required

### For High and Critical Risk Agents

In addition to the above:

- policy gate exists
- approval requirement is explicit
- audit record is mandatory
- unsafe tools are blocked by default
- live actions are disabled by default
- kill switch state is respected
- evidence requirements are enforced
- fail-closed behavior is tested
- approval tests pass
- policy tests pass
- contract tests pass

---

## 46. Non-Negotiable Safety Rules

These rules apply even in the simplest implementation:

- live trading is disabled by default
- no live action without explicit approval
- no risk increase without explicit approval
- kill switch cannot be overridden by an LLM
- broker execution tools must fail closed
- agents cannot invent backtest or performance results
- stale or missing evidence must be disclosed
- risk and execution workflows must emit audit logs
- policy is deterministic
- approval is deterministic
- unsafe uncertainty results in blocking, not guessing

---

## 47. Final Build Rule

Build HaruQuant agents like this:

```text
flat files first
simple ADK agents
existing tools reused directly
one registry
one runtime helper
one contracts file
one policy file
one audit file
explicit workflow functions
folders only when earned
tests for every agent
usage examples for every agent
audit footprint for important decisions
fail-closed safety for risk and execution
```

The system should feel like:

```text
a few senior trading agents with many reliable tools
```

not:

```text
a large company of tiny agents with bureaucracy around every task
```

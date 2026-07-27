# HaruQuant ADK Incremental Implementation Plan — Simple Build Version

Status: revised simple implementation plan  
Target runtime: Google ADK  
Architecture style: direct Python ADK agents + shared root-level tools + lightweight runtime  
Goal: build the streamlined HaruQuant trading agent system from scratch without unnecessary folder/file overhead.

---

## 1. Why This Version Exists

The previous implementation plan was too heavy for the way HaruQuant is currently being built. It introduced many enterprise-style folders too early:

```text
agentic/
├── host/
├── agents/
├── workflows/
├── capabilities/
├── policy/
├── approvals/
├── evaluation/
├── observability/
├── registry/
└── audit/
```

That structure is useful for a mature production platform, but it creates too much overhead at the start.

The new implementation approach is based on the simpler working pattern already used in `01_agent.py`:

```text
Direct ADK Agent(...)
+ tools imported from the root tools/ folder
+ simple Runner
+ simple session service
+ agent can run independently
```

The key design decision is:

> Start simple. Add structure only when repetition, risk, or file size forces it.

---

## 2. Current Repository Reality

The current repository already has this useful structure:

```text
HARUQUANT/
├── .vscode/
├── agentic/
├── api/
├── data/
├── docs/
├── scripts/
├── tests/
├── tools/
├── ui/
├── venv/
├── pyproject.toml
├── requirements.txt
└── README.md
```

Important note:

> The `tools/` folder already exists outside `agentic/`. Keep it there.

Do not move tools into `agentic/capabilities/` or `agentic/agents/.../tools/` at this stage.

The root-level `tools/` folder is the correct place for reusable deterministic functions such as:

```text
tools/data.py
tools/simulation.py
tools/research.py
tools/strategy.py
tools/backtest.py
tools/analytics.py
tools/risk.py
tools/execution.py
tools/audit.py
```

Agents should import from `tools/` directly.

---

## 3. New Implementation Philosophy

Use this build order:

```text
Tools
→ One Agent
→ Reusable Runner
→ More Independent Agents
→ Simple Department Files
→ Simple Workflows
→ Safety Gates
→ Tests
→ Optional Manifest/Governance Layer Later
```

Do not start with:

```text
Contracts → Runtime → Policies → Registries → Manifests → Audit → First Agent
```

That is too much ceremony for the first version.

The practical rule is:

```text
One concept starts as one file.
Only split into a folder when the file becomes painful.
```

---

## 4. What We Are Keeping vs Delaying

### Keep Immediately

| Concept | Initial Implementation |
|---|---|
| Google ADK agents | Direct `Agent(...)` objects in Python |
| Tools | Reusable functions in root-level `tools/` |
| Runner | One small `agentic/runtime/runner.py` |
| Model config | One small `agentic/config/agent_model.py` or existing config |
| Permissions | One small `agentic/runtime/permissions.py` |
| Safety | Safety inside tools first, then optional runtime checks |
| Audit | Simple JSONL logger |
| Workflows | Simple Python functions |
| Tests | Simple pytest files |

### Delay Until Later

| Heavy Concept | Delay Because |
|---|---|
| `.agent.md` manifests | Too much overhead before agents stabilize |
| `SKILL.md` files | Useful only when procedures repeat often |
| `.prompt.md` files | Inline instructions are simpler at first |
| `.instructions.md` files | Inline agent instructions are easier at first |
| Per-agent folders | Too many files for early development |
| Per-agent README files | Add later for stable agents |
| Agent registry folder | Use Python dictionaries first |
| Full audit folder | Use JSONL logs first |
| Approval subsystem | Start with explicit booleans and permission checks |
| Evaluation folder | Start with pytest and simple evaluator functions |
| Observability folder | Start with logging/audit JSONL |
| Capabilities folder | Root `tools/` already covers this need |

---

## 5. Final Simple Folder Structure

Use this target structure for the first real implementation:

```text
HARUQUANT/
├── agentic/
│   ├── __init__.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── executive.py
│   │   ├── research.py
│   │   ├── strategy.py
│   │   ├── validation.py
│   │   ├── risk.py
│   │   ├── execution.py
│   │   └── operations.py
│   │
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   ├── permissions.py
│   │   ├── safety.py
│   │   └── schemas.py
│   │
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── research_to_strategy.py
│   │   └── strategy_lifecycle.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── agent_model.py
│   │
│   └── examples/
│       ├── 01_basic_agents.py
│       ├── 02_research_agent.py
│       ├── 03_strategy_agent.py
│       └── 04_strategy_lifecycle.py
│
├── tools/
│   ├── __init__.py
│   ├── data.py
│   ├── simulation.py
│   ├── research.py
│   ├── market_context.py
│   ├── strategy.py
│   ├── backtest.py
│   ├── analytics.py
│   ├── risk.py
│   ├── execution.py
│   └── audit.py
│
├── tests/
│   ├── test_tools.py
│   ├── test_agents.py
│   ├── test_permissions.py
│   ├── test_safety.py
│   └── test_workflows.py
│
├── docs/
│   ├── architecture/
│   └── implementation/
│
├── api/
├── data/
├── scripts/
├── ui/
├── pyproject.toml
├── requirements.txt
└── README.md
```

This gives a clean separation:

```text
agentic/agents/     = ADK agent definitions
agentic/runtime/    = runner, permissions, schemas, safety helpers
agentic/workflows/  = simple orchestration functions
agentic/examples/   = usage examples
tools/              = reusable deterministic functions, already root-level
tests/              = all tests
docs/               = documentation
```

---

## 6. What Not to Build Yet

Do not create these folders in the first version:

```text
agentic/host/
agentic/capabilities/
agentic/policy/
agentic/approvals/
agentic/evaluation/
agentic/observability/
agentic/registry/
agentic/audit/
```

Do not create this per-agent structure yet:

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
├── prompts/
├── instructions/
├── skills/
├── tools/
├── fixtures/
└── tests/
```

That structure is useful later, not now.

Start with:

```text
agentic/agents/research.py
```

Inside that file:

```python
research_lead_agent = Agent(...)
market_intelligence_agent = Agent(...)
quant_research_agent = Agent(...)
research_validator_agent = Agent(...)
```

Split only when the file becomes too large.

---

## 7. Simple Agent Pattern

Every agent should initially follow this pattern:

```python
# agentic/agents/research.py

from google.adk.agents import Agent

from agentic.config.agent_model import AGENT_MODEL
from tools.data import mt5_data_download
from tools.research import calculate_adr, calculate_atr, calculate_spread_statistics


research_agent = Agent(
    name="research_agent",
    model=AGENT_MODEL,
    description="Researches market behavior and produces evidence-backed trading hypotheses.",
    instruction=\"\"\"
    You are the HaruQuant Research Agent.

    Use tools to retrieve and analyze market data.

    Your job:
    - inspect trend
    - inspect volatility
    - inspect spread behavior
    - identify possible strategy hypotheses
    - clearly separate facts from assumptions

    You cannot:
    - execute live trades
    - approve live deployment
    - invent backtest results
    - claim profitability without validation evidence
    \"\"\",
    tools=[
        mt5_data_download,
        calculate_atr,
        calculate_adr,
        calculate_spread_statistics,
    ],
)
```

This is close to the working style of `01_agent.py`: direct ADK agent creation, tools imported from `tools/`, and no manifest overhead.

---

## 8. Simple Runner Pattern

Create one reusable runner:

```python
# agentic/runtime/runner.py

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


APP_NAME = "haruquant"
USER_ID = "haruperi"


async def run_agent(agent, prompt: str, session_id: str = "default") -> str:
    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    final_parts: list[str] = []

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_parts.append(part.text)

    return "\n".join(final_parts)
```

Then usage becomes:

```python
# agentic/examples/02_research_agent.py

import asyncio

from agentic.agents.research import research_agent
from agentic.runtime.runner import run_agent


async def main() -> None:
    response = await run_agent(
        agent=research_agent,
        session_id="research_example",
        prompt="Analyze EURUSD H1 using the latest 100 candles.",
    )

    print(response)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 9. Simple Permission Model

Start with one file:

```python
# agentic/runtime/permissions.py

AGENT_PERMISSIONS = {
    "research_agent": {
        "can_trade_live": False,
        "can_place_paper_orders": False,
        "can_run_backtest": False,
        "can_modify_risk": False,
    },
    "strategy_agent": {
        "can_trade_live": False,
        "can_place_paper_orders": False,
        "can_run_backtest": False,
        "can_modify_risk": False,
    },
    "validation_agent": {
        "can_trade_live": False,
        "can_place_paper_orders": False,
        "can_run_backtest": True,
        "can_modify_risk": False,
    },
    "risk_agent": {
        "can_trade_live": False,
        "can_place_paper_orders": False,
        "can_run_backtest": False,
        "can_modify_risk": False,
    },
    "execution_agent": {
        "can_trade_live": False,
        "can_place_paper_orders": True,
        "can_run_backtest": False,
        "can_modify_risk": False,
    },
}


def has_permission(agent_name: str, permission: str) -> bool:
    return AGENT_PERMISSIONS.get(agent_name, {}).get(permission, False)


def require_permission(agent_name: str, permission: str) -> None:
    if not has_permission(agent_name, permission):
        raise PermissionError(
            f"Agent '{agent_name}' does not have permission '{permission}'."
        )
```

Do not build a full policy engine yet.

---

## 10. Simple Safety Model

Put safety first inside the tools. This is more important than having many governance folders.

Example:

```python
# tools/execution.py

def place_market_order(
    symbol: str,
    side: str,
    volume: float,
    live_enabled: bool = False,
) -> dict:
    if not live_enabled:
        return {
            "status": "blocked",
            "reason": "live_enabled is false. Order was staged but not sent live.",
            "requested_order": {
                "symbol": symbol,
                "side": side,
                "volume": volume,
            },
        }

    return {
        "status": "blocked",
        "reason": "Live execution is disabled in this implementation phase.",
    }
```

Later, when live trading is actually needed, the tool should require:

```text
live_enabled=True
approval_id present
risk_check_passed=True
kill_switch_active=False
execution_environment="production"
```

For now, fail closed.

---

## 11. Simple Audit Model

Use one tool:

```python
# tools/audit.py

import json
from datetime import datetime, timezone
from pathlib import Path


AUDIT_PATH = Path("data/logs/audit.jsonl")


def write_audit_event(event_type: str, payload: dict) -> dict:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }

    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")

    return {
        "status": "logged",
        "path": str(AUDIT_PATH),
        "event": event,
    }
```

Use it from tools and workflows:

```python
from tools.audit import write_audit_event

write_audit_event(
    event_type="research_agent_run",
    payload={
        "agent": "research_agent",
        "symbol": "EURUSD",
        "timeframe": "H1",
    },
)
```

That is enough for phase 1.

---

## 12. Simple Schemas

Use one schemas file first:

```python
# agentic/runtime/schemas.py

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    SUCCESS = "success"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"
    FAILED = "failed"


class SimpleAgentResult(BaseModel):
    agent_name: str
    status: AgentStatus
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    next_step: str | None = None


class ResearchEvidencePack(BaseModel):
    symbol: str
    timeframe: str
    summary: str
    observations: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StrategySpec(BaseModel):
    name: str
    symbol: str
    timeframe: str
    direction: str
    entry_rules: list[str]
    exit_rules: list[str]
    risk_rules: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

Do not split schemas into many files until needed.

---

## 13. Streamlined Agent Departments

The architecture still keeps the lean department model, but each department starts as one Python file.

### 13.1 Executive Agents

File:

```text
agentic/agents/executive.py
```

Agents:

```text
ceo_agent
planner_agent
```

Purpose:

- user-facing interpretation
- request routing
- workflow selection
- final summary

Initial tools:

```text
tools.audit.write_audit_event
runtime.permissions.has_permission
```

No live execution.

---

### 13.2 Research Agents

File:

```text
agentic/agents/research.py
```

Agents:

```text
research_agent
market_intelligence_agent
quant_research_agent
research_validator_agent
```

Purpose:

- analyze market data
- read news/calendar/sentiment where available
- produce research evidence packs
- validate whether hypothesis is testable

Initial tools:

```text
tools.data.mt5_data_download
tools.research.calculate_atr
tools.research.calculate_adr
tools.research.calculate_spread_statistics
tools.research.calculate_session_statistics
tools.market_context.fetch_forexfactory_calendar
tools.market_context.fetch_forexfactory_news
tools.audit.write_audit_event
```

---

### 13.3 Strategy Agents

File:

```text
agentic/agents/strategy.py
```

Agents:

```text
strategy_agent
strategy_designer_agent
strategy_reviewer_agent
strategy_librarian_agent
```

Purpose:

- convert idea/hypothesis into strategy spec
- normalize rules
- identify missing inputs
- flag high-risk trade management
- save/register strategy artifacts if needed

Initial tools:

```text
tools.strategy.generate_strategy_spec
tools.strategy.validate_strategy_spec
tools.strategy.classify_strategy_type
tools.strategy.detect_high_risk_trade_management
tools.strategy.save_strategy_spec
tools.audit.write_audit_event
```

Delay code generation until strategy specs are stable.

---

### 13.4 Validation Agents

File:

```text
agentic/agents/validation.py
```

Agents:

```text
validation_agent
backtest_analyst_agent
optimization_agent
robustness_agent
```

Purpose:

- run backtests
- analyze results
- run robustness/optimization later
- produce validation evidence

Initial tools:

```text
tools.backtest.run_backtest
tools.backtest.validate_backtest_result
tools.analytics.calculate_trade_metrics
tools.analytics.calculate_drawdown_metrics
tools.analytics.calculate_ratio_metrics
tools.analytics.build_backtest_report
tools.audit.write_audit_event
```

Start with backtest only. Add optimization and robustness later.

---

### 13.5 Risk Agents

File:

```text
agentic/agents/risk.py
```

Agents:

```text
risk_agent
risk_governor_agent
portfolio_manager_agent
allocation_agent
```

Purpose:

- check risk limits
- calculate portfolio impact
- approve/reject paper admission
- propose allocation, not live execution

Initial tools:

```text
tools.risk.check_max_drawdown_limit
tools.risk.check_correlation_limit
tools.risk.check_var_limit
tools.risk.calculate_position_size
tools.risk.run_risk_governor_checks
tools.audit.write_audit_event
```

---

### 13.6 Execution Agents

File:

```text
agentic/agents/execution.py
```

Agents:

```text
execution_agent
execution_readiness_agent
paper_trading_agent
kill_switch_agent
```

Purpose:

- check broker readiness
- run paper trading actions
- block live trading by default
- manage kill switch

Initial tools:

```text
tools.simulation.trading_is_connected
tools.simulation.trading_connect
tools.simulation.trading_account_info
tools.simulation.trading_symbol_info
tools.execution.place_market_order
tools.execution.check_kill_switch_state
tools.execution.trigger_kill_switch
tools.audit.write_audit_event
```

Live execution remains blocked until explicit later phase.

---

### 13.7 Operations Agents

File:

```text
agentic/agents/operations.py
```

Agents:

```text
operations_agent
audit_agent
performance_reporter_agent
cost_agent
```

Purpose:

- summarize logs
- summarize strategy performance
- monitor costs
- report failures

Initial tools:

```text
tools.audit.write_audit_event
tools.audit.read_audit_events
tools.analytics.build_performance_report
```

---

## 14. Incremental Build Phases

## Phase 0 — Minimal Cleanup

### Goal

Align the repo with the simple structure without deleting existing useful code.

### Tasks

- [ ] Keep root `tools/` as the main tool layer.
- [ ] Keep `agentic/` as the agent runtime and agent definitions area.
- [ ] Create `agentic/agents/` if missing.
- [ ] Create `agentic/runtime/` if missing.
- [ ] Create `agentic/workflows/` if missing.
- [ ] Create `agentic/examples/` if missing.
- [ ] Do not create the heavy governance folders yet.
- [ ] Move or copy `01_agent.py` pattern into `agentic/examples/01_basic_agents.py`.

### Exit Gate

- [ ] Repository imports work.
- [ ] Existing tools still import from root `tools/`.
- [ ] One example can run.

---

## Phase 1 — Tool Foundation

### Goal

Create or clean the minimum tool layer before building many agents.

### Required Root Tool Files

```text
tools/data.py
tools/research.py
tools/market_context.py
tools/strategy.py
tools/backtest.py
tools/analytics.py
tools/risk.py
tools/execution.py
tools/audit.py
```

### Minimum Tools

#### Data

- [ ] `mt5_data_download`
- [ ] `get_symbol_metadata`
- [ ] `validate_ohlcv_data`

#### Research

- [ ] `calculate_atr`
- [ ] `calculate_adr`
- [ ] `calculate_spread_statistics`
- [ ] `calculate_session_statistics`

#### Market Context

- [ ] `fetch_forexfactory_calendar`
- [ ] `fetch_forexfactory_news`
- [ ] `fetch_forexfactory_sentiment`
- [ ] `filter_events_by_symbol`

#### Strategy

- [ ] `generate_strategy_spec`
- [ ] `validate_strategy_spec`
- [ ] `classify_strategy_type`
- [ ] `detect_high_risk_trade_management`
- [ ] `save_strategy_spec`

#### Backtest

- [ ] `run_backtest`
- [ ] `validate_backtest_config`
- [ ] `validate_backtest_result`

#### Analytics

- [ ] `calculate_trade_metrics`
- [ ] `calculate_drawdown_metrics`
- [ ] `calculate_ratio_metrics`
- [ ] `build_backtest_report`

#### Risk

- [ ] `check_max_drawdown_limit`
- [ ] `check_correlation_limit`
- [ ] `check_var_limit`
- [ ] `calculate_position_size`
- [ ] `run_risk_governor_checks`

#### Execution

- [ ] `place_market_order`
- [ ] `check_kill_switch_state`
- [ ] `trigger_kill_switch`
- [ ] `run_execution_readiness_check`

#### Audit

- [ ] `write_audit_event`
- [ ] `read_audit_events`

### Exit Gate

- [ ] Each tool can be imported.
- [ ] Each risky tool fails closed.
- [ ] Tool tests pass.
- [ ] No tool performs live trading by default.

---

## Phase 2 — Runtime Foundation

### Goal

Create the small runtime layer.

### Files

```text
agentic/runtime/runner.py
agentic/runtime/permissions.py
agentic/runtime/safety.py
agentic/runtime/schemas.py
```

### Tasks

- [ ] Implement reusable `run_agent`.
- [ ] Implement `AGENT_PERMISSIONS`.
- [ ] Implement `has_permission`.
- [ ] Implement `require_permission`.
- [ ] Implement basic safety constants:
  - [ ] `LIVE_TRADING_ENABLED = False`
  - [ ] `REQUIRE_APPROVAL_FOR_LIVE = True`
  - [ ] `DEFAULT_ENVIRONMENT = "development"`
- [ ] Implement simple Pydantic schemas.

### Exit Gate

- [ ] Runner can execute one simple ADK agent.
- [ ] Permissions block unsupported actions.
- [ ] Schemas import cleanly.
- [ ] Runtime tests pass.

---

## Phase 3 — First Independent Agent

### Goal

Create one useful independent agent before building the whole system.

### Recommended First Agent

```text
agentic/agents/research.py
```

Create:

```python
research_agent = Agent(...)
```

### Tools

- `mt5_data_download`
- `calculate_atr`
- `calculate_adr`
- `calculate_spread_statistics`
- `write_audit_event`

### Example Prompt

```text
Analyze EURUSD H1 using the latest 100 candles.

Include:
1. trend direction
2. volatility read
3. spread condition
4. market structure notes
5. practical trading hypothesis
```

### Exit Gate

- [ ] Research agent runs independently.
- [ ] Research agent uses at least one real tool.
- [ ] Research agent does not claim profitability.
- [ ] Research agent does not run backtests.
- [ ] Research agent emits or calls audit logging.
- [ ] Example script works.

---

## Phase 4 — Department Agent Files

### Goal

Create the core department files, but keep each department in one Python file.

### Files

```text
agentic/agents/executive.py
agentic/agents/research.py
agentic/agents/strategy.py
agentic/agents/validation.py
agentic/agents/risk.py
agentic/agents/execution.py
agentic/agents/operations.py
```

### Build Order

1. `research.py`
2. `strategy.py`
3. `validation.py`
4. `risk.py`
5. `execution.py`
6. `executive.py`
7. `operations.py`

### Exit Gate

- [ ] Each file imports successfully.
- [ ] Each file exposes at least one working agent.
- [ ] Each agent can run standalone.
- [ ] No agent has unrestricted live trading capability.
- [ ] Basic tests pass.

---

## Phase 5 — Strategy Agent

### Goal

Create the first strategy development agent.

### File

```text
agentic/agents/strategy.py
```

### Initial Agent

```python
strategy_agent = Agent(...)
```

### Tools

- `generate_strategy_spec`
- `validate_strategy_spec`
- `classify_strategy_type`
- `detect_high_risk_trade_management`
- `save_strategy_spec`
- `write_audit_event`

### Agent Must Not

- run backtests
- approve live trading
- execute trades
- invent performance results
- hide high-risk rules such as martingale or grid

### Exit Gate

- [ ] Strategy agent creates a structured strategy spec.
- [ ] Missing fields are clearly listed.
- [ ] High-risk trade management is flagged.
- [ ] Spec can be saved.
- [ ] Strategy agent can run independently.

---

## Phase 6 — Validation Agent

### Goal

Create the first backtest/analytics agent.

### File

```text
agentic/agents/validation.py
```

### Initial Agent

```python
validation_agent = Agent(...)
```

### Tools

- `run_backtest`
- `validate_backtest_config`
- `validate_backtest_result`
- `calculate_trade_metrics`
- `calculate_drawdown_metrics`
- `calculate_ratio_metrics`
- `build_backtest_report`
- `write_audit_event`

### Start Small

Only implement:

```text
StrategySpec → Backtest → Metrics → Report
```

Delay:

```text
optimization
WFO
WFM
Monte Carlo
cross-market tests
cross-timeframe tests
```

### Exit Gate

- [ ] Validation agent can run a basic backtest.
- [ ] Backtest result is validated.
- [ ] Metrics are calculated.
- [ ] Report is created.
- [ ] No performance result is invented.

---

## Phase 7 — Risk Agent

### Goal

Create risk gate before any execution agent becomes powerful.

### File

```text
agentic/agents/risk.py
```

### Initial Agent

```python
risk_agent = Agent(...)
risk_governor_agent = Agent(...)
```

### Tools

- `check_max_drawdown_limit`
- `check_correlation_limit`
- `check_var_limit`
- `calculate_position_size`
- `run_risk_governor_checks`
- `write_audit_event`

### Required Behavior

Risk agent can say:

```text
approved_for_research
approved_for_backtest
approved_for_paper
rejected
needs_more_evidence
```

Risk agent cannot say:

```text
approved_for_live
```

Live approval is delayed until later.

### Exit Gate

- [ ] Risk checks are deterministic.
- [ ] Missing evidence causes rejection or clarification.
- [ ] Risk report is structured.
- [ ] Risk agent cannot execute trades.

---

## Phase 8 — Execution Agent

### Goal

Create safe execution wrapper with live trading blocked by default.

### File

```text
agentic/agents/execution.py
```

### Initial Agents

```python
execution_agent = Agent(...)
execution_readiness_agent = Agent(...)
paper_trading_agent = Agent(...)
kill_switch_agent = Agent(...)
```

### Tools

- `trading_is_connected`
- `trading_connect`
- `trading_account_info`
- `trading_symbol_info`
- `place_market_order`
- `run_execution_readiness_check`
- `check_kill_switch_state`
- `trigger_kill_switch`
- `write_audit_event`

### Required Behavior

- Paper trading can be enabled.
- Live order submission is blocked by default.
- Any live order tool must require `live_enabled=True`.
- Any live order tool must still block until production approval exists.
- Kill switch can block all execution.

### Exit Gate

- [ ] Execution readiness can summarize broker state.
- [ ] Paper order can be staged.
- [ ] Live order is blocked by default.
- [ ] Kill switch blocks execution.
- [ ] Audit log records execution attempts.

---

## Phase 9 — Simple Workflows

### Goal

Create simple orchestration without a heavy workflow engine.

### Files

```text
agentic/workflows/research_to_strategy.py
agentic/workflows/strategy_lifecycle.py
```

### Workflow 1 — Research to Strategy

```text
Research Agent
→ Strategy Agent
→ Strategy Reviewer
```

### Workflow 2 — Strategy Lifecycle

```text
Research
→ Strategy
→ Validation
→ Risk
→ Paper Execution
```

### Simple Workflow Function Pattern

```python
# agentic/workflows/research_to_strategy.py

from agentic.agents.research import research_agent
from agentic.agents.strategy import strategy_agent
from agentic.runtime.runner import run_agent


async def run_research_to_strategy(symbol: str, timeframe: str) -> dict:
    research_output = await run_agent(
        agent=research_agent,
        session_id=f"research_{symbol}_{timeframe}",
        prompt=f"Research {symbol} {timeframe} and produce a testable hypothesis.",
    )

    strategy_output = await run_agent(
        agent=strategy_agent,
        session_id=f"strategy_{symbol}_{timeframe}",
        prompt=f"Convert this research into a strategy spec:\n\n{research_output}",
    )

    return {
        "research": research_output,
        "strategy": strategy_output,
    }
```

### Exit Gate

- [ ] Workflow runs end-to-end.
- [ ] Workflow does not use direct live execution.
- [ ] Outputs are saved or logged.
- [ ] Workflow can fail safely.

---

## Phase 10 — Tests

### Goal

Add enough tests to keep the system safe without creating bureaucracy.

### Required Tests

```text
tests/test_tools.py
tests/test_agents.py
tests/test_permissions.py
tests/test_safety.py
tests/test_workflows.py
```

### Minimum Test Cases

#### Tools

- [ ] data tool imports
- [ ] strategy spec tool returns dict/model
- [ ] backtest result validator rejects bad result
- [ ] risk governor rejects missing evidence
- [ ] execution tool blocks live order by default
- [ ] audit writes JSONL event

#### Agents

- [ ] each agent can be constructed
- [ ] each agent has name
- [ ] each agent has instruction
- [ ] each agent has tools

#### Permissions

- [ ] research cannot trade live
- [ ] strategy cannot trade live
- [ ] validation can run backtest
- [ ] execution cannot trade live by default

#### Safety

- [ ] live order without `live_enabled=True` is blocked
- [ ] live order with `LIVE_TRADING_ENABLED=False` is blocked
- [ ] kill switch blocks execution

#### Workflows

- [ ] research to strategy workflow returns both outputs
- [ ] strategy lifecycle stops if validation fails
- [ ] risk rejection prevents execution

### Exit Gate

- [ ] `pytest` passes.
- [ ] Live execution remains blocked.
- [ ] Tool imports remain stable.
- [ ] Workflow tests cover happy path and blocked path.

---

## Phase 11 — When to Split Files into Folders

Only split when necessary.

### Split `agentic/agents/research.py` into a folder when:

- file exceeds roughly 400–600 lines
- agent instructions become hard to read
- multiple developers work on the same file
- tools and agent definitions become mixed
- tests need agent-specific fixtures

Then split to:

```text
agentic/agents/research/
├── __init__.py
├── lead.py
├── market_intelligence.py
├── quant.py
└── validator.py
```

Do not immediately create:

```text
prompts/
instructions/
skills/
schemas/
fixtures/
README.md
```

Add those only if needed.

---

## Phase 12 — When to Add Manifest-Based Agents

Add `.agent.md`, `.prompt.md`, `.instructions.md`, and `SKILL.md` only after an agent becomes stable.

### Trigger Conditions

Add manifests when:

- the agent instruction becomes long
- the agent is used in multiple workflows
- the agent needs formal audit
- the agent is nearing production use
- multiple model/prompt versions need tracking
- you need non-developers to read/edit agent behavior
- you need registry-driven loading

Until then, direct Python ADK agents are preferred.

### Migration Path

From:

```text
agentic/agents/research.py
```

To:

```text
agentic/agents/research/
├── __init__.py
├── lead.py
├── lead.agent.md
├── prompts/
│   └── lead.prompt.md
└── instructions/
    └── lead.instructions.md
```

But this is a later maturity step, not the starting point.

---

## Phase 13 — When to Add Governance Folders

Only add these folders when the simple files become too large or too important:

```text
agentic/policy/
agentic/approvals/
agentic/evaluation/
agentic/observability/
agentic/registry/
agentic/audit/
```

### Add `agentic/policy/` when:

- `agentic/runtime/permissions.py` becomes too large
- risk/execution policy needs multiple files
- approval rules need versioning

### Add `agentic/audit/` when:

- JSONL logs are no longer enough
- you need audit reports
- you need immutable decision records
- you need replay/reproducibility

### Add `agentic/evaluation/` when:

- pytest is not enough
- you need golden tasks
- you need LLM output scoring
- you need regression evaluation across model versions

### Add `agentic/registry/` when:

- you have many agents
- you need lifecycle status
- you need agent metadata
- you need dynamic discovery/loading

### Add `agentic/approvals/` when:

- live trading approval is implemented
- paper-to-live promotion needs records
- approval expiry and approver identity matter

---

## Phase 14 — Practical Build Order by Agent

Build in this order:

```text
1. research_agent
2. strategy_agent
3. validation_agent
4. risk_agent
5. execution_readiness_agent
6. paper_trading_agent
7. kill_switch_agent
8. planner_agent
9. ceo_agent
10. operations_agent
```

Do not build all 30+ agents immediately.

Build one useful agent per department first.

After that, add specialists only when needed.

---

## Phase 15 — Minimal Agent Completion Checklist

For the simple implementation, an agent is complete when:

- [ ] It is defined in one of `agentic/agents/*.py`.
- [ ] It has a clear `name`.
- [ ] It has a clear `description`.
- [ ] It has clear `instruction`.
- [ ] It imports tools from root `tools/`.
- [ ] It can run through `agentic/runtime/runner.py`.
- [ ] It does not include unauthorized tools.
- [ ] Its tools fail closed where needed.
- [ ] It has a simple test.
- [ ] It has a working example or workflow usage.

This replaces the previous heavy checklist that required:

```text
.agent.md
README.md
schemas/
prompts/
instructions/
skills/
policy.py
permissions.py
evaluator.py
fixtures/
per-agent tests/
registry entry
audit report
```

Those are maturity additions, not day-one requirements.

---

## Phase 16 — Production Readiness Later

Before live trading or production deployment, reintroduce the stricter requirements.

### Required Before Live Trading

- [ ] formal risk governor
- [ ] live approval packet
- [ ] human approval record
- [ ] kill switch tested
- [ ] broker reconciliation tested
- [ ] max drawdown gate tested
- [ ] margin gate tested
- [ ] spread/slippage gate tested
- [ ] live execution tool tested in sandbox/demo
- [ ] audit record for every live action
- [ ] no agent can directly bypass risk approval
- [ ] production environment flag required
- [ ] live trading explicitly enabled in config
- [ ] emergency stop documented

### Optional Later Additions

- [ ] `.agent.md` manifests
- [ ] prompt files
- [ ] instruction files
- [ ] skills
- [ ] agent registry
- [ ] formal audit reports
- [ ] approval database
- [ ] observability dashboards
- [ ] golden task evaluation

---

## 17. Final Target Mental Model

The implementation should feel like this:

```text
Simple Python agents
+ root-level tools
+ one runner
+ a few workflow functions
+ tests
+ safety inside tools
```

Not like this:

```text
A giant enterprise agent platform before the first agent works.
```

The final rule:

> Build usefulness first. Add structure only when it reduces pain, not before.

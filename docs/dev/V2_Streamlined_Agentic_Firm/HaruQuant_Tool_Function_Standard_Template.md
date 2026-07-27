# HaruQuant Tool Function Standard Template

**Document purpose:** Standardize the anatomy, safety pattern, result envelope, and implementation style for all HaruQuant tool functions.

**Recommended location:** `docs/tool_function_standard.md`

**Applies to:** All tool functions in the root-level `tools/` folder.

---

## 1. Core Principle

Every HaruQuant tool should be:

- Simple to call from a Google ADK agent.
- Deterministic where possible.
- Safe by default.
- Fail-closed for trading and live execution.
- Traceable through request IDs and tool-call IDs.
- Auditable through a standard return envelope.
- Explicit about risk level, approval requirements, and side effects.

The goal is not to make tools complicated. The goal is to make every tool predictable, testable, and safe to expose to agents.

---

## 2. Standard Tool Function Anatomy

Every HaruQuant tool should follow this structure:

```text
1. Imports
2. Function signature with keyword-only arguments
3. Full docstring with:
   - purpose
   - tool class
   - risk level
   - approval requirement
   - side effects
   - inputs
   - returns
4. Create request/tool IDs
5. Validate inputs
6. Permission/safety gate
7. Dry-run path
8. Main logic
9. Error handling
10. Standard result dictionary
```

---

## 3. Standard Tool Classes

| Tool Class | Meaning | Example |
|---|---|---|
| `read_only` | Reads data only and does not mutate state | Get symbol metadata, read strategy spec |
| `write_safe` | Writes internal artifacts but does not affect trading state | Save research brief, create report |
| `write_controlled` | Runs jobs or changes workflow/internal state | Run backtest, run robustness test |
| `critical` | Can affect live trading, broker state, risk config, or safety systems | Place live order, reset kill switch |

---

## 4. Standard Risk Levels

| Risk Level | Meaning |
|---|---|
| `low` | No trading, financial, compliance, or system-integrity impact |
| `medium` | Creates internal artifacts, runs compute, or reads sensitive trading context |
| `high` | Affects strategy lifecycle, paper trading, portfolio recommendations, or risk posture |
| `critical` | Affects live capital, broker state, risk controls, credentials, or audit integrity |

---

## 5. Standard Approval Types

| Approval Type | Meaning |
|---|---|
| `none` | No approval required beyond agent permission |
| `audit_required` | Must be recorded in audit log |
| `risk_governor_required` | Requires deterministic RiskGovernor approval |
| `human_required` | Requires explicit Human Board approval |
| `human_and_risk_required` | Requires both Human Board and RiskGovernor approval |
| `forbidden` | Not allowed under normal workflows |

---

## 6. Standard Tool Result Envelope

Every tool should return this shape:

```python
{
    "status": "success | rejected | blocked | failed",
    "tool_name": "string",
    "tool_call_id": "uuid",
    "request_id": "uuid or external request id",
    "agent_name": "calling agent name",
    "environment": "local | development | test | paper | live",
    "dry_run": True,
    "data": {},
    "errors": [],
    "warnings": [],
    "audit": {
        "started_at": "timestamp",
        "finished_at": "timestamp",
        "side_effects": [],
        "approval_required": "none | audit_required | risk_governor_required | human_required | human_and_risk_required | forbidden",
        "risk_level": "low | medium | high | critical",
    },
}
```

---

## 7. Status Meaning

| Status | Meaning |
|---|---|
| `success` | Tool completed normally |
| `rejected` | Input was invalid or business rule failed |
| `blocked` | Permission, policy, approval, or safety gate blocked the action |
| `failed` | Unexpected runtime/system error occurred |

Use `rejected` for normal business validation failures.

Use `blocked` for safety or permission failures.

Use `failed` only for unexpected system errors.

---

## 8. Standard Generic Tool Template

```python
from __future__ import annotations

from typing import Any, Literal
from datetime import datetime, timezone
from uuid import uuid4


def tool_name(
    *,
    # Required business inputs
    symbol: str,
    timeframe: str | None = None,

    # Optional controls
    request_id: str | None = None,
    agent_name: str | None = None,
    dry_run: bool = True,
    environment: Literal["local", "development", "test", "paper", "live"] = "development",
) -> dict[str, Any]:
    """
    Short one-line summary of what this tool does.

    Purpose:
        Explain why this tool exists and what business capability it provides.

    Tool class:
        read_only | write_safe | write_controlled | critical

    Risk level:
        low | medium | high | critical

    Approval required:
        none | audit_required | risk_governor_required | human_required |
        human_and_risk_required | forbidden

    Side effects:
        Describe whether this tool reads data, writes files, starts jobs,
        changes lifecycle state, places orders, closes positions, etc.

    Inputs:
        symbol:
            Trading symbol, for example EURUSD, GBPJPY, XAUUSD.
        timeframe:
            Optional timeframe, for example M1, M5, H1, D1.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        dry_run:
            If True, validate and simulate only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections.
        Return status="rejected" instead.
        Raise only for programmer errors or unexpected system failures.
    """

    tool_call_id = str(uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    request_id = request_id or str(uuid4())

    errors: list[str] = []
    warnings: list[str] = []

    if not symbol:
        errors.append("symbol is required")

    if timeframe is not None and timeframe not in {
        "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"
    }:
        errors.append(f"Unsupported timeframe: {timeframe}")

    if errors:
        return {
            "status": "rejected",
            "tool_name": "tool_name",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": None,
            "errors": errors,
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "none",
                "risk_level": "low",
            },
        }

    if environment == "live":
        return {
            "status": "blocked",
            "tool_name": "tool_name",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": None,
            "errors": ["This tool is not allowed to run in live mode."],
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "human_required",
                "risk_level": "critical",
            },
        }

    try:
        result_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "message": "Tool completed successfully.",
        }
        side_effects: list[str] = []
        status = "success"

    except Exception as exc:
        return {
            "status": "failed",
            "tool_name": "tool_name",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": None,
            "errors": [str(exc)],
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "none",
                "risk_level": "low",
            },
        }

    return {
        "status": status,
        "tool_name": "tool_name",
        "tool_call_id": tool_call_id,
        "request_id": request_id,
        "agent_name": agent_name,
        "environment": environment,
        "dry_run": dry_run,
        "data": result_data,
        "errors": errors,
        "warnings": warnings,
        "audit": {
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "side_effects": side_effects,
            "approval_required": "none",
            "risk_level": "low",
        },
    }
```

---

## 9. Minimal Read-Only Tool Example

Use this pattern for tools that only read internal state, broker metadata, historical data, or reports.

```python
from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from uuid import uuid4


def get_symbol_metadata(
    *,
    symbol: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Read broker or internal metadata for a trading symbol.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.
    """

    tool_call_id = str(uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    request_id = request_id or str(uuid4())

    if not symbol:
        return {
            "status": "rejected",
            "tool_name": "get_symbol_metadata",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": True,
            "data": None,
            "errors": ["symbol is required"],
            "warnings": [],
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "none",
                "risk_level": "low",
            },
        }

    data = {
        "symbol": symbol,
        "pip_size": 0.0001,
        "tick_size": 0.00001,
        "contract_size": 100000,
        "min_lot": 0.01,
        "lot_step": 0.01,
    }

    return {
        "status": "success",
        "tool_name": "get_symbol_metadata",
        "tool_call_id": tool_call_id,
        "request_id": request_id,
        "agent_name": agent_name,
        "environment": environment,
        "dry_run": True,
        "data": data,
        "errors": [],
        "warnings": [],
        "audit": {
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "side_effects": [],
            "approval_required": "none",
            "risk_level": "low",
        },
    }
```

---

## 10. Controlled Tool Example

Use this pattern for backtests, optimization, robustness jobs, strategy lifecycle updates, and paper trading.

```python
from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from uuid import uuid4


def run_backtest(
    *,
    strategy_id: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    dry_run: bool = False,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Run a reproducible strategy backtest.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Creates a backtest result artifact.
    """

    tool_call_id = str(uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    request_id = request_id or str(uuid4())

    errors = []
    warnings = []

    if not strategy_id:
        errors.append("strategy_id is required")
    if not symbol:
        errors.append("symbol is required")
    if not timeframe:
        errors.append("timeframe is required")
    if not start_date:
        errors.append("start_date is required")
    if not end_date:
        errors.append("end_date is required")

    if errors:
        return {
            "status": "rejected",
            "tool_name": "run_backtest",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": None,
            "errors": errors,
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "audit_required",
                "risk_level": "medium",
            },
        }

    if environment == "live":
        return {
            "status": "blocked",
            "tool_name": "run_backtest",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": None,
            "errors": ["Backtests must not run in live execution environment."],
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "audit_required",
                "risk_level": "medium",
            },
        }

    if dry_run:
        return {
            "status": "success",
            "tool_name": "run_backtest",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": {
                "message": "Backtest request validated. No backtest executed because dry_run=True.",
                "strategy_id": strategy_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
            },
            "errors": [],
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "audit_required",
                "risk_level": "medium",
            },
        }

    result_id = f"bt_{tool_call_id}"

    return {
        "status": "success",
        "tool_name": "run_backtest",
        "tool_call_id": tool_call_id,
        "request_id": request_id,
        "agent_name": agent_name,
        "environment": environment,
        "dry_run": dry_run,
        "data": {
            "backtest_result_id": result_id,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
        },
        "errors": [],
        "warnings": warnings,
        "audit": {
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "side_effects": ["created_backtest_result"],
            "approval_required": "audit_required",
            "risk_level": "medium",
        },
    }
```

---

## 11. Critical Tool Example

Use this for live orders, kill switch reset, risk-threshold changes, broker connection, and permission changes.

```python
from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from uuid import uuid4


def place_live_order(
    *,
    strategy_id: str,
    symbol: str,
    side: str,
    volume: float,
    risk_approval_id: str | None,
    human_approval_id: str | None = None,
    live_enabled: bool = False,
    request_id: str | None = None,
    agent_name: str | None = None,
    dry_run: bool = True,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Submit a live order request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        risk_governor_required or human_and_risk_required depending context

    Side effects:
        May place a live broker order if all gates pass.

    Important:
        This tool must fail closed.
    """

    tool_call_id = str(uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    request_id = request_id or str(uuid4())

    errors = []
    warnings = []

    if not strategy_id:
        errors.append("strategy_id is required")
    if not symbol:
        errors.append("symbol is required")
    if side not in {"buy", "sell"}:
        errors.append("side must be 'buy' or 'sell'")
    if volume <= 0:
        errors.append("volume must be greater than 0")
    if not risk_approval_id:
        errors.append("risk_approval_id is required")
    if not live_enabled:
        errors.append("live_enabled must be true for live execution")

    if errors:
        return {
            "status": "blocked",
            "tool_name": "place_live_order",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": None,
            "errors": errors,
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "risk_governor_required",
                "risk_level": "critical",
            },
        }

    if environment != "live":
        return {
            "status": "blocked",
            "tool_name": "place_live_order",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": None,
            "errors": ["Live orders are only allowed in environment='live'."],
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "risk_governor_required",
                "risk_level": "critical",
            },
        }

    if dry_run:
        return {
            "status": "success",
            "tool_name": "place_live_order",
            "tool_call_id": tool_call_id,
            "request_id": request_id,
            "agent_name": agent_name,
            "environment": environment,
            "dry_run": dry_run,
            "data": {
                "message": "Live order validated but not submitted because dry_run=True.",
                "strategy_id": strategy_id,
                "symbol": symbol,
                "side": side,
                "volume": volume,
                "risk_approval_id": risk_approval_id,
                "human_approval_id": human_approval_id,
            },
            "errors": [],
            "warnings": warnings,
            "audit": {
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "side_effects": [],
                "approval_required": "risk_governor_required",
                "risk_level": "critical",
            },
        }

    # Real broker call should happen here only after:
    # - permission check
    # - risk approval token validation
    # - kill switch health check
    # - audit logger health check
    # - broker heartbeat check
    # - spread/news/session checks

    broker_order_id = f"live_order_{tool_call_id}"

    return {
        "status": "success",
        "tool_name": "place_live_order",
        "tool_call_id": tool_call_id,
        "request_id": request_id,
        "agent_name": agent_name,
        "environment": environment,
        "dry_run": dry_run,
        "data": {
            "broker_order_id": broker_order_id,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "side": side,
            "volume": volume,
            "risk_approval_id": risk_approval_id,
            "human_approval_id": human_approval_id,
        },
        "errors": [],
        "warnings": warnings,
        "audit": {
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "side_effects": ["submitted_live_order"],
            "approval_required": "risk_governor_required",
            "risk_level": "critical",
        },
    }
```

---

## 12. Practical Naming Rules

Use clear verb-based function names.

Good examples:

```text
get_symbol_metadata
get_historical_ohlcv
calculate_adr
calculate_spread_statistics
create_strategy_spec
run_backtest
run_robustness_test
request_risk_approval
place_paper_order
place_live_order
trigger_kill_switch
write_audit_event
```

Avoid vague names:

```text
process
handle
do_task
run
analyze
execute
helper
tool
```

---

## 13. Input Rules

Every tool should:

- Use keyword-only arguments with `*`.
- Validate all required fields.
- Return `rejected` for missing or invalid business inputs.
- Avoid silent defaults for risk-sensitive values.
- Avoid reading hidden global state unless explicitly documented.
- Include `request_id`, `agent_name`, `dry_run`, and `environment` where useful.

---

## 14. Output Rules

Every tool should:

- Return the standard result envelope.
- Keep `data` for business output only.
- Keep `errors` as a list of strings.
- Keep `warnings` as a list of strings.
- Include audit metadata.
- Include side effects.
- Never hide failed or blocked actions.

---

## 15. Safety Rules

Every tool should fail closed when:

- Required input is missing.
- Environment is unsafe.
- Live mode is disabled.
- Approval is missing.
- RiskGovernor approval is missing.
- Kill switch is unhealthy.
- Audit logger is unavailable.
- Broker heartbeat is unhealthy.
- Tool permissions are missing.
- Risk policy conditions are violated.

For trading tools, it is better to reject a valid trade than to allow an uncontrolled trade.

---

## 16. Exception Handling Rules

Normal business problems should not raise exceptions.

Return `rejected` or `blocked` instead.

Examples:

| Situation | Return |
|---|---|
| Missing symbol | `rejected` |
| Unsupported timeframe | `rejected` |
| Strategy not approved | `blocked` |
| Risk approval missing | `blocked` |
| Live mode disabled | `blocked` |
| Broker API crashed unexpectedly | `failed` |
| Programming bug | raise or return `failed` |

---

## 17. Dry-Run Rules

Tools that can create side effects should support `dry_run`.

Use `dry_run=True` as the default for:

- paper orders
- live orders
- lifecycle mutation
- strategy activation
- allocation changes
- broker connection
- risk-threshold changes
- kill-switch reset

Use `dry_run=False` only when the caller intentionally wants the action to happen and all gates pass.

---

## 18. Audit Rules

Every tool should record enough information to answer:

- Who called the tool?
- Which agent called it?
- What was requested?
- Was it approved, rejected, blocked, or failed?
- Did it create side effects?
- What evidence or approval ID was used?
- What risk level was involved?
- Was the environment live, paper, test, or development?

The tool result itself should contain audit metadata, even if the actual audit logger writes to a separate file.

---

## 19. Tool Implementation Checklist

Before a tool is considered complete:

- [ ] Function uses keyword-only arguments.
- [ ] Function has a clear docstring.
- [ ] Tool class is declared in docstring.
- [ ] Risk level is declared in docstring.
- [ ] Approval requirement is declared in docstring.
- [ ] Side effects are declared in docstring.
- [ ] Required inputs are validated.
- [ ] Unsafe environments are blocked.
- [ ] Dry-run path exists if the tool has side effects.
- [ ] Tool returns standard result envelope.
- [ ] Tool uses `success`, `rejected`, `blocked`, or `failed`.
- [ ] Audit metadata is included.
- [ ] Errors and warnings are lists.
- [ ] No secrets are returned.
- [ ] No hidden live actions happen.
- [ ] Unit tests cover success path.
- [ ] Unit tests cover rejected path.
- [ ] Unit tests cover blocked path.
- [ ] Unit tests cover failed path if relevant.

---

## 20. Minimal Unit Test Pattern

```python
def test_get_symbol_metadata_rejects_missing_symbol():
    result = get_symbol_metadata(symbol="")

    assert result["status"] == "rejected"
    assert "symbol is required" in result["errors"]


def test_run_backtest_dry_run_success():
    result = run_backtest(
        strategy_id="strategy_001",
        symbol="EURUSD",
        timeframe="H1",
        start_date="2024-01-01",
        end_date="2024-12-31",
        dry_run=True,
    )

    assert result["status"] == "success"
    assert result["dry_run"] is True
    assert result["audit"]["side_effects"] == []


def test_place_live_order_blocks_without_live_enabled():
    result = place_live_order(
        strategy_id="strategy_001",
        symbol="EURUSD",
        side="buy",
        volume=0.01,
        risk_approval_id="risk_001",
        live_enabled=False,
        environment="live",
    )

    assert result["status"] == "blocked"
    assert result["data"] is None
```

---

## 21. Recommended Final Rule

Use this rule for every HaruQuant tool:

```text
A tool should do one bounded thing, validate its inputs, enforce its safety assumptions, return a standard result, and never silently mutate important state.
```

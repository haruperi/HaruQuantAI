# HaruQuant Agent Auditing Checklist

> Production-ready audit checklist for HaruQuant Google ADK agents.

## Status

Aligned with:

- `Agentic_AI_Playbook_HaruQuant_Aligned.md`
- `HaruQuant_Agent_Standard.md`
- `HaruQuant_AI_Tool_Function_Standard.md`

## Purpose

This checklist verifies whether a HaruQuant agent is clear, safe, testable, auditable, registry-ready, and production-ready.

It is specifically designed for HaruQuant's current implementation direction:

```text
flat files first
Google ADK agents
few agents, many tools
strict contracts
deterministic policy gates
runtime + registry + policy + audit
unit tests and usage examples
folders only when earned
```

This audit applies to agents implemented under:

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
        registry.py
        policy.py
        audit.py
        contracts.py
        workflows.py
```

---

## 1. Document Relationship and Alignment

| Document                                          | Purpose                                                                         |
| :------------------------------------------------ | :------------------------------------------------------------------------------ |
| `Agentic_AI_Playbook_HaruQuant_Aligned.md`        | Broad architecture and operating model.                                         |
| `HaruQuant_Agent_Standard.md`                     | Implementation standard for Google ADK agents.                                  |
| `HaruQuant_AI_Tool_Function_Standard.md`          | Implementation standard for AI-callable tool functions.                         |
| `HaruQuant_Agent_Auditing_Checklist.md`           | Evidence checklist proving that an agent complies with the standards.           |
| `HaruQuant_Tool_Function_Auditing_Checklist.md`   | Evidence checklist proving that tool functions comply with the tool standard.   |

Rule:

```text
The Playbook defines the philosophy and architecture.
The Agent Standard defines how HaruQuant agents must be built.
The Tool Function Standard defines how HaruQuant tools must be built.
The Audit Checklists define the evidence required to prove compliance.
```

---

## 2. HaruQuant Agent Definition

For HaruQuant, an agent is:

```text
An LLM-powered decision unit built using Google ADK that interprets requests,
uses approved tools, reasons over evidence, produces structured decisions or
handoff packages, and operates under explicit permissions and deterministic
policy gates.
```

A function, validator, data fetcher, broker bridge, backtest runner, metric calculator, or file writer is **not** an agent unless it performs LLM-powered interpretation or decision-making.

---

## 3. Audit Scoring Guide

Each checklist item should be scored from `0` to `3`.

|   Score | Meaning                                               |
| ------: | :---------------------------------------------------- |
|       0 | Missing completely                                    |
|       1 | Mentioned but vague, informal, or incomplete          |
|       2 | Present, usable, and documented                       |
|       3 | Production-grade, implemented, tested, and enforced   |

The master score is normalized out of exactly `1000`.

```text
area_score = round((raw_points_earned / raw_points_available) * area_max_score)
```

### Completion Rating

|   Score Percentage | Rating             | Action                              |
| -----------------: | :----------------- | :---------------------------------- |
|            90–100% | Production-ready   | Approve                             |
|             80–89% | Strong             | Approve with minor improvements     |
|             70–79% | Usable             | Improve before staging/production   |
|             50–69% | Partial            | Refactor required                   |
|          Below 50% | Incomplete         | Redesign required                   |

Critical fail conditions override numeric score.

---

## 4. Critical Fail Conditions

An agent fails immediately if any item below is true.

| Critical Fail Condition                                                                  | Pass/Fail   | Evidence / Notes   |
| :--------------------------------------------------------------------------------------- | :---------- | :----------------- |
| Agent can place, close, modify, or activate live trades without explicit approval        |             |                    |
| Agent can bypass risk, policy, approval, or kill-switch gates                            |             |                    |
| Agent can use tools outside its `ALLOWED_TOOLS` list                                     |             |                    |
| Agent has unrestricted tool access                                                       |             |                    |
| Agent can call critical tools without deterministic approval checks                      |             |                    |
| Agent can approve its own high-risk or live-trading action                               |             |                    |
| Agent has no clear input contract                                                        |             |                    |
| Agent has no clear output contract                                                       |             |                    |
| Agent output is raw free-form text with no normalized runtime response                   |             |                    |
| Agent can invent backtest results, risk approvals, broker fills, or performance claims   |             |                    |
| Agent cannot distinguish evidence, assumptions, interpretation, and recommendation       |             |                    |
| Agent lacks audit logging for high-risk decisions                                        |             |                    |
| Agent lacks request_id/workflow_id traceability                                          |             |                    |
| Agent cannot safely stop after critical failure                                          |             |                    |
| Agent uses LLM judgment alone for safety-critical enforcement                            |             |                    |
| Agent ignores stale, missing, or conflicting evidence                                    |             |                    |
| Agent can override kill switch                                                           |             |                    |
| Agent has no tests                                                                       |             |                    |
| Agent has no usage example                                                               |             |                    |

---

## 5. Agent Identity and Metadata Checklist

| Check                                                     |   Yes/No |   Score | Evidence / Notes   |
| :-------------------------------------------------------- | -------: | ------: | :----------------- |
| Agent has `AGENT_NAME`                                    |          |         |                    |
| Agent has `AGENT_VERSION`                                 |          |         |                    |
| Agent has `AGENT_DEPARTMENT`                              |          |         |                    |
| Agent has `AGENT_DESCRIPTION`                             |          |         |                    |
| Agent has `AGENT_RISK_LEVEL`                              |          |         |                    |
| Agent has `AGENT_REQUIRES_APPROVAL`                       |          |         |                    |
| Agent has `AGENT_INPUT_CONTRACT` where applicable         |          |         |                    |
| Agent has `AGENT_OUTPUT_CONTRACT`                         |          |         |                    |
| Agent purpose is clear from metadata                      |          |         |                    |
| Agent name matches its responsibility                     |          |         |                    |
| Agent does not overlap confusingly with another agent     |          |         |                    |
| Agent has owner/responsible maintainer where applicable   |          |         |                    |

Pass condition:

```text
A developer can understand the agent's identity, role, department, and risk level without reading the full implementation.
```

---

## 6. File-Level Standard Checklist

| Check                                                            |   Yes/No |   Score | Evidence / Notes   |
| :--------------------------------------------------------------- | -------: | ------: | :----------------- |
| Agent file starts with file-level docstring                      |          |         |                    |
| File docstring lists agents defined in the file                  |          |         |                    |
| File docstring lists builder functions                           |          |         |                    |
| File docstring lists allowed tool domains                        |          |         |                    |
| File docstring lists output contracts                            |          |         |                    |
| File docstring states risk level range                           |          |         |                    |
| File imports `logging`                                           |          |         |                    |
| File defines `logger = logging.getLogger(__name__)`              |          |         |                    |
| File does not execute agent runs at import time                  |          |         |                    |
| File does not call tools during import or builder construction   |          |         |                    |
| File does not mutate external state during import                |          |         |                    |

---

## 7. Agent Builder Checklist

| Check                                                                   |   Yes/No |   Score | Evidence / Notes   |
| :---------------------------------------------------------------------- | -------: | ------: | :----------------- |
| Builder function exists                                                 |          |         |                    |
| Builder function name follows `build_<agent_name>_agent()`              |          |         |                    |
| Builder returns `google.adk.agents.Agent`                               |          |         |                    |
| Builder uses metadata constants                                         |          |         |                    |
| Builder uses explicit `AGENT_DESCRIPTION`                               |          |         |                    |
| Builder uses explicit instruction string or loaded instruction          |          |         |                    |
| Builder uses `ALLOWED_TOOLS`                                            |          |         |                    |
| Builder has a detailed docstring                                        |          |         |                    |
| Builder logs construction                                               |          |         |                    |
| Builder does not call tools                                             |          |         |                    |
| Builder does not mutate files, DB, broker state, or external services   |          |         |                    |
| Builder can be imported and constructed in a unit test                  |          |         |                    |

---

## 8. Instruction Completeness Checklist

Every instruction must include the required sections from the Agent Standard.

| Required Instruction Section   |   Present? |   Score | Evidence / Notes   |
| :----------------------------- | ---------: | ------: | :----------------- |
| Role                           |            |         |                    |
| Responsibilities               |            |         |                    |
| Non-Goals                      |            |         |                    |
| Allowed Tools                  |            |         |                    |
| Blocked Actions                |            |         |                    |
| Required Evidence              |            |         |                    |
| Output Contract                |            |         |                    |
| Safety Rules                   |            |         |                    |
| Uncertainty Behavior           |            |         |                    |
| Escalation Rules               |            |         |                    |

Additional checks:

| Check                                                   |   Yes/No |   Score | Evidence / Notes   |
| :------------------------------------------------------ | -------: | ------: | :----------------- |
| Instruction prevents invented data/results              |          |         |                    |
| Instruction tells agent to disclose missing evidence    |          |         |                    |
| Instruction tells agent to disclose stale evidence      |          |         |                    |
| Instruction tells agent to escalate high-risk actions   |          |         |                    |
| Instruction aligns with declared permissions            |          |         |                    |
| Instruction aligns with output contract                 |          |         |                    |
| Instruction aligns with allowed/blocked tools           |          |         |                    |

---

## 9. Permission Declaration Checklist

| Check                                                 |   Yes/No |   Score | Evidence / Notes   |
| :---------------------------------------------------- | -------: | ------: | :----------------- |
| Agent declares whether it can read market data        |          |         |                    |
| Agent declares whether it can read research data      |          |         |                    |
| Agent declares whether it can create strategy specs   |          |         |                    |
| Agent declares whether it can modify strategy code    |          |         |                    |
| Agent declares whether it can run backtests           |          |         |                    |
| Agent declares whether it can run optimization        |          |         |                    |
| Agent declares whether it can write files             |          |         |                    |
| Agent declares whether it can modify database state   |          |         |                    |
| Agent declares whether it can review risk             |          |         |                    |
| Agent declares whether it can approve risk            |          |         |                    |
| Agent declares whether it can request paper trading   |          |         |                    |
| Agent declares whether it can request live trading    |          |         |                    |
| Agent declares whether it can place trades            |          |         |                    |
| Agent declares whether it can close trades            |          |         |                    |
| Agent declares whether it can activate kill switch    |          |         |                    |
| Agent declares `CAN_OVERRIDE_KILL_SWITCH = False`     |          |         |                    |
| Permissions match the real attached tools             |          |         |                    |
| Permissions are validated by policy layer             |          |         |                    |

---

## 10. Allowed Tools and Blocked Tools Checklist

| Check                                                                      |   Yes/No |   Score | Evidence / Notes   |
| :------------------------------------------------------------------------- | -------: | ------: | :----------------- |
| `ALLOWED_TOOLS` exists                                                     |          |         |                    |
| `BLOCKED_TOOL_NAMES` exists                                                |          |         |                    |
| Every tool in `ALLOWED_TOOLS` is imported from a tool domain package       |          |         |                    |
| No deep tool imports are used unless justified                             |          |         |                    |
| Attached ADK tools exactly match `ALLOWED_TOOLS`                           |          |         |                    |
| No blocked tool is attached                                                |          |         |                    |
| Agent cannot access execution tools unless execution role requires it      |          |         |                    |
| Agent cannot access live trading tools unless critical role and approved   |          |         |                    |
| Tool side-effect metadata matches agent permissions                        |          |         |                    |
| Policy validates allowed tool list                                         |          |         |                    |
| Tool failure behavior is defined                                           |          |         |                    |
| High-risk/critical tool access requires approval                           |          |         |                    |

---

## 11. Input Contract Checklist

| Check                                                         |   Yes/No |   Score | Evidence / Notes   |
| :------------------------------------------------------------ | -------: | ------: | :----------------- |
| `AGENT_INPUT_CONTRACT` is declared where needed               |          |         |                    |
| Required inputs are documented                                |          |         |                    |
| Optional inputs are documented                                |          |         |                    |
| Missing input behavior is defined                             |          |         |                    |
| Invalid input behavior is defined                             |          |         |                    |
| Agent can return `needs_clarification`                        |          |         |                    |
| Agent refuses unsafe vague requests                           |          |         |                    |
| Agent validates environment context before high-risk action   |          |         |                    |
| Agent does not silently guess important inputs                |          |         |                    |

---

## 12. Output Contract Checklist

| Check                                                                     |   Yes/No |   Score | Evidence / Notes   |
| :------------------------------------------------------------------------ | -------: | ------: | :----------------- |
| `AGENT_OUTPUT_CONTRACT` is declared                                       |          |         |                    |
| Output follows normalized agent response schema                           |          |         |                    |
| Output includes `status`                                                  |          |         |                    |
| Output includes `message`                                                 |          |         |                    |
| Output includes `data`                                                    |          |         |                    |
| Output includes `decision` where relevant                                 |          |         |                    |
| Output includes `evidence`                                                |          |         |                    |
| Output includes `tool_calls`                                              |          |         |                    |
| Output includes structured `error` when failed                            |          |         |                    |
| Output includes `metadata`                                                |          |         |                    |
| Output can be consumed by downstream workflow                             |          |         |                    |
| Output separates facts, assumptions, interpretation, and recommendation   |          |         |                    |
| Runtime validates output contract                                         |          |         |                    |

---

## 13. Runtime, Registry, and Policy Checklist

| Check                                            |   Yes/No |   Score | Evidence / Notes   |
| :----------------------------------------------- | -------: | ------: | :----------------- |
| Agent is runnable through `agentic/runtime.py`   |          |         |                    |
| Runtime validates `request_id`                   |          |         |                    |
| Runtime validates `workflow_id`                  |          |         |                    |
| Runtime normalizes raw ADK output                |          |         |                    |
| Runtime captures tool calls where possible       |          |         |                    |
| Agent is registered in `agentic/registry.py`     |          |         |                    |
| Unknown agent fails clearly                      |          |         |                    |
| Policy validates allowed tools                   |          |         |                    |
| Policy validates agent permissions               |          |         |                    |
| Policy requires evidence for handoff             |          |         |                    |
| Policy requires approval for live action         |          |         |                    |
| Policy blocks kill-switch override               |          |         |                    |
| Policy fails closed when uncertain               |          |         |                    |

---

## 14. Evidence, Approval, and Handoff Checklist

| Check                                                        |   Yes/No |   Score | Evidence / Notes   |
| :----------------------------------------------------------- | -------: | ------: | :----------------- |
| Agent records evidence used                                  |          |         |                    |
| Agent separates evidence from interpretation                 |          |         |                    |
| Agent marks assumptions clearly                              |          |         |                    |
| Agent discloses missing evidence                             |          |         |                    |
| Agent discloses stale evidence                               |          |         |                    |
| Agent discloses conflicting evidence                         |          |         |                    |
| Agent knows when approval is required                        |          |         |                    |
| Agent can request approval but not self-approve              |          |         |                    |
| Live trading requires explicit approval                      |          |         |                    |
| Missing/expired approval fails closed                        |          |         |                    |
| Agent belongs to a workflow or is intentionally standalone   |          |         |                    |
| Handoff preserves `request_id` and `workflow_id`             |          |         |                    |
| Agent can reject poor-quality handoff input                  |          |         |                    |

---

## 15. Logging and Audit Footprint Checklist

| Check                                                 |   Yes/No |   Score | Evidence / Notes   |
| :---------------------------------------------------- | -------: | ------: | :----------------- |
| Agent builder logs construction                       |          |         |                    |
| Runtime logs agent run started                        |          |         |                    |
| Runtime logs request_id                               |          |         |                    |
| Runtime logs workflow_id                              |          |         |                    |
| Runtime logs agent name/version                       |          |         |                    |
| Runtime logs allowed tools                            |          |         |                    |
| Runtime logs tool calls                               |          |         |                    |
| Runtime logs policy result                            |          |         |                    |
| Runtime logs output contract                          |          |         |                    |
| Runtime logs completion/failure/blocked actions       |          |         |                    |
| Audit record includes timestamp                       |          |         |                    |
| Audit record includes request_id/workflow_id          |          |         |                    |
| Audit record includes agent name/version/department   |          |         |                    |
| Audit record includes evidence references             |          |         |                    |
| Audit record includes decision and policy result      |          |         |                    |
| Audit record includes approval requirement            |          |         |                    |
| Logs and audit redact secrets                         |          |         |                    |

---

## 16. Unit Testing Checklist

Recommended location:

```text
tests/unit/agentic/agents/{department}/test_{agent_file}.py
```

| Check                                              |   Yes/No |   Score | Evidence / Notes   |
| :------------------------------------------------- | -------: | ------: | :----------------- |
| Unit test file exists                              |          |         |                    |
| Builder construction test exists                   |          |         |                    |
| Agent name/description test exists                 |          |         |                    |
| Instruction existence test exists                  |          |         |                    |
| Instruction completeness test exists               |          |         |                    |
| Metadata constants test exists                     |          |         |                    |
| Permission declaration test exists                 |          |         |                    |
| Allowed/blocked tools tests exist                  |          |         |                    |
| Output contract test exists                        |          |         |                    |
| Registry test exists                               |          |         |                    |
| No construction side effects test exists           |          |         |                    |
| High-risk approval tests exist where needed        |          |         |                    |
| Kill-switch/fail-closed tests exist where needed   |          |         |                    |

---

## 17. Usage Example and Evaluation Checklist

Recommended usage location:

```text
tests/usage/agentic/agents/{department}/{agent_name}.py
```

Recommended eval location:

```text
tests/evals/agentic/{department}/test_{agent_name}_eval.py
```

| Check                                                        |   Yes/No |   Score | Evidence / Notes   |
| :----------------------------------------------------------- | -------: | ------: | :----------------- |
| Usage example exists                                         |          |         |                    |
| Usage uses realistic prompt                                  |          |         |                    |
| Usage calls through `agentic.runtime`                        |          |         |                    |
| Usage includes `request_id` and `workflow_id`                |          |         |                    |
| Usage inspects normalized response                           |          |         |                    |
| Evaluation tests exist where needed                          |          |         |                    |
| Missing input scenario exists                                |          |         |                    |
| Missing/stale/conflicting evidence scenarios exist           |          |         |                    |
| Unsafe live trading request scenario exists where relevant   |          |         |                    |
| Policy bypass attempt scenario exists                        |          |         |                    |
| Tool failure scenario exists                                 |          |         |                    |
| Blocked tool request scenario exists                         |          |         |                    |

---

## 18. HaruQuant Trading Safety Checklist

Mandatory for trading-related agents.

| Check                                                                                      |   Yes/No |   Score | Evidence / Notes   |
| :----------------------------------------------------------------------------------------- | -------: | ------: | :----------------- |
| Agent distinguishes research, strategy, validation, risk, and execution responsibilities   |          |         |                    |
| Agent does not treat backtest result as live result                                        |          |         |                    |
| Agent does not treat paper trading as live approval                                        |          |         |                    |
| Agent respects RiskGovernor decisions                                                      |          |         |                    |
| Agent respects portfolio-level constraints                                                 |          |         |                    |
| Agent requires validation evidence before risk approval                                    |          |         |                    |
| Agent requires risk approval before execution                                              |          |         |                    |
| Agent cannot trigger live execution without full approval chain                            |          |         |                    |
| Agent discloses data limitations and uncertainty                                           |          |         |                    |

---

## 19. Master Audit Summary

| Area                                   | Includes Sections   |   Max Score |   Actual Score | Pass/Fail   | Evidence / Notes   |
| :------------------------------------- | :------------------ | ----------: | -------------: | :---------- | :----------------- |
| Critical Fail Conditions               | Section 4           |    Required |                |             |                    |
| Identity, File, Builder, Instruction   | Sections 5–8        |         160 |                |             |                    |
| Permissions, Tools, Contracts          | Sections 9–12       |         200 |                |             |                    |
| Runtime, Registry, Policy              | Section 13          |         140 |                |             |                    |
| Evidence, Approval, Handoff            | Section 14          |         130 |                |             |                    |
| Logging and Audit                      | Section 15          |         130 |                |             |                    |
| Tests, Usage, Evaluation               | Sections 16–17      |         160 |                |             |                    |
| Trading Safety                         | Section 18          |          80 |                |             |                    |
| **Total**                              |                     |    **1000** |                |             |                    |

---

## 20. Audit Decision Rule

An agent is production-ready only if:

1. It passes all critical fail conditions.
1. It scores at least 90%.
1. It has a valid builder.
1. It is registered.
1. It has explicit metadata.
1. It has explicit permissions.
1. It has allowed tools and blocked tools.
1. It has an output contract.
1. It has logging and audit footprint where required.
1. It has unit tests.
1. It has usage examples.
1. It has policy tests where relevant.
1. It has evaluation scenarios where relevant.
1. It passes CI or the relevant quality gate.

For high-risk and critical agents, also require:

1. Approval checks.
1. Kill-switch awareness.
1. Fail-closed behavior.
1. Evidence enforcement.
1. Deterministic policy gates.
1. Production action blocking by default.

---

## 21. Recommended Audit Workflow

1. Locate source file, builder, registry entry, instruction, contracts, tools, tests, usage examples, and workflows.
1. Run critical fail review.
1. Score checklist sections.
1. Run unit tests:

```bash
pytest tests/unit/agentic/agents -q
```

1. Run runtime, registry, policy, and contract tests:

```bash
pytest tests/unit/agentic -q
```

1. Run evaluations where applicable:

```bash
pytest tests/evals/agentic -q
```

1. Record final decision:

```text
Approved
Approved with minor fixes
Needs refactor
Rejected / redesign required
```

---

## 22. Agent Audit Report Template

```markdown
# Agent Audit Report: <agent_name>

## 1. Agent Summary
## 2. Critical Fail Review
## 3. Metadata Review
## 4. Builder Review
## 5. Instruction Review
## 6. Permissions Review
## 7. Tool Access Review
## 8. Contract Review
## 9. Runtime and Registry Review
## 10. Policy and Approval Review
## 11. Logging and Audit Review
## 12. Unit Test Review
## 13. Usage Example Review
## 14. Evaluation Review
## 15. Trading Safety Review
## 16. Master Score
## 17. Decision
## 18. Required Remediation
```

---

## 23. Definition of Done

An agent audit is complete only when:

```text
[ ] Critical fail conditions reviewed
[ ] Full checklist scored
[ ] Evidence recorded
[ ] Tests checked
[ ] Usage examples checked
[ ] Runtime/registry/policy checked
[ ] Risk/approval behavior checked
[ ] Audit report written
[ ] Final decision recorded
[ ] Remediation tasks created if needed
```

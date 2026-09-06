# Firm Organization and Deliberation

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-004`–`006`, `019`–`021`

## Organization without implicit authority

The Firm Coordinator and Research Planner give the system a recognizable
CEO/CIO-and-desk operating model. Departments group expertise and review duties.
Capabilities, mandate, permissions, and receiver domains—not titles—determine what
can happen.

The coordinator reports status and composes workflows. It cannot approve risk,
promotion, portfolio activation, or execution.

## Organization-to-package mapping

The organization is represented by a hybrid package structure. Shared control-plane
features remain focused top-level packages; registered role-bearing features are
leaf packages under `app/agentic/agents/<department>/<agent_name>/`.

| Organizational area | Owning package boundary |
|---|---|
| Executive coordination | `governance/`, `orchestration/`, and `deliberation/`; no separate authority-bearing executive package |
| Market intelligence | `agents/market_intelligence/fundamental_analyst/` and `agents/market_intelligence/sentiment_analyst/` |
| Market analysis | `agents/market_analysis/technical_analyst/` and `agents/market_analysis/quantitative_analyst/` |
| Strategy desk | `agents/strategy_desk/strategy_thesis_analyst/` and `agents/strategy_desk/trader/` |
| Experimentation | `agents/experimentation/simulation_interpreter/`, `experiment_designer/`, and `optimization_coordinator/` |
| Engineering | `agents/engineering/coder/` |
| Portfolio and risk advisory | `agents/portfolio_risk_advisory/portfolio_risk_advisor/` |
| Operations | `operations/` owns deterministic operational control; `agents/operations/evaluation_manager/` owns the role-bearing evaluation feature |

The Feature Registry maps each role-bearing capability to exactly one leaf package.
A leaf `agent.py` may instantiate more than one enabled `RoleManifest` when the
canonical capability includes several professional roles, but it does not duplicate
feature behaviour. The package-local `prompt.md` supplies the immutable base
instruction; each manifest supplies its bounded role-specific instruction and
identity. All hashes are validated and recorded.

## Discussion topology

The planner selects roles according to task classification, asset class, evidence
availability, evaluation status, conflicts of interest, and budget.

```text
request
  → independent relevant analysts in parallel
    → proposer
      → assigned bull/constructive and bear/adversarial challengers
        → bounded rebuttal
          → deterministic evidence checks
            → synthesizer preserving dissent
              → typed output or insufficient_evidence
```

Bull/bear roles are challenge stances for one task, not standing beliefs. A role
cannot serve as both sole proposer and sole judge for a governed outcome. Temporary
challenge stances do not create new packages, prompts, permissions, or standing
roles; deliberation records the assigned stance and its originating registered
role.

## Message types

- `brief`
- `claim`
- `counterclaim`
- `evidence_request`
- `tool_evidence`
- `rebuttal`
- `dissent`
- `synthesis`
- `refusal`

Messages are typed artefacts, not unrestricted chat. Every message has sender,
recipient, task, round, evidence references, timestamp, schema, and hash.

## Stop conditions

The workflow stops on objective completion, insufficient evidence, material
unresolved conflict, maximum rounds, deadline, budget, policy denial, incident, or
operator cancellation. More discussion is not an automatic remedy for uncertainty.

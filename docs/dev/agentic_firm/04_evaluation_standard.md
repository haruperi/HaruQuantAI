# Agentic Evaluation Standard

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-009`, `049`–`051`;
> `NFR-AGENTIC-003`, `007`, `008`

## Evaluation dimensions

Every role, model profile, prompt, tool, workflow, and council topology is evaluated
against a versioned baseline.

| Dimension | Required evidence |
|---|---|
| Contract reliability | Strict-schema success, refusal correctness, invalid-output containment |
| Factual grounding | Claim-to-source precision, availability-time correctness, unsupported-claim rate |
| Tool correctness | Correct selection, arguments, authorization, idempotency, and result interpretation |
| Safety | Injection, poisoning, privilege, secret, approval, exfiltration, and runaway-work cases |
| Reasoning utility | Human rubric, falsifiability, counterclaim quality, uncertainty, preserved dissent |
| Reproducibility | Model/prompt/tool/data/policy/configuration lineage and replay comparison |
| Economic value | Decision-relevant improvement over deterministic and single-agent baselines |
| Operational quality | Latency, cost, retries, failure rate, recovery, trace completeness |

## Mandatory evaluation sets

- Golden deterministic cases
- Difficult and ambiguous cases
- Refusal and missing-evidence cases
- Point-in-time and leakage cases
- Prompt-, memory-, peer-, and tool-injection cases
- Poisoned or contradictory source cases
- Authorization and approval-forgery cases
- Provider/model regression cases
- Null-data and random-label controls
- Historical regime, stress, and out-of-distribution cases

## Council ablation

Each multi-agent workflow is compared with:

1. Deterministic-only baseline
2. Best single-agent baseline
3. Full council
4. Council with each role removed in turn
5. Council without peer visibility

A role or discussion round is removed if its incremental, uncertainty-adjusted
benefit does not exceed its latency, cost, and new failure surface.

## Grading

Deterministic graders judge schemas, calculations, citations, permissions, and
known outcomes. Human graders use versioned rubrics and record inter-rater
agreement. Model graders are calibrated against human labels and never grade their
own promotion in isolation.

No fixed threshold becomes production policy merely because it appears in this
document. Thresholds are mandatory configuration values supported by validation
evidence and approved through the normal change process.

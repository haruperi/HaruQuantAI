# Agentic Observability and Operations

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-061`–`066`;
> `NFR-AGENTIC-002`, `004`, `005`

## Trace model

One correlation tree links:

`public request → workflow run → task/node → agent/model → tool/receiver →
handoff/approval → result/state transition`.

Each span records safe IDs, versions, status, timestamps, duration, retry, tokens,
cost, cache, schema result, policy decision, evidence count, and failure category.
Prompts, credentials, personal data, account secrets, and unrestricted trading
payloads are not captured by default.

## Metrics and SLO categories

- Availability and successful terminal rate
- Refusal and failure categories
- Queue, node, model, tool, and end-to-end latency
- Token, call, cost, fan-out, and discussion-round usage
- Schema, citation, grounding, permission, injection, and evaluation rates
- Retry, timeout, cancellation, recovery, and checkpoint age
- Provider/model drift and regression
- Sandbox and promotion-gate outcomes

Exact SLO thresholds are required deployment configuration supported by measured
baselines; no hidden defaults are permitted.

## Operational controls

Operators can inspect, cancel, quarantine, disable, replay in isolation, approve a
handoff, revoke an approval, and export an evidence packet through authenticated
UI/API paths. Every operation is audited.

## Replay and recovery

Replay pins immutable inputs and runs in a side-effect-free environment. Recovery
resumes only from committed checkpoints, reconciles ambiguous receiver outcomes
before retry, and never repeats an external mutation blindly.

Runbooks cover provider outage, runaway spend, injection, poisoned data, permission
misconfiguration, schema regression, stalled workflow, sandbox escape attempt,
approval compromise, and cross-account leakage.

Telemetry names and semantic fields should align where practical with the
[OpenTelemetry generative-AI semantic conventions](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)
without enabling sensitive content capture by default.

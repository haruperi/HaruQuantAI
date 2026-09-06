# Agentic Firm Mandate Specification

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-004`–`006`

## Purpose

`FirmMandate` is the immutable, versioned operating envelope for one Agentic
deployment. Startup fails closed when the mandate is absent, invalid, expired, or
incompatible with runtime configuration.

## Required fields

| Field | Meaning |
|---|---|
| `mandate_id`, `version`, `content_hash` | Stable identity and integrity |
| `environment` | `development`, `sandbox`, `demo`, or separately approved `live` |
| `effective_at`, `expires_at` | UTC validity |
| `owner_principal` | Authenticated mandate owner |
| `objectives` | Permitted research and advisory objectives |
| `asset_scopes` | Asset classes, venues, instruments, accounts, and exclusions |
| `enabled_features` | Canonical `FEAT-AGT-*` capabilities |
| `enabled_roles` | Versioned role manifests |
| `model_profiles` | Approved provider/model profiles by capability |
| `tool_scopes` | Tool/version, permission class, data/account/environment scope |
| `workflow_limits` | Participants, fan-out, rounds, retries, deadlines, concurrency |
| `budgets` | Token, call, tool, cost, compute, storage, and lifetime-search limits |
| `approval_policy` | Actions requiring human or deterministic-domain approval |
| `retention_policy` | Evidence, audit, working-memory, and incident retention |
| `prohibited_actions` | Explicit universal denials |
| `fallback_policy` | Refuse, degrade, cancel, or safe-drain behaviour |

## Universal prohibitions

Every mandate denies:

- Broker credentials and broker-native mutation tools
- Mandate modification or override by an agent
- Kill-switch clearing by an agent
- Self-approval and approval delegation to an agent
- Production code mutation or hot loading
- Unbounded discussion, retry, search, memory, or spend
- Use of unavailable, unlicensed, stale, or unverified evidence
- Treating a proposal receipt as an order, fill, or approval

## Environment behaviour

- `development`: fake or local dependencies; no external consequential mutations.
- `sandbox`: isolated provider/data/tool integration against non-production targets.
- `demo`: deterministic demo trading may consume approved proposals through its
  normal pipeline.
- `live`: Agentic may submit typed proposals only when an independently approved
  system configuration permits it. All receiver-domain and human controls remain
  mandatory.

## Precedence

When rules conflict, the stricter result wins:

`kill switch → law/venue/broker constraints → Risk mandate → system configuration → FirmMandate → workflow → role → tool → model output`.

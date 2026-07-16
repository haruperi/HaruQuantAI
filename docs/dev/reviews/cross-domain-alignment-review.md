# Cross-Domain Alignment Review

- **Review date:** 2026-07-15
- **Scope:** `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `app/utils/README.md`, and all service READMEs
- **Readiness verdict:** **Ready for implementation**

## Outcome

The blocking ownership, dependency, contract-registration, safety-command, scope,
audit, and workflow conflicts are resolved in the authoritative documentation.
Implementation may proceed by domain slice, subject to each README's requirements,
approval gates, targeted verification, and unchanged fail-closed safety rules.

This verdict means the target documents are mutually implementable. It does not mark
any domain implementation `Completed`; domain status changes still require the code,
tests, coverage, and validation evidence required by that domain README.

## Resolution Matrix

| Finding | Resolution | Authoritative evidence |
|---|---|---|
| `ALIGN-001` credential/security ownership | UI/API owns password hashing, credential encryption/persistence, active-key selection, reference resolution, and Brokers config composition; Utils retains shared redaction and other multi-domain primitives | `docs/PROJECT.md`; Utils and UI/API READMEs |
| `ALIGN-002` Portfolio dependency cycles | Risk and Simulation consume self-contained receiver-owned projections and never import Portfolio-owned contract types | PROJECT contract table; Risk, Simulation, and Portfolio READMEs |
| `ALIGN-003` unregistered results | Registered `StrategyMutationResult v1`, `ScenarioResult v1`, and `OperationalEvent v1`; Risk/Research internal results remain internal | PROJECT contract table; Strategy, Risk, Trading, Research, and UI/API READMEs |
| `ALIGN-004` kill-switch command ambiguity | Explicit global/portfolio/strategy/symbol scope; authorized activation; clearance additionally requires matching current attestation; active/unknown parent blocks | `SYS-WF-005`; PROJECT contract table; Risk and UI/API READMEs |
| `ALIGN-005` unowned UI/API capabilities | Raw strategy/SQX import/export/parsing/scoring/artifacts and documentation file management removed from initial scope | PROJECT and UI/API README |
| `ALIGN-006` audit producer mismatch | Exact producer set: Data, Strategy, Risk, Trading, Simulation, Optimization, Research, Portfolio, UI/API; Brokers logs only; Indicators/Analytics pure/read-only | PROJECT/Architecture audit policy and domain READMEs |
| `ALIGN-007` incomplete rebalance measurement | `SYS-WF-008` ends with Analytics measurement from immutable Trading facts; failure preserves executed-but-unmeasured truth and deterministic recomputation | PROJECT, Analytics, Portfolio, and Trading READMEs |
| `ALIGN-008` workflow participation/citations | `SYS-WF-006` and `SYS-WF-007` chains and Data/Strategy participation aligned | PROJECT, Data, Strategy, Portfolio, Risk READMEs |
| `ALIGN-009` shared configuration mismatch | `ALLOW_LIVE_MUTATIONS` is a Trading execution gate consumed by Trading/Portfolio/UI/API; database path types are `str` / `Path` | PROJECT and affected domain READMEs |
| `ALIGN-010` unregistered persisted/UI state | Removed documentation/SQX state claims and classified browser state as non-authoritative, non-persisted runtime state | PROJECT and UI/API README |

## Implementation Boundaries

- Commands/requests are receiver-owned; events/results are producer-owned.
- Cross-domain compatibility uses `contract_version`, not parsed `schema_id`.
- Risk remains the policy authority; Trading remains the execution authority;
  Brokers remains the provider adapter boundary.
- Missing, stale, unknown, unauthorized, or unverifiable safety evidence fails closed.
- No production code, live broker mutation, risk-policy change, or invented trading
  rule was introduced by this documentation alignment.

## Validation Checklist

- [x] Domain registry, contract table, workflow chains, and domain READMEs use the same owners and counterparties.
- [x] Direct `Risk → Portfolio` and `Simulation → Portfolio` contract dependencies are absent.
- [x] Credential ownership is single-valued and no removed Utils helper remains in the target surface.
- [x] Kill-switch scope, activation, clearance, hierarchy, and recovery semantics agree.
- [x] Initial UI/API routes/state exclude raw strategy/SQX and documentation-file capabilities.
- [x] Audit producer policy and exceptions are explicit.
- [x] `SYS-WF-008` preserves execution truth through Analytics failure.
- [x] Status-label definitions and implementation-state wording do not promote unverified code.
- [x] Accepted decisions are ordinary requirements; resolution history is in the changelog/ADR.

## Residual Risks

The remaining risks are implementation risks, not architecture blockers: exact library
constraints must be confirmed from `pyproject.toml` before coding; every domain must
add producer-consumer compatibility tests; encryption-key infrastructure must be
provided externally; and live behavior remains disabled until all deterministic gates
and environment-specific verification are complete.

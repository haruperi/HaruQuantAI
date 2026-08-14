# Parity Comparison (`FEAT-SIM-18`)

> **Feature:** `FEAT-SIM-18` Parity Comparison
> **Status:** `Completed` (programme Phase 2)
> **Module:** `app/services/simulator/parity/`

Owns the versioned **Parity Envelope**, the relationship-preserving evidence
normalizer, and the parity comparator. Parity is a falsifiable certification
over a versioned matrix — never a universal claim — and only a completed L5
certificate may make the bounded claim recorded in its immutable envelope.

## Public API (package root only)

All operations are exposed only through `app.services.simulator`:

- `get_parity_envelope(version="v1")` — published envelope mapping.
- `get_parity_maturity_ladder()` — the L1–L4 rungs plus distinct L5-Demo and
  L5-Live certificates.
- `normalize_parity_evidence(evidence, envelope)` — alpha-renamed,
  relationship-preserving normalized view with a canonical digest.
- `compare_parity_evidence(left, right, envelope)` — per-invariant results,
  aggregate account-currency economic error, deterministic ordered failures,
  certificate invalidation flag.

Failures raise cataloged `SimulationError` codes only (`SIM_INVALID_CONFIG`
for unknown envelopes, malformed evidence, unregistered fields, and scope
violations; `SIM_INTEGRITY_FAILURE` for broken identifier references).

## Envelope v1

Targets MT5-FX demo scope (`certificate_target=demo`, provider `mt5`,
`genuine_bid_ask_ticks` evidence class). Numeric invariants use exact zero
tolerance (exact `Decimal` equality); the aggregate economic-error budget is
`0`. Distributional invariants (`latency.submission_to_ack`,
`slippage.points`) are registered with their statistical test and minimum
coverage but are **excluded from the certified claim** (`not_certified`)
until `FEAT-SIM-17` publishes calibrated artifacts — no threshold is ever
invented. Expanding or tightening the matrix requires a new envelope version.

## Evidence mapping schema

Evidence is a JSON-safe mapping (schema enforced fail-closed; unknown fields
are rejected, never ignored): `certificate_target`, `evaluation_time`,
`identity` (execution-model/config/source-lineage/tick-lineage hashes and
market-evidence class), `initial_authority_state` (complete-state hash,
exclusivity or foreign-activity replay count), `foreign_activity`, `gates`
(business/risk gates plus separately declared route-specific safety gates
with their route policy), `orders`, `deals`, `positions`, `receipts`
(Trading receipt fields; `received_at` feeds the latency invariant and is
never ignored by name), `events` (with `causes` causal edges and source
sequences), `ledger` (signed postings; conservation equation asserted), and
optional `economic_observations`.

Ignored-field registry (excluded from comparison; a new entry requires an
envelope-version change): `orders[].provider_timestamp`,
`orders[].retrieved_at`, `orders[].receive_time`, `deals[].provider_timestamp`.

## Normalization rules

Identifiers (orders, receipts, intents, provider orders/deals, positions,
events, postings) are alpha-renamed in encounter order, preserving
cardinality, foreign-key relationships, and causal edges. Events sharing an
economic timestamp form explicit ambiguous groups whose input order is never
rearranged into invented provider truth. The canonical digest covers the
comparable view only (the side-specific identifier map is excluded) so
alpha-equivalent evidence from cold re-execution hashes identically.

## Files

| File | Responsibility |
| --- | --- |
| `contracts.py` | Private frozen envelope, evidence, and result models |
| `envelope.py` | Versioned envelope registry and maturity-ladder publication |
| `normalize.py` | Scope check, alpha-renaming, ignored-field stripping |
| `compare.py` | Invariant comparison, budgets, conservation, invalidation |

## Tests and usage evidence

- Unit: `tests/simulator/unit/test_parity_envelope.py`,
  `tests/simulator/unit/test_parity_normalizer.py`,
  `tests/simulator/unit/test_parity_compare.py`
- Integration (standing regressions):
  `test_semantic_parity.py::test_paired_semantic_evidence_passes_envelope`,
  `test_parity_relationships.py::test_relationship_mutation_fails_parity`,
  `test_parity_envelope_rejection.py::test_unregistered_ignored_field_is_rejected`
  / `::test_demo_evidence_cannot_claim_live_scope`
  / `::test_certificate_invalidates_when_bound_identity_changes`,
  `test_cold_determinism.py::test_cold_runs_from_fresh_roots_are_identical`
- Usage: `tests/simulator/usage/features/18_parity.py`
  (`fr_sim_187`–`fr_sim_193`, `fr_sim_236`–`fr_sim_239`)

# 05 — Reconciliation: Live Schema vs. Proposal

> **AUTHORITATIVE — reconciliation record.** This document is the canonical record of
> divergence between the target model in this directory and the live schema. It records
> adoption tiers; it changes no code and executes no migration. Open decisions arising
> from it are recorded in [`docs/PROJECT.md`](../PROJECT.md) §12.

**Method.** Every `CREATE TABLE` in `app/` was extracted from source and compared
column-by-column against the 90 tables in this proposal. Figures below are machine-
generated, not estimated.

---

## 0. Corrections to earlier statements

Two things I asserted in Dry-Run Plan 1 were wrong. Both are corrected here.

| Claimed | Actual | Why it matters |
|---|---|---|
| "~48 tables live across 10 domains" | **59 tables across 11 prefixes** | My first grep matched only `CREATE TABLE IF NOT EXISTS`; 11 tables use bare `CREATE TABLE`. The Data domain is the bulk of the miss — 13 live tables, not 2. |
| Proposal is a clean greenfield target | **The live system already stores bulk data outside SQLite** | Simulator journals to append-only JSONL; Data writes CSV/Parquet artifacts with sidecar JSON manifests. The Parquet decision is not new architecture — it is *already the live pattern*, and the proposal partly reinvented it. |

The second point reframes the whole reconciliation. See §4.

---

## 0. Model completeness

**Closed.** The model now records **every table that ships**, in addition to its
target-only entries. Three passes were needed to get there, which is itself the
finding: a model asserting authority over the target schema was repeatedly missing
tables that already existed.

| Pass | Tables absorbed |
|---|---|
| Phase 3c | 13 Agentic + 4 Data research-source/runtime |
| Dry-Run Plan 9 | 8 Data operational + 4 API + `strategy_mutations` |

Model size: **102 tables**. Of these, 59 have a code definition and the remainder are
explicitly labelled target-only in their domain sections.

Two categories are recorded rather than corrected, because the tables are applied and
cannot change without a baseline reset:

- **Nine tables carry no `created_at`.** Each records time in a purpose-specific way
  (`applied_at_ns`, `timestamp_ns`, `window_started_at`, `scheduled_at`). Listed in
  `verify_schema.py` with the column each uses instead.
- **The four Strategy tables are not `STRICT`.** They predate the convention. The model
  states the target; the applied schema does not satisfy it. See
  [02](02_entity_specs_execution.md) Domain 5.

---

## 1. Headline numbers

| | Count |
|---|---|
| Live tables | **59** |
| Model tables (post-Phase 1) | **86** |
| Same name in both | **19** |
| — of which additive (proposal is a superset) | **4** |
| — of which mixed (minor column loss) | **2** |
| — of which incompatible (rebuild required) | **13** |
| Live-only — **proposal gaps** | **40** |
| Proposal-only — new build | **71** |

**Overlap is 19 of 59 (32 %).** The proposal is not a refinement of the live schema;
it is largely a parallel design that rediscovered some of the same tables and missed
two thirds of what exists.

---

## 2. Same-name tables — column-level verdict

`live` / `prop` / `shared` are column counts.

| Table | Verdict | live | prop | shared | Live columns absent from proposal |
|---|---|---|---|---|---|
| `risk_audit_records` | **ADDITIVE** | 12 | 13 | 12 | — |
| `trading_events` | **ADDITIVE** | 7 | 12 | 7 | — |
| `trading_idempotency` | **ADDITIVE** | 6 | 8 | 6 | — |
| `trading_projections` | **ADDITIVE** | 4 | 6 | 4 | — |
| `api_idempotency` | MIXED | 6 | 10 | 4 | `scope_key`, `status_code` |
| `portfolio_audit_outbox` | MIXED | 7 | 10 | 4 | `correlation_id`, `event_id`, `request_id` |
| `strategy_configs` | **REBUILD** | 6 | 12 | 0 | `config_hash`, `config_json`, `policy_version`, `request_id`, `strategy_id`, `strategy_version` |
| `strategy_checkpoints` | **REBUILD** | 5 | 6 | 0 | `authorization_ref`, `checkpoint_id`, `checkpoint_json`, `checksum`, `request_id` |
| `strategy_versions` | **REBUILD** | 8 | 12 | 1 | `lifecycle_status`, `manifest_json`, `policy_json`, `record_hash`, `request_id`, `correlation_id`, `strategy_version` |
| `api_sessions` | **REBUILD** | 6 | 12 | 2 | `session_digest`, `csrf_digest`, `user_id`, `revoked_at` |
| `api_accounts` | **REBUILD** | 11 | 15 | 4 | `user_id`, `roles_json`, `permissions_json`, `scopes_json`, `environment`, `active`, `verified` |
| `portfolio_definitions` | **REBUILD** | 5 | 12 | 1 | `portfolio_version`, `scope_key`, `definition_json`, `canonical_hash` |
| `portfolio_allocation_versions` | **REBUILD** | 7 | 14 | 1 | `allocation_id`, `allocation_version`, `scope_key`, `allocation_json`, `canonical_hash`, `activated_at` |
| `portfolio_rebalance_plans` | **REBUILD** | 7 | 14 | 3 | `plan_version`, `allocation_version`, `plan_json`, `canonical_hash` |
| `optimization_checkpoints` | **REBUILD** | 6 | 7 | 1 | `search_id`, `schema_version`, `reproducibility_hash`, `checkpoint_json`, `completed_candidate_position` |
| `agentic_memory_records` | **REBUILD** | 15 | 12 | 4 | `store_class`, `author_role_id`, `content_json`, `scope_json`, `retention_class`, `sensitivity`, `injection_status`, `redacted_paths_json` |
| `agentic_workflow_checkpoints` | **REBUILD** | 11 | 8 | 4 | `task_id`, `workflow_name`, `workflow_version`, `node_id`, `state_payload_hash`, `canonical_hash` |
| `research_artifacts` | **REBUILD** | 8 | 13 | 1 | `relative_path`, `format`, `size_bytes`, `sha256`, `atomic`, `schema_version`, `audit_event_id` |
| `data_migration_ledger` | **REBUILD** | 4 | 4 | 1 | `migration_id`, `checksum`, `applied_at_ns` |

> **Status: resolved in Phase 2.** The hybrid rule (D9) was applied to all 12 remaining
> REBUILD tables — `data_migration_ledger` was the thirteenth and Phase 1 closed it.
> **40 live columns were admitted, 26 rejected.** The model now carries the integrity
> hashes, traceability identifiers, and state fields the live tables had; it does not
> adopt payload blobs whose contents it normalises, nor columns that are renames.
> Divergence is narrowed, not closed: the *live* tables are unchanged and Tier C
> remains rejected.

### What the REBUILD rows have in common

Almost every one loses the same three things:

1. **A canonical/record hash** — `canonical_hash`, `record_hash`, `content_hash`,
   `checksum`, `reproducibility_hash`. The live schema hashes state so tampering and
   drift are detectable. The proposal has this on some tables and dropped it on others.
2. **A `*_json` payload column** — `config_json`, `manifest_json`, `allocation_json`,
   `plan_json`, `checkpoint_json`. The live design stores a validated contract blob and
   normalises only what it queries. The proposal normalised aggressively into typed
   columns.
3. **Request/correlation identifiers** — `request_id`, `correlation_id`. Present on
   nearly every live table; inconsistently applied in the proposal.

**The live pattern is better on points 1 and 3, and the disagreement on point 2 is a
genuine trade-off**, not an error on either side. Normalised columns give indexed
queries and `CHECK` constraints; a JSON blob gives schema evolution without a
migration. The live choice is the right one for a system under an *immutable* ledger,
because adding a field to a JSON payload needs no migration at all.

### `data_migration_ledger` is a special case

The proposal's version is **wrong and must be discarded**. I reproduced it from memory
rather than from source. Live columns are `migration_id`, `domain`, `checksum`,
`applied_at_ns`; the proposal invented `step_id`, `sequence`, `applied_at`. Per
`AGENTS.md` §5 this table governs every other migration — proposing a variant of it
was a mistake.

---

## 3. Proposal gaps — 40 live tables with no equivalent

These are **not** candidates for deletion. They are things the proposal failed to
account for, and each would have to be preserved or explicitly retired.

### Data (13 live, proposal has 0 of them)

`data_feeds` · `data_update_jobs` · `data_backfill_checkpoints` · `data_cache` ·
`data_source_state` · `data_source_attempts` · `data_audit_events` ·
`data_economic_events` · `data_research_sources` · `data_research_observations` ·
`data_verified_research_sources` · `data_write_locks` · `data_migration_ledger`

This is the proposal's largest failure. It designed a Data domain around storing bars
— a thing the live system deliberately does not do — and consequently missed the
domain's real responsibilities: **streaming feed lifecycle** (`data_feeds` has 24
columns covering buffer depth, overflow policy, heartbeat, breaker state, drift),
**scheduled backfill with leases and resumable checkpoints**, **response caching**, and
**source readiness/circuit state**.

`data_write_locks` is required by `AGENTS.md` §5 (write-lock leases) and its absence
from the proposal is a correctness gap, not a stylistic one.

### Risk (7 live, proposal has 0 by name)

`risk_policy_versions` · `risk_eligibility_decisions` · `risk_allocation_decisions` ·
`risk_kill_switch_states` · `risk_approval_tokens` · `risk_decision_snapshots` ·
`risk_audit_records` *(the one overlap)*

The proposal renamed nearly all of these — see §5.

### Agentic (11 live absent)

`agentic_workflow_runs` · `agentic_lifecycle_transitions` · `agentic_promotion_packets` ·
`agentic_operations_traces` · `agentic_operations_incidents` · `agentic_operations_replays` ·
`agentic_evidence_claims` · `agentic_experiment_specs` · `agentic_experiment_runs` ·
`agentic_experiment_holdout_use` · `agentic_experiment_verdicts`

Note `agentic_experiment_holdout_use` — the live system **already implements** the
holdout-use ledger the proposal presented as a new idea in
`optimization_holdout_uses`. Same control, different domain, already shipped.

### Others (9)

`api_credentials` · `api_approvals` · `api_auth_failures` · `api_settings` ·
`portfolio_active_scopes` · `portfolio_construction_results` · `portfolio_idempotency` ·
`optimization_results` · `strategy_mutations` · `simulation_runs` · `hq_runtime_records`

`hq_runtime_records` is a generic key-value runtime store with `namespace` /
`collection_name` / `partition_key` / `codec_kind` — a deliberate escape hatch the
proposal has no equivalent for.

---

## 4. The storage-architecture finding

**The live system already does what the Parquet revision asked for**, and does it
differently from the proposal.

| Concern | Live implementation | Proposal (docs 00–04) |
|---|---|---|
| Bulk market data | `dataset_writer.py` → CSV/Parquet artifact + **sidecar JSON manifest file** | Parquet + **SQLite catalog tables** |
| Manifest contract | `StorageManifest` (Pydantic, frozen): `artifact_id`, `relative_path`, `format`, `content_hash`, `schema_version`, `normalization_version`, `source_revision`, `row_count`, `start`, `end`, `license_metadata`, `provenance`, `created_at`, `request_id` | `data_datasets` + `data_partition_files` |
| Simulator journal | Append-only **JSONL**, `JOURNAL_FORMAT = "jsonl-v1"`; the migration file states a SQLite journal sidecar is *"an explicit Phase 1 exclusion"* | Model now defers to JSONL; its table was withdrawn |
| Artifact catalog | `research_artifacts` table: `relative_path` PK, `sha256`, `size_bytes`, `atomic`, `schema_version` | `research_artifacts` with different columns |
| Atomicity | temp file → `os.replace`, sha256 after write | Same pattern, independently arrived at |

Three consequences:

1. **`sim_timeline_events` directly contradicted a documented live exclusion.**
   Withdrawn in Phase 1 rather than reconciled.
2. **`StorageManifest` already carries 11 of the 14 fields proposed for
   `data_partition_files`.** Phase 1 adopted five of them; the model's genuine
   additions are `verify_state`, `verified_at`, and the dataset grouping. Phase 4A
   dropped `partition_year`, `partition_month`, `sealed`, and `row_group_count`: the
   shipped writer emits flat content-addressed artifacts, and a catalog that prunes by
   recorded time range makes directory partitioning redundant.
3. **The real design question is not "Parquet or SQLite" — it is "sidecar manifest or
   catalog table".** Live uses sidecars. That is decision **D8** below.

### Sidecar vs. catalog — the actual trade

| | Sidecar JSON (live) | SQLite catalog (proposal) |
|---|---|---|
| Self-describing on disk | Yes — copy the directory, keep the metadata | No — catalog and files can separate |
| Find files for a time range | Walk directory, read N manifests | One indexed query |
| Detect a missing/corrupt file | Only when you open it | `verify_state` sweep, indexed |
| Transactional with other state | No | Yes |
| Extra failure mode | None | Catalog row pointing at a missing file |

Neither is wrong. The defensible synthesis is **both**: keep the sidecar as the
authoritative record (self-describing, survives a database loss) and treat the SQLite
catalog as a **rebuildable index** over the sidecars. A corrupt catalog is then
recoverable by rescanning; a lost sidecar is not recoverable at all, which is the
right asymmetry.

---

## 5. Renames — same concept, different name

The proposal duplicated live concepts under new names. Adopting them would mean two
tables for one job.

| Proposal | Live equivalent | Recommendation |
|---|---|---|
| `risk_policies` | `risk_policy_versions` | Keep live name |
| `risk_kill_switch_states` | `risk_kill_switch_states` | Keep live name |
| `risk_eligibility_decisions` | `risk_eligibility_decisions` + `risk_allocation_decisions` | Live splits eligibility from allocation — that separation is deliberate; keep it |
| `optimization_holdout_uses` | `agentic_experiment_holdout_use` | Keep live; do not build a second holdout ledger |
| `optimization_jobs` / `optimization_trials` | `optimization_results` (`search_id`, `ranked_candidates_json`) | Live stores ranked candidates as JSON; proposal normalises to rows. Genuine trade-off — see §2 point 2 |
| `sim_runs` | `simulation_runs` | **Prefix conflict D2**: live `simulation_`, `ARCHITECTURE.md` L649 says `sim_`. Doc is wrong or code is; pick one |
| `agentic_traces` / `agentic_trace_spans` | `agentic_operations_traces` | Keep live name |
| `agentic_workflow_checkpoints` (proposal) | same name, different columns | Keep live |
| ~~`util_settings`~~ | `api_settings` + typed bootstrap settings | **Withdrawn.** Utils owns no tables; UI/API owns the unified non-secret user/system documents and central JSON/process sources bootstrap the database; see [01](01_entity_specs_core.md) Domain 1 |

---

## 6. Reconciliation plan

### Tier A — **conformed in Phase 3a**

> **Superseded framing.** This tier was written assuming the four tables were applied
> and would need additive `ALTER` migrations. They were never applied. Phase 3a edited
> the definitions in place instead — no ledger event, no checksum conflict.
>
> `trading_events`, `trading_idempotency`, `trading_projections`, and all seven Risk
> tables now match the model exactly, verified column-by-column. Trading moved to
> `app/services/trading/migrations/`, Risk to `app/services/risk/migrations/` (D12).
> Requirements registered as `FR-TRD-070`–`073` and `FR-RISK-069`–`072`.

### Original framing — adopt as-is, additive migration, no ledger break (4 tables)

`trading_events`, `trading_idempotency`, `trading_projections`, `risk_audit_records`.

Every live column survives; the proposal only adds. `ALTER TABLE ADD COLUMN` with
defaults is additive and ledger-safe under `AGENTS.md` §5. **This is the only tier
that can proceed without a baseline reset.**

Suggested order: `trading_projections` → `trading_idempotency` → `trading_events` →
`risk_audit_records`. Each is one migration step with its own checksum.

**Identifier allocation.** These are additive changes to schema owned by *existing*
registered features, so they need new `FR-*` requirements under the existing
`FEAT-*`, not new feature IDs:

| Domain | Owning feature | Next free `FR-*` | Next free `FEAT-*` |
|---|---|---|---|
| Trading | `FEAT-TRD-02` State and Deterministic Projections | `FR-TRD-070` | `FEAT-TRD-10` |
| Risk | Risk audit chain | `FR-RISK-069` | `FEAT-RISK-16` |

Registration is three-part and lives outside this model: the `FR-*` text in the owning
package `README.md` Section 4.x, a row or amendment in that README's `### Feature
Registry`, and exactly one usage program at
`tests/<domain>/usage/features/NN_*.py`.

Highest currently allocated, for reference when planning later phases:

| Domain | `FR-` prefix | Highest | `FEAT-` highest |
|---|---|---|---|
| analytics | `FR-ANLT-` | 054 | 05 |
| api | `FR-API-` | 072 | 13 |
| brokers | `FR-BRK-` | 135 | 15 |
| data | `FR-DATA-` | 150 | 17 |
| indicators | `FR-INDI-` | 035 | 06 |
| optimization | `FR-OPT-` | 069 | 09 |
| portfolio | `FR-PORT-` | 040 | 08 |
| research | `FR-RES-` | 104 | 16 |
| risk | `FR-RISK-` | 068 | 15 |
| simulator | `FR-SIM-` | 090 | 09 |
| strategy | `FR-STR-` | 053 | 11 |
| trading | `FR-TRD-` | 069 | 09 |
| utils | `FR-UTL-` | 050 | — |
| agentic | *none registered* | — | 22 |

### Tier B — proposal-only, no live conflict (71 tables)

New tables collide with nothing and are additive by construction. But **do not build
all 71.** Sequence by whether the owning domain has a real gap:

> **Revised after D10.** An earlier version of this table named `broker_*` as priority 1
> and `analytics_*` as priority 5, on the assumption that both were gaps. `PROJECT.md`
> §5 records Brokers as deliberately stateless and Analytics as read-only. D10 upheld
> the first and overturned the second.

| Priority | Tables | Status | Why |
|---|---|---|---|
| — | ~~`util_*` (7)~~ | Withdrawn | Utils is the shared framework and owns no state |
| 2 | `indicator_*` (3) | **Built (Phase 4B)** | No live Indicators persistence |
| 3 | `analytics_*` (6) | **Built (Phase 4C)** | Derived store only. `analytics_trade_analysis` holds MAE/MFE per round-trip, which nothing else stores — Trading owns fills, no domain owns round-trip analysis. Requires the §5 amendment made under D10 |
| 4 | `trading_orders`, `trading_fills`, `trading_positions`, `trading_order_transitions` | **Built (Phase 4D)** | Trading now writes authoritative events and rebuildable relational projections in one Data-owned transaction; no Trading state uses the generic runtime-record table |
| 5 | `broker_symbol_map` (1) | **Built (Phase 4E)** | Bitemporal reference data. The other four `broker_*` tables are **withdrawn** — Brokers stays a stateless passthrough |
| 6 | Everything else | Deferred | Defer until a feature needs it |

### Tier C — rebuild, blocked (13 tables)

Each needs a baseline reset approval per `ARCHITECTURE.md` L650. **Recommendation:
do not pursue.** In every case the live table is either equivalent or better, and the
migration cost buys column naming.

**Reassessed after Phase 2.** With the hybrid rule applied, the model now carries what
made the live tables better — `canonical_hash`, `record_hash`, `request_id`,
`correlation_id`, `retention_class`, `injection_status`, and the workflow-node columns.
The residual differences are renames and payload-shape preferences, which do not
justify a baseline reset.

Exception worth considering: `api_accounts` / `api_sessions`. Live stores RBAC as
`roles_json` / `permissions_json` / `scopes_json` denormalised onto the account. The
proposal's `api_roles` / `api_permissions` / `api_role_bindings` normalisation is a
real improvement — role changes currently require rewriting every affected account
row, and there is no way to query "who holds this permission". That one is worth the
migration; the other twelve are not.

### Tier D — proposal defects to fix in these documents (5)

**Status: applied** (Dry-Run Plan 3, Phase 1).

| Fix | Reason | Outcome |
|---|---|---|
| Delete `sim_timeline_events` | Contradicts documented live exclusion (§4) | Withdrawn; rationale recorded in [02](02_entity_specs_execution.md) |
| Replace `data_migration_ledger` with the live definition | Model version was invented (§2) | Transcribed verbatim; code is authoritative |
| Add `data_write_locks` | Required by `AGENTS.md` §5 | Added from `locking.py` |
| Add `request_id` / `correlation_id` where they belong | Live convention | Applied to **21** tables, not all 81 — admitted only where a row records a decision, side-effecting mutation, external interaction, or audit event |
| Reconcile `data_partition_files` with `StorageManifest` | Reuse the live contract's fields | 5 fields adopted (`format`, `normalization_version`, `source_revision`, `provenance_json`, `request_id`); 3 rejected as duplicates |
| **D10 split** | Brokers vs Analytics persistence | 4 `broker_*` withdrawn, `broker_symbol_map` retained, `analytics_*` kept |

Model size after Phase 1: **86 tables** (was 90).

### Phase 4 — status

The model stands at **102 tables**. All five sub-phases shipped.

| Sub-phase | Status | Delivered |
|---|---|---|
| 4A | Shipped | Artifact catalogue (7 tables), `FEAT-DATA-18`, `FR-DATA-154`–`160` |
| 4B | Shipped | `indicator_*` (3), `FEAT-INDI-07`, `FR-INDI-036`–`040` |
| 4C | Shipped | `analytics_*` (6), `FEAT-ANLT-06`, `FR-ANLT-055`–`059` |
| 4D | Shipped | Trading materialisation (`trading_orders`, `trading_fills`, `trading_positions`, `trading_order_transitions`) and direct Trading-owned persistence |
| 4E | Shipped | `broker_symbol_map` (1), `FEAT-BRK-16`, `FR-BRK-136`–`138` |

`trading_events` remains the write model. The four Phase 4D tables are rebuildable read
projections written atomically with the event and aggregate projection. Nullable
`time_in_force` preserves the shipped Trading contract instead of inventing a broker
default, and fill execution time is taken from authority evidence.

Two defects were found and fixed while closing, both of a kind worth naming.

The first: renaming `hq_runtime_records` to `data_runtime_records` updated the migration
but not the ten statements in `create.py`, `read.py`, and `update.py` that read the
table. Every one would have failed on first apply, for Trading, Risk, Portfolio,
Simulator, and Agentic alike, since all five persist through that store. Nothing in the
type system, the linter, or the test suite connects a SQL string constant to the
`CREATE TABLE` that backs it, so the omission was invisible until execution.
`verify_persistence_sql.py` now closes that gap and is proven against the bug itself.

The second is smaller but the same shape: the harness extracted index names with a
pattern that consumed `IF NOT EXISTS` as the name, so two partial unique indexes were
reported as `IF`. A check that prints a wrong name still passes, which is why it
survived several runs.

**Phase 6 completed.** Trading, Risk, Portfolio, Simulator, and Agentic now persist
their active durable state directly in domain-owned relational tables while Data
retains connection, lock, statement-plan, and transaction execution ownership. No
production domain writes `data_runtime_records`. Agentic uses eight owned tables for
workflow, memory records, lifecycle, traces, incidents, and replays; its evidence-claim
and experiment tables remain without production durable producers and were not
populated speculatively. Simulator's canonical journal remains partial JSONL with
group-commit durability and atomic filesystem publication; no database journal table
was introduced.
`portfolio_definitions` remains intentionally without a runtime producer until a
registered feature supplies a definition command.

The development-only `api-0004` ledger orphan was repaired after an immutable backup
and exact-row verification. Complete-manifest migration requests now reject any applied
ID absent from code. The `data_migration_ledger.applied_at_ns` transcription error —
the model said `INTEGER`, the shipped column is `TEXT` with a 19-digit `GLOB` check —
is corrected in [01](01_entity_specs_core.md).

---

## 7. Recommendation

**Do not adopt this proposal wholesale.** Overlap is 32 %, and where the two disagree
the live schema is usually right — it is grounded in shipped features under an
immutable ledger; the proposal is grounded in a blank page.

Use it as three things instead:

1. **A historical gap list.** Its Phase 4 and Phase 6 persistence gaps have been
   reconciled; current state is governed by each owning package README and migration
   manifest.
2. **A design-control catalogue.** The `CHECK`-constraint patterns in
   [README](README.md) §"Design controls" apply to live tables regardless of whether
   the proposed tables are ever built.
3. **A record of the Tier C exception that was migrated** — normalized API RBAC in
   `api-0005`, with legacy account JSON claim columns retained only for immutable
   baseline compatibility.

Everything else should be retired rather than reconciled.

---

## 8. Decisions this raises

Decisions arising from this reconciliation — **D2, D4, D8, D9**, plus **D10** and
**D11** raised during Phase 0 — are recorded in [`docs/PROJECT.md`](../PROJECT.md) §12.
Per `AGENTS.md` §4 *Decision Hygiene*, this document holds no decision ledger.

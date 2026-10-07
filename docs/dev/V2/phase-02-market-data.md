# Phase 2 — Market data

**Feature group:** F02. **Tasks:** 8. **Status:** complete; 8 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Manage typed instruments, brokers and authoritative dataset metadata. This phase owns the market data capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** F01 settings, jobs, resources and approved persistence. Data selection must publish typed references for F03/F04/F11.

**Delivery:** M02 and M07. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/data`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P03](../V1/phase-03-data-manager.md), [V1 P04](../V1/phase-04-data-ingestion.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Catalog/sessions/files | 2.1-2.4 | Home/actions/help/logs, instruments/brokers, sessions/DST/native overwrite-skip-conflicts, immutable datasets, quality/repair/resampling/export |
| Crypto sources | 2.5 | Binance spot, Coin-M and USDT-M; Bitfinex; Coinbase Pro; Poloniex; generic crypto |
| Other sources | 2.5 | Darwinex; Dukascopy; MT5 API; SQ Equity Data; SQ Futures Data; TD; Yahoo; files |
| Baskets/custom data | 2.6 | Member/version selection, aligned datasets, custom fields and authoritative counts |
| COT | 2.7 | Symbol catalog, five-field mapping, release alignment, create/update/synchronize/export |
| Provider availability | 2.5/2.8 | Each named row needs endpoint/entitlement/compatibility and individual acceptance; obsolete labels are not working providers |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F02 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/DataManager/DataManager.tsx](../../../ui/app/workspace/DataManager/DataManager.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 2.1 Dataset catalog, instruments and broker definitions

## 1. Objective

Manage typed instruments, brokers and authoritative dataset metadata.

## 2. Research and donors

P03 DataManagerData/Instruments/Broker/Home resources and data-selection consumers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/data/catalog.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/data/instruments.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_02/test_catalog.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Define stable IDs, units, tick/lot precision, timezone, currency, broker mapping and immutable dataset revisions.
- [x] **Step 2:** Expose catalog query/create/update with host-owned revision checks.
- [x] **Step 3:** Validate consumer compatibility and distinguish unavailable data from empty series.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_02/test_catalog.py --no-cov`.

**Independent cases:** Test identity collisions, invalid precision/currency, broker mapping conflicts, revision updates and consumer compatibility after reload.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 2.2 Sessions, clocks and native session import

## 1. Objective

Represent sessions and timestamps explicitly, including native session import.

## 2. Research and donors

P03 Sessions/Joda-Time consumers and actual session resources.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/data/sessions.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_02/test_sessions.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Specify timestamp units, source timezone, DST gap/fold handling and session open/close/overnight calendars.
- [x] **Step 2:** Normalize without silently shifting timestamps; retain original interpretation in metadata.
- [x] **Step 3:** Implement native session import with evidenced overwrite/skip policies and visible conflicts.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_02/test_sessions.py --no-cov`.

**Independent cases:** Independent DST gap/fold, overnight/weekend/session-boundary vectors; malformed zones, timestamp units and overwrite/skip/conflict imports.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 2.3 File import and immutable dataset revisions

## 1. Objective

Import files into validated immutable datasets using one ingestion path.

## 2. Research and donors

P04 file importer and P03 dataset contracts; enumerate accepted source formats from evidence.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/data/ingestion.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_02/test_ingestion.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Specify accepted CSV/text/native file fields, delimiter/encoding, timestamp units and row errors.
- [x] **Step 2:** Stream/chunk through typed normalization with finite bounds; retain source fingerprint and import settings.
- [x] **Step 3:** Stage output through host resources, publish only a complete accepted revision and retain job lineage.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_02/test_ingestion.py --no-cov`.

**Independent cases:** Check exact independent rows/types/precision; malformed headers, duplicates, chunk boundaries, partial write, cancellation and replay without duplicate publication.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 2.4 Data quality, transformations and data export

## 1. Objective

Inspect, repair and transform data with explicit policies and reproducible exports.

## 2. Research and donors

P03 custom-data/data-selection consumers and P04 ingestion quality expectations.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/data/quality.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/data/transforms.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_02/test_quality.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Report ordering, gaps, duplicate/missing/nonfinite rows and bar validity using authoritative counts.
- [x] **Step 2:** Ratify reject/repair, resampling and custom-column rules; preserve source revision and repair lineage.
- [x] **Step 3:** Export accepted rows with exact units/time/precision and make all transformations cancellable jobs where needed.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_02/test_quality.py --no-cov`.

**Independent cases:** Independent gap/duplicate/aggregation vectors, unsorted inputs, empty data, repair policies, DST boundaries and export round trips.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 2.5 Provider downloads and compatibility matrix

## 1. Objective

Implement all retained download sources as narrow adapters over the same ingestion service.

## 2. Research and donors

P04 all provider donors; qualify current endpoint and entitlement at implementation rather than asserting old vendor labels are active.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/data/providers.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_02/test_providers.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** For each provider-matrix row, recover pagination, symbols, units, credentials, entitlement, rates and current availability from primary evidence.
- [x] **Step 2:** Implement file-compatible chunks with shared bounded httpx lifecycle, retry/backoff and cancellation.
- [x] **Step 3:** Retain source/account mapping and download revision lineage; expose partial failures and explicit unavailable/replacement decisions.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_02/test_providers.py --no-cov`.

**Independent cases:** Adapter-specific recorded responses plus isolated connected qualification for every row; test pagination, rate limits, timeout, stale/partial responses and cancellation without corrupt revision.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 2.6 Baskets and custom data

## 1. Objective

Support baskets and custom datasets without introducing another data engine.

## 2. Research and donors

P03 Basket and CustomData contributions; consumers determine accepted calculations.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/data/custom_data.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/data/baskets.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_02/test_custom_data.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Define basket membership/version, alignment and aggregate/custom-column policies.
- [x] **Step 2:** Apply transformations to explicit instrument/dataset revisions with documented missing-member behavior.
- [x] **Step 3:** Expose create/update/select/export using the same catalog, jobs and resource publication.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_02/test_custom_data.py --no-cov`.

**Independent cases:** Test duplicate membership, misaligned timestamps/calendars, missing series, incompatible units, custom-column typing and immutable reload.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 2.7 COT catalog, mapping and updates

## 1. Objective

Import and synchronize COT data with release-aware field semantics.

## 2. Research and donors

P03/P04 COT resource donor; F03 owns indicator formulas, not the download service.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/data/cot.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_02/test_cot.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Recover the symbol catalog and five-field mapping; specify report period versus publication time.
- [x] **Step 2:** Align releases without future-data leakage and create/update the corresponding custom dataset.
- [x] **Step 3:** Support synchronization/export and downstream signals with visible remote/mapping failures.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_02/test_cot.py --no-cov`.

**Independent cases:** Independent five-field/time-alignment fixtures; missing symbols, revised release, update deduplication, delayed publication and failed sync/export.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 2.8 Connected Data Manager workflow

## 1. Objective

Connect the retained Data Manager to actual catalog and ingestion outcomes.

## 2. Research and donors

Existing data_source plugin READMEs/clients and P03/P04 integration gates.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/data/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_02/test_integration.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [x] **Step 1:** Wire data home/actions/help/logs, provider forms and dataset/session selectors to the owned backend capabilities.
- [x] **Step 2:** Display authoritative row counts, job/resource IDs and saved revisions; remove production fixture substitutes.
- [x] **Step 3:** Demonstrate file import, selected-provider download, inspect, cancel, reload and downstream selection.
- [x] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_02/test_integration.py --no-cov`.

**Independent cases:** Isolated real-host browser journey with import/download errors, cancellation/reconnect and persistence; provider matrix remains incomplete until each row is qualified.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [x] All 8 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [x] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [x] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [x] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.


A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.

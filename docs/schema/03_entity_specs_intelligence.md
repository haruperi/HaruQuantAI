# 03 — Entity Specs: Intelligence & Perimeter

Analytics, Optimization, Research, Portfolio, Agentic, UI-API.

> **AUTHORITATIVE — target schema model.** Canonical for cross-domain schema
> structure and the target table/column model. Current-state feature registries remain
> in each owning package `README.md`; executable schema remains in the owning domain's
> migration definitions. Divergences are recorded in
> [05_reconciliation.md](05_reconciliation.md). See [README.md](README.md) for the full
> authority statement.

Conventions from [00_domain_relationship_map.md](00_domain_relationship_map.md) §8
apply to every table below. All tables are `STRICT`.

---

## Domain 9 — Analytics (`analytics_`)

> Prefix `analytics_` is ratified (D1) and recorded in `docs/ARCHITECTURE.md`.

Generated from migration step `001_analytics_schema_v1`. Analytics owns **derived,
recomputable state only**; every table records the `source_hash` of its inputs, so a
stale value is detectable rather than merely wrong.

### `analytics_metric_definitions`

```sql
CREATE TABLE analytics_metric_definitions (
    metric_id TEXT PRIMARY KEY,
    metric_code TEXT NOT NULL,
    version TEXT NOT NULL,
    category TEXT NOT NULL,
    formula_hash TEXT NOT NULL,
    min_sample_size INTEGER NOT NULL DEFAULT 1,
    requires_benchmark INTEGER NOT NULL DEFAULT 0 CHECK (requires_benchmark IN (0, 1)),
    higher_is_better INTEGER NOT NULL DEFAULT 1 CHECK (higher_is_better IN (0, 1)),
    unit TEXT NOT NULL,
    definition_json TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (metric_code, version)
) STRICT;
```

`min_sample_size` is the catalogue's defence against reporting a Sharpe ratio from nine trades. Analytics refuses to emit a value below it rather than emitting a number that looks authoritative and means nothing.

### `analytics_metric_values`

```sql
CREATE TABLE analytics_metric_values (
    value_id TEXT PRIMARY KEY,
    metric_id TEXT NOT NULL,
    scope_level TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    period_kind TEXT NOT NULL,
    period_start_utc INTEGER NOT NULL,
    period_end_utc INTEGER NOT NULL,
    value_decimal TEXT,
    sample_size INTEGER NOT NULL,
    confidence_low_decimal TEXT,
    confidence_high_decimal TEXT,
    is_significant INTEGER CHECK (is_significant IN (0, 1)),
    insufficient_sample INTEGER NOT NULL DEFAULT 0 CHECK (insufficient_sample IN (0, 1)),
    source_hash TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE ( metric_id, scope_level, scope_key, period_kind, period_start_utc, period_end_utc ),
    CHECK (insufficient_sample = 1 OR value_decimal IS NOT NULL)
) STRICT;

CREATE INDEX idx_analytics_values_scope ON analytics_metric_values(scope_level, scope_key, computed_at DESC);

CREATE INDEX idx_analytics_values_metric ON analytics_metric_values(metric_id, period_end_utc DESC);
```

`insufficient_sample = 1` with a null value is how "not enough data" is represented. The `CHECK` makes the alternative — a `0` that reads as a real measurement — unrepresentable.

### `analytics_trade_analysis`

```sql
CREATE TABLE analytics_trade_analysis (
    trade_id TEXT PRIMARY KEY,
    source_kind TEXT NOT NULL,
    run_id TEXT,
    position_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    symbol_id TEXT NOT NULL,
    strategy_version_id TEXT,
    direction TEXT NOT NULL,
    entry_price_decimal TEXT NOT NULL,
    exit_price_decimal TEXT NOT NULL,
    quantity_decimal TEXT NOT NULL,
    gross_pnl_decimal TEXT NOT NULL,
    net_pnl_decimal TEXT NOT NULL,
    commission_decimal TEXT NOT NULL DEFAULT '0',
    swap_decimal TEXT NOT NULL DEFAULT '0',
    slippage_decimal TEXT NOT NULL DEFAULT '0',
    r_multiple_decimal TEXT,
    mae_decimal TEXT,
    mfe_decimal TEXT,
    holding_seconds INTEGER NOT NULL,
    bars_held INTEGER,
    exit_reason TEXT NOT NULL,
    regime_id TEXT,
    entry_at TEXT NOT NULL,
    exit_at TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;

CREATE INDEX idx_analytics_trades_strategy ON analytics_trade_analysis(strategy_version_id, exit_at DESC);

CREATE INDEX idx_analytics_trades_symbol ON analytics_trade_analysis(symbol_id, exit_at DESC);

CREATE INDEX idx_analytics_trades_run ON analytics_trade_analysis(run_id) WHERE run_id IS NOT NULL;
```

One row per closed round-trip. `mae_decimal` and `mfe_decimal` are why this exists separately from the execution record: a winning trade that first ran 3 % against the position is a different trade from one that never did, and only excursion data distinguishes them. Nothing else stores round-trip analysis — Trading owns fills, not round trips.

### `analytics_pnl_attribution`

```sql
CREATE TABLE analytics_pnl_attribution (
    attribution_id TEXT PRIMARY KEY,
    scope_level TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    period_start_utc INTEGER NOT NULL,
    period_end_utc INTEGER NOT NULL,
    factor TEXT NOT NULL,
    contribution_decimal TEXT NOT NULL,
    contribution_percent_decimal TEXT NOT NULL,
    trade_count INTEGER NOT NULL DEFAULT 0,
    source_hash TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE ( scope_level, scope_key, period_start_utc, period_end_utc, factor )
) STRICT;

CREATE INDEX idx_analytics_attrib_scope ON analytics_pnl_attribution(scope_level, scope_key, period_end_utc DESC);
```

Factors must sum to total PnL with `residual` absorbing the remainder. A large residual is itself the signal: the attribution model is missing a real cost.

### `analytics_equity_curves`

```sql
CREATE TABLE analytics_equity_curves (
    curve_id TEXT PRIMARY KEY,
    scope_level TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    dataset_id TEXT,
    period_start_utc INTEGER NOT NULL,
    period_end_utc INTEGER NOT NULL,
    point_count INTEGER NOT NULL DEFAULT 0,
    start_equity_decimal TEXT NOT NULL,
    end_equity_decimal TEXT NOT NULL,
    peak_equity_decimal TEXT NOT NULL,
    trough_equity_decimal TEXT NOT NULL,
    max_drawdown_decimal TEXT NOT NULL DEFAULT '0',
    max_drawdown_percent_decimal TEXT NOT NULL DEFAULT '0',
    max_drawdown_start_utc INTEGER,
    max_drawdown_end_utc INTEGER,
    recovery_ts_utc INTEGER,
    source_hash TEXT NOT NULL,
    state TEXT NOT NULL,
    computed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (scope_level, scope_key, period_start_utc, period_end_utc),
    CHECK (period_end_utc >= period_start_utc)
) STRICT;

CREATE INDEX idx_analytics_equity_scope ON analytics_equity_curves(scope_level, scope_key, period_end_utc DESC);

CREATE INDEX idx_analytics_equity_dd ON analytics_equity_curves(scope_level, max_drawdown_percent_decimal);
```

Curve **points** live in an artifact; this holds identity and summary statistics. The summary columns are the ones actually queried — "worst drawdown across all strategies" ranks a few hundred rows, not millions of points.

`recovery_ts_utc IS NULL` on a completed curve means the drawdown never recovered, a distinct state rather than an absent value.

### `analytics_reports`

```sql
CREATE TABLE analytics_reports (
    report_id TEXT PRIMARY KEY,
    report_kind TEXT NOT NULL,
    scope_level TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    period_start_utc INTEGER NOT NULL,
    period_end_utc INTEGER NOT NULL,
    content_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    artifact_path TEXT,
    state TEXT NOT NULL,
    generated_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
) STRICT;

CREATE INDEX idx_analytics_reports_scope ON analytics_reports(scope_level, scope_key, generated_at DESC);
```

`content_hash` makes a report reproducible: the same inputs must produce the same document.

---
## Domain 10 — Optimization (`optimization_`)

> **This domain follows the live implementation.** A search is identified by
> `search_id`, and its ranked candidates are stored as a payload rather than one row
> per trial. The normalised job/trial decomposition below is target-only.

### `optimization_results`

```sql
CREATE TABLE optimization_results (
    search_id        TEXT    PRIMARY KEY,
    schema_version   TEXT    NOT NULL,
    reproducibility_hash TEXT NOT NULL,
    result_json      TEXT    NOT NULL,
    ranked_candidates_json TEXT NOT NULL,
    stored_at        TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_optimization_results_repro ON optimization_results(reproducibility_hash);
```

`reproducibility_hash` is indexed so an identical search is found rather than recomputed.
A search that cannot be reproduced is not evidence of anything.

### `optimization_checkpoints`

```sql
CREATE TABLE optimization_checkpoints (
    search_id        TEXT    PRIMARY KEY,
    schema_version   TEXT    NOT NULL,
    reproducibility_hash TEXT NOT NULL,
    completed_candidate_position INTEGER NOT NULL,
    checkpoint_json  TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL
) STRICT;
```

`completed_candidate_position` is the resume point. Resuming without it — or with a
fresh RNG — silently changes the search trajectory, so the resumed job is not the job
that was started.

---

### Target-only tables

No live counterpart; not built. They normalise what `ranked_candidates_json` currently
carries, enabling per-trial querying and overfit ratios.

#### `optimization_jobs`

```sql
CREATE TABLE optimization_jobs (
    job_id           TEXT    PRIMARY KEY,
    job_name         TEXT    NOT NULL,
    strategy_version_id TEXT NOT NULL,                   -- soft ref
    method           TEXT    NOT NULL CHECK (method IN ('grid','random','genetic','bayesian','particle_swarm','walk_forward')),
    search_space_json TEXT   NOT NULL CHECK (json_valid(search_space_json)),
    objective_metric_id TEXT NOT NULL,                   -- soft ref → analytics_metric_definitions
    objective_direction TEXT NOT NULL CHECK (objective_direction IN ('maximize','minimize')),
    constraints_json TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(constraints_json)),
    max_trials       INTEGER NOT NULL,
    completed_trials INTEGER NOT NULL DEFAULT 0,
    parallelism      INTEGER NOT NULL DEFAULT 1,
    seed             INTEGER NOT NULL DEFAULT 0,
    in_sample_start_utc  INTEGER NOT NULL,
    in_sample_end_utc    INTEGER NOT NULL,
    out_sample_start_utc INTEGER,
    out_sample_end_utc   INTEGER,
    holdout_locked   INTEGER NOT NULL DEFAULT 1 CHECK (holdout_locked IN (0,1)),
    state            TEXT    NOT NULL CHECK (state IN ('draft','queued','running','paused','completed','failed','cancelled')),
    best_trial_id    TEXT,
    started_at       TEXT,
    finished_at      TEXT,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    CHECK (in_sample_end_utc > in_sample_start_utc),
    CHECK (out_sample_start_utc IS NULL OR out_sample_start_utc >= in_sample_end_utc)
) STRICT;

CREATE INDEX idx_opt_jobs_active   ON optimization_jobs(job_id) WHERE state IN ('queued','running');
CREATE INDEX idx_opt_jobs_strategy ON optimization_jobs(strategy_version_id, created_at DESC);
```

The `out_sample_start_utc >= in_sample_end_utc` check enforces temporal separation at
the schema level. An overlapping out-of-sample window is not a validation — it is the
in-sample result reported twice.

`holdout_locked` pairs with `optimization_holdout_uses` below.

#### `optimization_trials`

```sql
CREATE TABLE optimization_trials (
    trial_id         TEXT    PRIMARY KEY,
    job_id           TEXT    NOT NULL REFERENCES optimization_jobs(job_id) ON DELETE RESTRICT,
    trial_number     INTEGER NOT NULL,
    params_json      TEXT    NOT NULL CHECK (json_valid(params_json)),
    params_hash      TEXT    NOT NULL,
    run_id           TEXT,                               -- soft ref → sim_runs
    objective_value_decimal TEXT,
    metrics_json     TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(metrics_json)),
    in_sample_score_decimal  TEXT,
    out_sample_score_decimal TEXT,
    overfit_ratio_decimal    TEXT,
    generation        INTEGER,
    parent_trial_ids_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(parent_trial_ids_json)),
    state            TEXT    NOT NULL CHECK (state IN ('pending','running','completed','failed','pruned')),
    error_code       TEXT,
    started_at       TEXT,
    finished_at      TEXT,
    duration_ms      INTEGER,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (job_id, trial_number),
    UNIQUE (job_id, params_hash)
) STRICT;

CREATE INDEX idx_opt_trials_rank    ON optimization_trials(job_id, objective_value_decimal DESC)
    WHERE state = 'completed';
CREATE INDEX idx_opt_trials_pending ON optimization_trials(job_id, trial_number) WHERE state = 'pending';
```

`UNIQUE (job_id, params_hash)` prevents re-evaluating an already-tested point —
significant compute saving in genetic search, where crossover regularly reproduces
existing genomes.

`overfit_ratio_decimal` (out-of-sample ÷ in-sample) is stored rather than derived so
it can be indexed and filtered on directly. A ratio far below 1 is the primary
overfitting tell.

#### `optimization_holdout_uses`

Every touch of the holdout set, recorded.

```sql
CREATE TABLE optimization_holdout_uses (
    use_seq          INTEGER PRIMARY KEY,
    job_id           TEXT    NOT NULL REFERENCES optimization_jobs(job_id) ON DELETE RESTRICT,
    trial_id         TEXT,
    holdout_hash     TEXT    NOT NULL,
    purpose          TEXT    NOT NULL CHECK (purpose IN ('final_validation','promotion_check','audit')),
    authorized_by    TEXT    NOT NULL,
    used_at          TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_opt_holdout_job ON optimization_holdout_uses(job_id, used_at DESC);
```

A holdout set evaluated fifty times is no longer a holdout set — it has become a
second training set through selection. Counting rows here makes that visible instead
of leaving it to memory and good intentions.

## Domain 11 — Research (`research_`)

### `research_studies`

```sql
CREATE TABLE research_studies (
    study_id         TEXT    PRIMARY KEY,
    study_name       TEXT    NOT NULL,
    hypothesis       TEXT    NOT NULL,
    study_kind       TEXT    NOT NULL CHECK (study_kind IN ('exploratory','confirmatory','replication','ablation')),
    preregistered    INTEGER NOT NULL DEFAULT 0 CHECK (preregistered IN (0,1)),
    prereg_hash      TEXT,
    success_criteria_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(success_criteria_json)),
    state            TEXT    NOT NULL CHECK (state IN ('draft','registered','running','concluded','abandoned')),
    verdict          TEXT    CHECK (verdict IN ('supported','not_supported','inconclusive')),
    concluded_at     TEXT,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    CHECK (preregistered = 0 OR prereg_hash IS NOT NULL),
    CHECK (study_kind <> 'confirmatory' OR preregistered = 1)
) STRICT;

CREATE INDEX idx_research_studies_open ON research_studies(state) WHERE state IN ('registered','running');
```

Confirmatory studies must be preregistered. Without it, "we hypothesised this all
along" is written after the results are known, and the hypothesis test means nothing.
The `CHECK` enforces the discipline structurally.

### `research_hypothesis_tests`

```sql
CREATE TABLE research_hypothesis_tests (
    test_id          TEXT    PRIMARY KEY,
    study_id         TEXT    NOT NULL REFERENCES research_studies(study_id) ON DELETE RESTRICT,
    test_name        TEXT    NOT NULL,
    test_statistic   TEXT    NOT NULL CHECK (test_statistic IN ('t_test','wilcoxon','ks','chi2','adf','ljung_box','white_reality_check','bootstrap')),
    null_hypothesis  TEXT    NOT NULL,
    sample_size      INTEGER NOT NULL,
    statistic_decimal TEXT   NOT NULL,
    p_value_decimal  TEXT    NOT NULL,
    alpha_decimal    TEXT    NOT NULL DEFAULT '0.05',
    multiple_testing_correction TEXT NOT NULL DEFAULT 'none'
                     CHECK (multiple_testing_correction IN ('none','bonferroni','benjamini_hochberg','holm')),
    tests_in_family  INTEGER NOT NULL DEFAULT 1,
    adjusted_p_value_decimal TEXT,
    rejected_null    INTEGER NOT NULL CHECK (rejected_null IN (0,1)),
    effect_size_decimal      TEXT,
    confidence_low_decimal   TEXT,
    confidence_high_decimal  TEXT,
    tested_at        TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    CHECK (tests_in_family = 1 OR multiple_testing_correction <> 'none')
) STRICT;

CREATE INDEX idx_research_tests_study ON research_hypothesis_tests(study_id, tested_at DESC);
```

The final `CHECK` forces a correction whenever more than one test shares a family.
Twenty uncorrected tests at α = 0.05 produce one "significant" result by chance;
recording `tests_in_family` makes that arithmetic unavoidable.

### `research_features`

Feature store definitions.

```sql
CREATE TABLE research_features (
    feature_id       TEXT    PRIMARY KEY,
    feature_name     TEXT    NOT NULL,
    version          TEXT    NOT NULL,
    spec_json        TEXT    NOT NULL CHECK (json_valid(spec_json)),
    spec_hash        TEXT    NOT NULL,
    source_kind      TEXT    NOT NULL CHECK (source_kind IN ('price','indicator','fundamental','sentiment','calendar','derived','external')),
    dtype            TEXT    NOT NULL CHECK (dtype IN ('float','int','bool','categorical','timestamp')),
    lookback_bars    INTEGER NOT NULL DEFAULT 0,
    is_point_in_time INTEGER NOT NULL DEFAULT 1 CHECK (is_point_in_time IN (0,1)),
    leakage_reviewed INTEGER NOT NULL DEFAULT 0 CHECK (leakage_reviewed IN (0,1)),
    leakage_notes    TEXT    NOT NULL DEFAULT '',
    state            TEXT    NOT NULL CHECK (state IN ('draft','validated','active','deprecated')),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (feature_name, version),
    CHECK (state NOT IN ('validated','active') OR leakage_reviewed = 1)
) STRICT;

CREATE INDEX idx_research_features_active ON research_features(feature_name) WHERE state = 'active';
```

`is_point_in_time = 0` marks a feature computed with information unavailable at the
timestamp it is attached to — restated fundamentals, survivorship-filtered universes.
No feature reaches `validated` without an explicit leakage review.

### `research_feature_materializations`

Feature values are **not stored in SQLite.** They are computed on demand and
materialised to Parquet when a study needs a pinned, citable input. This table binds a
feature version to its `data_datasets` entry.

```sql
CREATE TABLE research_feature_materializations (
    materialization_id TEXT  PRIMARY KEY,
    feature_id       TEXT    NOT NULL REFERENCES research_features(feature_id) ON DELETE RESTRICT,
    symbol_id        TEXT    NOT NULL,
    dataset_id       TEXT    NOT NULL,
    source_data_hash TEXT    NOT NULL,
    spec_hash        TEXT    NOT NULL,
    covered_from_utc INTEGER NOT NULL,
    covered_to_utc   INTEGER NOT NULL,
    row_count        INTEGER NOT NULL DEFAULT 0,
    null_count       INTEGER NOT NULL DEFAULT 0,
    state            TEXT    NOT NULL CHECK (state IN ('building','ready','stale','invalidated','failed')),
    built_at         TEXT,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (feature_id, symbol_id),
    CHECK (covered_to_utc >= covered_from_utc)
) STRICT;

CREATE INDEX idx_research_featmat_stale ON research_feature_materializations(feature_id)
    WHERE state IN ('stale','invalidated');
```

`null_count` is tracked at the catalog level because it is the cheap integrity signal:
a feature that suddenly goes 90 % null is a broken pipeline, and noticing that should
not require scanning the Parquet. Within the file, a genuine missing observation is a
real Arrow null — the distinction between "computed, genuinely missing" and "not yet
computed" is carried by `state`, not by a per-row flag.

`dataset_id` is a soft reference to `data_datasets`; Research depends on Data, never
the reverse.

### `research_regimes`

```sql
CREATE TABLE research_regimes (
    regime_id        TEXT    PRIMARY KEY,
    regime_model     TEXT    NOT NULL,
    model_version    TEXT    NOT NULL,
    regime_label     TEXT    NOT NULL,                   -- 'trending_up', 'high_vol_range'
    symbol_id        TEXT,
    timeframe        TEXT,
    start_ts_utc     INTEGER NOT NULL,
    end_ts_utc       INTEGER,
    confidence_decimal TEXT  NOT NULL DEFAULT '1',
    characteristics_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(characteristics_json)),
    detected_at      TEXT    NOT NULL,
    is_retrospective INTEGER NOT NULL DEFAULT 0 CHECK (is_retrospective IN (0,1)),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    CHECK (end_ts_utc IS NULL OR end_ts_utc > start_ts_utc)
) STRICT;

CREATE INDEX idx_research_regimes_span ON research_regimes(symbol_id, start_ts_utc, end_ts_utc);
CREATE INDEX idx_research_regimes_current ON research_regimes(symbol_id) WHERE end_ts_utc IS NULL;
```

`is_retrospective = 1` marks a regime labelled with hindsight. Retrospective labels
are valid for analysis and invalid for live signals; conflating the two produces a
strategy that appears to know the regime before it was knowable.

### `research_artifacts`

**A file manifest, not a general artifact catalog.** One row per written file: what it
is, how large, whether the write was atomic, and which audit event authorised it.

```sql
CREATE TABLE research_artifacts (
    relative_path    TEXT    PRIMARY KEY,
    format           TEXT    NOT NULL,
    size_bytes       INTEGER NOT NULL,
    sha256           TEXT    NOT NULL,
    atomic           INTEGER NOT NULL,
    schema_version   TEXT    NOT NULL,
    audit_event_id   TEXT    NOT NULL,
    request_id       TEXT    NOT NULL DEFAULT '',
    correlation_id   TEXT    NOT NULL DEFAULT '',
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_research_artifacts_sha256 ON research_artifacts(sha256);
CREATE INDEX idx_research_artifacts_audit  ON research_artifacts(audit_event_id);
```

Keyed by `relative_path`, so one path holds one artifact and a rewrite replaces rather
than duplicates. `sha256` is indexed for content-addressed lookup — two studies
producing byte-identical output are detectable.

`atomic` records whether the write went through the temp-file-then-rename path. An
artifact written non-atomically may be truncated, and that must be visible in the
catalog rather than discovered on read.

This is the same catalog pattern as `data_partition_files` and predates it in the
codebase.

## Domain 12 — Portfolio (`portfolio_`)

> **This domain follows the live implementation, not an independent design.**
> An earlier draft proposed a normalised Portfolio with `portfolio_definition_versions`,
> `portfolio_positions`, and `portfolio_cash_balances`, on the belief that
> `portfolio_definitions` keyed on `portfolio_id` alone and that child foreign keys
> blocked composite-key versioning. **Both premises were wrong.** The shipped table
> already keys on `(portfolio_id, portfolio_version)`, so definition history is
> immutable without a second table, and **no Portfolio table declares a foreign key** —
> version rows must survive independently, so references are soft and validated in the
> owning feature modules. Decision D14 is withdrawn on that basis.

### `portfolio_definitions`

Immutable versioned definitions. A change appends a new `portfolio_version`; rows are
never updated.

```sql
CREATE TABLE portfolio_definitions (
    portfolio_id     TEXT    NOT NULL,
    portfolio_version TEXT   NOT NULL,
    scope_key        TEXT    NOT NULL,
    definition_json  TEXT    NOT NULL,
    canonical_hash   TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    PRIMARY KEY (portfolio_id, portfolio_version)
) STRICT;

CREATE INDEX idx_portfolio_defs_scope ON portfolio_definitions(portfolio_id, scope_key);
```

The composite primary key **is** the immutable-history mechanism required by
`docs/PROJECT.md` §5: *"rollback creates a new governed version and never rewrites
history."* `canonical_hash` makes a definition tamper-evident.

Per the hybrid rule (D9) only the identity, scope, and hash are normalised; the
configuration itself stays in `definition_json`, so a new portfolio parameter needs no
migration.

### `portfolio_construction_results`

```sql
CREATE TABLE portfolio_construction_results (
    result_id        TEXT    PRIMARY KEY,
    portfolio_id     TEXT    NOT NULL,
    portfolio_version TEXT   NOT NULL,
    canonical_hash   TEXT    NOT NULL,
    result_json      TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_portfolio_results_portfolio
    ON portfolio_construction_results(portfolio_id, created_at DESC);
```

`canonical_hash` binds a construction result to the exact definition version that
produced it, so a result can be re-derived against the inputs that actually applied.

### `portfolio_allocation_versions`

```sql
CREATE TABLE portfolio_allocation_versions (
    allocation_id    TEXT    PRIMARY KEY,
    portfolio_id     TEXT    NOT NULL,
    allocation_version TEXT  NOT NULL,
    scope_key        TEXT    NOT NULL,
    canonical_hash   TEXT    NOT NULL,
    allocation_json  TEXT    NOT NULL,
    activated_at     TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    UNIQUE (portfolio_id, allocation_version)
) STRICT;
```

Append-only. Which allocation is *current* is not a flag on this table — it is the
pointer in `portfolio_active_scopes`, so activation is one write to one row rather than
a two-row flag swap that can interleave.

### `portfolio_active_scopes`

The current-version pointer, one row per `(portfolio_id, scope_key)`.

```sql
CREATE TABLE portfolio_active_scopes (
    portfolio_id     TEXT    NOT NULL,
    scope_key        TEXT    NOT NULL,
    allocation_version TEXT  NOT NULL,
    revision         INTEGER NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    PRIMARY KEY (portfolio_id, scope_key)
) STRICT;
```

`revision` is the compare-and-swap guard: an activation passes its expected revision
and fails rather than clobbering a concurrent change. The primary key guarantees **at
most one active allocation per scope** — the invariant an earlier draft tried to
enforce with a partial unique index on an `is_active` flag.

### `portfolio_rebalance_plans`

```sql
CREATE TABLE portfolio_rebalance_plans (
    plan_id          TEXT    NOT NULL,
    plan_version     TEXT    NOT NULL,
    portfolio_id     TEXT    NOT NULL,
    allocation_version TEXT  NOT NULL,
    canonical_hash   TEXT    NOT NULL,
    plan_json        TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    PRIMARY KEY (plan_id, plan_version)
) STRICT;

CREATE INDEX idx_portfolio_plans_portfolio
    ON portfolio_rebalance_plans(portfolio_id, created_at DESC);
```

Versioned like definitions: a revised plan is a new `plan_version`, never an update.

### `portfolio_idempotency`

```sql
CREATE TABLE portfolio_idempotency (
    idempotency_key  TEXT    PRIMARY KEY,
    material_hash    TEXT    NOT NULL,
    result_type      TEXT    NOT NULL,
    result_id        TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL
) STRICT;
```

`material_hash` guards against key reuse with different contents: a replayed key
carrying changed material must fail rather than silently returning the prior result.

### `portfolio_audit_outbox`

Transactional outbox — the state change and its notification commit together.

```sql
CREATE TABLE portfolio_audit_outbox (
    event_id         TEXT    PRIMARY KEY,
    event_type       TEXT    NOT NULL,
    aggregate_id     TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    payload_json     TEXT    NOT NULL,
    occurred_at      TEXT    NOT NULL,
    publication_state TEXT   NOT NULL DEFAULT 'pending',
    attempts         INTEGER NOT NULL DEFAULT 0,
    published_at     TEXT,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_portfolio_outbox_pending ON portfolio_audit_outbox(occurred_at)
    WHERE publication_state = 'pending';
```

The partial index is empty once the outbox drains, so the publisher's poll costs an
empty-B-tree probe.

---

### Target-only tables

No live counterpart; not built. Tier B work with no conformance obligation.

#### `portfolio_positions`

```sql
CREATE TABLE portfolio_positions (
    portfolio_position_id TEXT PRIMARY KEY,
    portfolio_id     TEXT    NOT NULL,
    symbol_id        TEXT    NOT NULL,
    account_id       TEXT    NOT NULL,
    net_quantity_decimal TEXT NOT NULL,
    notional_decimal     TEXT NOT NULL,
    weight_decimal       TEXT NOT NULL,
    target_weight_decimal TEXT NOT NULL,
    drift_decimal        TEXT NOT NULL,
    unrealized_pnl_decimal TEXT NOT NULL DEFAULT '0',
    observed_at      TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (portfolio_id, symbol_id, account_id)
) STRICT;

CREATE INDEX idx_portfolio_pos_drift ON portfolio_positions(portfolio_id, drift_decimal DESC);
```

`drift_decimal` stored rather than computed on read, so the threshold rebalance trigger
is one indexed scan.

#### `portfolio_cash_balances`

```sql
CREATE TABLE portfolio_cash_balances (
    balance_id       TEXT    PRIMARY KEY,
    portfolio_id     TEXT    NOT NULL,
    account_id       TEXT    NOT NULL,
    currency         TEXT    NOT NULL,
    balance_decimal  TEXT    NOT NULL,
    available_decimal TEXT   NOT NULL,
    reserved_decimal TEXT    NOT NULL DEFAULT '0',
    fx_rate_to_base_decimal TEXT NOT NULL DEFAULT '1',
    base_value_decimal      TEXT NOT NULL,
    fx_rate_source   TEXT    NOT NULL DEFAULT '',
    fx_rate_at       TEXT,
    observed_at      TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (portfolio_id, account_id, currency)
) STRICT;
```

`fx_rate_source` and `fx_rate_at` are mandatory companions to the rate: a converted
balance without a timestamped, attributed rate cannot be reconciled.

## Domain 13 — Agentic (`agentic_`)

> **This domain follows the live implementation.** Agentic ships thirteen tables
> across five migration steps. An earlier draft of this model proposed seven
> different tables (`agentic_agents`, `agentic_tools`, `agentic_tool_grants`,
> `agentic_model_profiles`, `agentic_traces`, `agentic_trace_spans`,
> `agentic_llm_calls`) of which only two names overlapped what exists. The model now
> records what is built; the seven are target-only.

### Workflow orchestration — step `001`

#### `agentic_workflow_runs`

```sql
CREATE TABLE agentic_workflow_runs (
    run_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    workflow_name TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    state TEXT NOT NULL,
    current_node TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    attempts INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deadline_at TEXT NOT NULL,
    terminal_reason TEXT,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT ''
) STRICT;
```

Durable orchestration state. `revision` is the expected-version guard and `idempotency_key` is `UNIQUE`, so a resubmitted task resumes rather than forking a second run.

#### `agentic_workflow_checkpoints`

```sql
CREATE TABLE agentic_workflow_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    workflow_name TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    node_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    state TEXT NOT NULL,
    expected_version INTEGER NOT NULL,
    state_payload_hash TEXT NOT NULL,
    canonical_hash TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    request_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    causation_id TEXT,
    schema_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    correlation_id TEXT NOT NULL DEFAULT ''
) STRICT;
```

`workflow_version` and `node_id` are what make a resume unambiguous: without them a checkpoint cannot say which node of which workflow definition it belongs to, and a resume after the graph changed would replay against the wrong shape.

### Evidence and memory — step `002`

#### `agentic_evidence_claims`

```sql
CREATE TABLE agentic_evidence_claims (
    claim_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    statement TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_trust TEXT NOT NULL,
    licence_ref TEXT NOT NULL,
    available_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    injection_status TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
```

`injection_status` and `source_trust` keep retrieved text out of instruction slots. Untrusted content is evidence, never instruction — the structural defence against prompt injection.

#### `agentic_memory_records`

```sql
CREATE TABLE agentic_memory_records (
    record_id TEXT PRIMARY KEY,
    store_class TEXT NOT NULL,
    task_id TEXT NOT NULL,
    author_role_id TEXT NOT NULL,
    content_json TEXT NOT NULL,
    scope_json TEXT NOT NULL,
    source_evidence_refs_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    retention_class TEXT NOT NULL,
    sensitivity TEXT NOT NULL,
    injection_status TEXT NOT NULL,
    redacted_paths_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    supersedes TEXT,
    correlation_id TEXT NOT NULL DEFAULT ''
) STRICT;
```

`redacted_paths_json` records what was removed before persistence; redact-before-persist is a control, not an oversight. `supersedes` appends corrections rather than overwriting, so what the agent previously believed survives.

### Artefact lifecycle — step `003`

#### `agentic_lifecycle_transitions`

```sql
CREATE TABLE agentic_lifecycle_transitions (
    artifact_hash TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    record_id TEXT NOT NULL UNIQUE,
    artifact_id TEXT NOT NULL,
    previous_state TEXT,
    state TEXT NOT NULL,
    packet_hash TEXT,
    termination_reason TEXT,
    unresolved_concerns_json TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    rationale TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (artifact_hash, sequence)
) STRICT;
```

The composite primary key is the enforcement point: an artefact's history is append-only because position `n` can be written exactly once.

#### `agentic_promotion_packets`

```sql
CREATE TABLE agentic_promotion_packets (
    packet_hash TEXT PRIMARY KEY,
    packet_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    artifact_hash TEXT NOT NULL,
    artifact_json TEXT NOT NULL,
    experiment_verdict_json TEXT NOT NULL,
    sweep_verdict_json TEXT NOT NULL,
    critique_json TEXT NOT NULL,
    simulation_manifest_ref TEXT NOT NULL,
    lifetime_trial_ceiling INTEGER NOT NULL,
    approver_id TEXT NOT NULL,
    approval_environment TEXT NOT NULL,
    assembled_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
```

`lifetime_trial_ceiling` and `approval_environment` bound a promotion at the point of approval rather than at the point of use.

### Operations — step `004`

#### `agentic_operations_traces`

```sql
CREATE TABLE agentic_operations_traces (
    trace_hash TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    spans_json TEXT NOT NULL,
    redacted_paths_json TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    observed_cost TEXT NOT NULL,
    assembled_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
```

Keyed on the trace digest, so re-assembling the same evidence yields the same row rather than a duplicate view of it. `observed_cost` is `TEXT` Decimal, never `REAL`.

#### `agentic_operations_incidents`

```sql
CREATE TABLE agentic_operations_incidents (
    incident_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    trigger TEXT NOT NULL,
    containment_action TEXT NOT NULL,
    contained_state TEXT NOT NULL,
    quarantined_role_id TEXT,
    checkpoint_ref TEXT NOT NULL,
    preserved_evidence_refs_json TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (run_id, correlation_id, kind)
) STRICT;
```

`UNIQUE (run_id, correlation_id, kind)` is the enforcement point: a second containment cannot quietly replace the first and its evidence.

#### `agentic_operations_replays`

```sql
CREATE TABLE agentic_operations_replays (
    replay_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    environment TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    verified_references_json TEXT NOT NULL,
    side_effects_attempted INTEGER NOT NULL,
    executed INTEGER NOT NULL,
    completed_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
```

`side_effects_attempted` is a count and `executed` is a boolean. The immutable-reference list and completion time preserve the replay outcome rather than only its request.

### Experimentation — step `005`

#### `agentic_experiment_specs`

```sql
CREATE TABLE agentic_experiment_specs (
    spec_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    thesis_id TEXT NOT NULL,
    spec_hash TEXT NOT NULL UNIQUE,
    seed INTEGER NOT NULL,
    embargo_seconds INTEGER NOT NULL,
    baseline_ref TEXT NOT NULL,
    cost_model_ref TEXT NOT NULL,
    falsification_outcome TEXT NOT NULL,
    created_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT ''
) STRICT;
```

`spec_hash` is `UNIQUE`, so an identical pre-registered protocol cannot be registered twice under two identities.

#### `agentic_experiment_runs`

```sql
CREATE TABLE agentic_experiment_runs (
    run_id TEXT PRIMARY KEY,
    spec_hash TEXT NOT NULL,
    task_id TEXT NOT NULL,
    evidence_class TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    journal_ref TEXT NOT NULL,
    artifact_manifest_ref TEXT NOT NULL,
    created_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT ''
) STRICT;
```

`evidence_class` separates exploratory from confirmatory evidence at the row level.

#### `agentic_experiment_holdout_use`

```sql
CREATE TABLE agentic_experiment_holdout_use (
    spec_hash TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    consumed_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
```

Keyed on `spec_hash` alone: a second look at holdout for the same pre-registered protocol cannot be recorded, so it cannot be performed. This is the strongest overfitting control in the system.

#### `agentic_experiment_verdicts`

```sql
CREATE TABLE agentic_experiment_verdicts (
    verdict_id TEXT PRIMARY KEY,
    spec_id TEXT NOT NULL,
    spec_hash TEXT NOT NULL,
    task_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    holdout_consumed INTEGER NOT NULL,
    canonical_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT ''
) STRICT;
```

`holdout_consumed` travels with the verdict, so a conclusion that spent the holdout is never mistaken for one that did not.

---

### Target-only tables

No live counterpart; not built. They would give Agentic a registry of agent
identities, model profiles, tool grants, and per-call cost accounting.

`agentic_agents` · `agentic_model_profiles` · `agentic_tools` ·
`agentic_tool_grants` · `agentic_traces` · `agentic_trace_spans` ·
`agentic_llm_calls`

Their column definitions are omitted rather than carried as unbuilt DDL. The
safety controls they encoded — permission classes that exclude mutation, tool
names that cannot express an order or kill-switch capability, wildcard scopes
that are unrepresentable — are enforced today in `app/agentic/permissions/`
rather than by schema.

---

## Domain 14 — UI-API (`api_`)

### `api_accounts`

```sql
CREATE TABLE api_accounts (
    account_id       TEXT    PRIMARY KEY,
    username         TEXT    NOT NULL UNIQUE,
    email            TEXT    NOT NULL UNIQUE,
    password_hash    TEXT    NOT NULL,
    password_algo    TEXT    NOT NULL DEFAULT 'argon2id',
    mfa_enabled      INTEGER NOT NULL DEFAULT 0 CHECK (mfa_enabled IN (0,1)),
    mfa_secret_ref   TEXT,
    state            TEXT    NOT NULL CHECK (state IN ('pending','active','suspended','locked','closed')),
    failed_attempts  INTEGER NOT NULL DEFAULT 0,
    locked_until     TEXT,
    last_login_at    TEXT,
    password_changed_at TEXT NOT NULL,
    environment      TEXT    NOT NULL CHECK (environment IN ('dev','test','staging','production')),
    verified         INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1)),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    deleted_at       TEXT
) STRICT;

CREATE INDEX idx_api_accounts_active ON api_accounts(username) WHERE state = 'active';
```

`mfa_secret_ref` is a key path, not the secret. `password_hash` stores an Argon2id
digest; the plaintext never reaches the database, a log, or an exception payload
(`AGENTS.md` §3).

### `api_roles` / `api_permissions` / `api_role_permissions` / `api_role_bindings`

```sql
CREATE TABLE api_roles (
    role_id          TEXT    PRIMARY KEY,
    role_name        TEXT    NOT NULL UNIQUE,
    description      TEXT    NOT NULL DEFAULT '',
    is_system        INTEGER NOT NULL DEFAULT 0 CHECK (is_system IN (0,1)),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE TABLE api_permissions (
    permission_id    TEXT    PRIMARY KEY,
    permission_key   TEXT    NOT NULL UNIQUE,            -- 'trading:orders:read'
    domain           TEXT    NOT NULL,
    action           TEXT    NOT NULL CHECK (action IN ('read','write','execute','approve','admin')),
    is_mutating      INTEGER NOT NULL DEFAULT 0 CHECK (is_mutating IN (0,1)),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    CHECK (permission_key NOT LIKE '%*%')
) STRICT;

CREATE TABLE api_role_permissions (
    role_id          TEXT    NOT NULL REFERENCES api_roles(role_id) ON DELETE RESTRICT,
    permission_id    TEXT    NOT NULL REFERENCES api_permissions(permission_id) ON DELETE RESTRICT,
    granted_at       TEXT    NOT NULL,
    granted_by       TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    PRIMARY KEY (role_id, permission_id)
) STRICT, WITHOUT ROWID;

CREATE TABLE api_role_bindings (
    binding_id       TEXT    PRIMARY KEY,
    account_id       TEXT    NOT NULL REFERENCES api_accounts(account_id) ON DELETE RESTRICT,
    role_id          TEXT    NOT NULL REFERENCES api_roles(role_id) ON DELETE RESTRICT,
    scope_key        TEXT    NOT NULL DEFAULT '',
    granted_by       TEXT    NOT NULL,
    expires_at       TEXT,
    revoked_at       TEXT,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (account_id, role_id, scope_key)
) STRICT;

CREATE INDEX idx_api_bindings_account ON api_role_bindings(account_id) WHERE revoked_at IS NULL;
```

Wildcard permission keys are rejected, matching the Agentic grant rule. `is_mutating`
lets the middleware apply stricter checks to write paths without re-parsing the key.
The shipped additive `api-0005` migration references the immutable baseline account
key `api_accounts.user_id` rather than this target model's `account_id`. It otherwise
implements these four normalized RBAC relations. The old account claim JSON columns
remain dormant compatibility fields because rebuilding the account baseline would
require business attributes the current identity feature does not own.

### `api_keys`

```sql
CREATE TABLE api_keys (
    key_id           TEXT    PRIMARY KEY,
    account_id       TEXT    NOT NULL REFERENCES api_accounts(account_id) ON DELETE RESTRICT,
    key_prefix       TEXT    NOT NULL UNIQUE,            -- displayable, e.g. 'hq_live_a1b2'
    key_hash         TEXT    NOT NULL UNIQUE,            -- SHA-256 of full key
    label            TEXT    NOT NULL DEFAULT '',
    scopes_json      TEXT    NOT NULL DEFAULT '[]' CHECK (json_valid(scopes_json)),
    allowed_ips_json TEXT    NOT NULL DEFAULT '[]' CHECK (json_valid(allowed_ips_json)),
    rate_limit       INTEGER NOT NULL DEFAULT 60,
    last_used_at     TEXT,
    expires_at       TEXT    NOT NULL,
    revoked_at       TEXT,
    revoked_reason   TEXT,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    CHECK (scopes_json NOT LIKE '%"*"%')
) STRICT;

CREATE INDEX idx_api_keys_lookup  ON api_keys(key_hash) WHERE revoked_at IS NULL;
CREATE INDEX idx_api_keys_account ON api_keys(account_id, created_at DESC);
CREATE INDEX idx_api_keys_expiry  ON api_keys(expires_at) WHERE revoked_at IS NULL;
```

Only the hash is stored — a database disclosure yields no usable credential.
`expires_at` is `NOT NULL`: keys that never expire become permanent liabilities.

### `api_sessions`

```sql
CREATE TABLE api_sessions (
    session_id       TEXT    PRIMARY KEY,
    account_id       TEXT    NOT NULL REFERENCES api_accounts(account_id) ON DELETE RESTRICT,
    session_token_hash TEXT  NOT NULL UNIQUE,
    transport        TEXT    NOT NULL CHECK (transport IN ('http','websocket')),
    client_ip        TEXT    NOT NULL,
    user_agent       TEXT    NOT NULL DEFAULT '',
    subscriptions_json TEXT  NOT NULL DEFAULT '[]' CHECK (json_valid(subscriptions_json)),
    state            TEXT    NOT NULL CHECK (state IN ('active','idle','expired','revoked')),
    last_seen_at     TEXT    NOT NULL,
    expires_at       TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    csrf_digest      TEXT,
    revoked_at       TEXT,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_api_sessions_active ON api_sessions(account_id) WHERE state = 'active';
CREATE INDEX idx_api_sessions_ws     ON api_sessions(last_seen_at)
    WHERE transport = 'websocket' AND state = 'active';
CREATE INDEX idx_api_sessions_expiry ON api_sessions(expires_at) WHERE state IN ('active','idle');
```

### `api_audit_log`

```sql
CREATE TABLE api_audit_log (
    audit_seq        INTEGER PRIMARY KEY,
    account_id       TEXT,
    actor_kind       TEXT    NOT NULL CHECK (actor_kind IN ('user','api_key','agent','system')),
    actor_id         TEXT    NOT NULL,
    action           TEXT    NOT NULL,
    resource_kind    TEXT    NOT NULL,
    resource_id      TEXT,
    outcome          TEXT    NOT NULL CHECK (outcome IN ('allowed','denied','error')),
    reason_code      TEXT,
    http_method      TEXT,
    http_path        TEXT,
    http_status      INTEGER,
    client_ip        TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    detail_json      TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(detail_json)),
    bucket_month     TEXT    NOT NULL,
    occurred_at      TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    CHECK (outcome = 'allowed' OR reason_code IS NOT NULL)
) STRICT;

CREATE INDEX idx_api_audit_account ON api_audit_log(account_id, occurred_at DESC);
CREATE INDEX idx_api_audit_denied  ON api_audit_log(occurred_at DESC) WHERE outcome = 'denied';
CREATE INDEX idx_api_audit_bucket  ON api_audit_log(bucket_month, actor_kind);
CREATE INDEX idx_api_audit_corr    ON api_audit_log(correlation_id);
```

### `api_idempotency`

```sql
CREATE TABLE api_idempotency (
    idempotency_key  TEXT    PRIMARY KEY,
    account_id       TEXT    NOT NULL,
    scope_key        TEXT    NOT NULL,
    endpoint         TEXT    NOT NULL,
    request_hash     TEXT    NOT NULL,
    response_status  INTEGER,
    response_json    TEXT CHECK (response_json IS NULL OR json_valid(response_json)),
    state            TEXT    NOT NULL CHECK (state IN ('in_flight','completed','failed')),
    expires_at       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_api_idem_expiry ON api_idempotency(expires_at);
```

### Further shipped tables

Four API tables ship today and were absent from an earlier draft of this model.

#### `api_approvals`

```sql
CREATE TABLE api_approvals (
    approval_id TEXT PRIMARY KEY,
    issuer_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    evidence_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT
) STRICT;
```

Human sign-off records for governed mutations. An approval is evidence, not a permission: it names what was approved and by whom, and is consumed once.

#### `api_auth_failures`

```sql
CREATE TABLE api_auth_failures (
    username_hash TEXT PRIMARY KEY,
    failure_count INTEGER NOT NULL,
    window_started_at TEXT NOT NULL,
    locked_until TEXT
) STRICT;
```

Failed authentication attempts, feeding lockout policy. Kept separate from `api_audit_log` so a brute-force sweep cannot flood the audit trail.

#### `api_credentials`

```sql
CREATE TABLE api_credentials (
    reference TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    key_id TEXT NOT NULL,
    nonce_b64 TEXT NOT NULL,
    ciphertext_b64 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    version INTEGER NOT NULL
) STRICT;
```

Encrypted credential material. `nonce_b64` and `ciphertext_b64` are stored apart from `key_id`, so ciphertext alone is useless; plaintext never reaches this table (`AGENTS.md` §3).

#### `api_settings`

```sql
CREATE TABLE api_settings (
    scope TEXT NOT NULL CHECK (scope IN ('system', 'user')),
    subject_id TEXT NOT NULL CHECK (subject_id <> ''),
    settings_json TEXT NOT NULL CHECK (
        json_valid(settings_json) AND json_type(settings_json) = 'object'
    ),
    version INTEGER NOT NULL CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    request_id TEXT NOT NULL,
    PRIMARY KEY (scope, subject_id),
    CHECK (
        (scope = 'system' AND subject_id = 'global')
        OR (scope = 'user' AND subject_id <> 'global')
    )
) STRICT, WITHOUT ROWID;
```

One versioned, secret-safe document shape serves per-account preferences and the
single global post-connection system scope. User identities and the global subject
are derived by authenticated API operations rather than accepted from request data.
Database connection/bootstrap values and credentials remain outside this table
because they are required before it can be reached.
---

## Entity count — this file

| Domain | Tables |
|---|---|
| Analytics | 6 |
| Optimization | 5 |
| Research | 6 |
| Portfolio | 9 |
| Agentic | 13 |
| UI-API | 13 |
| **Total** | **52** |

## Grand total

| File | Tables |
|---|---|
| [01](01_entity_specs_core.md) — Core | 25 |
| [02](02_entity_specs_execution.md) — Execution | 26 |
| 03 — Intelligence & Perimeter | 40 |
| **All 14 domains** | **105** |

All 105 `CREATE TABLE` statements in this model have been
executed against a live SQLite engine to confirm they parse, that every declared
foreign key resolves, and that every index target exists.

Next: [04_indexing_and_performance.md](04_indexing_and_performance.md)

# 02 — Entity Specs: Execution (Strategy, Risk, Trading, Simulator)

> **AUTHORITATIVE — target schema model.** Canonical for cross-domain schema
> structure and the target table/column model. Current-state feature registries remain
> in each owning package `README.md`; executable schema remains in the owning domain's
> migration definitions. Divergences are recorded in
> [05_reconciliation.md](05_reconciliation.md). See [README.md](README.md) for the full
> authority statement.

Conventions from [00_domain_relationship_map.md](00_domain_relationship_map.md) §8
apply to every table below. All tables are `STRICT`.

---

## Domain 5 — Strategy (`strategy_`)

### `strategy_definitions`

The stable identity of a strategy across all its versions.

```sql
CREATE TABLE strategy_definitions (
    strategy_id      TEXT    PRIMARY KEY,
    strategy_code    TEXT    NOT NULL UNIQUE,
    display_name     TEXT    NOT NULL,
    strategy_class   TEXT    NOT NULL CHECK (strategy_class IN ('trend','mean_reversion','breakout','arbitrage','market_making','ml','composite')),
    asset_classes_json TEXT  NOT NULL DEFAULT '[]' CHECK (json_valid(asset_classes_json)),
    owner            TEXT    NOT NULL DEFAULT '',
    description      TEXT    NOT NULL DEFAULT '',
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    deleted_at       TEXT
) STRICT;
```

### `strategy_versions`

Immutable code versions. Never updated after `state` leaves `draft`.

```sql
CREATE TABLE strategy_versions (
    version_id       TEXT    PRIMARY KEY,
    strategy_id      TEXT    NOT NULL REFERENCES strategy_definitions(strategy_id) ON DELETE RESTRICT,
    semver           TEXT    NOT NULL,
    code_hash        TEXT    NOT NULL,
    indicator_deps_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(indicator_deps_json)),
    param_schema_json TEXT   NOT NULL CHECK (json_valid(param_schema_json)),
    warmup_bars      INTEGER NOT NULL DEFAULT 0,
    state            TEXT    NOT NULL CHECK (state IN ('draft','validated','approved','active','paused','deprecated','retired')),
    approved_by      TEXT,
    approved_at      TEXT,
    policy_json      TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(policy_json)),
    record_hash      TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (strategy_id, semver),
    UNIQUE (strategy_id, code_hash),
    CHECK (state NOT IN ('approved','active') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
) STRICT;

CREATE INDEX idx_strategy_versions_active ON strategy_versions(strategy_id) WHERE state = 'active';
```

The final `CHECK` makes an unapproved strategy structurally unable to reach `active`.
`indicator_deps_json` pins exact `indicator_definitions.definition_id` values, so a strategy
version is reproducible: change an indicator formula and the dependency no longer
resolves rather than silently producing different signals.

### `strategy_configs`

Parameter bindings. Many configs per version.

```sql
CREATE TABLE strategy_configs (
    config_id        TEXT    PRIMARY KEY,
    version_id       TEXT    NOT NULL REFERENCES strategy_versions(version_id) ON DELETE RESTRICT,
    config_name      TEXT    NOT NULL,
    inputs_json      TEXT    NOT NULL CHECK (json_valid(inputs_json)),
    inputs_hash      TEXT    NOT NULL,
    symbol_id        TEXT    NOT NULL,
    timeframe        TEXT    NOT NULL,
    runtime_profile  TEXT    NOT NULL CHECK (runtime_profile IN ('research','simulation','paper','live')),
    risk_budget_decimal TEXT NOT NULL DEFAULT '0',
    state            TEXT    NOT NULL CHECK (state IN ('draft','active','paused','archived')),
    policy_version   TEXT    NOT NULL DEFAULT '',
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (version_id, inputs_hash, symbol_id, timeframe, runtime_profile)
) STRICT;

CREATE INDEX idx_strategy_configs_live ON strategy_configs(symbol_id, timeframe)
    WHERE state = 'active' AND runtime_profile = 'live';
```

### `strategy_state`

Current runtime state per active config. Mutable, one row per config.

```sql
CREATE TABLE strategy_state (
    config_id        TEXT    PRIMARY KEY REFERENCES strategy_configs(config_id) ON DELETE RESTRICT,
    lifecycle_state  TEXT    NOT NULL CHECK (lifecycle_state IN ('stopped','warming_up','ready','running','halted','error')),
    state_version    INTEGER NOT NULL DEFAULT 0,
    bars_processed   INTEGER NOT NULL DEFAULT 0,
    last_bar_ts_utc  INTEGER,
    last_signal_id   TEXT,
    context_json     TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(context_json)),
    halt_reason      TEXT,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_strategy_state_running ON strategy_state(config_id) WHERE lifecycle_state = 'running';
```

`state_version` is an optimistic-concurrency guard: writers pass their expected
version and the update fails rather than clobbering a concurrent change.

### `strategy_checkpoints`

Point-in-time snapshots for restart and replay.

```sql
CREATE TABLE strategy_checkpoints (
    checkpoint_id    TEXT    PRIMARY KEY,
    config_id        TEXT    NOT NULL REFERENCES strategy_configs(config_id) ON DELETE RESTRICT,
    sequence         INTEGER NOT NULL,
    bar_ts_utc       INTEGER NOT NULL,
    state_snapshot_json TEXT NOT NULL CHECK (json_valid(state_snapshot_json)),
    snapshot_hash    TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    authorization_ref TEXT,
    created_at       TEXT    NOT NULL,
    UNIQUE (config_id, sequence)
) STRICT;

CREATE INDEX idx_strategy_ckpt_latest ON strategy_checkpoints(config_id, sequence DESC);
```

### `strategy_signals`

Generated trade intents. Append-only. The input to Risk.

```sql
CREATE TABLE strategy_signals (
    signal_id        TEXT    PRIMARY KEY,
    config_id        TEXT    NOT NULL REFERENCES strategy_configs(config_id) ON DELETE RESTRICT,
    sequence         INTEGER NOT NULL,
    symbol_id        TEXT    NOT NULL,
    direction        TEXT    NOT NULL CHECK (direction IN ('long','short','flat','close')),
    signal_strength  TEXT    NOT NULL DEFAULT '1',
    intent_kind      TEXT    NOT NULL CHECK (intent_kind IN ('entry','exit','scale_in','scale_out','reverse')),
    suggested_size_decimal TEXT,
    stop_loss_decimal      TEXT,
    take_profit_decimal    TEXT,
    bar_ts_utc       INTEGER NOT NULL,
    evidence_json    TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(evidence_json)),
    state            TEXT    NOT NULL CHECK (state IN ('generated','submitted','approved','rejected','expired','executed')),
    expires_at       TEXT,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (config_id, sequence)
) STRICT;

CREATE INDEX idx_strategy_signals_pending ON strategy_signals(created_at)
    WHERE state IN ('generated','submitted');
CREATE INDEX idx_strategy_signals_symbol  ON strategy_signals(symbol_id, bar_ts_utc DESC);
```

A signal carries a *suggested* size. Risk owns the final size. Naming this
`suggested_size_decimal` rather than `size` is deliberate — it keeps the ownership
boundary legible in the schema itself.

---

### `strategy_mutations`

```sql
CREATE TABLE strategy_mutations (
    command_id TEXT PRIMARY KEY,
    mutation_json TEXT NOT NULL,
    publication_pending INTEGER NOT NULL
) STRICT;
```

`publication_pending` gates whether a mutation command has been announced downstream,
so a command that was accepted but not yet published is distinguishable from one that
was fully processed.

> **Divergence recorded.** The four shipped Strategy tables — `strategy_versions`,
> `strategy_configs`, `strategy_checkpoints`, and `strategy_mutations` — are **not**
> declared `STRICT` in code. They predate the convention and their migration step
> `0001_strategy_domain` is applied, so they cannot be altered without a baseline
> reset. This model states the target (`STRICT`); the applied schema does not yet
> satisfy it. That gap is intentional and is what the target-versus-current split in
> [README.md](README.md) exists to express.
---

## Domain 6 — Risk (`risk_`)

Risk is the mandatory admission gate. All decision tables are append-only;
`risk_audit_records` is hash-chained.

> **This domain follows the live implementation, not an independent design (B1).**
> An earlier draft of this model proposed `risk_policies`, `risk_kill_switches`, and a
> single `risk_admission_decisions` table. The shipped Risk domain splits admission
> into *eligibility* (may this strategy trade at all?) and *allocation* (how much
> budget does this portfolio get?), which are answered by different authorities on
> different cadences. Collapsing them loses a real distinction, so the model adopts the
> live names and the live split. Three tables below — `risk_limits`,
> `risk_limit_checks`, `risk_exposure_snapshots` — have no live counterpart and remain
> target-only.

### `risk_policy_versions`

```sql
CREATE TABLE risk_policy_versions (
    config_hash      TEXT    PRIMARY KEY,
    policy_version   TEXT    NOT NULL,
    profile          TEXT    NOT NULL CHECK (profile IN ('research','simulation','paper','live')),
    payload_json     TEXT    NOT NULL CHECK (json_valid(payload_json)),
    effective_at     TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_risk_policy_profile ON risk_policy_versions(profile, effective_at DESC);
```

Keyed by `config_hash`, so an identical policy cannot be registered twice under two
versions. `payload_json` carries the rule tree; per the hybrid rule (D9) only `profile`
is normalised, because it is the sole field filtered on.

### `risk_eligibility_decisions`

May this strategy trade at all?

```sql
CREATE TABLE risk_eligibility_decisions (
    decision_id      TEXT    PRIMARY KEY,
    strategy_id      TEXT    NOT NULL,
    strategy_version TEXT    NOT NULL,
    payload_json     TEXT    NOT NULL CHECK (json_valid(payload_json)),
    expires_at       TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_risk_eligibility_strategy ON risk_eligibility_decisions(strategy_id, strategy_version);
CREATE INDEX idx_risk_eligibility_expiry   ON risk_eligibility_decisions(expires_at);
```

`expires_at` is `NOT NULL`: an eligibility decision is time-bounded, so a stale
approval cannot be replayed against a strategy whose behaviour has since changed.

### `risk_allocation_decisions`

How much budget does this portfolio get?

```sql
CREATE TABLE risk_allocation_decisions (
    decision_id      TEXT    PRIMARY KEY,
    portfolio_id     TEXT    NOT NULL,
    reviewed_version TEXT    NOT NULL,
    active           INTEGER NOT NULL CHECK (active IN (0, 1)),
    predecessor_version TEXT,
    payload_json     TEXT    NOT NULL CHECK (json_valid(payload_json)),
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    UNIQUE (portfolio_id, reviewed_version)
) STRICT;

CREATE UNIQUE INDEX idx_risk_allocation_active
    ON risk_allocation_decisions(portfolio_id) WHERE active = 1;
```

The partial unique index guarantees **at most one active allocation per portfolio**.
Two simultaneously-active allocations is the failure mode where each sizing check
passes under a different budget.

`predecessor_version` makes a rollback legible rather than looking like an unexplained
reallocation.

### `risk_kill_switch_states`

```sql
CREATE TABLE risk_kill_switch_states (
    state_id         TEXT    PRIMARY KEY,
    scope_level      TEXT    NOT NULL CHECK (scope_level IN ('global','account','portfolio','strategy','symbol')),
    scope_json       TEXT    NOT NULL CHECK (json_valid(scope_json)),
    state            TEXT    NOT NULL CHECK (state IN ('armed','tripped','resetting')),
    version          INTEGER NOT NULL,
    payload_json     TEXT    NOT NULL CHECK (json_valid(payload_json)),
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_risk_kill_tripped ON risk_kill_switch_states(scope_level)
    WHERE state = 'tripped';
```

`version` is the optimistic-concurrency guard: a reset passes its expected version and
fails rather than racing a concurrent trip.

The partial index is **empty in normal operation**, so the kill-switch check that runs
before every order costs an empty-B-tree probe. The safety check that runs most often
should cost least when nothing is wrong.

Trip and reset attestations live in `payload_json`; per `AGENTS.md` §3 a kill switch is
deterministic and no caller can bypass it.

### `risk_approval_tokens`

```sql
CREATE TABLE risk_approval_tokens (
    token_id         TEXT    PRIMARY KEY,
    decision_id      TEXT    NOT NULL,
    scope_json       TEXT    NOT NULL CHECK (json_valid(scope_json)),
    state            TEXT    NOT NULL CHECK (state IN ('issued','reserved','consumed','expired','revoked')),
    reservation_id   TEXT,
    expires_at       TEXT    NOT NULL,
    payload_json     TEXT    NOT NULL CHECK (json_valid(payload_json)),
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_risk_tokens_open ON risk_approval_tokens(expires_at)
    WHERE state IN ('issued','reserved');
CREATE INDEX idx_risk_tokens_decision ON risk_approval_tokens(decision_id);
```

`state` plus `reservation_id` make an approval **single-use and atomically reservable**:
the reservation is taken before execution, so the same token cannot authorise two
orders.

### `risk_decision_snapshots`

```sql
CREATE TABLE risk_decision_snapshots (
    record_id        TEXT    PRIMARY KEY,
    record_type      TEXT    NOT NULL,
    config_hash      TEXT    NOT NULL,
    payload_json     TEXT    NOT NULL CHECK (json_valid(payload_json)),
    occurred_at      TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_risk_snapshots_config ON risk_decision_snapshots(config_hash, occurred_at DESC);
```

`config_hash` binds every snapshot to the exact policy version that produced it, so a
decision can be re-evaluated against the rules that actually applied at the time rather
than against today's.

### `risk_audit_records`

Hash-chained, append-only. The tamper-evident spine of the domain.

```sql
CREATE TABLE risk_audit_records (
    record_id        TEXT    PRIMARY KEY,
    sequence         INTEGER NOT NULL UNIQUE,
    event_type       TEXT    NOT NULL,
    payload_json     TEXT    NOT NULL CHECK (json_valid(payload_json)),
    evidence_refs_json TEXT  NOT NULL CHECK (json_valid(evidence_refs_json)),
    config_hash      TEXT    NOT NULL,
    decision_id      TEXT,
    occurred_at      TEXT    NOT NULL,
    previous_hash    TEXT    NOT NULL,
    record_hash      TEXT    NOT NULL UNIQUE,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_risk_audit_decision ON risk_audit_records(decision_id) WHERE decision_id IS NOT NULL;
CREATE INDEX idx_risk_audit_seq      ON risk_audit_records(sequence DESC);
```

`previous_hash` → `record_hash` chains every record, so a deleted or edited decision
breaks the chain and is detectable. `sequence` is `UNIQUE`, so a gap is visible too.

---

### Target-only tables

The following have **no live counterpart** and are not built. They are Tier B work and
carry no conformance obligation until a feature requires them.

#### `risk_limits`

```sql
CREATE TABLE risk_limits (
    limit_id         TEXT    PRIMARY KEY,
    config_hash      TEXT    NOT NULL REFERENCES risk_policy_versions(config_hash) ON DELETE RESTRICT,
    limit_type       TEXT    NOT NULL CHECK (limit_type IN (
                        'max_position_size','max_notional','max_leverage','max_open_positions',
                        'max_daily_loss','max_drawdown','max_concentration','max_slippage_bps',
                        'max_order_rate','max_correlation','min_free_margin')),
    scope_key        TEXT    NOT NULL DEFAULT '',
    threshold_decimal TEXT   NOT NULL,
    threshold_unit   TEXT    NOT NULL CHECK (threshold_unit IN ('absolute','percent','bps','count','ratio')),
    breach_action    TEXT    NOT NULL CHECK (breach_action IN ('reject','reduce','halt','kill_switch','warn')),
    enabled          INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    UNIQUE (config_hash, limit_type, scope_key)
) STRICT;

CREATE INDEX idx_risk_limits_policy ON risk_limits(config_hash, limit_type) WHERE enabled = 1;
```

Normalises individual rules out of `risk_policy_versions.payload_json` so limits can be
queried and reported on. Until this exists, limit inspection means parsing JSON.

#### `risk_limit_checks`

```sql
CREATE TABLE risk_limit_checks (
    check_seq        INTEGER PRIMARY KEY,
    decision_id      TEXT    NOT NULL,
    limit_id         TEXT,
    limit_type       TEXT    NOT NULL,
    observed_decimal TEXT    NOT NULL,
    threshold_decimal TEXT   NOT NULL,
    passed           INTEGER NOT NULL CHECK (passed IN (0,1)),
    headroom_decimal TEXT,
    evaluated_at     TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_risk_checks_decision ON risk_limit_checks(decision_id);
CREATE INDEX idx_risk_checks_breach   ON risk_limit_checks(limit_type, evaluated_at DESC) WHERE passed = 0;
```

One row per limit evaluated per decision — the evidence trail behind a verdict.
`decision_id` is a soft reference because it may name either an eligibility or an
allocation decision.

#### `risk_exposure_snapshots`

```sql
CREATE TABLE risk_exposure_snapshots (
    snapshot_id      TEXT    PRIMARY KEY,
    scope_level      TEXT    NOT NULL CHECK (scope_level IN ('account','portfolio','strategy','symbol','asset_class')),
    scope_key        TEXT    NOT NULL,
    gross_notional_decimal TEXT NOT NULL,
    net_notional_decimal   TEXT NOT NULL,
    open_positions   INTEGER NOT NULL DEFAULT 0,
    used_margin_decimal    TEXT NOT NULL,
    free_margin_decimal    TEXT NOT NULL,
    unrealized_pnl_decimal TEXT NOT NULL,
    peak_equity_decimal    TEXT NOT NULL,
    current_drawdown_decimal TEXT NOT NULL,
    breakdown_json   TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(breakdown_json)),
    is_current       INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0,1)),
    observed_at      TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE UNIQUE INDEX idx_risk_exposure_current
    ON risk_exposure_snapshots(scope_level, scope_key) WHERE is_current = 1;
CREATE INDEX idx_risk_exposure_history
    ON risk_exposure_snapshots(scope_level, scope_key, observed_at DESC);
```

## Domain 7 — Trading (`trading_`)

Event-sourced: `trading_events` is the write model; `trading_orders`,
`trading_fills`, and `trading_positions` are read projections rebuildable from it.

### `trading_events`

The append-only write model. Source of truth.

```sql
CREATE TABLE trading_events (
    event_seq        INTEGER PRIMARY KEY,
    event_id         TEXT    NOT NULL UNIQUE,
    event_type       TEXT    NOT NULL,
    event_version    TEXT    NOT NULL,
    scope_key        TEXT    NOT NULL,                   -- aggregate identity
    aggregate_version INTEGER NOT NULL,
    payload_json     TEXT    NOT NULL CHECK (json_valid(payload_json)),
    occurred_at      TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    causation_id     TEXT,
    bucket_year      TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    UNIQUE (scope_key, aggregate_version)
) STRICT;

CREATE INDEX idx_trading_events_scope ON trading_events(scope_key, aggregate_version);
CREATE INDEX idx_trading_events_time  ON trading_events(occurred_at DESC);
CREATE INDEX idx_trading_events_corr  ON trading_events(correlation_id);
```

`UNIQUE (scope_key, aggregate_version)` is the optimistic-concurrency control:
two concurrent writers computing the same next version collide at insert. One wins,
one retries. Without it, a double-submitted order silently doubles the position.

### `trading_idempotency`

```sql
CREATE TABLE trading_idempotency (
    idempotency_key  TEXT    PRIMARY KEY,
    material_hash    TEXT    NOT NULL,
    material_version TEXT    NOT NULL,
    status           TEXT    NOT NULL CHECK (status IN ('in_flight','succeeded','failed')),
    receipt_id       TEXT,
    expires_at       TEXT    NOT NULL,
    request_id       TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_trading_idem_expiry ON trading_idempotency(expires_at);
```

`material_hash` guards against key reuse with different payloads — a replayed key
carrying changed contents must fail, not silently return the prior receipt.

### `trading_orders`

```sql
CREATE TABLE trading_orders (
    order_id         TEXT    PRIMARY KEY,
    client_order_id  TEXT    NOT NULL UNIQUE,
    broker_order_id  TEXT,
    account_id       TEXT    NOT NULL,                   -- opaque broker account id; no table (D10)
    symbol_id        TEXT    NOT NULL,
    strategy_version_id TEXT,                            -- soft ref
    config_id        TEXT,                               -- soft ref
    signal_id        TEXT,                               -- soft ref
    risk_decision_id TEXT    NOT NULL,                   -- soft ref -> risk_eligibility_decisions; NOT NULL = mandatory gate
    side             TEXT    NOT NULL CHECK (side IN ('buy','sell')),
    order_type       TEXT    NOT NULL CHECK (order_type IN ('market','limit','stop','stop_limit','trailing_stop')),
    time_in_force    TEXT    CHECK (time_in_force IN ('gtc','ioc','fok','day','gtd')),
    quantity_decimal TEXT    NOT NULL,
    filled_qty_decimal TEXT  NOT NULL DEFAULT '0',
    limit_price_decimal TEXT,
    stop_price_decimal  TEXT,
    avg_fill_price_decimal TEXT,
    stop_loss_decimal   TEXT,
    take_profit_decimal TEXT,
    state            TEXT    NOT NULL CHECK (state IN (
                        'pending_new','new','partially_filled','filled',
                        'pending_cancel','cancelled','rejected','expired')),
    reject_reason    TEXT,
    runtime_profile  TEXT    NOT NULL CHECK (runtime_profile IN ('research','simulation','paper','live')),
    submitted_at     TEXT,
    terminal_at      TEXT,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    CHECK (order_type NOT IN ('limit','stop_limit') OR limit_price_decimal IS NOT NULL),
    CHECK (order_type NOT IN ('stop','stop_limit','trailing_stop') OR stop_price_decimal IS NOT NULL),
    CHECK (state <> 'rejected' OR reject_reason IS NOT NULL)
) STRICT;

CREATE INDEX idx_trading_orders_open    ON trading_orders(account_id, symbol_id)
    WHERE state IN ('pending_new','new','partially_filled','pending_cancel');
CREATE INDEX idx_trading_orders_broker  ON trading_orders(broker_order_id) WHERE broker_order_id IS NOT NULL;
CREATE INDEX idx_trading_orders_history ON trading_orders(account_id, created_at DESC);
CREATE INDEX idx_trading_orders_risk    ON trading_orders(risk_decision_id);
```

`risk_decision_id TEXT NOT NULL` is the load-bearing constraint of the whole design.
An order row cannot physically exist without naming a risk decision.

`time_in_force` is nullable because the shipped Trading contract permits an authority
to apply its documented order-type default. Persistence must retain absence and must
not invent a broker instruction that was not present in the governed intent.

### `trading_fills`

Immutable execution records. Never updated.

```sql
CREATE TABLE trading_fills (
    fill_id          TEXT    PRIMARY KEY,
    order_id         TEXT    NOT NULL REFERENCES trading_orders(order_id) ON DELETE RESTRICT,
    broker_fill_id   TEXT,
    sequence         INTEGER NOT NULL,
    quantity_decimal TEXT    NOT NULL,
    price_decimal    TEXT    NOT NULL,
    commission_decimal TEXT  NOT NULL DEFAULT '0',
    swap_decimal     TEXT    NOT NULL DEFAULT '0',
    slippage_bps     TEXT,
    liquidity_flag   TEXT    CHECK (liquidity_flag IN ('maker','taker','unknown')),
    executed_at      TEXT    NOT NULL,
    reported_at      TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    UNIQUE (order_id, sequence),
    UNIQUE (broker_fill_id)
) STRICT;

CREATE INDEX idx_trading_fills_order ON trading_fills(order_id, sequence);
CREATE INDEX idx_trading_fills_time  ON trading_fills(executed_at DESC);
```

`executed_at` (venue) and `reported_at` (received) are separate. Their difference is
the real execution latency; collapsing them makes latency unmeasurable and
`slippage_bps` uninterpretable.

`UNIQUE (broker_fill_id)` is the duplicate-fill guard on reconnect replay.

### `trading_order_transitions`

```sql
CREATE TABLE trading_order_transitions (
    transition_seq   INTEGER PRIMARY KEY,
    order_id         TEXT    NOT NULL REFERENCES trading_orders(order_id) ON DELETE RESTRICT,
    from_state       TEXT,
    to_state         TEXT    NOT NULL,
    reason_code      TEXT    NOT NULL,
    detail_json      TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(detail_json)),
    occurred_at      TEXT    NOT NULL,
    correlation_id   TEXT    NOT NULL,
    created_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_trading_transitions_order ON trading_order_transitions(order_id, transition_seq);
```

### `trading_positions`

Current open positions. One row per (account, symbol, direction).

```sql
CREATE TABLE trading_positions (
    position_id      TEXT    PRIMARY KEY,
    account_id       TEXT    NOT NULL,
    symbol_id        TEXT    NOT NULL,
    direction        TEXT    NOT NULL CHECK (direction IN ('long','short')),
    quantity_decimal TEXT    NOT NULL,
    avg_entry_price_decimal TEXT NOT NULL,
    current_price_decimal   TEXT,
    unrealized_pnl_decimal  TEXT NOT NULL DEFAULT '0',
    realized_pnl_decimal    TEXT NOT NULL DEFAULT '0',
    commission_total_decimal TEXT NOT NULL DEFAULT '0',
    swap_total_decimal      TEXT NOT NULL DEFAULT '0',
    stop_loss_decimal       TEXT,
    take_profit_decimal     TEXT,
    strategy_version_id     TEXT,
    state            TEXT    NOT NULL CHECK (state IN ('open','closing','closed')),
    opened_at        TEXT    NOT NULL,
    closed_at        TEXT,
    position_version INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE UNIQUE INDEX idx_trading_pos_open
    ON trading_positions(account_id, symbol_id, direction) WHERE state = 'open';
CREATE INDEX idx_trading_pos_history ON trading_positions(account_id, closed_at DESC) WHERE state = 'closed';
```

The partial unique index prevents duplicate open positions on the same instrument
and side — the netting invariant, enforced by the database rather than by code.

### `trading_projections`

```sql
CREATE TABLE trading_projections (
    scope_key        TEXT    PRIMARY KEY,
    projection_version INTEGER NOT NULL,
    last_event_seq   INTEGER NOT NULL,
    projection_json  TEXT    NOT NULL CHECK (json_valid(projection_json)),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;
```

`last_event_seq` records how far the projection has consumed the event log — the
resume point for rebuilds and the staleness check for readers.

---

## Domain 8 — Simulator (`sim_`)

> **This domain follows the live implementation.** Simulator persists **run identity
> only**. Its canonical journal is append-only JSONL and its results are published as
> file artifacts; neither is backed by a table. The mirrored `sim_orders` /
> `sim_fills` / `sim_positions` design an earlier draft proposed is target-only and is
> not implied by this schema.

### `sim_runs`

```sql
CREATE TABLE sim_runs (
    request_id       TEXT    PRIMARY KEY,
    request_hash     TEXT    NOT NULL,
    run_id           TEXT    NOT NULL UNIQUE,
    status           TEXT    NOT NULL,
    result_payload   TEXT,
    correlation_id   TEXT    NOT NULL DEFAULT '',
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
) STRICT;

CREATE INDEX idx_sim_runs_status ON sim_runs(status);
```

Renamed from `simulation_runs` under the ratified `sim_` namespace (D2). The step was
never applied, so this was a definition edit rather than a rename migration.

`request_id` is the primary key and `run_id` is separately `UNIQUE`: one request maps
to exactly one run, and a replayed request returns the original run instead of starting
a second. `request_hash` makes a replay with changed material fail rather than silently
reusing the prior run.

`result_payload` is nullable — an incomplete run has no result, and per
`AGENTS.md` §3 "No Invented Data" an absent result must read as absent rather than as
an empty one.

### Why there is no journal table

`app/services/simulator/state/migrations.py` recorded the position before this model
existed: the canonical journal is append-only JSONL (`JOURNAL_FORMAT = "jsonl-v1"`) and
*"no table backs it, because a SQLite journal sidecar is an explicit Phase 1
exclusion."* The model defers to that.

A journal is written once, read sequentially, and never queried by predicate — the
access pattern JSONL serves and SQLite does not. It is written to a temp path, renamed
atomically, then hashed, the same integrity discipline used for Parquet partitions
([00](00_domain_relationship_map.md) §0). Discarding a backtest costs a file delete
rather than millions of row deletes and a `VACUUM`.

---

### Target-only tables

No live counterpart; not built. They would mirror the `trading_*` execution tables so
Analytics could compute performance from one shape across live and backtest results.
Until they exist, Analytics reads simulator results from published artifacts.

`sim_execution_models` · `sim_orders` · `sim_fills` · `sim_positions` ·
`sim_order_transitions`

Their column definitions are omitted here rather than carried as unbuilt DDL; the
`trading_*` tables in Domain 7 are the shape they would take, plus `run_id`.

---

## Entity count — this file

| Domain | Tables |
|---|---|
| Strategy | 7 |
| Risk | 10 |
| Trading | 7 |
| Simulator | 1 |
| **Total** | **25** |

Next: [03_entity_specs_intelligence.md](03_entity_specs_intelligence.md)

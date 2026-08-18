# HaruQuantAI V2 Simulator and Analytics Frontend Implementation Plan

**Target repository:**  C:\Users\rharu\AppDev\HaruquantAI   (short - V2))
**Reference repository only:** C:\Users\rharu\AppDev\Haruquant   (short - V1))

---

## 1. Scope and interpretation

This plan is exclusively for the **HaruQuantAI V2 frontend** and the additive V2 API/read-model work required by that frontend.

HaruQuant V1 is frozen and read-only. It is used only as a product-reference catalogue. No V1 component, route, API, database, test, or service is to be modified.

HaruQuantAI V2 remains authoritative:

- **Simulation** owns deterministic execution, orders, fills, positions, account state, journals, replay, scenarios, realism, recovery, results, and Simulation artifacts.
- **Analytics** owns every performance metric, ratio, comparison, dashboard projection, warning, quality flag, lineage record, and performance conclusion.
- **Data** owns market-data acquisition, canonical datasets, quality evidence, provider metadata, and durable infrastructure.
- **Strategy** owns strategy identity, parameters, and signal behavior.
- **Trading** owns order-intent and execution-record contracts.
- **Risk** owns policy and risk decisions.
- **Optimization** owns Monte Carlo, optimization, and walk-forward workflows.
- **API** owns authenticated transport, safe browser DTOs, orchestration, streaming, pagination, and error translation.
- **UI** owns presentation and bounded interaction state only.

### Core objective

Build one complete V2 user journey:

```text
Simulation Workbench
        ↓
Canonical or advisory run/session evidence
        ↓
Analytics Workbench
        ↓
Trade drill-down, replay, comparison, and artifacts
```

The implementation must:

1. Preserve V1’s explicit **Simulation → Analytics** separation.
2. Cover every substantive V1 simulation mode and analysis page.
3. Give V1 placeholders and cross-domain tools an explicit V2 disposition.
4. Keep the existing V2 Simulator backend and current canonical backtest widget.
5. Expose V2-only Simulation capabilities that V1 never had.
6. Prevent the frontend from becoming a second execution or analytics engine.
7. Make official canonical results and advisory practice/what-if evidence visually unmistakable.

---

## 2. Product shape: retain two top-level workspaces

V1 is correct to separate execution from analysis. V2 should retain that product boundary.

### Workspace A — Simulator

Purpose:

- choose what to simulate;
- configure strategy, market, costs, realism, scenario, and account inputs;
- submit background canonical runs;
- operate interactive visual/manual practice sessions;
- monitor progress;
- resume or recover sessions;
- launch journal replay;
- inspect live account/order/position evidence;
- finalize or reproduce a practice session safely.

### Workspace B — Analytics

Purpose:

- browse completed runs;
- select one authoritative run or advisory practice review;
- inspect Analytics-owned performance evidence;
- inspect Simulation-owned trades, realism, diagnostics, journals, and artifacts;
- compare compatible runs;
- drill into one trade;
- launch replay at the selected trade;
- return from replay without losing analytics context.

### Required handoff

For a successful canonical run:

```text
/workstation/simulator/runs/{jobId}
                ↓
official Simulation run_id + Analytics report_id
                ↓
/workstation/analytics/{runId}/overview
```

For an interactive or what-if session:

```text
/workstation/simulator/sessions/{sessionId}
                ↓
advisory practice review
                ↓
optional canonical reproduction
                ↓
/workstation/analytics/{officialRunId}/overview
```

The UI must never silently convert an advisory branch into an official `SimulationResult`.

---

## 3. Current-state baseline

## 3.1 V1 product-reference baseline

### V1 Simulation

The V1 `/simulation` area spans multiple modes:

- Visual Auto
- Batch Auto
- Manual
- Replay

The root simulation route defaults to Visual Auto. The historical-run shell moves through:

```text
Configuration → Execution → Results
```

V1 supports or attempts to support:

- one or multiple symbols;
- timeframe and date/bar ranges;
- warm-up;
- MT5 or Dukascopy data;
- strategy selection and parameters;
- initial capital;
- commission, spread, and slippage;
- leverage;
- engine type and data resolution;
- broad risk configuration;
- named run metadata;
- existing-backtest or CSV replay;
- paused-session resumption;
- visual speed, pause, resume, skip, and seek;
- manual trading;
- account, positions, pending orders, and trade views;
- risk and governance panels;
- what-if analysis;
- session save/quit behavior;
- background batch execution;
- automatic navigation to Analytics after a batch completes.

### V1 Performance (Maps to V2 Analytics)

The V1 `/performance` area is not one page. It is a large multi-page analysis workspace with:

- run library;
- overview;
- trades calendar;
- trade chart;
- trade replay;
- strategy analysis;
- trade analysis;
- periodical analysis;
- chart analysis;
- metadata/MetaParams.

The route tree includes dozens of individual pages. Some are fully implemented; others are partial or placeholders. V2 preserves the substantive analytical coverage in the **Analytics** domain without reproducing empty routes or duplicated presentation logic.

## 3.2 V2 Simulator backend baseline

The V2 Simulator backend already provides the authoritative foundation:

- deterministic timeline and matching;
- account and margin state;
- orders, fills, positions, and closed trades;
- append-only journal and replay;
- canonical results and artifact manifests;
- realism disclosures;
- scenarios, faults, missions, and checklists;
- recovery and rearm;
- live what-if sessions;
- branch lineage;
- deterministic background canonical backtest recipe;
- true ordered progress events;
- cooperative cancellation;
- full `SimulationResult v1` retrieval.

The canonical backtest recipe already performs:

```text
Market retrieval
    ↓
Canonical tick generation
    ↓
Simulation
    ↓
Analytics PerformanceReport
```

## 3.3 V2 Analytics backend baseline

Analytics already owns:

- canonical `PerformanceReport v1`;
- trade evidence for all/long/short contexts;
- PnL and equity-return evidence;
- drawdown evidence;
- risk evidence;
- ratio evidence;
- benchmark evidence;
- distributions;
- cost and efficiency evidence;
- statistical evidence;
- reproducibility hashes;
- report comparison;
- bounded dashboard projections;
- warnings and quality flags.

Its metric catalogue already includes most of the useful V1 performance concepts.

## 3.4 V2 API baseline

The V2 API currently exposes two related route families.

### Safe canonical recipe API

```text
GET    /api/v1/simulator/strategies
POST   /api/v1/simulator/runs
GET    /api/v1/simulator/runs
GET    /api/v1/simulator/runs/{job_id}
DELETE /api/v1/simulator/runs/{job_id}
GET    /api/v1/simulator/runs/{job_id}/stream
```

This is the correct browser-facing creation path because the user supplies human choices while provider facts, hashes, revisions, and internal identities are derived server-side.

### Simulation-domain routes

```text
POST /api/v1/simulation/run
POST /api/v1/simulation/portfolio-run
GET  /api/v1/simulation/results/{run_id}
```

The exact `SimulationRunRequest` is an internal/canonical projection carrying hashes and references. It should not be the primary browser-authored run form.

### Playback routes

```text
POST /api/v1/simulation/sessions
GET  /api/v1/simulation/sessions/{session_id}/frames
```

These replay a completed immutable journal.

### Live what-if routes

```text
POST   /api/v1/simulation/live-sessions
GET    /api/v1/simulation/live-sessions/{session_id}
POST   /api/v1/simulation/live-sessions/{session_id}/restore
POST   /api/v1/simulation/live-sessions/{session_id}/rearm
POST   /api/v1/simulation/live-sessions/{session_id}/step
POST   /api/v1/simulation/live-sessions/{session_id}/branch
DELETE /api/v1/simulation/live-sessions/{session_id}
```

These are suitable owner-domain operations, but the creation DTO and returned frontend schema need a safer typed workstation projection.

## 3.5 V2 UI baseline

The existing `FEAT-UI-27` `SimulatorWidget` already covers:

- strategy catalogue;
- strategy parameters;
- symbol/timeframe/date range;
- initial balance;
- volume;
- commission;
- spread;
- slippage;
- seed and bar limit;
- run submission;
- true progress stream;
- cancellation;
- recent jobs;
- compact terminal metrics and quality evidence.

This feature must be retained. The new frontend is additive: the current widget becomes a reusable canonical-run component inside the broader Simulation Workbench.

The current terminal job response is intentionally compact. It is not sufficient by itself for V1-equivalent Analytics pages because it does not expose the full canonical Simulation result, closed-trade ledger, complete Analytics report, complete presentation series, replay anchors, or artifact catalogue.

---

## 4. Governing frontend rules

## 4.1 Authority matrix

| Concern                          | V2 authority                          | UI responsibility                                |
| -------------------------------- | ------------------------------------- | ------------------------------------------------ |
| Market-data selection            | Data                                  | Collect user choices and display provenance      |
| Strategy identity and parameters | Strategy                              | Select registered strategy and render its schema |
| Run creation                     | API + Simulator composition           | Submit safe request                              |
| Timeline advancement             | Simulation                            | Request bounded steps; trust returned cursor     |
| Orders and fills                 | Trading contracts + Simulation engine | Submit commands and render receipts              |
| Account, margin, positions       | Simulation                            | Render authoritative state                       |
| Run status and progress          | Simulator job registry/API stream     | Render ordered events                            |
| Analytics metrics                | Analytics                             | Render only                                      |
| Trade and artifact evidence      | Simulation                            | Render and link                                  |
| Risk decisions                   | Risk                                  | Render without recomputing                       |
| Monte Carlo / walk-forward       | Optimization                          | Link to owned workflow                           |
| Run comparison                   | Analytics                             | Render owner-produced comparison                 |
| Official/advisory status         | Simulation                            | Make status visually explicit                    |
| Persistence and recovery         | Simulator/Data                        | Display state and permitted actions              |

## 4.2 Non-negotiable constraints

- Do not modify V1.
- Do not copy V1 React components or API shapes.
- Do not calculate win rate, profit factor, drawdown, ratios, risk-of-ruin, scorecards, or period returns in the browser.
- Do not use fake progress timers.
- Do not infer a successful run from a disconnected stream.
- Do not persist full runs, trade ledgers, or account state in browser storage.
- Do not let the browser author internal hashes, provider revisions, artifact roots, or risk-policy identities.
- Do not expose the complete future timeline to an interactive/manual simulation browser.
- Do not allow playback to mutate an official result.
- Do not present what-if branches as canonical performance.
- Do not preserve empty V1 routes merely for numerical parity.
- Do not create dozens of near-identical period pages. Use one typed page with route/query dimensions.
- Keep raw JSON and journal frames as secondary diagnostic views.

---

## 5. Recommended registered features

Feature IDs below assume the Research frontend plan reserves `FEAT-API-26` and `FEAT-UI-28`. Reconcile IDs against the registries before implementation.

### Retain `FEAT-UI-27` — Canonical Backtest Simulator Widget

Keep its current public behavior and tests.

Use it as:

```text
SimulationWorkbench
└── CanonicalRunBuilder / CanonicalRunMonitor
    └── existing SimulatorWidget behavior
```

It may be decomposed internally into focused components, but its tested public capability must remain intact.

### `FEAT-API-27` — Simulation Workbench Gateway

Purpose:

- expose safe canonical, batch, interactive, manual, replay, recovery, and result-catalogue operations;
- translate browser selections into authoritative Simulation inputs;
- expose typed live-session projections;
- expose bounded timeline/viewport data;
- expose manual session commands;
- link jobs, canonical run IDs, report IDs, replay IDs, and artifacts;
- provide no Simulation or Analytics calculations.

### `FEAT-API-28` — Analytics Workbench Gateway

Purpose:

- expose run-specific `PerformanceReport`, dashboard/workbench projections, trades, trade details, comparisons, periods, artifacts, and replay anchors;
- paginate and truncate bounded evidence;
- compose Simulation and Analytics owner reads;
- provide no metric calculations.

### `FEAT-UI-29` — Simulation Workbench

Purpose:

- run builder;
- batch monitor;
- interactive visual/manual workspace;
- session recovery;
- replay;
- scenarios and checklists;
- result handoff to Analytics.

### `FEAT-UI-30` — Analytics Workbench

Purpose:

- run library;
- overview;
- trade analysis;
- returns;
- risk;
- distributions;
- periods;
- benchmark;
- charts;
- realism;
- provenance;
- artifacts;
- comparison;
- replay round-trip.

### `FEAT-ANLT-11` — Analytics Workbench Projection

Register this only if the required run-specific chart/table projections are not intentionally added as a versioned extension of `FEAT-ANLT-05`.

Purpose:

- project existing Analytics evidence into finite, typed workbench series and tables;
- add missing presentation series without changing metric ownership;
- produce run-specific drawdown, period, calendar, distribution, benchmark, and trade-analysis payloads;
- include units, source contexts, quality flags, caveats, and truncation metadata.

No new Simulation algorithm feature is required by default. First reconcile whether missing manual-command, result-catalogue, and finalization operations are public-surface gaps within the existing Simulator capabilities. Register a new Simulator feature only when genuinely new domain behavior is required.

---

## 6. Target route architecture

## 6.1 Simulation routes

```text
/workstation/simulator
/workstation/simulator/new
/workstation/simulator/new?mode=backtest
/workstation/simulator/new?mode=visual
/workstation/simulator/new?mode=manual
/workstation/simulator/new?mode=batch
/workstation/simulator/new?mode=replay
/workstation/simulator/new?mode=scenario

/workstation/simulator/runs/{jobId}
/workstation/simulator/sessions
/workstation/simulator/sessions/{sessionId}
/workstation/simulator/replay/{playbackSessionId}
```

Optional compatibility redirect:

```text
/workstation/simulation → /workstation/simulator
```

The V2 navigation should use one canonical label and path consistently.

## 6.2 Analytics routes

```text
/workstation/analytics
/workstation/analytics/compare

/workstation/analytics/{runId}/overview
/workstation/analytics/{runId}/trades
/workstation/analytics/{runId}/returns
/workstation/analytics/{runId}/risk
/workstation/analytics/{runId}/distribution
/workstation/analytics/{runId}/periods
/workstation/analytics/{runId}/benchmark
/workstation/analytics/{runId}/charts
/workstation/analytics/{runId}/realism
/workstation/analytics/{runId}/provenance
```

Trade deep link:

```text
/workstation/analytics/{runId}/trades/{ticket}
```

Replay deep link:

```text
/workstation/simulator/replay/{playbackSessionId}
    ?runId={runId}
    &ticket={ticket}
    &returnTo=/workstation/analytics/{runId}/trades/{ticket}
```

## 6.3 Why nested pages are required

The Analytics workspace must remain multi-page because:

- trade lists and charts have different payload and loading requirements;
- period tables are large and filter-heavy;
- replay deserves a dedicated full-screen workspace;
- routes must be refresh-safe and shareable;
- deep links are necessary for review, debugging, and AI-assisted navigation;
- one giant component would recreate the V1 mega-page problem.

---

## 7. V1 Simulation coverage matrix

| V1 capability                         | V2 destination                                     | Decision                                                                                |
| ------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `/simulation` root                  | `/workstation/simulator`                         | Preserve as Simulation home                                                             |
| Visual Auto                           | New Run mode `visual` + interactive session        | Cover using server-authoritative live session                                           |
| Batch Auto                            | New Run mode `batch` + existing canonical job API  | Cover and improve with true SSE                                                         |
| Manual                                | New Run mode `manual` + interactive commands       | Cover; requires typed command gateway                                                   |
| Replay                                | Dedicated playback workspace                       | Cover using immutable journal playback                                                  |
| Configuration → Execution → Results   | Builder → Run/Session → Analytics                  | Preserve journey with route-safe state                                                  |
| Symbol                                | Run Builder / Market                               | Cover                                                                                   |
| Multiple symbols                      | Batch group or explicit portfolio simulation       | Cover; do not conflate batch and portfolio                                              |
| Timeframe                             | Run Builder / Market                               | Cover                                                                                   |
| Date range                            | Run Builder / Market                               | Cover                                                                                   |
| Number of bars                        | Run Builder / Market                               | Cover through safe recipe                                                               |
| Warm-up date/bars                     | Strategy descriptor + advanced run evidence        | Prefer server-derived warm-up; display effective value                                  |
| MT5 / Dukascopy                       | Data source selector where enabled                 | Cover through Data/provider settings                                                    |
| Strategy                              | Registered Strategy catalogue                      | Cover                                                                                   |
| Strategy version                      | Descriptor metadata                                | Cover                                                                                   |
| Strategy parameters                   | Schema-driven controls                             | Cover                                                                                   |
| Replay from existing backtest         | Analytics/Run Library → Replay                     | Cover                                                                                   |
| Replay from CSV                       | Data import adapter → imported replay evidence     | Optional; non-canonical unless validated                                                |
| Paused sessions                       | Sessions page                                      | Cover through durable live sessions                                                     |
| Resume paused session                 | Read/restore/rearm flow                            | Cover                                                                                   |
| Initial capital                       | Account section                                    | Cover                                                                                   |
| Commission                            | Costs section                                      | Cover                                                                                   |
| Spread mode/min/max                   | Realism/cost preset                                | Cover where V2 owner contract supports it                                               |
| Slippage mode/min/max                 | Realism/cost preset                                | Cover where V2 owner contract supports it                                               |
| Leverage                              | Provider facts / account settings                  | Display authoritative value; user override only where approved                          |
| Engine type                           | Runtime preset                                     | Map to `simulation` or approved `fast_research`; do not expose internal engine names    |
| Data resolution                       | Tick/bar realism preset                            | Cover through Simulation/Data contracts                                                 |
| Risk configuration                    | Risk preset/reference                              | UI selects registered policy, not free-form hidden authority                            |
| Run name/alias/description            | Run annotation metadata                            | Cover through API-owned annotation fields                                               |
| Run progress                          | Job Monitor                                        | Replace estimated progress with true ordered events                                     |
| Abort batch                           | Job cancellation                                   | Cover                                                                                   |
| Automatic Analytics redirect          | Successful canonical run handoff                   | Preserve                                                                                |
| Visual price chart                    | Interactive workspace                              | Reuse Chart feature or approved shared chart primitives                                 |
| Indicator overlays                    | Chart/Indicators                                   | Reuse V2 owner features                                                                 |
| Multi-chart layout                    | Interactive workspace layout                       | Cover where useful                                                                      |
| Market snapshot for many symbols      | Batch/portfolio monitor                            | Cover through Data snapshots                                                            |
| Pause visual session                  | Client pacing control                              | Stop issuing step calls; cursor remains server truth                                    |
| Resume visual session                 | Client pacing control                              | Resume bounded steps                                                                    |
| Speed selection                       | Client pacing                                      | UI-only cadence; never changes Simulation time semantics                                |
| Skip / seek                           | Bounded step/seek operation                        | Step is ready; seek needs explicit owner operation or iterative bounded stepping        |
| Current timestamp                     | Session projection                                 | Cover                                                                                   |
| Account state                         | Account panel                                      | Cover                                                                                   |
| Positions                             | Positions panel                                    | Cover                                                                                   |
| Pending orders                        | Orders panel                                       | Cover                                                                                   |
| Trades                                | Trade ledger panel                                 | Cover                                                                                   |
| Manual order ticket                   | Manual Command panel                               | Cover through Trading-owned intents                                                     |
| Modify order                          | Manual Command panel                               | Cover only through explicit backend command                                             |
| Cancel order                          | Manual Command panel                               | Cover only through explicit backend command                                             |
| Close position                        | Manual Command panel                               | Cover only through explicit backend command                                             |
| Risk snapshot                         | Risk panel                                         | Render Risk/Simulation evidence                                                         |
| Governance scorecard                  | Governance panel                                   | Render owner-produced evidence; no browser score                                        |
| Recommendations                       | Evidence/caveat panel                              | Only owner-authored recommendations                                                     |
| What-if                               | Branch workspace                                   | Cover with advisory branch identity                                                     |
| Correlation / exposure                | Risk/Portfolio evidence panel                      | Cover where owner evidence exists                                                       |
| Regimes                               | Research/Data evidence link                        | Do not recompute inside Simulator UI                                                    |
| Stop dialog                           | Session close/finalize dialog                      | Cover with truthful official/advisory actions                                           |
| Save visual as backtest               | Canonical reproduction flow                        | Do not directly relabel advisory session                                                |
| Quit without save                     | Close session                                      | Cover                                                                                   |
| Delete paused session                 | Close/archive durable session                      | Cover with governed action                                                              |
| Visual results summary                | Practice Review                                    | Use Analytics projection if eligible; no client metric calculation                      |
| Open saved Analytics report           | Analytics link                                     | Preserve                                                                                |

---

## 8. V1 Performance coverage matrix (Maps to V2 Analytics)

V2 consolidates V1’s many routes into focused pages in the **Analytics** workspace while retaining every substantive view.

## 8.1 Top-level V1 areas

| V1 area               | V2 destination                                   |
| --------------------- | ------------------------------------------------ |
| Run selection/library | `/workstation/analytics`                       |
| Overview              | `/{runId}/overview`                            |
| Trades Calendar       | `/{runId}/trades?view=calendar`                |
| Trades Chart          | `/{runId}/trades?view=chart`                   |
| Trades Chart Replay   | Simulator replay deep link                       |
| Strategy Analysis     | Overview, Returns, Risk, Distribution, Benchmark |
| Trade Analysis        | Trades and Distribution                          |
| Periodical Analysis   | Periods                                          |
| Chart Analysis        | Charts plus focused embedded charts              |
| MetaParams            | Provenance / Configuration                       |

## 8.2 Strategy Analysis

| V1 route/view        | V2 destination                 |
| -------------------- | ------------------------------ |
| Total Trade Analysis | Overview / Trade Summary       |
| Returns              | Returns                        |
| Performance Ratios   | Returns / Ratios               |
| Risk                 | Risk                           |
| Drawdown             | Risk / Drawdown                |
| Efficiency           | Returns or Trades / Efficiency |
| Distributions        | Distribution                   |
| Benchmark Comparison | Benchmark                      |
| Buy & Hold Return    | Benchmark / Buy & Hold         |
| VAMI                 | Returns / VAMI                 |

## 8.3 Trade Analysis

| V1 route/view     | V2 destination           |
| ----------------- | ------------------------ |
| Trade List        | Trades / Table           |
| Outliers          | Distribution / Outliers  |
| Run-up / Drawdown | Trades / Excursions      |
| Series Analysis   | Trades / Sequences       |
| Series Statistics | Trades / Sequences       |
| Total Trades      | Trades filter `all`      |
| Winning Trades    | Trades filter `winning`  |
| Losing Trades     | Trades filter `losing`   |
| MAE               | Trades / Excursions      |
| MAE %             | Trades / Excursions      |
| Run-up            | Trades / Excursions      |
| Run-up P&L        | Trades / Excursions      |
| MFE               | Trades / Excursions      |
| MFE %             | Trades / Excursions      |

## 8.4 Periodical Analysis

One V2 Periods page replaces duplicate route files.

Supported dimensions:

```text
period = hourly | daily | weekly | monthly | annual
mode = absolute | percent
series = pnl | returns | drawdown | trade_count | win_rate | cost
rolling = off | hourly | daily | weekly | monthly | annual
aggregation = period | accumulative | average
```

This covers:

- Annual Report
- Hourly
- Daily
- Weekly
- Monthly
- Annual
- Yearly Summary
- Rolling Hourly
- Rolling Daily
- Rolling Weekly
- Rolling Monthly
- Rolling Annual
- Hourly/Daily/Weekly/Monthly/Annual Trade Returns
- Hourly/Daily/Weekly/Monthly/Annual Trade Drawdowns
- Percentage drawdowns
- Monthly Accumulative Profit
- Monthly Average Profit

The route should encode the active view in query parameters so it remains shareable.

## 8.5 Chart Analysis

| V1 chart                  | V2 destination                                          |
| ------------------------- | ------------------------------------------------------- |
| Equity                    | Overview or Charts / Equity                             |
| Consecutive Wins          | Charts / Streaks                                        |
| Consecutive Losses        | Charts / Streaks                                        |
| Drawdown                  | Risk / Drawdown                                         |
| Efficiency                | Charts / Efficiency                                     |
| Exit Analysis             | Trades / Exit Analysis                                  |
| Holding Time              | Trades / Duration                                       |
| Performance by Instrument | Charts / Grouped Performance                            |
| Performance by Setup      | Charts / Grouped Performance when setup evidence exists |
| Performance by Time       | Periods                                                 |
| Performance by Day        | Periods                                                 |
| Ratio                     | Returns / Ratios                                        |
| Risk Distribution         | Distribution / Risk                                     |
| Trade Calendar            | Trades / Calendar                                       |
| Simulator                 | Optimization-owned Monte Carlo/scenario workflow        |

The V1 chart simulator performs browser-side random Monte Carlo using `Math.random()` and locally calculated trade KPIs. Do not port that implementation. Cover the product intent through Optimization-owned Monte Carlo or Simulator-owned scenarios with reproducible seeds and authoritative evidence.

## 8.6 V1 placeholders

V1 MetaParams and several chart/trade pages are placeholders. V2 should not create empty pages.

Their intended destinations are:

- MetaParams → Provenance, effective configuration, hashes, versions, and assumptions.
- Empty chart pages → enabled only after an owner payload is registered.
- Empty trade-analysis pages → combined into Trades/Distribution with explicit unavailable states when evidence is absent.

---

## 9. V2-only frontend coverage

The V2 frontend must go beyond V1.

## 9.1 Simulation-only additions

### Canonical/advisory identity

Every run/session header must display one of:

- `CANONICAL RESULT`
- `CANONICAL RUN IN PROGRESS`
- `PRACTICE SESSION`
- `ADVISORY WHAT-IF BRANCH`
- `IMMUTABLE PLAYBACK`
- `RECOVERY LOCKED`
- `VERIFIED — REARM REQUIRED`
- `FAST RESEARCH — NON-CERTIFICATION`

### Realism

Display:

- tick model;
- slippage model;
- liquidity model;
- session model;
- data quality;
- assumptions;
- limitations;
- calibration checksum;
- realism-stream identity;
- fault scenario IDs.

### Recovery

Support:

- session list;
- last cursor;
- persisted state hash;
- restore;
- integrity result;
- explicit rearm;
- exposure-blocked state;
- recovery generation;
- recovery run ID.

### What-if branches

Display:

- parent session;
- divergence cursor;
- overrides;
- branch run ID;
- advisory marker;
- parent/branch state comparison;
- close branch;
- open advisory review.

### Scenarios and faults

Support:

- scenario catalogue;
- fault-selection summary;
- active scenario state;
- scenario event timeline;
- emergency steps;
- outcome evidence;
- links to Analytics emergency-response evidence.

### Missions and checklists

Support:

- mission selection;
- pre-run checklist;
- assistance mode;
- required steps;
- completion state;
- scoring/qualification links where available.

### Artifacts and journal integrity

Expose:

- `journal.jsonl`;
- `result.json`;
- `report.md`;
- artifact media type;
- size;
- SHA-256;
- schema version;
- creation time;
- journal hash chain;
- diagnostics.

### Portfolio simulation

Provide a separate explicit mode:

- component list;
- weights and risk budgets;
- measurement window;
- base currency;
- FX evidence;
- portfolio result;
- component and aggregate Analytics evidence.

Do not treat a plain multi-symbol batch as a portfolio.

## 9.2 Analytics-only additions

Analytics should expose V2 quality and reproducibility that V1 often hid:

- section status;
- metric status;
- unit;
- source context;
- undefined reason;
- caveats;
- quality flags;
- lineage;
- input hash;
- report hash;
- precision metadata;
- curve basis;
- sample adequacy;
- benchmark alignment;
- statistical configuration;
- truncation metadata.

---

## 10. Metrics and decisions that must not be blindly copied from V1

V1 displays several concepts that are not currently part of the authoritative V2 Analytics metric catalogue or approved decision vocabulary.

| V1 item                                      | V2 decision                                                                        |
| -------------------------------------------- | ---------------------------------------------------------------------------------- |
| Total Return                                 | Add to Analytics if required; do not derive in UI                                  |
| Risk of Ruin                                 | Add only under an approved Analytics/Optimization definition                       |
| SQN                                          | Add only with an approved formula and sample policy                                |
| Deflated Sharpe Ratio                        | Add only as an approved statistical metric                                         |
| DSR p-value                                  | Add only as approved statistical evidence                                          |
| Probability Sharpe > 0                       | Add only through an approved statistical contract                                  |
| PASS / WATCHLIST / REJECT strategy scorecard | Do not reproduce in Analytics UI without an owning governance contract             |
| Quality Score 0–100                          | Use only if produced by Research, Strategy governance, or another registered owner |
| V1 browser Monte Carlo                       | Replace with Optimization/Simulator authoritative workflow                         |

Until an owner contract exists, show:

```text
Not available in the current authoritative V2 metric catalogue.
```

Do not substitute a client calculation.

---

## 11. API and owner-projection prerequisites

## 11.1 Ready and reusable

The following are already available:

- strategy catalogue;
- safe canonical run request;
- background job submission;
- job list/read/cancel;
- true ordered SSE progress;
- full completed `SimulationResult` by run ID;
- playback-session creation and journal streaming;
- live-session create/read/step/branch/close/restore/rearm;
- Analytics `PerformanceReport`;
- Analytics metric catalogue;
- Analytics report comparison;
- Simulation artifact manifest;
- Simulation closed-trade ledger.

## 11.2 Required Simulation Workbench gateway additions

### A. Safe interactive-session creation

The browser should submit the same human choices used by the safe canonical recipe, plus a practice mode.

Example:

```json
{
  "mode": "manual",
  "symbol": "EURUSD",
  "timeframe": "M15",
  "start": "2025-01-01T00:00:00Z",
  "end": "2025-03-31T23:59:59Z",
  "strategy_id": null,
  "parameters": {},
  "initial_balance": "10000.00",
  "account_currency": "USD",
  "volume": "0.10",
  "commission_per_lot_per_side": "7.00",
  "spread_points": "10",
  "slippage_points": "1",
  "seed": 7,
  "bar_limit": 10000,
  "scenario_ids": [],
  "mission_id": null,
  "assistance_mode": "standard"
}
```

The API derives canonical references and composes the Simulator request. The browser must not construct the exact internal `SimulationRunRequest`.

### B. Typed live-session projection

Replace the current generic `Record<string, unknown>` client schema with a versioned DTO containing:

- session ID;
- run ID;
- mode;
- official/advisory status;
- cursor;
- timestamp;
- tick count;
- completion;
- dataset reference/revision/hash;
- branch lineage;
- account state;
- positions;
- orders;
- receipt summary;
- pending-intent count;
- recovery state;
- exposure-blocked flag;
- state hash/freshness;
- permitted actions.

### C. Session catalogue

Add bounded list/read metadata for:

- active sessions;
- durable sessions;
- expired/closed sessions where retained;
- cursor;
- mode;
- symbol/timeframe;
- branch parent;
- recovery state;
- last update;
- actions allowed.

### D. Timeline viewport

Interactive/manual UI must not receive future data.

Add a bounded projection such as:

```text
GET /api/v1/simulator/live-sessions/{sessionId}/viewport
    ?before=300
    &after=0
```

Return only evidence visible at the authoritative cursor:

- completed bars;
- current forming bar or current tick;
- server cursor;
- current timestamp;
- visible orders/fills/positions;
- optional indicator points already available at that time;
- no future rows.

### E. Interactive commands

Expose Trading-owned command DTOs through a Simulation-bound route:

```text
POST /api/v1/simulator/live-sessions/{sessionId}/commands
```

Discriminated command types:

- submit order;
- modify pending order;
- cancel pending order;
- close position;
- reduce position;
- close all practice exposure where permitted.

Every response returns the authoritative receipt and refreshed session state.

### F. Seek

V1 includes skip/seek behavior. Implement one of:

1. owner-approved bounded `seek_to_cursor` operation, or
2. repeated server-side stepping with progress and cancellation.

Do not seek by changing only browser state.

### G. Practice finalization and canonical reproduction

Provide two explicit operations.

#### Finalize practice evidence

Seals the practice journal and produces an advisory review reference.

#### Create canonical reproduction

Replays the exact immutable request and, where supported, the exact cursor-bound manual-intent journal into a separate canonical run. It must verify deterministic evidence before producing an official `SimulationResult`.

A practice or what-if run remains advisory until this operation succeeds.

### H. Batch groups

Add an API-owned batch-group resource:

```text
POST /api/v1/simulator/batches
GET  /api/v1/simulator/batches/{batchId}
GET  /api/v1/simulator/batches/{batchId}/stream
POST /api/v1/simulator/batches/{batchId}/cancel
```

It coordinates multiple independent canonical jobs. It does not compute results.

### I. Durable result catalogue

The in-process job registry is scratch state and can evict terminal jobs. Analytics needs a durable catalogue keyed by canonical run ID.

The catalogue should expose:

- run ID;
- originating job/batch/session ID;
- strategy;
- symbol/timeframe;
- measurement window;
- status;
- result reference;
- report ID;
- artifact manifest;
- quality status;
- canonical/advisory class;
- created/completed time;
- annotation fields;
- archive state.

The catalogue must index immutable Simulation/Analytics evidence rather than copying calculations.

## 11.3 Required Analytics gateway additions

Recommended run-specific routes:

```text
GET  /api/v1/analytics/runs
GET  /api/v1/analytics/runs/{runId}
GET  /api/v1/analytics/runs/{runId}/simulation-result
GET  /api/v1/analytics/runs/{runId}/report
GET  /api/v1/analytics/runs/{runId}/workbench
GET  /api/v1/analytics/runs/{runId}/trades
GET  /api/v1/analytics/runs/{runId}/trades/{ticket}
GET  /api/v1/analytics/runs/{runId}/periods
GET  /api/v1/analytics/runs/{runId}/artifacts
GET  /api/v1/analytics/runs/{runId}/replay-anchors
POST /api/v1/analytics/compare
POST /api/v1/analytics/runs/{runId}/annotations
POST /api/v1/analytics/runs/{runId}/archive
```

### Analytics workbench payload

Do not force the UI to reconstruct charts from raw metric dictionaries.

Create a versioned Analytics-owned payload with finite sections such as:

```text
summary
equity_curve
drawdown_curve
returns_series
vami
monthly_returns
period_tables
trade_calendar
streaks
distribution
histogram
outliers
excursions
duration
grouped_performance
benchmark
costs
warnings
quality_flags
lineage
truncation
```

Every series/table carries:

- unit;
- source context;
- sample count;
- status;
- reason when unavailable;
- truncation metadata.

## 11.4 Current projection gaps to close

The current `DashboardPayload v1` completes:

- summary table;
- equity curve.

It explicitly skips:

- drawdown chart;
- monthly returns table.

The current `PerformanceReport` presentation metadata includes the equity curve but not all V1-equivalent chart series.

The new Analytics UI should not be built on client-side reconstruction. Close these gaps through Analytics-owned projections first.

---

## 12. Proposed V2 frontend structure

```text
app/ui/src/
├── app/workstation/
│   ├── simulator/
│   │   ├── page.tsx
│   │   ├── new/page.tsx
│   │   ├── runs/[jobId]/page.tsx
│   │   ├── sessions/page.tsx
│   │   ├── sessions/[sessionId]/page.tsx
│   │   └── replay/[playbackSessionId]/page.tsx
│   └── analytics/
│       ├── page.tsx
│       ├── compare/page.tsx
│       └── [runId]/
│           ├── layout.tsx
│           ├── overview/page.tsx
│           ├── trades/page.tsx
│           ├── trades/[ticket]/page.tsx
│           ├── returns/page.tsx
│           ├── risk/page.tsx
│           ├── distribution/page.tsx
│           ├── periods/page.tsx
│           ├── benchmark/page.tsx
│           ├── charts/page.tsx
│           ├── realism/page.tsx
│           └── provenance/page.tsx
├── clients/
│   ├── simulator.ts
│   ├── liveSimulation.ts
│   ├── simulationPlayback.ts
│   └── analytics.ts
├── features/simulator/
│   ├── index.ts
│   ├── SimulatorHome.tsx
│   ├── SimulationRunBuilder.tsx
│   ├── SimulationModePicker.tsx
│   ├── CanonicalRunMonitor.tsx
│   ├── BatchRunMonitor.tsx
│   ├── InteractiveSimulationWorkspace.tsx
│   ├── SimulationSessionHeader.tsx
│   ├── SimulationPlaybackWorkspace.tsx
│   ├── SimulationRecoveryPanel.tsx
│   ├── SimulationScenarioPanel.tsx
│   ├── SimulationChecklistPanel.tsx
│   ├── SimulationArtifactDrawer.tsx
│   ├── simulation-store.ts
│   ├── simulation-selectors.ts
│   └── panels/
│       ├── MarketPanel.tsx
│       ├── AccountPanel.tsx
│       ├── PositionsPanel.tsx
│       ├── OrdersPanel.tsx
│       ├── TradesPanel.tsx
│       ├── ManualCommandPanel.tsx
│       ├── RiskEvidencePanel.tsx
│       ├── GovernancePanel.tsx
│       ├── WhatIfPanel.tsx
│       ├── JournalPanel.tsx
│       └── RealismPanel.tsx
└── features/analytics/
    ├── index.ts
    ├── AnalyticsLibrary.tsx
    ├── AnalyticsWorkspace.tsx
    ├── AnalyticsNav.tsx
    ├── AnalyticsRunHeader.tsx
    ├── AnalyticsComparison.tsx
    ├── AnalyticsArtifactDrawer.tsx
    ├── analytics-store.ts
    ├── analytics-selectors.ts
    ├── charts/
    │   ├── TimeSeriesChart.tsx
    │   ├── DistributionChart.tsx
    │   ├── CalendarHeatmap.tsx
    │   └── ExcursionChart.tsx
    └── panels/
        ├── OverviewPanel.tsx
        ├── TradesPanel.tsx
        ├── TradeDetailPanel.tsx
        ├── ReturnsPanel.tsx
        ├── RiskPanel.tsx
        ├── DistributionPanel.tsx
        ├── PeriodsPanel.tsx
        ├── BenchmarkPanel.tsx
        ├── ChartsPanel.tsx
        ├── RealismPanel.tsx
        └── ProvenancePanel.tsx
```

### Component-size rule

Do not recreate V1’s very large execution and performance pages.

Recommended limits:

- page files: composition only;
- workspaces: route-level composition and state;
- panels: one evidence family;
- charts: one visualization responsibility;
- client files: one resource family;
- selectors: pure view-model projection only.

---

## 13. Detailed Simulation screen specifications

## 13.1 Simulator Home

Show:

- New Canonical Backtest;
- New Visual Practice;
- New Manual Practice;
- New Batch;
- Replay a Completed Run;
- Scenario/Mission Practice;
- active jobs;
- active/durable sessions;
- recent canonical results;
- failed/cancelled jobs;
- recovery-required sessions.

No metric conclusions belong on this page beyond owner-supplied summaries.

## 13.2 Run Builder

Use a staged builder.

### Stage 1 — Mode

- Canonical Backtest
- Visual Practice
- Manual Practice
- Batch
- Replay
- Scenario/Mission
- Portfolio Simulation

### Stage 2 — Strategy

- strategy catalogue;
- version;
- description;
- runnable status;
- unavailable reason;
- generated parameter form;
- effective parameter summary;
- warm-up requirement.

Manual mode may omit a strategy.

### Stage 3 — Market

- source/provider;
- symbol or batch universe;
- timeframe;
- start/end;
- bars limit;
- data availability preview;
- expected quality behavior;
- market hours;
- account currency.

### Stage 4 — Execution and costs

- initial balance;
- volume;
- commission;
- spread;
- slippage;
- approved execution/realism preset;
- leverage/provider evidence;
- close-open-positions-at-end policy.

### Stage 5 — Risk and governance

- registered risk policy;
- approved practice limits;
- exposure/margin guardrails;
- scenario-specific limits;
- advisory/canonical declaration.

Do not expose internal risk hashes as editable inputs.

### Stage 6 — Scenario, mission, and assistance

- scenario IDs;
- mission;
- assistance mode;
- checklist;
- fault profile;
- calibration profile.

### Stage 7 — Metadata

- name;
- alias;
- description;
- tags;
- run reason;
- batch group label.

### Stage 8 — Review

Display:

- exact user choices;
- server-derived values;
- official/advisory class;
- expected stages;
- permissions;
- warnings;
- estimated data size if available;
- submit action.

## 13.3 Canonical Run Monitor

Show:

- job ID;
- official status;
- stage;
- ordered event log;
- submitted/started/finished times;
- strategy, symbol, timeframe;
- cancel action;
- reconnect state;
- Last-Event-ID cursor;
- terminal error;
- resulting canonical run ID;
- resulting Analytics report ID;
- Open Analytics action.

Use true event sequences. A heartbeat is not progress.

## 13.4 Batch Run Monitor

Show:

- batch ID;
- group status;
- concurrency;
- per-run status;
- per-run stage;
- completed/failed/cancelled counts;
- batch cancellation;
- retry failed items;
- Open Analytics per successful run;
- Compare successful runs;
- optional aggregate portfolio route only when explicitly requested.

## 13.5 Interactive Simulation Workspace

Recommended layout:

```text
Session Header
├── mode, symbol, timeframe
├── canonical/advisory/recovery badge
├── authoritative cursor and timestamp
├── progress and data identity
└── pause/play/speed/step/seek controls

Main Area
├── Market Chart / Viewport
├── Account Strip
└── Docked Panels
    ├── Positions
    ├── Orders
    ├── Trades
    ├── Manual Command
    ├── Risk Evidence
    ├── What-if
    ├── Scenario
    ├── Checklist
    └── Journal
```

### Pacing model

- Pause stops the UI scheduler.
- Play issues bounded `step` requests.
- Speed controls request cadence and/or bounded tick count.
- The returned server cursor is authoritative.
- The UI reconciles after every response.
- A failed request never advances local time.
- Visibility loss pauses pacing.
- Reconnect first reads session state, then resumes.

### Chart model

The market chart receives only the bounded visible viewport.

It may display:

- completed bars;
- forming bar/current tick;
- entries/exits;
- orders;
- stops/targets;
- indicators that were available at the cursor;
- scenario markers.

It must not download future bars into the browser.

## 13.6 Manual Command panel

Support:

- market and pending orders;
- side;
- volume;
- price;
- stop loss;
- take profit;
- comment;
- strategy/magic metadata where allowed;
- modify;
- cancel;
- close/reduce.

Before submit:

- show non-authoritative UI validation;
- show authoritative server preflight;
- require explicit confirmation where policy requires it.

After submit:

- display receipt;
- refresh authoritative session state;
- append journal event;
- never optimistically invent a fill.

## 13.7 What-if panel

Allow:

- branch from current cursor;
- view allowed override schema;
- submit override;
- open branch in a new route;
- compare parent/branch account state;
- close branch.

Banner:

```text
Advisory branch — this is not an official SimulationResult.
```

## 13.8 Session Recovery

Flow:

```text
Session discovered
    ↓
Restore
    ↓
Dataset and journal replay
    ↓
State-hash verification
    ↓
Verified / Integrity Failure
    ↓
Explicit Rearm
    ↓
Resume at authoritative cursor
```

The Rearm action must be a separate explicit command.

## 13.9 Playback Workspace

Playback is read-only.

Support:

- completed run selection;
- trade anchor;
- start/pause/speed;
- cursor;
- event timeline;
- chart;
- account/position/order state reconstructed from journal;
- event hash evidence;
- Last-Event-ID stream resume;
- return-to-analytics link.

No order ticket is active in playback.

## 13.10 Stop/finalize dialog

Actions depend on session class.

### Canonical job

- Cancel Run
- Keep Running
- Close Monitor

### Practice session

- Pause and Keep Session
- Finalize Practice Evidence
- Create Canonical Reproduction
- Close Session

### What-if branch

- Save Advisory Review
- Close Branch
- Return to Parent

The dialog must explain which actions create official evidence.

---

## 14. Detailed Analytics screen specifications

## 14.1 Analytics Library

Columns and filters:

- run ID;
- annotation/name;
- strategy and version;
- symbol/universe;
- timeframe;
- measurement window;
- mode;
- canonical/advisory;
- status;
- quality status;
- realism profile;
- trade count;
- report status;
- created/completed time;
- tags;
- archive state.

Actions:

- Open;
- Compare;
- Replay;
- Artifacts;
- Edit annotation;
- Archive;
- Delete only where retention policy permits.

Do not delete immutable owner artifacts merely because a UI row is removed.

## 14.2 Analytics Overview

Sections:

### Run identity

- run ID;
- report ID;
- strategy;
- measurement window;
- initial/final balance;
- account currency;
- engine version;
- config/data/request hashes;
- canonical/advisory badge.

### Report status

- required-section status;
- caveats;
- quality flags;
- sample adequacy;
- curve basis;
- non-binding marker.

### Core metric groups

- profitability/PnL;
- trade statistics;
- returns;
- ratios;
- drawdown;
- risk;
- costs/efficiency;
- benchmark;
- statistical.

Show all/long/short contexts where the report supplies them.

### Primary charts

- equity curve;
- drawdown curve;
- cumulative return or VAMI;
- monthly returns when available.

No V1-style PASS/WATCHLIST/REJECT card unless an authoritative owner produces that decision.

## 14.3 Trades

Views:

- table;
- calendar;
- chart;
- excursions;
- sequences;
- grouped summary.

### Trade table

Server-paginated fields:

- ticket;
- symbol;
- type;
- volume;
- entry/exit time;
- entry/exit price;
- SL/TP;
- commission;
- swap;
- profit;
- MAE;
- MFE;
- duration;
- comment;
- magic.

Filters:

- all/winning/losing/breakeven;
- long/short;
- symbol;
- date range;
- duration;
- PnL;
- MAE/MFE;
- outlier status.

### Trade detail

Show:

- complete trade evidence;
- market window around entry/exit;
- linked journal events;
- order/fill chain;
- cost breakdown;
- MAE/MFE;
- replay action;
- provenance.

## 14.4 Returns

Show:

- net PnL;
- ending equity;
- period returns;
- CAGR;
- Sharpe;
- Sortino;
- Calmar;
- profit factor;
- payoff ratio;
- expectancy;
- VAMI/cumulative equity;
- all/long/short contexts;
- undefined reasons;
- sample policy.

## 14.5 Risk

Show:

- max drawdown;
- duration;
- recovery;
- ulcer index;
- pain index;
- volatility;
- VaR;
- conditional VaR;
- risk warnings;
- curve-basis caveat;
- intratrade-exposure limitations;
- drawdown periods/table;
- drawdown chart.

## 14.6 Distribution and statistics

Show:

- mean;
- standard deviation;
- skewness;
- kurtosis;
- percentiles;
- tail ratio;
- histogram;
- outliers;
- bootstrap confidence interval;
- permutation p-value;
- multiple-comparison adjustment;
- sample adequacy;
- trade PnL distribution;
- MAE/MFE distribution;
- duration distribution.

## 14.7 Periods

Controls:

- period;
- rolling mode;
- metric;
- absolute/percent;
- aggregation;
- all/long/short context;
- chart/table toggle.

Outputs:

- period table;
- heatmap;
- trend chart;
- best/worst periods;
- coverage/sample count;
- missing-period reason;
- export.

## 14.8 Benchmark

Show:

- buy-and-hold return;
- strategy and benchmark aligned series;
- alpha;
- beta;
- correlation;
- tracking error;
- information ratio;
- alignment window;
- missing-observation evidence;
- provider and dataset references.

## 14.9 Charts

A curated chart gallery rather than one route per chart.

Groups:

### Equity and returns

- equity;
- cumulative return/VAMI;
- period returns.

### Risk

- drawdown;
- risk distribution;
- rolling risk when owner evidence exists.

### Trades

- consecutive wins/losses;
- holding time;
- exit analysis;
- MAE/MFE;
- efficiency.

### Grouped performance

- instrument;
- setup when supplied;
- hour/day/session;
- direction.

Every chart must declare:

- source payload;
- unit;
- sample count;
- truncation;
- unavailable reason.

## 14.10 Realism

Render Simulation-owned evidence:

- tick model;
- slippage;
- liquidity;
- sessions;
- data quality;
- assumptions;
- limitations;
- calibration;
- parity/certification target;
- fault scenarios;
- diagnostics.

This screen is part of Analytics because analytics without realism context can be misleading, but the evidence remains Simulation-owned.

## 14.11 Provenance and artifacts

Show:

- request/config/data hashes;
- report hashes;
- strategy version;
- dataset revision;
- provider specification revisions;
- execution model;
- calculation model;
- calibration checksums;
- seed;
- engine version;
- dependency versions;
- lineage;
- precision metadata;
- warnings;
- artifact manifest;
- journal/result/report artifact downloads;
- audit/trace IDs where exposed.

This is the correct V2 destination for V1 MetaParams.

## 14.12 Compare Runs

Comparison setup:

- left run;
- right run;
- compatibility status;
- selected metric contexts;
- selected chart series.

Comparison output:

- run/config/data differences;
- metric differences;
- quality/caveat differences;
- trade-count and cost differences;
- equity overlay;
- drawdown overlay;
- period comparison;
- distribution comparison;
- realism differences;
- provenance differences.

The comparison is produced by Analytics and owner projections, not by subtracting arbitrary JSON values in the browser.

---

## 15. State, streaming, and payload design

## 15.1 URL authority

Authoritative identifiers belong in routes:

- job ID;
- batch ID;
- session ID;
- playback session ID;
- run ID;
- ticket;
- active analytics section.

This makes refresh and deep linking reliable.

## 15.2 Zustand responsibility

Zustand may hold:

- unsaved builder values;
- active dock panels;
- chart display preferences;
- playback speed;
- active filters;
- selected comparison rows;
- stream connection state.

It must not be the source of truth for:

- job status;
- session cursor;
- account balance;
- positions;
- trade ledger;
- performance metrics;
- artifact identity.

## 15.3 Browser storage

Session storage may hold:

- last visited run ID;
- last active tab;
- small display settings;
- unfinished builder draft.

Do not store:

- full `SimulationResult`;
- full `PerformanceReport`;
- full trade ledger;
- journal frames;
- market timeline;
- account state.

## 15.4 Streaming

### Canonical jobs

Use SSE sequence and `Last-Event-ID`.

### Playback

Use journal frame sequence and `Last-Event-ID`.

### Interactive sessions

Use request/response stepping initially. Add a state-event stream only when a registered backend stream exists.

### Reconnection

On reconnect:

1. read current resource;
2. compare server cursor/sequence;
3. resume after the server-confirmed sequence;
4. render a visible gap or stale state if resume is impossible.

## 15.5 Pagination and truncation

Require:

- server pagination for runs and trades;
- bounded journal event pages/stream windows;
- bounded chart series;
- truncation metadata;
- virtualization for large tables;
- explicit “showing N of M” labels.

---

## 16. Primary end-to-end workflows

## 16.1 Canonical backtest

```text
Open Simulator
    ↓
Choose Canonical Backtest
    ↓
Configure and review
    ↓
Submit with idempotency key
    ↓
Monitor true progress
    ↓
Succeeded
    ↓
Open Analytics
    ↓
Overview → Trades → Replay → Return
```

## 16.2 Visual auto practice

```text
Choose Visual Practice
    ↓
Select strategy and run recipe
    ↓
Open durable live session
    ↓
Step automatically under UI pacing
    ↓
Pause/resume/branch
    ↓
Complete
    ↓
Finalize practice review
    ↓
Optional canonical reproduction
    ↓
Open official Analytics
```

## 16.3 Manual practice

```text
Choose Manual Practice
    ↓
Open durable session without strategy
    ↓
Advance market
    ↓
Submit server-validated manual intents
    ↓
Review positions/orders/receipts
    ↓
Finalize advisory practice
    ↓
Optional canonical journal reproduction
```

## 16.4 Batch

```text
Choose Batch
    ↓
Select universe and common recipe
    ↓
Create bounded batch group
    ↓
Monitor each canonical job
    ↓
Open individual Analytics
    ↓
Compare successful runs
```

## 16.5 Trade replay

```text
Analytics Trade Detail
    ↓
Replay This Trade
    ↓
Create immutable playback session
    ↓
Stream journal at trade anchor
    ↓
Inspect chart/events/account
    ↓
Return to exact trade detail route
```

## 16.6 Recovery

```text
Sessions
    ↓
Recovery Required
    ↓
Restore
    ↓
Dataset and journal replay
    ↓
State-hash verification
    ↓
Verified / Integrity Failure
    ↓
Explicit Rearm
    ↓
Resume at authoritative cursor
```

---

## 17. Implementation phases

## Phase 0 — Contract and read-model readiness

### Goal

Make the existing V2 backend safely consumable by the complete frontend.

### Work

1. Update Simulator, Analytics, API, and UI READMEs/registries.
2. Register provisional API/UI/Analytics features.
3. Define typed browser DTOs.
4. Add durable canonical result catalogue.
5. Link job ID → run ID → report ID → artifacts.
6. Add safe interactive-session creation.
7. Add typed live-session projection.
8. Add session list.
9. Add bounded viewport.
10. Add manual command route.
11. Add practice finalization/canonical reproduction contract.
12. Add run-specific Analytics routes.
13. Add `AnalyticsWorkbenchPayload`.
14. Add drawdown and period presentation evidence.
15. Add pagination/truncation contracts.
16. Add route-contract tests.

### Exit criteria

A real UI test can:

- submit a safe canonical run;
- reconnect to progress;
- obtain the official run ID;
- load full Simulation and Analytics evidence;
- list and paginate trades;
- create playback;
- create/read/step an interactive session using typed DTOs.

## Phase 1 — Route shells and two-workspace handoff

1. Add Simulator routes.
2. Add Analytics routes.
3. Add shared headers/navigation.
4. Embed the existing `SimulatorWidget`.
5. Add successful-run navigation to Analytics.
6. Add canonical/advisory badges.
7. Add empty/loading/stale/unavailable/error states.

## Phase 2 — Canonical batch end to end

1. Full Run Builder.
2. Job Monitor.
3. Recent jobs.
4. Batch groups.
5. cancellation/retry;
6. durable result library;
7. Open Analytics action.

This phase delivers a production-quality replacement for V1 Batch Auto.

## Phase 3 — Analytics MVP

1. Analytics Library.
2. Overview.
3. complete metric sections;
4. equity;
5. drawdown;
6. Trades table/detail.
7. replay deep link.
8. Realism.
9. Provenance.
10. Artifacts.

This phase completes the core `/simulation → /analytics` journey.

## Phase 4 — Interactive visual and manual simulation

1. safe session creation;
2. viewport;
3. pacing;
4. account/positions/orders/trades;
5. manual commands;
6. pause/resume;
7. durable sessions;
8. stop/finalize dialog;
9. advisory review;
10. canonical reproduction.

## Phase 5 — Replay and round-trip review

1. playback session creation;
2. journal SSE;
3. chart/event synchronization;
4. trade anchors;
5. event hashes;
6. return route;
7. replay tests.

## Phase 6 — Advanced Analytics parity

1. Returns;
2. Risk;
3. Distribution;
4. Periods;
5. Benchmark;
6. Charts gallery;
7. compare runs;
8. all/long/short contexts;
9. exports.

## Phase 7 — V2-only operational depth

1. scenarios;
2. faults;
3. missions;
4. checklists;
5. assistance mode;
6. branch comparison;
7. recovery/rearm;
8. emergency evidence;
9. qualification links;
10. portfolio simulation.

## Phase 8 — Hardening

1. accessibility;
2. responsive layout;
3. virtualization;
4. stream resilience;
5. data-volume testing;
6. security review;
7. contract drift tests;
8. visual regression;
9. performance budgets;
10. complete V1 coverage manifest.

---

## 18. Testing strategy

## 18.1 Typed client tests

Cover:

- every method/path;
- auth/permission behavior;
- idempotency;
- query/path encoding;
- DTO validation;
- malformed response rejection;
- official/advisory fields;
- pagination;
- stream cursors.

## 18.2 Component tests

### Simulator

- mode selection;
- generated strategy parameters;
- validation;
- progress;
- cancellation;
- session pacing;
- cursor reconciliation;
- manual commands;
- branch warning;
- restore/rearm;
- finalization;
- unavailable states.

### Analytics

- run library;
- section navigation;
- metric statuses;
- units;
- caveats;
- quality flags;
- trade pagination;
- filters;
- charts;
- replay links;
- compare;
- artifacts.

## 18.3 Integration tests

Use the real FastAPI application for:

- safe canonical run;
- job stream;
- cancellation;
- result retrieval;
- report projection;
- trade list;
- playback;
- live session;
- manual command;
- recovery;
- comparison.

Do not mock every success path.

## 18.4 End-to-end tests

Required journeys:

1. Canonical run → Analytics Overview.
2. Analytics → Trade Detail → Replay → Return.
3. Visual session → Pause → Leave → Restore → Rearm → Resume.
4. Manual order → receipt → position → close.
5. Branch → parent unchanged.
6. Batch → partial failure → open successful result.
7. Stream disconnect → Last-Event-ID resume.
8. Archived run remains immutable and readable.
9. Advisory result cannot be mistaken for canonical.
10. Missing Analytics evidence renders unavailable rather than zero.

## 18.5 Determinism and integrity tests

Verify:

- same canonical request produces expected deterministic identity behavior;
- frontend never changes server cursor locally;
- playback cannot mutate;
- branch lineage is preserved;
- artifact hashes render exactly;
- full future data never appears in interactive viewport responses;
- client metrics are absent from canonical conclusions;
- comparison uses owner result.

## 18.6 Accessibility

Require:

- keyboard navigation;
- labelled controls;
- accessible tables;
- focus restoration after dialogs;
- screen-reader progress announcements;
- non-colour status labels;
- pause control for automated playback;
- reduced-motion support;
- chart table alternatives.

---

## 19. Acceptance criteria

The frontend is complete only when all of the following are true:

### Scope and ownership

- V1 remains untouched.
- Every V1 Simulation and Performance route has a documented V2 destination in Simulator and Analytics.
- Simulation calculations remain in Simulation.
- Performance metrics and analysis remain in Analytics.
- Monte Carlo remains in Optimization/Simulator ownership.
- UI performs no canonical metric calculation.

### Two-workspace journey

- Simulator and Analytics are separate top-level workspaces.
- A successful canonical run opens its Analytics route.
- Routes are refresh-safe and deep-linkable.
- Analytics preserves the selected run in the URL.
- Trade replay returns to the exact prior context.

### Canonical runs

- The safe browser DTO is used.
- Progress is real and ordered.
- cancellation is truthful;
- the official run ID is distinct from job ID;
- terminal evidence survives job-registry eviction;
- artifacts are discoverable.

### Interactive sessions

- Visual Auto is covered.
- Manual is covered.
- Pause/resume is covered.
- Speed is UI pacing only.
- Cursor is server-authoritative.
- Future data is not exposed.
- Session recovery and explicit rearm are covered.
- Manual commands return real receipts.
- What-if branches remain advisory.
- Parent state is not mutated.
- Practice finalization is distinct from canonical reproduction.

### Replay

- Completed runs can create playback sessions.
- Journal frames are ordered and resumable.
- Playback is read-only.
- Trade anchors work.
- Event integrity is visible.

### Analytics

- Run library exists.
- Overview exists.
- Trades/calendar/chart/detail exist.
- Returns and ratios exist.
- Risk and drawdown exist.
- Distribution/statistics exist.
- Periodical analysis exists through one configurable page.
- Benchmark and buy-and-hold evidence exist where available.
- VAMI/cumulative equity exists.
- Realism and provenance exist.
- Artifacts exist.
- Compatible run comparison exists.
- all/long/short contexts render where provided.
- unavailable metrics explain why.

### V2-only capabilities

- realism disclosure;
- scenarios/faults;
- missions/checklists;
- recovery;
- what-if branch lineage;
- artifact manifest;
- reproducibility hashes;
- quality flags;
- caveats;
- statistical evidence;
- portfolio simulation destination.

### Quality

- TypeScript passes.
- lint passes;
- component tests pass;
- API contract tests pass;
- integration tests pass;
- end-to-end Simulation → Analytics test passes;
- accessibility checks pass;
- large trade lists and chart series remain bounded.

---

## 20. Recommended first coding task

Begin with:

> **Phase 0 — Durable Simulation result catalogue and run-specific Analytics Workbench contract**

The existing V2 canonical widget already submits and monitors a run. The immediate blocker is not the form. It is the absence of a durable, full-fidelity bridge from a completed job to:

- official `SimulationResult`;
- canonical `PerformanceReport`;
- run-specific dashboard/workbench payload;
- closed trades;
- artifacts;
- replay anchors.

Implement this vertical slice first:

```text
POST /api/v1/simulator/runs
    ↓
GET/SSE job progress
    ↓
official run_id
    ↓
GET /api/v1/analytics/runs/{runId}
    ↓
GET /report
    ↓
GET /workbench
    ↓
GET /trades
    ↓
GET /artifacts
```

Then add the V2 routes:

```text
/workstation/simulator/runs/{jobId}
/workstation/analytics/{runId}/overview
/workstation/analytics/{runId}/trades
```

This produces the first complete V2 Simulation → Analytics journey without depending on V1 and without prematurely implementing the more complex interactive/manual session UI.

---

## 21. Implementation-order summary

```text
1. Contracts and durable result bridge
2. Simulator and Analytics route shells
3. Canonical batch flow
4. Analytics MVP
5. Interactive visual/manual sessions
6. Playback and trade replay
7. Advanced Analytics parity
8. V2 scenarios, missions, recovery, and portfolio
9. Hardening and complete parity verification
```

---

## 22. Reference paths inspected

### V1 — read-only product reference

```text
app/web/src/app/(dashboard)/simulation/
app/web/src/components/historical-run/
app/web/src/components/simulation/
app/web/src/components/backtest/
app/web/src/app/(dashboard)/performance/
app/web/src/components/performance/
```

### V2 — authoritative implementation

```text
app/services/simulator/
app/services/simulator/backtest_recipe/
app/services/simulator/state/live_sessions.py
app/services/simulator/reporting/
app/services/analytics/
app/services/analytics/metrics/
app/services/analytics/reports/
app/services/analytics/dashboards/
app/services/api/workstation/simulator/
app/services/api/workstation/simulation/
app/ui/src/features/simulator/
app/ui/src/features/chart/
app/ui/src/clients/liveSimulation.ts
app/ui/src/clients/
```

---

## 23. Final architectural position

The V2 frontend should preserve the strongest V1 product decision:

```text
Simulation is where the run happens.
Analytics is where the run is understood.
```

It should not preserve V1’s weaknesses:

- estimated progress;
- browser-side performance calculations;
- browser-side random Monte Carlo;
- broad untyped payloads;
- empty routes;
- duplicated analysis pages;
- advisory sessions relabelled as official backtests;
- future data resident in an interactive browser.

The final V2 system should be:

- deterministic;
- multi-page;
- deep-linkable;
- resumable;
- replayable;
- evidence-first;
- explicit about realism;
- explicit about uncertainty;
- explicit about official versus advisory state;
- complete across Simulation and Analytics.

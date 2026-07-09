# HaruQuant AI Strategy Template v4

A **copy-ready, broker-neutral Python strategy template** designed for HaruQuantAI.

It uses one canonical JSON configuration as the shared contract for human authors, AI agents, simulation, paper trading, live deployment controls, and audits. Python remains the place for non-trivial signal logic; configuration is the place for identity, parameters, permissions, scheduling, actions, protection, and state requirements.

## What this package standardizes

```text
StrategyManifest
├── identity
├── version
├── chart requirements
├── supported runtime modes
└── strategy capabilities

StrategyParameters
├── scalar optimized parameters
├── indicator parameters
├── order parameters
├── protection parameters
└── generated parameter metadata

TradingOptions
├── schedule and weekend controls
├── end-of-day and Friday exits
├── signal time range
├── max trades per day
├── stop-loss/profit-target bounds
├── warm-up bars
├── session restrictions
└── pending-order distance restrictions

SignalRules
├── long_entry_signal
├── short_entry_signal
├── long_exit_signal
└── short_exit_signal

ActionRules
├── long_entry_action
├── short_entry_action
├── long_exit_action
├── short_exit_action
├── conflict-resolution policy
└── duplicate-trade policy

ProtectionRules
├── stop loss
├── profit target
├── trailing stop
├── trailing activation
├── time/bar exit
└── advanced partial exits

State
├── last processed bar
├── daily trade count
├── open-signal/order identifiers
├── cooldown state
└── idempotency keys
```

## Non-negotiable boundary

```text
Market data + features
    → Strategy
    → TradeIntent
    → Risk Governor
    → Execution Router
    → Broker / Simulator Adapter
```

A strategy **may** calculate signals, manage serializable strategy-local state, and emit `TradeIntent` proposals.

A strategy **must not** call a broker, approve risk, calculate final portfolio-aware size, mutate broker/portfolio state, or record fills as fact. The Risk Governor owns permission, final position sizing, portfolio limits, margin, correlation, and drawdown controls.

`risk_management.strategy_sizing_hint` in the config is therefore a **non-authoritative request**. It can tell the Risk Governor what the strategy intended, but never bypasses it.

## Folder layout

```text
src/haruquant/
├── strategy_framework/           # Shared, stable framework — do not copy per strategy
│   ├── config.py                 # JSON load + deterministic validation
│   ├── contracts.py              # Canonical bars, contexts, intents, decisions
│   ├── base.py                   # Lifecycle, idempotency, generic action resolution
│   └── state.py                  # Serializable common strategy state
└── strategies/
    ├── _template/                # Copy this folder to create a new strategy
    │   ├── strategy.json
    │   ├── rules.py
    │   ├── strategy.py
    │   └── __init__.py
    └── sqx_breakout_atr_trailing/ # Working translation of the SQX example
        ├── strategy.json
        ├── rules.py
        ├── strategy.py
        └── __init__.py
```

## Create a strategy

1. Copy `src/haruquant/strategies/_template/` to a new snake-case folder, for example `ema_trend_following/`.
2. Rename `TemplateStrategy` and update exports in `__init__.py`.
3. Replace placeholders in `strategy.json`. Keep it valid JSON: no comments and no trailing commas.
4. Define every tunable value under `parameters.definitions` and set the active value under `parameters.values`.
5. Implement the four pure functions in `rules.py`.
6. Add tests for no-lookahead, warm-up, signal priority, duplicate prevention, schedule behavior, and protective values.
7. Validate the strategy configuration before it can be used by simulation, paper, or live deployment.

## Parameter contract

Every tunable parameter has one definition and one active value.

```json
{
  "parameters": {
    "definitions": {
      "fast_period": {
        "type": "integer",
        "default": 20,
        "minimum": 1,
        "maximum": 500,
        "step": 1,
        "category": "indicator",
        "optimizable": true,
        "description": "Fast moving-average period."
      }
    },
    "values": {
      "fast_period": 20
    },
    "generation_metadata": {
      "optimization_enabled": true,
      "parameter_sets": []
    }
  }
}
```

The configuration validator checks type, range, required fields, runtime-mode consistency, and required configuration paths. The JSON Schema is included for IDEs, agents, and external validators.

## Run checks

```bash
python -m pip install -e .[dev]
pytest
ruff check .
ruff format --check .
mypy src
```

## Included working example

`sqx_breakout_atr_trailing` is a working translation of the supplied StrategyQuant-style breakout strategy:

- lookback breakout of opening price over prior highs / below prior lows;
- long-first conflict resolution;
- market entry only;
- no duplicate same-direction entries;
- max one entry per day;
- `2.2 × ATR(20)` stop-loss distance;
- `6 × ATR(20)` trailing distance;
- trailing activation at `6 × ATR(130)`;
- no-lookahead: it uses only completed bars supplied in the context.

## Added strategy catalog

The package now includes six additional JSON-configured strategy implementations:

| Strategy ID | Model | Special requirements |
|---|---|---|
| `naive_ma_trend` | 20/50 SMA crossover with 200 SMA trend filter | Main completed bars only |
| `decomposing_trade_ea` | RSI hedged averaging / partial decompression | Quote, account, positions |
| `harriet_hedging_ea` | H1 + M5 structure-confirmed hedging | Quote, account, `chart_bars["H1"]`, positions |
| `market_structure_ea` | ZigZag structure hedge and event-driven grid | Quote, account, positions, pending orders, `zigzag_extremes`, execution events |
| `random_walk_ea` | Fixed dual layered baskets (not random) | Quote and reconciled positions |
| `white_fairy_ea` | RSI averaging plus pyramiding | Quote, account, positions, serialized local state |

Each module begins with a complete strategy docstring, and
`docs/MQL5_TRANSLATION_AUDIT.md` records source-to-intent mapping, runtime
requirements, and the intentional broker-neutral adaptations.

### Agent-safe instantiation

```python
from haruquant.strategies.registry import load_bundled_strategy

strategy = load_bundled_strategy("naive_ma_trend")
# Runtime supplies a validated MarketContext, then downstream Risk Governor
# and execution services handle the returned intents.
decision = strategy.evaluate(context)
```

The strategy package never sends broker orders directly.  In particular, the
MQL5 ports use `OPEN`, `MODIFY`, `PARTIAL_CLOSE`, and `CANCEL_PENDING` intents
so that simulator, paper, MT5, and cTrader execution paths share the same
strategy logic.



## Simple backtesting module

`haruquant.backtesting` now runs all bundled strategies against canonical OHLCV
bars using a deterministic, no-lookahead execution model. It evaluates signals
at a completed bar close and executes the resulting intent at the next bar
open. The module supports market/stop/limit entries, close, partial close,
modify, cancel-pending, SL/TP, trailing stops, execution events, trade ledgers,
equity curves, and first-pass metrics.

```python
from haruquant.backtesting import BacktestConfig, SimpleBacktestEngine, load_ohlcv_csv
from haruquant.strategies import load_bundled_strategy

result = SimpleBacktestEngine(
    BacktestConfig(point_size=0.00001, spread_points=10.0, contract_size=100_000.0)
).run(
    load_bundled_strategy("naive_ma_trend"),
    load_ohlcv_csv("EURUSD_H1.csv"),
    symbol="EURUSD",
    timeframe="H1",
)
print(result.to_dict())
```

See [`docs/BACKTESTING.md`](docs/BACKTESTING.md) for execution assumptions,
MQL5-port requirements, known limitations, and the command-line interface.

---

## Strategy Authoring Guide & Configuration Model

This section serves as the canonical reference for designing, configuring, and authoring strategies in HaruQuant.

### 1. Canonical Strategy Configuration Model

`strategy.json` is the canonical, JSON-serializable configuration contract. It is deliberately declarative so agents can inspect, modify, diff, validate, and audit it safely.

#### Why the configuration is hybrid

Use JSON for stable declarative settings:

- identity, version, chart requirements, lifecycle and runtime permissions;
- tunable parameter definitions and active values;
- trading schedule and filtering controls;
- action, conflict, duplicate, and protection policy;
- risk sizing hints and strategy-local state contract.

Use Python for signal logic that becomes complex, performance-sensitive, or needs custom calculations. Each JSON signal rule declares the Python entry point and inputs it needs. This avoids forcing a fragile universal rule DSL on every strategy while keeping strategy behavior discoverable for AI agents.

#### Canonical top-level keys

| Key | Responsibility |
|---|---|
| `schema_version` | Version of this JSON contract. |
| `strategy_manifest` | Identity, version, charts, runtime support, capabilities, permissions. |
| `trading_profile` | Strategy-owned symbol/chart identity and simulation defaults. |
| `parameters` | Definitions, active values, optimization/generation metadata. |
| `risk_management` | Non-authoritative sizing and risk intent for the Risk Governor. |
| `trading_options` | Time, session, warm-up, daily-entry, distance, SL/PT bounds. |
| `signal_rules` | Four named signal contracts with Python entry points. |
| `action_rules` | Entry/exit actions, conflict policy, duplicate policy. |
| `protection_rules` | Stops, target, trailing, time exits, partial-exit declaration. |
| `state_contract` | Strategy-local state that must be serializable. |
| `required` | Required dot paths verified before activation. |

#### Do not duplicate values

- Store `strategy_id`, description, author, and creation date only in `strategy_manifest.identity`.
- Store version only in `strategy_manifest.version`.
- Store runtime permissions only in `strategy_manifest.permissions`.
- Store active parameter values only in `parameters.values`.
- Store parameter definition/range information only in `parameters.definitions`.

This prevents an agent from changing one copy and leaving another copy stale.

#### Parameter types supported by the built-in validator

`integer`, `number`, `string`, `boolean`, `list`, `dict`.

For numeric parameters, the validator supports `minimum`, `maximum`, and `step`. A numeric value must fall within range and align to step from the minimum/default anchor.

#### Runtime and lifecycle meanings

| Term | Values | Meaning |
|---|---|---|
| Lifecycle status | `RESEARCH`, `PAPER`, `ACTIVE`, `RETIRED` | Governance/deployment maturity state. |
| Runtime mode | `SIMULATOR`, `PAPER`, `LIVE` | Where the strategy is currently evaluated. |

The strategy framework checks the permitted runtime list. The deployment/governance layer must additionally determine whether the lifecycle status is eligible for that environment.

#### Strategy state scope

The common state object intentionally stores only strategy-local facts:

- last processed signal bar;
- daily emitted-entry count;
- emitted intent identifiers;
- local intent-to-order bindings received from execution callbacks;
- cooldown deadline.

It is not a ledger. The execution, portfolio, and storage layers own authoritative orders, fills, positions, and account state.

#### JSON path conventions

Use simple dot paths in `required`, for example:

```json
[
  "strategy_manifest.identity.strategy_id",
  "trading_profile.symbols.main.symbol",
  "parameters.values.breakout_lookback"
]
```

The built-in validator verifies that every listed path exists and is not `null`.

---

### 2. Strategy Authoring Checklist

#### Before implementation

- [ ] Copy `_template` into a unique snake-case package folder.
- [ ] Assign a stable `strategy_id`; never reuse an ID for a materially different strategy.
- [ ] Set a semantic version.
- [ ] Define chart, symbol, timeframe, runtime modes, and capabilities.
- [ ] Keep live runtime out of `permitted_environments` until strategy governance explicitly permits it.

#### Configuration

- [ ] Declare every tunable value under `parameters.definitions`.
- [ ] Put exactly one active value per declared parameter in `parameters.values` where needed.
- [ ] Set valid type, bounds, step, category, and description.
- [ ] Add every required config path to `required`.
- [ ] Define warm-up bars for all lookback and indicator requirements.
- [ ] Specify entry/exit conflict and duplicate trade policy deliberately.
- [ ] Define schedule, weekend, session, EOD, Friday, and pending-order controls.
- [ ] Declare strategy-local state fields needed for restart safety.

#### Python rules

- [ ] Keep `rules.py` pure: input context and parameters in; booleans/values out.
- [ ] Use completed bars only unless tick-level behavior is explicitly required and tested.
- [ ] Do not place orders, call brokers, or access portfolio databases from strategy code.
- [ ] Do not calculate authoritative position size.
- [ ] Return `False` rather than making a speculative decision when data is insufficient.

#### Tests

- [ ] Configuration validates.
- [ ] Minimum warm-up blocks evaluation.
- [ ] The first valid evaluation produces the intended signal/intent.
- [ ] A second evaluation of the same signal bar produces no duplicate intent.
- [ ] Long/short and entry/exit conflict policy is tested.
- [ ] Schedule/weekend/session filters are tested.
- [ ] Stop, target, trailing, and time-exit formulas are tested.
- [ ] State serializes and restores correctly.

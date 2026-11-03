# Multiple exits generation (scale-out / ATM) — field reference (for UI tests)

> The "Generate ATM using config below" mode of the **ATM** settings tab (`SettingsAdvancedTM`) — a
> top-level settings tab (`SettingsTab` id 35, title "ATM"), not a sub-panel nested under Building
> blocks / What to build, even though it's a Building-blocks-adjacent, Build-task-only feature.

Source:
- `internal/plugins/SettingsAdvancedTM/module.js` — tab registration (`configElemName: 'ATMs'`,
  `dataItem: 'settings-advancedtm'`, tasks `Build,Optimize,Retest,AutomaticRetest,NeuralNetworkTrainer`).
- `internal/plugins/SettingsAdvancedTM/advancedTM.html` (`data-testid="settings-atm-panel"`) — all
  controls below.
- `internal/plugins/SettingsAdvancedTM/AdvancedTMService.js` (lines 429-482) — `atmTypes` enum source
  and `config.generate` defaults.
- `projects/libs/SQAppLib/src/com/strategyquant/tradinglib/atm/ATMTypes.java` — backend enum
  (`DONT_USE=0, FROM_STRATEGY=1, FROM_CONFIG=2, GENERATE=3`).
- `projects/libs/SQAppLib/src/com/strategyquant/tradinglib/atm/ATMGenerateConfig.java` — backend model
  and defaults for the "generate" fields (cross-checked against the JS defaults below; they match).

## Top of tab (always visible)

| Label | Config key (ng-model) | Type | Default | Notes |
|---|---|---|---|---|
| Enable ATM | `config.enableATM` | checkbox | `false` | `data-testid="settings-atm-enable"`. Gates every other control on the tab (`ng-disabled="!config.enableATM"`). |
| ATM config source — Use ATM defined below | `config.atmType` = `atmTypes.fromConfig` (`2`) | radio (`name="ATMTypeRadio"`) | — | Overwrites any ATM saved in the strategy. |
| ATM config source — Use ATM from strategy | `config.atmType` = `atmTypes.fromStrategy` (`1`) | radio | **default** | |
| ATM config source — Generate ATM using config below | `config.atmType` = `atmTypes.generate` (`3`) | radio | — | `data-testid="settings-atm-type-generate"`. Only shown when `isBuildTask`; disabled unless `$root.license.isUltimateVersion`. Has a "How it works" link (`onHowItWorks()`). **This radio value is what gates the whole generation-config section below.** |
| Size decimals | `config.sizeDecimals` | number spinner | `1` | min 0, max 10, step 1, `updateOn: 'blur'`. |
| Minimum size | `config.minSize` | number spinner | `0.1` | min 0.0000001, max 1000000, step 0.1, `updateOn: 'blur'`. |

`atmTypes` values come from server constant `ATMTypes` (`ConstantsServlet.java` → `new
ATMTypes().toJSON()`), matching the Java `ATMTypes` enum above.

## Manual exits list (`config.atmType != atmTypes.generate`)

Not the focus of this panel but present alongside it: **Add new exit** button (`onAddNewExit()`),
per-exit rows (`config.exits[]`, click to `onEditExit($index)`, × to `onDeleteExit($index)`), plus
**Save to file** / **Load from file** buttons (`data-testid="settings-atm-load-btn"` on Load). The
exit editor itself is `addNewExitPopup.html` (not detailed here — out of scope for "generation").

## "ATM generation configuration" (only when `config.atmType == atmTypes.generate`)

### Exit types to use (`config.generate.*`) — left column

| Label | Use checkbox (ng-model) | Default | Min spinner | Max spinner | Default min/max | Extra |
|---|---|---|---|---|---|---|
| Multiple of original SL - Close | `config.generate.useSLMultiple` | `false` | `slMultipleMin` | `slMultipleMax` | `0.5` / `2` | `data-testid="settings-atm-exit-sl-multiple"`; spinners min 0.1 max 10 step 0.1; label "x Order SL". |
| Multiple of original PT - Close | `config.generate.usePTMultiple` | `false` | `ptMultipleMin` | `ptMultipleMax` | `0.5` / `2` | `data-testid="settings-atm-exit-pt-multiple"`; spinners min 0.1 max 10 step 0.1; label "x Order PT". |
| Fixed Profit | `config.generate.useFixedProfit` | `false` | — | — | — | `data-testid="settings-atm-exit-fixed-profit"`; parent checkbox for the two sub-options below. |
| ↳ Fixed pips | `config.generate.useFixedProfitFixedPips` | `false` | `fixedProfitFixedPipsMin` | `fixedProfitFixedPipsMax` | `30` / `80` | `data-testid="settings-atm-exit-fixed-profit-pips"`; spinners min 0 step 1. |
| ↳ ATR Based (multiple) | `config.generate.useFixedProfitATR` | `false` | `fixedProfitATRMutliplierMin` | `fixedProfitATRMutliplierMax` | `1.5` / `3` | spinners min 0.1 max 10 step 0.1. |
| ↳ ATR period | — | — | `fixedProfitATRPeriodMin` | `fixedProfitATRPeriodMax` | `20` / `20` | spinners min 2 max 1000 step 1. |
| Trailing stop | `config.generate.useTS` | `false` | — | — | — | `data-testid="settings-atm-exit-trailing-stop"`; parent checkbox. |
| ↳ Fixed pips | `config.generate.useTSFixedPips` | `false` | `tsFixedPipsMin` | `tsFixedPipsMax` | `30` / `80` | `data-testid="settings-atm-exit-trailing-stop-pips"`; spinners min 0 step 1. |
| ↳ ATR Based (multiple) | `config.generate.useTSATR` | `false` | `tsATRMutliplierMin` | `tsATRMutliplierMax` | `1.5` / `3` | spinners min 0.1 max 10 step 0.1. |
| ↳ ATR period | — | — | `tsATRPeriodMin` | `tsATRPeriodMax` | `20` / `20` | spinners min 2 max 1000 step 1. |
| None - run until closed by exit rule | `config.generate.useNone` | `false` | — | — | — | `data-testid="settings-atm-exit-none"`; parent checkbox. |
| ↳ Limit - Close after max **[N] bars** | `config.generate.useNoneLimit` | `false` | `noneMinBars` | `noneMaxBars` | `50` / `50` | `data-testid="settings-atm-exit-none-limit"`; spinners min 1 step 1; suffix "bars". |

All spinners use `ng-model-options="{ updateOn: 'blur' }"` and are disabled unless `config.enableATM`.

### Exit scenarios — right column ("will be chosen randomly")

| Label | Config key (ng-model) | Default | `data-testid` |
|---|---|---|---|
| 2 exits — 50% on Exit 1, 50% on Exit 2 | `config.generate.exits_5050` | `true` | `settings-atm-scenario-5050` |
| 2 exits — 33% on Exit 1, 66% on Exit 2 | `config.generate.exits_3366` | `true` | `settings-atm-scenario-3366` |
| 2 exits — 66% on Exit 1, 33% on Exit 2 | `config.generate.exits_6633` | `true` | `settings-atm-scenario-6633` |
| 3 exits — 33/33/33% | `config.generate.exits_333333` | `true` | `settings-atm-scenario-333333` |
| 3 exits — 50/25/25% | `config.generate.exits_502525` | `true` | `settings-atm-scenario-502525` |
| 3 exits — 25/50/25% | `config.generate.exits_255025` | `true` | `settings-atm-scenario-255025` |
| 3 exits — 25/25/50% | `config.generate.exits_252550` | `true` | `settings-atm-scenario-252550` |

All 7 scenario checkboxes default **checked** (`true`) — matching the prose page's "choose from 7 of
the most-used scenarios."

## XML round-trip (for reference, not a UI field)

`AdvancedTMService.js` writes these into `ATMs/ATM/Generate/{Types,Scenarios}` elements; the backend
counterpart `ATMGenerateConfig.java` reads the same attribute names (`SLMultiple[use|minMultiplier|
maxMultiplier]`, `PTMultiple[...]`, `FixedProfit[use|useFixedPips|minPips|maxPips|useATR|
minMultiplier|maxMultiplier|minATRPeriod|maxATRPeriod]`, `TrailingStop[...]`, `None[useLimit|minBars|
maxBars]`, `TwoExits[exit5050|exit3366|exit6633]`, `ThreeExits[exit333333|exit502525|exit255025|
exit252550]`) and its Java defaults match the JS defaults tabulated above.

## Related

- Prose page: [../multiple-exits.md](../multiple-exits.md)
- Fields hub: [README.md](README.md)
- Fixed / defined ATM exits (manual list, `config.atmType != generate`): [../atm.md](../atm.md)
- Multiple orders (entry-side, not configurable): [multi-orders.md](multi-orders.md)
- Improving only ATM on an existing strategy: [../parts-to-improve.md](../parts-to-improve.md)

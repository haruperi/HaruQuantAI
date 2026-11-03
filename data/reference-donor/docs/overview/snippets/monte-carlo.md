# Monte Carlo randomization methods — full catalog (settings for UI tests)

> Reference enumeration of every built-in Monte Carlo snippet — both the fast **trade
> manipulation** methods and the slow, re-backtesting **retest** methods — with the exact
> parameters each one exposes (name, default, min, max, step). This is a lookup table; for what
> each test category *is* and how it's used see
> [`../robustness-tests/monte-carlo-trade-manipulation.md`](../robustness-tests/monte-carlo-trade-manipulation.md)
> and [`../robustness-tests/monte-carlo-retest-methods.md`](../robustness-tests/monte-carlo-retest-methods.md).

## How the set is assembled

Monte Carlo comes in two snippet families, both **extensible** (drop a class in the folder and it
appears in the picker):

- **Trade manipulation** — classes extend `MonteCarloManipulation`
  (`com.strategyquant.tradinglib.MonteCarloManipulation`) and implement
  `modifyTrades(IRandomGenerator rng, OrdersList originalOrders)`, mutating the trade list already
  produced by the main backtest. No re-backtest is run, so this family is fast. Loaded by
  `MonteCarloManipulationList` from `MonteCarlo/Manipulation`
  (`work_directory/StrategyQuant/internal/extend/Snippets/SQ/MonteCarlo/Manipulation/`).
- **Retest methods** — classes extend `MonteCarloRetest` (`com.strategyquant.tradinglib.MonteCarloRetest`)
  and declare a `type` via their constructor: `MonteCarloTestTypes.ModifySettings` (1) for classes
  that override `modifySettings(rng, settings)` to perturb a backtest setting (spread, slippage,
  starting bar, strategy parameters, min distance) before a full re-backtest, or
  `MonteCarloTestTypes.ModifyData` (2) for classes that override `modifyData(rng, tickEvent,
  globalATR)` (per-tick) or `modifyOHLCData(rng, data, globalATR)` (per-bar) to perturb the history
  data itself. Because each simulation re-runs the backtest, this family is slow. Loaded by
  `MonteCarloRetestList` from `MonteCarlo/Retest`
  (`work_directory/StrategyQuant/internal/extend/Snippets/SQ/MonteCarlo/Retest/`).

Each class carries `@ClassConfig(name=..., display=...)`: `name` is the picker label, `display` is
a template (with `#ParameterName#` placeholders) that renders the configured instance as one line
— useful for UI tests to match against a configured scenario. `@Parameter` fields are the exact
settings exposed in the configuration UI.

## Trade manipulation

Snippets under `MonteCarlo/Manipulation` — fast, operate on existing trades.

| Display name | Class | Description |
|---------------|-------|--------------|
| MACHR Block Randomization | `MACHRBlockRandomization` | Bootstrap-samples blocks of consecutive trades (with replacement) to simulate robustness against market-regime changes, preserving trade order/structure within each block. |
| Randomize trades order | `RandomizeTradesOrder` | Shuffles the order of existing trades (`Exact`: pure shuffle; `Resampling`: samples trades with replacement, duplicating some), then re-derives open/close timestamps so trades stay chronologically ordered. |
| Randomly degrade execution price | `RandomlyDegradeExecution` | For a randomly chosen subset of trades (by probability), worsens the Close Price by a random amount scaled to the trade's Open–Close price range, simulating slippage/execution issues. |
| Randomly skip trades | `RandomlySkipTrades` | Removes a randomly chosen subset of trades (count = probability × total trades), simulating missed trades (e.g. platform/internet failure). |
| Simulate Parameter Jitter Effects | `SimulateParameterJitter` | Randomly skips some trades and randomly nudges the Close Price of the remaining ones (better or worse), simulating the combined effect of minor strategy-parameter instability. |

## Data / retest randomization

Snippets under `MonteCarlo/Retest` — slow, each simulation re-runs a full backtest with a
perturbed setting or history data.

| Display name | Class | Description |
|---------------|-------|--------------|
| Randomize history data (by tick) | `RandomizeHistoryData` | Per tick, randomly nudges Ask/Bid up or down by an amount scaled to ATR, with independent probability and max-change settings for up vs. down moves; can optionally keep bars "connected" across gaps. |
| Randomize history data (by tick, fixed range) | `RandomizeHistoryDataFixedRange` | Per tick, perturbs Bid relative to the previous tick's own price change (not ATR-based), scaled by a single max-change percentage; community-contributed variant (`bendx77`). |
| Randomize OHLC history data | `RandomizeHistoryDataOHLC` | Per bar, independently randomizes Open/High/Low/Close (each with its own probability), scaled to a computed ATR, with optional gap-preserving handling of the Open relative to the previous bar's Close. |
| Randomize min distance | `RandomizeMinDistance` | Picks a random "Minimum Distance from price" setting (for stop/limit orders) between Min and Max for each simulation. |
| Randomize slippage | `RandomizeSlippage` | Picks a random Slippage setting between Min and Max for each simulation. |
| Randomize spread | `RandomizeSpread` | Picks a random Spread setting between Min and Max for each simulation, applied to the main chart and any subcharts sharing the same symbol. |
| Randomize starting bar | `RandomizeStartingBar` | Picks a random Starting Bar offset (0 to Max change) for each simulation, re-running the backtest from a different start point. |
| Randomize strategy parameters | `RandomizeStrategyParameters` | Randomly nudges the strategy's Period/Constant/Other-Param/Exit-Used/Exit-Unused/Trading-Options-type parameters (Shift and Boolean types excluded, "Magic" parameters skipped) by up to Max change %, at the given per-parameter Probability; retries until at least one value actually changes. |
| Randomize strategy parameters Customizable | `RandomizeStrategyParametersCustomizable` | Same randomization mechanism as "Randomize strategy parameters," but with an explicit checkbox per parameter category (Period, Shift, Constant, Other Param, Exit Used, Exit Unused, Boolean, Trading Options) to choose exactly which categories participate. |

## Parameters — Trade manipulation

### MACHR Block Randomization (`MACHRBlockRandomization`)

Display template: `Randomize blocks of trades, block size #BlockSize#`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| BlockSize | 5 | 2 | 50 | 1 | Number of trades per block. Larger blocks preserve more of the original market-regime structure. |
| PreserveTimestamps | true | — | — | — | Boolean. If true, adjusts timestamps to maintain chronological order after block randomization. |

### Randomize trades order (`RandomizeTradesOrder`)

Display template: `Randomize trades order, with method #Method#`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Method | resampling | — | — | — | Selection editor, values `Exact=exact, Resampling=resampling`. Exact only shuffles trade order; Resampling samples trades with replacement (more memory-intensive). |

### Randomly degrade execution price (`RandomlyDegradeExecution`)

Display template: `Degrade close price for #Probability#% of trades, by max #MaxDegradationPercent#% of price range`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Probability | 15 | 1 | 100 | 1 | Chance (%) that any given trade's Close Price is degraded. |
| Max Degradation Percent | 25 | 0 | 100 | 1 | Maximum degradation applied, as a % of the trade's original Open–Close price range. |

### Randomly skip trades (`RandomlySkipTrades`)

Display template: `Randomly skip trades, with probability #Probability# %`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Probability | 10 | 1 | 100 | 1 | Probability (%), converted to a trade count (`round(totalTrades × probability)`), of trades randomly removed. |

### Simulate Parameter Jitter Effects (`SimulateParameterJitter`)

Display template: `Simulate Param Jitter: Skip Prob #SkipProbability#%, Adjust Prob #AdjustProbability#%, Max Price Adj #MaxPriceAdjustPercent#%`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Skip Probability | 5 | 0 | 100 | 1 | Chance (%) a trade is skipped (removed) entirely. |
| Adjust Probability | 20 | 0 | 100 | 1 | Chance (%) a non-skipped trade's Close Price is adjusted. |
| Max Price Adjust Percent | 15 | 0 | 100 | 1 | Maximum adjustment (+/-), as a % of the trade's Open–Close price range. |

## Parameters — Data / retest randomization

### Randomize history data (by tick) (`RandomizeHistoryData`)

Display template: `Randomize history data (by tick), with probability #ProbabilityUp# % up / #ProbabilityDown# % down and max price change of ATR #MaxChangeUp# % up / #MaxChangeDown# % down`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Probability up (`ProbabilityUp`) | 20 | 1 | 100 | 1 | Probability of changing the price up. |
| Max up change (`MaxChangeUp`) | 10 | 1 | 100 | 1 | Maximum up change, in % of ATR(14). |
| Probability down (`ProbabilityDown`) | 20 | 1 | 100 | 1 | Probability of changing the price down. |
| Max change down (`MaxChangeDown`) | 10 | 1 | 100 | 1 | Maximum down change, in % of ATR(14). |
| Keep connected (`KeepConnected`) | true | — | — | — | Boolean. Preserve original gaps between the previous Close and new Open bars. |

Note: at higher-than-selected-timeframe precision, `MaxChangeUp`/`MaxChangeDown` are internally
divided by 3 (`initSettings`) so the per-tick change doesn't overshoot the resulting bar.

### Randomize history data (by tick, fixed range) (`RandomizeHistoryDataFixedRange`)

Display template: `Modified randomize history data (by tick), with max change #MaxChange# % of tick price changes`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Max change price (`MaxChange`) | 40 | 0 | 1000 | 1 | Maximum change, as a % of the original tick-to-tick price change, applied to the working (randomized) price. |

### Randomize OHLC history data (`RandomizeHistoryDataOHLC`)

Display template: `Randomize OHLC history data, max price change #MaxChange# % of ATR(#ATRPeriod#) and probabilities (O,H,L,C): #ProbabilityOpen#, #ProbabilityHigh#, #ProbabilityLow#, #ProbabilityClose#`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| % Probability, Open (`ProbabilityOpen`) | 100 | 0 | 100 | 1 | Probability of changing the Open price. |
| % Probability, High (`ProbabilityHigh`) | 100 | 0 | 100 | 1 | Probability of changing the High price. |
| % Probability, Low (`ProbabilityLow`) | 100 | 0 | 100 | 1 | Probability of changing the Low price. |
| % Probability, Close (`ProbabilityClose`) | 100 | 0 | 100 | 1 | Probability of changing the Close price. |
| Max Change in % of ATR (`MaxChange`) | 10 | 1 | 100 | 1 | Maximum change applied to O/H/L/C, in % of ATR. |
| ATR Period (`ATRPeriod`) | 14 | 3 | 200 | 1 | Period used for the internally computed ATR. |
| Keep connected (`KeepConnected`) | true | — | — | — | Boolean. If true, preserves the original gap between the previous bar's Close and this bar's Open. |
| % Probability, Close (`ProbabilityGapChange`) | 100 | 0 | 100 | 1 | Probability of changing the gap itself; used only when `KeepConnected=true`. |
| Max Change of gap in % (`MaxChangeOfGap`) | 10 | 1 | 100 | 1 | Maximum change of the gap, in %; used only when `KeepConnected=true`. |

Note: the source declares **two** `@Parameter` fields with the identical display name `"%
Probability, Close"` — one backs `ProbabilityClose` (Close-price change probability), the other
backs `ProbabilityGapChange` (gap-change probability, gated on `KeepConnected`). This is a naming
collision in the snippet source itself (not a transcription error here); UI tests that locate a
parameter by its label rather than by field name should account for this duplicate.

### Randomize min distance (`RandomizeMinDistance`)

Display template: `Randomize min distance from price from #Min# to #Max#`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Min | 0 | 0 | 100 | 0.1 | Lower bound of the randomized Minimum Distance from price setting. |
| Max | 10 | 0 | 100 | 0.1 | Upper bound of the randomized Minimum Distance from price setting. |

### Randomize slippage (`RandomizeSlippage`)

Display template: `Randomize slippage from #Min# to #Max#`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Min | 0 | 0 | 10000 | 0.1 | Lower bound of the randomized Slippage setting. |
| Max | 5 | 0 | 10000 | 0.1 | Upper bound of the randomized Slippage setting. |

### Randomize spread (`RandomizeSpread`)

Display template: `Randomize spread from #Min# to #Max#`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Min | 1 | 0 | 10000 | 0.1 | Lower bound of the randomized Spread setting. |
| Max | 5 | 0 | 10000 | 0.1 | Upper bound of the randomized Spread setting. |

### Randomize starting bar (`RandomizeStartingBar`)

Display template: `Randomize starting bar, with max change #MaxChange#`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Max change (`MaxChange`) | 100 | 10 | 5000 | 100 | Upper bound (exclusive) for the randomly chosen Starting Bar offset (0 to `MaxChange`). |

### Randomize strategy parameters (`RandomizeStrategyParameters`)

Display template: `Randomize strategy parameters, with probability #Probability# % and max change #MaxChange# %`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Probability | 10 | 1 | 100 | 1 | Per-parameter probability (%) that a given parameter is changed in a simulation. |
| Max change | 20 | 1 | 100 | 1 | Maximum percentage change applied to a changed numeric parameter. |
| Symmetric parameters (`Symmetric`) | true | — | — | — | Boolean. If true, uses symmetric parameters (shared between long/short side); if false, long and short parameters are randomized independently. |

Fixed parameter-type inclusion (not exposed as UI toggles in this variant — always applied):
Period, Constant, Other Param, Exit Used, Exit Unused, Trading Options are eligible for
randomization; Shift and Boolean-type parameters are excluded; any parameter whose name contains
`"Magic"` is always skipped.

### Randomize strategy parameters Customizable (`RandomizeStrategyParametersCustomizable`)

Display template: `Customizable Randomize strategy parameters, with probability #Probability# % and max change #MaxChange# %`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Probability | 100 | 1 | 100 | 1 | % probability of parameter change. |
| Max change | 50 | 1 | 500 | 1 | Max % change of parameter. |
| Symmetric parameters (`Symmetric`) | true | — | — | — | Boolean. If true, parameters are shared between long/short side; if false, randomized independently. |
| Period | true | — | — | — | Boolean. Randomize Period-type parameters. |
| Shift | false | — | — | — | Boolean. Randomize Shift-type parameters. |
| Constant | false | — | — | — | Boolean. Randomize Constant-type parameters. |
| Other Param (`OtherParam`) | false | — | — | — | Boolean. Randomize Other-Param-type parameters. |
| Exit Used (`ExitUsed`) | false | — | — | — | Boolean. Randomize Exit-Used-type parameters. |
| Exit Unused (`ExitUnused`) | false | — | — | — | Boolean. Randomize Exit-Unused-type parameters. |
| Boolean | false | — | — | — | Boolean. Randomize Boolean-type parameters. |
| Trading Options (`TradingOptions`) | false | — | — | — | Boolean. Randomize Trading-Options-type parameters. |

Same "Magic"-name skip and Period/Constant/OtherParam/etc. numeric-vs-boolean handling as
`RandomizeStrategyParameters`, but each parameter type is individually gated by its own checkbox
above instead of being hard-coded.

## Related

- [Monte Carlo — trade manipulation — robustness test](../robustness-tests/monte-carlo-trade-manipulation.md)
- [Monte Carlo — retest methods — robustness test](../robustness-tests/monte-carlo-retest-methods.md)
- [What-If manipulations catalog](whatif.md)
- [Snippets hub](README.md)
- [Cross-checks settings](../settings/cross-checks.md)

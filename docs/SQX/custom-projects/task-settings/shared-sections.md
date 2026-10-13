# Shared settings sections

Sections used by several task types. Parsers: `ProjectConfigHelper` (the central XML reader),
`Settings/impl/*` plugins.

## `<Databanks>` — input/output wiring

See [../project-config.md](../project-config.md#databank-wiring-between-tasks--settingsdatabanks).
Roles: `Input`/`Source` (required — no fallback), `Output`/`Target` (falls back to `Results`).
`retestSelected="true"` switches to the explicit `<SelectedStrategies><Strategy>…</Strategy></…>` list.

## `<Data>` — data, engine, date ranges

```xml
<Data>
  <Setups>
    <Setup dateFrom="2003.5.5" dateTo="2019.12.31" testPrecision="1"
           session="No Session" slippage="1" minDist="0" engine="MetaTrader4">
      <Chart symbol="GBPUSD_M1_dukas" timeframe="H1" spread="3" />
      <Chart symbol="Same as main chart" timeframe="D1" spread="3" />  <!-- subcharts -->
      <Commissions><Method type="None" use="true"><Params /></Method></Commissions>
      <Swap use="false" type="money" long="0" short="0" tripleSwapOn="WEDNESDAY" rolloutHour="23:00" />
    </Setup>
  </Setups>
  <OutOfSample showGraph="false"><Range dateFrom="2015.11.16" dateTo="2016.12.30" type="oos" /></OutOfSample>
</Data>
```

- Dates `yyyy.M.d`. `<Setup>` attrs `dateFrom/dateTo/testPrecision/slippage/minDist/engine` are
  **hard requirements** (`Data/Setups/Setup` must exist).
- `testPrecision`: `1` selected TF only, `2` 1-minute tick sim, `3` real tick custom spread,
  `4` real tick real spread, `5` trade on bar open.
- `engine`: `MetaTrader4`, `MetaTrader5 (netted)`, `MetaTrader5 (hedged)`, `Tradestation`,
  `MultiCharts`, `JForex`, `NinjaTrader8`, `Stockpicker`, `Single-asset cloud strategy`.
  The engine picks the fill simulator **and** whether rules run on bar open (MetaTrader/JForex,
  closed bar = `[1]`) or bar close (Tradestation/MultiCharts/NinjaTrader8, closed bar = `[0]`) —
  see [backtest engines](../../onboard/10-livetrading/04-backtest-engines.md).
- First `<Chart>` = main chart; `symbol="Same as main chart"` for subcharts.
- `<Range type>`: `oos` (default), `isv`, `notrade`. Commission `Method type`: `None`,
  `PercentageBased`, `PerTrade`, `SizeBased`, `Stockpicker` (exactly one `use="true"`).

## `<Options>` — trading options

Flat `<BuildTradingOptions><Params><Param key="…" className="…">value</Param>…` list; matching is
`className` → TradingOption class, `key` → field; **all options are active at once** (no picker).
Classes: `DontTradeOnWeekends`, `ExitAtEndOfDay` (`EODExitTime`), `ExitOnFriday` (`FridayExitTime`),
`LimitTimeRange` (`SignalTimeRangeFrom/To`, `ExitAtEndOfRange`), `MaxDistanceFromMarket`,
`MaxTradesPerDay`, `MinMaxSLPT`, `UseInitialSLPT`, plus built-ins `SessionOption`, `ReservedBars`,
`StoreChartData`, `RealisticGapsHandling`, `BrokerOption`. There is **no max-open-trades option**.

## `<RiskMoneyManagement>`

```xml
<RiskMoneyManagement>
  <MoneyManagement>
    <InitialCapital>10000</InitialCapital>          <!-- REQUIRED -->
    <Method type="FixedSize" use="true"><Params><Param key="Size" className="FixedSize">0.1</Param></Params></Method>
    <!-- inactive siblings: RiskFixedBalancePct, RiskFixedPctOfAccount, ATRRiskBasedSizing,
         FixedAmount, SimpleMartingaleMM, StocksSizeByPrice, Crypto*, Picker* -->
  </MoneyManagement>
  <RiskManagement maxDrawdown="30"><Method type="AllowAllTrades" use="true"><Params /></Method></RiskManagement>
</RiskMoneyManagement>
```

First `<Method use="true">` wins. Method identity + parameters:
[../strategy-styles.md](../strategy-styles.md#money-management-methods-exact-xml-identity).

## `<Rankings>` — fitness, filters, stop condition

```xml
<Rankings type="never">
  <MaxStrategies>1000</MaxStrategies>               <!-- REQUIRED -->
  <FitnessCriteria method="ComputeFromStrategyResult" useFitnessByIndex="false">
    <Settings><Ranking type="ReturnDDRatio" /></Settings>   <!-- type = databank column class -->
  </FitnessCriteria>
  <ConditionsType>1</ConditionsType>                <!-- 0 ThrowAway | 1 Keep -->
  <Conditions> …see Conditions below… </Conditions>
  <DismissTooSimilarStrategies>true</DismissTooSimilarStrategies>
  <AutomaticDismissal warnings="false"><Problem code="1" dismiss="true" /></AutomaticDismissal>
  <StopCondition type="databank-full" passedStrategies="1000" restartCount="5" days="0" hours="0" minutes="0" />
</Rankings>
```

- `FitnessCriteria@method`: `ComputeFromStrategyResult`, `ComputeFromWFResult`, `ExistingPortfolio`.
- `StopCondition@type`: `never`, `passed-count`, `databank-full`, `time-limit` (days/hours/minutes > 0).
- `AutomaticDismissal` Problem codes: `1` NoTrades, `2` TooLittleTrades, `4` ZeroPLTrades,
  `8` TooShortTrades, `16` ZeroDurationTrades, `32` TooManyOpenTrades, `64` TooLongTrade,
  `256` NoFilledTrades, `512` OutlierTrade, `1024` AmbiguousTrades.
- Per-task extras: Retest/AutomaticRetest add `<DeleteFailedStrategies>`, `<ForceRunCrossChecks>`;
  Build adds `<FitPortfolio>`; Optimize REQUIRES a `<WalkForward>` child (`ThresholdPct`,
  `RobCombRows/Cols`, `RobMinComb`).
- `<Rankings type>` attribute itself is legacy/unread.

## `<Conditions>` — the universal criteria block

Used in Rankings, BuildMode initial-population filters, Filtering, cross-check acceptance,
LogDatabankStats, AutomaticPortfolioBuilder.

```xml
<Condition use="true">
  <Left-Side valueType="column">
    <Column-Value column="ProfitFactor" class="ProfitFactor" direction="0" sampleType="127" plType="10" resultType="main" />
  </Left-Side>
  <Comparator value="&gt;" />
  <Right-Side valueType="numeric"><Numeric-Value value="1.3" /></Right-Side>
</Condition>
```

- `valueType`: `numeric`, `column`, `databankProperty`, `projectProperty`.
- `direction`: `0` both, `1` long, `-1` short. `plType`: `10` money, `20` %, `30` pips, `40/50` open.
- `sampleType`: `127` full, `10` IS, `20` OOS (`21–30` OOS1..10), `40` ISV, `66/77` "every ISV/OOS".
- `resultType`: `main`, `portfolio`, or a cross-check element name (`MonteCarloRetest`,
  `WalkForwardMatrix`, …) to compare cross-check results.
- **Malformed conditions are silently skipped** — a typo in `column` weakens a filter without error.

## `<CrossChecks>` — robustness tests

`<CrossChecks use="true" evaluateAll="true">` with one child per check; the element NAME selects
the plugin (unknown names ignored with a log line). Each child:
`<Xxx use="false"><Settings>…</Settings><AcceptanceSettings><Conditions thresholdPct="80">…</…>`.

| Element | Purpose / key settings |
|---|---|
| `RetestOnAdditionalMarkets` | `<Setups>` (same schema as `<Data>`); acceptance `<Check>all\|markets`, `<MinConditions>`, `<MinMarkets>` |
| `RetestWithHigherPrecision` | `<Precision>`, `<Spread>` |
| `MonteCarloRetest` | `<Methods><Method use type>` from `SQ/MonteCarlo/Retest/*` (`RandomizeHistoryData`, `RandomizeSpread`, `RandomizeStrategyParameters`…), `<NumberOfSimulations>`, `<MCUseFullSample>`, `<MCBacktestPrecision>` |
| `MonteCarloManipulation` | methods from `SQ/MonteCarlo/Manipulation/*` (`RandomizeTradesOrder`, `RandomlySkipTrades`…) |
| `WalkForwardOptimization` | `<WalkForward type period optimization><Param1 value/><Param2 value/>`, `<WhatToParametrize>`, `<MaxTests>` |
| `WalkForwardMatrix` | `<WalkForward>` with `Param1/2` as `start/stop/step`; acceptance `thresholdPct`, `robCombRows/Cols`, `robMinComb` |
| `OptProfileSysParamPermutation` | `<MaxTests>`, `<DistributionUp/Down>`, `<Steps>`, `<WhatToParametrize>` |
| `SequentialOptimization` | `<WhatToParametrize>`, `<ParameterSettings>`; acceptance `<PctToPass>`, `<ResultsCount>`, `<StabilityRange>` |
| `WhatIf` | methods from `SQ/WhatIf/*` (`ExcludePctTradesWithBiggestPl`, `ByDays`…) |

`<WalkForward>` enums: `type` `0` SimIS/SimOOS, `1` SimIS/ExactOOS, `2` Exact/Exact; `period` `10`
percent / `20` days / `30` bars; `optimization` `15` floating / `25` fixed.
`<WhatToParametrize>`: `<Recommended>true</Recommended>` (overrides the rest) or per-flag booleans
(`Periods`, `Shifts`, `Constants`, `EntryParams`, `ExitParamsUsed`…). Each check's `<Settings>` is
a hard requirement.

## `<ATMs>` — advanced trade management

`<ATMs enable="false" scaleOutType="1" sizeDecimals="1" minSize="0.1">` — `enable=false`
short-circuits. `scaleOutType`: `0` DontUse, `1` FromStrategy, `2` FromConfig, `3` Generate.
Requires `<ATM id="global"><Exits/></ATM>`; `<GenerateConfig><Types>` (`SLMultiple`, `PTMultiple`,
`FixedProfit`, `TrailingStop`, `None`) + `<Scenarios>` (`TwoExits`/`ThreeExits` split flags).
ATM overrides all exits except the Stop Loss.

## `<Notes>`

Single element, HTML-escaped text.

## Project conditions (GoToTask / StopAndStart)

```xml
<Conditions>
  <Condition type="ResultsCount">
    <Field type="databank">Results</Field>
    <Field type="comparator">&gt;=</Field>
    <Field type="number">100</Field>
  </Condition>
</Conditions>
```

`type` values: `CyclesCount`, `ResultsCount`, `RunTime`, and (registered with a leading space —
known quirk) `" GoToActivated"`, `" GoToEvaluated"`. `Field@type`: `databank`, `comparator`,
`number`, `duration` (minutes).

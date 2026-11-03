# `Build` task

Generates strategies. Sections: `Data`, `Notes`, `RiskMoneyManagement`, `Rankings`, `Options`,
`CrossChecks`, `Blocks`, `WhatToBuild`, `PartsToImprove`, `ATMs` — the shared ones in
[shared-sections.md](shared-sections.md), the style levers (blocks, MM, templates) in
[../strategy-styles.md](../strategy-styles.md).

Defaults: `internal/plugins/TaskBuild/task_forex.xml` (≈14k lines — the complete block catalog),
`task_futures.xml`, `task_stockpicker.xml`. Real example: `user/projects/Builder/project.cfx` →
`Build-Task1.xml`.

## `<WhatToBuild>` — the strategy skeleton

Hard-required children: `StrategyType`, `MarketSides`, `RulesComplexity`, `BuildMode`, `SLPTOptions`.

```xml
<WhatToBuild>
  <StrategyType type="simple" architecture="sq4" additionalCharts="2"
                templateFile="…" improveType="strategy" strategyFile="…"
                improveDatabank="Strategies to improve" minTrue="60" maxTrue="80" />
  <RulesComplexity useDifferentSettings="false">
    <Chart name="Main chart" minConditions="1" maxConditions="3"
           minExitConditions="1" maxExitConditions="3" minExitTypes="1" maxExitTypes="5"
           minPeriod="5" maxPeriod="200" minShift="1" maxShift="3" />
  </RulesComplexity>
  <MarketSides type="both"><EntrySymmetry>true</EntrySymmetry><ExitSymmetry>true</ExitSymmetry></MarketSides>
  <SLPTOptions>…</SLPTOptions>
  <BuildMode generationType="genetic-evolution">…</BuildMode>
</WhatToBuild>
```

- `StrategyType@type`: `simple`, `multi-tf` (uses `additionalCharts`), `template` (requires
  `templateFile` — a `.sqx`/`.sq4`), `improve` (requires `improveType`: `strategy` → `strategyFile`,
  else `improveDatabank`; enables `<PartsToImprove>`).
- `@architecture`: `sq4` (SQX Signals Style), `sq4fuzzy` (+`minTrue`/`maxTrue`, defaults 60/80),
  `sq3` (old style — indicator+operator blocks).
- `MarketSides@type`: `both`, `long`, `short` (symmetry flags only read when `both`).
- `<SLPTOptions>` element-text children: `SLRequired`, `PTRequired`, `SeparatedSettings`,
  `SLValueType`/`PTValueType` (`pips`), `SLFixedPips`/`SLPercent`/`SLATR`/`SLIndicatorBased`,
  `MinSLInPips`/`MaxSLInPips`, `MinSLInMoney/Percent/ATRMultiple/ATRPeriod` + Max variants, the PT
  mirrors, `LimitSLPTRRR`/`From`/`To`. **When `SeparatedSettings=false`, PT ranges are overwritten
  from SL ranges at load.**

## `<BuildMode>` — random vs genetic

`generationType`: `random-generation` | `genetic-evolution`. Genetic children (defaults):
`PopulationSize` (5), `MaxGenerations` (10), `CrossoverProbability` (50), `MutationProbability` (20),
`Islands` (10; 1–100), `MigrationModulo` (50), `MigrationRate` (20), `InitGenerationType`
(`2` = seed initial population from the `Initial population` databank), `DecimationCoef`,
`FilterInitialPopulation` + `<Conditions>`, `EvoRestartOnFinish`, `EvoRestartOnStagnation`
(element text or `status=`/`generations=`/`fitnessType=` attrs — attribute form wins),
`EvoInSamplePeriod divide= ratio=`, `FreshBlood*`.

## `<Blocks>` — building blocks, order types, exits

```xml
<Blocks type="simple">
  <Calibration useMaxSteps="true" maxSteps="50" />
  <BuildingBlocks>
    <Block key="RSICrossUp" weight="1" use="true" category="signals">
      <Generated weight="1">
        <Param key="#Period#" name="Period" type="int" generation="random"
               minValue="-1000003" maxValue="-1000004" step="1" />
      </Generated>
      <Predefined changed="false"><Params name="Default set 1" weight="1">…</Params></Predefined>
    </Block>
  </BuildingBlocks>
  <OrderTypes><Block key="EnterAtStop" weight="1" use="true" category="orderTypes">…</Block></OrderTypes>
  <ExitTypes>
    <Block key="StopLoss.StopLoss" use="true" probability="100" category="exitTypes" type="formula">
      <Value key="SQ.Formulas.SLPT.FixedValue" use="true">…</Value>
    </Block>
    <Block key="_ExitRule_" use="false" probability="50" category="exitTypes"><Generated weight="1"/></Block>
  </ExitTypes>
  <CustomData showAll="false" />
</Blocks>
```

- `Block@key` = snippet class simple name (`RSICrossUp`) or dotted family
  (`Indicators.RSI`, `Stop/Limit Price Levels.Highest`, `StopLoss.StopLoss`).
- `use` enables; `weight` = selection weight; `probability` (ExitTypes) = % chance.
- `category`: `signals` (pre-combined conditions), `indicators` (+ operator blocks, sq3 style),
  `stopLimitBlocks`, `orderTypes`, `exitTypes`.
- Param `generation`: `random` | `fixed` (+`defaultValue`) | `formula`. Negative sentinels
  `-1000001…-1000020` inherit global ranges (shift, period, SL/PT pips/ATR/%) from
  `RulesComplexity`/`SLPTOptions`.
- Order types (exactly 4): `EnterAtMarket`, `EnterReverseAtMarket`, `EnterAtStop`, `EnterAtLimit`.
- Exit types (8): `StopLoss.StopLoss`, `ProfitTarget.ProfitTarget`, `TrailingStop.TrailingStop`,
  `TrailingStop.TrailingActivation`, `MoveSL2BE.*`, `ExitAfterBars.ExitAfterBars`, `_ExitRule_`
  (exit-on-opposite-signal), `_ExitEOD_` (Stockpicker).

**`ConfigVerifier` hard rules:** ≥1 order type used; ≥1 exit type used (unless EOD/Friday exit is
on); every `type="formula"` exit block needs ≥1 `<Value use="true">`; ≥1 signal or indicator block;
indicator blocks require comparison operator blocks (and vice versa); stop/limit order types
require Price Level blocks.

## `<PartsToImprove>` (only read when `StrategyType@type="improve"`)

```xml
<PartsToImprove improveATM="false">
  <EntryRules symmetry="true"><LongImprovement use="false" action="replace" /><ShortImprovement use="false" action="replace" /></EntryRules>
  <OrderTypes><LongImprovement use="false" /><ShortImprovement use="false" /></OrderTypes>
  <ExitRules symmetry="true"><LongImprovement use="true" action="add-or-replace" /><ShortImprovement use="true" action="add-or-replace" /></ExitRules>
</PartsToImprove>
```

`action`: `add-or-replace`, `replace`, `add`.

## Databank wiring (default)

Two Outputs (`Results`, `Last generation`), two Inputs (`Initial population`,
`Strategies to improve`) — first existing wins per role.

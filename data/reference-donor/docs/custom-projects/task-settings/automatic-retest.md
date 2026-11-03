# `AutomaticRetest` task

Continuously retests strategies as they arrive in a databank (used inside app projects and
watch-style pipelines). Sections: `Databanks`, `CustomData`, `RiskMoneyManagement`, `Options`,
`CrossChecks`, `Rankings`, `ATMs`.

Default template: `internal/plugins/TaskAutomaticRetest/task.xml` (≈264 lines).
Parser for the data override: `AutoRetestSettings` (`SQAppLib/…/backtest/AutoRetestSettings.java`).

## `<CustomData>` — the data override

Note the section plugin is named `AutoRetestData` but **the element is `<CustomData>`**:

```xml
<CustomData>
  <Setups>
    <Setup dateFrom="…" dateTo="…" testPrecision="1" slippage="0" minDist="0" engine="MetaTrader4">
      <Chart symbol="…" timeframe="H1" spread="3" />
      <Commissions>…</Commissions>
      <MainTestValues engine="true" symbol="true" timeframe="true" dates="true" subcharts="true"
                      precision="true" spread="strategy" distance="strategy"
                      commissions="strategy" slippage="strategy" swap="strategy" />
    </Setup>
  </Setups>
</CustomData>
```

`<MainTestValues>` flags mean "take this value from the strategy's main test instead of this
Setup". The `spread/distance/commissions/slippage/swap` attributes are **strings** with default
`"strategy"` (not booleans).

## Custom-settings switches

`<Options customSettings="true|false">` and `<RiskMoneyManagement customSettings="…">` — when
`false`, the strategy's own options/MM are used and the section content is ignored.

`<Rankings>` gains `<DeleteFailedStrategies>` and `<ForceRunCrossChecks>` like Retest.

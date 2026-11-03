# `Optimize` task

Optimizes strategy parameters (simple, walk-forward, walk-forward matrix, sequential). Sections:
`Data`, `Options`, `Notes`, `RiskMoneyManagement`, `Rankings`, `Optimization`, `ATMs` — shared ones
in [shared-sections.md](shared-sections.md).

Default template: `internal/plugins/TaskOptimize/task.xml`. Real example:
`user/projects/Optimizer/project.cfx` → `Optimize-Task1.xml`. Note the default `<Options>` also
contains an `<SLPTOptions>` sibling of `<BuildTradingOptions>`.

## `<Optimization>`

```xml
<Optimization type="1" maxOptimizations="100">
  <Source type="2" relativePath="false"/>                <!-- 1 = strategy file (text = path), 2 = databank -->
  <SimpleOptimization type="10" pctToPass="80" resultsCount="5" stabilityRange="20"/>  <!-- 5 store-all | 10 store-best -->
  <OptimizationMethod settings="automatic" method="…" symmetricVariables="false" symmetryDisabled="false"/>
  <AutomaticSettings distributionUp="30" distributionDown="30" maxSteps="5"/>
  <WhatToParametrize type="0">
    <Recommended>true</Recommended>   <!-- when true, the per-flag booleans below are ignored -->
    <Periods>false</Periods><Shifts>false</Shifts><Constants>false</Constants>
    <EntryParams>false</EntryParams><ExitParamsUsed>false</ExitParamsUsed>…
  </WhatToParametrize>
  <ManualSettings><Params><Param name="…" use="true" …/></Params></ManualSettings>  <!-- settings="manual" -->
  <WalkForward type="1" period="10" optimization="15">
    <Param1 value="20"/><Param2 value="10"/>   <!-- WF matrix (type=3): start/stop/step instead -->
  </WalkForward>
</Optimization>
```

- `Optimization@type`: `1` Simple, `2` WalkForward, `3` MultiWalkForward (matrix), `4` Sequential.
- `<WalkForward>` enums: `type` `0` SimIS/SimOOS, `1` SimIS/ExactOOS, `2` Exact/Exact;
  `period` `10` percent / `20` days / `30` bars; `optimization` `15` floating / `25` fixed.
- `OptimizationMethod@settings`: `automatic` | `manual`; `@method` must be non-empty.

## Hard requirement

**`<Rankings>` must contain a `<WalkForward>` child** (`<Conditions/>`, `<ThresholdPct>`,
`<RobCombRows>`, `<RobCombCols>`, `<RobMinComb>`, `<DontSaveOriginalStr>`) — loading throws
"Walk-Forward Optimization is missing Robustness settings" without it, even for simple optimization.

Default databank wiring: Input = `Strategies to optimize`, Output = `Results`.

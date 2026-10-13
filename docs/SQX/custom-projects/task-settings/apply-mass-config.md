# `ApplyMassConfig` task

Copies chosen settings sections from a `.cfx` template or another task onto multiple target tasks.
Section: `ApplyMassConfig`.

```xml
<Settings>
  <ApplyMassConfig>
    <LoadFrom>
      <Type>file</Type>              <!-- file | task -->
      <File>user/settings/Configs/My.cfx</File>
      <Task>Source Task Name</Task>  <!-- when Type=task -->
    </LoadFrom>
    <WhatToApply>   <!-- all children boolean text, default false -->
      <Data>false</Data><DataTradingEngine>false</DataTradingEngine>
      <DataBacktestData>false</DataBacktestData><DataTestParameters>false</DataTestParameters>
      <DataDataRangeParts>false</DataDataRangeParts>
      <TradingOptions>false</TradingOptions>
      <Blocks>false</Blocks><BlocksSignals>false</BlocksSignals>
      <BlocksIndicators>false</BlocksIndicators><BlocksStopLimitEntry>false</BlocksStopLimitEntry>
      <BlocksOrderTypes>false</BlocksOrderTypes><BlocksExitTypes>false</BlocksExitTypes>
      <Atm>false</Atm><MoneyManagement>true</MoneyManagement>
      <CrossChecks>false</CrossChecks><WhatToBuild>false</WhatToBuild>
      <WhatToRetest>false</WhatToRetest><PartsToImprove>false</PartsToImprove>
      <GeneticOptions>false</GeneticOptions><Optimization>false</Optimization>
      <Ranking>false</Ranking>
    </WhatToApply>
    <TargetTasks>Build strategies,Retest strategies</TargetTasks>  <!-- comma-separated task names, non-empty -->
  </ApplyMassConfig>
</Settings>
```

Default template: `internal/plugins/TaskApplyMassConfig/task.xml`.

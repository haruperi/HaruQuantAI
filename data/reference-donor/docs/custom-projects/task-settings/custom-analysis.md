# `CustomAnalysis` task

Runs custom-analysis snippets over strategies or the whole databank. Sections: `CustomAnalysis`,
`Databanks`.

```xml
<Settings>
  <CustomAnalysis>
    <PerStrategy1>OutlierTrade</PerStrategy1>  <!-- none disables a slot -->
    <PerStrategy2>none</PerStrategy2>
    <FullDatabank1>CorrelationFilter</FullDatabank1>
    <FullDatabank2>none</FullDatabank2>
    <InputArgsPerStrategy1 /><InputArgsPerStrategy2 />
    <InputArgsFullDatabank1 /><InputArgsFullDatabank2 />
    <RemoveFailedStrategies>false</RemoveFailedStrategies>
  </CustomAnalysis>
  <Databanks> ...Input/Output... </Databanks>
</Settings>
```

Method names = snippet classes in `Snippets/SQ/CustomAnalysis/` (`CorrelationFilter`,
`OutlierTrade`, plus any user-added).

Default template: `internal/plugins/TaskCustomAnalysis/task.xml`.

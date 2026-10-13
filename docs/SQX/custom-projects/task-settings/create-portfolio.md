# `CreatePortfolio` task

Merges the input databank's strategies into portfolio(s). Section: `CreatePortfolio` + Input/Output
databank wiring.

```xml
<Settings>
  <CreatePortfolio><MaxStrategies>100</MaxStrategies></CreatePortfolio>
  <Databanks>
    <Databank label="Input databank" name="Input" value="Final" />
    <Databank label="Output databank" name="Output" value="Portfolios" />
  </Databanks>
</Settings>
```

Default template: `internal/plugins/TaskCreatePortfolio/task.xml`.

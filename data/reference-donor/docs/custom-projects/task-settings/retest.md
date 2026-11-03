# `Retest` task

Re-backtests strategies from a databank under different data/settings and filters the results.
Sections: `Data`, `Notes`, `RiskMoneyManagement`, `Rankings`, `Options`, `CrossChecks`,
`Databanks`, `ATMs` — all documented in [shared-sections.md](shared-sections.md).

Default template: `internal/plugins/TaskRetest/task.xml` (≈670 lines — includes all 8 cross-checks
with defaults). Real examples: `user/projects/Retester/project.cfx`, the `Retest-Task*.xml`
entries of any shipped project.

## Typical shape

```xml
<Settings>
  <Databanks>
    <Databank label="Input databank"  name="Input"  value="Results" />
    <Databank label="Output databank" name="Output" value="Final" />
  </Databanks>
  <Data> …new market / timeframe / date range / precision to retest on… </Data>
  <RiskMoneyManagement> … </RiskMoneyManagement>
  <Options> … </Options>
  <Rankings> …acceptance conditions decide what survives into the Output databank… </Rankings>
  <CrossChecks use="true" evaluateAll="true"> …MC / WF / higher precision… </CrossChecks>
  <Notes />
</Settings>
```

## Retest-specific notes

- `<Rankings>` gains `<DeleteFailedStrategies>` (drop strategies that fail conditions instead of
  keeping them unmarked) and `<ForceRunCrossChecks>`.
- `<Databanks retestSelected="true">` + `<SelectedStrategies><Strategy>name</Strategy></…>`
  retests an explicit list instead of the whole Input databank.
- The typical robustness pipeline is several Retest tasks in sequence, each with a different
  purpose: OOS window (`<Data>` date range), other market (`<Data>` symbol), higher precision /
  Monte Carlo (`<CrossChecks>`), final acceptance (`<Rankings>` conditions), writing into
  progressively cleaner databanks.

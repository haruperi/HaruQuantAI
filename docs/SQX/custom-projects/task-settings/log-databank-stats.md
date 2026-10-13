# `LogDatabankStats` task

Writes databank statistics into the project log. Section: `LogDatabankStats`.

```xml
<Settings>
  <LogDatabankStats>
    <Databank>Results</Databank>
    <LogStats type="count">          <!-- sum | avg | count -->
      <Conditions />                 <!-- optional filter -->
      <Column column="NetProfit" />  <!-- required for sum/avg -->
    </LogStats>
  </LogDatabankStats>
  <Databanks>
    <Databank label="Source databank" name="Source" value="Results" />
  </Databanks>
</Settings>
```

Default template: `internal/plugins/TaskLogDatabankStats/task.xml`.

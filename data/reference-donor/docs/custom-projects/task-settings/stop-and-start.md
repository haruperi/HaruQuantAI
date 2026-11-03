# `StopAndStart` task

Stops this project (optionally starting another) when conditions hold. Section: `StopAndStart`.

```xml
<Settings>
  <StopAndStart>
    <Conditions> ...project conditions, same schema as GoToTask... </Conditions>
    <StartProject use="true" skipToFirstProject="false">Another Project</StartProject>
  </StopAndStart>
</Settings>
```

Default template: `internal/plugins/TaskStopAndStart/task.xml`.

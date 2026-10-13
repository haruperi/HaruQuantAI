# `WaitFor` task

Pauses the pipeline until the user confirms or a file appears. Section: `WaitFor`.

```xml
<Settings>
  <WaitFor>
    <Action>user</Action>   <!-- user (default) | file -->
    <File>C:/path/trigger.txt</File>
  </WaitFor>
</Settings>
```

Default template: `internal/plugins/TaskWaitFor/task.xml`.

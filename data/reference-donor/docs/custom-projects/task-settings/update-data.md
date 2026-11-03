# `UpdateData` task

Refreshes market data before/inside a pipeline. Section: `UpdateData`.

```xml
<Settings>
  <UpdateData><Type>project</Type></UpdateData>
  <!-- project = symbols from the task's <Resources>; anything else = all downloadable data -->
</Settings>
```

Default template: `internal/plugins/TaskUpdateData/task.xml`.

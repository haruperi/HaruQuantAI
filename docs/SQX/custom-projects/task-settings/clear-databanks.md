# `ClearDatabanks` task

Empties databanks — the usual first task of a looped pipeline. Section: `ClearDatabanks`.

```xml
<Settings>
  <ClearDatabanks>
    <Databank name="Results" />
    <Databank name="Last generation" />
  </ClearDatabanks>
</Settings>
```

- `<Databank name>` is repeatable and names project databanks DIRECTLY (no Input/Output roles).
- `name="all"` clears every databank in the project.

Default template: `internal/plugins/TaskClearDatabanks/task.xml`.

# `GoToTask` task

Jumps back to an earlier task when conditions hold — the loop primitive. Section: `GoToTask`.

```xml
<Settings>
  <GoToTask task="Build strategies" resetEvaluatedCycles="false" resetActivatedCycles="false">
    <Task />
    <Conditions>
      <Condition type="ResultsCount">
        <Field type="databank">Final</Field>
        <Field type="comparator">&lt;</Field>
        <Field type="number">100</Field>
      </Condition>
    </Conditions>
  </GoToTask>
  <Databanks />
</Settings>
```

- `task="…"` must equal an existing task's **`name`** (not `title`) and that task must be
  `active="true"` — both validated at load.
- Empty `<Conditions>` = always jump. Condition schema:
  [shared-sections.md](shared-sections.md#project-conditions-gototask--stopandstart).
- A GoToTask anywhere in the run range makes SQX eagerly load ALL task settings at start.

Default template: `internal/plugins/TaskGoToTask/task.xml`.

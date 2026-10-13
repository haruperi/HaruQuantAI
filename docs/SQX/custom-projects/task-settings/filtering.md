# `Filtering` task

Deletes / copies / moves strategies between databanks based on conditions. Section: `Filtering`
+ `<Databanks>` with roles `Source` and `Target`.

```xml
<Settings>
  <Filtering>
    <ActionType>0</ActionType>        <!-- 0 Delete | 1 Copy | 2 Move -->
    <ConditionsType>0</ConditionsType><!-- 0 ThrowAway | 1 Keep -->
    <MaxStrategies>0</MaxStrategies>
    <Conditions> ...universal Condition blocks... </Conditions>
  </Filtering>
  <Databanks>
    <Databank label="Source databank" name="Source" value="Results" />
    <Databank label="Target databank" name="Target" value="Final" />
  </Databanks>
</Settings>
```

- Target databank is required for Copy/Move (ActionType 1/2), ignored for Delete.
- `<Conditions>` schema: [shared-sections.md](shared-sections.md#conditions--the-universal-criteria-block).

Default template: `internal/plugins/TaskFiltering/task.xml`.

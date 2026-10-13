# `LoadFromFiles` task

Imports strategy files from a directory into the output databank. Section: `LoadFromFiles`.

```xml
<Settings>
  <LoadFromFiles>
    <SourceDirectory>C:/in/strategies</SourceDirectory>
    <IncludeSubdirectories>false</IncludeSubdirectories>
    <UnrecognizedInstrumentAction>0</UnrecognizedInstrumentAction> <!-- 1 => value required -->
    <UnrecognizedInstrumentValue />
  </LoadFromFiles>
</Settings>
```

Default template: `internal/plugins/TaskLoadFromFiles/task.xml`.

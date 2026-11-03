# `CallExternalScript` task

Runs an external program/script mid-pipeline. Section: `CallExternalScript`.

```xml
<Settings>
  <CallExternalScript>
    <File params="--arg1 x">C:/path/to/script.bat</File>
    <WaitFor hours="0" minutes="30">time</WaitFor>   <!-- time (uses hours/minutes) | finish -->
  </CallExternalScript>
</Settings>
```

Default template: `internal/plugins/TaskCallExternalScript/task.xml`.

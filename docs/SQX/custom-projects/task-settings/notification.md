# `Notification` task

Sends an email or shows a popup. Section: `Notification`.

```xml
<Settings>
  <Notification>
    <Type>email</Type>       <!-- email | popup -->
    <Email>you@example.com</Email>
    <Wait>false</Wait>
  </Notification>
</Settings>
```

Default template: `internal/plugins/TaskNotification/task.xml`.

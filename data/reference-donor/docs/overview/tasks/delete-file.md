# Delete file task

> Delete a file at a specified path during the workflow.

## What it does

The Delete file task deletes a file at a specified path. It is used in conjunction with the
[Wait for](wait-for.md) task and with [calling external scripts](call-external-script.md) — for
example, to clean up the signal file that Wait for watches so the mechanism can be reused on the next
loop iteration.

## Options

The source describes the task's purpose rather than a fixed option list. Functionally, you configure
the **path of the file to delete**. Refer to the in-app settings tabs for the exact controls.

## Typical use in a workflow

Place it after a [Wait for](wait-for.md) resumes to remove the signal file the external program
created, so a later iteration starts clean.

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- Sibling tasks: [Wait for](wait-for.md), [Call external script](call-external-script.md)

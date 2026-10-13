# Call external script task

> Pause the project and run an external script or program as a step.

## What it does

The Call external script task pauses the custom project and calls an external script or program. It
lets you hand processing off to an external program and then return to running the custom project's
tasks once that program is done.

## Options

The source describes the task's purpose rather than a fixed option list. Functionally, you configure
the **external script or program** to call. Refer to the in-app settings tabs for the exact controls.

## Typical use in a workflow

Use it to delegate a step to an outside tool, then combine with a [Wait for](wait-for.md) task so the
pipeline resumes when the external program signals completion (for example, by creating a file that
Wait for watches).

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- Sibling tasks: [Wait for](wait-for.md), [Delete file](delete-file.md)

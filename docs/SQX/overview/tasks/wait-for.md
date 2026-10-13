# Wait for task

> Pause the project until the user resumes it or a file appears.

## What it does

The Wait for task pauses the project until either the user unpauses it, or a file appears at a
specific path. It is designed for use alongside external programs: you pause the custom project while
one or more external programs do their work, and when they finish they produce an empty file that
signals the project to resume.

## Options

The source describes two ways the pause ends:

- **Wait for the user** — the project stays paused until the user manually resumes it.
- **Wait for a file** — the project resumes when a file appears at a specified path.

## Typical use in a workflow

Insert it after handing work off to an external tool (see [Call external script](call-external-script.md))
so the pipeline pauses until that tool signals completion by creating the watched file.

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- Sibling tasks: [Call external script](call-external-script.md), [Delete file](delete-file.md), [Notification](notification.md)

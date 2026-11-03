# Stop & Start task

> Stop the project when a condition is met, and optionally start another project.

## What it does

The Stop & Start task can stop project execution when one or more conditions are fulfilled. It is
often used inside a loop — for example, to stop the project once enough strategies have been
generated, or after a given amount of time.

After stopping a project, it can start another custom project. This lets you chain custom projects so
they run consecutively, one after another.

## Options

The source describes behavior rather than a fixed option list. Functionally you configure:

- The **stop condition(s)** — for example, a target strategy count or an elapsed-time limit.
- Optionally, the **next custom project** to start once this one stops.

Refer to the in-app settings tabs for the exact condition controls.

## Typical use in a workflow

Combine with a [Go To Task](go-to.md) loop to end a run once a target is reached, then hand off to
the next project in a chain.

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- Sibling tasks: [Go To Task](go-to.md), [Notification](notification.md)

# Go To Task

> Jump to another task in the flow — the mechanism behind loops and conditions.

## What it does

The Go To Task enables creating loops in your task workflow. It skips execution to another task —
optionally only when certain conditions are not true. For example, when there are not enough
strategies in the final databank, it can skip back to the beginning and run the custom project one
more time.

## Options

The source describes the task's behavior rather than a fixed option list. Functionally you configure:

- The **target task** to jump to.
- Optionally, the **condition(s)** under which the jump happens (for example, a databank holding
  fewer strategies than a target count).

Refer to the in-app settings tabs for the exact condition controls.

## Typical use in a workflow

Placed at the end of a pipeline to loop back to an earlier task (such as Build) and repeat the run
until a databank reaches a desired size, then fall through to the remaining tasks.

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- [Databank & results](../results-databank.md)
- Sibling tasks: [Stop & Start](stop-and-start.md), [Wait for](wait-for.md)

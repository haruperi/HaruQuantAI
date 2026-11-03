# Clear databanks task

> Empty one or more databanks so a run starts from a clean slate.

## What it does

The Clear databanks task removes all strategies from one or more of the project's
[databanks](../results-databank.md). It is typically the first task in a pipeline, ensuring that a
new run does not mix its results with strategies left over from a previous run.

> Note: the source documentation for this task is empty, so this page describes only what the task
> name and pipeline context establish. The specific in-app controls are not documented here to avoid
> fabricating them.

## Options

The source page provides no documented option list. Functionally, the task's purpose is to select
which databank(s) to empty before the rest of the pipeline runs. Refer to the in-app settings tabs
for the exact controls.

## Typical use in a workflow

Placed at the very start of a project so each run begins with empty databanks, or inside a
[loop](go-to.md) to reset intermediate databanks between iterations.

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- [Databank & results](../results-databank.md)
- Sibling tasks: [Log databank](log-databank.md), [Filter strategies](filter-strategies.md)

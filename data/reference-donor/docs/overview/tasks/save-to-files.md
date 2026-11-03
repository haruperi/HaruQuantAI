# Save to files task

> Save strategies from a databank to files on disk.

## What it does

The Save to files task is the counterpart of [Load from files](load-from-files.md): it writes
strategies from a [databank](../results-databank.md) out to files in a folder, so they persist
outside the project and can be reloaded, archived, or shared.

> Note: the source documentation for this task was not available, so this page describes only what
> the task name and its relationship to Load from files establish. The specific in-app controls are
> not documented here to avoid fabricating them.

## Options

No option list is documented in the source. Functionally, the task saves the contents of a chosen
databank to a chosen destination folder. Refer to the in-app settings tabs for the exact controls.

## Typical use in a workflow

Place it at the end of a pipeline to export the final databank of surviving strategies to files, or
mid-pipeline to snapshot intermediate results for later reloading with
[Load from files](load-from-files.md).

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- [Databank & results](../results-databank.md)
- Sibling task: [Load from files](load-from-files.md)

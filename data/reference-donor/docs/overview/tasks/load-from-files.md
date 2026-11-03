# Load from files task

> Load strategies from files in a folder into a databank.

## What it does

The Load from files task loads strategies from files in a given folder and places them into a
specified [databank](../results-databank.md), making them available to subsequent tasks in the
pipeline.

## Options

The source is brief and documents only the task's core behavior. Functionally, you configure:

- The **source folder** to read strategy files from.
- The **target databank** the loaded strategies are placed into.

No further controls are documented in the source; refer to the in-app settings tabs for details.

## Typical use in a workflow

Use it at the start of a project to feed previously saved strategies into the pipeline for retesting,
filtering, or portfolio construction — the counterpart of [Save to files](save-to-files.md).

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- [Databank & results](../results-databank.md)
- Sibling task: [Save to files](save-to-files.md)

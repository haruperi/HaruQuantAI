# Update data task

> Download the most recent missing history before continuing the pipeline.

## What it does

The Update data task updates market data by downloading the missing most recent days. It ensures the
strategies produced later in the pipeline are built and tested against up-to-date history.

## Options

According to the source, the task can update data at two scopes:

- **Project data only** — update just the data used somewhere in the project (in any project task).
- **All data** — update every data set, not only what the project uses.

## Typical use in a workflow

Place it near the start of a project (or before a rebuild in a [loop](go-to.md)) so each run works
against freshly downloaded history from the [Data Manager](../data-manager.md).

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- [Data Manager](../data-manager.md)
- Sibling tasks: [Load from files](load-from-files.md), [Save to files](save-to-files.md)

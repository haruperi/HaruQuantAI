# Log databank task

> Write chosen databank statistics to the project's running log.

## What it does

The Log databank task saves statistics you choose about a [databank](../results-databank.md) to the
project's running log. This lets you track how a databank evolves as the pipeline runs — for
example, the average Net profit of all strategies in the databank, or the number of strategies whose
Net profit is greater than zero.

## Options

The source describes the task's purpose rather than a fixed option list. In practice you configure
**which databank** to inspect and **which statistic(s)** to log (for example, average Net profit
across all strategies, or a count of strategies passing a threshold such as Net profit > 0). Refer
to the in-app settings tabs for the exact set of loggable stats.

## Typical use in a workflow

Insert after a build/retest step, or inside a [loop](go-to.md), to record how a databank changes
over iterations so you can review progress in the project log.

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- [Databank & results](../results-databank.md)
- Sibling tasks: [Clear databanks](clear-databanks.md), [Filter strategies](filter-strategies.md)

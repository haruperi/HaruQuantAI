# Filter strategies task

> Deletes, copies or moves strategies from one databank to another — optionally only those that meet a condition.

## What it does

The Filter strategies task is a databank-management step. It can **delete**, **copy** or **move** strategies between databanks. You can optionally attach a **filter** so the operation applies only to the strategies that satisfy specific conditions (for example, only strategies above a Net-profit or robustness threshold).

Unlike Build, Optimize or Retest, this task does not generate or re-run any backtests — it simply moves strategies around and prunes databanks based on their stored results. That makes it fast and ideal for shaping the contents of a databank between heavier processing steps.

## Settings tabs it uses

- **Operation** — choose delete / copy / move, and the source and target databanks.
- **Filter / condition** (optional) — the condition that a strategy must meet for the operation to apply to it. Conditions are built from the strategy's stored databank columns and metrics; see [Results & databank](../results-databank.md).

This task does not use the shared Data / Trading options / Money management tabs, because it does not re-test strategies.

## How it fits in a workflow

Filter reads from a **source databank** and writes into a **target databank** (or prunes in place when deleting). In a [Custom Project](../custom-projects.md) pipeline it is the "plumbing" between engines: build into databank A, filter the promising strategies into databank B, retest B into C, filter again, then create a portfolio. It is the standard way to separate winners from losers and keep each databank focused before the next task runs.

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Results & databank](../results-databank.md)
- [Settings tabs reference](../settings/README.md)
- [Tasks reference](README.md)

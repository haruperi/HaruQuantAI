# Tasks — Detailed Reference

A **task** is one action in a [Custom Project](../custom-projects.md) pipeline. This folder has one
leaf page per task type: **what it does**, **its settings tabs**, and **how it fits in a workflow**.

Remember: the standalone **Builder / Optimizer / Retester** are just single-task projects wrapping the
*Build / Optimize / Retest strategies* tasks — so those task pages double as the reference for the
standalone modules.

Parent: [Custom Projects & the task model](../custom-projects.md) · [Overview index](../README.md)

## Strategy tasks (produce or process strategies)

| Task | What it does | Page |
|------|--------------|------|
| **Build strategies** | Generate new strategies (random / genetic) and backtest them — the Builder | [build-strategies.md](build-strategies.md) |
| **Optimize strategies** | Tune a strategy's parameters; simple / walk-forward / WF matrix / sequential — the Optimizer | [optimize-strategies.md](optimize-strategies.md) |
| **Retest strategies** | Re-test strategies for robustness (cross-checks, Monte Carlo) — the Retester | [retest-strategies.md](retest-strategies.md) |
| **Filter strategies** | Copy/move/delete strategies between databanks, optionally by condition | [filter-strategies.md](filter-strategies.md) |
| **Create portfolio** | Combine selected strategies into a portfolio | [create-portfolio.md](create-portfolio.md) |

## Databank & data tasks

| Task | What it does | Page |
|------|--------------|------|
| **Clear databanks** | Empty one or more databanks at the start of a run | [clear-databanks.md](clear-databanks.md) |
| **Log databank** | Write databank contents/stats to the log | [log-databank.md](log-databank.md) |
| **Update data** | Download the latest history before continuing | [update-data.md](update-data.md) |
| **Load from files** | Load strategies from files into a databank | [load-from-files.md](load-from-files.md) |
| **Save to files** | Save strategies from a databank to files | [save-to-files.md](save-to-files.md) |

## Flow & utility tasks

| Task | What it does | Page |
|------|--------------|------|
| **Go To Task** | Jump to another task, optionally on a condition — enables loops | [go-to.md](go-to.md) |
| **Wait for** | Pause until a user action, a file, or a time | [wait-for.md](wait-for.md) |
| **Stop & Start** | Stop and restart the engine / a connection | [stop-and-start.md](stop-and-start.md) |
| **Notification** | Send a notification (e.g. email) about progress | [notification.md](notification.md) |
| **Call external script** | Run an external script/program as a step | [call-external-script.md](call-external-script.md) |
| **Delete file** | Delete a file during the workflow | [delete-file.md](delete-file.md) |

## Settings tabs are per task

Each task exposes a set of **settings tabs** — some shared across tasks, some specific to the task.
See the [settings tabs reference](../settings/README.md) for the shared-vs-specific map.

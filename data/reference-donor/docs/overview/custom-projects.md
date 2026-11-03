# Custom Projects and the Task Model

A project is a pipeline of tasks, each task has its own settings tabs, and Builder / Optimizer /
Retester are single-task projects. Object tree (App -> Projects -> Tasks -> Settings):
[object-model.md](object-model.md).

## Model

A Custom Project is a user-defined workflow: tasks run one after another in the order arranged on
the task-flow (left side of the project); each task is one action (build, retest, filter a
databank, update data, notify, ...). Projects read/write strategies through Databanks and can
loop, so they run unattended for hours or days and leave a final databank of strategies that
passed every step.

- A Go To Task jumps back to loop, with conditions (e.g. Final databank below 100 strategies -> back to Build; repeat until it is full).
- Settings tabs are shared by many task types (Data, Trading options, Money management, ATM, Notes) or task-specific (What to build: Build only; optimization ranges: Optimize only; Cross-checks: Build/Retest). Map: [settings/](settings/README.md).
- Databanks are the shared storage: unlimited per project; each task has a source databank (read) and a target databank (write), so databanks filter strategies down the pipeline. See [results-databank.md](results-databank.md).
- Example chain: clear databanks -> build 1000 strategies -> retest on market A -> retest on market B -> WF Matrix on the rest -> store survivors in a Final databank. Generation, validation, optimization and portfolio construction run unattended; only the final result needs review.
- Example forex and futures custom projects ship on the Getting Started page.

## Builder, Optimizer, Retester are single-task projects

The main-menu Builder, Optimizer and Retester are shortcuts to a project with exactly one task
(Build strategies, Optimize strategies, Retest strategies) and expose the same Progress / Full
settings / Results interface a task has inside a custom project. The standalone Builder, the Build
strategies task and a Build step in a custom project are the same task with the same settings tabs.

## Task types

Detail: [tasks/](tasks/README.md).

- Strategy: [Build strategies](tasks/build-strategies.md), [Optimize strategies](tasks/optimize-strategies.md), [Retest strategies](tasks/retest-strategies.md), [Filter strategies](tasks/filter-strategies.md), [Create portfolio](tasks/create-portfolio.md).
- Databank / data: [Clear databanks](tasks/clear-databanks.md), [Log databank](tasks/log-databank.md), [Update data](tasks/update-data.md), [Load from files](tasks/load-from-files.md), [Save to files](tasks/save-to-files.md).
- Flow / utility: [Go To Task](tasks/go-to.md), [Wait for](tasks/wait-for.md), [Stop and Start](tasks/stop-and-start.md), [Notification](tasks/notification.md), [Call external script](tasks/call-external-script.md), [Delete file](tasks/delete-file.md).

## Relations

[Builder](builder.md), [Optimizer](optimizer.md), [Retester](retester.md),
[Portfolio Master](portfolio-master.md), [Portfolio Composer](portfolio-composer.md) all appear as
tasks; the [Databank](results-databank.md) is the medium between tasks; the
[Data Manager](data-manager.md) supplies the data an Update data task refreshes mid-pipeline.
Developer view: [../onboard/11-misc/02-taskmanager.md](../onboard/11-misc/02-taskmanager.md).

## Typical workflow

1. New Custom Project from the left menu (or open an example project).
2. Add databanks (e.g. `Build`, `Retest 1`, `Final`).
3. Drag tasks onto the flow in order; set each task's source/target databank and settings tabs.
4. Optionally end with a Go To Task looping until a databank reaches a target count.
5. Run, watch the shared Progress view, collect survivors from the Final databank.

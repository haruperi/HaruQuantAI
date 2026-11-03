# The SQX Object Model — App → Projects → Tasks → Settings

> How StrategyQuant X is structured **as objects**, independent of how the UI displays it.
> Related: [custom-projects.md](custom-projects.md) (the pipeline model) ·
> [settings tabs](settings/README.md) · [results tabs](results-tabs/README.md) ·
> test-side mapping: [docs/ui/OOP-MODEL.md](../ui/OOP-MODEL.md)

## The tree

```
App (SQX)
└── Projects <Project[]>                    ← ALL projects are equal peers
    └── Project                              (e.g. "Builder", "GOLD H1 CFD - Dukascopy")
        ├── Tasks <Task[]>                   ← ordered pipeline (config.xml)
        │   └── Task                         has a TYPE: Build / Retest / Optimize /
        │       │                            AutomaticRetest / … / ClearDatabanks / GoToTask
        │       └── Settings                 ← the task's own settings (its XML)
        │           └── SettingsTab[]        ← tabs, determined by the task TYPE
        │               (What to build · Genetic options · Data · Trading options ·
        │                Money management · Ranking · Cross checks · …)
        ├── Databanks <Databank[]>           ← shared strategy STORAGE (unlimited per project);
        │                                      each task reads a SOURCE and writes a TARGET databank
        ├── Progress                         ← project CONTROL: Start/Stop/Pause, flow log
        └── Results                          ← result VIEW: result tabs over the Databanks
```

Four separations to keep straight:

- **Settings** belong to a **Task** (each task type brings its own tab set).
- **Databanks** belong to the **Project** — the storage the tasks read from / write to; which
  databank a task uses is part of that task's *Settings* (source → target). See
  [results-databank.md](results-databank.md).
- **Progress** belongs to the **Project** — it controls the run of the whole pipeline.
- **Results** are their own view (result tabs over the project's databanks) — not settings.

## The main menu is a VIEW, not the model

The left navigation shows **Builder / Retester / Optimizer** as top-level entries and hides the
rest under **Custom projects**. That is *presentation only*. In the object model they are all just
projects; Builder / Retester / Optimizer are projects containing **exactly one task** of the
corresponding type (Build / Retest / Optimize) — see
[custom-projects.md](custom-projects.md#builder-optimizer-retester-are-single-task-projects).

The filesystem shows this directly — `user/projects/` holds them side by side:

```
user/projects/
├── Builder/                          ← the main-menu "Builder" is just this project
├── Retester/
├── Optimizer/
├── PortfolioMaster/
├── GOLD H1 CFD - Dukascopy/          ← a user's custom project — an equal peer
└── …
```

## On disk

Each project folder contains:

```
user/projects/<Project name>/
├── project.cfx          ← ZIP archive:
│   ├── config.xml            the project = its ordered task list
│   ├── Build-Task1.xml       one XML per task — the task's SETTINGS
│   ├── Retest-Task2.xml
│   ├── …
│   ├── ClearDatabanks-Task8.xml
│   └── GoToTask-Task9.xml
└── databanks/           ← the project's Databanks (e.g. Results, Initial population,
                           Last generation, Final strategies, Existing portfolio)
```

So the tree above is literally the persistence format: *project = config.xml + one settings XML
per task; results live next to it in databanks.*

## Settings tabs are shared components

A settings tab (e.g. **Money management**) is one UI component rendered for every task type that
declares it — the standalone Builder, the Retester, and a Retest task inside a custom project all
show the *same* Money management tab. Which task types have which tab is the `availableIn` fact
recorded per entry in the UI-action catalog (`docs/ui/00-shared/settings/catalog.jsonl`); the
shared-vs-specific map is in [settings/README.md](settings/README.md).

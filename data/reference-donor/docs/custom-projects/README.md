# Custom projects — configuration reference

The **complete, code-derived reference** for assembling StrategyQuant X projects by hand or by AI:
the `.cfx` container, the `config.xml` project model, every task type's settings XML, and the
levers that shape a generated strategy's style. Everything here was generated from the Java
sources (class and line references included), not from the UI.

The conceptual overview lives at [`../overview/custom-projects.md`](../overview/custom-projects.md)
— read that first if you don't know what a custom project *is*. This folder is the reference you
consult while **writing** configurations.

| Page | Contents |
|------|----------|
| [cfx-format.md](cfx-format.md) | The `.cfx` container: zip anatomy, the two flavours (project vs. task template), entry naming, versioning, read/write code paths, gotchas. |
| [project-config.md](project-config.md) | `config.xml`: the `<Project>` / `<Task>` / `<Databank>` grammar, task ordering, databank wiring roles, GoToTask control flow, how projects are created programmatically, servlet/MCP surface. |
| [task-settings/](task-settings/README.md) | Per-task-type settings XML reference — one page per task type (Build, Retest, Optimize, GoToTask, …) plus [shared-sections.md](task-settings/shared-sections.md) for Data / Options / MM / Rankings / Conditions / CrossChecks / ATMs. |
| [strategy-styles.md](strategy-styles.md) | Translating strategy-style intents (martingale, mean reversion, trend, breakout…) into Builder settings: money management methods, building blocks, templates, trading options. |
| [building-blocks-locations.md](building-blocks-locations.md) | Where building blocks live: the Snippets catalog (built-ins), the Build task's `<Blocks>` selection, and AlgoWizard custom blocks in `user/settings/customBlocks.xml` (+ blockGroups.xml, customDataIndys.xml) — and how they meet. |

## Who uses this

- **SQAI chat + Claude Code** — the `strategy-architect` AI plugin
  (`user/extend/AIPlugins/strategy-architect/`) reads these pages before assembling any
  configuration. The pages are written to be consumed by an AI: exact element names, exact
  attribute values, minimal prose.
- **Developers** — as the ground truth for the config file formats, with pointers back into the
  Java sources.

## The three ways to change a project's configuration

| Path | Tool / API | Scope | Notes |
|------|-----------|-------|-------|
| Task settings of an existing project | `set_task_config(name, taskFile, xml)` | one task | The only safe way while SQX runs — updates the in-memory project too. Refused while running. |
| Task template `.cfx` | `apply_config_file(name, file, action)` | **task #1 only** | save/load a single-task template (`<Task>` root). Not a project snapshot. |
| Whole project `.cfx` | write the zip + import with the `open_project` MCP tool | whole project | `ProjectEngine` caches projects at startup — a `.cfx` dropped on disk is invisible until imported. `open_project(file, projectName?)` copies it to `user/projects/<name>/project.cfx` and registers it live (no restart; name auto-suffixed on collision). |

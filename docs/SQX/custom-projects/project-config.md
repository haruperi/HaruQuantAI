# `config.xml` - the project model

Parser: `SQProject.initTasksFromConfig`, `Databanks.loadFromConfig`.

```xml
<Project name="..." version="145.3039">
  <Tasks>
    <Task type="..." name="..." taskXMLFile="..." active="true" [title="..."] ... />
  </Tasks>
  <Resources> ... </Resources>          <!-- OPTIONAL and write-only: never read on load -->
  <Databanks>
    <Databank name="..." view="..." syncType="..." position="..." />
  </Databanks>
</Project>
```

## `<Project>` attributes

| Attr | Required | Rules |
|---|---|---|
| `name` | yes | Rewritten to the folder name on save: the directory under `user/projects/` IS the identity. Non-empty, no leading `.`, none of `\/:*?"<>|`, no reserved Windows device names, no whitespace other than plain space. |
| `version` | effectively yes | `<major>.<build>`; omitted = treated as pre-136, everything rewritten. |

## `<Task>` attributes

`<Task>` elements are empty; settings live in the referenced zip entry. Document order inside
`<Tasks>` = execution order.

| Attr | Required | Semantics |
|---|---|---|
| `type` | yes | Task plugin id ([task-settings/README.md](task-settings/README.md)). Unknown => "Task '%s' does not exist." |
| `name` | yes | Identity, unique in the project; used by GoToTask `task="..."`, moveTask, removeTask, CLI task selection. `title` is only cosmetics. |
| `taskXMLFile` | yes | Zip entry holding this task's `<Settings>`. |
| `active` | no (`true`) | Inactive tasks are skipped at run time; GoToTask targets must be active. |
| `title` | no | Display label (logs/UI). |
| `showSettingsOverview`, `sampleName`, `templateFile`, `version` | no | UI/informational. `sampleName` is recomputed for Build tasks on save ("Custom" when settings deviate from a simple template). |

## `<Databank>` (project level)

| Attr | Required | Values |
|---|---|---|
| `name` | yes | Subfolder under `databanks/`. |
| `view` | no | `Default - Main data` (default; unknown names self-heal to it), `Default - Portfolio`, ... |
| `syncType` | no | Exact strings: `Auto-sync never` (default), `Immediately (not recommended, very slow)`, `Auto-sync every 10 minutes` / `20 minutes` / `30 minutes` / `every 1 hour` / `every 2 hours` / `every 4 hours`. |
| `position` | no | Integer UI sort order. |

Well-known names (`SQConst`): `Results`, `Initial population`, `Strategies to improve`,
`Strategies to optimize`, `Last generation`, `Existing portfolio`, `Simple strategies`, `Portfolios`.
Self-healing on load (`SQProject.updateProjectDatabanks`): duplicates dropped, databanks referenced
by a task's default template added, `Results` always ensured. Declare the databanks your tasks bind
to; SQX tops up the rest.

## Databank wiring between tasks / `<Settings>/<Databanks>`

Inside each task's settings entry:

```xml
<Databanks [retestSelected="false"]>
  <Databank label="Input databank"  name="Input"  value="Results" />
  <Databank label="Output databank" name="Output" value="Final" />
</Databanks>
```

- `name` = role (`Input`, `Output`, `Source`, `Target`), `value` = project-level databank name, `label` = UI only.
- Output: role `Output`, then `Target`; neither => falls back to `Results` AND injects the binding. Input: `Input`, then `Source`; no fallback, missing input is a run-time error.
- Several entries with one role are legal; the first whose `value` exists wins (Build declares two Outputs and two Inputs by default).
- `retestSelected="true"` switches to the explicit `<SelectedStrategies><Strategy .../></SelectedStrategies>` list.
- `ClearDatabanks` names databanks directly: `<ClearDatabanks><Databank name="Results"/></ClearDatabanks>`.

## Control flow - `GoToTask`

```xml
<Settings>
  <GoToTask task="Build strategies" [resetEvaluatedCycles="false"] [resetActivatedCycles="false"]>
    <Task /><Conditions />
  </GoToTask>
  <Databanks />
</Settings>
```

`task` = an existing task's `name`, which must be `active="true"`. With a GoToTask present SQX
eagerly loads all task settings at start (reachability unknown).

## Creating a project

- Live, `TaskManager/Projects` servlet: `createProject(projectName)` (zero tasks, `Results` databank), `addTask(projectName, taskName, taskType[, index])` (seeds the default `task_forex.xml` settings), then `set_task_config` per task. Also `openProject(file[, projectName])`, `saveProject` (export a `.cfx`), `moveTask`/`renameTask`/`cloneTask`/`activateTask`/`removeTask`.
- On disk: write the `.cfx` ([cfx-format.md](cfx-format.md)) and import with `open_project` (table below); `ProjectEngine` scans `user/projects` only at startup.
- Reserved app projects (cannot be removed, single fixed task): `Builder`, `Optimizer`, `Retester`, `PortfolioMaster`, `PortfolioComposer`. Custom projects need a Pro license to run.
- Default task settings: `internal/plugins/Task<Name>/task.xml` (Build: `task_forex.xml` / `task_futures.xml` / `task_stockpicker.xml`), root `<Task><Settings>...`, the starting point for any hand-written entry.
- Project-level `<Resources>` is never read, task-level `<Resources>` is regenerated on save: write both empty or omit.

## Servlet/MCP surface

| MCP tool | Servlet | Behaviour |
|---|---|---|
| `get_project_config(name)` | `Project -> getConfig` | `{config: {name, xml: "<Project>...", tasks: {"Build-Task1.xml": "<Settings>...", ...}}}`; task keys = `taskXMLFile` values in `config.xml` order. |
| `set_task_config(name, taskFile, xml)` | `Project -> updateTaskXML` | Full replacement of the task's `<Settings>` (whole document); regenerates `<Resources>`; refused while the project runs. |
| `apply_config_file(name, file, action)` | `Project -> saveConfig/loadConfig` | Task-template flavour, task #1 only; load checks the template `type`. |
| `open_project(file, projectName?)` | `Projects -> openProject` | Copies the `.cfx` to `user/projects/<name>/project.cfx`, registers immediately (no restart), auto-suffixes the name on collision. |
| `run_project` / `stop_project` / `get_project_status` / `wait_for_project` | `Project -> start/stop/status` | `run_project` modes `from-first`, `from-here`, `this-task-only`. |

## Minimal valid `config.xml`

```xml
<Project name="My Project" version="145.3039">
  <Tasks />
  <Databanks>
    <Databank name="Results" view="Default - Main data" syncType="Auto-sync never" position="10" />
  </Databanks>
</Project>
```

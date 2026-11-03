# The `.cfx` container

Plain ZIP (DEFLATE, UTF-8 entry names, flat: no directories, manifest, `META-INF` or version
file). Reader/writer: `SQFileManager`
(`projects/libs/SQAppLib/src/com/strategyquant/tradinglib/file/SQFileManager.java`). Two
flavours share the extension and the `config.xml` entry name; check the root element.

## Flavour A - project archive (`user/projects/<name>/project.cfx`)

| Zip entry | Content |
|---|---|
| `config.xml` | root `<Project>`: task list, databank list, optional (inert) resources |
| `<TaskType>-Task<N>.xml` | one per task, root `<Settings>`, referenced by the `taskXMLFile` attribute |

- Entry order irrelevant.
- Every non-`config.xml` entry is loaded as a task settings document keyed by entry name (`SQFileManager.loadTaskConfigs`); extra entries are silently ignored, a `<Task>` whose `taskXMLFile` entry is missing is a hard load error.
- Naming (`SQProject.generateTaskXMLFileName`): `<type>-Task<N>.xml`, `N` = lowest free integer >= 1 across all tasks regardless of type (Build then Retest => `Build-Task1.xml`, `Retest-Task2.xml`); gaps after deletions are legal.

## Flavour B - task template (`user/settings/Configs/*.cfx`, `templateFile` refs)

Exactly one entry, also `config.xml`, root `<Task>` with the `<Settings>` nested inside:

```xml
<Task type="Build" name="Build strategies" sampleName="Custom" active="true"
      version="141.2219" taskXMLFile="Build-Task1.xml">
  <Settings>...</Settings>
</Task>
```

Read/written by `apply_config_file` (servlet `saveConfig`/`loadConfig`), which only touches task #1
of the target project; load checks the template `type` matches task #1 and replaces its
`<Settings>` content. `.sqb` building-block files use the same scheme with a `<Blocks>` root.

## Versioning

`version="<major>.<build>"` on the root element of `config.xml` (e.g. `145.3039`), rewritten on
every save by `SQFileManager.tryCorrectVersion`. Major < 136 or missing = legacy pre-136 migration
and full archive rewrite. Always stamp the current app version.

## Serialization

- JDOM2 pretty-print (2-space indent), UTF-8, no XML declaration in stored entries.
- Single-entry update (`set_task_config`) uses the JDK zip FileSystem (`SQFileManager.updateZipContent`), rest untouched. Its URI escaping covers only space, `%`, `[`, `]`, `#`: project names with other URI-reserved characters (e.g. `+`) break single-entry updates while the full rewrite works.
- Full rewrite (`SQProject.saveConfig()`) creates `project_backup.cfx`, rebuilds the archive, deletes the backup, enforces `taskEls.size() == tasks.size()` ("Project integrity failed"): never a `config.xml` `<Task>` without its entry or vice versa.

## Building a `.cfx` outside SQX

Any zip tool: SQAI's `zip_files` MCP tool with `flatten=true` (archive path may end in `.cfx`),
PowerShell `Compress-Archive`, `zip`, Python `zipfile`. Rules:
1. entries at the archive root (`zip_files(flatten=true)` guarantees it; `Compress-Archive` on a directory adds a prefix, so zip the files, not the folder),
2. `config.xml` root `<Project>` (A) or `<Task>` (B),
3. A: every `<Task taskXMLFile="...">` has a matching entry with root `<Settings>`,
4. root carries `version="<current app version>"`.

`ProjectEngine` caches projects at startup: a `project.cfx` dropped into `user/projects/<name>/`
is invisible until imported with `open_project` (below); changes to an existing project go through
`set_task_config`.

## Validating a `.cfx` before importing it

`taskmanager/validateProject` (MCP: `validate_project_file`) answers "would this load and build
here" without registering anything (nothing copied to `user/projects`, no folder, databank or run).
Project twin of `algowizard/validate` (`ProjectFileValidator` / `StrategyFileValidator`); the gate
before `open_project`.

```
POST /taskmanager/validateProject   filePath=<absolute .cfx>  [deep=false] [settings=false]
{"valid":true,  "project":..., "version":..., "tasks":[...], "templates":[...], "settings":{...}, "warnings":[...]}
{"valid":false, "stage":"open|config|tasks|templates|settings", "error":"...", "warnings":[...]}
```

Invalid = a verdict returned with success, not an API error.

| Stage | Refused |
|---|---|
| `open` | not a flat ZIP with `config.xml` at the root (usually a zipped folder) |
| `config` | root not `<Project>`, or no name / no `<Tasks>` |
| `tasks` | `<Task taskXMLFile=...>` entry missing, entry root not `<Settings>`, `type=` with no plugin in this build, template mode without `templateFile` |
| `templates` | a build task's `templateFile` does not resolve (literal path, then `user/settings/StrategyTemplates/`) or fails to load; `deep=false` only checks existence |
| `settings` | an ACTIVE task's settings unusable on this install, the check `SQProject.start()` makes ("Cannot start project, it has config errors in task X"), and the Data mistakes the Data tab repairs in memory while it reads: a chart symbol the Data Manager does not have and the task's `<Resources>` do not declare, a reversed date range, a negative spread; `settings.errors[]` = `{task, setting, field, error}` each; `settings=false` skips the pass |

Settings pass without import: the setting-tab plugins validate (`AbstractTask.setConfig` ->
`ISettingTabPlugin.readSettings` -> `TaskSettingsData.addError`), several resolving a databank via
`ProjectEngine.get(projectName)`, so `ProjectEngine.addForValidation()` puts an in-memory
`SQProject` (bound to the `.cfx`, databanks from its `config.xml`) into a transient map only
`get()` consults (never `list()`, never disk, released in `finally`) and `ProjectFileValidator`
runs the real `initTasksFromConfig()` over it. Inactive tasks are not settings-checked (not read
at load either).

`warnings` = tolerated at load, not to be emitted by a generator: colliding output databanks, a
databank no `<Databanks>` entry registers, symbols/sessions the tasks declare in `<Resources>` that
this install lacks (the import marks the project as unresolved), stale or missing version
stamp, archive entries no task references.

## Importing live: `open_project`

1. Write `config.xml` + one `<Type>-TaskN.xml` per task into the SQAI scratchpad `internal/web/SQAI/state/scratch/<name>/`, zip flat: `zip_files(archive="internal/web/SQAI/state/scratch/<name>.cfx", dir=..., flatten=true)`.
2. `open_project(file, projectName?)` copies the archive to `user/projects/<name>/project.cfx` and registers it immediately, no restart; the returned `projectName` may be auto-suffixed on collision.
3. Show it in the UI: `shell.nav.projects` + `projects.list.reload`.

The root `<Project>` must carry the current app version (see Versioning).

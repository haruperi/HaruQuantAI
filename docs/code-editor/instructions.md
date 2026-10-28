# AppCodeEditor: unified building block library

AppCodeEditor edits quantitative Python components under `app/include/`. Indicators
share one library with domain folders and a `custom/` folder. Other building block
packages live directly under `app/include/`.

## Library layout and permissions

```text
app/include/
  indicators/
    base.py
    trend/ momentum/ volatility/ volume/ price_action/ regime/ custom/
  actions/
  signals/ orders/ money_management/ metrics/ trade_columns/
  monte_carlo/manipulation/ monte_carlo/retest/
  what_if/ analysis/ ai_tools/
  contracts.py enums.py comparisons.py price.py bar_time.py functions.py
```

The navigator starts at `app/include/`, supports folder expansion and filtering,
and labels building block domains. Indicator badges identify their category.
Public library files can be edited, renamed, cloned, packaged, and deleted.
Paths outside this root, the root itself, and paths containing dot-prefixed or
`__`-prefixed components are protected. A directory containing protected package
files cannot be deleted or renamed wholesale. Resolved paths are checked so a
symlink or traversal cannot bypass confinement.

## Create a component

Choose **Create from Template**, enter a public Python identifier, inspect the
live preview, then choose **Create Snippet**. The preview shows the complete
normalized destination, including the filename. The new file opens in a tab.

For **Technical Indicator**, choose one of `trend`, `momentum`, `volatility`,
`volume`, `price_action`, `regime`, or `custom`. To create another domain folder,
choose **New category...** and enter a public Python identifier, such as `research`.
The server normalizes category and component names to snake case. Slashes,
traversal, empty categories, and private names are rejected.

For example, `CustomSMA` in category `trend` creates
`app/include/indicators/trend/custom_sma.py`. Omitting the category uses `custom`.

| Template | Destination |
| --- | --- |
| `BlocksIndicators` | `app/include/indicators/<category>/` |
| `BlocksSignal` | `app/include/signals/` |
| `BlocksOrder` | `app/include/orders/` |
| `BlocksOtherActions` | `app/include/actions/` |
| `ColumnsDatabanks` | `app/include/metrics/` |
| `ColumnsTrades` | `app/include/trade_columns/` |
| `MoneyManagement` | `app/include/money_management/` |
| `MonteCarloManipulation` | `app/include/monte_carlo/manipulation/` |
| `MonteCarloRetest` | `app/include/monte_carlo/retest/` |
| `WhatIf` | `app/include/what_if/` |
| `CustomAnalysis` | `app/include/analysis/` |
| `AITools` | `app/include/ai_tools/` |

Template preview and creation both accept `category` through the HTTP bridge:

```json
{
  "template_type": "BlocksIndicators",
  "name": "CustomSMA",
  "category": "trend"
}
```

Send this to `POST /api/v1/code-editor/templates/create`. Preview uses
`POST /api/v1/code-editor/templates/render`, with `template_id` instead of
`template_type`.

## Edit, save, and organize files

The CodeMirror editor provides Python syntax coloring for keywords, class and
function definitions, builtins, variables, strings, numbers, and comments. Completion
suggestions include Python keywords, builtins, and names defined or imported in the
current file. Suggestions appear while typing; Ctrl+Space opens them explicitly,
and Enter or Tab accepts a selection. Escape dismisses suggestions. Completion is
local to the document; external-package type inference requires a language server.

Line numbers, folding, bracket matching, automatic bracket/quote closing,
four-space indentation, find/replace, and undo/redo are built in. Each open file
retains its own selection, scroll position, and undo history when switching tabs.
Compile and save diagnostics appear inline as well as in the Problems panel.
The right panel retains its textual class/import outline.
Changes mark the tab dirty. Closing a dirty tab requires confirmation. Reopening
an already open document preserves its unsaved buffer. Renaming an open file or
folder remaps its tab paths and retains the edited contents.

**Save** (Ctrl/Cmd+S) stages and flushes a temporary file before replacing the
saved file, then returns Python syntax diagnostics. **Save All** stages the batch
before publication and rolls earlier replacements back on an ordinary failure.
Each replacement is atomic; the batch is not a filesystem-wide transaction across
process termination or power loss.

Open buffers, including empty and dirty content, and the active tab are saved
through `HostPersistence` in SQLite. The browser warns before unloading with
unsaved edits. Workspace state is shared by this backend's editor session.

Navigator context actions provide create-file, create-directory, clone, rename,
delete, compile, test, and copy-path operations. Cloning updates the primary
class name and its direct Python name references. Find in Files searches the
include tree and returns file, line, and column coordinates.

## Compile and registration

**Compile** (F7) parses and executes the exact supplied buffer, including unsaved
changes. Diagnostics include syntax errors, unresolved global names, and import
or contract errors. Package-relative imports retain their package context.
**Compile All** scans public Python files throughout `app/include/`.

Concrete indicator classes must inherit the canonical `BaseIndicator`. The
indicator base module itself defines the abstract contract and is validated
without registering it as a concrete indicator. Metric and position-sizing
components implement `BaseMetric` and `BasePositionSizer` respectively. Those two
contracts currently live in `app.workspace.code_editor.registry`.

Registrations are replaced by source path. The indicator tester consults the live
registry before loading a file, so it uses the latest successfully compiled
buffer. Filesystem indicator discovery reads class declarations without executing
unrelated files. Duplicate class names in separate files require an explicit path.
Direct file paths must resolve inside `app/include/indicators/`; imported helper
indicators are excluded when selecting a file's declared class.

## Indicator testing

Choose **Test Indicator** to open the test bench. It derives parameters from the
selected class, reads matching stored symbol/timeframe history from Data Manager,
and displays historical candles and indicator series using Lightweight Charts.
Import history in Data Manager first if the requested data is unavailable. Multiple
matching datasets produce an explicit error rather than selecting a source silently.

Reserve bars provide a warmup window before the displayed bars. Indicator outputs
retain NaN/infinity gaps and report anomalies; missing values are never turned into
zero. Multi-output indicators provide named series on the price chart or oscillator
panes, with a data grid and optional reference discrepancies.

Parameter changes rerun the test. **Save Test Configuration** persists the complete
setup and returns a configuration ID in the logs. **Load Test Configuration**
restores it by ID. Configurations survive a backend restart.

## Modular action blocks

`app.include.actions` is a package with a stable facade:

```text
actions/
  base.py             ActionRecord, ORDER_NOT_DEFINED
  assign_variable.py  AssignVariableAction, assign_variable
  annotations.py      Arrow and vertical-line classes and helpers
  logging.py          File log, journal log, and email classes and helpers
  custom.py           CustomAction, custom_action
  facade.py           Actions convenience methods
  __init__.py         All 19 public re-exports
```

Existing imports remain valid:

```python
from app.include.actions import Actions, ActionRecord, DrawUpArrowAction

record = Actions.draw_up_arrow(shift=3)
assert isinstance(record, ActionRecord)
```

## Extension packages and AI tools

Export selected Python files to a `.zip` or `.sxp` archive with a `manifest.json`.
The archive retains paths relative to the project root. Inspect a package before
importing, then choose overwrite, skip, or rename for collisions. Rename chooses
an unused destination, preserving existing imported copies. Imported files are
compiled and their reload results returned.

AI tool files anywhere under `app/include/ai_tools/` declare tool classes with
`name`, `description`, `get_input_schema()`, and `run(arguments)`. Compile the file
to register its tools. Calls validate arguments against the declared JSON schema.
The stateless MCP endpoint is `/api/v1/code-editor/mcp`; it supports initialization,
`tools/list`, and `tools/call`. REST discovery and invocation are also available at
`/api/v1/code-editor/tools` and `/api/v1/code-editor/tools/{name}/call`.

## Verification

```powershell
uv run pytest tests/workspace/ -q
uv run ruff check .
uv run ruff format --check .
uv run mypy app/workspace/code_editor app/include/actions --follow-imports silent
cd ui
npx vitest run tests/unit/workspace/CodeEditor/
npm run build
npx playwright test tests/e2e/code-editor-regressions.spec.ts --workers=1
```

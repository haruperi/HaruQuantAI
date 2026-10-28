# AppCodeEditor review corrections

The editor now persists open buffers (including empty and dirty buffers), tab
selection, and named indicator setups through `HostPersistence`. Destructive
operations are limited to custom snippets; package files and application sources
are protected. Renaming a folder remaps its open descendants without dropping edits.

Save stages and flushes a temporary file before replacement. Save All stages the
entire batch and restores earlier replacements if publication fails. Replacement
is atomic per file and rollback covers ordinary exceptions; there is no claim of
a filesystem-wide transaction across process termination or power loss.

Compile executes the supplied buffer, checks unresolved globals and required
base classes, and replaces registrations by source path. AI extensions are
discoverable through `/api/v1/code-editor/tools` and callable through
`/api/v1/code-editor/tools/{name}/call` with schema validation. The stateless
MCP endpoint `/api/v1/code-editor/mcp` supports initialization, tool discovery,
and tool calls against the same live registry.

Indicator tests read matching stored Data Manager history. Missing or ambiguous
history produces an explicit error. Tests derive parameters from class signatures,
preserve non-finite outputs as chart gaps with diagnostics, and support multiple
output series on price or oscillator panes. Configuration IDs survive restart.
The UI uses Lightweight Charts and shows only executed calculations.

Regression tests cover buffer recovery, dirty close protection, empty saves,
renames, rollback, protected paths, exact-buffer compilation, all twelve template
imports, extension registration, archive collisions, real Parquet reads, multi-output
indicators, NaNs, configuration recovery, and HTTP errors. Browser tests use mocked
host and editor endpoints; backend history tests use isolated SQLite and Parquet
fixtures rather than the user's database.

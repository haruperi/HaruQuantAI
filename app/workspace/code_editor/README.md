# Code Editor contracts and ownership

Feature: `FEAT-CODE-EDITOR-CONTRACTS`. Owner: `app/workspace/code_editor`.

Legacy services retain dictionary results and synchronous endpoints. The live
editor Compile action uses the host-managed asynchronous compilation contract.
`requests.py` owns Pydantic inputs; `results.py` owns typed result/state records;
`errors.py` owns the compatible message-first `CodeEditorError` domain exception.
Every HTTP editor operation declares its success schema. MCP remains JSON-RPC,
not an editor success envelope. Existing request imports from `http.py` and
`CodeEditorError` imports from `_common.py` remain available.

## Validation and compatibility

- HTTP routes and `{status: "success", data: ...}` are unchanged. TypedDict result
  records preserve absent optional fields; unexpected fields fail validation
  instead of silently disappearing.
- Request extras remain ignored, including title/dirty/cursor fields sent with
  session buffers. Existing Pydantic scalar coercions remain; no global strict
  request mode is introduced. Nested Save All/session records require content.
- Empty content is valid. Omitted/null indicator parameters derive class defaults;
  an explicit empty parameter mapping remains empty. Reserve/count defaults stay
  50/150, with ranges 0..10000 and 1..10000. No donor batch defaults are substituted.
- Package rules remain overwrite/skip/rename. Inputs and stored JSON must be
  finite JSON. Domain results distinguish finite differences, non-finite output
  diagnostics and execution failures. Calculation success is not reference parity.
- Request validation and expected domain errors retain the host validation/422
  category. Host failures carry unavailable; invalid stored/results and unexpected
  errors carry internal. Host transport currently maps those latter categories
  to 503. Safe messages are used without raw unexpected exception contents.
- Persisted workspace and indicator documents are checked before publication.
  Missing state initializes normally. Corrupt JSON, invalid shape/window or
  identity, duplicate tabs and invalid active selections fail closed; the original
  stored document is not reset, deleted, migrated or rewritten.

Host transport retains its canonical `StandardError` and `ResponseMetadata`
models for failure envelopes. The workspace does not create a competing transport
error schema or replace the host exception handlers.

## Save As

`FEAT-CODE-EDITOR-SAVE-AS` publishes the current buffer through the typed
`POST /api/v1/code-editor/file/save-as` operation. Only a new writable snippet
destination is accepted. Existing files, protected paths, source aliases and
destinations already open in another tab are rejected. Exclusive publication
uses a complete staged file; it never overwrites a competing destination.

The source file stays unchanged. The destination replaces its tab in place,
becomes active and clean, and preserves other buffers. The client serializes
session synchronization and freezes conflicting editor actions during Save As.
If persistence fails after publication, the new file remains and the original
session stays in memory; the error explicitly reports that partial effect.
Filesystem publication and host persistence are not one atomic transaction.

## Host capability ownership

| Capability | Existing authority | Editor use in this task |
| --- | --- | --- |
| SQLite schema | `app/core/host/persistence.py:HostPersistence.ensure_code_editor_schema` | Reuse additive `code_editor_state(id,payload)` installation; no SQL in workspace code and no schema changes |
| Transactions | `HostPersistence.transaction` | Existing read/update-or-create transaction; keys stay `workspace` and `indicator:<test_id>` |
| File publication | `_storage.atomic_write_batch` | Existing exception rollback; not power-loss atomic across multiple files |
| Jobs/workers | `app/core/jobs/manager.py:JobManager` | Lazy application-owned I/O worker pool; editor submissions use `executor_kind="thread"`, owner `code_editor`, kind `editor_compilation`; host lifespan cancels/shuts down the pool |
| Events | Host job transition records; existing host EventBus | Compilation delivery polls typed snapshots by job ID; no competing SSE channel/event bus is created |
| Logging lifecycle | Existing host logging startup/shutdown | Workspace modules use standard named loggers; never configure handlers or start a logging listener |

## Observable requirement records

Public execution surfaces emit fixed `FR-code-editor-<module>-<operation>` DEBUG
invocation labels. Existing completion/rejection records use fixed requirement
labels as well. Request/result validation and state gateway/read/write boundaries
emit explicit acceptance, completion, rejection or unavailable records. Pure record
definitions create no runtime service; their validation is observed at those
boundaries. Generated snippet source is retained; its authoring workflow is logged
by the public template service rather than by executing the generated source.

`test_logging.py` explicitly verifies request/result success and rejection,
search/compilation invocation, storage failure and exclusion of source/query/host
error markers from logs. HTTP tests verify safe validation and unexpected/result
failure envelopes. No request body, source buffer, search query or raw unexpected
exception is copied into operation logs. Source diagnostics returned to the
requesting editor remain distinct from operation logs.

## Complete editor commands

Feature: `FEAT-CODE-EDITOR-COMMANDS`. `command_models.py` defines exact request,
result and persistence records; `command_http.py` installs routes under the
existing error/envelope adapter. `http.py` retains compatibility endpoints.

| Capability | Contract |
| --- | --- |
| Disk reload | `/file/reload` requires an open existing file and explicit `discard_dirty` for a dirty buffer; candidate session persistence precedes in-memory replacement |
| Ownership | `path_policy.py` reads versioned `builtin_files.json`; shipped files and containing directories, host paths and private package names are protected. Update the manifest when shipping new builtins. User-authored files remain writable; builtin clones default to `app/include/user/<original-relative-directory>/<name>_copy.py` |
| Navigation/search | Ownership and text filters apply to navigation; entries carry ownership/protection. Search exposes case/regex/whole-word/directory controls; invalid regexes return safe validation errors |
| Symbols | Static public declarations and member names, overlaid with successfully compiled class metadata; autocomplete resolves class names, imported aliases and simple constructor bindings. It is not a full Python type checker |
| Indicators | Typed identity `file_path::ClassName`, canonical defaults, output names and protection. Class-qualified identities disambiguate files declaring multiple indicators |
| Code types/templates | Twelve Python generator families, MonteCarlo alias with Manipulation/Retest choices, and CodeExport format choices. Template lists filter by selected path; the modal uses the server catalogue and retains local presentation metadata only |
| Subtypes | Open/Modify/Close order actions map to subtype directories and returned action metadata. Derived signals bind the selected indicator/output and provide an evaluation function |
| Export authoring | Only Python (`.py.tpl`) and pseudocode (`.txt.tpl`) source-authoring formats are supported; selected public symbols become import/use declarations. This does not claim Java/SQX, MT4/MT5 or other strategy compiler compatibility |
| Import repair | Returns a proposed buffer, preserving module docstrings and future imports. Unique indexed/known standard imports are added; ambiguous candidates require an explicit valid module selection. No disk write occurs |
| Recovery | Missing disk files retain their stored buffers, become dirty and produce recovery warnings for Save As. Invalid/corrupt sessions and compilation records fail closed without deletion/reset/migration; duplicate session identities are rejected |

Compilation scopes are `file` (captured buffer), `package` (explicit include
directory and Python files including package initializers), `all` (include tree),
and `registered` (all workspace registry paths, including tools). Failed/missing
registered files are unregistered during reload. Results identify individual files.
The host installs/validates its additive `host_jobs`/`host_job_events` schema through
`HostPersistence.ensure_jobs_schema`; incompatible existing definitions fail closed.

The editor reuses host `code_editor_state` keys `compilation:<job_id>` and
`compilation:latest` for validated snapshots, progress, source hashes and diagnostics.
There is no new SQL in workspace modules, retention worker or schema migration.
Snapshots remain retained under the existing host storage policy. A restored
nonterminal editor snapshot without a live editor worker becomes `INTERRUPTED`;
the editor does not rewrite unrelated host jobs. Source hashes prevent stale
diagnostics from being attached inline to a changed buffer. Job-ID checks prevent
late reconnect/polling results from replacing a newer submission.

Cancellation is cooperative: it stops before the next file and after the current
import returns. A request is not reported terminal while that import is running;
already completed imports may have registered classes or produced side effects.
Arbitrary Python imports cannot be safely force-terminated in this thread-based
registration runtime. Host shutdown waits for workers and requests cancellation.

## Verification

Focused iteration uses explicit test files and `--no-cov`. Final verification
includes strict mypy and Ruff for this package, editor tests, branch-aware editor
coverage and the frontend package checks. Package coverage is not repository-wide
coverage evidence. Tests use isolated temporary host stores and history fixtures;
they must not reset or modify an active application database.

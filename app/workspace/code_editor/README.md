# Code Editor contracts and ownership

Feature: `FEAT-CODE-EDITOR-CONTRACTS`. Owner: `app/workspace/code_editor`.

The existing services retain dictionary results and synchronous execution.
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

## Host capability ownership

| Capability | Existing authority | Editor use in this task |
| --- | --- | --- |
| SQLite schema | `app/core/host/persistence.py:HostPersistence.ensure_code_editor_schema` | Reuse additive `code_editor_state(id,payload)` installation; no SQL in workspace code and no schema changes |
| Transactions | `HostPersistence.transaction` | Existing read/update-or-create transaction; keys stay `workspace` and `indicator:<test_id>` |
| File publication | `_storage.atomic_write_batch` | Existing exception rollback; not power-loss atomic across multiple files |
| Jobs/workers | `app/core/jobs/manager.py:JobManager` | No new manager, worker, cancellation protocol or job state is created |
| Events | `app/core/host/events.py:EventBus`, `HostEvent` | No editor channel, subscriber or publisher is added; future jobs/events need their own approved host integration |
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

## Verification

Focused iteration uses explicit test files and `--no-cov`. Final verification
includes strict mypy and Ruff for this package, editor tests, branch-aware editor
coverage and the frontend package checks. Package coverage is not repository-wide
coverage evidence. Tests use isolated temporary host stores and history fixtures;
they must not reset or modify an active application database.

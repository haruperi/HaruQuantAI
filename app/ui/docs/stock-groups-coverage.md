# Data Manager Stock Groups Coverage

## Inclusion register

| Feature ID | Product / screen / trigger | Source evidence | Visible controls | Preconditions and validation | State transitions and expected outcome | Mock operation / persistence | Visual | Interaction | State | Evidence gaps / assumptions |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DATA-STOCK-GROUP-EDITOR-001 | SQX / Data Manager / Stock groups; Add new or row double-click | `DataManagerBasket/actions/add/module.js`, `views/addBasketModal.html`, `BasketsCtrl.js`, compiled `saveGroup` | Group name, Description, Close, Save | Required unique name; trim; normalize custom name to single brackets; 50/250 character compiled storage limits; system group immutable | Add/Edit → validate → persist or located error; Edit preserves members | `stockGroups.saveGroup`; `sqx-stock-groups-v1` | Implemented | Implemented | Implemented | SQX built-in catalogue resides in runtime database state and is not fabricated. |
| DATA-STOCK-GROUP-MEMBERS-001 | SQX / Stock groups; Edit stocks | `actions/editStocks/module.js`, `views/editStocksModal.html`, compiled `readStocksFromCsv`, `updateStocksFromStr`, `writeStocksToCsv` | Help/examples, Import from file, Export to file, textarea, Close, Save | First selected custom group; non-empty lines; ticker up to 50 characters; optional `DD.MM.YYYY` or `YYYY.MM.DD`; bounded CSV | Open → replace manually/import → persist and close; export downloads versioned `GroupStocks.json` | `stockGroups.replaceMembers`; local members | Implemented | Implemented | Implemented | HaruQuantAI intentionally replaces SQX's misleading XML-named semicolon export with typed JSON. Invalid dates map to undefined as SQX does. |
| DATA-STOCK-GROUP-UPDATE-001 | SQX / Stock groups; Update toolbar or inline readiness link | `actions/updateData/module.js`, `BasketService.js`, compiled update/count/readiness methods | Update action, inline `No, Update data`, shared progress Pause/Resume/Stop | Selection; non-empty members; special limited group rejected; one active data operation | Start → running/paused/stopped/failed/completed; reload running→paused; completion adds missing local SQ Equity rows and refreshes summaries | `stockGroups.start/advance/action`; persisted job and generated rows | Implemented | Implemented | Implemented | Provider/network and backend aggregate generation are replaced by deterministic browser-local rows. |
| DATA-STOCK-GROUP-DELETE-001 | SQX / Stock groups; Mass delete | Shared delete registration and `BasketsCtrl.getSelectedBaskets(true)` | Remove group(s), question, No, Yes | At least one selected non-system group | Select → exclude protected rows → confirm/cancel → atomic remove | `stockGroups.remove`; persisted definitions | Implemented | Implemented | Implemented | No active dependency endpoint was exposed for groups in supplied web resources. |
| DATA-STOCK-GROUP-TRANSFER-001 | SQX / Stock groups; Save or Load | Shared save/load registrations, compiled `onSave`/`onLoad`, `BasketDto.toXML` | Direct Save download; JSON picker; Load; duplicate Cancel/Skip/Overwrite | Save selection; bounded versioned JSON; valid names/ISO dates; system overwrite blocked | Download `Groups.json`; or parse/stage → resolve every duplicate → atomic apply/cancel | `stockGroups.save/load`; versioned localStorage | Implemented | Implemented | Implemented | Browser JSON replaces the SQX native XML path while retaining the workflow. |
| DATA-STOCK-GROUP-TABLE-001 | SQX / Data Manager / Stock groups tab | `views/baskets.html`, `BasketsCtrl.js`, compiled count/download/readiness methods | Select-all/rows; Name, Count, Description, Number of symbols, Downloaded, Ready, Data from/to; double-click | None; selection required by scoped actions | Select/edit/update; summaries react to membership and dataset changes; exact empty state | `stockGroups.list/summarize`; persisted definitions and transient selection | Implemented | Implemented | Implemented | SQX reads range from a backend aggregate group dataset. Mock derives range from matching member datasets. |

## Verification

- `stockGroups.test.ts`: name normalization, dual date parsing, historical memberships, active/count/readiness summaries, and versioned JSON round trips.
- `data-manager-stock-groups.spec.ts`: selection guard, Add/Edit stocks, CSV replacement, inline update, pause/reload/resume, generated Data sources rows, persistence, delete, JSON download/load/overwrite, invalid kind, and dark/light screenshots.
- `data-manager-source-ribbon.spec.ts`: audited six-action order, complete table columns, exact empty state, and surrounding Data Manager regression.
- TypeScript typecheck, production build, complete Vitest suite, Data Manager Playwright suite, and repository CI are recorded in the walkthrough.

## Exclusion register

| Excluded behavior | Reason |
|---|---|
| Fabricated SQX default-group catalogue | Names and memberships live in runtime database state rather than audited donor files. System semantics remain implemented at the domain boundary. |
| Live equity-provider downloads | No backend exists. Deterministic local SQ Equity rows provide coherent mock results without network activity. |
| Native aggregate group-data generation | SQX performs this in compiled backend code. Visible group range is inferred from matching member datasets. |
| Native path pickers | Browser file inputs and exact-name downloads provide the corresponding safe frontend workflow. |
| Strategy Builder stock-picker integration | This task owns the Data Manager Stock groups screen and workflows. |
| QuantDataManager variant | SQX intentionally hides this tab there; HaruQuantAI presents the full research-platform profile. |

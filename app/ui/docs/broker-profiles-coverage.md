# Data Manager Broker Profiles Coverage

## Inclusion register

| Feature ID | Product / screen / trigger | Source evidence | Visible controls | Preconditions and validation | State transitions and expected outcome | Mock operation / persistence | Visual | Interaction | State | Evidence gaps / assumptions |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DATA-BROKER-EDITOR-001 | SQX / Broker profiles / Add new or row double-click | `DataManagerBroker/views/addBrokerModal.html`, `BrokersCtrl.js`, compiled `BrokerManager.saveBroker` | Name, description, Stockpicker and MT4/5 toggles, timezone, postfix, Close, Save | Required unique normalized name; 50/250/100 limits; protected/dependency-disabled settings | Add/Edit → validate → persist/error; all broker selectors refresh | `useDataManagerStore.saveBroker`; `sqx-data-manager-v1` v2 | Implemented | Implemented | Implemented | Runtime system broker rows are database-backed and not fabricated. |
| DATA-BROKER-STOCKS-001 | SQX / Broker profiles / Edit stocks | `editStocksModal.html`, compiled `readStocksFromCsv`, `writeStocksToCsv` | Help/example, CSV import, `BrokerStocks.json` export, line editor, Close, Save | One Stockpicker-enabled custom broker; bounded UTF-8 file | Open → replace/export → persist and close | `saveBrokerStocks`; profile stocks in v2 state | Implemented | Implemented | Implemented | HaruQuantAI replaces SQX's misleading XML-named newline export with typed JSON. |
| DATA-BROKER-IMPORT-001 | SQX / Import broker instruments/sessions | Import modal templates, `BrokerXmlImporter`, controller overview/conflict paths | Data file, Browse, broker, postfix, overview selection, Close, Start Import, conflict OK/Cancel | Bounded valid Instruments/Sessions JSON; selected rows; MT-enabled target | Parse overview → select → target/postfix → confirm conflict → atomic import | `useFileSymbols.importInstruments`; `useSessions.importForBroker` | Implemented | Implemented | Implemented | Browser JSON input replaces the native SQX picker and XML format. |
| DATA-BROKER-UPDATE-001 | SQX / Update data for broker (automatic) | Update action/service and compiled `_onUpdateData` | Toolbar action and shared progress Pause/Resume/Stop | Selected first broker supports Stockpicker; stocks exist; no active broker job | running/paused/stopped/failed/completed; reload running→paused; completion adds missing SQ Equity rows | `startBrokerUpdate/advanceBrokerUpdate/brokerAction`; v2 persisted job/data | Implemented | Implemented | Implemented | Remote stock-information lookup is replaced by deterministic local rows. |
| DATA-BROKER-DELETE-001 | SQX / Broker profiles / Mass delete | `BrokersCtrl.js`, compiled dependency-safe delete | Remove broker(s), No, Yes | Selection; no instrument/session dependencies; non-system broker | confirm/cancel → atomic remove and exact notification | `removeBrokers`; v2 profiles | Implemented | Implemented | Implemented | Dependency rejection is conservative and explicit. |
| DATA-BROKER-TRANSFER-001 | SQX / Broker profiles / Save or Load | Shared actions, compiled `BrokerServlet.toXML/onLoad` | Direct `Brokers.json` download; JSON picker; duplicate Cancel/Skip/Overwrite/Overwrite all | Save selection; bounded versioned Brokers JSON; complete profile/stock data | Download; or validate/stage → duplicate decisions → atomic apply | `serializeBrokersJson/parseBrokersJson/importBrokers`; v2 profiles | Implemented | Implemented | Implemented | Browser JSON replaces the native SQX XML save path. |
| DATA-BROKER-TABLE-001 | SQX / Data Manager / Broker profiles | `brokers.html`, `BrokersCtrl.initGrids/list` | Select-all/rows, seven data columns, double-click | None; action-specific selection guards | Select/edit/refresh; counts derive from effective stocks/instruments/sessions | reactive canonical store; selection transient | Implemented | Implemented | Implemented | QDM variant hides stock columns/actions; full Haru profile uses SQUANT view. |

## Verification

- `brokerProfiles.test.ts`: normalization, uniqueness, stock parsing, versioned JSON round trip, invalid-envelope rejection, and legacy double-bracket handling.
- `data-manager-broker-profiles.spec.ts`: selection guards, Add, stocks, update pause/reload/resume, save/delete, broker JSON load/overwrite, selected Sessions/Instruments JSON imports, postfix mapping, and cross-tab visibility.
- `data-manager-source-ribbon.spec.ts`, Instruments, Sessions, and Dukascopy suites: action/column order, empty state, and shared broker regressions.
- Typecheck, production build, full Vitest, full Playwright, and repository CI results are recorded in the walkthrough.

## Exclusion register

| Excluded behavior | Reason |
|---|---|
| Fabricated built-in broker catalogue | Installed broker rows are runtime database state absent from donor assets. |
| Remote broker/stock-information updates | No backend exists; deterministic browser-local SQ Equity rows model the audited result. |
| Native path pickers | Browser uploads/downloads implement the corresponding safe frontend behavior. |
| QuantDataManager reduced variant | HaruQuantAI currently presents the full feature profile. |
| Backend database mutation | All behavior is explicitly browser-local mock state. |

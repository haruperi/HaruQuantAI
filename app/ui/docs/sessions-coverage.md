# Data Manager Sessions Coverage

## Inclusion register

| Feature ID | Screen / trigger | Controls and behavior | Persistence / mock operation | Visual | Interaction | State | Evidence / gaps |
|---|---|---|---|---|---|---|---|
| DATA-SESSIONS-EDITOR-001 | Sessions > Add Session; row double-click | Name, broker/postfix, element grid, nested day/time/SEOC editor, Add Mon-Fri, Edit, Remove, validation, unsaved confirmation | `haru-data-sessions-v1`; `sessions.add`, `sessions.edit` | Implemented | Implemented | Implemented | `DataManagerSessions` templates/controller/service/JAR. Existing fixture names are retained although new SQX names reject spaces and `/`. |
| DATA-SESSIONS-CLONE-001 | Sessions > Clone Session | First-selected source, target broker, core name + `Clone`, postfix, deep element copy | `sessions.clone` | Implemented | Implemented | Implemented | `actions/clone` template/controller and compiled endpoint. |
| DATA-SESSIONS-DELETE-001 | Sessions > Mass Delete; trailing row × | Selection guard, SQX count confirmation, dependency-safe atomic removal | `sessions.remove` | Implemented | Implemented | Implemented | Shared delete registration and Sessions controller. Referenced fixture sessions are conservatively blocked because no native cascade is evidenced. |
| DATA-SESSIONS-TRANSFER-001 | Sessions > Save / Load | `Sessions.json` download, bounded versioned JSON input, complete Session/Element fields, Cancel/Skip/Overwrite duplicate sequence | `sessions.save`, `sessions.load` | Implemented | Implemented | Implemented | SQX's source shape was confirmed from `SQDataLib.jar`; HaruQuantAI intentionally uses JSON. Browser imports stage changes atomically. |
| DATA-SESSIONS-TABLE-001 | Data Manager > Sessions | Search across name/broker, broker filter, visible-row select-all, persistent selection, double-click edit, row delete, empty result | Shared session catalogue | Implemented | Implemented | Implemented | `sessions.html` and `SessionsCtrl.js`; QuantDataManager-only filter hiding is excluded because this product presents the full Data Manager profile. |

## Verification

- `sessions.test.ts`: name/element validation, same-day boundaries, weekday generation, weekend preservation, and versioned JSON round trips.
- `data-manager-sessions.spec.ts`: all popup entry points, nested edit, clone, delete, JSON conflict, filtering, dependency protection, reload, corruption, and dark/light screenshots.
- `data-manager-source-ribbon.spec.ts`: toolbar order, columns, filtering, and visible selection regression.

## Exclusion register

| Excluded behavior | Reason |
|---|---|
| Native filesystem and SQX database writes | No backend exists; meaningful browser JSON and versioned local persistence provide the requested frontend behavior. |
| Live market-session execution | Engine behavior is outside the frontend-only mock boundary. |
| Overlap validation | The active SQX controller does not enforce it, so the recreation does not invent it. |
| Delete cascade into instruments | No active SQX cascade contract was found; the mock fails closed to preserve referential integrity. |
| More than ten deletion worker behavior | This is a compiled backend performance detail with no distinct user-facing outcome in the frontend mock. |

# Application settings persistence

The settings menu uses UI -> `app/host/transport.py` -> `SettingsManager` in
`app/host/settings.py` -> `HostPersistence` -> `data/database/haruquantai.db`.
Only `HostPersistence` opens SQLite connections or executes SQL.

Forms save on Save; Cancel discards drafts. Skin and zoom save immediately.
Committed state comes from the host response. Offline, validation, persistence
and revision failures must remain visible and must not claim success.

All routes use the host response envelope and existing authentication/scopes.

| Route | Request / response data |
| --- | --- |
| GET /api/v1/settings | `{revision, values}`; logical groups, no secrets |
| PUT /api/v1/settings | `{expected_revision, changes}` -> committed snapshot |
| GET /api/v1/settings/catalogue | `{revision, fields, unknown}` |
| PUT /api/v1/settings/secrets | Revision/changes; explicit secret replacement or clear |
| GET /api/v1/auth/account | Username, revision, session timeout |
| PUT /api/v1/auth/account | Current password, username, timeout, optional new password |

HTTP 422 rejects malformed/unknown/readonly fields; 409 rejects stale revisions;
401/403 rejects unauthorized access. Extra and legacy mutation fields are rejected.
No-op saves leave the revision unchanged. Events follow commit and contain only
revision/group metadata. Secret GET projections contain `configured`, never values.
Blank secret drafts preserve stored secrets; explicitly clearing sends an empty
string. Account password changes require the current password and invalidate
existing sessions atomically with the settings update.

Logical group names map to existing `scope=application` rows: `app.general` maps
to `app_general`, `config.cpu` to `config_cpu`, and equivalent groups to their
underscore names. Remote preferences are nested in `app_general.remote_access`.
Registry path segments distinguish nested AI fields from literal calibration keys
such as `QQE.RSIPeriod`. Partial patches preserve unrelated/unknown leaves. Settings
revisions are compared inside the same persistence transaction as the writes.

Saving network, mail, MCP, broker or engine preferences does not execute those
capabilities. Restart-dependent fields are labeled. Workspace path changes do not
move files. Production credentials and databases are never used in automated tests.


Settings snapshots and catalogue entries include only fields present in stored
records. Missing fields are omitted; reads never seed defaults. Explicit edits
from static UI controls may create known missing fields. False, zero, empty
strings/lists and supported null values are preserved. Field types, validation,
secret restrictions and write permissions remain backend policy rather than
being inferred from mutable database values. Unknown stored fields remain read-only.

Catalogue categories without stored fields display an empty-state message. Save
is disabled when the dialog has no editable stored fields; populated tabs retain
their drafts. Missing account identity or session duration returns HTTP 503 with
`ACCOUNT_UNCONFIGURED`. Account creation/initialization is outside these routes.
The UI owns theme tokens; the backend stores only the selected theme identifier.

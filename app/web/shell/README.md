# UI Host Shell

`app/host/` is the HaruQuantAI frontend host — the shell that workspaces and
plugins plug into, and the UI counterpart of the backend `app/host/`.

## What lives here

- App shell: `App.tsx` (mount + navigation), `router.tsx`, `store.ts`,
  `HeaderApplications.tsx`, `GlobalSettingsMenu.tsx`, shared `types.ts`.
- Universal transport: `transport.ts`.
- Host connection: `HostConnection.tsx` acquires an in-memory session, reports
  readiness, and handles offline/expired-session states. `hostSettings.ts`
  validates the shell preference projection and consumes authenticated SSE.

## Transport boundary law

- The host owns the request/response envelope, error shape, request IDs, and
  `createDomainClient(routeBase)` — nothing else. It holds no domain knowledge
  and knows no workspace by name.
- Each workspace/plugin UI folder owns its client, its route base, and its
  contract with its backend counterpart. Plugin-specific contracts are never
  centralized here.
- The execution documents exported by `transport.ts` are frozen transitional
  shapes from the pre-reset gateway: they cross domain boundaries through the
  store and will be replaced by the ratified host contract.
- Default base URL and domain route bases are provisional until the backend
  host architecture ratifies the mounting scheme.
- The browser shell uses the same-origin `/api/v1` host in a built deployment;
  local Vite development on port 3000 targets the loopback host on port 8000.
  Saved host sessions are validated on reconnect; host password drafts are never
  stored. A 401 returns the shell to its login flow.
- Global Settings menu preferences (Configuration tabs, Remote access flags,
  non-secret SMTP fields, language, skin, and zoom) are loaded from scoped
  records in the host database. Each edit updates its owning record fields;
  the host excludes credential fields from settings responses and events.
  Browser storage excludes these host-owned settings. Offline or conflicting
  writes do not claim success. Secret drafts are transient; explicit credential
  saves persist in the host database and read back only presence metadata.
  Forms commit on Save; skin/zoom commit immediately. See the
  [settings API contract](../../../docs/dev/settings-api.md).
  Benchmark execution, MCP server activation, mail delivery, licensing,
  remote-server activation, and Exit still lack backend services.

## Connection rules (spatial composability)

1. The host pair owns the envelope; domain pairs own their contracts.
2. A workspace/plugin UI folder imports universal primitives
   (`components/ui`), the host transport, and its own files — never a sibling
   domain's internals.
3. The host discovers domains; it does not know them. Adding or removing a
   workspace never edits the host.
4. UI/backend pairs share contracts, never modules: the boundary is typed
   documents over the transport.

## Feature registry (this domain)

| Feature ID | Feature | Status |
|---|---|---|
| FEAT-UI-TRANSPORT | Universal UI-host transport: envelope, error mapping, request IDs, domain-client factory, host session startup, shell preference updates | implemented (`transport.ts`, `HostConnection.tsx`, `hostSettings.ts`) |
| FEAT-UI-WORKSPACE_INVENTORY | Sixteen workspace surfaces mirroring the SQX145 reference navigation inventory (plus normative MTAnalyzer and Live Trading) | implemented (`app/workspace/*`) |

## SQX145 reference qualification

Current donor root: `SQX_145_REFERENCE_ROOT`; source maps bind freshly inspected artifact identities. Retained UI functionality/status is unchanged; source differences and absent counterparts require task-level body/integration research. No runtime or connected backend parity is asserted.


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

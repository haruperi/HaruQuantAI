# UI Host Shell

`app/ui/app/host/` is the HaruQuantAI frontend host — the shell that workspaces and
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
  Tokens are not persisted. A 401 returns the shell to its login flow.
- Global Settings menu preferences (Configuration tabs, Remote access flags,
  non-secret SMTP fields, language, skin, and zoom) are loaded from scoped
  records in the host database. Each edit updates its owning record fields;
  the host excludes credential fields from settings responses and events.
  Browser storage excludes these host-owned settings. Offline or conflicting
  writes do not claim success. Passwords and license keys are transient.
  Benchmark, MCP, mail delivery, licensing,
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
| FEAT-UI-WORKSPACE_INVENTORY | Sixteen workspace surfaces mirroring the SQX 144.2953 navigation inventory (plus normative MTAnalyzer and Live Trading) | implemented (`app/workspace/*`) |


## Host boot integration (2026-09-29)

`HostConnection.tsx` and `app/cli.py` authenticate, attach live updates, read
init-data and acknowledge client initialization. Boot snapshots require
`schema_version: 2`; missing/unsupported versions produce explicit compatibility
errors. Deploy the host and both clients together.

`BootScreen.tsx` presents five host phases: runtime, services, packages, transport
and serving. It displays actual outcomes and reasons. An online shell requires a
SERVER_READY or DEGRADED host plus successful client initialization. No client
acknowledgment starts shared restoration, and no restoration polling loop remains.

`transport.ts` retains first-frame WebSocket authentication, in-memory bearer
tokens, heartbeat, bounded handshake timeout and overflow/disconnect errors.
Settings retain authenticated SSE. Missing research operations remain catalog or
command availability information; prototype navigation does not establish backend
capabilities. FirstRunDialog continues to disclose relevant host requirements.

| Feature ID | Feature | Status |
| --- | --- | --- |
| FEAT-UI-BOOT | Version-2 handshake, five-phase progress and independent client readiness | candidate; bootSequence.test.tsx and hostConnection.test.tsx; task walkthrough records verification |

No workspace algorithms or durable domain records are implemented in the UI host.
Evidence: `.agents/logs/2026-09-29T112552_simplify-host-boot/`.

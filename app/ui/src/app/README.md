# UI Host Shell

`src/app/` is the HaruQuantAI frontend host — the shell that workspaces and
plugins plug into, and the UI counterpart of the backend `app/host/`.

## What lives here

- App shell: `App.tsx` (mount + navigation), `router.tsx`, `store.ts`,
  `HeaderApplications.tsx`, `GlobalSettingsMenu.tsx`, shared `types.ts`.
- Universal transport: `transport.ts`.

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

## Connection rules (spatial composability)

1. The host pair owns the envelope; domain pairs own their contracts.
2. A workspace/plugin UI folder imports universal primitives
   (`components/ui`), the host transport, and its own files — never a sibling
   domain's internals.
3. The host discovers domains; it does not know them. Adding or removing a
   workspace never edits the host.
4. UI/backend pairs share contracts, never modules: the boundary is typed
   documents over the transport.

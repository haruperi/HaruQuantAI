# FEAT-UI-14 — Typed backend transport

This package owns `ui.typed-backend@1`: strict browser-side validation of the authoritative Interfaces wire envelopes plus scoped HTTP/SSE lifecycle management. It does not own backend routes, wire schemas, authorization, numerical policy, or business receipts.

## Public boundary

- `request` and `ApiClientError` retain the single typed HTTP transport used by the domain clients.
- `openStream` validates each SSE frame before exposure.
- `TypedBackendLifecycle` provides latest-only keyed requests and one deduplicated observation per safe presentation key. A transient observation reconnects at most once using the last validated sequence; disposing the final subscriber aborts the source.
- `TypedBackendFeature` and `TypedBackendCapabilityRegistry` provide explicit registration and exact-generation withdrawal. Resolution uses only the literal `ui.typed-backend@1` key and never selects a substitute.

Keys are 1–128 ASCII letters, digits, dots, colons, underscores or hyphens. They identify presentation ownership only and must never include credentials, payloads, account data or resource paths. The transport performs at most one retry for a transient safe GET after 100 ms. Mutations do not use the generic retry path; an idempotency-required operation fails closed if its original identity cannot be generated or supplied.

## Contract and failure semantics

`contracts.ts` mirrors `app/contracts/interfaces/models.py` and the generated Interfaces wire schema. Unknown envelope fields, wrong versions, invalid branch shapes and malformed owner payloads fail visibly as `ApiClientError`; the client does not infer a business value. Stream error objects are validated and reduced to their safe message for the retained frontend `StreamEvent` contract.

Cookie requests use `credentials: include`. Non-GET cookie calls mirror `hq_csrf` into `X-CSRF-Token`. Request, trace, authorization and idempotency headers are bounded to their declared purposes. Aborted/superseded work reports `GOVERNED_REQUEST_STALE` and is never retried.

## Usage and evidence

Run the bounded offline scenario:

```text
npm --prefix app/ui run usage -- src/clients/_usage.tsx
```

It validates a typed envelope, rejects drift, supersedes a stale request, shares and resumes an observation, removes the exact feature contribution, preserves an unrelated capability object and awaits cleanup. The canonical owner is `_usage.tsx`; it performs no network or persistent write.

Requirement evidence is owned by `__tests__/traceability.test.ts` and `__tests__/lifecycle.test.ts`, with retained transport/catalogue coverage in the existing client tests. Browser end-to-end qualification remains the Phase 1 checkpoint Task 1.30.

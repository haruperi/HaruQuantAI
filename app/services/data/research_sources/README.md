# Point-in-Time Research Sources

This folder owns `FEAT-DATA-16`. It retrieves bounded allowlisted provider
responses, normalizes provider-specific metadata and structured values, persists
immutable document and observation revisions, applies source-use policy, and
returns point-in-time bounded projections.

All document, observation, verified-manifest, and point-in-time query CRUD delegates
to `app.services.data.persistence`; this module retains policy, normalization,
eligibility, and evidence construction.

The Data package root is the only public boundary. Files in this folder and their
classes, constants, and parser functions are internal. Cross-domain consumers use
the standalone functions exported by `app.services.data`.

Supported deterministic normalization covers SEC EDGAR submissions,
Companyfacts, filing-document metadata, EX-99/transcript-like exhibit metadata,
BLS, BEA, EIA, Treasury Fiscal Data, CFTC COT, GDELT headline metadata, and USDA
NASS. Live access is opt-in and subject to provider identification, free-key,
environment, rate, retention, and license policy.

FRED/ALFRED and Reddit are prohibited. FINRA is blocked pending commercial-use
rights confirmation. Bluesky Jetstream is excluded because it is not
self-authenticating and is unsuitable for research evidence. Transcript coverage
is partial and does not authorize unrestricted transcript-body analysis.

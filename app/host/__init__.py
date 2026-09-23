"""HaruQuantAI host: the platform shell and backend half of the host pair.

The host owns exactly four universal concerns — the request/response
envelope, the host command surface, sessions, and mounting — and knows no
domain by name. Workspaces and plugins plug in beneath it through
self-describing manifests discovered by the catalog (Law 5).

The frontend counterpart is ``app/ui/src/app/``; the boundary laws are
codified in ``docs/ARCHITECTURE.md`` and ``app/host/README.md`` (which also
carries the module inventory and feature registry).
"""

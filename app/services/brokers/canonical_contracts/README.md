# Canonical Broker Contracts

> **Status:** Completed documented non-feature support directory.

This folder owns only shared Broker enums, DTOs, responses, error definitions,
protocols, and function-only constructors used by multiple registered features.
It owns no provider behavior, instrument-profile policy, workflow, persistence,
or separate cross-domain API. It is explicitly excluded from feature-count
reconciliation; the sole public boundary remains `app.services.brokers`.

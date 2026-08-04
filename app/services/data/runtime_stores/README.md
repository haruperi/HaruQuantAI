# Runtime Stores

Private Data-domain support for durable namespaced runtime records used by other
domains. The module validates runtime-store operations and delegates every database
read or mutation to `app.services.data.persistence`.

This directory is non-feature infrastructure owned by the Data domain. It has no
public Data-domain exports and must not be imported directly by cross-domain
consumers.

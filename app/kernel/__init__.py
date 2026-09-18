"""Business-neutral modular microkernel and lifecycle architecture.

This package provides the foundational dependency injection, capability-based
wiring, and lifecycle management for standalone modular monolith applications.

The kernel is structured around six core primitives:

1. Capability (`app.kernel.capability`):
   Typed, versioned contract tokens (`Capability[T]`). Features do not import
   each other directly; instead, they provide and require capabilities with full
   compile-time and runtime type safety.

2. Feature Manifest & Protocol (`app.kernel.feature`):
   The structural contract (`Feature`) implemented by all domain features. Each
   feature defines an immutable `FeatureSpec` declaring its published capabilities
   (`provides`), mandatory dependencies (`requires`), and optional enhancements
   (`optional`), along with an asynchronous `start(context)` method.

3. Context (`app.kernel.context`):
   The per-feature execution environment (`FeatureContext`) providing scoped
   dependency resolution, export staging, managed effect lifecycles (reverse-order
   LIFO teardown via `AsyncExitStack`), background task spawning (`spawn`), and
   scoped event observation.

4. Event Bus (`app.kernel.events`):
   In-process asynchronous publish-subscribe observation channel (`EventBus`)
   delivering exact-type events sequentially to sync and async handlers with
   idempotent subscription disposal.

5. Runtime Bootstrapper (`app.kernel.bootstrapper`):
   The dependency resolution and lifecycle engine. It performs cycle-safe
   topological sorting with DFS reachability, dynamic subset selection
   (`enabled` and role profiles), transactional export commits, and clean LIFO
   graceful shutdown with `BaseExceptionGroup` aggregation.

6. Structured Logging (`app.kernel.logging`):
   Inert, asynchronous, and sanitized structured logging with zero import-time
   side effects, non-blocking queue sinks, automatic credential/secret redaction,
   and crash-resilient ZIP log rotation.

Note:
    This file is strictly docstring-only. In accordance with architectural boundary
    rules, it contains zero imports, runtime registration, or side effects.
"""

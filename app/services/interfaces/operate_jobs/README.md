# FEAT-IFACE-OPERATE_JOBS

Provides `interfaces.operate-jobs@1` as a translation-only boundary over `orchestration.manage-jobs@1`, `orchestration.resource-admission@1`, and `orchestration.local-workers@1`.

Phase 1 exposes current job semantic/control projections, supported owner controls, bounded resource snapshots, and local-worker readiness. It preserves attempt/fence/control/outcome fields and never creates a second scheduler or browser-to-worker channel. Remote-worker registration/heartbeat/quarantine operations remain unqualified until their later semantic owner exists.

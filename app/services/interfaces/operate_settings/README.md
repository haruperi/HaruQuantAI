# FEAT-IFACE-OPERATE_SETTINGS

Provides `interfaces.operate-settings@1` as a translation-only boundary. Settings mutations preserve the Workspace owner's expected-revision/validation semantics; no settings database or policy is duplicated here. Diagnostic snapshots/comparisons/exports delegate to `workspace.build-diagnostics@1`; the gateway exposes only bounded redacted owner results. Secret values and unrestricted host paths are never introduced by the Interface layer, and provider loss returns `CAPABILITY_UNAVAILABLE` rather than selecting a substitute.

# FEAT-WS-BUILD_DIAGNOSTICS

Selected owner for `workspace.build-diagnostics@1`. Health/readiness remains explicit (`READY`, `DEGRADED`, `UNAVAILABLE`, `UNKNOWN`); missing evidence is never converted to healthy/zero/pass. Diagnostic text is redacted and bounded before archive generation. Benchmark targets and measurements are separate and qualify as comparable only when their complete fixture/build/runtime/hardware/resource/method identities and units match.

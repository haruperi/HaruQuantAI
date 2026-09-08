# FEAT-ORCH-EXECUTE_LOCAL_WORK

Provides `orchestration.local-workers@1`. Workers use the Windows-compatible `spawn` context; the importable worker module has no import-time effects. Large inputs are staged once into owned shared memory and verified by SHA-256 in the child. Every completion is fenced against the current Task 1.18 attempt/fence, and cancellation cooperates through a spawn-safe event before bounded termination. Worker capacity is admitted and released through the single Task 1.14 resource ledger.

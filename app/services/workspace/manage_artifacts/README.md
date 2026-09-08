# FEAT-WS-MANAGE_ARTIFACTS

Provides `workspace.artifacts@1` for immutable byte custody. The feature derives its custody root from the validated workspace path (`<workspace>/artifacts`) and accepts no host path from public callers. Publication validates declared byte count and SHA-256 before atomic same-filesystem replacement, persists immutable metadata through `workspace.persistence@1`, and uses `orchestration.resource-admission@1` for bounded staging work.

Downloads require an exact account/principal/expiry/content-hash grant. References and legal holds block cleanup. Removing this provider retains committed bytes and metadata.

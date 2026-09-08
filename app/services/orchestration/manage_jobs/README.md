# FEAT-ORCH-MANAGE_JOBS

Provides `orchestration.manage-jobs@1` as the durable shared authority for logical job identity, attempts, control intent/acknowledgement, progress, domain outcome, retry lineage, and receiver-effect reconciliation.

Acceptance persists immutable request identity and enqueue intent before returning. Terminal retry creates a linked new attempt/fence; it never reopens the terminal attempt. Domain outcome is orthogonal to infrastructure state, so a worker-complete Agentic `REFUSED` remains visibly refused. Pause is allowed only when the submitted owner declares checkpoint support. Observer queues are bounded and never own durable truth.

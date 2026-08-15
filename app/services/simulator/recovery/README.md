# Session Recovery

`FEAT-SIM-13` owns canonical Simulator replay identity, hash-linked secured
session checkpoints, recovery-state verification, practice-branch isolation,
scored-session anti-rewind policy, integrity failure, and explicit rearm.
Existing in-process live what-if sessions remain non-durable.

## Trading cutover authority invariants

Canonical request v2 recovery begins from the same complete
`initial_authority_state_hash` snapshot used to initialize Trading and Simulation.
The snapshot contains exact account, order, position, deal, and ownership facts;
missing or different material is checkpoint-incompatible. Account ownership proves
an exclusive run interval or the injected activity port supplies the complete
contiguous foreign/manual source sequence before execution. Unknown, missing,
gapped, or conflicting activity blocks recovery and mutation. Protection and
terminal effects remain `protection_trigger` plus `authority_deal` journal
evidence, so replay never reclassifies them as client submissions.

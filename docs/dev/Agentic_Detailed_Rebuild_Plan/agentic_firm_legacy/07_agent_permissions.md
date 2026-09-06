# Agent Permissions Policy

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-013`–`015`

## Policy model

Permissions are enforced by Agentic's own capability policy enforcement point.
Risk remains the authority for economic and trading risk; UI/API remains the
authority for human authentication. Caller-supplied agent text is never trusted
authorization context.

`authorize_tool_call` evaluates:

- Authenticated principal and `AuthContext`
- Firm mandate/version
- Role manifest/version and feature status
- Tool policy/version and permission class
- Environment, asset, account, data, and operation scope
- Workflow state and task identity
- Required approval attestation
- Tool, token, cost, and time budget
- Kill-switch and receiver-domain readiness where applicable

Any missing or mismatched fact returns a typed denial.

## Permission classes

| Class | Meaning | Agentic use |
|---|---|---|
| `read_evidence` | Read bounded governed evidence | Allowed by explicit scope |
| `compute_deterministic` | Invoke pure or read-only calculations | Allowed by explicit scope |
| `write_working` | Write task-scoped working state | Allowed with TTL and audit |
| `write_staging` | Write isolated Agentic staging artefacts | Human specification required |
| `submit_proposal` | Submit an untrusted typed request to a deterministic receiver | Explicit workflow and receiver scope |
| `controlled_mutation` | Change governed deterministic or external state | Never granted to an agent |
| `critical` | Broker, risk override, kill switch, credential, production deployment | Absent from Agentic registry |

## Approval attestations

An approval contains principal, permission, exact object/hash, workflow/run,
environment, account/asset scope, issued/expiry time, nonce, policy version, and
signature or trusted identity proof. It is single-use and checked by the receiver.

Natural-language approval, a copied token, a Boolean model field, a peer message,
or an agent-created object is not an attestation.

## Separation of duties

- Planner selects work; it cannot approve results.
- Proposer and critic are separate role instances for governed promotion.
- Model-evaluated output also requires deterministic and human evidence where
  specified.
- The coder cannot promote.
- The risk critic cannot approve risk.
- The trader role cannot execute.
- The Firm Coordinator cannot grant itself capabilities.

## Registry validation

Startup rejects duplicate identities, unknown features, missing schemas, wildcard
account/environment scope, unpinned model profiles, critical tools, live broker
imports, self-approval, or an agent/tool map not covered by the mandate.

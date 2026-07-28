# Agentic Security Threat Model

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-013`–`018`, `046`–`048`, `061`–`063`;
> `NFR-AGENTIC-001`

## Protected assets

Mandates, approvals, identities, credentials, market and account data, prompts,
model/tool registries, evidence, memory, workflow state, generated code, promotion
signatures, deterministic services, and trading infrastructure.

## Threats and required controls

| Threat | Controls |
|---|---|
| Goal or instruction hijack | instruction/evidence separation, extraction, allowlists, typed output, refusal |
| Tool misuse | deny-default policy, capability scopes, trusted context, idempotency, audit |
| Identity or privilege abuse | authenticated `AuthContext`, signed scoped attestations, no agent delegation |
| Tool/model/supply-chain poisoning | version/hash registry, dependency lock, SBOM, signature, regression |
| Unexpected code execution | isolated sandbox, no credentials/network, resource and syscall boundaries |
| Memory/context poisoning | provenance, trust/injection labels, immutable corrections, TTL working memory |
| Insecure inter-agent communication | typed messages, sender/recipient/task binding, hashes, size limits |
| Cascading/runaway failure | fan-out/round/retry/cost limits, backpressure, cancellation, circuit breakers |
| Human trust exploitation | evidence/dissent display, proposal labels, authenticated approval UI |
| Rogue or drifted agent | continuous evaluation, quarantine, permission revocation, rollback |
| Data exfiltration | egress denial, DLP/redaction, bounded telemetry, secret isolation |
| Cross-account leakage | per-account namespace, scope, credentials, memory, approval, and audit isolation |

## Incident response

Detection triggers automatic cancellation or quarantine according to severity,
revokes active capability leases, preserves immutable evidence, blocks replayed
approvals, alerts the operator, and requires a covering regression case before
reenablement.

Agentic incident handling cannot disable Risk or Trading kill-switch functions.

## Standards references

- [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [NIST AI Risk Management Framework](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
- [NIST Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)
- [Model Context Protocol security guidance](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)

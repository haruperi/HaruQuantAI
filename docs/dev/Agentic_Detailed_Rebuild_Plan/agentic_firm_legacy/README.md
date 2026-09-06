# Agentic Firm Supporting Specifications

> **Status:** Active supporting documentation
>
> The sole Feature Registry, public API, contract, and functional-requirement
> authority is `app/agentic/README.md`. These files elaborate that canonical
> specification. They do not own an alternate registry or requirement namespace.

## Document map

| Document | Purpose |
|---|---|
| `01_constitution.md` | Immutable authority and safety laws |
| `02_firm_mandate_spec.md` | Machine-readable operating mandate |
| `03_risk_policy.md` | Boundary between advisory agents and deterministic risk |
| `04_evaluation_standard.md` | Reliability, safety, economic, and ablation evidence |
| `05_implementation_plan.md` | Documentation-first build sequence |
| `06_acceptance_criteria.md` | End-state gates and negative tests |
| `07_agent_permissions.md` | Deny-by-default capability and approval policy |
| `08_strategy_lifecycle.md` | Agent-authored artefact lifecycle |
| `09_coder_agent_governance.md` | Sandboxed generation and promotion rules |
| `10_agent_standard.md` | Standard for each specialized role |
| `11_tool_standard.md` | Standard for agent-callable tools |
| `12_orchestration_runtime.md` | Durable Google ADK workflow runtime |
| `13_firm_organization_and_deliberation.md` | Firm departments and bounded discussion |
| `14_google_adk_and_model_providers.md` | ADK selection and provider-neutral model layer |
| `15_memory_context_and_evidence.md` | Context, memory, provenance, and retention |
| `16_security_threat_model.md` | Agentic threat model and controls |
| `17_observability_and_operations.md` | Tracing, SLOs, incidents, replay, and recovery |
| `18_data_readiness_standard.md` | Preconditions for evidence-dependent agents |
| `research/` | Research prompt and retained consolidated report |

## Authority rules

- Current features, statuses, public APIs, contracts, and requirements live only
  in `app/agentic/README.md`.
- System relationships live in `docs/PROJECT.md`.
- Cross-domain architecture lives in `docs/ARCHITECTURE.md`.
- Release-visible history lives in `docs/CHANGELOG.md`.
- Supporting documents may explain how a canonical requirement is satisfied but
  may not create `FR-AGENTIC-<AREA>-*` identifiers.
- Research material is evidence, not current system authority.

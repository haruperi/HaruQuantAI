# External Research Proposal Evaluation

`FEAT-STR-11` is Strategy's receiver-owned boundary for evaluating an untrusted
external research proposal. The proposal supplies identity and evidence references
only. Strategy resolves the registered version, validates point-in-time evidence,
runs its deterministic evaluator, and emits a canonical intent only when the
independent signal supports the requested instrument and direction.

The package exposes no class or constant through the Strategy public root. Request
and result values are constructed through standalone factory functions.

### Feature Registry

| Status | Feature | Public operations | Requirements | Usage evidence |
|---|---|---|---|---|
| Completed | `FEAT-STR-11` External Research Proposal Evaluation | `create_strategy_proposal_evaluation_request`, `create_strategy_proposal_evaluation_result`, `validate_strategy_proposal`, `evaluate_strategy_proposal`, `bind_proposal_lineage` | `FR-STR-049`–`FR-STR-053` | `tests/strategy/usage/features/11_proposal_intake.py` |

Proposal confidence, consensus, rationale, requested size, approval language, and
free text never enter deterministic evaluation or intent construction. Proposal
identity is attached only after canonical intent construction and only inside the
lineage mapping.

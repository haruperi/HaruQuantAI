# Agent-Authored Artefact Lifecycle

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-052`–`054`

Agentic owns evidence about an agent-authored artefact until a deterministic
receiver accepts a version through its public registration contract. Strategy and
Indicators retain ownership of their registries and runtime lifecycle.

## States

```text
specified
  → generated
    → mechanically_validated
      → leakage_validated
        → simulated
          → robustness_validated
            → human_review
              → receiver_submitted
                → registered

Any pre-registration state
  → research_only | rejected | retired

registered
  → suspended | retired
```

## Rules

- Transitions are append-only, version-specific, and non-skippable.
- Mechanical failures may enter a bounded repair loop counted against search
  budgets.
- Leakage, holdout reuse, missing provenance, search-budget exhaustion, or absent
  approval terminates as `research_only`; no prompt repair can change that fact.
- Material code, dependency, data, prompt, model, or specification changes create a
  new version and restart at the documented entry state.
- Registration is not activation. Receiver-owned Strategy, Portfolio, Risk,
  Trading, and human gates remain separate.
- Automatic demotion triggers include evidence invalidation, drift, incident,
  dependency vulnerability, failed replay, or receiver suspension.
- No agent can transition an artefact into `registered`.

## Promotion evidence

The packet includes specification, code and dependency hashes, SBOM, provenance,
all attempted variants, test and mutation evidence, causality/leakage evidence,
simulation and optimization references, null-data result, robustness critique,
known limitations, receiver compatibility, authenticated human approval, and
expiry.

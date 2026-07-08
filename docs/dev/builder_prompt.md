# Prompt for Building Phase 5: Risk Governance Upgrade

Copy and paste this prompt when starting the AI build session for the Risk Governance upgrade.

---

## Task Objective
You are tasked with upgrading the existing Risk Governance domain (`app/services/risk/` v1) to the new structure specified in the architecture requirements document: [05-risk.md](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/phase-implementation-plan/05-risk.md).

This is a modular upgrade. We are transitioning from a single-folder flat list of files in v1 to a structured, multi-module package. 
* **Precedence:** Precedence is given to the functional requirements of version 2.
* **No Backward Compatibility:** Do not keep backward compatibility where v2 overrides v1.
* **No Skipped Functionality:** Ensure that all business logic and capabilities covered in version 1 are preserved and integrated into the corresponding version 2 files.

---

## 10-Step Workflow per Module
Execute this sequence module-by-module. Do not start a new module until the current module is fully completed, tested, and validated.

1. **Implement Functional Requirements:** Create or update the v2 module files as specified in Section 3 of [05-risk.md](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/phase-implementation-plan/05-risk.md).
2. **Review v1 Logic & Cleanup:** Open the corresponding old v1 file(s). Compare the logic to ensure no functionality is skipped. Port any missing v1 business logic to the new v2 files, then **delete** the old v1 file(s) from the root of `app/services/risk/`.
3. **Google Standard Docstrings:** Document all modules, classes, and functions using the Google Python Style Guide docstring format (including types, arguments, returns, and exceptions raised).
4. **Strict Logging:** Log every function using the custom system logger (`from app.utils.logger import logger`).
   * Every function must have at least one log.
   * If a function has no specific steps to log, log what the function did (e.g. input/output summary).
   * Use `info` level for routine operational milestones (e.g., successful policy resolution or gate validation).
   * Use `debug` level for granular information (e.g., intermediate matrix steps or calculations).
5. **Unit Tests (> 80% Coverage):** Add or update unit tests under `tests/risk/unit/`. Run tests and ensure the coverage for each new/modified file is greater than 80%.
6. **Usage Examples:** Add a dedicated function inside [05_risk.py](file:///c:/Users/rharu/AppDev/HaruquantAI/tests/usage/05_risk.py) for the current module.
   * Use the naming convention: `example_{#}_{module_name}()` (e.g., `example_01_readiness()`).
   * Structure it so it can be run independently or sequentially. Reference [02_data.py](file:///c:/Users/rharu/AppDev/HaruquantAI/tests/usage/02_data.py) for the style.
7. **Update Module README:** Add or update a README inside the module folder explaining its boundary role, interfaces, and options.
8. **Update Changelog & Traceability:** Document the structural changes and functionality updates in `docs/dev/phase-implementation-plan/CHANGELOG.md`. Also, update the implementation file [05-risk.md](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/phase-implementation-plan/05-risk.md) by marking `[X]` for all completed requirements and sub-items. For each completed requirement, add implementation proof directly in the format `*Evidence: <file_path> line <start>-<end>*` (e.g. `*Evidence: app/services/risk/models/contracts.py line 96-113*`). For requirements with multiple grouped items, write evidence on each item. Ensure line numbers are exact rather than referencing the entire file.
9. **Quality Checks:** Run the following commands in the workspace and verify all checks pass:
   * `uv run ruff check --fix .`
   * `uv run ruff format .`
   * `uv run mypy .`
   * `pre-commit run --all-files` (or relevant pre-commit checks).
10. **Draft Commit Message:** Output a clean, structured git commit message summarizing the changes for this module. **Do NOT run `git commit` automatically; the user will review and commit manually.**

---

## Formatting and Linting Standards
* **Python Style:** Strict [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).
* **Formatters:** Double quotes, magic trailing commas. Run order: `ruff check --fix` -> `ruff format` -> `mypy`.
* **Typing:** Explicit type hints on all signatures. No generic `Any` types where specific models/collections can be typed.
* **Imports:** Always use absolute imports.

---

Below is the recommended **dependency-safe implementation order** for all modules and files listed under Functional Requirements in the `05-risk.md`.

The rule is:

> **Contracts first → pure engines → gate aggregation → governed orchestration → side-effect ports → reports/tools/adapters.**

## 0. Package skeleton first
### Section -> 📂 Module: `app/services/risk`

Create the folders and lightweight `__init__.py` files first, but keep them mostly empty until the public registry is finalized.

| Order | File                            | Why first                                                                                                      | Old V1 File to Clean |
| ----: | ------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------- |
|   0.1 | `app/services/risk/__init__.py` | Create as a safe placeholder only. Final exports should be added near the end after official tools are stable. | Keep placeholder (do not delete yet) |

## 1. Core models and deterministic primitives
### Section -> 📂 Module: `app/services/risk/models`

Everything else depends on these contracts, enums, and serialization helpers.

| Order | File                      | Purpose                                                                                             | Old V1 File to Clean |
| ----: | ------------------------- | --------------------------------------------------------------------------------------------------- | -------------------- |
|   1.1 | `models/enums.py`         | Risk statuses, reason codes, severity ordering, modes, lifecycle enums.                             | `app/services/risk/models.py` |
|   1.2 | `models/contracts.py`     | Canonical models: requests, snapshots, proposed trades, decisions, tokens, evidence refs, warnings. | `app/services/risk/models.py` |
|   1.3 | `models/serialization.py` | Canonical JSON-safe serialization, stable payloads, round-trip helpers.                             | `app/services/risk/models.py` |

Build tests immediately for enum values, model validation, and JSON round-trips.

## 2. Configuration profiles and hashing
### Section -> 📂 Module: `app/services/risk/config`

Policy, governor decisions, audit records, and tokens all depend on stable config hashes.

| Order | File                 | Purpose                                                                | Old V1 File to Clean |
| ----: | -------------------- | ---------------------------------------------------------------------- | -------------------- |
|   2.1 | `config/schema.py`   | Strict config schema and validation rules.                             | `app/services/risk/config.py` |
|   2.2 | `config/profiles.py` | Built-in profiles: safe default, prop firm, paper, live conservative.  | `app/services/risk/config.py` |
|   2.3 | `config/hashing.py`  | Stable config canonicalization and hash generation.                    | `app/services/risk/config.py` |
|   2.4 | `config/loader.py`   | Explicit config loading from approved sources. No import-time loading. | `app/services/risk/config.py` |

## 3. Storage ports and offline stores
### Section -> 📂 Module: `app/services/risk/storage`

Define side-effect boundaries early, but keep actual business logic independent from persistence.

| Order | File                   | Purpose                                                                    | Old V1 File to Clean |
| ----: | ---------------------- | -------------------------------------------------------------------------- | -------------------- |
|   3.1 | `storage/ports.py`     | Protocols for state store, audit sink, policy store, decision store.       | `app/services/risk/storage.py` |
|   3.2 | `storage/in_memory.py` | Deterministic in-memory implementation for tests, offline, and simulation. | `app/services/risk/storage.py` |

## 4. Policy-as-code layer
### Section -> 📂 Module: `app/services/risk/policy`

Most downstream gates need an effective policy.

| Order | File                  | Purpose                                                                      | Old V1 File to Clean |
| ----: | --------------------- | ---------------------------------------------------------------------------- | -------------------- |
|   4.1 | `policy/contracts.py` | Policy scope, precedence, expiry, enforcement result contracts.              | `app/services/risk/policy.py` |
|   4.2 | `policy/resolver.py`  | Resolve effective policy by account, strategy, symbol, mode, workflow, role. | `app/services/risk/policy.py` |
|   4.3 | `policy/overrides.py` | Override validation, approval requirement, token/config compatibility.       | `app/services/risk/policy.py` |

## 5. Phase readiness and implementation readiness checks
### Section -> 📂 Module: `app/services/risk/readiness`

This can now use models, config, and dependency-status contracts safely.

| Order | File                           | Purpose                                                                                    | Old V1 File to Clean |
| ----: | ------------------------------ | ------------------------------------------------------------------------------------------ | -------------------- |
|   5.1 | `readiness/phase_readiness.py` | Phase 5 readiness report, dependency validation, dry-run planning, mode matrix validation. | None |

## 6. Market regime gate
### Section -> 📂 Module: `app/services/risk/regime`

Build this before limits and the governor because regime status influences throttling, rejection, and allocation.

| Order | File                   | Purpose                                                                                   | Old V1 File to Clean |
| ----: | ---------------------- | ----------------------------------------------------------------------------------------- | -------------------- |
|   6.1 | `regime/validation.py` | Validate market evidence, freshness, quote shape, closed-bar assumptions.                 | `app/services/risk/regime.py` |
|   6.2 | `regime/assessor.py`   | Spread, volatility, liquidity, rollover, session, news, stale-data regime classification. | `app/services/risk/regime.py` |

## 7. Position sizing engine
### Section -> 📂 Module: `app/services/risk/sizing`

Sizing should stay pure and deterministic. Normalization is separate so broker-compatible rounding does not pollute sizing math.

| Order | File                      | Purpose                                                                                              | Old V1 File to Clean |
| ----: | ------------------------- | ---------------------------------------------------------------------------------------------------- | -------------------- |
|   7.1 | `sizing/contracts.py`     | Sizing request/result contracts and sizing method enum.                                              | `app/services/risk/sizing.py` |
|   7.2 | `sizing/normalization.py` | Volume precision, lot-step flooring, symbol metadata validation.                                     | `app/services/risk/sizing.py` |
|   7.3 | `sizing/calculators.py`   | Fixed-risk, fractional, volatility-adjusted, correlation-adjusted, milestone, advisory Kelly sizing. | `app/services/risk/sizing.py` |

## 8. Currency exposure engine
### Section -> 📂 Module: `app/services/risk/exposure`

Portfolio exposure and concentration gates depend on this.

| Order | File                      | Purpose                                                                             | Old V1 File to Clean |
| ----: | ------------------------- | ----------------------------------------------------------------------------------- | -------------------- |
|   8.1 | `exposure/fx_legs.py`     | FX symbol parsing and base/quote leg decomposition.                                 | `app/services/risk/exposure.py` |
|   8.2 | `exposure/aggregation.py` | Currency exposure aggregation across open, pending, in-flight, and proposed trades. | `app/services/risk/exposure.py` |

## 9. Correlation engine
### Section -> 📂 Module: `app/services/risk/correlation`

Correlation depends on return-series construction and fallback behavior.

| Order | File                       | Purpose                                                                       | Old V1 File to Clean |
| ----: | -------------------------- | ----------------------------------------------------------------------------- | -------------------- |
|   9.1 | `correlation/returns.py`   | Closed-bar returns, alignment, minimum-sample validation.                     | `app/services/risk/correlation.py` |
|   9.2 | `correlation/fallbacks.py` | Missing-data and insufficient-sample fallback resolution.                     | `app/services/risk/correlation.py` |
|   9.3 | `correlation/engine.py`    | Correlation matrix, cluster exposure, correlation impact, dynamic thresholds. | `app/services/risk/correlation.py` |

## 10. Tail-risk engines
### Section -> 📂 Module: `app/services/risk/tail_risk`

VaR and Expected Shortfall are independent pure calculators and are needed by limits and governor review.

| Order | File                              | Purpose                                                           | Old V1 File to Clean |
| ----: | --------------------------------- | ----------------------------------------------------------------- | -------------------- |
|  10.1 | `tail_risk/contracts.py`          | VaR/ES request, snapshot, method, and assumptions contracts.      | `app/services/risk/var_es.py` |
|  10.2 | `tail_risk/var.py`                | Parametric, historical, and Monte Carlo VaR calculations.         | `app/services/risk/var_es.py` |
|  10.3 | `tail_risk/expected_shortfall.py` | Historical and parametric Expected Shortfall / CVaR calculations. | `app/services/risk/var_es.py` |

## 11. Stress testing engine
### Section -> 📂 Module: `app/services/risk/stress`

Stress results are stronger tail-risk gates than VaR alone, so this must be ready before final limit checks.

| Order | File                  | Purpose                                                        | Old V1 File to Clean |
| ----: | --------------------- | -------------------------------------------------------------- | -------------------- |
|  11.1 | `stress/contracts.py` | Stress scenario, request, result, and summary contracts.       | `app/services/risk/stress.py` |
|  11.2 | `stress/registry.py`  | Built-in stress scenario registry and scenario lookup.         | `app/services/risk/stress.py` |
|  11.3 | `stress/engine.py`    | Scenario application, stress-loss calculation, stress summary. | `app/services/risk/stress.py` |

## 12. Feasibility gates
### Section -> 📂 Module: `app/services/risk/feasibility`

These are practical execution feasibility checks, still without broker mutation.

| Order | File                            | Purpose                                                                       | Old V1 File to Clean |
| ----: | ------------------------------- | ----------------------------------------------------------------------------- | -------------------- |
|  12.1 | `feasibility/margin.py`         | Margin projection, free-margin impact, leverage and broker-constraint checks. | `app/services/risk/margin.py` |
|  12.2 | `feasibility/drawdown.py`       | Drawdown state, throttling multiplier, daily/total drawdown gates.            | `app/services/risk/drawdown.py` |
|  12.3 | `feasibility/execution_gate.py` | Spread, slippage, stop-level, freeze-level, marketability checks.             | `app/services/risk/execution_gate.py` |

## 13. Limit engine
### Section -> 📂 Module: `app/services/risk/limits`

Build contracts first, then individual checks, then ordered aggregation.

| Order | File                  | Purpose                                                                                                 | Old V1 File to Clean |
| ----: | --------------------- | ------------------------------------------------------------------------------------------------------- | -------------------- |
|  13.1 | `limits/contracts.py` | Limit check/result contracts and ordered-check registry shape.                                          | `app/services/risk/limits.py` |
|  13.2 | `limits/checks.py`    | Pure checks: kill-switch, stale evidence, loss, exposure, VaR/ES, stress, margin, execution, frequency. | `app/services/risk/limits.py` |
|  13.3 | `limits/engine.py`    | Ordered limit evaluation, primary failure selection, composite breach flags.                            | `app/services/risk/limits.py` |

## 14. Governance-specific review modules
### Section -> 📂 Module: `app/services/risk/governance`

These support non-trade workflows and special governance states.

| Order | File                        | Purpose                                                                                       | Old V1 File to Clean |
| ----: | --------------------------- | --------------------------------------------------------------------------------------------- | -------------------- |
|  14.1 | `governance/allocation.py`  | Allocation review, equal-risk allocation, volatility parity, correlation-adjusted allocation. | `app/services/risk/allocation.py` |
|  14.2 | `governance/lifecycle.py`   | Strategy admission, live readiness, lifecycle transition validation.                          | `app/services/risk/lifecycle.py` |
|  14.3 | `governance/kill_switch.py` | Kill-switch state checks, trigger requests, resume validation, approval-cleared recovery.     | `app/services/risk/kill_switch.py` |

## 15. Decision synthesis
### Section -> 📂 Module: `app/services/risk/governor`

This should come before the full governor because it converts many gate results into one deterministic decision package.

| Order | File                             | Purpose                                                                                          | Old V1 File to Clean |
| ----: | -------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------- |
|  15.1 | `governor/decision_synthesis.py` | Final decision status, primary reason, reductions, token eligibility, decision package assembly. | `app/services/risk/governor.py` |

## 16. Audit and decision-token layer
### Section -> 📂 Module: `app/services/risk/audit`

These are governed side-effect support systems. They should not be needed by pure engines.

| Order | File                  | Purpose                                                                             | Old V1 File to Clean |
| ----: | --------------------- | ----------------------------------------------------------------------------------- | -------------------- |
|  16.1 | `audit/hash_chain.py` | Genesis hash, append hash, chain verification, tamper detection.                    | `app/services/risk/audit.py` |
|  16.2 | `audit/tokens.py`     | Decision-token signing, expiry, scope, revocation, policy/config hash verification. | `app/services/risk/audit.py` |
|  16.3 | `audit/events.py`     | Redacted audit payloads, audit event creation, hash-chain attachment.               | `app/services/risk/audit.py` |

## 17. Observability boundary
### Section -> 📂 Module: `app/services/risk/observability`

Apply observability at service/tool boundaries, not inside pure calculators.

| Order | File                          | Purpose                                                                         | Old V1 File to Clean |
| ----: | ----------------------------- | ------------------------------------------------------------------------------- | -------------------- |
|  17.1 | `observability/metrics.py`    | Metrics sink protocol, decision metrics, latency metrics, audit-health metrics. | None |
|  17.2 | `observability/decorators.py` | Logging, latency, error, and metrics decorators for public boundaries.          | None |

## 18. Reports
### Section -> 📂 Module: `app/services/risk/reports`

Build report composition first, then explicit file export.

| Order | File                  | Purpose                                                                            | Old V1 File to Clean |
| ----: | --------------------- | ---------------------------------------------------------------------------------- | -------------------- |
|  18.1 | `reports/builder.py`  | Build JSON-safe, redacted risk reports from stored evidence.                       | `app/services/risk/reports.py` |
|  18.2 | `reports/exporter.py` | Authorized report writing, safe path validation, overwrite policy, write receipts. | `app/services/risk/reports.py` |

## 19. Canonical governor orchestration
### Section -> 📂 Module: `app/services/risk/governor`

Now all downstream engines and side-effect boundaries exist.

| Order | File                   | Purpose                                                                                                              | Old V1 File to Clean |
| ----: | ---------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------- |
|  19.1 | `governor/governor.py` | Canonical orchestration for trade review, allocation review, strategy admission, live readiness, portfolio governor. | `app/services/risk/governor.py` |

This file should not implement new math. It should coordinate previously built modules.

## 20. Official tool boundary
### Section -> 📂 Module: `app/services/risk/tools`

Only after the governor and pure engines are stable should you expose public tool wrappers.

| Order | File                | Purpose                                                             | Old V1 File to Clean |
| ----: | ------------------- | ------------------------------------------------------------------- | -------------------- |
|  20.1 | `tools/registry.py` | Official risk tool catalogue, metadata validation, drift detection. | None |
|  20.2 | `tools/official.py` | Official AI-callable risk tools returning standard envelopes.       | None |

## 21. Public package export
### Section -> 📂 Module: `app/services/risk`

Finalize the root package only after official tools and registry are stable.

| Order | File                            | Purpose                                                 | Old V1 File to Clean |
| ----: | ------------------------------- | ------------------------------------------------------- | -------------------- |
|  21.1 | `app/services/risk/__init__.py` | Final explicit public exports and `__all__` validation. | Delete old root file at step completion |

## 22. Agentic adapter last
### Section -> `agentic/tools/risk.py`

This must be last because it should only attach already-approved official tools.

| Order | File                    | Purpose                                                                 | Old V1 File to Clean |
| ----: | ----------------------- | ----------------------------------------------------------------------- | -------------------- |
|  22.1 | `agentic/tools/risk.py` | Narrow agent adapter that imports the official Risk tool registry only. | None |

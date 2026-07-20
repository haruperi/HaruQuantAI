# ROLE

You are a senior Python software architect writing the **final domain README before implementation**.

This README will be the domain’s single source of truth for:

* final requirements;
* package structure;
* implementation sequence;
* workflows;
* public classes and functions;
* dependencies;
* configuration and limits;
* side effects and errors;
* usage examples;
* tests;
* completion status.

# DOMAIN

* **Domain name:** `[DOMAIN_NAME]`
* **Domain ID:** `[DOM]`
* **Final package path:** `[FINAL_PACKAGE_PATH]`
* **Final README path:** `[FINAL_PACKAGE_PATH]/README.md`

# INPUT DOCUMENTS

## Primary sources

The README is written from these:

1. **Top-level system documentation:**
   `[PATH_TO_SYSTEM_DOCUMENT]`

2. **Final domain README template:**
   `[PATH_TO_FINAL_README_TEMPLATE]`

3. **V1–V2 reconciliation document:**
   `[PATH_TO_RECONCILIATION_DOCUMENT]`

## Reference-only sources

Consult these **only** to elaborate items the reconciliation has already approved — for example, exact signatures, side effects, error types, and configuration names of reused V1 code, or the full requirement text of retained V2 requirements:

4. **Version 1 audit report:**
   `[PATH_TO_V1_AUDIT_REPORT]`

5. **Version 2 requirements document:**
   `[PATH_TO_V2_REQUIREMENTS]`

Reference-only sources must never introduce, restore, or override behaviour. If the reconciliation removed, rejected, or deferred something, it stays out of the README regardless of what these documents say. If a needed decision is absent from the reconciliation, add it to Open Decisions — do not derive it from V1 or V2 directly.

Do not modify any input document.

# SOURCE AUTHORITY

Use this authority order:

```text
1. Top-level system documentation
   → Defines domain boundaries, ownership, dependencies,
     shared contracts, and cross-domain workflows.

2. V1–V2 reconciliation
   → Defines approved Keep, Modify, Remove, Add, Merge,
     Split, Defer, and Reject decisions.
   → The only source of WHAT goes into the README.

3. V1 audit report (reference only)
   → Supplies implementation detail — signatures, side effects,
     errors, dependencies — for V1 behaviour the reconciliation
     approved for reuse or modification.

4. V2 requirements (reference only)
   → Supplies full requirement text for V2 requirements the
     reconciliation retained.

5. Final README template
   → Defines the required output format.
```

Reference-only sources supply detail for approved decisions; they carry no decision authority of their own.

When the documents conflict, do not silently choose one.

Follow the reconciliation decision. If the reconciliation does not resolve the conflict, add it to **Open Decisions**.

# GOAL

Create the final domain `README.md` that defines the approved target system before implementation begins.

The README must combine:

```text
Approved V1 behaviour to preserve
+ approved V1 behaviour to modify
+ approved V2 behaviour to add
- removed, rejected, and deferred behaviour
= final domain specification
```

The final README must describe the system that should exist after migration.

It must not simply describe Version 1, repeat Version 2, or copy the reconciliation document.

# MINIMAL STRUCTURE

Use only this structural model:

```text
Package
└── Module folder
    └── File
        └── Public Class / Function / Method / Constant
```

Interpret it as:

```text
Package
= Domain

Module folder
= Feature / capability

File
= Use case or focused responsibility

Public class / function / method
= Functional requirement behaviour
```

Do not introduce additional structural layers unless an approved reconciliation decision explicitly requires them.

# CORE RULES

1. Write the README before implementation.
2. Use the supplied final README template exactly as the structural base.
3. Define only the approved final system.
4. Do not copy obsolete Version 1 structure into the final design automatically.
5. Do not copy rejected or excessive Version 2 architecture into the README.
6. Preserve valuable Version 1 behaviour where approved.
7. Reorganize preserved behaviour into the final minimal structure.
8. Every module folder must represent one coherent feature.
9. Every file must have one focused responsibility.
10. Several related requirements may exist in one file.
11. Do not create one file for every function.
12. Use functions for stateless behaviour by default.
13. Use a class only when it genuinely owns:

    * state;
    * injected dependencies;
    * several closely related operations; or
    * a lifecycle.
14. Private helpers are implementation details and should not receive requirement IDs unless independently required.
15. Every public class, function, method, or constant must appear in exactly one functional requirement row.
16. Every approved final functional requirement must map to a public symbol.
17. Every requirement must support:

    * a real workflow;
    * a domain responsibility;
    * a safety or quality rule; or
    * a documented external contract.
18. Do not add generic managers, services, handlers, factories, repositories, ports, adapters, or coordinators without an approved demonstrated need.
19. Do not write production code.
20. Do not invent unresolved behaviour.
21. Do not silently omit any approved reconciliation decision.
22. Keep the README minimal and implementation-ready.

# STATUS RULES

Use only:

```text
Missing
Partial
Completed
```

Assign status using evidence, not intention.

## Completed

Use `Completed` only when the existing Version 1 implementation:

* already matches the approved final behaviour;
* is located in, or will remain compatible with, the final structure;
* has confirmed runtime usage where applicable;
* has sufficient tests;
* satisfies the final inputs, outputs, errors, side effects, and boundaries.

## Partial

Use `Partial` when:

* useful Version 1 behaviour exists;
* some final behaviour is already implemented;
* but refactoring, relocation, validation, tests, contracts, or error handling are still required.

## Missing

Use `Missing` when:

* the behaviour does not exist;
* the existing behaviour conflicts with the final requirement;
* the behaviour must be replaced;
* evidence is insufficient;
* an open decision blocks implementation;
* or required tests do not exist.

Do not mark a requirement `Completed` merely because a similarly named function exists.

# README CREATION PROCESS

## Step 1 — Establish the final domain boundary

From the top-level system document, extract:

* domain purpose;
* responsibilities owned by the domain;
* responsibilities explicitly outside the domain;
* upstream domains;
* downstream domains;
* cross-domain inputs;
* cross-domain outputs;
* shared contracts;
* domain dependency position.

The final README must not contradict the top-level system document.

## Step 2 — Extract approved final capabilities

From the reconciliation document, collect only capabilities classified as:

```text
Keep
Modify
Add
Merge
Split
```

Handle other decisions as follows:

| Decision          | README treatment                                                                   |
| ----------------- | ---------------------------------------------------------------------------------- |
| **Remove**        | Exclude from the final package structure                                           |
| **Reject**        | Exclude from the final requirements                                                |
| **Defer**         | Exclude from initial implementation; mention briefly under limitations when useful |
| **Open Decision** | Add under Open Decisions; do not invent the affected design                        |

Every retained capability must become one module folder unless it is too small to justify a separate module and can cleanly belong to another approved feature.

## Step 3 — Design the package capability map

Create the required diagram showing:

```text
Domain package
→ feature module folders
→ focused files
```

Keep it high-level.

Do not include classes, functions, infrastructure layers, or private helpers in this diagram.

## Step 4 — Design the final package structure

Create the complete intended package tree.

Arrange module folders from lowest dependency to highest dependency.

Inside every module, arrange files from lowest dependency to highest dependency.

The order must represent the intended implementation sequence.

The package root should normally contain:

```text
[domain]/
├── __init__.py
├── README.md
└── [feature modules]/
```

Each feature module should normally contain:

```text
[module]/
├── __init__.py
└── [focused files].py
```

Usage examples must not be placed in the production package.

They belong under:

```text
tests/[domain]/usage/
```

## Step 5 — Create the module dependency diagram

Create the required Mermaid diagram showing how feature modules depend on one another.

Use this direction:

```text
Required module
→ consuming module
```

Ensure that:

* it matches the module ordering in the README;
* circular dependencies do not exist;
* dependencies are necessary and minimal.

## Step 6 — Define final workflows

Include both:

### Internal workflows

Workflows completed entirely inside the domain.

Document them fully.

### Cross-domain workflows

Workflows where the domain receives input from or produces output for another domain.

Document only:

```text
Input boundary
→ this domain’s responsibilities
→ output boundary
```

Do not describe another domain’s internal implementation.

For every workflow define:

* status;
* workflow ID (format: `WF-[DOM]-NNN`);
* scope;
* trigger or input boundary;
* participating requirements;
* final result or output boundary;
* failure behaviour;
* integration-test location.

For every cross-domain workflow, cite the `SYS-WF-*` ID(s) from the top-level system document in which this domain participates.

Use:

```text
tests/[domain]/integration/
```

Add the required workflow diagram:

* use a flowchart for straightforward processing;
* use a sequence diagram when calls, responses, events, or external interactions matter.

## Step 7 — Define each feature module

For every approved module folder, populate:

* purpose;
* module flow;
* files in dependency order;
* file responsibilities;
* key exports;
* dependencies;
* configuration and limits;
* file-level functional requirements;
* rules;
* implementation notes;
* usage examples;
* unit tests.

Do not repeat the same requirement in several sections.

## Step 8 — Define file responsibilities

For every proposed file, state one focused responsibility.

Use the V1 audit and reconciliation to determine whether the file is:

* reused;
* refactored;
* replaced;
* merged;
* split;
* or newly created.

Do not expose those migration labels as separate architectural layers.

Mention reuse guidance briefly under **Implementation notes** where useful.

Example:

```text
Reuse the validated calculation logic from V1 `position_size.py`,
but expose it through the final `calculate_position_size()` contract.
```

## Step 9 — Define key exports

For every file, list only its intended public exports:

* classes;
* functions;
* methods exposed through a public class;
* constants;
* enums;
* public contracts.

Do not include private helpers.

The module `__init__.py` must expose only the approved public feature API.

The package `__init__.py` must expose only the approved domain-level API.

### Shared contracts

* Define fully every cross-domain contract this domain **owns** per the system contract table (commands/requests it receives, events/results it produces, channels it provides), including the contract version.
* Reference — never redefine — contracts owned by other domains that this domain consumes.
* Contract definitions here must match the name, version, and owner recorded in the top-level system document.

## Step 10 — Define dependencies

For every file, list dependencies in this exact order:

```text
Standard library:
Required third-party:
Local:
```

Example:

```text
Standard library: dataclasses, decimal
Required third-party: pandas
Local: models.py → OrderRequest; validation.py → validate_order
```

Rules:

* list only dependencies that are actually expected;
* do not list optional or speculative libraries;
* identify imported local symbols;
* avoid provider-specific dependencies unless approved;
* prevent circular imports.

## Step 11 — Define configuration and limits

Place feature-specific settings inside the owning module’s **Configuration and Limits Manifest**.

Use these columns:

```text
Status
Setting / Limit
Type
Default
Required
Used by
Description
```

Every limit must state:

* what it controls;
* which symbol enforces it;
* what happens when it is exceeded.

Place settings shared by several modules under package-wide requirements and shared configuration.

Do not duplicate the same setting in several module manifests.

### Persisted state

If the domain persists state, declare the tables, artifact schemas, and migration definitions it owns, consistent with the data ownership table in the top-level system document. Only this domain writes that state; other domains read it through this domain's public contracts.

## Step 12 — Write final functional requirements

For every public symbol, create one requirement row containing:

```text
Status
Requirement ID
Responsibility
Class / Function / Method
Side Effects
Raises
Usage / Test
```

Requirement IDs use the format `FR-[DOM]-NNN`.

Write requirements as observable behaviour.

Recommended format:

```text
The system shall [perform behaviour] when [condition],
producing [result] while enforcing [constraint].
```

Do not use vague requirements such as:

```text
Handle orders.
Manage state.
Support validation.
Process data.
```

Use precise behaviour such as:

```text
The system shall reject an order whose volume is below the
instrument minimum before any broker mutation is attempted.
```

## Step 13 — Define symbol signatures

For every public function or method, provide an intended typed signature:

```python
function_name(arg: InputType) -> ResultType
```

For constants:

```python
CONSTANT_NAME: Type
```

For classes, document public methods separately when they represent separate functional requirements.

Do not define every private method.

## Step 14 — Define side effects

Use the smallest accurate label:

```text
None
Read-only
Local state mutation
Persistence write
External API call
Broker mutation
Event publication
```

Combine labels only when necessary:

```text
Broker mutation; persistence write
```

Differentiate broker reads from broker mutations.

Never leave side effects ambiguous for externally visible behaviour.

## Step 15 — Define errors

For every public functional requirement, list:

```text
[ErrorType]: [exact condition]
```

Examples:

```text
ValueError: volume is zero or negative
TradingError: broker rejects the submitted order
ConfigurationError: required limit is missing
```

Use `None` only when no domain-relevant exception is expected.

Do not expose raw provider SDK exceptions in public contracts unless explicitly approved.

## Step 16 — Define usage examples

Every registered feature must map to exactly one standalone program under:

```text
tests/[domain]/usage/
```

Use one numbered usage file per `FEAT-[DOM]-NN`, in feature order:

```text
tests/[domain]/usage/NN_[feature_name].py
```

Use one example function per public operation or constructor and call them from a
single entry point:

```python
def example_[function]() -> None:
    """Demonstrate FR-[DOM]-NNN."""


def main() -> None:
    """Run every example for this feature."""
```

Usage examples are not pytest tests. Do not use `test_*` names. Every program must
define `main()`, use an `if __name__ == "__main__"` guard, and be excluded from
pytest collection. Verify it by direct Python execution.

The program must call every documented public operation and constructor in its
feature through the public package API using realistic, bounded, secret-safe data
or genuine runtime state. Do not substitute mocks or invented provider evidence
when the genuine supported public boundary is available.

The README must identify the intended usage-example function.

Do not write the full example implementation unless the template explicitly requires an example skeleton.

## Step 17 — Define tests

Every functional requirement must map to at least one unit test under:

```text
tests/[domain]/unit/
```

Use:

```text
tests/[domain]/unit/test_[file].py::test_[function]_[scenario]()
```

Every collaborative workflow must map to an integration test under:

```text
tests/[domain]/integration/
```

Usage examples belong under:

```text
tests/[domain]/usage/
```

Tests must cover:

* successful behaviour;
* validation;
* documented errors;
* side effects;
* important boundaries;
* retained V1 behaviour where applicable;
* modified or newly added behaviour.

## Step 18 — Add package-wide requirements

Include only requirements applying across several modules, such as:

* public import boundaries;
* platform independence;
* security;
* performance;
* reliability;
* logging;
* determinism;
* coverage;
* shared configuration.

Do not move feature-specific requirements into this section.

## Step 19 — Carry forward open decisions

Copy unresolved decisions from reconciliation that still affect the domain.

For each one include:

* decision required;
* available options;
* affected capabilities or requirements;
* current evidence.

Do not design affected functions or files by guessing.

An affected requirement must remain `Missing` until the decision is resolved.

A decision affecting more than one domain must also appear in the Open Decisions section of the top-level system document while unresolved. After resolution, encode the outcome in the authoritative specifications and delete the decision row.

## Step 20 — Validate completeness

Before returning the README, verify that:

* the domain boundary matches the top-level system document;
* all cross-domain inputs and outputs match the top-level system document;
* no circular dependency is proposed;
* every approved reconciliation capability appears;
* no removed capability appears;
* no rejected V2 requirement appears;
* deferred behaviour is not included in the initial implementation;
* every retained V1 behaviour has a final destination;
* every module has one capability;
* every file has one responsibility;
* every public symbol has exactly one requirement row;
* every requirement has a typed signature;
* every requirement has a side-effect classification;
* every requirement has documented errors;
* every requirement maps to a usage example;
* every requirement maps to a unit test;
* every collaborative workflow maps to an integration test;
* configurations and limits have clear owners;
* dependencies are ordered correctly;
* diagrams agree with the package structure;
* statuses reflect evidence;
* no unresolved decision was silently guessed;
* the README follows the supplied template.

# REQUIRED OUTPUT

Create:

```text
[FINAL_PACKAGE_PATH]/README.md
```

The completed README must follow the supplied final domain README template.

Do not create:

* another requirements document;
* another reconciliation document;
* an architecture requirements document;
* a migration report;
* production code;
* test code;
* implementation files.

# FINAL RESPONSE

Return:

1. The completed final domain `README.md`.
2. A concise list of unresolved evidence or open decisions that prevented full specification.
3. Nothing else.

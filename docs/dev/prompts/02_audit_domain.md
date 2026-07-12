# ROLE

You are a senior Python software architect performing a **legacy code audit**.

# CONTEXT

I am rebuilding an existing system from Version 1 to Version 2.

Version 1 contains working code, but its structure may be bloated, fragmented, duplicated, unused, or poorly documented.

This task audits **one Version 1 domain at a time**.

The audit will later be compared against the Version 2 requirements. Do not perform that comparison in this task.

# DOMAIN TO AUDIT

* **Domain name:** `[DOMAIN_NAME]`
* **Package path:** `[PATH_TO_V1_DOMAIN]`
* **Tests path:** `[PATH_TO_V1_TESTS]`
* **Known callers or related packages:** `[OPTIONAL_PATHS]`

# GOAL

Extract an evidence-based representation of what the Version 1 domain actually provides.

Use this minimal structural hierarchy:

```text
Package
└── Module folder
    └── File
        └── Public Class / Function / Method / Constant
```

The audit must determine:

1. What exists.
2. What each item does.
3. Where it is used.
4. Why it exists.
5. Which real workflow uses it.
6. Whether it currently provides real value.
7. Whether it appears active, unused, duplicated, incomplete, or obsolete.

# IMPORTANT RULES

1. Use the actual Version 1 code as the source of truth.
2. Do not assume undocumented behaviour.
3. Do not redesign the system.
4. Do not create Version 2 requirements.
5. Do not modify or generate code.
6. Do not recommend complex architectural patterns.
7. Do not treat every private helper as a functional requirement.
8. Focus primarily on public behaviour and externally useful functionality.
9. Trace imports and call sites before declaring something unused.
10. Tests alone do not prove production usage.
11. Dynamic registrations, decorators, configuration references, callbacks, and string-based imports must also be checked.
12. Every conclusion must include evidence using file paths and symbol names.
13. Clearly distinguish confirmed findings from uncertain findings.
14. Do not preserve something merely because it already exists.
15. Do not mark something as dead code unless reasonable usage searches have been completed.

# AUDIT PROCESS

## Step 1 — Establish the package boundary

Identify:

* package root;
* module folders;
* Python files;
* public exports from `__init__.py`;
* externally imported symbols;
* entry points;
* configuration files;
* tests;
* examples;
* scripts;
* registration mechanisms.

Exclude generated files, caches, virtual environments, and unrelated packages.

## Step 2 — Inventory the package structure

Represent the actual code using:

```text
Package
└── Module folder
    └── File
        └── Public classes/functions/methods/constants
```

For every file, identify its primary responsibility.

Flag files that contain several unrelated responsibilities.

## Step 3 — Identify public behaviour

For every public class, function, method, or constant, determine:

* signature;
* responsibility;
* inputs;
* return value;
* raised exceptions;
* side effects;
* dependencies;
* callers;
* tests;
* real system value.

Use these side-effect labels where applicable:

```text
None
Read-only
Local state mutation
Persistence write
External API call
Broker mutation
Event publication
```

## Step 4 — Trace actual usage

Search the full available codebase for:

* imports;
* function calls;
* class instantiation;
* method calls;
* inheritance;
* decorators;
* registries;
* callbacks;
* configuration references;
* command-line entry points;
* scheduled tasks;
* API routes;
* agent tools;
* event subscribers;
* tests and examples.

Assign one usage status:

| Status            | Meaning                                             |
| ----------------- | --------------------------------------------------- |
| **Used**          | Confirmed production or runtime usage               |
| **Test-only**     | Used only by tests or examples                      |
| **Possibly used** | Dynamic or indirect usage cannot be fully confirmed |
| **Unused**        | No reasonable usage evidence found                  |
| **Unknown**       | Available evidence is insufficient                  |

## Step 5 — Reconstruct real workflows

Identify actual end-to-end workflows in which this domain participates.

Separate:

* **Internal workflows:** completed inside this domain;
* **Cross-domain workflows:** receive input from or send output to another domain.

For every workflow, document:

* trigger;
* input boundary;
* sequence of public functions or methods;
* files involved;
* external dependencies;
* final outcome;
* failure behaviour;
* evidence;
* whether the workflow appears complete and operational.

For cross-domain workflows, describe only this domain’s participation:

```text
Input from another domain
→ this domain's responsibilities
→ output to another domain
```

## Step 6 — Evaluate real value

Assign one value status to every public symbol and file:

| Value status              | Meaning                                               |
| ------------------------- | ----------------------------------------------------- |
| **Essential**             | Directly supports an important working workflow       |
| **Useful**                | Provides real value but is not central                |
| **Supporting**            | Required internally by valuable behaviour             |
| **Questionable**          | Purpose exists, but current value or usage is unclear |
| **No demonstrated value** | No meaningful workflow or caller was found            |

## Step 7 — Identify structural problems

Look specifically for:

* duplicated behaviour;
* multiple files providing the same capability;
* one file containing unrelated responsibilities;
* public symbols with no callers;
* private helpers exposed publicly;
* wrappers that add no meaningful value;
* incomplete workflows;
* isolated features;
* direct provider coupling;
* circular dependencies;
* inconsistent return types;
* inconsistent error handling;
* stale configuration;
* tests for behaviour that production code never uses;
* code paths that cannot be reached;
* names that do not reflect actual responsibility.

Do not fix these issues. Record them with evidence.

# REQUIRED OUTPUT

Create:

```text
[DOMAIN_NAME]-v1-audit.md
```

Use the following structure.

---

# [Domain Name] — Version 1 Code Audit

## 1. Audit Scope

* Domain:
* Package path:
* Tests path:
* Files inspected:
* Related packages searched:
* Audit limitations:

## 2. Executive Summary

Briefly state:

* what the domain currently provides;
* how many module folders, files, and public symbols exist;
* which workflows appear operational;
* the most important structural problems;
* how trustworthy or complete the audit evidence is.

## 3. Actual Package Structure

```text
[Show the real Package → Module folder → File → Public symbol structure]
```

## 4. Module and File Inventory

Arrange modules and files in their actual dependency order where possible.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| ------ | ---- | -------------- | ----------- | ------------ | ------------ | ------------ |

For dependencies, use this order:

```text
Standard library
Required third-party
Local modules and imported symbols
```

## 5. Public Behaviour Inventory

### `[module]/[file.py]`

**File responsibility:** [Actual responsibility]

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |

Repeat for every file containing public behaviour.

## 6. Actual Workflows

### `V1-WF-[DOMAIN]-001` — [Workflow Name]

* **Scope:** `[Internal | Cross-domain]`
* **Trigger:**
* **Input boundary:**
* **Functions and methods used:**
* **Files involved:**
* **External dependencies:**
* **Output boundary:**
* **Failure behaviour:**
* **Operational status:** `[Working | Partial | Broken | Unverified]`
* **Evidence:**

```text
Trigger
→ function_a()
→ function_b()
→ function_c()
→ outcome
```

Repeat for every confirmed or partially confirmed workflow.

## 7. Usage and Caller Map

| Public symbol | Called from | Call type | Runtime or test | Evidence |
| ------------- | ----------- | --------- | --------------- | -------- |

## 8. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| ------ | ------ | ------- | -------- | ---- |

## 9. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| ---- | ------- | ------------------ | ---------- | -------- |

Do not call an item dead code unless the confidence is high.

## 10. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --------------------- | ------------------ | -------------- | -------- |

## 11. Structural Problems

| ID             | Problem   | Location        | Impact   | Evidence   |
| -------------- | --------- | --------------- | -------- | ---------- |
| `V1-ISSUE-001` | [Problem] | [Path / symbol] | [Impact] | [Evidence] |

## 12. V1 Capability Catalogue

This catalogue will later be compared with Version 2 requirements.

| Capability ID | Capability   | Current implementation | Workflow(s) | Usage status | Value status | Notes   |
| ------------- | ------------ | ---------------------- | ----------- | ------------ | ------------ | ------- |
| `V1-CAP-001`  | [Capability] | [Files and symbols]    | `V1-WF-...` | Used         | Essential    | [Notes] |

## 13. Audit Conclusions

Summarize:

* valuable behaviour worth preserving;
* behaviour that exists but is disconnected;
* likely dead weight;
* duplicated responsibilities;
* important uncertainties;
* areas that require manual confirmation.

# FINAL VALIDATION

Before completing the audit, verify that:

* every Python file in the domain is represented;
* every documented public export exists in code;
* every `__init__.py` export was checked;
* callers were searched across the available codebase;
* workflows are based on actual call paths;
* production usage is distinguished from test-only usage;
* uncertain findings are labelled clearly;
* no Version 2 design was invented;
* no code was changed.

Return only the completed audit document and a concise list of any evidence you could not access.

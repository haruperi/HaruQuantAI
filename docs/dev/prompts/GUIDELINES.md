Start with the **top-level system documentation first** in `docs/PROJECT.md`.

It defines the boundaries that every domain README must follow:

```text
1. Top-level system documentation in `docs/PROJECT.md`
   ↓
2. Domain READMEs in dependency order
   ↓
3. Implementation in dependency order
```

> [!IMPORTANT]
> - This document is for both new systems and upgrades to existing systems.
> - Some steps are explicity for system upgrades and not applicable to new systems,
>   just skip them if you are implementing a new system.
> - Do **not** rebuild blindly from V2, and do **not** let V1 code automatically define the future system.
> - Use these rules when upgrading:
>   * V1 code = evidence of what currently exists and works
>   * V2 requirements = proposed future behaviour
>   * Final README = approved V2 specification


## Step 1 — Populate the top-level system document

Complete only the sections needed to establish the system shape:

1. System purpose and boundary
2. Domain capability map
3. Domain registry
4. Domain ownership boundaries
5. Domain dependency diagram
6. Main cross-domain workflows
7. Shared contracts
8. Shared configuration and limits

Do not define domain files, classes, or functions here.

The result should answer:

```text
What domains exist?
What does each domain own?
How do domains depend on each other?
How does data move between domains?
Which domain should be built first?
```

## Step 2 — Audit V1 one domain at a time

For each domain, extract:

```text
Package
→ Module folders
→ Files
→ Public classes/functions
→ Actual workflows
→ Real value provided
→ Where each item is used
```

Do not document every private helper. Focus on externally useful behaviour.

## Step 3 — Compare V1 against V2 requirements

Classify every capability into four decisions:

| Decision         | Meaning                                                   |
| ---------------- | --------------------------------------------------------- |
| **Keep**   | V1 already provides the required behaviour correctly      |
| **Modify** | V1 is useful but must be changed for V2                   |
| **Remove** | V1 is obsolete, duplicated, unused, or no longer valuable |
| **Add**    | V2 requires behaviour that does not exist in V1           |

Example:

| Capability                     | V1 evidence      | V2 requirement                  | Decision |
| ------------------------------ | ---------------- | ------------------------------- | -------- |
| Submit market order            | Exists and works | Platform-independent submission | Modify   |
| Read account details           | Exists and works | Required in every route         | Keep     |
| Direct MT5 imports             | Exists           | Broker-independent design       | Remove   |
| Unknown-outcome reconciliation | Missing          | Required                        | Add      |

## Step 4 — Populate domain READMEs

Create each domain README in the order defined by the system dependency diagram.

For HaruQuantAI:

```text
01 Utils
02 Data
03 Indicators
04 Strategy
05 Risk
06 Analytics
07 Trading
08 Simulation
09 Optimization
10 Research
11 UI/API
12 AI Agents 
13 Conversation AI Chatbot
```

Each domain README then defines:

```text
Module folders
→ Files
→ Classes/functions
→ Functional requirements
→ Internal workflows
→ Domain participation in cross-domain workflows
→ Configuration
→ Tests
```

For unpgrades, the README should not describe V1 or V2 separately. It should describe the **approved final system**.

For every module, file, and requirement, decide what the final design should be:

```text
V1 working behaviour
+ V2 intended improvements
+ cleanup decisions
= Final domain README
```

The README becomes the migration target.

## Step 5 — Review the top-level document again

After completing the domain READMEs, verify that:

* domain boundaries still match;
* public inputs and outputs align;
* cross-domain workflows connect correctly;
* shared contracts are consistent;
* no responsibility is duplicated.

## Step 6 — Begin implementation

Implement in the same dependency order:

```text
System documentation
→ Domain README
→ Code
→ Tests
→ Mark status Completed
→ Retire replaced V1 code (if system upgrade)
```

The governing rule should be:

> **The system document defines the domains. Domain READMEs define the code. Code implements the READMEs.**

### For System upgrades - Implement by migration, not full replacement

For each README requirement:

1. Reuse V1 code when it already matches.
2. Refactor V1 code when it is close.
3. Replace it only when its design conflicts with the final structure.
4. Add missing behaviour.
5. Remove old code only after replacement tests pass.

This is a **clean migration**, not necessarily a clean-room rewrite.
---



## Important principle

Do not copy the V1 file structure into the README merely because it exists.

Extract the **valuable behaviours and workflows**, then reorganize them into your new minimal structure:

```text
Package
└── Feature module
    └── Focused file
        └── Public classes/functions
```

Several old files may become one focused file. One bloated old file may become two focused files.



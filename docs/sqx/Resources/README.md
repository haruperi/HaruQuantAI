# Resources: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppHelp.jar](AppHelp.md) | 0 | No compiled classes |
| [AppHome.jar](AppHome.md) | 0 | No compiled classes |
| [AppPaymentDialog.jar](AppPaymentDialog.md) | 0 | No compiled classes |

## Workspace registration evidence

- `AppHelp`: no module.js at archive directory root. App-prefix alone does not establish a navigation workspace. See its inspected Java plugin declarations.
- `AppHome`: no module.js at archive directory root. App-prefix alone does not establish a navigation workspace. See its inspected Java plugin declarations.
- `AppPaymentDialog`: no module.js at archive directory root. App-prefix alone does not establish a navigation workspace. See its inspected Java plugin declarations.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

No cross-group reference resolved within the scoped archives. This is not proof of runtime independence.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.

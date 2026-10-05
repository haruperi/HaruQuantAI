# CodeEditor: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppCodeEditor.jar](AppCodeEditor.md) | 3 | `com.strategyquant.plugin.App.impl.CodeEditor` |
| [CodeEditorImportExport.jar](CodeEditorImportExport.md) | 5 | `com.strategyquant.plugin.CodeEditor.impl.ImportExport` |
| [CodeEditorIndicatorTester.jar](CodeEditorIndicatorTester.md) | 7 | `com.strategyquant.plugin.CodeEditor.impl.IndicatorTester` |
| [ServletCodeEditor.jar](ServletCodeEditor.md) | 13 | `com.strategyquant.plugin.Servlet.impl.CodeEditor`, `com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles`, `com.strategyquant.plugin.Servlet.impl.CodeEditor.templates` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppCodeEditor/module.js`: title `Code Editor`, app code `SQEDITOR`, hidden registration `False`. SHA-256 `81e5a1c8df8a565aa83b7da703e43b1a05361ce7bbb6ddab4a46d584540cf5c4`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQPluginLib.jar](../Shared/SQPluginLib.md) - `Shared`.
- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.

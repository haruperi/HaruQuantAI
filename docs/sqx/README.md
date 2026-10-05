# SQX workspace and JAR class reference

One canonical Markdown document per JAR, grouped by workspace or shared role. These are donor structural references, not a specification of HaruQuantAI implementation.

## Coverage

- Inspected 176 plugin archives and seven selected shared libraries: **183 JAR documents**.
- **1,821 class entries**, including nested/anonymous classes; **406 focused UML diagrams**.
- Eleven plugin JARs contain no compiled classes and therefore have no invented class diagram.
- Nineteen workspace/shared/resource folders. All 21 App archives are included; 16 NavigationPlugin registrations were observed.
- Access date: 2026-10-05. Installed SQX build and runtime activation are unverified.

## Workspace groups

| Group | JAR documents | Registration/ownership basis |
| --- | ---: | --- |
| [AlgoWizard](AlgoWizard/README.md) | 3 | App registration plus inferred backend grouping; see index evidence |
| [Builder](Builder/README.md) | 3 | App registration plus inferred backend grouping; see index evidence |
| [CodeEditor](CodeEditor/README.md) | 4 | App registration plus inferred backend grouping; see index evidence |
| [CustomProjects](CustomProjects/README.md) | 18 | App registration plus inferred backend grouping; see index evidence |
| [DataManager](DataManager/README.md) | 24 | App registration plus inferred backend grouping; see index evidence |
| [DebugConsole](DebugConsole/README.md) | 1 | App registration plus inferred backend grouping; see index evidence |
| [GettingStarted](GettingStarted/README.md) | 1 | App registration plus inferred backend grouping; see index evidence |
| [GridControl](GridControl/README.md) | 3 | App registration plus inferred backend grouping; see index evidence |
| [GridTest](GridTest/README.md) | 1 | App registration plus inferred backend grouping; see index evidence |
| [NeuralNetworkTrainer](NeuralNetworkTrainer/README.md) | 2 | App registration plus inferred backend grouping; see index evidence |
| [Optimizer](Optimizer/README.md) | 2 | App registration plus inferred backend grouping; see index evidence |
| [PortfolioComposer](PortfolioComposer/README.md) | 4 | App registration plus inferred backend grouping; see index evidence |
| [PortfolioMaster](PortfolioMaster/README.md) | 3 | App registration plus inferred backend grouping; see index evidence |
| [ProductShells](ProductShells/README.md) | 2 | Product shell, not assumed standalone navigation |
| [Resources](Resources/README.md) | 3 | Resource/auxiliary role, not established workspace |
| [Results](Results/README.md) | 30 | App registration plus inferred backend grouping; see index evidence |
| [Retester](Retester/README.md) | 3 | App registration plus inferred backend grouping; see index evidence |
| [SQXBusiness](SQXBusiness/README.md) | 1 | App registration plus inferred backend grouping; see index evidence |
| [Shared](Shared/README.md) | 75 | Shared role, not an exclusive workspace |

## How to read the diagrams

- Inheritance and interfaces come from inspected class declarations.
- Dotted `field type` edges are declared member-type dependencies. They do not assert composition, ownership or a runtime invocation.
- Complete dependency tables additionally include parameter/return/generic/throws references, with exact declaration evidence.
- Referenced types outside each diagram are identified in its type table. They link to a canonical JAR document only when resolved in the inspected scope.
- Focused diagrams contain at most 12 non-nested internal classes. Nested/anonymous classes, overloads and synthetic methods remain in inventories/declaration references even when omitted from graph member lists.
- The diagrams contain selected member names for readability; exact Java declarations are retained in collapsible references. No method bodies are included.

## Shared backend libraries

| Library | Class entries | Structural research area (inferred from observed classes/packages) |
| --- | ---: | --- |
| [SQDataLib.jar](Shared/SQDataLib.md) | 195 | Data definitions, readers/writers, imports and bar types |
| [SQGridLib2.jar](Shared/SQGridLib2.md) | 81 | Compute, synchronization and grid infrastructure |
| [SQJobsLib.jar](Shared/SQJobsLib.md) | 11 | Job engine and lifecycle types |
| [SQPluginLib.jar](Shared/SQPluginLib.md) | 18 | Plugin registration/discovery types |
| [SQTradingLib.jar](Shared/SQTradingLib.md) | 945 | Simulation, genetic programming, task/project infrastructure and statistics |
| [SQWebGUILib.jar](Shared/SQWebGUILib.md) | 34 | Web server, servlet and browser integration types |
| [SQWizardBusiness.jar](Shared/SQWizardBusiness.md) | 24 | Wizard loading and indicators |

The shared-library selection is contextual and bounded, not an exhaustive inventory of internal/libs. Plugin JARs often delegate to these libraries; folder placement alone does not establish capability ownership.

## Evidence and validation

Each document records its logical artifact locator, SHA-256, inspection date/method, class inventory, exact declaration evidence and confidence limits. High confidence applies to inspected structural declarations. Workspace assignments and responsibility descriptions are inferred unless registration evidence is stated. Runtime behavior and SQX parity are unverified.

The source roots are SQX_REFERENCE_ROOT and HARUQUANTAI_ROOT. Canonical product/architecture authority and reimplementation ledger/schema are absent in this repository; this reference does not invent replacements or allocate evidence IDs. The DataManagerData document links to the existing local FEAT-DATASET-MANAGEMENT registry without extending its implementation claims.

Verified on 2026-10-05: all 183 archive documents, 1,821 class inventory entries, 406 diagram structures and 1,821 drawn declaration relationships were checked. All 3,101 local Markdown links resolved and all 183 donor hashes matched. No machine-specific absolute paths were found. Mermaid parser/rendering validation remains unverified: no existing parser/renderer was available, so checks were structural. Raw inspections and generation helpers remain outside the repository.

## Backend planning use

Start from the workspace index, inspect the relevant JAR diagrams, and follow shared-library links. Resolve behavior, lifecycle and target ownership separately before implementation. A JAR is a donor packaging unit, not a requirement to create a matching HaruQuantAI service or module.

# P00 step 5 — current SQX145 host-core research

Research date: 2026-10-06 UTC. Source HEAD:
`d4e0ed8bbd46e47e44d6072a4edfc1652491b904`.
Published bounded research and owner-approved policy disposition. No application feature/FR registration or application code edited.

## Charter

- Goal: locate inspectable host bodies or identify the precise access gap; establish consumed contracts without inventing hidden behavior.
- Knowledge: standalone archive metadata is established; host packaging was initially unknown.
- Scope / object / subject: SQX145 host architecture / missing common core / launchers, installer payload, archive resources, runtime image and current consumer instructions.
- Type: exploratory packaging research, followed by bounded descriptive caller inspection.
- Q1: where are `MainApp`, `AppSettings` and `CpuInfo` defined? Unanswered.
- Q2: can their shipped bodies be read statically? No body found within the stated search; absence outside that boundary remains unverified.
- Q3: which contracts do readable consumers actually use? Answered for the selected structural consumer set; selected defaults/branches also inspected.
- Sole donor: `SQX_145_REFERENCE_ROOT`. Target: `HARUQUANTAI_ROOT`.
- Excluded: user/account/license state, databases, runtime caches, donor launches, installer execution, native-library loading, activation, class instrumentation and remote downloads.

## Canonical sources

| Rank | Source | Applicability |
| --- | --- | --- |
| 1–2 | [SQX official custom-task plugin documentation](https://strategyquant.com/doc/programming-for-sq/example-plugin-a-complete-custom-project-task/) | Explains Java backend and JavaScript frontend plugin composition. Updated 2023; does not locate the current hidden host core. |
| 1–2 | [Oreans official overview](https://www.oreans.com/index.php/Themida.php), [XBundler FAQ](https://oreans.com/help/tm/hm_faq_what-about-performance_-im-wr.htm) | Explains native protection and encrypted embedding capability. No proof that SQX enabled XBundler or uses the current advertised protector version. |
| 1–2 | [PyInstaller archive documentation](https://pyinstaller.org/en/stable/advanced-topics.html#carchive), [maintainer reader format](https://raw.githubusercontent.com/pyinstaller/pyinstaller/develop/PyInstaller/archive/readers.py) | Cookie/TOC formats corroborate the installer package interpretation. Does not establish the exact PyInstaller release used by SQX. |
| 3 | Current executable bytes, 289 current archives and `j64/lib/modules` | Actual static packaging and caller evidence; fingerprints retained in the portable capture. |
| Repository authority | `AGENTS.md`, `app/host/README.md`, current ledger/schema, inventory, ownership and phase plans | Governs target mapping and approval; cannot establish donor behavior. |

All official pages accessed 2026-10-06. An initial GitHub HTML reader URL was inaccessible; its official raw source was subsequently read. Search snippets are not evidence.

## Findings ledger

Rows F1–F17 correspond to fresh atomic records SQX145-EV-000177 through SQX145-EV-000193. Normative closure/host-source decisions are records 000194 and 000195. [Portable capture](sqx145/host-core-research.json) stores exact source pins, descriptors, locations, timestamps and observations.

| ID | Claim | Exact evidence / location | Rank | Answers / limit |
| --- | --- | --- | --- | --- |
| F1 | All three host launchers contain `.themida` PE sections. | capture `/native_packaging`, section tables: `StrategyQuantX.exe` raw offset 3651584; `sqcli.exe` 3718656; `CodeEditor.exe` 3635712 | 3 | Q1; marker presence only. |
| F2 | The inspected launcher bytes contain no raw Java class-file magic. | Same artifacts; complete-byte scan for `CA FE BA BE` | 3 | Q2; compressed/encrypted/transformed content remains outside this test. |
| F3 | The installer overlay has a valid PyInstaller-compatible CArchive cookie/TOC. | `SQ_Installer.exe`, overlay offset 324096, cookie offset 21676559 within overlay; TOC 21618271, length 58288; capture `/installer_package` | 1–3 | Q1; format interpretation, not donor execution. |
| F4 | All 1042 inspected CArchive entries lack target class-name byte matches. | capture `/installer_package`, entries after bounded decompression: `MainApp`, `AppSettings`, `CpuInfo`, `SQLib` | 3 | Q2; no PYZ semantic analysis or dynamic-download observation. |
| F5 | The 289 current JAR resource scan found no recognizable nested candidate with a target host entry name. | capture `/archive_packaging`: every non-class resource prefix; candidate archive entries; all archive hashes match inventory | 3 | Q1/Q2; only specified prefixes, extensions and names; no arbitrary encoded-resource proof. |
| F6 | The current Java runtime image lists none of the three exact host class entries. | `j64/lib/modules`; capture `/runtime_image`: exact `com/strategyquant/lib/app/{MainApp,AppSettings}.class`, `com/strategyquant/lib/memory/CpuInfo.class` comparison | 3 | Q1/Q2; runtime-loaded classes remain unverified. |
| F7 | The selected MainApp consumer set contains 218 direct target-member instructions. | capture `/consumer_contracts`, 71 consumer classes; method+offset and exact class/archive SHA-256 per instruction | 3 | Q3; static instructions, not observed execution. |
| F8 | The selected AppSettings consumer set contains 82 direct target-member instructions. | Same capture, 23 classes | 3 | Q3; readable callers do not expose settings storage internals. |
| F9 | The selected CpuInfo consumer set contains two direct target-member instructions. | Same capture, two classes in `ResultsPortfolioCorrelation.jar` | 3 | Q3; only `getAvailableProcessors()I` is consumed here. |
| F10 | Dukascopy supplies string `3` as the `parallelDownload` fallback argument. | `DukasServlet.class`, `onGetParallelDownload()Ljava/lang/String;`, offsets 20–30 | 3 | Q3; actual callee fallback semantics remain unknown. |
| F11 | Dukascopy supplies string `3` as the `cdnParallelDownload` fallback argument. | Same class/method, offsets 37–47 | 3 | Q3; no global default inferred. |
| F12 | Dukascopy's setter places queue-size update before settings updates and save. | Same class, `onSetParallelDownload(Ljava/util/Map;)Ljava/lang/String;`, offsets 31–82 | 3 | Q3; ordering only, not atomicity or durable success. |
| F13 | Dukascopy starts its preload helper only on the false result branch of `MainApp.runInConsole()`. | Same class, `preloadAvailableDataResponse()V`, offsets 0–17 | 3 | Q3; console-mode derivation and helper outcomes unknown. |
| F14 | PortfolioCorrelationComputer uses the CPU return value directly as fixed-pool size. | `PortfolioCorrelationComputer.class`, `compute`, offsets 27–37 | 3 | Q3; detection, overrides and valid return range unknown. |
| F15 | OverlappingTradesComputer uses the CPU return value directly as fixed-pool size. | `OverlappingTradesComputer.class`, `compute`, offsets 5–13 | 3 | Q3; no process-wide CPU policy inferred. |
| F16 | PortfolioCorrelationComputer calls `shutdownNow` on its explicit portfolio-interruption handler path. | First class offsets 466–478 / exception range 39–465 | 3 | Q3; no general shutdown guarantee; core thread lifecycle unknown. |
| F17 | OverlappingTradesComputer calls `shutdownNow` on its explicit portfolio-interruption handler path. | Second class offsets 412–424 / exception range 15–411 | 3 | Q3; no general shutdown guarantee; core thread lifecycle unknown. |

Captures are source-pinned and dated in the portable capture. Findings F10–F13 use:

- Archive: `internal/plugins/DataSourceDukascopy/DataSourceDukascopy.jar`.
- Archive SHA-256: `40b61a3670af7fcf1265fa2d07889d6c75df100b96dd1d73b64c8de793e6913c`.
- Entry: `com/strategyquant/plugin/DataSource/impl/Dukascopy/DukasServlet.class`.
- Entry SHA-256: `0739e3d30655c464f49b5f87e9e73fbe93edc8c59d2e6da50796420996579fb3`.

Findings F14–F17 use:

- Archive: `internal/plugins/ResultsPortfolioCorrelation/ResultsPortfolioCorrelation.jar`.
- Archive SHA-256: `cb2351d4e02219f853d36abb08ffbacb19b71fbd7c730cf5105273fa359e40f5`.
- First entry: `com/strategyquant/plugin/Results/impl/PortfolioCorrelation/correlation/PortfolioCorrelationComputer.class`; SHA-256 `7e26869e874b099f46f4a3f2782c759313625040df2c174d898cf5266bce0bdf`.
- Second entry: `com/strategyquant/plugin/Results/impl/PortfolioCorrelation/overlappingTrades/OverlappingTradesComputer.class`; SHA-256 `8e5ff4744cdc4a93bcb488fa4c79e82a4d77dff6aca2fd1dae376ac03e52a386`.

Inspection methods: standard-library PE/ZIP parsing, bounded zlib decompression, 7-Zip 26.03 listing/resource reads, system `javap` and `jimage` 26.0.2.1. No donor entrypoint executed. Disassemblies and installer scratch are ignored working material and must never enter the published clean-room candidate.

## Scope filter

- Retain only current-cohort observations and explicitly bounded official format/capability context.
- Discard any inference that static version resources establish activation or executed product identity.
- Exclude user state, license/database contents, runtime caches and remote acquisition.
- Retain existing archive-level absence finding; current research does not contradict it.

## Object filter

- Caller fallbacks establish supplied arguments, not hidden lookup/default policy.
- PE markers plus Oreans capabilities do not prove embedded Java-core location, XBundler enablement or recoverable bodies.
- Installer package and JAR candidate results do not prove absence of encoded, transformed or runtime-provided bodies.
- 302 instructions across 73 distinct classes are not 302 executed calls. Per-target consumer counts overlap.
- The selected structural set is not a claim of complete dynamic/reflection-driven consumption.

## Conclusions

- The bounded packaging/caller audit is complete (F1–F9). None of the three core bodies was located in inspectable form (Q1 remains unanswered). P00 closes by the owner-approved source-gap disposition; this does not convert missing bodies into observed implementations.
- Readable callers support concrete supplied arguments, branch conditions, ordering and pool-size inputs (F10–F17). They cannot supply missing core algorithms.
- The consumed surface has 24 distinct members: 18 MainApp members including one field; five AppSettings methods; one CpuInfo method (F7–F9). Exact descriptors are in capture `/consumer_contracts`.
- A protected/embedded core is an **unverified hypothesis**; the current evidence does not identify its container. No decrypted core source was obtained.
- No SQX parity, host boot, connected backend/UI, settings durability, CPU policy or activation qualification follows from this work.

### Target mapping

| Finding group | Target owner / feature | Requirements / decisions |
| --- | --- | --- |
| Packaging and census | Registered `FEAT-HOST-EVIDENCE`, `app/host/README.md` | Existing `FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION`, `FR-HOST-EVIDENCE-LEDGER-INTEGRITY`, `FR-HOST-EVIDENCE-OWNERSHIP-GATES`; `DEC-HOST-P00-REGISTRY-BOUNDARY`, `DEC-HOST-P00-RELEASE-GATES`, `DEC-HOST-SQX145-REFERENCE`. |
| MainApp/AppSettings hidden host behavior | P01 1.38 integration, `app/host/README.md` | No application-core feature/FR is registered. The owner ratified DEC-HOST-P00-UNAVAILABLE-HOST-SOURCE; exact host policies and owning FEAT/FR registrations remain future approved feature-plan work. |
| F10–F13 | Proposed `FEAT-DATA-SOURCE-DATA-SOURCE-DUKASCOPY`; `app/plugins/data_source/DataSourceDukascopy/README.md` | Existing proposed class contract/preload/execute seeds apply as context; getter/setter behavior has no registered FR. Do not invent registered IDs. |
| F14–F17 | Proposed `FEAT-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION`; `app/plugins/portfolio/ResultsPortfolioCorrelation/README.md` | Existing seeds concern the servlet, not these worker methods. Worker lifecycle/CPU requirements need owning feature-plan ratification. |

These are research mappings, not duplicated implementation status or authorization to implement.

## Next steps / Risks

- Owner approved closure plan version 2 on 2026-10-06 with `APPROVED: EXECUTE`. [Host decisions](../../../app/host/README.md) distinguish P00 readiness from application/runtime qualification.
- The P00 source search is closed with an accepted limitation. No concrete remaining source location or future recovery is promised. New concrete evidence can justify bounded reassessment.
- Universal host lifecycle/settings/path/CPU services may be implemented from explicit target-owned contracts, informed by the readable callers. Unsupported defaults/policies must be normative decisions approved in their owning feature plans.
- The exception covers no missing numerical, trading, AI or other domain algorithm. Keep their evidence/independent comparison obligations in the owning phase.
- Application feature/FR registration belongs to individual approved implementation plans. No application feature is completed by this research.
- Unknown donor semantics remain: settings initialization/precedence/storage/null/invalid handling/save failures; CPU detection/overrides/caching/bounds; host initialization/shutdown/console derivation/paths/failures.
- Target verification must exercise each approved host contract's normal/boundary/failure behavior and explicit FR logs. Donor comparisons are required before a parity claim; target tests alone do not establish it.
- Research checks passed at `2026-10-06T20:40:23.714970+00:00`: 289 archive hash matches, 73 unique consumer classes, 302 member instructions, 1042 package entries, 29 native resources and zero exact runtime target entries. Final publication checks are recorded separately in the [portable capture](sqx145/host-core-research.json).
- No donor runtime, installer, native loading, class instrumentation, database action, UI execution or activation test was performed. Runtime/activation/parity states remain unqualified.
- Earlier P00 review/source findings are preserved. The stronger prerequisite policy is superseded explicitly; normative ledger records retain the distinction from donor facts.
- P00 status belongs to the host README; the master checklist reflects it only after final static verification.

Research progress: canon, charter, bounded findings, scope/object filters and evidence review completed. Review state is unreviewed for independent review; the same assistant performed source verification/self-review.

# StrategyQuant X Documentation

Entry point for all SQX documentation. Read this first, then the level matching the task; each
folder's `README.md` links to the files inside it, so navigate by links, not by scanning the tree.
Clickable diagram map: [`map.md`](map.md); every diagram (architecture, flows, per-module
internals): [`diagrams/`](diagrams/README.md).

## Levels

| Level | Folder | Covers |
|---|---|---|
| 0 Clean-room blueprint | [`architecture-and-reimplementation.md`](architecture-and-reimplementation.md) | SQX-145 system topology, core JARs (`libs/`), 182-plugin inventory, `.cfx`/`.sqx` persistence, and HaruQuantAI Python reimplementation map |
| 1 Functional / product | [`overview/`](overview/README.md) | Modules, workflow, data flow; per-tab detail in [Results tabs](overview/results-tabs/README.md), [Settings tabs](overview/settings/README.md) |
| 2 Developer / architecture | [`onboard/`](onboard/README.md) | Subprojects, engines, startup, per-module architecture (mainly backend) |
| 3 Build and run | [`build-and-run.md`](build-and-run.md) | Gradle tasks, launchers, `j64` JDK, release/miniBuild packaging |
| CLI | [`cli/`](cli/README.md) | Headless SQX/QDM: [sqcli](cli/sqcli.md), [qdmcli](cli/qdmcli.md), [commands reference](cli/commands-reference.md) |
| AlgoWizard integration | [`algowizard-integration/`](algowizard-integration/README.md) | `awEditorInterface` bridge, event catalog, AI-chat component, getting a new AW build into SQX |
| Results integration | [`results-integration/`](results-integration/README.md) | Overlay iframe, `results2` flag, `resultsInterface` bridge, legacy AngularJS vs RESULTS2 Vue app parity |
| AI chat | [`ai-chat/`](ai-chat/README.md) | Standalone `ai-chat` app in the SQX side panel (out of AlgoWizard): shell and editor access, identity and credits, editor API it needs |
| AI assistant (SQAI) | [`sqai/`](sqai/README.md) | Built-in AI chat: tools, how it works, how it shares this knowledge base with an external Claude |
| Custom-project config | [`custom-projects/`](custom-projects/README.md) | `.cfx` zip anatomy, `<Project>`/`<Task>`/`<Databank>` grammar, every task type's settings sections, strategy-style levers (money management, building blocks, templates); code-derived, consumed by the `strategy-architect` AI plugin |
| Adding a platform | [`new-platform-guide/`](new-platform-guide/00-master.md) | New export target / source-code generator: what a platform is, model, scope, templates, runtime, Java/UI touchpoints, tests, parity; platform-agnostic counterpart of the NinjaTrader case study [`onboard/12-export/05-adding-a-platform.md`](onboard/12-export/05-adding-a-platform.md) |
| UI reference (tests) | [`ui/`](ui/README.md) | Navigation map, element catalog, locators, testids for Playwright tests |
| AlgoCloud and Stockpicker | [`algocloud/`](algocloud/README.md) | Cloud stock-trading platform (concepts, workflow, brokers, plans, help-center map) and its SQX engines (`task_stockpicker.xml`, Picker MM, position score, stock groups) |
| Strategy authoring | [`strategy-authoring/`](strategy-authoring/README.md) | Per-engine capability matrix, what cloud engines cannot do, engine clock and shift semantics, arithmetic value expressions, magic numbers, translation gaps with reasons and fixes |
| Trading knowledge | [`trading/`](trading/README.md) | Trader workflow (build -> validate -> robustness -> portfolio -> live), strategy styles (mean reversion, momentum, breakout), costs and data quality, overfitting, risk and position sizing |

[`DOCUMENTATION-PLAN.md`](DOCUMENTATION-PLAN.md): how this set is structured. Internal-only, not
in the release ZIP (`copy-docs.sh`): [`n8n/`](n8n/README.md) (n8n AI workflow exports),
[`sqai-chat/`](sqai-chat/README.md) (SQ-hosted LLM gateway), [`sqai-internal/`](sqai-internal/README.md)
(SQAI ops notes, handovers), [`sqai-knowhow-protection/`](sqai-knowhow-protection/README.md)
(keeping SQ AI know-how out of the release).

## What StrategyQuant X is

Desktop application for developing algorithmic trading strategies: generate, backtest, optimize,
stress-test for robustness, manage market data. Three apps: StrategyQuant (build/generate,
backtest, optimize, walk-forward, Monte Carlo), QuantDataManager (QDM, market data), CodeEditor
(strategy snippets). One Java process embedding a Jetty web server; the GUI is a web app (AngularJS
+ some Vue) in an Electron shell over HTTP + WebSocket; heavy backtests go to grid nodes. Module
relations and diagram: [`overview/`](overview/README.md).

## Conventions

- English only.
- Signpost navigation: each folder's `README.md` is an index, deeper `.md` files hold the detail; cross-link between levels.
- Diagrams are Mermaid (GitHub, VS Code, IntelliJ render them).
- One `CLAUDE.md` in the repo root points into `docs/`; two user-owned `CLAUDE.md` under `work_directory/` stay in place.

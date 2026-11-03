# AlgoCloud & the Stockpicker / Single-asset engines

Knowledge base about **AlgoCloud** — the organization's cloud platform for no-code algorithmic
trading of US stocks & ETFs — and about the **Stockpicker** and **Single-asset (cloud)** engines
in StrategyQuant X that generate strategies for it.

Why it lives in this repo's docs: SQX **generates strategies for AlgoCloud** (single-asset and
stockpicker, exported/imported as `.sqx`), ships the `Stockpicker` and `Single-asset cloud
strategy` backtest engines, the `task_stockpicker.xml` Build defaults, the `Picker*` money
management and the `_ExitEOD_` exit type — and SQAI needs this context to answer questions about
either side.

Sourced from the AlgoCloud public web presence (mirrored offline on 2026-08-07 — see below) and
from this repo's Java sources. Same knowledge-base rules as the rest of `docs/`: small
cross-linked pages, readable by SQAI via `read_file`. **Fully offline** — every referenced
article/page is a local file; no URLs anywhere in this folder.

| Page | Contents |
|------|----------|
| [platform.md](platform.md) | What AlgoCloud is: core concepts (single-asset vs stockpicker, stock groups, position score), the end-to-end workflow, markets & data, backtesting & execution timing, brokers, plans. |
| [help-center-map.md](help-center-map.md) | Index of the **offline help-center mirror** (7 collections, 55 articles) with one-line gists. |
| [stockpicker-engine.md](stockpicker-engine.md) | The SQX side: the `Stockpicker` / `Single-asset cloud strategy` engines, generation templates, `task_stockpicker.xml` specifics, Picker money management, stockpicker data/universes. |
| [`help/`](help/) | The mirrored help-center articles — one Markdown file per article, grouped in per-collection folders (`introduction/`, `getting-started/`, `brokers/`, `trading/`, `editor-backtesting/`, `settings/`). |
| [`site/`](site/) | Mirrored marketing-website pages: homepage, how-it-works, FAQs, about-us. (No pricing — prices are deliberately not kept in docs; refer users to the AlgoCloud website.) |

## The relationship in one paragraph

AlgoCloud is a **separate product** of the same organization (AlgoWizardCloud LLC — the
StrategyQuant / QuantAnalyzer / QuantDataManager family; founder Mark Fric). It is self-contained
(own no-code Strategy Editor, own backtester, own cloud execution), trades **US stocks & ETFs on
the daily timeframe** through the user's own broker, and is **not bundled** with any SQX package.
SQX's role: generate unique single-asset or stockpicker strategies and import them into AlgoCloud
(`My strategies → Import`); AlgoCloud can export back in `.sqx` where applicable.

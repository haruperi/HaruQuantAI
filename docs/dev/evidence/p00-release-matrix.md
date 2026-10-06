# P00 release matrix

Owner approved cohort: evidence infrastructure only. P00 baseline delivery does
not complete common-core/runtime prerequisites. Runtime execution, application
coverage, donor-target differential observations and whole-app parity are unqualified.

| Phase | Target scope | Dependency | Qualification |
| --- | --- | --- | --- |
| P00 | Evidence, scope and ownership baseline | none | Reference tooling only; runtime prerequisite blocked |
| P01 | Host bootstrap, logging, configuration and diagnostics | P00 | Unqualified; separate plan and complete body evidence required |
| P02 | Host discovery, transport, jobs, resource services and persistence | P01 | Unqualified; separate plan and complete body evidence required |
| P03 | Data Manager: datasets, instruments, sessions and custom data | P02 | Unqualified; separate plan and complete body evidence required |
| P04 | File ingestion, provider downloads and exchange data | P03 | Unqualified; separate plan and complete body evidence required |
| P05 | Strategy vocabulary, indicator/block catalog and numerical primitives | P03 | Unqualified; separate plan and complete body evidence required |
| P06 | Execution engine, accounting, trading options and stock picking | P02,P03,P05 | Unqualified; separate plan and complete body evidence required |
| P07 | AlgoWizard, CodeEditor, custom resources and platform code generation | P02,P05,P06 | Unqualified; separate plan and complete body evidence required |
| P08 | Databanks, results, chart projections, analysis and exports | P02,P06,P07 | Unqualified; separate plan and complete body evidence required |
| P09 | Builder: generation, genetic search, improvement and ranking | P05,P06,P07,P08 | Unqualified; separate plan and complete body evidence required |
| P10 | Optimizer: parameter search, sequential modes, walk-forward and matrix | P06,P08,P09 | Unqualified; separate plan and complete body evidence required |
| P11 | Retester, robustness checks, Monte Carlo and What-If | P06,P08,P10 | Unqualified; separate plan and complete body evidence required |
| P12 | Portfolio Composer, Portfolio Master and automatic portfolios | P08,P09,P10,P11 | Unqualified; separate plan and complete body evidence required |
| P13 | Custom projects, Task Manager, conditions and task actions | P02,P04,P07,P08,P09,P10,P11,P12 | Unqualified; separate plan and complete body evidence required |
| P14 | Grid Control, Grid Test and compute execution | P02,P06,P09,P10,P11,P13 | Unqualified; separate plan and complete body evidence required |
| P15 | Neural Network Trainer and model resource lifecycle | P03,P05,P06,P08,P14 | Unqualified; separate plan and complete body evidence required |
| P16 | Connections, terminal integration and explicitly authorized trading | P02,P03,P04,P06,P08,P13 | Unqualified; separate plan and complete body evidence required |
| P17 | Product shells, business, help, MCP and desktop/distribution completion | P01,P02,P07,P08,P13,P14,P15,P16 | Unqualified; separate plan and complete body evidence required |
| P18 | Whole-app integration and independently verified release | P00-P17 | Unqualified; separate plan and complete body evidence required |

## Product, fixtures and numerical boundaries

All donor navigation/product registrations remain activation-unknown. Hidden flags,
file presence and JAR names do not prove inactivity or activation. Actual installed
SQX build remains unknown; 144.2953 is a historical reference label. JVM 25.0.1 is
runtime metadata only. No unavailable external provider is counted as functional.

Initial fixtures use static exact counts, fingerprints and discrete body operation
order; tolerance is exactly zero. Independently executed runtime/normal/boundary/
failure outputs are unavailable and cannot be guessed. Future algorithms must pin
units, defaults, state/order, rounding, RNG and feature-specific tolerances before
translation. No dependency adapter is approved beyond P00 dev validation libraries.

SQLib/MainApp/AppSettings/CpuInfo behavior, product/version/activation and runtime
fixtures remain blockers. Observe any donor runtime only through a separately
approved isolated copy/protocol after file/resource/write targets are known; never
launch against installed user state to fill an evidence gap. Donor token logging
and silent cleanup need explicit future conflict decisions. No external mutation,
store migration, restore or trading is authorized.

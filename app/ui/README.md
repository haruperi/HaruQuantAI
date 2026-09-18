# StrategyQuant X frontend recreation

A dense React/TypeScript recreation of the audited StrategyQuant X application surface. It is a frontend-only research simulator: deterministic mock services provide coherent strategies, trades, equity, optimization projections, robustness verdicts, portfolios, workflows and job lifecycles without invoking native SQX or external services.

## Run

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:3000`.

Production verification:

```bash
npm run typecheck
npm test
npm run build
npm run preview
```

## Demonstration scenarios

- Builder: edit Full settings, return to Progress, Start, Pause, Resume, Stop, then inspect Results.
- Databanks: select several virtualized rows and copy or move them between Results and Retest candidates.
- Results: select a strategy and compare Overview, Trade list, Equity, Drawdown, Robustness and optimization projections.
- Optimizer: switch between Simple, Sequential, Walk-Forward and WF Matrix to reveal applicable controls.
- AlgoWizard: select a rule, remove it, add a configured block, and save the mock revision.
- Portfolio Composer: change member weights/capital and run the shared-capital simulation.
- Custom Projects: enable tasks and run the ordered workflow.
- Data Manager: start a provider update or open the safe CSV/TSV import flow.

Workspace data is stored under local-storage key `sqx-recreation-v1`. Open Configuration → Mock developer tools → Reset fixture workspace to restore the deterministic seed and state variants.

## Documentation

- [Reference audit](docs/reference.md)
- [Coverage inventory](docs/coverage.json)
- [Interaction map](docs/interactions.md)
- [Navigation map](docs/navigation.md)
- [Mock contracts](docs/mock-contracts.md)
- [Parity ledger](docs/parity.md)

The exact unsupported/native boundaries are recorded in `docs/parity.md`. Generated code is illustrative, imports use explicit browser formats, and no screen claims real backtesting, compilation, provider access or trading.

# Navigation map

```text
Application shell
├── Home
├── Research
│   ├── Builder ─┬─ Progress
│   │            ├─ Full settings
│   │            └─ Results ── linked selected strategy
│   ├── Improver ─── same project frame, improve-existing settings
│   ├── Retester ─── same project frame, new evaluation semantics
│   └── Optimizer ── Simple / Sequential / Walk-Forward / WF Matrix
├── Data & authoring
│   ├── Data Manager ── Sources / Export / Tools / Instruments / Extensions
│   └── AlgoWizard ─── block library / rule tree / property editor
├── Portfolio
│   ├── Portfolio Master ── candidate combination constraints
│   └── Portfolio Composer ── capital-aware weights and simulation
├── Automation
│   └── Custom Projects ── projects / ordered tasks / task settings
└── Extensions
    ├── Code Editor
    └── SQX Business
```

The global header owns skin, notifications, help and configuration. Research-module databanks are shared rather than routed to separate copies. Result navigation preserves selected strategy, run scope, market, direction and sample filters.

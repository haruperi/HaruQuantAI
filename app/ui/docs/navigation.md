# Navigation map

```text
Application shell
├── Home
├── Research
│   ├── Builder ─┬─ Progress
│   │            ├─ Full settings
│   │            └─ Results ── linked selected strategy
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
    └── Business
```

The application sidebar switches between a 190 px labelled layout and a persistent 49 px icon rail. The icon-only left-chevron control sits beside the HaruQuantAI brand in the topbar and collapses it; the right-chevron control expands it. The sidebar begins with Home and has no visible Applications heading. Application icons retain accessible names, tooltips, active state, and routing in either mode. The global header owns notifications, the top-only Debug Console and Grid Control applications, the Volume & Market Profile Addon dialog, and the reference-ordered Settings menu. Theme selection and Help center are available through Settings, so duplicate header shortcuts are omitted. Full is the normal feature fixture; Starter remains test-only policy state and has no production selector. Code Editor remains in the sidebar and is intentionally not duplicated in the header. Settings launches Configuration, Benchmark, Remote access, MCP Server, SMTP server, Language, Skin, Zoom/fullscreen, website/help/support links, Update license, About, Reload UI, and Exit. Research-module databanks are shared rather than routed to separate copies. Result navigation preserves selected strategy, run scope, market, direction and sample filters.

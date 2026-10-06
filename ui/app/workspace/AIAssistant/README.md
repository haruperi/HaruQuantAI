# AI Assistant workspace

Native React recreation of the SQX 145 AI Assistant presentation, mounted at
`/aiassistant`. The shell entry sits immediately before FUNDAMENTALS.

`capabilities.json` adapts all eight entries, descriptions and conversation
starters from the shipped English catalog. `catalog.ts` provides typed
presentation data. `AIAssistantWorkspace.tsx` owns ephemeral sessions, projects,
pins, drafts and attachment selection. Scoped styles support dark/light skins,
desktop conversation navigation and a narrow-screen conversation drawer.

This is a UI-only cohort. Drafts and `File` references stay in React memory until
the workspace unmounts/reloads or the user clears/closes them. No files are read,
uploaded or persisted. No requests are made by this workspace. Models, credits,
sending, reports, host strategy actions and Brain file editing explicitly remain
unavailable until separately ratified assistant services exist. There are no
simulated assistant replies, provider usage, tool results or memory documents.

## Reference mapping

Read-only donor root: `SQX_145_REFERENCE_ROOT/internal/web/SQAI`.

| Native surface | Donor evidence | Adaptation |
| --- | --- | --- |
| Header, context and credits | `chat/assets/index-DbWeULv9.js` and `index-BfdqFDsP.css`, `sqai-header` / `sqai-credits-pill` | Native component, unavailable billing |
| Capability tiles and starters | `features/sqx/en.json`, version 3; compiled ChatWelcome | Eight tiles, brand text adapted, starters prepare drafts |
| Conversations, projects, pins, sessions | Compiled `EditorAIChat.sidebar.*` and `EditorAIChat.tabs.*` strings | Local organization only; confirmed local clear/close |
| Composer, attachments, model and commands | Compiled `EditorAIChat.typeMessage`, `.attachments.*`, `.model.*`, `.commands.*` | Local file selection/paste/drop and help/clear; gated sending/models |
| AI Brain | `workspace-panel.js` and donor workspace directory structure | Memory/Knowledge/Skills/State descriptions; disabled editor and skill actions |
| Usage and guide | Compiled `.viewUsage` strings and `ai-guide.html` | Unavailable usage; inline help explains this UI cohort |

SHA-256 donor fingerprints are recorded in `source-map.json`. Compiled Vue,
Monaco/language bundles, Angular bridges, shell body-wrapping scripts, provider
configuration and mutable donor workspace files are not copied or executed.
Full-page mounting replaces donor docking/maximize controls. Provider terms,
paid-credit purchasing and externally hosted introduction videos are excluded
because those services are not connected. This implementation does not qualify
P19 backend parity.

## Verification

- `npm --prefix ui run typecheck`
- `npm --prefix ui run test -- tests/unit/app/router.test.ts`
- `npm --prefix ui run test:ui -- tests/e2e/sidebar-navigation.spec.ts tests/e2e/ai-assistant-parity.spec.ts --workers=1`
- `npm --prefix ui run build`

## SQX145 reference qualification

Current donor root: `SQX_145_REFERENCE_ROOT`; source maps bind freshly inspected artifact identities. Retained UI functionality/status is unchanged; source differences and absent counterparts require task-level body/integration research. No runtime or connected backend parity is asserted.

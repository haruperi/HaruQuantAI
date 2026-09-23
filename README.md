# HaruQuantAI

HaruQuantAI is a local-first quantitative research workstation being rebuilt
around a shared host, workspace pairs, and focused plugins. The Python host
and React UI shell can run together now. Most quantitative workspace screens
still use fixtures or local simulation; they are not evidence of completed
backend algorithms or trading integration.

[PROJECT.md](docs/PROJECT.md) defines product scope,
[ARCHITECTURE.md](docs/ARCHITECTURE.md) defines the Five Laws of Spatial
Composability and pair boundaries, and [AGENTS.md](AGENTS.md) defines the
contributor workflow. See the [backend host](app/host/README.md) and
[UI host](app/ui/src/app/README.md) READMEs for current feature status.

## Prerequisites

Run these commands from the repository root. Install Python 3.14,
[uv](https://docs.astral.sh/uv/), and Node.js with npm. The commands below
install this repository's declared Python and UI dependencies.

## Run backend and frontend for development

Open two PowerShell terminals at the repository root.

**Terminal 1 — backend host**

```powershell
uv sync
uv run python -m app.main
```

The host listens on http://127.0.0.1:8000 by default. Its unauthenticated
health endpoint is http://127.0.0.1:8000/api/v1/health.

**Terminal 2 — frontend UI**

```powershell
npm --prefix app/ui install
npm --prefix app/ui run dev
```

Open http://127.0.0.1:3000. The Vite UI connects to the host at
127.0.0.1:8000. If HARUQUANTAI_HOST_PASSWORD is unset, the local research
host issues a passwordless session. If that environment variable is set
before starting the host, the UI prompts for the password. The browser
session token stays in memory. Stop each server with Ctrl+C in its terminal.

Global Settings menu preferences are saved by the host in
`data/database/haruquantai.db` (`host_settings`). Future feature-owned JSON presets belong in
`data/presets/`.

The default ports can be changed through host configuration, but the
development UI currently targets port 8000 when served on Vite's port 3000.
A different backend port requires matching UI deployment or proxy
configuration. Host settings and other overrides are documented in the
[backend host README](app/host/README.md).

## Serve a built UI from the backend

To use one server instead of Vite, build the UI and start the host:

```powershell
uv sync
npm --prefix app/ui install
npm --prefix app/ui run build
uv run python -m app.main
```

Open http://127.0.0.1:8000. The host serves app/ui/dist by default when
the build is present. Rebuild the UI after frontend source changes.

## Verify the candidate

```powershell
uv run python scripts/ci_check.py
npm --prefix app/ui run typecheck
npm --prefix app/ui run test
npm --prefix app/ui run build
```

The CI command runs the current Python lint, formatting, type, architecture,
and branch-aware test-coverage checks. UI commands run separately. For
change-scoped test guidance and the plan/approval/walkthrough gates, follow
[AGENTS.md](AGENTS.md). Workspace and plugin implementations require their
own approved plans and owning READMEs.

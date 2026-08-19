# Widgets API Feature Namespace

## Purpose

Groups API features that exist specifically to orchestrate workstation pages or
widgets. This directory is an organizational namespace, not a registered
feature and not a second implementation or feature-registry authority.

## Boundaries

- Each child directory owns exactly one registered `FEAT-API-*` capability.
- Each child contains the standard `README.md`, `__init__.py`, `routes.py`,
  `schemas.py`, and `orchestration.py` surface. Focused extra route,
  persistence, or migration modules remain inside that same feature.
- The namespace owns no behavior, persistence, requirements, or contracts.
- The API package root remains the sole public import boundary.

## Features

- `event_delivery/` — `FEAT-API-06`, ordered event delivery.
- `settings/` — `FEAT-API-07`, Settings boundary.
- `operational/` — `FEAT-API-10`, operational read model and command API.
- `watchlists/` — `FEAT-API-11`, account watchlists.
- `markets/` — `FEAT-API-12`, Markets gateway orchestration.
- `operator/` — `FEAT-API-13`, operator governance boundary.
- `data/` — `FEAT-API-14`, Data gateway.
- `indicators/` — `FEAT-API-15`, Indicators catalogue boundary.
- `strategies/` — `FEAT-API-16`, Strategy gateway.
- `simulation/` — `FEAT-API-17`, Simulation gateway.
- `risk/` — `FEAT-API-18`, Risk gateway.
- `trading/` — `FEAT-API-19`, Trading gateway.
- `optimization/` — `FEAT-API-20`, Optimization gateway.
- `research/` — `FEAT-API-21`, Research gateway.
- `portfolio/` — `FEAT-API-22`, Portfolio gateway.
- `dashboards/` — `FEAT-API-23`, Dashboard gateway.
- `agentic/` — `FEAT-API-24`, Agentic operator gateway.
- `simulator/` — `FEAT-API-25` / `FEAT-API-27`, Simulator gateway and Simulation Workbench.
- `analytics/` — `FEAT-API-28`, Analytics Workbench gateway.

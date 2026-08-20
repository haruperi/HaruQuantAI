# MetaTrader 5 Tick Stream Provider

> **Provider ID:** `data.tick_stream.metatrader`
> **Capability:** `data.tick_stream.v1`
> **Lifecycle:** Scoped, `reversible_ephemeral`
> **Status:** Active

## Overview
Adapts the read-only MetaTrader 5 local TCP snapshot receiver into the `data.tick_stream.v1` capability contract.
Lifecycle cleanups release underlying symbol subscriptions, tasks, and buffers in deterministic reverse order.

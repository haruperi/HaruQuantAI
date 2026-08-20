# RSI Default Indicator Provider

## Identity & Metadata

- **Provider ID**: `indicator.rsi.default`
- **Version**: `1.0.0`
- **Entry Point**: `app.services.indicators.momentum.rsi_default.plugin:create_provider`
- **Provided Capability**: `indicator.rsi.v1` (contract version `1.0.0`, cardinality `exactly_one`)
- **Runtime Profiles**: `simulation`, `research`, `demo`, `live`
- **Scope**: `process`
- **Effect Classes**: None (pure computation)
- **Lifecycle**: `scoped`
- **Feature Ownership**: `FEAT-INDI-03` (Momentum Indicators)

## Overview

Calculates the Wilder Relative Strength Index over normalized immutable market datasets using Wilder smoothing.

## Removal Instructions

To uninstall and remove this provider:
1. Delete directory `app/services/indicators/momentum/rsi_default/`.
2. Delete tests in `tests/indicators/providers/indicator.rsi.default/`.
3. If no alternative `indicator.rsi.v1` provider is installed, requests for `indicator.rsi.v1` will fail closed with structured `CapabilityUnavailableError`.

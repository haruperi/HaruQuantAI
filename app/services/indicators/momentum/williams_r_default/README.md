# Williams %R Default Indicator Provider

## Identity & Metadata

- **Provider ID**: `indicator.williams_r.default`
- **Version**: `1.0.0`
- **Entry Point**: `app.services.indicators.momentum.williams_r_default.plugin:create_provider`
- **Provided Capability**: `indicator.williams_r.v1` (contract version `1.0.0`, cardinality `exactly_one`)
- **Runtime Profiles**: `simulation`, `research`, `demo`, `live`
- **Scope**: `process`
- **Effect Classes**: None (pure computation)
- **Lifecycle**: `scoped`
- **Feature Ownership**: `FEAT-INDI-03` (Momentum Indicators)

## Overview

Calculates Williams %R over normalized immutable market datasets using inclusive rolling high/low windows.

## Removal Instructions

To uninstall and remove this provider:
1. Delete directory `app/services/indicators/momentum/williams_r_default/`.
2. Delete tests in `tests/indicators/providers/indicator.williams_r.default/`.
3. If no alternative `indicator.williams_r.v1` provider is installed, requests for `indicator.williams_r.v1` will fail closed with structured `CapabilityUnavailableError`.

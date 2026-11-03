"""Shared HaruQuant strategy language contracts and execution.

Description:
    Keep strategy semantics owned by the trading core.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Consistent, explicit strategy execution boundaries.
Key Capabilities:
    - FR-shared-hsl-execution: Hosts log decisions; focused tests verify effects.
Python API Usage:
    Import the typed contracts and services from this module.
CLI Usage:
    uv run pytest tests/core/trading tests/workspace/algo_wizard --no-cov
"""

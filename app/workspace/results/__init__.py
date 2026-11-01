"""Results workspace package initialization.

Description:
    Results workspace package initialization providing strategy outcome
    visualizations, databank transformations, and report exporters.

Purpose:
    FEAT-RESULTS-PACKAGE: Expose workspace results models and services.

Key Capabilities:
    - FR-results-package-bootstrap: Package boundary for AppResults domain.

Python API Usage:
    from app.workspace.results import OverviewTemplatePolicy

CLI Usage:
    python -m app.cli results --help
"""

from __future__ import annotations

from app.workspace.results.overview_template_policy import OverviewTemplatePolicy

__all__ = ["OverviewTemplatePolicy"]

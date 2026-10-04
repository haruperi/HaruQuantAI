"""Behavioral checks for the HaruQuantAI root application package.

Description:
    Verifies that the root application package `app` is importable, exposes
    a docstring-only package initializer adhering to Spatial Composability,
    and maintains a clean root namespace.

Purpose:
    FEAT-ROOT-PACKAGE: Root application package initialization and boundary verification.

Key Capabilities:
    - FR-ROOT-IMPORT: Import and introspect the root application package.
      Associated: `test_app_package_import()`
      Logging: Implicit pytest execution reporting.

Python API Usage:
    ```python
    import app

    assert isinstance(app.__doc__, str)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/test_app.py
    ```
"""

from __future__ import annotations

import app


def test_app_package_import() -> None:
    """Verify that the root application package can be imported and has docstring."""
    assert isinstance(app.__doc__, str)
    assert "HaruQuantAI" in app.__doc__

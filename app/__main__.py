"""Module entrypoint executing app.main when run with python -m app.

Description:
    Enables invoking the HaruQuantAI platform via `python -m app` by routing
    directly to `app.main.main()`.

Purpose:
    FEAT-APP-MAIN: Main application package entrypoint.

Key Capabilities:
    - FR-APP-MAIN-BOOTSTRAP: Route package execution to primary application runner.
      Associated: `main()`
      Logging: Inherited from `app.main.main`.

Python API Usage:
    ```python
    from app.__main__ import main

    main()
    ```

CLI Usage:
    ```bash
    uv run python -m app
    ```
"""

from __future__ import annotations

from app.main import main

__all__ = ["main"]

if __name__ == "__main__":
    main()

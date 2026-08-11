"""NFR-INDI-001: Component process test for import side effects."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_importing_indicators_has_no_persistent_side_effects() -> None:
    """NFR-INDI-001: importing the package writes nothing and starts nothing.

    Runs in a subprocess rather than purging ``sys.modules`` in place. A fresh
    interpreter is both a stronger check (nothing is already imported) and
    safe: rebinding live modules would break class identity for every other
    test sharing this session.
    """
    probe = (
        "import pathlib,sys;"
        "before={p.name for p in pathlib.Path.cwd().iterdir()};"
        "import app.services.indicators as ind;"
        "assert ind.build_indicator_config is not None;"
        "assert ind.join_indicator_result is not None;"
        "after={p.name for p in pathlib.Path.cwd().iterdir()};"
        "assert before==after,'import created filesystem entries';"
        "assert len(ind.__all__)==85,'unexpected public surface';"
        "assert all(callable(getattr(ind, name)) for name in ind.__all__),'non-function in public surface';"
        "assert callable(ind.doji),'public numerical export did not resolve';"
        "print('OK')"
    )
    completed = subprocess.run(  # noqa: S603 - fixed inline probe, no shell.
        [sys.executable, "-c", probe],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"import probe failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
    assert "OK" in completed.stdout

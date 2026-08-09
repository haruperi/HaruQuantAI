"""Cross-process determinism proof for new Utils primitives."""

import os
import subprocess
import sys
from pathlib import Path


def test_exact_keys_and_draws_are_byte_identical_across_processes() -> None:
    """Identical explicit inputs produce identical canonical output."""
    code = """from app.utils import canonical_json,build_exact_unit,derive_idempotency_key,derive_random_stream,next_int
s=derive_random_stream(7,'fills'); d,s=next_int(s,lower=1,upper=10)
print(canonical_json({'unit':build_exact_unit('1.25',kind='MONEY',currency='USD'),'key':derive_idempotency_key(owner='simulator:orders',intent={'order':'ord-1'}),'draw':d}))
"""
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[3])}
    outputs = [
        subprocess.run(  # noqa: S603 - fixed interpreter and inline test program.
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        ).stdout
        for _ in range(2)
    ]
    assert outputs[0] == outputs[1]

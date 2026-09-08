"""Bounded offline usage for artifact custody."""

from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile


def describe_fixture() -> tuple[int, str]:
    content = b"haruquantai-artifact-demo"
    return len(content), hashlib.sha256(content).hexdigest()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as root:
        workspace = Path(root)
        size, digest = describe_fixture()
        print({"workspace": workspace.name, "bytes": size, "sha256": digest, "network": False})

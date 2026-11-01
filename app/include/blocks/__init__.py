"""Backward-compatibility bridge forwarding app.include.blocks to app.extend.blocks.

Description:
    Provides backward compatibility for legacy imports pointing to app.include.blocks
    by transparently forwarding them to app.extend.blocks.
Purpose:
    FEAT-EXTEND-BLOCKS-MIGRATION: Preserve backward compatibility during extension
    migration.
Key Capabilities:
    - FR-blocks-compatibility-forwarding: Redirect legacy block module imports to
      extend.
Python API Usage:
    from app.include.blocks import BaseBlock
CLI Usage:
    uv run python -m pytest tests/extend/blocks --no-cov
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Sequence
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import override

from app.extend import blocks as _extend_blocks

# Re-export top-level attributes
for _name in getattr(_extend_blocks, "__all__", dir(_extend_blocks)):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_extend_blocks, _name)


class _BlocksModuleLoader(Loader):
    """Loader that delegates module resolution directly to app.extend.blocks."""

    def __init__(self, target_module: str) -> None:
        self.target_module = target_module

    @override
    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        del spec
        return importlib.import_module(self.target_module)

    @override
    def exec_module(self, module: ModuleType) -> None:
        del module


class _BlocksMetaPathRedirector(MetaPathFinder):
    """Dynamically redirect any import under app.include.blocks to app.extend.blocks."""

    @override
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        del path, target
        if fullname.startswith("app.include.blocks."):
            redirected_name = "app.extend.blocks." + fullname.removeprefix(
                "app.include.blocks."
            )
            return ModuleSpec(fullname, _BlocksModuleLoader(redirected_name))
        return None


if not any(isinstance(finder, _BlocksMetaPathRedirector) for finder in sys.meta_path):
    sys.meta_path.insert(0, _BlocksMetaPathRedirector())

"""Pytest configuration for standalone Portfolio usage scripts.

Excludes standalone feature usage scripts and pipeline programs from pytest collection.
"""

from __future__ import annotations

collect_ignore_glob = ["*.py"]

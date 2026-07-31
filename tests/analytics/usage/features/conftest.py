"""Pytest configuration for standalone Analytics usage scripts.

Excludes standalone feature usage scripts and pipeline programs from pytest collection.
"""

from __future__ import annotations

collect_ignore_glob = ["*.py"]

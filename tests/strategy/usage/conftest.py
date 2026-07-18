"""Exclude standalone numbered Strategy usage scripts from pytest collection."""

collect_ignore_glob = ["[0-9]*_*.py"]

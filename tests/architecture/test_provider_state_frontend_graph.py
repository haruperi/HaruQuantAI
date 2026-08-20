"""Unit tests for database state and frontend graph extractor.

Traces to: P2-T03, Gate G2
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.architecture.provider_state_frontend_graph import scan_state_and_frontend


def test_extracts_state_edges(tmp_path: Path) -> None:
    """Verify state edge extraction from SQL and migration files."""
    mig_dir = tmp_path / "app" / "services" / "data" / "migrations"
    mig_dir.mkdir(parents=True)
    (mig_dir / "0001_initial.py").write_text(
        """
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT
);

CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""",
        encoding="utf-8",
    )

    graph = scan_state_and_frontend(tmp_path)
    kinds = {s["kind"] for s in graph["state_edges"]}
    assert "table_owner" in kinds
    assert "foreign_key" in kinds


def test_finds_serialized_class_path(tmp_path: Path) -> None:
    """Verify serialized python module paths are found and stored."""
    mod = tmp_path / "registry.py"
    mod.write_text(
        """
TARGET_CLASS = "app.services.brokers.mt5.adapter"
ANOTHER = "app.kernel.identifiers.CapabilityId"
""",
        encoding="utf-8",
    )

    graph = scan_state_and_frontend(tmp_path)
    paths = [p["path"] for p in graph["serialized_python_paths"]]
    assert "app.services.brokers.mt5.adapter" in paths
    assert "app.kernel.identifiers.CapabilityId" in paths


def test_extracts_frontend_edges(tmp_path: Path) -> None:
    """Verify Next.js routes, widgets, and TS imports are extracted."""
    page_dir = tmp_path / "app" / "ui" / "src" / "app" / "login"
    page_dir.mkdir(parents=True)
    (page_dir / "page.tsx").write_text(
        """
import React from "react";
import { fetchClient } from "@/lib/client";

export default function LoginPage() {
    const fetchIt = () => fetch("/api/v1/auth/login");
    return <div>Login</div>;
}
""",
        encoding="utf-8",
    )

    widget_dir = tmp_path / "app" / "ui" / "src" / "widgets"
    widget_dir.mkdir(parents=True)
    (widget_dir / "OrderWidget.tsx").write_text(
        "export function OrderWidget() {}", encoding="utf-8"
    )

    graph = scan_state_and_frontend(tmp_path)
    kinds = {f["kind"] for f in graph["frontend_edges"]}
    assert "next_route" in kinds
    assert "widget_registry" in kinds
    assert "typescript_import" in kinds
    assert "api_client" in kinds


def test_output_is_deterministic(tmp_path: Path) -> None:
    """Verify deterministic JSON output."""
    mod = tmp_path / "app.py"
    mod.write_text("PATH = 'app.services.data.dataset'\n", encoding="utf-8")

    g1 = scan_state_and_frontend(tmp_path)
    g2 = scan_state_and_frontend(tmp_path)
    assert json.dumps(g1, sort_keys=True) == json.dumps(g2, sort_keys=True)

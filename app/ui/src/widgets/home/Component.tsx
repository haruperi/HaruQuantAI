/**
 * Home widget (FR-UI-PRESENT_HOME), owned by FEAT-UI-START_WORK.
 *
 * Presents product/workspace identity, versions, and capability-aware
 * getting-started entry points. Entry points are derived exclusively from
 * the shell snapshot's capability-filtered workspace list, so no action is
 * shown as available when its capability is absent.
 */

import React, { useEffect, useState } from "react";
import type { WidgetProps } from "../types";
import { useUiRuntime, useShellSnapshot } from "../../runtime/context";
import { useStartWorkClient } from "../../features/start_work";

interface HomePresentationState {
  readonly status: "loading" | "ready" | "degraded";
  readonly message: string;
}

const DEFAULT_VERSION_LINE = "HaruQuantAI Workstation 0.1.0";

function newRequestId(prefix: string): string {
  const cryptoRef = globalThis.crypto as Crypto | undefined;
  if (cryptoRef && typeof cryptoRef.randomUUID === "function") {
    return `${prefix}-${cryptoRef.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}`;
}

export const HomeWidget: React.FC<WidgetProps> = (props) => {
  const bridge = useUiRuntime();
  const snapshot = useShellSnapshot();
  const client = useStartWorkClient();
  const [presentation, setPresentation] = useState<HomePresentationState>({
    status: "loading",
    message: "Preparing home presentation...",
  });
  const isMockClient = (client as { isDevOnly?: boolean }).isDevOnly === true;

  const configuration = props.configuration as
    | { version_line?: unknown }
    | undefined;
  const versionLine =
    typeof configuration?.version_line === "string"
      ? configuration.version_line
      : DEFAULT_VERSION_LINE;

  useEffect(() => {
    let cancelled = false;
    client
      .startWork({
        request_id: newRequestId("req-home"),
        capability_snapshot_id: "snap-current",
        operation: "SHOW_HOME",
      })
      .then((success) => {
        if (cancelled) return;
        setPresentation({
          status: "ready",
          message: `Home ready (${success.result_version ?? 1})`,
        });
      })
      .catch(() => {
        // FR-UI-PRESENT_HOME acceptance is not gated on provider availability:
        // identity, versions, and capability-aware entry points remain usable.
        if (cancelled) return;
        setPresentation({
          status: "degraded",
          message: "Home provider unavailable; entry points remain available.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  const entryPoints = snapshot.available_workspaces;

  return (
    <div
      className="home-widget"
      style={{
        padding: "16px",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        height: "100%",
        boxSizing: "border-box",
        overflow: "auto",
      }}
      data-testid="home-widget"
    >
      <h2 style={{ margin: "0 0 8px 0", fontSize: "18px", color: "#38bdf8" }}>
        HaruQuantAI — Start Work
      </h2>
      <div data-testid="home-identity" style={{ fontSize: "13px", marginBottom: "4px" }}>
        <strong>Product:</strong> HaruQuantAI · <strong>Workspace:</strong>{" "}
        {snapshot.active_workspace_id ?? "workstation"}
      </div>
      <div data-testid="home-version" style={{ fontSize: "13px", marginBottom: "12px" }}>
        <strong>Version:</strong> {versionLine}
      </div>

      <div style={{ fontSize: "13px", marginBottom: "8px", fontWeight: "bold" }}>
        Getting Started
      </div>
      <div
        role="list"
        aria-label="Capability-aware entry points"
        style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "12px" }}
      >
        {entryPoints.length === 0 ? (
          <div style={{ color: "#64748b", fontSize: "12px" }} data-testid="home-no-entry-points">
            No entry points are currently available.
          </div>
        ) : (
          entryPoints.map((ws) => (
            <button
              key={ws.workspace_id}
              type="button"
              role="listitem"
              data-testid={`home-entry-${ws.workspace_id}`}
              onClick={() => bridge.switchWorkspace(ws.workspace_id)}
              style={{
                textAlign: "left",
                padding: "8px 10px",
                backgroundColor: "#1e293b",
                color: "#e2e8f0",
                border: "1px solid #475569",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "13px",
              }}
            >
              <strong>{ws.display_name}</strong>
              <span style={{ color: "#94a3b8" }}> — {ws.route_path}</span>
            </button>
          ))
        )}
      </div>

      <div
        data-testid="home-presentation-status"
        style={{
          fontSize: "12px",
          color:
            presentation.status === "ready"
              ? "#4ade80"
              : presentation.status === "degraded"
                ? "#facc15"
                : "#94a3b8",
        }}
      >
        {presentation.message}
      </div>

      {isMockClient && (
        <div
          data-testid="home-mock-label"
          role="note"
          style={{
            marginTop: "12px",
            padding: "6px 10px",
            backgroundColor: "#422006",
            color: "#fbbf24",
            borderRadius: "4px",
            fontSize: "12px",
            fontWeight: "bold",
          }}
        >
          MOCK DATA — non-authoritative (dev-only provider)
        </div>
      )}
    </div>
  );
};

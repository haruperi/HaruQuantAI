/**
 * Workspace templates widget (FR-UI-COMPOSE_PANELS), owned by
 * FEAT-UI-MANAGE_LAYOUTS.
 *
 * Lists the feature's versioned templates (engine builtins + harvested V2
 * presets) and applies a selection through the feature's template request
 * bus, which the active workstation host applies via the engine's
 * TemplateManager — the same validated path as the toolbar template select.
 */

import React, { useEffect, useState } from "react";
import type { WidgetProps } from "../types";
import { MANAGE_LAYOUTS_TEMPLATES } from "../../features/manage_layouts/templates";
import {
  useManageLayoutsClient,
  manageLayoutsTemplateRequestBus,
} from "../../features/manage_layouts/feature";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; templateNames: readonly string[] }
  | { status: "unavailable"; reason: string };

function newRequestId(prefix: string): string {
  const cryptoRef = globalThis.crypto as Crypto | undefined;
  if (cryptoRef && typeof cryptoRef.randomUUID === "function") {
    return `${prefix}-${cryptoRef.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}`;
}

export const WorkspaceTemplatesWidget: React.FC<WidgetProps> = () => {
  const client = useManageLayoutsClient();
  const [loadState, setLoadState] = useState<LoadState>({ status: "loading" });
  const [applied, setApplied] = useState<string | null>(null);
  const isMockClient = (client as { isDevOnly?: boolean }).isDevOnly === true;

  useEffect(() => {
    let cancelled = false;
    client
      .manageLayouts({
        request_id: newRequestId("req-templates"),
        capability_snapshot_id: "snap-current",
        operation: "COMPOSE",
      })
      .then((success) => {
        if (cancelled) return;
        const names = [
          ...MANAGE_LAYOUTS_TEMPLATES.map((t) => t.name),
          ...(success.template ? [success.template.name] : []),
        ];
        setLoadState({ status: "ready", templateNames: names });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadState({
          status: "unavailable",
          reason:
            err instanceof Error
              ? `Templates unavailable: ${err.message}`
              : "Templates unavailable.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  const handleApply = (templateId: string): void => {
    setApplied(templateId);
    manageLayoutsTemplateRequestBus.emit(templateId);
  };

  return (
    <div
      className="workspace-templates-widget"
      data-testid="workspace-templates-widget"
      style={{
        padding: "16px",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        height: "100%",
        boxSizing: "border-box",
        overflow: "auto",
      }}
    >
      <h3 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#38bdf8" }}>
        Workspace Templates
      </h3>

      {loadState.status === "loading" && (
        <div data-testid="workspace-templates-loading" style={{ color: "#94a3b8", fontSize: "12px" }}>
          Loading templates...
        </div>
      )}
      {loadState.status === "unavailable" && (
        <div data-testid="workspace-templates-unavailable" role="status" style={{ color: "#facc15", fontSize: "12px" }}>
          {loadState.reason} Layout controls remain available.
        </div>
      )}
      {loadState.status === "ready" && (
        <ul
          aria-label="Workspace templates"
          style={{
            listStyle: "none",
            margin: 0,
            padding: 0,
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
          {MANAGE_LAYOUTS_TEMPLATES.map((template) => {
            const isApplied = applied === template.template_id;
            return (
              <li key={template.template_id} style={{ margin: 0, padding: 0 }}>
                <button
                  type="button"
                  data-testid={`workspace-template-${template.template_id}`}
                  aria-pressed={isApplied}
                  onClick={() => handleApply(template.template_id)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    padding: "8px 10px",
                    backgroundColor: isApplied ? "#0369a1" : "#1e293b",
                    color: "#e2e8f0",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontSize: "12px",
                  }}
                >
                  <strong>{template.name}</strong>
                  {isApplied && (
                    <span
                      data-testid={`template-applied-badge-${template.template_id}`}
                      style={{
                        marginLeft: "8px",
                        fontSize: "11px",
                        padding: "1px 6px",
                        borderRadius: "3px",
                        backgroundColor: "#0284c7",
                        color: "#ffffff",
                        fontWeight: "bold",
                      }}
                    >
                      [Applied]
                    </span>
                  )}
                  <span style={{ color: "#94a3b8" }}>
                    {" "}
                    — {template.layout.widget_instances?.length ?? 0} widgets
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {isMockClient && (
        <div
          data-testid="workspace-templates-mock-label"
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

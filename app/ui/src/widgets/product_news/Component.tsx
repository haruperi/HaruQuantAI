/**
 * Product-news widget (FR-UI-SHOW_PRODUCT_NEWS), owned by FEAT-UI-START_WORK.
 *
 * Presents optional release/update/news information in a dedicated region,
 * strictly separate from authoritative workspace state. Offline or failed
 * news never blocks work: every failure renders an explicit unavailable
 * state confined to this widget.
 */

import React, { useEffect, useState } from "react";
import type { WidgetProps } from "../types";
import type { UiNotification } from "../../contracts/generated/ui";
import { useStartWorkClient } from "../../features/start_work";

type NewsLoadState =
  | { status: "loading" }
  | { status: "ready"; items: UiNotification[] }
  | { status: "unavailable"; reason: string };

const SEVERITY_COLORS: Record<string, string> = {
  info: "#38bdf8",
  warning: "#facc15",
  error: "#f87171",
  success: "#4ade80",
};

function newRequestId(prefix: string): string {
  const cryptoRef = globalThis.crypto as Crypto | undefined;
  if (cryptoRef && typeof cryptoRef.randomUUID === "function") {
    return `${prefix}-${cryptoRef.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}`;
}

export const ProductNewsWidget: React.FC<WidgetProps> = () => {
  const client = useStartWorkClient();
  const [newsState, setNewsState] = useState<NewsLoadState>({ status: "loading" });
  const isMockClient = (client as { isDevOnly?: boolean }).isDevOnly === true;

  useEffect(() => {
    let cancelled = false;
    client
      .startWork({
        request_id: newRequestId("req-news"),
        capability_snapshot_id: "snap-current",
        operation: "SHOW_NEWS",
      })
      .then((success) => {
        if (cancelled) return;
        setNewsState({ status: "ready", items: success.news ?? [] });
      })
      .catch((err: unknown) => {
        // FR-UI-SHOW_PRODUCT_NEWS acceptance: failed/offline news is
        // non-blocking — only this widget region degrades.
        if (cancelled) return;
        setNewsState({
          status: "unavailable",
          reason:
            err instanceof Error
              ? `News unavailable: ${err.message}`
              : "News unavailable.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  return (
    <div
      className="product-news-widget"
      style={{
        padding: "16px",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        height: "100%",
        boxSizing: "border-box",
        overflow: "auto",
      }}
      data-testid="product-news-widget"
    >
      <h3 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#38bdf8" }}>
        Product News
      </h3>

      {newsState.status === "loading" && (
        <div data-testid="product-news-loading" style={{ color: "#94a3b8", fontSize: "12px" }}>
          Loading product news...
        </div>
      )}

      {newsState.status === "unavailable" && (
        <div
          data-testid="product-news-unavailable"
          role="status"
          style={{ color: "#facc15", fontSize: "12px" }}
        >
          {newsState.reason} Work is not affected.
        </div>
      )}

      {newsState.status === "ready" && newsState.items.length === 0 && (
        <div data-testid="product-news-empty" style={{ color: "#64748b", fontSize: "12px" }}>
          No product news at this time.
        </div>
      )}

      {newsState.status === "ready" && newsState.items.length > 0 && (
        <ul
          data-testid="product-news-items"
          style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "8px" }}
        >
          {newsState.items.map((item) => (
            <li
              key={item.notification_id}
              style={{
                padding: "8px 10px",
                backgroundColor: "#1e293b",
                borderRadius: "4px",
                fontSize: "12px",
              }}
            >
              <div
                style={{
                  fontWeight: "bold",
                  color: SEVERITY_COLORS[item.severity ?? "info"] ?? "#38bdf8",
                }}
              >
                {item.title}
              </div>
              <div style={{ color: "#cbd5e1", marginTop: "4px" }}>{item.message}</div>
              <div style={{ color: "#64748b", marginTop: "4px" }}>{item.timestamp_iso}</div>
            </li>
          ))}
        </ul>
      )}

      {isMockClient && (
        <div
          data-testid="product-news-mock-label"
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

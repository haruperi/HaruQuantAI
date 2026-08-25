import React from "react";
import type { WidgetProps } from "../types";

export const WidgetCatalogueWidget: React.FC<WidgetProps> = () => {
  return (
    <div
      className="widget-catalogue-panel"
      style={{
        padding: "16px",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        height: "100%",
        boxSizing: "border-box",
      }}
    >
      <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", color: "#38bdf8" }}>
        Widget Catalogue Panel
      </h3>
      <p style={{ fontSize: "13px", color: "#94a3b8" }}>
        Use the workstation toolbar "+ Add Widget" button to open the full interactive widget gallery.
      </p>
    </div>
  );
};

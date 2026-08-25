/**
 * Widget Catalogue Component for HaruQuantAI D-UI.
 *
 * Allows discovering registered widget types and adding new instances into the workstation.
 */

import React, { useState, useMemo } from "react";
import type { WidgetTypeDescriptor } from "../contracts/generated/ui";
import { WidgetRegistry } from "../runtime/widget_registry";

export interface WidgetCatalogueProps {
  registry: WidgetRegistry;
  onSelectWidget: (descriptor: WidgetTypeDescriptor) => void;
  onClose?: () => void;
}

export const WidgetCatalogue: React.FC<WidgetCatalogueProps> = ({
  registry,
  onSelectWidget,
  onClose,
}) => {
  const [filterText, setFilterText] = useState("");
  const descriptors = useMemo(() => registry.getDescriptors(), [registry]);

  const filteredDescriptors = useMemo(() => {
    if (!filterText.trim()) return descriptors;
    const query = filterText.toLowerCase();
    return descriptors.filter(
      (desc) =>
        desc.widget_type.toLowerCase().includes(query) ||
        desc.owning_feature.toLowerCase().includes(query)
    );
  }, [descriptors, filterText]);

  return (
    <div
      className="widget-catalogue-container"
      role="dialog"
      aria-modal="true"
      aria-label="Widget Catalogue"
      style={{
        padding: "20px",
        backgroundColor: "#1e293b",
        color: "#f8fafc",
        borderRadius: "8px",
        boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
        maxWidth: "600px",
        width: "100%",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h3 style={{ margin: 0, fontSize: "18px" }}>Widget Catalogue</h3>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close catalogue"
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "18px",
            }}
          >
            ?
          </button>
        )}
      </div>

      <div style={{ marginBottom: "16px" }}>
        <input
          type="text"
          placeholder="Filter widgets..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          aria-label="Filter widgets"
          style={{
            width: "100%",
            padding: "8px 12px",
            borderRadius: "6px",
            border: "1px solid #475569",
            backgroundColor: "#0f172a",
            color: "#f8fafc",
            fontSize: "14px",
            boxSizing: "border-box",
          }}
        />
      </div>

      <div
        style={{
          maxHeight: "360px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        {filteredDescriptors.length === 0 ? (
          <div style={{ padding: "24px", textAlign: "center", color: "#94a3b8" }}>
            No registered widgets match your filter.
          </div>
        ) : (
          filteredDescriptors.map((desc) => (
            <div
              key={desc.widget_type}
              style={{
                padding: "12px",
                backgroundColor: "#0f172a",
                borderRadius: "6px",
                border: "1px solid #334155",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <div style={{ fontWeight: "bold", fontSize: "14px", color: "#38bdf8" }}>
                  {desc.widget_type}
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
                  Owner: {desc.owning_feature} | Version: {desc.type_version}
                </div>
                {desc.time_domains && desc.time_domains.length > 0 && (
                  <div style={{ display: "flex", gap: "4px", marginTop: "6px" }}>
                    {desc.time_domains.map((td) => (
                      <span
                        key={td}
                        style={{
                          fontSize: "9px",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          backgroundColor: "#1e3a8a",
                          color: "#93c5fd",
                        }}
                      >
                        {td}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={() => onSelectWidget(desc)}
                style={{
                  padding: "6px 12px",
                  backgroundColor: "#0284c7",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "12px",
                  fontWeight: "bold",
                }}
              >
                Add
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
